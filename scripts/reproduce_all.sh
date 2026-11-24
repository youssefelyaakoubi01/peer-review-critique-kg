#!/usr/bin/env bash
# The whole chain, from the collection to the summary of the results (ICLR 2024 and 2025).
#
#   scripts/reproduce_all.sh                       # lists the stages, what they need and how long they took; runs nothing
#   scripts/reproduce_all.sh all                   # every stage, in order
#   scripts/reproduce_all.sh from graph            # from a stage to the end
#   scripts/reproduce_all.sh only baselines gnn    # the named stages
#   scripts/reproduce_all.sh results               # tables, tests, figures and summary only: trains nothing
#   DRY_RUN=1 scripts/reproduce_all.sh all         # prints the commands without running them
#
# The chain takes days (see the list). Run it detached from the terminal:
#   setsid nohup scripts/reproduce_all.sh all > logs/reproduce_all.out 2>&1 < /dev/null &
#
# The run stops at the first error. Each stage writes logs/reproduce_<stage>.out, next to
# the log of each script. What a second run reproduces exactly: everything computed on
# CPU from the same inputs. What it does not: the answers of the LLM when the cache is
# empty (data/interim/llm), and the trainings on the GPU, which use operations that are
# not deterministic. The durations below are those of the runs recorded in JOURNAL.md.
#
# Not in the chain: the annotation by humans (phase 4, scripts/04b_annotation_metrics.py
# once the files are annotated) and the holdout year, ICLR 2026, which has its own chain
# after this one: scripts/03_run_full.sh years 2026 (about 23 h of GPU), then
# scripts/07_run_holdout.sh, then the stage `results` again for the summary.
# The protocol checks read the graph of the holdout year and come after it:
# scripts/07_run_protocol.sh (graph with the vocabulary of the training year, three stages,
# ablations of the encoders; several hours of GPU), scripts/08_ablations.py --group followup,
# then the stage `results` again, which runs scripts/07g_protocol_results.py when their
# predictions exist.
set -euo pipefail
cd "$(dirname "$0")/.."

STAGES=(env collect clean extract annotation graph baselines gnn ablations explain results paper tests)

describe() {   # stage -> needs | measured duration | what it does
    case "$1" in
        env)        echo "- | seconds | checks the environment and the package versions" ;;
        collect)    echo "OpenReview credentials in .env, network | 4 min for 2024-2025, 14 min for 2026 (rate limited) | collects the submissions and their replies, reports" ;;
        clean)      echo "- | 1 min | cleans the collected data, attaches the initial scores" ;;
        extract)    echo "GPU, ${EXTRACT_GPU_GB} GiB free | 49 h (segmentation 11 h, typing 11 h, alignment of the author responses 27 h) | extracts and types the critiques with the LLM" ;;
        annotation) echo "- | seconds | draws the critiques to annotate (never overwrites an annotated file)" ;;
        graph)      echo "GPU, ${SMALL_GPU_GB} GiB free | 35 min | text of the articles, embeddings, graphs of settings A and B, RDF export" ;;
        baselines)  echo "GPU, ${SMALL_GPU_GB} GiB free | 6 min | baselines without the graph and homogeneous GCN" ;;
        gnn)        echo "GPU, ${TRAIN_GPU_GB} GiB free | 1 h | heterogeneous GNNs: hyper-parameter search and five seeds" ;;
        ablations)  echo "GPU, ${TRAIN_GPU_GB} GiB free | 25 min | ablations of the main model" ;;
        explain)    echo "CPU, three processes | 2 h 30 | explanations of the main model on the sampled test papers" ;;
        results)    echo "CPU | 53 min, mostly the bootstrap (23 min of them for the sensitivity analyses) | tables, intervals, tests, sensitivity analyses, figures, results/RESULTS_SUMMARY.md" ;;
        paper)      echo "pdflatex, latexmk | seconds | numbers of the text read from the result tables, then paper/main.pdf" ;;
        tests)      echo "- | minutes | pytest" ;;
        *)          echo "unknown stage: $1" >&2; return 1 ;;
    esac
}

# Free GPU memory asked before a stage starts (the GPU is shared with other users).
EXTRACT_GPU_GB=14   # measured: 13.5 GiB for the model, its working memory and one request of 16,384 tokens
TRAIN_GPU_GB=10     # ablations.gpu.min_free_gb; measured peak of one HGT training: 7.8 GiB
SMALL_GPU_GB=4      # embeddings, MLPs and GCN: peak not measured, this is a margin

list_stages() {
    printf '%-11s | %s\n' "stage" "needs | measured duration | what it does"
    for stage in "${STAGES[@]}"; do printf '%-11s | %s\n' "$stage" "$(describe "$stage")"; done
    echo
    sed -n '3,8p' "$0" | sed 's/^# \{0,3\}//'
}

run() {   # prints a command, and runs it unless DRY_RUN is set
    echo "+ $*"
    if [ -z "${DRY_RUN:-}" ]; then "$@"; fi
}

need_gpu() {   # stops if the GPU has less free memory than asked; never touches another process
    echo "+ check: at least $1 GiB free on the GPU"
    if [ -n "${DRY_RUN:-}" ]; then return 0; fi
    local free
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1)
    if [ "$free" -lt $(( $1 * 1024 )) ]; then
        echo "stopped: ${free} MiB free on the GPU, $1 GiB needed. The GPU is shared: wait for it to be free." >&2
        exit 3
    fi
}

