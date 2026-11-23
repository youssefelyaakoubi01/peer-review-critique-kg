#!/usr/bin/env bash
# Holdout year (ICLR 2026), once its critiques are extracted (scripts/03_run_full.sh years 2026):
# graph of setting A extended with the holdout year, then the frozen models on it.
#
#   setsid nohup scripts/07_run_holdout.sh > logs/07_run_holdout.out 2>&1 < /dev/null &
#   scripts/07_run_holdout.sh graph      # only the graph (SPECTER2 of the new articles, text embeddings, extended graph)
#   scripts/07_run_holdout.sh models     # only the frozen models and their tables
#
# Measured: graph about 35 min on the GPU (embeddings of the reviews and critiques of the
# new year), models a few minutes, tables about 10 min of CPU (bootstrap).
# The GPU is shared: each step that uses it stops if too little memory is free.
set -euo pipefail
cd "$(dirname "$0")/.."
STEP="${1:-all}"

need_gpu() {
    local free
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1)
    if [ "$free" -lt $(( $1 * 1024 )) ]; then
        echo "stopped: ${free} MiB free on the GPU, $1 GiB needed. The GPU is shared: wait for it to be free." >&2
        exit 3
    fi
}

if [ "$STEP" = "all" ] || [ "$STEP" = "graph" ]; then
    need_gpu 6
    uv run --project envs/specter2 python scripts/05b_embed_articles.py --holdout
    uv run python scripts/05c_extend_graph.py
fi
if [ "$STEP" = "all" ] || [ "$STEP" = "models" ]; then
    need_gpu 12
    uv run python scripts/07c_holdout.py
    CUDA_VISIBLE_DEVICES="" uv run python scripts/07d_holdout_results.py
fi
echo "done: $STEP ($(date -u '+%Y-%m-%d %H:%M:%S') UTC)"
