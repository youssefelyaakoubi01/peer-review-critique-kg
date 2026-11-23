"""Borderline papers: those whose mean initial rating does not settle the outcome.

The zone is defined on the training papers only. The mean initial rating is cut into
bins of fixed width; a bin with enough papers is uncertain when its acceptance rate
lies between two bounds. The zone runs from the start of the first uncertain bin to
the end of the last one, and is then applied unchanged to validation and test papers.
"""

import numpy as np
import pandas as pd


def rate_table(mean_rating: np.ndarray, labels: np.ndarray, width: float, min_papers: int,
               low: float, high: float) -> pd.DataFrame:
    """Acceptance rate of the training papers per bin of mean initial rating."""
    start = np.floor(np.asarray(mean_rating, dtype=float) / width) * width
    table = pd.DataFrame({"bin_start": start, "label": np.asarray(labels, dtype=float)})
    table = table.groupby("bin_start")["label"].agg(papers="size", acceptance_rate="mean").reset_index()
    table.insert(1, "bin_end", table["bin_start"] + width)
    table["enough_papers"] = table["papers"] >= min_papers
    table["uncertain"] = table["enough_papers"] & table["acceptance_rate"].between(low, high)
    return table


def zone(table: pd.DataFrame) -> tuple[float, float]:
    """[start, end) of the borderline zone. Fails if a bin with enough papers inside
    the zone is not uncertain: the zone would not be one interval."""
    uncertain = table[table["uncertain"]]
    if uncertain.empty:
        raise ValueError("no bin of mean rating has an acceptance rate inside the bounds")
    start, end = float(uncertain["bin_start"].min()), float(uncertain["bin_end"].max())
    inside = table[(table["bin_start"] >= start) & (table["bin_end"] <= end) & table["enough_papers"]]
    if not inside["uncertain"].all():
        raise ValueError(f"the borderline zone [{start}, {end}) is not one interval:\n{inside}")
    return start, end


def training_zone(mean_rating: np.ndarray, labels: np.ndarray, settings: dict) -> tuple[pd.DataFrame, tuple[float, float]]:
    """(table of the bins, zone) from the training papers, with the settings of the config
    (`baselines.borderline`)."""
    table = rate_table(mean_rating, labels, settings["bin_width"], settings["min_papers"], settings["low"], settings["high"])
    bounds = zone(table)
    table["in_zone"] = (table["bin_start"] >= bounds[0]) & (table["bin_end"] <= bounds[1])
    return table, bounds


def subsets(mean_rating: np.ndarray, text_available: np.ndarray, bounds: tuple[float, float]) -> dict[str, np.ndarray]:
    """Masks of the subsets of papers every metric is reported on."""
    inside = in_zone(mean_rating, bounds)
    return {"all": np.ones(len(inside), dtype=bool), "borderline": inside, "with_text": text_available,
            "borderline_with_text": inside & text_available}


def in_zone(mean_rating: np.ndarray, bounds: tuple[float, float]) -> np.ndarray:
    mean_rating = np.asarray(mean_rating, dtype=float)
    return (mean_rating >= bounds[0]) & (mean_rating < bounds[1])
