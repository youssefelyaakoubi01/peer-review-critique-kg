"""Anti-leakage guard: reject model inputs that contain forbidden fields."""

from collections.abc import Iterable


def find_forbidden_fields(columns: Iterable[str], forbidden: Iterable[str]) -> list[str]:
    """Return the names in `columns` that match a forbidden field (case-insensitive)."""
    forbidden_lower = {f.lower() for f in forbidden}
    return sorted(c for c in columns if c.lower() in forbidden_lower)


def assert_no_forbidden_fields(columns: Iterable[str], forbidden: Iterable[str]) -> None:
    """Raise ValueError if any forbidden field is present in `columns`."""
    leaked = find_forbidden_fields(columns, forbidden)
    if leaked:
        raise ValueError(f"leakage: forbidden fields in model inputs: {leaked}")
