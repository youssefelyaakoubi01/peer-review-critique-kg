"""Comparison of models from their stored predictions: metrics per seed, paired
bootstrap over the papers, AUC difference between two models.

A table of predictions has one row per (model, setting, seed, paper): columns model,
setting, seed, forum_id, split, label, probability, borderline, text_available.
"""

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from src.eval import metrics, stats

SUBSETS = {"all": lambda t: np.ones(len(t), dtype=bool), "borderline": lambda t: t["borderline"].to_numpy(),
           "with_text": lambda t: t["text_available"].to_numpy(),
           "borderline_with_text": lambda t: (t["borderline"] & t["text_available"]).to_numpy()}


def by_seed_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, setting, seed, split), table in predictions.groupby(["model", "setting", "seed", "split"], sort=False):
        for subset, mask in SUBSETS.items():
            chosen = table[mask(table)]
            rows.append({"model": model, "setting": setting, "seed": seed, "split": split, "subset": subset, "n_papers": len(chosen),
                         "n_accepted": int(chosen["label"].sum()),
                         **metrics.classification_metrics(chosen["label"].to_numpy(), chosen["probability"].to_numpy())})
    return pd.DataFrame(rows)


def seed_matrix(predictions: pd.DataFrame, model: str, setting: str, papers: pd.Index) -> np.ndarray:
    """Probabilities of one model, one row per seed, columns in the order of `papers`."""
    table = predictions[(predictions["model"] == model) & (predictions["setting"] == setting)]
    wide = table.pivot(index="seed", columns="forum_id", values="probability")
    return wide[papers].to_numpy()


def mean_auc(labels: np.ndarray, matrix: np.ndarray) -> float:
    """AUC averaged over the seeds (rows of `matrix`)."""
    return float(np.mean([metrics.classification_metrics(labels, p)["auc"] for p in matrix]))


def bootstrap(predictions: pd.DataFrame, subset: str, models: list[tuple[str, str]], settings: dict) -> tuple:
    """(papers of the subset, labels, probabilities per model [seeds x papers], bootstrap
    samples per model [resamples x metrics]). Every model is resampled with the same papers."""
    papers = predictions.drop_duplicates("forum_id").set_index("forum_id")
    papers = papers[SUBSETS[subset](papers)]
    labels = papers["label"].to_numpy()
    indices = stats.resamples(len(papers), settings["n_resamples"], settings["seed"])
    matrices = {key: seed_matrix(predictions, *key, papers.index) for key in models}
    samples = dict(zip(models, Parallel(n_jobs=-1)(delayed(stats.bootstrap_metrics)(labels, matrices[key], indices) for key in models)))
    return papers, labels, matrices, samples


def versus(labels: np.ndarray, matrices: dict, samples: dict, key: tuple[str, str], other: tuple[str, str], confidence: float) -> dict:
    """AUC of `key` minus AUC of `other`: difference of the seed means, paired bootstrap
    interval, DeLong test on the probabilities averaged over the seeds."""
    low, high = stats.interval(samples[key][:, 0] - samples[other][:, 0], confidence)  # column 0: AUC
    test_result = stats.delong(labels, matrices[key].mean(axis=0), matrices[other].mean(axis=0))
    return {"difference": mean_auc(labels, matrices[key]) - mean_auc(labels, matrices[other]), "ci_low": low, "ci_high": high,
            "delong_auc_mean_probability": test_result["auc_a"] - test_result["auc_b"], "delong_z": test_result["z"],
            "delong_p": test_result["p_value"]}