config_value() {   # one value of configs/default.yaml, as a line of words
    uv run python -c "
from src.utils.config import load_config
cfg = load_config()
print(*$1)"
}

stage_env() { run uv run python scripts/00_check_env.py; }

stage_collect() {
    local years dir
    years=$(config_value 'cfg["years"]')
    # the archive of initial scores was downloaded by hand: check it is there and unchanged
    dir=$(config_value '[cfg["paths"]["raw"] / cfg["external"]["iclr_insights"]["dir"]]')
    echo "+ check: files of the external archive of initial scores in $dir"
    if [ -z "${DRY_RUN:-}" ]; then
        uv run python - <<'PY'
import hashlib
from src.utils.config import load_config
cfg = load_config()
source = cfg["external"]["iclr_insights"]
for year, name in source["files"].items():
    path = cfg["paths"]["raw"] / source["dir"] / name
    if not path.is_file():
        raise SystemExit(f"missing: {path}. Download it from {source['url']} first.")
    if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"][year]:
        raise SystemExit(f"{path} is not the file used in the study (checksum differs)")
PY
    fi
    # shellcheck disable=SC2086
    run uv run --env-file .env python scripts/01_collect.py --full --years $years
    run uv run python scripts/01b_collect_report.py --tag full
    run uv run python scripts/01c_check_initial_scores.py --tag full
}

stage_clean() { run uv run python scripts/02_clean.py; }

stage_extract() {
    need_gpu "$EXTRACT_GPU_GB"
    run scripts/03_run_full.sh   # starts the vLLM server, extracts, writes the report, stops the server
}

stage_annotation() { run uv run python scripts/04_prepare_annotation.py; }

stage_graph() {
    need_gpu "$SMALL_GPU_GB"
    run uv run python scripts/05a_article_text.py
    run uv run python scripts/05d_input_dates.py
    run uv run python scripts/05e_model_dates.py   # dates of the pretrained weights, read on the Hugging Face Hub (network)
    run uv run --project envs/specter2 python scripts/05b_embed_articles.py
    run uv run python scripts/05_build_graph.py
}

stage_baselines() {
    need_gpu "$SMALL_GPU_GB"
    run uv run python scripts/06_baselines.py
}

stage_gnn() {
    need_gpu "$TRAIN_GPU_GB"
    run uv run python scripts/07_hetero_gnn.py
}

stage_ablations() {
    need_gpu "$TRAIN_GPU_GB"
    run uv run python scripts/08_ablations.py
}

stage_explain() {   # three processes side by side, on CPU only
    local shards=3 pids=() shard pid
    for shard in $(seq 0 $((shards - 1))); do
        echo "+ CUDA_VISIBLE_DEVICES= uv run python scripts/09_explain.py --shard $shard --shards $shards &"
        if [ -z "${DRY_RUN:-}" ]; then
            CUDA_VISIBLE_DEVICES="" uv run python scripts/09_explain.py --shard "$shard" --shards "$shards" &
            pids+=($!)
        fi
    done
    for pid in "${pids[@]}"; do wait "$pid"; done
}

stage_results() {   # trains nothing; the report of the extraction is written by the extract stage
    export CUDA_VISIBLE_DEVICES=""
    run uv run python scripts/07b_main_results.py
    run uv run python scripts/08b_ablation_results.py
    run uv run python scripts/07e_sensitivity.py   # reads the tables of 07b and 08b, and those of the holdout year when they exist
    run uv run python scripts/09b_explain_results.py
    if [ -f results/predictions/protocol_vocabulary.parquet ]; then   # the protocol checks have their own chain (see above)
        run uv run python scripts/07g_protocol_results.py
    fi
    run uv run python scripts/10_consolidate.py
    unset CUDA_VISIBLE_DEVICES
}

stage_paper() { run uv run python scripts/11_paper.py; }

stage_tests() { run uv run pytest -q; }

# ---- which stages
case "${1:-list}" in
    list|-h|--help) list_stages; exit 0 ;;
    all)     selected=("${STAGES[@]}") ;;
    results) selected=(results) ;;
    only)    shift; selected=("$@") ;;
    from)
        selected=()
        for stage in "${STAGES[@]}"; do
            if [ "$stage" = "${2:-}" ] || [ ${#selected[@]} -gt 0 ]; then selected+=("$stage"); fi
        done ;;
    *) echo "unknown argument: $1" >&2; list_stages >&2; exit 2 ;;
esac
if [ ${#selected[@]} -eq 0 ]; then echo "no stage selected" >&2; list_stages >&2; exit 2; fi
for stage in "${selected[@]}"; do describe "$stage" > /dev/null; done   # every name is a stage

mkdir -p logs
for stage in "${selected[@]}"; do
    echo "=== stage $stage ($(date -u '+%Y-%m-%d %H:%M:%S') UTC): $(describe "$stage")"
    if [ -n "${DRY_RUN:-}" ]; then
        "stage_$stage"
    else
        "stage_$stage" 2>&1 | tee "logs/reproduce_${stage}.out"
    fi
done
echo "=== done: ${selected[*]} ($(date -u '+%Y-%m-%d %H:%M:%S') UTC)"
