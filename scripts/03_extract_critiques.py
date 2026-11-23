"""Phase 3: segment reviews into critiques, type them, align them on the author replies.

The vLLM server must be running (scripts/03_serve_vllm.sh), unless --backend names a
hosted API (paid: `uv run --env-file .env ... --backend deepseek --budget <USD>`).

    uv run python scripts/03_extract_critiques.py --sample dev --prompt-set v2    # frozen pilot sample
    uv run python scripts/03_extract_critiques.py --full --prompt-set v2          # whole corpus, only after validation
    uv run python scripts/03_extract_critiques.py --full --years 2026 --skip-align --prompt-set v3   # one more year, setting A

Answers are cached by hash: a second run sends nothing to the model. Outputs go to
data/interim/llm/<tag>/ (critiques, critique_responses, audit, run_stats.json); the tag
is <sample>_<prompt set> by default, followed by the years when --years is given. A
year added later gets its own directory: the run of the other years is left untouched
(its failed answers are not cached, and would be sent to the model again).
"""

import argparse
import json
import sys
from datetime import datetime
from importlib.metadata import version

import requests

from src.llm import inputs, pipeline, steps
from src.llm.client import LLMClient, ServerDown
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging


def check_server(llm) -> None:
    try:
        models = requests.get(f"{llm['base_url']}/models", timeout=10).json()["data"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise SystemExit(f"vLLM server not reachable at {llm['base_url']} ({exc}). Run scripts/03_serve_vllm.sh") from exc
    served = [m["id"] for m in models]
    if llm["model"] not in served:
        raise SystemExit(f"server serves {served}, config expects {llm['model']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    cfg = load_config()
    llm = cfg["llm"]
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sample", choices=sorted(llm["samples"]["seeds"]), help="frozen sample of reviews")
    mode.add_argument("--full", action="store_true", help="whole corpus")
    parser.add_argument("--prompt-set", choices=sorted(llm["prompt_sets"]), required=True)
    parser.add_argument("--tag", help="name of the output directory (default: <sample>_<prompt set>)")
    parser.add_argument("--years", type=int, nargs="+", help="with --full: only the reviews of these years")
    parser.add_argument("--skip-align", action="store_true",
                        help="segmentation and typing only (setting A): the author replies are not read")
    parser.add_argument("--limit", type=int, help="only the first reviews (dry run)")
    parser.add_argument("--backend", choices=["vllm", *sorted(llm.get("backends", {}))], default="vllm",
                        help="local vLLM server (default) or a hosted API of `llm.backends`")
    parser.add_argument("--budget", type=float, help="hosted API: stop when the requests of this run have cost this (USD)")
    args = parser.parse_args()
    if args.years and not args.full:
        parser.error("--years requires --full")
    if args.full and not args.years:
        # the whole corpus of the study: training and test years, not a holdout year
        args.years = sorted([*cfg["splits"]["train"], *cfg["splits"]["test"]])
    hosted = args.backend != "vllm"
    if hosted:
        llm = {**llm, **llm["backends"][args.backend], "backend": args.backend}
        if args.budget is not None:
            llm["budget_usd"] = args.budget
    named_years = args.years if args.full and "--years" in sys.argv else []
    tag = args.tag or "_".join([args.sample or "full", args.prompt_set, *map(str, named_years),
                                *([args.backend] if hosted else [])])
    prompt_names = llm["prompt_sets"][args.prompt_set]
    log = setup_run_logging(f"03_extract_critiques_{tag}", cfg["paths"]["logs"])
    if not hosted:
        check_server(llm)

    prompts = {step: steps.load_prompt(cfg["paths"]["prompts"], name) for step, name in prompt_names.items()}
    reviews = inputs.select_reviews(cfg, args.sample, args.years)
    if args.limit:
        reviews = reviews.head(args.limit)
    examples = inputs.prompt_example_ids(cfg["paths"]["prompts"])
    if args.sample and examples & set(reviews["review_id"]):
        raise SystemExit(f"sample {args.sample} contains prompt examples: {sorted(examples & set(reviews['review_id']))}")
    replies = {} if args.skip_align else inputs.author_replies(cfg, set(reviews["review_id"]))
    log.info("tag=%s reviews=%d with_author_replies=%d model=%s prompts=%s",
             tag, len(reviews), len(replies), llm["model"], prompt_names)

    out_dir = cfg["paths"]["llm"] / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = out_dir / "failures.jsonl"
    if failures.exists():
        # failures.jsonl holds the failures of one run only (failed answers are never
        # cached), but the log of an earlier run is kept: it cannot be computed again
        # without sending its items to the model.
        failures.rename(out_dir / f"failures_before_{datetime.now():%Y%m%d_%H%M%S}.jsonl")
    client = LLMClient(llm, cfg["paths"]["llm"] / "cache", failures)

    def save(tables, timings) -> None:
        """Write the tables and the run statistics as they stand (called after each pass)."""
        critiques, responses, audit = tables
        critiques.to_parquet(out_dir / "critiques.parquet", index=False)
        responses.to_parquet(out_dir / "critique_responses.parquet", index=False)
        audit.to_parquet(out_dir / "audit.parquet", index=False)
        stats = {
            "tag": tag, "sample": args.sample or "full", "prompt_set": args.prompt_set,
            "years": args.years, "skip_align": args.skip_align, "limit": args.limit, "backend": args.backend,
            "served": sorted(client.served), "budget_usd": llm.get("budget_usd") if hosted else None,
            "model": llm["model"], "revision": llm["revision"],
            "prompts": prompt_names, "concurrency": llm["concurrency"],
            "packages": {p: version(p) for p in ("pydantic", "requests")},
            "reviews": len(reviews), "reviews_with_author_replies": len(replies),
            "passes": timings, "complete": len(timings) == len(prompt_names), "totals": client.stats,
        }
        (out_dir / "run_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        log.info("pass %s; tables written to %s", timings[-1], out_dir)

    try:
        critiques, responses, audit, timings = pipeline.extract(client, prompts, llm, reviews, replies, save, log)
    except ServerDown as exc:
        log.error("run stopped: %s. Answers already computed are cached: run the same command again.", exc)
        return 1
    log.info("critiques=%d responses=%d failures=%d output=%s",
             len(critiques), len(responses), client.stats["failures"], out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
