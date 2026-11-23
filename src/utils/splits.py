"""Split assignment: by conference year, validation carved out of the training years."""

import hashlib
from typing import Any


def validation_score(forum_id: str, salt: str) -> float:
    """Deterministic pseudo-uniform number in [0, 1) derived from the submission id."""
    digest = hashlib.sha256(f"{salt}:{forum_id}".encode()).hexdigest()
    return int(digest[:16], 16) / 16**16


def assign_split(forum_id: str, year: int, splits: dict[str, Any]) -> str:
    """ "train", "val", "test" or "holdout" for one submission.

    Test and holdout years are never mixed with training years. Within the training
    years, a fixed fraction of submissions goes to validation; the assignment only
    depends on the submission id and the salt, never on a random seed.
    """
    if year in splits.get("holdout", []):
        return "holdout"
    if year in splits["test"]:
        return "test"
    if year in splits["train"]:
        validation = splits["validation"]
        in_val = validation_score(forum_id, validation["salt"]) < validation["fraction"]
        return "val" if in_val else "train"
    raise ValueError(f"year {year} is not covered by the splits")
