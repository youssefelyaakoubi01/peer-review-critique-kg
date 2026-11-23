"""Load and validate the YAML configuration."""

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "default.yaml"

N_SEEDS = 5


def validate_config(cfg: dict[str, Any]) -> None:
    """Raise ValueError if the config breaks a project rule (splits, seeds)."""
    years = cfg["years"]
    splits = cfg["splits"]

    if set(splits) - {"holdout"} != {"train", "test", "validation"}:
        raise ValueError(f"splits must define train, test and validation (and may define holdout), got {sorted(splits)}")
    train, test, holdout = splits["train"], splits["test"], splits.get("holdout", [])
    if not train or not test:
        raise ValueError("train and test must each contain at least one year")
    if len(set(train) | set(test) | set(holdout)) != len(train) + len(test) + len(holdout):
        raise ValueError("a year appears in several splits")
    if set(train) | set(test) | set(holdout) != set(years):
        raise ValueError("splits must cover exactly the configured years")
    # Temporal order: training years, then test years, then holdout years.
    if not max(train) < min(test):
        raise ValueError("test years must come strictly after training years")
    if holdout and not max(test) < min(holdout):
        raise ValueError("holdout years must come strictly after test years")

    validation = splits["validation"]
    if not 0 < validation["fraction"] < 0.5:
        raise ValueError("validation.fraction must be in (0, 0.5)")
    if not isinstance(validation["salt"], str) or not validation["salt"]:
        raise ValueError("validation.salt must be a non-empty string")

    seeds = cfg["seeds"]
    if len(seeds) != N_SEEDS or len(set(seeds)) != N_SEEDS:
        raise ValueError(f"exactly {N_SEEDS} distinct seeds are required, got {seeds}")


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Read a YAML config, validate it and resolve paths against the repo root."""
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    validate_config(cfg)
    cfg["paths"] = {k: REPO_ROOT / v for k, v in cfg["paths"].items()}
    return cfg
