"""Averages over the explained articles, with bootstrap intervals.

The sample has the same number of articles in each group (stratum), which is not their
share of the test year: every article is weighted by the size of its group divided by
the number of its articles in the sample, and the bootstrap draws inside each group.
"""

import numpy as np

from src.eval import stats


def weights(strata: np.ndarray, populations: np.ndarray) -> np.ndarray:
    """Weight of each article: population of its stratum / articles of the stratum in the sample."""
    strata = np.asarray(strata, dtype=object)
    sizes = {name: int((strata == name).sum()) for name in set(strata)}
    return np.asarray(populations, dtype=float) / np.array([sizes[name] for name in strata], dtype=float)


def bootstrap_counts(strata: np.ndarray, n_resamples: int, seed: int) -> np.ndarray:
    """[resample, article]: how many times each article is drawn, resampling inside each stratum."""
    strata = np.asarray(strata, dtype=object)
    rng = np.random.default_rng(seed)
    counts = np.zeros((n_resamples, len(strata)), dtype=np.float64)
    for name in sorted(set(strata)):
        members = np.flatnonzero(strata == name)
        counts[:, members] = rng.multinomial(len(members), np.full(len(members), 1 / len(members)), size=n_resamples)
    return counts


def ratio(numerator: np.ndarray, denominator: np.ndarray, weight: np.ndarray, counts: np.ndarray,
          confidence: float) -> tuple[float, float, float]:
    """(weighted sum of `numerator` / weighted sum of `denominator`, low, high): one value
    per article in each array; an article outside the group has zeros in both. nan when
    the denominator is zero."""
    top, bottom = weight * numerator, weight * denominator
    if bottom.sum() == 0:
        return float("nan"), float("nan"), float("nan")
    with np.errstate(invalid="ignore", divide="ignore"):
        samples = (counts @ top) / (counts @ bottom)
    return (float(top.sum() / bottom.sum()), *stats.interval(samples, confidence))
