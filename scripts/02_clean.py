"""Phase 2: normalise the raw OpenReview forums into parquet tables.

Usage: uv run python scripts/02_clean.py

Reads the forums of the latest full collection of each configured year, drops
desk-rejected submissions, attaches the pre-rebuttal scores (external archive, or current
state for a year reverted by the conference: `clean.initial_scores`), aligns author
replies on reviews, splits notes into two temporal phases, and writes to
data/interim/:
    papers.parquet, reviews.parquet, reviews_final.parquet, discussion.parquet,
    outcomes.parquet, each with a <name>.stats.md next to it.
The figures quoted in JOURNAL.md come from results/tables/clean_report*.{csv,md}.
"""

import sys

import pandas as pd

from src.clean import normalize, views
from src.collect import external, parse, report, store
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

MINUTE_MS = 60_000
LABEL_WIDTH = 70
ROLES = ("authors", "reviewer", "area_chair", "senior_area_chair", "program_chairs", "public")


def share(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def word_count(*columns: pd.Series) -> pd.Series:
    total = pd.Series(0, index=columns[0].index)
    for column in columns:
        total = total + column.fillna("").str.split().str.len()
    return total


def describe(table: pd.DataFrame, name: str) -> str:
    """Descriptive statistics of one table (markdown)."""
    lines = [f"# {name}", "", f"Rows: {len(table)}", "", "| column | dtype | missing | distinct |", "|---|---|---|---|"]
    for column in table.columns:
        values = table[column]
        hashable = values.map(lambda v: tuple(v) if isinstance(v, (list, tuple)) or hasattr(v, "tolist") else v)
        lines.append(f"| {column} | {values.dtype} | {int(values.isna().sum())} | {hashable.nunique()} |")
    # Infinite values (external tracing score) are left out of the summary statistics.
    numeric = table.select_dtypes("number").astype("float64").replace(float("inf"), float("nan"))
    if len(numeric.columns):
        lines += ["", "## Numeric columns", "", report.to_markdown(
            numeric.describe().T.round(3).reset_index(names="column")
        )]
    if "year" in table.columns:
        lines += ["", "## Rows per year", "", report.to_markdown(
            table.groupby("year").size().rename("rows").reset_index()
        )]
    return "\n".join(lines) + "\n"


def build_tables(cfg, log):
    """Normalised tables, desk rejects dropped per year, release time per year, raw score labels."""
    raw_dir = cfg["paths"]["raw"]
    venue = cfg["project"]["venue"]
    source = cfg["external"]["iclr_insights"]
    initial_scores, rating_levels = cfg["clean"]["initial_scores"], cfg["clean"].get("rating_levels", {})
    windows = {year: report.event_windows(events) for year, events in cfg["collect"].get("review_events", {}).items()}

    papers, reviews, finals, discussion, outcomes = [], [], [], [], []
    desk_rejected = {}
    raw_labels: set[tuple[int, str, str]] = set()  # (year, score, value as stored by OpenReview)
    for year in cfg["years"]:
        run = store.read_json(store.latest_manifest(raw_dir, "full", [year]))["years"][str(year)]
        info = store.read_json(store.year_dir(raw_dir, venue, year) / "venue.json")["info"]
        if info["api_version"] != "v2":
            raise SystemExit(f"year {year}: only API v2 venues are supported by the cleaning step")
        if initial_scores[year] == "iclr_insights":
            ext = external.load_iclr_insights(raw_dir / source["dir"] / source["files"][year])
        elif initial_scores[year] == "current_state" and year in windows:
            ext = None
        else:
            raise SystemExit(f"year {year}: no usable source of initial scores ({initial_scores[year]!r})")
        desk_rejected[year] = 0
        for forum_id in run["forums"]:
            doc = store.read_json(store.notes_path(raw_dir, venue, year, forum_id))
            if parse.paper_status(doc, info) == "desk_rejected":
                desk_rejected[year] += 1
                continue
            initial_rows, final_rows = normalize.review_records(doc, info, ext, source["fields"], windows.get(year),
                                                                rating_levels.get(year))
            for reply in doc["replies"]:
                if parse.reply_kind(reply, info) == "review":
                    for field in normalize.SCORE_FIELDS:
                        raw_labels.add((year, field, str(parse.content_value(reply, field))[:LABEL_WIDTH]))
            papers.append(normalize.paper_record(doc))
            reviews += initial_rows
            finals += final_rows
            discussion += normalize.discussion_records(doc, info)
            outcomes.append(normalize.outcome_record(doc, info, cfg["splits"], initial_rows))
        log.info("year=%d forums=%d desk_rejected_dropped=%d", year, len(run["forums"]), desk_rejected[year])

    papers, reviews, finals = pd.DataFrame(papers), pd.DataFrame(reviews), pd.DataFrame(finals)
    discussion, outcomes = pd.DataFrame(discussion), pd.DataFrame(outcomes)
    for frame in (reviews, finals):
        for column in [c for c in frame.columns if c.endswith(("_initial", "_final", "_ext_post"))]:
            frame[column] = frame[column].astype("Int64")
    for column in ("label", "label_withdrawn_as_reject", "first_author_response_tcdate"):
        outcomes[column] = outcomes[column].astype("Int64")

    # Release of the reviews: end of the conference-wide edit burst (see report.py), or
    # of the first release window when the edits of the year are listed in the config.
    release = {y: windows[y]["release"][0][1] if y in windows
               else report.release_burst_end(finals.loc[finals["year"] == y, "tmdate"]) for y in cfg["years"]}
    release_ms = finals["year"].map(release)
    finals["modified_after_release"] = (finals["tmdate"] // MINUTE_MS > release_ms // MINUTE_MS) & (
        finals["tmdate"] - finals["tcdate"] > MINUTE_MS
    )
    for year, spans in windows.items():  # listed edits: modified = touched after a release edit
        of_year = finals["year"] == year
        finals.loc[of_year, "modified_after_release"] = [
            report.last_modification(created, modified, spans) not in ("never_modified", "release")
            for created, modified in zip(finals.loc[of_year, "tcdate"], finals.loc[of_year, "tmdate"])]
    # A conference date known before the discussion starts, hence allowed as model input.
    reviews["created_after_release"] = reviews["tcdate"] > reviews["year"].map(release)
    finals = finals.drop(columns=["tcdate"])

    # Author replies received by each review (aligned through the reply threads).
    author = discussion[(discussion["role"] == "authors") & discussion["target_review_id"].notna()]
    per_review = author.groupby("target_review_id")["tcdate"].agg(["size", "min"])
    finals["n_author_replies"] = finals["review_id"].map(per_review["size"]).fillna(0).astype(int)
    finals["first_author_reply_tcdate"] = finals["review_id"].map(per_review["min"]).astype("Int64")

    tables = {"papers": papers, "reviews": reviews, "reviews_final": finals,
              "discussion": discussion, "outcomes": outcomes}
    labels = pd.DataFrame(sorted(raw_labels), columns=["year", "score", "stored_value"])
    labels["integer"] = [rating_levels.get(year, {}).get(parse.parse_score(value), parse.parse_score(value)) if field == "rating"
                         else parse.parse_score(value) for year, field, value in zip(labels["year"], labels["score"], labels["stored_value"])]
    labels = labels.sort_values(["score", "year", "integer"]).reset_index(drop=True)
    return tables, desk_rejected, release, labels[["score", "year", "integer", "stored_value"]]


def by_year_table(cfg, tables, desk_rejected, release) -> pd.DataFrame:
    papers, reviews, finals = tables["papers"], tables["reviews"], tables["reviews_final"]
    discussion, outcomes = tables["discussion"], tables["outcomes"]
    merged = reviews.merge(finals, on=["review_id", "forum_id", "year"])
    rows = []
    for year in cfg["years"]:
        o, r, d = outcomes[outcomes["year"] == year], merged[merged["year"] == year], discussion[discussion["year"] == year]
        p = papers[papers["year"] == year]
        ri = r[r["rating_initial"].notna()]
        labelled = o[o["label"].notna()]
        authors = d[d["role"] == "authors"]
        before = r[r["phase"] == normalize.PHASE_BEFORE]
        rows.append({
            "year": year,
            "release_end_utc": report.iso(release[year]),
            "desk_rejected_excluded": desk_rejected[year],
            "papers": len(o),
            # Decisions
            **{f"decision_{k}": int((o["decision_type"] == k).sum()) for k in ("oral", "spotlight", "poster", "reject")},
            "papers_with_decision": len(labelled),
            "acceptance_rate_with_decision": share(int(labelled["label"].sum()), len(labelled)),
            # Withdrawn papers
            "withdrawn": int(o["withdrawn"].sum()),
            "withdrawn_before_decision": int(o["withdrawn_before_decision"].sum()),
            "withdrawn_after_decision": int((o["withdrawn"] & ~o["withdrawn_before_decision"]).sum()),
            "withdrawn_before_decision_without_review": int((o["withdrawn_before_decision"] & (o["n_reviews"] == 0)).sum()),
            # Setting A, two variants
            "eligible_withdrawn_excluded": int(o["eligible"].sum()),
            "acceptance_rate_withdrawn_excluded": share(int(o.loc[o["eligible"], "label"].sum()), int(o["eligible"].sum())),
            "eligible_withdrawn_as_reject": int(o["eligible_withdrawn_as_reject"].sum()),
            "acceptance_rate_withdrawn_as_reject": share(
                int(o.loc[o["eligible_withdrawn_as_reject"], "label_withdrawn_as_reject"].sum()),
                int(o["eligible_withdrawn_as_reject"].sum()),
            ),
            # Reviews
            "reviews": len(r),
            "reviews_before_author_response": len(before),
            "reviews_after_author_response": len(r) - len(before),
            "reviews_with_initial_scores": len(ri),
            "share_reviews_with_initial_scores": share(len(ri), len(r)),
            "reviews_created_after_release": int(r["created_after_release"].sum()),
            "reviews_modified_after_release": int(r["modified_after_release"].sum()),
            "share_reviews_modified_after_release": share(int(r["modified_after_release"].sum()), len(r)),
            "reviews_rating_changed": int((ri["rating_initial"] != ri["rating_final"]).sum()),
            "share_reviews_rating_changed": share(int((ri["rating_initial"] != ri["rating_final"]).sum()), len(ri)),
            "mean_rating_initial": round(float(ri["rating_initial"].mean()), 3),
            "mean_rating_final_same_reviews": round(float(ri["rating_final"].mean()), 3),
            # Discussion: phases and alignment
            "papers_with_author_response": int(o["has_author_response"].sum()),
            "discussion_notes": len(d),
            "discussion_before_author_response": int((d["phase"] == normalize.PHASE_BEFORE).sum()),
            "discussion_after_author_response": int((d["phase"] == normalize.PHASE_AFTER).sum()),
            **{f"discussion_by_{role}": int((d["role"] == role).sum()) for role in ROLES},
            "author_replies": len(authors),
            "author_replies_aligned_on_a_review": int(authors["target_review_id"].notna().sum()),
            "share_author_replies_aligned": share(int(authors["target_review_id"].notna().sum()), len(authors)),
            "author_replies_to_the_submission": int((authors["thread_root"] == "submission").sum()),
            "author_replies_parent_unknown": int((authors["thread_root"] == "unknown").sum()),
            "author_replies_under_meta_review_or_decision": int(authors["thread_root"].isin(["meta_review", "decision"]).sum()),
            "reviews_with_an_author_reply": int((r["n_author_replies"] > 0).sum()),
            "share_reviews_with_an_author_reply": share(int((r["n_author_replies"] > 0).sum()), len(r)),
            # Text
            "papers_with_meta_review": int(o["meta_review"].notna().sum()),
            "papers_missing_abstract": int(p["abstract"].isna().sum()),
            "papers_missing_keywords": int((p["keywords"].str.len() == 0).sum()),
            "papers_with_tldr": int(p["tldr"].notna().sum()),
            "median_abstract_words": float(word_count(p["abstract"]).median()),
            "median_review_words": float(word_count(*(r[f] for f in normalize.REVIEW_TEXT_FIELDS)).median()),
        })
    return pd.DataFrame(rows)


def splits_table(tables) -> pd.DataFrame:
    """Papers, labels and reviews per split, for the two treatments of withdrawn papers."""
    # Reviews of setting A. (The model-input view also needs `papers_initial`, which is
    # written later by scripts/05a_article_text.py.)
    reviews = tables["reviews"][tables["reviews"]["phase"] == normalize.PHASE_BEFORE]
    rows = []
    for variant in views.LABEL_COLUMNS:
        selected = views.labels(tables["outcomes"], variant)
        n_reviews = reviews.merge(selected[["forum_id", "split"]], on="forum_id").groupby("split").size()
        for (split, year), group in selected.groupby(["split", "year"]):
            rows.append({
                "withdrawn": variant, "split": split, "year": year, "papers": len(group),
                "accepted": int(group["label"].sum()), "rejected": int((group["label"] == 0).sum()),
                "acceptance_rate": share(int(group["label"].sum()), len(group)),
                "reviews": int(n_reviews.get(split, 0)),
            })
    return pd.DataFrame(rows)


def scales_table(cfg, tables) -> pd.DataFrame:
    """Distinct values of every score per year, initial and final (same scale across years?)."""
    reviews, finals = tables["reviews"], tables["reviews_final"]
    rows = []
    for field in normalize.SCORE_FIELDS:
        for version, frame in (("initial", reviews), ("final", finals)):
            row = {"score": field, "version": version}
            for year in cfg["years"]:
                values = frame.loc[frame["year"] == year, f"{field}_{version}"].dropna().unique()
                row[str(year)] = " ".join(str(v) for v in sorted(values)) or "not available"
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    log = setup_run_logging("02_clean", CFG["paths"]["logs"])
    interim, tables_dir = CFG["paths"]["interim"], CFG["paths"]["tables"]
    tables, desk_rejected, release, scale_labels = build_tables(CFG, log)

    interim.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_parquet(interim / f"{name}.parquet", index=False)
        (interim / f"{name}.stats.md").write_text(describe(table, name), encoding="utf-8")
        log.info("written %s rows=%d columns=%d", name, len(table), len(table.columns))

    reviews, finals, outcomes = tables["reviews"], tables["reviews_final"], tables["outcomes"]
    merged = reviews.merge(finals, on=["review_id", "forum_id", "year"]).merge(
        outcomes[["forum_id", "status"]], on="forum_id"
    )
    has_initial = merged["rating_initial"].notna()

    # Is the absence of initial scores related to the outcome? (leakage check)
    missing = (
        merged.assign(has_initial=has_initial)
        .groupby(["year", "status"])
        .agg(reviews=("review_id", "size"), with_initial_scores=("has_initial", "sum"))
        .reset_index()
    )
    missing["share_with_initial_scores"] = (missing["with_initial_scores"] / missing["reviews"]).round(4)

    # Validation of the join and of the field mapping: external post value = our final value.
    mapping = []
    for year in CFG["years"]:
        r = merged[(merged["year"] == year) & has_initial]
        for field in normalize.SCORE_FIELDS:
            both = r[r[f"{field}_ext_post"].notna()]
            mapping.append({
                "year": year, "field": field, "reviews_compared": len(both),
                "initial_available": int(r[f"{field}_initial"].notna().sum()),
                "share_ext_post_equals_final": share(int((both[f"{field}_ext_post"] == both[f"{field}_final"]).sum()), len(both)),
            })

    discussion = tables["discussion"]
    phases = (
        discussion.groupby(["year", "phase", "role"]).size().rename("notes").reset_index()
        .pivot_table(index=["year", "role"], columns="phase", values="notes", fill_value=0)
        .astype(int)
        .reset_index()
    )
    phases.columns.name = None

    by_year = by_year_table(CFG, tables, desk_rejected, release)
    outputs = {
        "by_year": by_year,
        "splits": splits_table(tables),
        "scales": scales_table(CFG, tables),
        "scale_labels": scale_labels,
        "phases_by_role": phases,
        "initial_scores_by_status": missing,
        "score_fields": pd.DataFrame(mapping),
    }
    tables_dir.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(tables_dir / f"clean_report_{name}.csv", index=False)

    wide = by_year.astype(object).set_index("year").T.reset_index(names="metric")
    text = "\n".join([
        "# Cleaning report",
        "",
        "Tables in `data/interim/` (desk-rejected submissions excluded): "
        + ", ".join(f"`{n}` ({len(t)} rows)" for n, t in tables.items()) + ".",
        "",
        "## Per year", "", report.to_markdown(wide), "",
        "## Score scales: distinct values per year", "", report.to_markdown(outputs["scales"]), "",
        "## Score scales: value stored by OpenReview and integer kept", "",
        f"(Stored values are cut at {LABEL_WIDTH} characters.)", "",
        report.to_markdown(scale_labels), "",
        "## Splits of the papers usable in setting A, by treatment of withdrawn papers", "",
        "A paper is usable if it has a label and an initial rating for every review posted "
        "before the first author response. Reviews: those posted before the author response.", "",
        report.to_markdown(outputs["splits"]), "",
        "## Discussion notes by role and phase", "", report.to_markdown(phases), "",
        "## Initial scores available, by paper status", "", report.to_markdown(missing), "",
        "## Score fields: external post-rebuttal value versus our final value", "",
        report.to_markdown(outputs["score_fields"]), "",
    ])
    (tables_dir / "clean_report.md").write_text(text, encoding="utf-8")
    log.info("report written to %s", tables_dir / "clean_report.md")
    print(text)
    return 0


CFG = load_config()

if __name__ == "__main__":
    sys.exit(main())
