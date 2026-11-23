#!/usr/bin/env bash
# Phase 3: start the vLLM server (OpenAI-compatible API) in its own environment.
# Usage: scripts/03_serve_vllm.sh            (reads the model settings from configs/default.yaml)
# The server only listens on localhost. Stop it with Ctrl-C or by killing the process.
# GPU_MEMORY_UTILIZATION (default 0.92): share of the card the server takes. Lower it when
# another user holds part of the GPU; the model context stays the same, only the number
# of requests served at once (hence the speed) goes down. Below about 0.70 on this 20 GB
# card, one request of the maximum length no longer fits.
set -euo pipefail
cd "$(dirname "$0")/.."

read -r MODEL REVISION MAX_LEN SEED PORT < <(uv run python - <<'PY'
from urllib.parse import urlparse
from src.utils.config import load_config
llm = load_config()["llm"]
print(llm["model"], llm["revision"], llm["max_model_len"], llm["seed"], urlparse(llm["base_url"]).port)
PY
)

# vLLM would otherwise compile FlashInfer's sampling kernel at start-up with the system
# nvcc, which is too old on this machine (CUDA 11.5: "Unknown option --compress-mode").
# The PyTorch sampler is used instead; at temperature 0 decoding is greedy either way.
export VLLM_USE_FLASHINFER_SAMPLER=0

exec uv run --project envs/vllm vllm serve "$MODEL" \
    --revision "$REVISION" \
    --host 127.0.0.1 --port "$PORT" \
    --max-model-len "$MAX_LEN" \
    --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION:-0.92}" \
    --seed "$SEED"
