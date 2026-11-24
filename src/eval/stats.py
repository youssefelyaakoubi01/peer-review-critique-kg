"""Statistical comparison of models on the same test papers: bootstrap confidence
intervals and the DeLong test for two correlated AUCs.

DeLong, DeLong and Clarke-Pearson (1988), computed with the mid-rank formulation of
Sun and Xu (2014).
"""

import numpy as np
from scipy import stats

from src.eval.metrics import METRICS, classification_metrics


def placements(positives: np.ndarray, negatives: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """(AUC, V10, V01): for each positive, the share of negatives it is ranked above
    (ties count for one half); for each negative, the share of positives ranked above it."""
    m, n = len(positives), len(negatives)
    both = stats.rankdata(np.concatenate([positives, negatives]))
    v10 = (both[:m] - stats.rankdata(positives)) / n
    v01 = 1.0 - (both[m:] - stats.rankdata(negatives)) / m
    return float(v10.mean()), v10, v01


def delong(labels: np.ndarray, scores_a: np.ndarray, scores_b: np.ndarray) -> dict[str, float]:
    """Two-sided test of AUC(a) = AUC(b) for two scores of the same papers."""
    labels = np.asarray(labels).astype(bool)
    parts = [placements(np.asarray(s, dtype=float)[labels], np.asarray(s, dtype=float)[~labels]) for s in (scores_a, scores_b)]
    covariance = np.cov(np.stack([p[1] for p in parts])) / labels.sum() + np.cov(np.stack([p[2] for p in parts])) / (~labels).sum()
    difference = parts[0][0] - parts[1][0]
    variance = covariance[0, 0] + covariance[1, 1] - 2 * covariance[0, 1]
    if variance <= 0:  # the two scores rank the papers in the same way
        return {"auc_a": parts[0][0], "auc_b": parts[1][0], "difference": difference, "z": float("nan"), "p_value": float("nan")}
    z = difference / np.sqrt(variance)
    return {"auc_a": parts[0][0], "auc_b": parts[1][0], "difference": difference, "z": float(z),
            "p_value": float(2 * stats.norm.sf(abs(z)))}


def holm(p_values: np.ndarray) -> np.ndarray:
    """Holm step-down adjustment of the p-values of one family of tests (Holm, 1979).

    The i-th smallest of m p-values is multiplied by m - i + 1, the adjusted values are
    made non-decreasing in that order and capped at one. A missing p-value (a test that
    could not be computed) stays missing and is not counted in the family.
    """
    p_values = np.asarray(p_values, dtype=float)
    adjusted = np.full(p_values.shape, np.nan)
    known = np.flatnonzero(~np.isnan(p_values))
    order = known[np.argsort(p_values[known], kind="stable")]
    scaled = p_values[order] * (len(order) - np.arange(len(order)))
    adjusted[order] = np.minimum(np.maximum.accumulate(scaled), 1.0)
    return adjusted


def resamples(n: int, n_resamples: int, seed: int) -> np.ndarray:
    """Indices of `n_resamples` bootstrap samples of `n` papers (one row each)."""
    return np.random.default_rng(seed).integers(0, n, size=(n_resamples, n))


def bootstrap_metrics(labels: np.ndarray, probabilities: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """Metrics of each bootstrap sample, averaged over the seeds of a model.

    `probabilities`: one row per seed. Returns an array (samples, metrics), metrics in
    the order of `METRICS`.
    """
    out = np.empty((len(indices), len(METRICS)))
    for row, sample in enumerate(indices):
        values = [classification_metrics(labels[sample], seed_probabilities[sample]) for seed_probabilities in probabilities]
        out[row] = [np.mean([v[metric] for v in values]) for metric in METRICS]
    return out


def interval(samples: np.ndarray, confidence: float = 0.95) -> tuple[float, float]:
    """Percentile interval of bootstrap values."""
    tail = (1 - confidence) / 2 * 100
    low, high = np.nanpercentile(samples, [tail, 100 - tail])
    return float(low), float(high)
