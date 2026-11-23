#!/usr/bin/env bash
# Phase 3 on the whole corpus: start the vLLM server if it is not running, extract the
# critiques with the validated prompt set, write the report, stop the server.
#
#   nohup scripts/03_run_full.sh > logs/03_run_full.out 2>&1 &     # whole corpus (about two days)
#   scripts/03_run_full.sh check                                   # dry run on a frozen sample
#   scripts/03_run_full.sh years 2026                              # one more year, setting A only
#                                                                  # (segmentation and typing), in its own directory
#   LIMIT=40 scripts/03_run_full.sh years 2026                     # dry run of the same on a few reviews
#
# The run can be interrupted and started again: answers already computed are cached.
set -euo pipefail
cd "$(dirname "$0")/.."

read -r PROMPT_SET BASE_URL < <(uv run python - <<'PY'
from src.utils.config import load_config
llm = load_config()["llm"]
print(llm["validated_prompt_set"], llm["base_url"])
PY
)
SAMPLE="${1:-}"
if [ -z "$SAMPLE" ]; then
    SELECTION=(--full); TAG="full_${PROMPT_SET}"
elif [ "$SAMPLE" = "years" ]; then
    shift
    SELECTION=(--full --years "$@" --skip-align); TAG="full_${PROMPT_SET}_$(IFS=_; echo "$*")"
    if [ -n "${LIMIT:-}" ]; then SELECTION+=(--limit "$LIMIT"); TAG="dryrun_${TAG}"; fi
else
    SELECTION=(--sample "$SAMPLE"); TAG="dryrun_${SAMPLE}_${PROMPT_SET}"
fi

mkdir -p logs
SERVER_PID=""
stop_server() {
    if [ -n "$SERVER_PID" ]; then
        echo "stopping the vLLM server (process $SERVER_PID and its children)"
        pkill -TERM -P "$SERVER_PID" 2>/dev/null || true   # the server itself, started by uv
        kill -TERM "$SERVER_PID" 2>/dev/null || true
    fi
}
trap stop_server EXIT

if curl -sf "$BASE_URL/models" > /dev/null; then
    echo "vLLM server already running: it will be left running at the end"
else
    SERVER_LOG="logs/vllm_server_$(date +%Y%m%d_%H%M%S).log"
    echo "starting the vLLM server (log: $SERVER_LOG)"
    scripts/03_serve_vllm.sh > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    for _ in $(seq 1 180); do   # up to 15 minutes to load the model
        curl -sf "$BASE_URL/models" > /dev/null && break
        kill -0 "$SERVER_PID" 2>/dev/null || { echo "the vLLM server exited, see $SERVER_LOG"; exit 1; }
        sleep 5
    done
    curl -sf "$BASE_URL/models" > /dev/null || { echo "the vLLM server did not answer in time"; exit 1; }
fi

uv run python scripts/03_extract_critiques.py "${SELECTION[@]}" --prompt-set "$PROMPT_SET" --tag "$TAG"
uv run python scripts/03b_llm_report.py --tag "$TAG" > /dev/null
echo "done: data/interim/llm/$TAG, results/tables/llm_${TAG}_report.md"
