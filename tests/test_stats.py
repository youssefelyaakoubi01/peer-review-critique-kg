"""DeLong test and bootstrap confidence intervals."""

import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

from src.eval import stats
from src.eval.metrics import METRICS, classification_metrics


def direct_delong(labels, a, b):
    """DeLong et al. (1988) written from the definition, with every pair compared."""
    positive = labels.astype(bool)
    parts = []
    for scores in (a, b):
        x, y = scores[positive], scores[~positive]
        psi = (x[:, None] > y[None, :]) + 0.5 * (x[:, None] == y[None, :])
        parts.append((psi.mean(), psi.mean(axis=1), psi.mean(axis=0)))
    s10 = np.cov(np.stack([p[1] for p in parts]))
    s01 = np.cov(np.stack([p[2] for p in parts]))
    s = s10 / positive.sum() + s01 / (~positive).sum()
    difference = parts[0][0] - parts[1][0]
    return difference, difference / np.sqrt(s[0, 0] + s[1, 1] - 2 * s[0, 1])


def sample(seed, n=300, ties=False):
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, 2, size=n)
    a = labels + rng.normal(size=n)
    b = labels + rng.normal(size=n) * 1.5
    if ties:
        a, b = np.round(a), np.round(b)
    return labels, a, b


@pytest.mark.parametrize("ties", [False, True])
def test_delong_agrees_with_the_definition(ties):
    labels, a, b = sample(0, ties=ties)
    result = stats.delong(labels, a, b)
    difference, z = direct_delong(labels, a, b)
    assert result["auc_a"] == pytest.approx(roc_auc_score(labels, a)) and result["auc_b"] == pytest.approx(roc_auc_score(labels, b))
    assert result["difference"] == pytest.approx(difference) and result["z"] == pytest.approx(z)
    assert 0 < result["p_value"] < 1


def test_delong_is_symmetric_and_does_not_reject_equal_models():
    labels, a, b = sample(1)
    forward, backward = stats.delong(labels, a, b), stats.delong(labels, b, a)
    assert forward["z"] == pytest.approx(-backward["z"]) and forward["p_value"] == pytest.approx(backward["p_value"])
    same = stats.delong(labels, a, a)
    assert same["difference"] == 0 and np.isnan(same["p_value"])
    # a much better score is detected
    strong = stats.delong(labels, labels + 0.1 * np.random.default_rng(2).normal(size=len(labels)), b)
    assert strong["p_value"] < 1e-6 and strong["difference"] > 0


def test_delong_keeps_its_level_when_the_two_scores_are_equally_good():
    rejections = 0
    for seed in range(200):
        rng = np.random.default_rng(seed)
        labels = rng.integers(0, 2, size=200)
        a, b = labels + rng.normal(size=200), labels + rng.normal(size=200)
        rejections += stats.delong(labels, a, b)["p_value"] < 0.05
    assert rejections / 200 < 0.12  # nominal level 0.05


def test_bootstrap_metrics_average_the_seeds_and_their_interval_holds_the_estimate():
    labels, a, b = sample(3, n=400)
    probabilities = np.stack([1 / (1 + np.exp(-a)), 1 / (1 + np.exp(-b))])  # two "seeds"
    indices = stats.resamples(len(labels), 200, seed=0)
    assert indices.shape == (200, 400) and np.array_equal(indices, stats.resamples(len(labels), 200, seed=0))
    samples = stats.bootstrap_metrics(labels, probabilities, indices)
    assert samples.shape == (200, len(METRICS))
    first = indices[0]
    expected = np.mean([classification_metrics(labels[first], p[first])["auc"] for p in probabilities])
    assert samples[0, 0] == pytest.approx(expected)
    estimate = np.mean([classification_metrics(labels, p)["auc"] for p in probabilities])
    low, high = stats.interval(samples[:, 0], 0.95)
    assert low < estimate < high and 0.02 < high - low < 0.15
    assert stats.interval(np.arange(101.0), 0.9) == pytest.approx((5.0, 95.0))


def test_holm_adjusts_a_family_by_hand():
    # sorted: 0.01, 0.02, 0.03, 0.04 -> x4, x3, x2, x1 = 0.04, 0.06, 0.06, 0.04 -> made non-decreasing: 0.04, 0.06, 0.06, 0.06
    adjusted = stats.holm(np.array([0.03, 0.01, 0.04, 0.02]))
    assert adjusted == pytest.approx([0.06, 0.04, 0.06, 0.06])
    assert stats.holm(np.array([0.5, 0.9])) == pytest.approx([1.0, 1.0])  # capped at one
    assert stats.holm(np.array([0.2])) == pytest.approx([0.2])            # a family of one test is unchanged


def test_holm_leaves_missing_tests_out_of_the_family():
    adjusted = stats.holm(np.array([0.01, np.nan, 0.03]))
    assert adjusted[[0, 2]] == pytest.approx([0.02, 0.03]) and np.isnan(adjusted[1])
    assert len(stats.holm(np.array([]))) == 0
    # never below the raw p-value, and the order of the tests is kept
    raw = np.random.default_rng(0).random(50)
    adjusted = stats.holm(raw)
    assert (adjusted >= raw).all() and (np.diff(adjusted[np.argsort(raw)]) >= 0).all()
