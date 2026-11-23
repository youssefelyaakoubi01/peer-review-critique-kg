"""Phase 1: can the external pre-rebuttal scores be attached to our reviews?

Joins the papercopilot/iclr-insights score pairs ("initial;post", ICLR 2024 and
2025) to the reviews collected from OpenReview and checks the join:
  - coverage: share of our reviews that receive a score pair;
  - consistency: the external "post" score must equal our final score;
  - agreement between "score changed" and our timestamp-based flag
    "modified after release".

Usage: uv run python scripts/01c_check_initial_scores.py --tag full
Writes results/tables/initial_scores_check_<tag>.{csv,md}.
"""

import argparse
import math
import sys

import pandas as pd

from src.collect import external, parse, report, store
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging


def share(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tag", choices=["pilot", "full"], required=True)
    args = parser.parse_args()

    cfg = load_config()
    log = setup_run_logging(f"01c_check_initial_scores_{args.tag}", cfg["paths"]["logs"])
    raw_dir = cfg["paths"]["raw"]
    venue = cfg["project"]["venue"]
    source = cfg["external"]["iclr_insights"]
    # the external scores only cover some years: the latest run that holds all of them
    covered = sorted(source["files"]) if args.tag == "full" else None
    manifest_path = store.latest_manifest(raw_dir, args.tag, covered)
    manifest = store.read_json(manifest_path)
    log.info("manifest=%s", manifest_path)

    papers, reviews, _ = report.load_rows(
        raw_dir, venue, manifest, cfg["openalex"]["title_match_threshold"]
    )
    reviews = report.flag_modified_after_release(reviews, report.release_times(papers, reviews))
    status = papers.set_index("forum_id")["status"]

    rows = []
    for year_str, run in manifest["years"].items():
        year = int(year_str)
        if year not in source["files"]:
            log.info("year=%d: no external file, skipped", year)
            continue
        ext = external.load_iclr_insights(raw_dir / source["dir"] / source["files"][year])
        info = store.read_json(store.year_dir(raw_dir, venue, year) / "venue.json")["info"]

        joined = []
        for forum_id in run["forums"]:
            doc = store.read_json(store.notes_path(raw_dir, venue, year, forum_id))
            for reply in doc["replies"]:
                if parse.reply_kind(reply, info) == "review":
                    joined.append(
                        {"review_id": reply["id"], **external.join_review(ext, forum_id, reply)}
                    )
        ours = reviews[reviews["year"] == year].merge(pd.DataFrame(joined), on="review_id")
        matched = ours[ours["matched"]]
        reliable = matched[matched["tracing_score"].map(lambda s: s is not None and s <= 1)]
        changed = matched["ext_rating_initial"] != matched["ext_rating_post"]
        flagged = matched["modified_after_release"].map(lambda v: v is True)
        any_changed = matched["ext_any_score_changed"].map(lambda v: v is True)

        forums = set(run["forums"])
        reviewed = ours.groupby("forum_id")["matched"].all()
        decided = [f for f in reviewed.index if status.get(f) in ("accepted", "rejected")]
        rows.append(
            {
                "year": year,
                "papers_ours": len(forums),
                "papers_external": len(ext),
                "papers_in_both": len(forums & set(ext)),
                "external_papers_without_scores": sum(1 for p in ext.values() if not p["reviews"]),
                "external_tracing_score_infinite": sum(
                    1 for p in ext.values()
                    if isinstance(p["tracing_score"], float) and math.isinf(p["tracing_score"])
                ),
                "reviews_ours": len(ours),
                "reviews_matched": len(matched),
                "share_reviews_matched": share(len(matched), len(ours)),
                "reviewed_papers_ours": len(reviewed),
                "reviewed_papers_all_reviews_matched": int(reviewed.sum()),
                "decided_papers_all_reviews_matched": int(reviewed.loc[decided].sum()),
                "decided_papers_reviewed": len(decided),
                # Consistency of the join: external post-rebuttal score versus our final score
                "matched_post_rating_equals_final": int(
                    (matched["ext_rating_post"] == matched["rating_final"]).sum()
                ),
                "share_post_rating_equals_final": share(
                    int((matched["ext_rating_post"] == matched["rating_final"]).sum()), len(matched)
                ),
                "share_post_confidence_equals_final": share(
                    int((matched["ext_confidence_post"] == matched["confidence_final"]).sum()),
                    len(matched),
                ),
                "share_post_rating_equals_final_tracing_le_1": share(
                    int((reliable["ext_rating_post"] == reliable["rating_final"]).sum()),
                    len(reliable),
                ),
                "reviews_matched_tracing_le_1": len(reliable),
                # Initial versus final rating
                "matched_rating_changed": int(changed.sum()),
                "share_matched_rating_changed": share(int(changed.sum()), len(matched)),
                "matched_rating_increased": int(
                    (matched["ext_rating_post"] > matched["ext_rating_initial"]).sum()
                ),
                "matched_rating_decreased": int(
                    (matched["ext_rating_post"] < matched["ext_rating_initial"]).sum()
                ),
                # Our timestamp flag versus the external score change
                "score_changed_and_flagged_modified": int((any_changed & flagged).sum()),
                "score_changed_not_flagged_modified": int((any_changed & ~flagged).sum()),
                "score_unchanged_flagged_modified": int((~any_changed & flagged).sum()),
                "score_unchanged_not_flagged_modified": int((~any_changed & ~flagged).sum()),
            }
        )

    table = pd.DataFrame(rows)
    tables_dir = cfg["paths"]["tables"]
    tables_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"initial_scores_check_{args.tag}"
    table.to_csv(tables_dir / f"{prefix}.csv", index=False)
    # Object dtype keeps integers as integers when the table is transposed.
    wide = table.astype(object).set_index("year").T.reset_index(names="metric")
    text = "\n".join(
        [
            f"# External pre-rebuttal scores: join check ({args.tag})",
            "",
            f"Source: {source['url']} ({source['license']}). Manifest: `{manifest_path.name}`.",
            "",
            report.to_markdown(wide),
            "",
        ]
    )
    (tables_dir / f"{prefix}.md").write_text(text, encoding="utf-8")
    log.info("written %s", tables_dir / f"{prefix}.md")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
