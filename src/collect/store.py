"""Raw data layout, atomic writes and resumability.

data/raw/openreview/ICLR/{year}/
    venue.json                  API version, invitation names, venue group
    notes/{forum_id}.json.gz    submission + replies in their current (final) state
    history/{forum_id}.json.gz  every version of the submission and of each review
data/raw/openreview/manifests/{tag}_{timestamp}.json   one file per run

A forum is complete when its history file exists (it is written last).
"""

import gzip
import json
import os
from pathlib import Path
from typing import Any


def write_json(path: Path, obj: Any) -> None:
    """Atomic write (temporary file + rename); gzip if the name ends with .gz."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(tmp, "wt", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def openreview_root(raw_dir: Path) -> Path:
    return raw_dir / "openreview"


def year_dir(raw_dir: Path, venue: str, year: int) -> Path:
    return openreview_root(raw_dir) / venue / str(year)


def notes_path(raw_dir: Path, venue: str, year: int, forum_id: str) -> Path:
    return year_dir(raw_dir, venue, year) / "notes" / f"{forum_id}.json.gz"


def history_path(raw_dir: Path, venue: str, year: int, forum_id: str) -> Path:
    return year_dir(raw_dir, venue, year) / "history" / f"{forum_id}.json.gz"


def is_complete(raw_dir: Path, venue: str, year: int, forum_id: str) -> bool:
    return (
        notes_path(raw_dir, venue, year, forum_id).exists()
        and history_path(raw_dir, venue, year, forum_id).exists()
    )


def manifest_dir(raw_dir: Path) -> Path:
    return openreview_root(raw_dir) / "manifests"


def latest_manifest(raw_dir: Path, tag: str, years: list[int] | None = None) -> Path:
    """Most recent manifest of a run tag (timestamps sort lexicographically).

    With `years`, the most recent one that covers all of them: years are collected in
    separate runs, and each run only lists its own years.
    """
    candidates = sorted(manifest_dir(raw_dir).glob(f"{tag}_*.json"))
    if years is not None:
        wanted = {str(year) for year in years}
        candidates = [path for path in candidates if wanted <= set(read_json(path)["years"])]
    if not candidates:
        covering = "" if years is None else f" covering {sorted(years)}"
        raise FileNotFoundError(f"no manifest with tag '{tag}'{covering} in {manifest_dir(raw_dir)}")
    return candidates[-1]
