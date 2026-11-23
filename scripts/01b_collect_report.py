"""Phase 1: descriptive report of a collection run, computed from data/raw/.

Usage: uv run python scripts/01b_collect_report.py --tag pilot
       uv run python scripts/01b_collect_report.py --tag full --years 2026

Writes results/tables/collect_report_<name>_{by_year,review_fields,openalex}.csv and
results/tables/collect_report_<name>.md, where <name> is the tag, followed by the years
when --years is given (the report then covers the latest run that holds these years).
"""

import argparse
import sys

from src.collect import report, store
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tag", choices=["pilot", "full"], required=True)
    parser.add_argument("--years", type=int, nargs="+", help="report on these years only")
    args = parser.parse_args()

    cfg = load_config()
    log = setup_run_logging(f"01b_collect_report_{args.tag}", cfg["paths"]["logs"])
    raw_dir = cfg["paths"]["raw"]
    tables_dir = cfg["paths"]["tables"]

    manifest_path = store.latest_manifest(raw_dir, args.tag, args.years)
    manifest = store.read_json(manifest_path)
    if args.years:
        manifest["years"] = {str(year): manifest["years"][str(year)] for year in args.years}
    log.info("manifest=%s", manifest_path)

    papers, reviews, openalex = report.load_rows(
        raw_dir, cfg["project"]["venue"], manifest, cfg["openalex"]["title_match_threshold"]
    )
    tables = {
        "by_year": report.by_year_table(papers, reviews),
        "review_fields": report.review_fields_table(reviews),
        "openalex": report.openalex_table(openalex),
    }

    tables_dir.mkdir(parents=True, exist_ok=True)
    prefix = "_".join(["collect_report", args.tag, *map(str, args.years or [])])
    for name, table in tables.items():
        table.to_csv(tables_dir / f"{prefix}_{name}.csv", index=False)

    history = manifest.get("history")
    lines = [
        f"# Collection report ({' '.join([args.tag, *map(str, args.years or [])])})",
        "",
        f"Manifest: `{manifest_path.name}` (started {manifest['started_at']}).",
        "",
        "## Run",
        "",
        f"- Submissions in this run: {len(papers)}",
        f"- Notes newly collected in this run: "
        f"{sum(run['n_collected'] for run in manifest['years'].values())}",
        f"- OpenReview requests in this run: {manifest['n_requests']} "
        f"(of which notes pass: {manifest['n_requests_notes']}) in {manifest['elapsed_seconds']} s",
    ]
    if history is None:
        lines.append("- Version history: not requested in this run")
    else:
        lines.append(
            f"- Version history: {history['n_collected']} forums collected in this run, "
            f"{history['n_skipped']} already on disk, {history['n_pending']} still pending"
        )
        if history["stopped_by"]:
            stop = history["stopped_by"]
            lines.append(
                f"- History pass stopped by the rate limit on `{stop['endpoint']}` "
                f"(policy `{stop['policy']}`, retry after {stop['retry_after_seconds']:.0f} s)"
            )
    for endpoint, policy in sorted(manifest.get("rate_limit_policies", {}).items()):
        lines.append(f"- Rate-limit policy announced for `{endpoint}`: `{policy}`")
    lines += ["", "## Per year (one line per metric)", ""]
    by_year = tables["by_year"].set_index("year").T.reset_index(names="metric")
    lines += [report.to_markdown(by_year), "", "## Review fields per year (share of reviews)", ""]
    fields = tables["review_fields"]
    if len(fields):
        wide = fields.pivot(index="field", columns="year", values="share").reset_index()
        lines.append(report.to_markdown(wide))
    else:
        lines.append("No review collected.")
    lines += ["", "## OpenAlex references by paper status", ""]
    if len(tables["openalex"]):
        lines += [
            f"OpenAlex was queried for {len(openalex)} of the {len(papers)} submissions of this run.",
            "",
            report.to_markdown(tables["openalex"]),
        ]
    else:
        lines.append("OpenAlex lookup not run.")
    text = "\n".join(lines) + "\n"

    (tables_dir / f"{prefix}.md").write_text(text, encoding="utf-8")
    log.info("report written to %s", tables_dir / f"{prefix}.md")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
