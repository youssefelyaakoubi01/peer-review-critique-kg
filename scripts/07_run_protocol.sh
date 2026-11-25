#!/usr/bin/env bash
# Protocol checks (section `protocol` of the config): the graph whose vocabulary of concepts
# is counted on the training years, then the three stages and the ablations of the encoders.
#
#   setsid nohup scripts/07_run_protocol.sh > logs/07_run_protocol.out 2>&1 < /dev/null &
#   scripts/07_run_protocol.sh graph vocabulary      # only the named steps, in this order
#
# Steps: graph, vocabulary, encoders, search, rolling, depth (the follow-up of `search` on HAN, which reads
# the configuration that step kept). Every training script records its
# finished runs and does not run them again: a step that was interrupted is simply started
# again. A step that stops (GPU busy, projected run time over its limit) does not stop the
# following ones, except `graph`, which `vocabulary` and `rolling` read.
# The GPU is shared: each step stops if too little memory is free.
set -uo pipefail
cd "$(dirname "$0")/.."
if [ "$#" -eq 0 ]; then set -- graph vocabulary encoders search rolling depth; fi

need_gpu() {
    local free
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1)
    if [ "$free" -lt $(( $1 * 1024 )) ]; then
        echo "stopped: ${free} MiB free on the GPU, $1 GiB needed. The GPU is shared: wait for it to be free." >&2
        return 3
    fi
}

step() {   # name, then the command
    local name="$1"; shift
    echo "== $name: start ($(date -u '+%Y-%m-%d %H:%M:%S') UTC)"
    if "$@"; then
        echo "== $name: done ($(date -u '+%Y-%m-%d %H:%M:%S') UTC)"
    else
        local code=$?
        echo "== $name: STOPPED with code $code ($(date -u '+%Y-%m-%d %H:%M:%S') UTC)"
        return "$code"
    fi
}

failed=()
for name in "$@"; do
    case "$name" in
        graph)      step graph bash -c 'uv run python scripts/05f_inductive_graph.py' || { echo "the graph was not built: nothing else is run" >&2; exit 1; } ;;
        vocabulary|search|rolling|depth)
                    { need_gpu 12 && step "$name" uv run python scripts/07f_protocol_checks.py --stage "$name"; } || failed+=("$name") ;;
        encoders)   { need_gpu 10 && step encoders uv run python scripts/08_ablations.py --group encoder_variants; } || failed+=("$name") ;;
        *)          echo "unknown step: $name" >&2; exit 2 ;;
    esac
done
if [ "${#failed[@]}" -gt 0 ]; then
    echo "steps that did not finish: ${failed[*]} ($(date -u '+%Y-%m-%d %H:%M:%S') UTC)"
    exit 1
fi
echo "done: $* ($(date -u '+%Y-%m-%d %H:%M:%S') UTC)"
