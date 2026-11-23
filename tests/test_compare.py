"""Comparison of models from their stored predictions (src/eval/compare.py)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from src.eval import compare

SETTINGS = {"n_resamples": 200, "seed": 0, "confidence": 0.95}


def predictions(n=300, seeds=(0, 1)):
    rng = np.random.default_rng(0)
    labels = rng.integers(0, 2, size=n)
    borderline = rng.random(n) < 0.4
    rows = []
    for model, noise in (("good", 0.8), ("weak", 2.5)):
        for seed in seeds:
            probability = 1 / (1 + np.exp(-(labels - 0.5 + noise * np.random.default_rng(seed + 10 * len(model)).normal(size=n))))
            rows.append(pd.DataFrame({"model": model, "setting": "A", "seed": seed, "forum_id": [f"f{i}" for i in range(n)], "split": "test",
                                      "label": labels, "probability": probability, "borderline": borderline, "text_available": True}))
    return pd.concat(rows, ignore_index=True)


def test_metrics_are_computed_per_model_seed_and_subset():
    table = predictions()
    by_seed = compare.by_seed_metrics(table)
    assert len(by_seed) == 2 * 2 * len(compare.SUBSETS)
    row = by_seed[(by_seed["model"] == "good") & (by_seed["seed"] == 1) & (by_seed["subset"] == "borderline")].iloc[0]
    chosen = table[(table["model"] == "good") & (table["seed"] == 1) & table["borderline"]]
    assert row["n_papers"] == len(chosen) and row["auc"] == pytest.approx(roc_auc_score(chosen["label"], chosen["probability"]))
    everyone = by_seed[by_seed["subset"] == "all"]
    assert (everyone["n_papers"] == 300).all()
    assert by_seed.loc[by_seed["subset"] == "with_text", "auc"].tolist() == everyone["auc"].tolist()  # every paper has text here


def test_two_models_are_compared_on_the_same_resampled_papers():
    table = predictions()
    models = [("good", "A"), ("weak", "A")]
    papers, labels, matrices, samples = compare.bootstrap(table, "borderline", models, SETTINGS)
    assert len(papers) == int(table.drop_duplicates("forum_id")["borderline"].sum()) == len(labels)
    assert matrices[models[0]].shape == (2, len(papers)) and samples[models[0]].shape[0] == 200
    # columns follow the papers, whatever the order of the rows of the table
    shuffled = table.sample(frac=1.0, random_state=1)
    assert np.array_equal(compare.seed_matrix(shuffled, "good", "A", papers.index), matrices[models[0]])
    result = compare.versus(labels, matrices, samples, models[0], models[1], 0.95)
    assert result["difference"] == pytest.approx(compare.mean_auc(labels, matrices[models[0]]) - compare.mean_auc(labels, matrices[models[1]]))
    assert result["ci_low"] < result["difference"] < result["ci_high"] and result["ci_low"] > 0 and result["delong_p"] < 0.05
    reverse = compare.versus(labels, matrices, samples, models[1], models[0], 0.95)
    assert reverse["difference"] == pytest.approx(-result["difference"]) and reverse["ci_high"] == pytest.approx(-result["ci_low"])
