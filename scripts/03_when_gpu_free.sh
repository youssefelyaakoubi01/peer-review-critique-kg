#!/usr/bin/env bash
# Start scripts/03_run_full.sh as soon as the GPU is free, with the same arguments.
#
#   setsid nohup scripts/03_when_gpu_free.sh years 2026 > logs/03_run_2026.out 2>&1 < /dev/null &
#
# The GPU is shared with other users. The vLLM server needs at least 13.5 GiB to hold the
# model and one request of the maximum length, and takes 18 GiB to run at its usual
# pace: it is only started once no other process has used the GPU for FREE_MINUTES
# minutes in a row (default 10). Nothing belonging to another user is ever touched.
# To cancel while it waits: pkill -f 03_when_gpu_free.sh
set -euo pipefail
cd "$(dirname "$0")/.."
FREE_MINUTES="${FREE_MINUTES:-10}"
MAX_USED_MIB="${MAX_USED_MIB:-500}"

free=0
checks=0
while [ "$free" -lt "$FREE_MINUTES" ]; do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
    if [ "$used" -le "$MAX_USED_MIB" ]; then free=$((free + 1)); else free=0; fi
    if [ "$free" -gt 0 ] || [ $((checks % 10)) -eq 0 ]; then   # one line every ten minutes while the GPU is busy
        echo "$(date '+%F %T') waiting for the GPU: ${used} MiB used, free for ${free} of ${FREE_MINUTES} minutes"
    fi
    checks=$((checks + 1))
    sleep 60
done
echo "$(date '+%F %T') the GPU is free: starting scripts/03_run_full.sh $*"
exec scripts/03_run_full.sh "$@"
