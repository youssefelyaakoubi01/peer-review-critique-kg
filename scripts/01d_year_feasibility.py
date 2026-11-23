"""Feasibility of a candidate year, from its raw collection only.

    uv run python scripts/01d_year_feasibility.py --year 2026

Answers, before the year joins the study, the questions the pipeline depends on:
  - which score fields the review form has, and on which scales;
  - whether the current state of a review can stand for its initial version: when the
    reviews were created and last modified;
  - whether the text of the submissions from before the decisions is available
    (archive `external.iclr_dataset.before_decision`), and whether it looks like it;
  - how many reviews the critique extraction would have to read.

Nothing here relates a score or a text to the outcome of a paper. The outcome is only
used to count the papers by status and for the leakage check of the text archive
(abstracts with a link, accepted against rejected).

Outputs in results/tables/: feasibility_<year>.md and feasibility_<year>_{scores,
rating_levels,dates,modification,replies,text}.csv.
"""

import argparse
import re
import sys
from datetime import datetime, timezone

import pandas as pd

from src.collect import external, parse, report, store
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

SCORES = ("rating", "confidence", "soundness", "presentation", "contribution")
LINK = r"https?://|github\.com|\.github\.io|huggingface\.co"
DAY_MS = 86_400_000


def day(ms: float | None) -> str | None:
    return None if ms is None or pd.isna(ms) else datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def share(part: int, whole: int) -> float | None:
    return round(part / whole, 4) if whole else None


