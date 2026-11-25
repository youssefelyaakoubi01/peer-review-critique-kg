"""Hyper-parameter search with a fixed budget, and a record of training runs that
survives an interruption (protocol checks, scripts/07f_protocol_checks.py).

A space lists the values of each hyper-parameter. A budget smaller than the number of
combinations draws that many of them without replacement, with a seed: every family of
models gets the same number of configurations, whatever the size of its space.
"""

import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.models.baselines import grid


def sample_configurations(space: dict[str, list], budget: int | None, seed: int) -> list[dict[str, Any]]:
    """`budget` configurations of `space`, drawn without replacement; the whole space if
    it holds no more than `budget` configurations (or if `budget` is None)."""
    every = grid({"grid": space})
    if budget is None or budget >= len(every):
        return every
    return random.Random(seed).sample(every, budget)


def best_first(scores: list[float], top: int) -> list[int]:
    """Indices of the `top` highest scores, best first. A missing score (a run that
    failed) is never kept; on a tie, the configuration drawn first comes first."""
    values = np.asarray(scores, dtype=float)
    order = [int(i) for i in np.argsort(-np.where(np.isnan(values), -np.inf, values), kind="stable") if not np.isnan(values[i])]
    return order[:top]


def at_edge(params: dict[str, Any], space: dict[str, list]) -> list[str]:
    """Hyper-parameters whose chosen value is the smallest or the largest of their space
    (a space with one value has no edge)."""
    return [name for name, values in space.items() if len(values) > 1 and params[name] in (min(values), max(values))]


def named_configurations(model: str, base: dict[str, Any], cells: dict[str, dict[str, Any]],
                         stored: bool = False) -> dict[str, dict[str, Any]]:
    """Configurations fixed in advance, one per cell of a design: {"<model>_<cell>": the
    values of the cell, then those of `base`}. A cell marked `stored` was trained by
    another stage: it is left out, or it is the only kind returned when `stored` is set.
    A cell may not change a value of `base`, and two cells may not be the same configuration."""
    named = {}
    for cell, values in cells.items():
        own = {key: value for key, value in values.items() if key != "stored"}
        if set(own) & set(base):
            raise ValueError(f"cell {cell} changes a value of the base: {sorted(set(own) & set(base))}")
        if bool(values.get("stored", False)) == stored:
            named[f"{model}_{cell}"] = {**{key: own[key] for key in own if key != "weight_decay"}, **base,
                                        **({"weight_decay": own["weight_decay"]} if "weight_decay" in own else {})}
    every = [json.dumps({key: value for key, value in values.items() if key != "stored"}, sort_keys=True) for values in cells.values()]
    if len(set(every)) != len(every):
        raise ValueError("two cells of the design are the same configuration")
    return named


class Records:
    """Training runs already made, one row each, written to a CSV file after every run.
    A run is identified by the columns `key`; the hyper-parameters are stored as JSON."""

    def __init__(self, path: Path, key: list[str]):
        self.path, self.key = Path(path), key
        self.rows: list[dict[str, Any]] = pd.read_csv(self.path).to_dict("records") if self.path.exists() else []

    @staticmethod
    def identity(row: dict[str, Any], key: list[str]) -> tuple:
        return tuple(json.dumps(row[k], sort_keys=True) if isinstance(row[k], dict) else str(row[k]) for k in key)

    def find(self, row: dict[str, Any], failed: bool = False) -> dict[str, Any] | None:
        """The successful run with the key of `row`, if there is one. `failed`: a run that
        failed is returned as well (a configuration of a search that ran out of memory is
        part of the result of that search: it is not tried a second time)."""
        wanted = self.identity(row, self.key)
        for record in self.rows:
            if (failed or record.get("status") == "ok") and self.identity(record, self.key) == wanted:
                return record
        return None

    def add(self, row: dict[str, Any]) -> dict[str, Any]:
        """Record a run (a run with the same key is replaced) and write the file."""
        stored = {k: json.dumps(v, sort_keys=True) if isinstance(v, dict) else v for k, v in row.items()}
        wanted = self.identity(stored, self.key)
        self.rows = [record for record in self.rows if self.identity(record, self.key) != wanted] + [stored]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(self.rows).to_csv(self.path, index=False)
        return stored

    def seconds(self, **where: Any) -> list[float]:
        """Durations of the recorded runs whose columns have the given values."""
        return [float(r["seconds"]) for r in self.rows if all(str(r.get(k)) == str(v) for k, v in where.items())]
