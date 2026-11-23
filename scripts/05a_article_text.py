"""Phase 5a: title, abstract and keywords of the submissions before the decisions.

    uv run python scripts/05a_article_text.py

The current text of an accepted paper on OpenReview is its camera-ready version, which
a model must never read. This script takes the text from an archive scraped while the
submissions were anonymous (config `external.iclr_dataset`), checks that it is what it
claims to be, and writes data/interim/papers_initial.parquet.

Checks, in results/tables/article_text_source.{csv,md}, per year, archive version and
outcome of the paper:
- share of our papers found in the archive;
- share of abstracts with a link (code, project page): authors add them to the
  camera-ready version, so before the decisions accepted and rejected papers should
  show about the same share;
- share of titles and abstracts that differ from the current text: after the decisions
  only accepted papers change.
results/tables/article_text_coverage.csv gives the coverage by submission number.

The outcome of the papers is only used for these checks: the table written for the
models holds no outcome, and its content does not depend on it.
"""

import re
import sys

import pandas as pd

from src.collect import external, report
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

LINK = r"https?://|github\.com|\.github\.io|huggingface\.co"
GROUPS = {1: "accepted", 0: "rejected"}


def normalise(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def check_rows(ours: pd.DataFrame, archive: pd.DataFrame, year: int, kind: str, version: dict) -> list[dict]:
    """One row per outcome group: coverage, links, differences with the current text."""
    merged = ours.merge(archive, on="forum_id", how="left", suffixes=("", "_archive"), indicator=True)
    rows = []
    for group, papers in merged.groupby("group"):
        found = papers[papers["_merge"] == "both"]
        rows.append({
            "year": year, "version": kind, "committed": version["committed"], "outcome": group,
            "papers": len(papers),
            "found_in_archive": round(len(found) / len(papers), 4),
            "current_abstracts_with_link": round(float(papers["abstract"].str.contains(LINK, case=False).mean()), 4),
            "archive_abstracts_with_link": round(float(found["abstract_archive"].str.contains(LINK, case=False).mean()), 4),
            "title_differs_from_current": round(float((found["title"].map(normalise) != found["title_archive"].map(normalise)).mean()), 4),
            "abstract_differs_from_current": round(float((found["abstract"].map(normalise) != found["abstract_archive"].map(normalise)).mean()), 4),
        })
    return rows


def main() -> int:
    cfg = load_config()
    log = setup_run_logging("05a_article_text", cfg["paths"]["logs"])
    source = cfg["external"]["iclr_dataset"]
    root = cfg["paths"]["raw"] / source["dir"]
    versions = [v for kind in ("before_decision", "after_decision") for v in source[kind].values()]
    external.fetch_iclr_dataset(root, source["url"], versions)

    interim = cfg["paths"]["interim"]
    papers = pd.read_parquet(interim / "papers.parquet", columns=["forum_id", "year", "number", "title", "abstract"])
    outcomes = pd.read_parquet(interim / "outcomes.parquet",
                               columns=["forum_id", "label", "eligible_withdrawn_as_reject"])
    ours = papers.merge(outcomes, on="forum_id")
    ours = ours[ours["eligible_withdrawn_as_reject"]]
    ours["group"] = ours["label"].map(GROUPS).fillna("withdrawn")

    checks, coverage, initial = [], [], []
    for year in cfg["years"]:
        of_year = ours[ours["year"] == year]
        for kind in ("before_decision", "after_decision"):
            if kind == "after_decision" and year not in source[kind]:
                continue  # no later version of the archive for this year: no contrast row
            version = source[kind][year]
            archive = external.load_iclr_dataset(external.iclr_dataset_file(root, version), year)
            checks += check_rows(of_year, archive, year, kind, version)
            if kind != "before_decision":
                continue
            found = of_year["forum_id"].isin(set(archive["forum_id"]))
            deciles = pd.qcut(of_year["number"], 10, labels=False)
            for decile, group in of_year.assign(found=found).groupby(deciles):
                coverage.append({"year": year, "decile_of_submission_number": int(decile) + 1,
                                 "first_number": int(group["number"].min()), "last_number": int(group["number"].max()),
                                 "papers": len(group), "found_in_archive": round(float(group["found"].mean()), 4)})
            table = of_year[["forum_id", "year"]].merge(archive, on="forum_id", how="left")
            table["text_available"] = table["title"].notna()
            table["text_source"] = f"iclr_dataset:{version['path']}@{version['commit'][:7]}"
            table.loc[~table["text_available"], "text_source"] = None
            initial.append(table)
            log.info("year=%d papers=%d found=%d (%.4f) archive=%s", year, len(of_year), int(found.sum()),
                     found.mean(), version["path"])

    tables = cfg["paths"]["tables"]
    tables.mkdir(parents=True, exist_ok=True)
    checks, coverage = pd.DataFrame(checks), pd.DataFrame(coverage)
    checks.to_csv(tables / "article_text_source.csv", index=False)
    coverage.to_csv(tables / "article_text_coverage.csv", index=False)
    (tables / "article_text_source.md").write_text("\n".join([
        "# Text of the submissions before the decisions", "",
        f"Archive: {source['url']} ({source['paper']}, {source['license']}). `before_decision`: version used; "
        "`after_decision`: a later version of the same archive, shown for contrast. `current`: the text "
        "collected from OpenReview in phase 1 (camera-ready for accepted papers).", "",
        report.to_markdown(checks), "",
        "## Coverage of the version used, by submission number", "",
        report.to_markdown(coverage), "",
    ]), encoding="utf-8")

    initial = pd.concat(initial, ignore_index=True)
    initial = initial[["forum_id", "year", "title", "abstract", "keywords", "text_available", "text_source"]]
    initial.to_parquet(interim / "papers_initial.parquet", index=False)
    by_year = initial.groupby("year")["text_available"].agg(["size", "sum"])
    (interim / "papers_initial.stats.md").write_text("\n".join([
        "# papers_initial", "",
        "Title, abstract and keywords of the usable submissions before the decisions (archive "
        f"{source['url']}). A paper missing from the archive has no text (`text_available` false).", "",
        f"Rows: {len(initial)}", "",
        "| year | papers | with text | share |", "|---|---|---|---|",
        *(f"| {year} | {int(row['size'])} | {int(row['sum'])} | {row['sum'] / row['size']:.4f} |"
          for year, row in by_year.iterrows()), "",
        f"Abstract length in characters (papers with text): median "
        f"{int(initial['abstract'].str.len().median())}, min {int(initial['abstract'].str.len().min())}.",
        f"Keywords per paper (papers with text): mean "
        f"{initial.loc[initial['text_available'], 'keywords'].map(len).mean():.2f}.",
        "Checks: `results/tables/article_text_source.md`.", "",
    ]), encoding="utf-8")
    log.info("papers_initial: %d rows, %d with text", len(initial), int(initial["text_available"].sum()))
    print(report.to_markdown(checks))
    print(report.to_markdown(coverage[coverage["year"] == 2025]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