def modification_class(reviews: pd.DataFrame, events: dict[str, list[list[str]]]) -> pd.Series:
    """How each review was last modified: never since its creation, by a conference-wide
    edit (windows of `collect.review_events`), or at another time (by its reviewer)."""
    windows = report.event_windows(events)
    return pd.Series([report.last_modification(created, modified, windows)
                      for created, modified in zip(reviews["tcdate"], reviews["tmdate"])], index=reviews.index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    cfg = load_config()
    year, venue, raw_dir, tables_dir = args.year, cfg["project"]["venue"], cfg["paths"]["raw"], cfg["paths"]["tables"]
    log = setup_run_logging(f"01d_year_feasibility_{year}", cfg["paths"]["logs"])

    manifest_path = store.latest_manifest(raw_dir, "full", [year])
    forums = store.read_json(manifest_path)["years"][str(year)]["forums"]
    if year not in cfg["external"]["iclr_dataset"]["before_decision"]:
        raise SystemExit(f"no text archive configured for {year} (external.iclr_dataset.before_decision)")
    info = store.read_json(store.year_dir(raw_dir, venue, year) / "venue.json")["info"]
    log.info("manifest=%s forums=%d", manifest_path.name, len(forums))

    papers, reviews, replies = [], [], []
    for forum_id in forums:
        doc = store.read_json(store.notes_path(raw_dir, venue, year, forum_id))
        submission = doc["submission"]
        status = parse.paper_status(doc, info)
        kinds = [parse.reply_kind(reply, info) for reply in doc["replies"]]
        author_times = [reply["tcdate"] for reply, kind in zip(doc["replies"], kinds)
                        if kind in ("official_comment", "rebuttal") and parse.signed_by_authors(reply) and reply.get("tcdate")]
        first_author_reply = min(author_times) if author_times else None
        papers.append({"forum_id": forum_id, "status": status, "decision": parse.decision_text(doc["replies"], info),
                       "title": parse.content_value(submission, "title"), "abstract": parse.content_value(submission, "abstract"),
                       "n_reviews": kinds.count("review"), "first_author_reply": first_author_reply})
        for reply, kind in zip(doc["replies"], kinds):
            signed_by_authors = parse.signed_by_authors(reply)
            replies.append({"kind": kind, "by_authors": signed_by_authors, "created": day(reply.get("tcdate"))})
            if kind != "review":
                continue
            content = reply.get("content") or {}
            reviews.append({"forum_id": forum_id, "status": status, "tcdate": reply.get("tcdate"), "tmdate": reply.get("tmdate"),
                            "fields": sorted(content),
                            "after_author_reply": first_author_reply is not None and reply.get("tcdate", 0) > first_author_reply,
                            **{score: parse.content_value(reply, score) for score in SCORES}})
    papers, reviews, replies = pd.DataFrame(papers), pd.DataFrame(reviews), pd.DataFrame(replies)
    usable = reviews[reviews["status"] != "desk_rejected"]

    # ---- scores: values as stored, per field
    score_rows = []
    for score in SCORES:
        counts = usable[score].map(lambda v: "(missing)" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)).value_counts()
        for value, n in counts.items():
            score_rows.append({"field": score, "value_as_stored": value, "parsed": parse.parse_score(None if value == "(missing)" else value),
                               "n_reviews": int(n), "share": share(int(n), len(usable))})
    scores = pd.DataFrame(score_rows).sort_values(["field", "parsed", "value_as_stored"], kind="stable")
    scores.to_csv(tables_dir / f"feasibility_{year}_scores.csv", index=False)
    other_fields = usable["fields"].explode().value_counts()

    # ---- rating: share of each level, next to the initial ratings of the study years
    levels = {year: usable["rating"].map(parse.parse_score).value_counts(normalize=True).sort_index()}
    study = pd.read_parquet(cfg["paths"]["interim"] / "reviews.parquet", columns=["year", "rating_initial"])
    for study_year, group in study.groupby("year"):
        levels[int(study_year)] = group["rating_initial"].dropna().astype(int).value_counts(normalize=True).sort_index()
    rating_levels = pd.DataFrame([{"level": rank + 1, **{f"value_{y}": int(shares.index[rank]) for y, shares in sorted(levels.items())},
                                   **{f"share_{y}": round(float(shares.iloc[rank]), 4) for y, shares in sorted(levels.items())}}
                                  for rank in range(max(len(shares) for shares in levels.values()))
                                  if all(rank < len(shares) for shares in levels.values())])
    rating_levels.to_csv(tables_dir / f"feasibility_{year}_rating_levels.csv", index=False)
    mean_ratings = {y: round(float((shares.index.to_numpy() * shares.to_numpy()).sum()), 3) for y, shares in sorted(levels.items())}

    # ---- dates: creation and last modification of the reviews, per day
    release_end = report.release_burst_end(usable["tmdate"])
    dates = pd.concat([usable["tcdate"].map(day).value_counts().rename("reviews_created"),
                       usable["tmdate"].map(day).value_counts().rename("reviews_last_modified")], axis=1).fillna(0).astype(int)
    dates = dates.sort_index().reset_index(names="day_utc")
    dates.to_csv(tables_dir / f"feasibility_{year}_dates.csv", index=False)
    modified_later = usable[(usable["tmdate"] // report.MINUTE_MS > release_end // report.MINUTE_MS)
                            & (usable["tmdate"] - usable["tcdate"] > report.MINUTE_MS)]
    hours = pd.to_datetime(usable["tmdate"], unit="ms", utc=True).dt.strftime("%Y-%m-%d %H:00").value_counts().sort_index()
    busiest = hours[hours >= 20].rename_axis("hour_utc").reset_index(name="reviews_last_modified")
    events = cfg["collect"].get("review_events", {}).get(year)
    modification = None
    if events:
        classes = modification_class(usable, events).value_counts()
        modification = classes.rename_axis("last_modification").reset_index(name="reviews")
        modification["share"] = (modification["reviews"] / len(usable)).round(5)
        modification.to_csv(tables_dir / f"feasibility_{year}_modification.csv", index=False)

    # ---- replies by kind, author and day
    reply_table = replies.groupby(["kind", "by_authors"]).agg(n=("created", "size"), first_day=("created", "min"),
                                                               last_day=("created", "max")).reset_index()
    reply_table.to_csv(tables_dir / f"feasibility_{year}_replies.csv", index=False)

    # ---- text before the decisions
    source = cfg["external"]["iclr_dataset"]
    version = source["before_decision"][year]
    root = raw_dir / source["dir"]
    external.fetch_iclr_dataset(root, source["url"], [version])
    archive = external.load_iclr_dataset(external.iclr_dataset_file(root, version), year)
    ours = papers[papers["status"] != "desk_rejected"].merge(archive, on="forum_id", how="left", suffixes=("", "_archive"), indicator=True)
    norm = lambda text: re.sub(r"\s+", " ", text or "").strip().lower()  # noqa: E731
    text_rows = []
    for status, group in ours.groupby("status"):
        found = group[group["_merge"] == "both"]
        text_rows.append({
            "status": status, "papers": len(group), "found_in_archive": share(len(found), len(group)),
            "current_abstracts_with_link": round(float(group["abstract"].fillna("").str.contains(LINK, case=False).mean()), 4),
            "archive_abstracts_with_link": round(float(found["abstract_archive"].fillna("").str.contains(LINK, case=False).mean()), 4),
            "title_differs_from_current": round(float((found["title"].map(norm) != found["title_archive"].map(norm)).mean()), 4),
            "abstract_differs_from_current": round(float((found["abstract"].map(norm) != found["abstract_archive"].map(norm)).mean()), 4),
            "archive_without_keywords": round(float((found["keywords"].map(len) == 0).mean()), 4)})
    text = pd.DataFrame(text_rows)
    text.to_csv(tables_dir / f"feasibility_{year}_text.csv", index=False)

    # ---- report
    status_counts = papers["status"].value_counts()
    decisions = papers["decision"].fillna("(no decision note)").value_counts()
    reviewed = papers[(papers["status"] != "desk_rejected") & (papers["n_reviews"] > 0)]
    lines = [
        f"# Feasibility of ICLR {year} (raw collection only)", "",
        f"Manifest: `{manifest_path.name}`. API {info['api_version']}. Text archive: `{version['path']}` at commit "
        f"`{version['commit'][:7]}` ({version['committed']}).", "",
        "## Papers", "",
        report.to_markdown(status_counts.rename_axis("status").reset_index(name="papers")), "",
        f"- Papers that are not desk rejected: {int((papers['status'] != 'desk_rejected').sum())}, of which with at least one review: {len(reviewed)}.",
        f"- Papers with an author reply: {int(papers['first_author_reply'].notna().sum())}.", "",
        "Decision notes (text as stored):", "",
        report.to_markdown(decisions.rename_axis("decision").reset_index(name="papers")), "",
        "## Reviews", "",
        f"- Reviews in total: {len(reviews)}; of papers that are not desk rejected: {len(usable)} "
        f"(what the critique extraction would read, before the eligibility rules of the cleaning step).",
        f"- By status of the paper: {usable['status'].value_counts().to_dict()}.",
        f"- Posted after the first author reply of their forum: {int(usable['after_author_reply'].sum())} ({share(int(usable['after_author_reply'].sum()), len(usable))}).", "",
        "Content fields (share of these reviews):", "",
        report.to_markdown((other_fields / len(usable)).round(4).rename_axis("field").reset_index(name="share")), "",
        "## Score scales (values as stored)", "",
        report.to_markdown(scores), "",
        "Rating: share of each level, in the order of the scale; initial ratings for the study years "
        "(`data/interim/reviews.parquet`), current ratings for the candidate year.", "",
        report.to_markdown(rating_levels), "",
        f"Mean rating: {mean_ratings}.", "",
        "## Dates of the reviews (UTC)", "",
        f"- End of the densest burst of last modifications (estimated release, `report.release_burst_end`): {report.iso(release_end)}.",
        f"- Reviews last modified after that burst, and more than a minute after their creation: {len(modified_later)} "
        f"({share(len(modified_later), len(usable))}).", "",
        "Hours with at least 20 last modifications:", "",
        report.to_markdown(busiest), "",
        *(["Last modification of each review (windows of `collect.review_events` in the config):", "",
           report.to_markdown(modification), ""] if modification is not None else []),
        "Per day:", "",
        report.to_markdown(dates), "",
        "## Replies by kind", "",
        report.to_markdown(reply_table), "",
        "## Text of the submissions before the decisions", "",
        f"Archive rows for {year}: {len(archive)}.", "",
        report.to_markdown(text), "",
    ]
    (tables_dir / f"feasibility_{year}.md").write_text("\n".join(lines), encoding="utf-8")
    log.info("report written to %s", tables_dir / f"feasibility_{year}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
