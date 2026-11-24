"""Phase 5d: dates of the sources of the model inputs against the date of the decisions.

    uv run python scripts/05d_input_dates.py

Reads the raw OpenReview forums (creation date of the decision notes), the commit
dates of the archive of submission texts named in the config and the dates of the author
replies (data/interim/discussion.parquet); writes nothing a model reads. Output: results/tables/input_dates.csv, one row per year:
    decision notes, first and last day on which one was created, day the version of the
    text archive used for that year was committed, whether this commit precedes the
    first decision note, how many submissions of that version already carry a
    decision and which values this field takes (its `decision` column is read for this
    count only; the authors never are): a withdrawal or a desk rejection is known
    before the decisions, an acceptance or a rejection is not;
    author replies aligned on a review (the input added in setting B), and those created
    on or after the day of the first decision note.
A commit made after the decisions does not show by itself that the text is later than
the decisions (a file can be committed after it was scraped): a file scraped after the
decisions would carry them. The other checks on the content are those of
scripts/05a_article_text.py.
"""

import sys
from datetime import date, datetime, timezone

import pandas as pd

from src.collect import external, parse, store
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging


def day(milliseconds: int) -> date:
    return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).date()


def decision_days(replies: list[dict], info: dict) -> list[date]:
    """Day (UTC) on which each decision note of a forum was created."""
    return [day(reply["tcdate"]) for reply in replies if parse.reply_kind(reply, info) == "decision"]


def row(year: int, days: list[date], committed: date) -> dict:
    return {"year": year, "decision_notes": len(days), "first_decision_note": min(days).isoformat(),
            "last_decision_note": max(days).isoformat(), "text_archive_committed": committed.isoformat(),
            "days_from_first_decision_to_commit": (committed - min(days)).days,
            "text_committed_before_decisions": committed < min(days)}


def archive_decisions(path, year: int) -> dict:
    """Submissions of one year in a version of the text archive, and those that already carry a decision."""
    table = pd.read_parquet(path, columns=["year", "decision"])
    decisions = table.loc[table["year"] == year, "decision"].fillna("").astype(str).str.strip()
    values = decisions[decisions != ""].value_counts().sort_index()
    return {"archive_submissions": len(decisions), "archive_submissions_with_a_decision": int((decisions != "").sum()),
            "archive_decision_values": "; ".join(f"{value}: {count}" for value, count in values.items())}


def late_replies(replies: pd.DataFrame, year: int, first_decision: date) -> dict:
    """Author replies to a review in one year, and those created on or after the day of the first decision note."""
    of_year = replies.loc[replies["year"] == year, "tcdate"]
    late = int((of_year.map(day) >= first_decision).sum())
    return {"author_replies_to_a_review": len(of_year), "author_replies_from_first_decision_day": late,
            "share_author_replies_from_first_decision_day": late / len(of_year) if len(of_year) else float("nan")}


def main() -> int:
    cfg = load_config()
    log = setup_run_logging("05d_input_dates", cfg["paths"]["logs"])
    raw_dir, venue = cfg["paths"]["raw"], cfg["project"]["venue"]
    source = cfg["external"]["iclr_dataset"]
    versions, root = source["before_decision"], raw_dir / source["dir"]
    replies = pd.read_parquet(cfg["paths"]["interim"] / "discussion.parquet", columns=["year", "role", "target_review_id", "tcdate"])
    replies = replies[(replies["role"] == "authors") & replies["target_review_id"].notna()]
    rows = []
    for year in cfg["years"]:
        run = store.read_json(store.latest_manifest(raw_dir, "full", [year]))["years"][str(year)]
        info = store.read_json(store.year_dir(raw_dir, venue, year) / "venue.json")["info"]
        days = [found for forum_id in run["forums"]
                for found in decision_days(store.read_json(store.notes_path(raw_dir, venue, year, forum_id))["replies"], info)]
        rows.append({**row(year, days, date.fromisoformat(versions[year]["committed"])),
                     **archive_decisions(external.iclr_dataset_file(root, versions[year]), year),
                     **late_replies(replies, year, min(days))})
    table = pd.DataFrame(rows)
    table.to_csv(cfg["paths"]["tables"] / "input_dates.csv", index=False)
    log.info("dates of the decisions and of the text archive\n%s", table.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
