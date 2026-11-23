"""Descriptive statistics of a collection run, computed from data/raw/ only."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.collect import parse, store
from src.collect.openalex import load_result, match_row

MINUTE_MS = 60_000
BURST_DENSITY = 0.1
BURST_MAX_GAP = 5


def load_rows(
    raw_dir: Path, venue: str, manifest: dict[str, Any], openalex_threshold: float
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Paper, review and OpenAlex rows for the forums listed in a manifest."""
    papers, reviews, openalex = [], [], []
    for year_str, run in manifest["years"].items():
        year = int(year_str)
        info = store.read_json(store.year_dir(raw_dir, venue, year) / "venue.json")["info"]
        for forum_id in run["forums"]:
            doc = store.read_json(store.notes_path(raw_dir, venue, year, forum_id))
            history_file = store.history_path(raw_dir, venue, year, forum_id)
            history = store.read_json(history_file) if history_file.exists() else None
            paper = parse.paper_row(doc, history, info)
            papers.append(paper)
            reviews.extend(parse.review_rows(doc, history, info))
            result = load_result(raw_dir, venue, year, forum_id)
            if result is not None:
                openalex.append(
                    {
                        "year": year,
                        "forum_id": forum_id,
                        "status": paper["status"],
                        **match_row(result, openalex_threshold),
                    }
                )
    return pd.DataFrame(papers), pd.DataFrame(reviews), pd.DataFrame(openalex)


