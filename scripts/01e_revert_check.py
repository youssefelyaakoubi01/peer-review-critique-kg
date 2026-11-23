"""What the conference-wide edits of a year did to its reviews, on a small sample.

    uv run --env-file .env python scripts/01e_revert_check.py --year 2026

ICLR 2026 reverted the reviews that had been modified during the discussion. The edit
history of a few reviews (config `collect.revert_check`: some reverted, some only
released) shows what the revert did: for every readable edit, its time, the invitation
it went through, who signed it (role only, never an identifier), and whether its
rating and text are those of the review today.

The raw edits are stored unchanged in data/raw/openreview/<venue>/<year>/edits_sample/.
Output: results/tables/feasibility_<year>_revert_check.csv.
"""

import argparse
import re
import sys

import pandas as pd

from src.collect import openreview_v2, parse, report, store
from src.collect.client import OpenReviewSession
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

TEXT_FIELDS = ("summary", "strengths", "weaknesses", "questions")


def role(signatures: list[str] | None) -> str:
    """Role of the signatory, without its identifier: Reviewer, Program_Chairs, Conference..."""
    last = (signatures or ["?"])[0].split("/")[-1]
    return re.sub(r"_[A-Za-z0-9]{4}$", "", last) if last.startswith(("Reviewer", "Area_Chair")) else last


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    cfg = load_config()
    year, venue, raw_dir, collect_cfg = args.year, cfg["project"]["venue"], cfg["paths"]["raw"], cfg["collect"]
    log = setup_run_logging(f"01e_revert_check_{year}", cfg["paths"]["logs"])
    sys.path.insert(0, str(cfg["paths"]["logs"].parent / "scripts"))
    feasibility = __import__("01d_year_feasibility")

    forums = store.read_json(store.latest_manifest(raw_dir, "full", [year]))["years"][str(year)]["forums"]
    info = store.read_json(store.year_dir(raw_dir, venue, year) / "venue.json")["info"]
    current, rows = {}, []
    for forum_id in forums:
        doc = store.read_json(store.notes_path(raw_dir, venue, year, forum_id))
        if parse.paper_status(doc, info) == "desk_rejected":
            continue
        for reply in doc["replies"]:
            if parse.reply_kind(reply, info) == "review":
                current[reply["id"]] = reply
                rows.append({"review_id": reply["id"], "tcdate": reply["tcdate"], "tmdate": reply["tmdate"]})
    reviews = pd.DataFrame(rows).sort_values("review_id").reset_index(drop=True)
    reviews["group"] = feasibility.modification_class(reviews, collect_cfg["review_events"][year])
    settings = collect_cfg["revert_check"]
    sample = pd.concat([reviews[reviews["group"] == "revert"].sample(settings["reverted"], random_state=settings["seed"]),
                        reviews[reviews["group"] == "release"].sample(settings["released"], random_state=settings["seed"])])

    session = OpenReviewSession(collect_cfg["max_requests_per_minute"], collect_cfg["max_rate_limit_wait_seconds"])
    out = []
    for item in sample.itertuples():
        path = store.year_dir(raw_dir, venue, year) / "edits_sample" / f"{item.review_id}.json.gz"
        if not path.exists():
            store.write_json(path, openreview_v2.fetch_versions(session, item.review_id))
        note = current[item.review_id]
        for edit in sorted(store.read_json(path), key=parse.version_time):
            content = parse.version_content(edit, "v2")
            same_text = [content[f] == note["content"].get(f) for f in TEXT_FIELDS if f in content]
            out.append({
                "review_id": item.review_id, "group": item.group, "review_created_utc": report.iso(item.tcdate),
                "edit_time_utc": report.iso(parse.version_time(edit)), "invitation": (edit.get("invitation") or "").split("/-/")[-1],
                "signed_by": role(edit.get("signatures")), "content_fields": len(content),
                "rating_in_edit": parse.parse_score(parse.content_value(edit.get("note") or {}, "rating")),
                "rating_today": parse.parse_score(parse.content_value(note, "rating")),
                "text_same_as_today": all(same_text) if same_text else None})
    table = pd.DataFrame(out)
    table.to_csv(cfg["paths"]["tables"] / f"feasibility_{year}_revert_check.csv", index=False)
    log.info("requests=%d reviews=%d edits=%d\n%s", session.n_requests, len(sample), len(table),
             table.drop(columns=["review_id"]).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
