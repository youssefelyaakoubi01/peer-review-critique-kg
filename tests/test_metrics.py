"""Metrics, their summary over seeds, and the borderline zone."""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef, roc_auc_score

from src.eval import borderline, metrics


# --------------------------------------------------------------------------- metrics
def test_calibration_error_on_a_case_computed_by_hand():
    labels, probabilities = np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9])
    # two bins: mean probability 0.15 against a rate of 0, 0.85 against a rate of 1
    assert metrics.expected_calibration_error(labels, probabilities, n_bins=2) == pytest.approx(0.15)
    # a perfectly calibrated constant prediction
    assert metrics.expected_calibration_error(np.array([0, 1, 0, 1]), np.full(4, 0.5)) == pytest.approx(0.0)
    # a probability of exactly 1 falls in the last bin
    assert metrics.expected_calibration_error(np.array([1, 0]), np.array([1.0, 0.0]), n_bins=15) == pytest.approx(0.0)


def test_metrics_agree_with_scikit_learn():
    rng = np.random.default_rng(0)
    labels = rng.integers(0, 2, size=500)
    probabilities = np.clip(labels * 0.3 + rng.random(500) * 0.7, 0, 1)
    predicted = (probabilities >= 0.5).astype(int)
    result = metrics.classification_metrics(labels, probabilities)
    assert set(result) == set(metrics.METRICS)
    assert result["auc"] == pytest.approx(roc_auc_score(labels, probabilities))
    assert result["macro_f1"] == pytest.approx(f1_score(labels, predicted, average="macro"))
    assert result["mcc"] == pytest.approx(matthews_corrcoef(labels, predicted))
    assert result["accuracy"] == pytest.approx(accuracy_score(labels, predicted))


def test_a_constant_prediction_has_no_ranking_power():
    labels = np.array([0, 0, 0, 1, 1])
    result = metrics.classification_metrics(labels, np.full(5, 0.4))
    assert result["auc"] == 0.5 and result["mcc"] == 0.0
    assert result["accuracy"] == pytest.approx(0.6)  # everything predicted rejected
    assert result["ece"] == pytest.approx(0.0)
    assert metrics.classification_metrics(labels, np.full(5, 0.5))["accuracy"] == pytest.approx(0.4)  # 0.5 counts as accepted


def test_auc_is_missing_when_one_class_is_absent():
    result = metrics.classification_metrics(np.array([1, 1, 1]), np.array([0.2, 0.6, 0.9]))
    assert np.isnan(result["auc"]) and result["accuracy"] == pytest.approx(2 / 3)
    assert all(np.isnan(value) for value in metrics.classification_metrics(np.array([]), np.array([])).values())


def by_seed_table():
    rows = []
    for model, values in {"a": [0.70, 0.72, 0.74], "b": [0.5, 0.5, 0.5]}.items():
        for seed, auc in enumerate(values):
            rows.append({"model": model, "split": "test", "seed": seed, "n_papers": 10, "auc": auc, "macro_f1": auc,
                         "mcc": auc, "accuracy": auc, "ece": 1 - auc})
    return pd.DataFrame(rows)


def test_summary_is_the_mean_and_sample_standard_deviation_over_seeds():
    summary = metrics.summarise(by_seed_table(), ["model", "split"]).set_index("model")
    assert summary.at["a", "auc_mean"] == pytest.approx(0.72) and summary.at["a", "auc_std"] == pytest.approx(0.02)
    assert summary.at["b", "auc_std"] == 0.0 and summary.at["a", "n_seeds"] == 3 and summary.at["a", "n_papers"] == 10
    table = by_seed_table()
    table.loc[0, "n_papers"] = 11  # the papers evaluated cannot change with the seed
    with pytest.raises(ValueError, match="varies between seeds"):
        metrics.summarise(table, ["model", "split"])


def test_latex_table_writes_what_the_summary_holds():
    summary = metrics.summarise(by_seed_table(), ["model", "split"])
    summary["model"] = ["scores_lr", "majority"]
    text = metrics.latex_table(summary, "model", {"majority": "Majority class"}, "Caption.", "tab:x",
                               group="split", group_labels={"test": "Test papers"})
    assert r"\toprule" in text and r"\bottomrule" in text and r"\label{tab:x}" in text
    assert r"scores\_lr & $0.720 \pm 0.020$" in text and r"Majority class & $0.500 \pm 0.000$" in text
    assert r"\emph{Test papers} ($n = 10$)" in text


# --------------------------------------------------------------------------- borderline zone
def rating_sample():
    # (mean rating, number of papers, number accepted)
    bins = [(3.0, 40, 0), (4.5, 40, 4), (5.0, 40, 12), (5.25, 40, 20), (5.5, 40, 30), (6.0, 40, 36), (7.0, 5, 2)]
    ratings = np.concatenate([np.full(n, rating) for rating, n, _ in bins])
    labels = np.concatenate([np.r_[np.ones(k), np.zeros(n - k)] for _, n, k in bins])
    return ratings, labels


def test_the_zone_covers_the_bins_whose_acceptance_rate_is_uncertain():
    ratings, labels = rating_sample()
    table = borderline.rate_table(ratings, labels, width=0.25, min_papers=20, low=0.2, high=0.8)
    assert table.set_index("bin_start")["acceptance_rate"].loc[5.0] == pytest.approx(0.3)
    # 7.0 has a rate of 0.4 but only 5 papers: it does not count
    assert table.loc[table["uncertain"], "bin_start"].tolist() == [5.0, 5.25, 5.5]
    assert borderline.zone(table) == (5.0, 5.75)
    assert borderline.in_zone(np.array([4.99, 5.0, 5.6, 5.75, 7.0]), (5.0, 5.75)).tolist() == [False, True, True, False, False]


def test_the_zone_must_be_one_interval():
    ratings, labels = rating_sample()
    labels = labels.copy()
    labels[ratings == 5.25] = 1  # a certain bin between two uncertain ones
    table = borderline.rate_table(ratings, labels, width=0.25, min_papers=20, low=0.2, high=0.8)
    with pytest.raises(ValueError, match="not one interval"):
        borderline.zone(table)
    with pytest.raises(ValueError, match="no bin"):
        borderline.zone(borderline.rate_table(ratings, np.zeros(len(ratings)), 0.25, 20, 0.2, 0.8))
