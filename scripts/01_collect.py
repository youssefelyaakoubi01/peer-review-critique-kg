"""Phase 1: collect ICLR submissions, reviews and discussions from OpenReview.

Pilot (sizes from the config):
    uv run --env-file .env python scripts/01_collect.py --pilot
Full collection of given years (only after the pilot has been validated):
    uv run --env-file .env python scripts/01_collect.py --full --years 2023 2024 2025
References through OpenAlex for the forums of the latest run of a tag:
    uv run --env-file .env python scripts/01_collect.py --pilot --openalex-only

The collection is resumable: a submission whose files already exist is skipped
(use --force to fetch it again).
"""

import argparse
import sys
import time
from datetime import datetime
from importlib.metadata import version

from src.collect import parse, store
from src.collect.client import OpenReviewSession
from src.collect.collector import collect_histories, collect_notes, pilot_allocation, utc_now
from src.collect.openalex import OpenAlexClient
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pilot", action="store_true", help="collect the pilot sample")
    mode.add_argument("--full", action="store_true", help="collect every submission of --years")
    parser.add_argument("--years", type=int, nargs="+", help="conference years (required with --full)")
    parser.add_argument("--force", action="store_true", help="fetch again what is already on disk")
    parser.add_argument(
        "--skip-history", action="store_true", help="collect notes only, not the version history"
    )
    parser.add_argument(
        "--max-wait",
        type=float,
        help="seconds a run may wait for an exhausted quota (default: config value)",
    )
    parser.add_argument("--openalex", action="store_true", help="also look up references in OpenAlex")
    parser.add_argument(
        "--openalex-only",
        action="store_true",
        help="skip OpenReview; look up references for the latest run of this tag",
    )
    args = parser.parse_args()
    if args.full and not args.years:
        parser.error("--full requires --years")
    return args


def run_openreview(cfg, args, tag, log) -> dict:
    raw_dir = cfg["paths"]["raw"]
    venue = cfg["project"]["venue"]
    collect_cfg = cfg["collect"]
    pilot = collect_cfg["pilot"]

    years = (args.years or pilot["years"]) if args.pilot else args.years
    # Candidate years may be collected and examined before they join the study.
    unknown = sorted(set(years) - set(cfg["years"]) - set(collect_cfg.get("candidate_years", [])))
    if unknown:
        raise SystemExit(f"years not in the config: {unknown}")
    allocation = pilot_allocation(years, pilot["size"]) if args.pilot else None

    max_wait = args.max_wait if args.max_wait is not None else collect_cfg["max_rate_limit_wait_seconds"]
    session = OpenReviewSession(collect_cfg["max_requests_per_minute"], max_rate_limit_wait=max_wait)
    manifest = {
        "tag": tag,
        "started_at": utc_now(),
        "command": " ".join(sys.argv),
        "packages": {p: version(p) for p in ("openreview-py", "requests")},
        "max_requests_per_minute": collect_cfg["max_requests_per_minute"],
        "years": {},
    }
    start = time.monotonic()
    for year in years:
        sample = None
        if allocation is not None:
            sample = {
                "total": allocation[year],
                "withdrawn": pilot["withdrawn_per_year"],
                "desk_rejected": pilot["desk_rejected_per_year"],
            }
        manifest["years"][str(year)] = collect_notes(
            session,
            raw_dir,
            venue,
            collect_cfg["venue_id_template"].format(year=year),
            year,
            log,
            sample=sample,
            force=args.force,
        )
    manifest["n_requests_notes"] = session.n_requests
    if args.skip_history:
        manifest["history"] = None
    else:
        manifest["history"] = collect_histories(
            session, raw_dir, venue, manifest["years"], log, force=args.force
        )
    manifest["finished_at"] = utc_now()
    manifest["elapsed_seconds"] = round(time.monotonic() - start, 1)
    manifest["n_requests"] = session.n_requests
    manifest["rate_limit_policies"] = session.policies

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = store.manifest_dir(raw_dir) / f"{tag}_{stamp}.json"
    store.write_json(path, manifest)
    log.info(
        "openreview done: requests=%d elapsed=%.0fs manifest=%s",
        session.n_requests, manifest["elapsed_seconds"], path,
    )
    return manifest


def run_openalex(cfg, manifest, force, log) -> None:
    raw_dir = cfg["paths"]["raw"]
    venue = cfg["project"]["venue"]
    client = OpenAlexClient(cfg["openalex"])
    counts = {"collected": 0, "skipped": 0, "no_title": 0}
    for year_str, run in manifest["years"].items():
        year = int(year_str)
        for forum_id in run["forums"]:
            doc = store.read_json(store.notes_path(raw_dir, venue, year, forum_id))
            title = parse.content_value(doc["submission"], "title")
            if not title:
                counts["no_title"] += 1
                continue
            counts[client.collect(raw_dir, venue, year, forum_id, title, force=force)] += 1
    log.info("openalex done: %s requests=%d", counts, client.n_requests)


def main() -> int:
    args = parse_args()
    cfg = load_config()
    tag = "pilot" if args.pilot else "full"
    log = setup_run_logging(f"01_collect_{tag}", cfg["paths"]["logs"])

    if args.openalex_only:
        manifest = store.read_json(store.latest_manifest(cfg["paths"]["raw"], tag))
    else:
        manifest = run_openreview(cfg, args, tag, log)
    if args.openalex or args.openalex_only:
        run_openalex(cfg, manifest, args.force, log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