def release_burst_end(tmdates: pd.Series) -> int | None:
    """Last minute (in ms) of the conference-wide edit that released the reviews (API v2).

    That edit stamps the `tmdate` of every review while it runs, which takes tens
    of minutes on a full conference (2023-11-10 17:05-17:2x for ICLR 2024). The
    burst is the run of dense minutes starting at the most frequent minute: a
    minute is dense if it holds at least BURST_DENSITY of the modal count, and the
    run tolerates gaps of BURST_MAX_GAP minutes.
    """
    minutes = (tmdates.dropna() // MINUTE_MS).astype("int64").value_counts()
    if not len(minutes):
        return None
    threshold = max(1, BURST_DENSITY * minutes.max())
    dense = set(minutes[minutes >= threshold].index)
    end = int(minutes.idxmax())
    while True:
        ahead = [m for m in range(end + 1, end + 1 + BURST_MAX_GAP) if m in dense]
        if not ahead:
            return end * MINUTE_MS
        end = ahead[-1]


def release_times(papers: pd.DataFrame, reviews: pd.DataFrame) -> dict[int, int | None]:
    """Estimated time (ms) at which the reviews of each year were released to the authors.

    API v2: end of the release burst, see release_burst_end().
    API v1: no such stamp; the earliest author reply of the year is used instead
    (to be re-examined on full 2023 data).
    """
    estimates: dict[int, int | None] = {}
    for year, group in papers.groupby("year"):
        if not len(reviews):
            estimates[year] = None
        elif group["api_version"].iloc[0] == "v2":
            estimates[year] = release_burst_end(reviews.loc[reviews["year"] == year, "tmdate"])
        else:
            first = group["first_author_reply_tcdate"].dropna()
            estimates[year] = int(first.min()) if len(first) else None
    return estimates


def flag_modified_after_release(
    reviews: pd.DataFrame, releases: dict[int, int | None]
) -> pd.DataFrame:
    """Add `modified_after_release` (True / False / None when the release time is unknown).

    A review is modified after release when its last modification is later than
    the release minute and later than its own creation (a review posted late and
    never touched is not "modified"). For such a review the content shown to the
    authors before the discussion is not what the API returns today.
    """
    reviews = reviews.copy()
    flags = []
    for row in reviews.itertuples(index=False):
        release = releases.get(row.year)
        if release is None or pd.isna(row.tmdate) or pd.isna(row.tcdate):
            flags.append(None)
            continue
        after_release = row.tmdate // MINUTE_MS > release // MINUTE_MS
        flags.append(bool(after_release and row.tmdate - row.tcdate > MINUTE_MS))
    reviews["modified_after_release"] = pd.array(flags, dtype="object")
    return reviews


def event_windows(events: dict[str, list[list[str]]]) -> dict[str, list[tuple[int, int]]]:
    """Windows of the conference-wide edits of a year (`collect.review_events`), in ms."""
    def ms(text: str) -> int:
        return int(datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)

    return {name: [(ms(start), ms(end)) for start, end in windows] for name, windows in events.items()}


def last_modification(tcdate: int, tmdate: int, windows: dict[str, list[tuple[int, int]]]) -> str:
    """How a review was last modified: "never_modified" since its creation, the name of a
    conference-wide edit (e.g. "release", "revert"), or "other" (by its reviewer)."""
    if tmdate - tcdate <= MINUTE_MS:
        return "never_modified"
    for name, spans in windows.items():
        if any(start <= tmdate < end for start, end in spans):
            return name
    return "other"


def iso(ms: int | None) -> str | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")


def count(series: pd.Series) -> int:
    """Number of True values (None counts as not True)."""
    return int(sum(1 for v in series if v is True))


def by_year_table(papers: pd.DataFrame, reviews: pd.DataFrame) -> pd.DataFrame:
    """Counts per year: papers by status, reviews, replies, acceptance rate, missing data."""
    releases = release_times(papers, reviews)
    reviews = flag_modified_after_release(reviews, releases) if len(reviews) else reviews
    rows = []
    for year, group in papers.groupby("year"):
        status = group["status"].value_counts()
        decided = int(status.get("accepted", 0) + status.get("rejected", 0))
        revs = reviews[reviews["year"] == year] if len(reviews) else reviews
        n_reviews = len(revs)
        reviewed = group[group["n_reviews"] > 0]
        decided_papers = group[group["status"].isin(["accepted", "rejected"])]

        modified = count(revs["modified_after_release"]) if n_reviews else 0
        unknown = int(sum(1 for v in revs["modified_after_release"] if v is None)) if n_reviews else 0
        initial_known = n_reviews - modified - unknown
        if n_reviews:
            per_paper = revs.groupby("forum_id")["modified_after_release"].agg(
                lambda flags: all(v is False for v in flags)
            )
            papers_all_known = int(per_paper.sum())
        else:
            papers_all_known = 0
        collected = revs[revs["history_collected"]] if n_reviews else revs

        rows.append(
            {
                "year": year,
                "api_version": group["api_version"].iloc[0],
                "n_papers": len(group),
                **{f"n_{s}": int(status.get(s, 0)) for s in parse.STATUSES},
                "acceptance_rate": (
                    round(status.get("accepted", 0) / decided, 4) if decided else None
                ),
                "n_reviews": n_reviews,
                "reviews_per_reviewed_paper": (
                    round(reviewed["n_reviews"].mean(), 2) if len(reviewed) else None
                ),
                "n_author_replies": int(group["n_author_replies"].sum()),
                "n_official_comments": int(group["n_official_comments"].sum()),
                "n_public_comments": int(group["n_public_comments"].sum()),
                "n_meta_reviews": int(group["has_meta_review"].sum()),
                "n_decisions": int(group["has_decision"].sum()),
                # Initial versus final version of the reviews
                "release_time_estimate_utc": iso(releases.get(year)),
                "reviews_not_modified_after_release": initial_known,
                "reviews_modified_after_release": modified,
                "reviews_modification_unknown": unknown,
                "share_reviews_initial_known": (
                    round(initial_known / n_reviews, 4) if n_reviews else None
                ),
                "reviewed_papers_all_initial_known": papers_all_known,
                # Version history actually collected (edit endpoint: 18 requests per hour)
                "papers_history_collected": int(group["history_collected"].sum()),
                "reviews_history_collected": len(collected),
                "reviews_history_forbidden": count(revs["history_forbidden"]) if n_reviews else 0,
                "reviews_creation_edit_readable": (
                    count(collected["creation_edit_readable"]) if len(collected) else 0
                ),
                "reviews_with_readable_reviewer_edits": (
                    int(sum(1 for v in collected["n_reviewer_edits_readable"] if v and v > 0))
                    if len(collected)
                    else 0
                ),
                "reviews_with_several_versions": (
                    int(sum(1 for v in collected["n_versions_readable"] if v and v > 1))
                    if len(collected)
                    else 0
                ),
                # Post-decision content (leakage): camera-ready revisions by status
                "accepted_with_camera_ready_revision": int(
                    group.loc[group["status"] == "accepted", "camera_ready_revision"].sum()
                ),
                "not_accepted_with_camera_ready_revision": int(
                    group.loc[group["status"] != "accepted", "camera_ready_revision"].sum()
                ),
                # Missing data
                "missing_title": int(group["missing_title"].sum()),
                "missing_abstract": int(group["missing_abstract"].sum()),
                "missing_keywords": int(group["missing_keywords"].sum()),
                "missing_pdf": int((~group["has_pdf"]).sum()),
                "decided_without_review": int((decided_papers["n_reviews"] == 0).sum()),
                "decided_without_meta_review": int((~decided_papers["has_meta_review"]).sum()),
                "reviews_missing_rating": int(revs["rating_final"].isna().sum()) if n_reviews else 0,
                "reviews_missing_confidence": (
                    int(revs["confidence_final"].isna().sum()) if n_reviews else 0
                ),
            }
        )
    return pd.DataFrame(rows)


def review_fields_table(reviews: pd.DataFrame) -> pd.DataFrame:
    """Share of reviews carrying each content field, per year (sub-scores differ by year)."""
    if not len(reviews):
        return pd.DataFrame(columns=["year", "field", "n_reviews", "share"])
    exploded = reviews[["year", "content_fields"]].explode("content_fields").dropna()
    counts = exploded.groupby(["year", "content_fields"]).size().rename("n_reviews").reset_index()
    totals = reviews.groupby("year").size().rename("total")
    counts = counts.join(totals, on="year")
    counts["share"] = (counts["n_reviews"] / counts["total"]).round(4)
    return counts.rename(columns={"content_fields": "field"})[["year", "field", "n_reviews", "share"]]


def openalex_table(openalex: pd.DataFrame) -> pd.DataFrame:
    """OpenAlex match and reference coverage by paper status (leakage check)."""
    columns = ["status", "n_papers", "n_matched", "n_with_references", "median_references"]
    if not len(openalex):
        return pd.DataFrame(columns=columns)
    rows = []
    for status, group in openalex.groupby("status"):
        with_refs = group[group["n_references"] > 0]
        rows.append(
            {
                "status": status,
                "n_papers": len(group),
                "n_matched": int(group["matched"].sum()),
                "n_with_references": len(with_refs),
                "median_references": (
                    float(with_refs["n_references"].median()) if len(with_refs) else None
                ),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def to_markdown(table: pd.DataFrame) -> str:
    """Minimal GitHub-flavoured table (avoids the optional `tabulate` dependency)."""
    def cell(value: Any) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "—"
        return str(value)

    lines = [
        "| " + " | ".join(str(c) for c in table.columns) + " |",
        "|" + "|".join("---" for _ in table.columns) + "|",
    ]
    for row in table.itertuples(index=False):
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    return "\n".join(lines)
