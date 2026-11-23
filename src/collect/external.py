"""External sources.

1. Pre-rebuttal review scores: papercopilot/iclr-insights.

Scores archived by its authors when ICLR 2024 and 2025 reviews were released
(arXiv:2511.15462), shared under CC BY 4.0. One record per paper:

    {"id": <OpenReview forum id>, "title": ..., "tracing_score": <int or Infinity>,
     "review": {<4-character reviewer key>: {"rating": "initial;post", ...}}}

The reviewer key is the suffix of the anonymous OpenReview signature
(".../Submission123/Reviewer_Kha2" -> "Kha2"), which is how a score pair is
attached to one of our reviews. Only numeric scores are available: no text.

2. Text of the submissions before the decisions: berenslab/iclr-dataset
(arXiv:2404.08403), scraped while the submissions were anonymous. Only the year, the
OpenReview id, the title, the abstract and the keywords are read: the author columns
of these files are never loaded.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

REVIEWER_PREFIX = "Reviewer_"


def parse_pair(value: Any) -> tuple[int | None, int | None]:
    """ "3;5" -> (3, 5): score before and after the rebuttal."""
    parts = str(value).split(";")
    if len(parts) != 2:
        return None, None

    def to_int(text: str) -> int | None:
        try:
            return int(float(text))
        except ValueError:
            return None

    return to_int(parts[0]), to_int(parts[1])


def load_iclr_insights(path: Path) -> dict[str, dict[str, Any]]:
    """Records keyed by forum id; each score becomes an (initial, post) pair of integers."""
    with open(path, encoding="utf-8") as f:
        records = json.load(f)  # the file uses the non-standard token Infinity
    papers = {}
    for record in records:
        papers[record["id"]] = {
            "tracing_score": record.get("tracing_score"),
            "reviews": {
                key: {field: parse_pair(value) for field, value in scores.items()}
                for key, scores in (record.get("review") or {}).items()
            },
        }
    return papers


def reviewer_key(reply: dict[str, Any]) -> str | None:
    """Anonymous reviewer id of a review note, without its "Reviewer_" prefix."""
    for signature in reply.get("signatures") or []:
        name = signature.rsplit("/", 1)[-1]
        if name.startswith(REVIEWER_PREFIX):
            return name[len(REVIEWER_PREFIX):]
    return None


def join_review(
    external: dict[str, dict[str, Any]], forum_id: str, reply: dict[str, Any]
) -> dict[str, Any]:
    """External score pairs for one of our reviews (empty fields if there is no match)."""
    paper = external.get(forum_id)
    scores = None if paper is None else paper["reviews"].get(reviewer_key(reply) or "")
    row: dict[str, Any] = {
        "paper_in_external": paper is not None,
        "matched": scores is not None,
        "tracing_score": None if paper is None else paper["tracing_score"],
        "ext_rating_initial": None,
        "ext_rating_post": None,
        "ext_confidence_initial": None,
        "ext_confidence_post": None,
        "ext_any_score_changed": None,
    }
    if scores is not None:
        row["ext_rating_initial"], row["ext_rating_post"] = scores.get("rating", (None, None))
        row["ext_confidence_initial"], row["ext_confidence_post"] = scores.get(
            "confidence", (None, None)
        )
        row["ext_any_score_changed"] = any(a != b for a, b in scores.values())
    return row


# --------------------------------------------------------------------------- iclr-dataset
ICLR_DATASET_COLUMNS = ["year", "id", "title", "abstract", "keywords"]  # never the authors


def iclr_dataset_file(root: Path, version: dict[str, Any]) -> Path:
    """Local copy of one version of a data file: <root>/files/<name>_<commit>.parquet."""
    name = Path(version["path"]).name.split(".")[0]
    return root / "files" / f"{name}_{version['commit'][:7]}.parquet"


def fetch_iclr_dataset(root: Path, url: str, versions: list[dict[str, Any]]) -> None:
    """Clone the repository (once) and extract the data files at the pinned commits."""
    repo = root / "repo"
    if not repo.exists():
        root.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", url, str(repo)], check=True)
    for version in versions:
        target = iclr_dataset_file(root, version)
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.run(["git", "-C", str(repo), "show", f"{version['commit']}:{version['path']}"],
                              check=True, capture_output=True).stdout
        target.write_bytes(blob)


def load_iclr_dataset(path: Path, year: int) -> pd.DataFrame:
    """Submissions of one year: forum_id, title, abstract, keywords (list of strings)."""
    table = pd.read_parquet(path, columns=ICLR_DATASET_COLUMNS)
    table = table[table["year"] == year].drop(columns=["year"]).rename(columns={"id": "forum_id"})
    table["keywords"] = table["keywords"].map(lambda ks: [str(k).strip() for k in (ks if ks is not None else []) if str(k).strip()])
    if table["forum_id"].duplicated().any():
        raise ValueError(f"{path.name}: a submission of {year} appears twice")
    return table.reset_index(drop=True)
