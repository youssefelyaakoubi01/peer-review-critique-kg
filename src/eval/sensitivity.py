"""Sensitivity analyses computed from what is already stored: the scope of the concept
vocabulary, the Holm correction of the tests of a table, and models compared again on
other subsets of papers. Nothing here trains a model.
"""

from typing import Any

import numpy as np
import pandas as pd

from src.eval import stats
from src.eval.compare import bootstrap, mean_auc, versus
from src.eval.sources import excludes_zero

Key = tuple[str, str]  # (model, setting)


# --------------------------------------------------------------------------- concepts
def concept_scope(article_year: np.ndarray, has_concept: np.ndarray, shares_concept: np.ndarray, concept_sizes: np.ndarray,
                  training_years: list[int], min_articles: int, max_shared: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """What the concept vocabulary owes to the years after the training years.

    The vocabulary of the graph is counted on every article of the graph. `has_concept`:
    (article, concept) index pairs, `shares_concept`: (article, article) pairs stored in
    both directions, `concept_sizes`: number of articles of each concept in the graph.
    Returns (one row of counts, number of shares_concept pairs per pair of years).
    """
    article_year = np.asarray(article_year)
    articles, concepts = has_concept
    in_training = np.isin(article_year, training_years)
    total = np.bincount(concepts, minlength=len(concept_sizes))
    if not np.array_equal(total, concept_sizes):
        raise ValueError("the has_concept edges do not give the stored number of articles of each concept")
    training = np.bincount(concepts[in_training[articles]], minlength=len(concept_sizes))
    below = training < min_articles          # not a concept with a vocabulary counted on the training years
    carries, would_carry = total <= max_shared, training <= max_shared
    scope = pd.DataFrame([{
        "training_years": " ".join(map(str, training_years)), "min_articles": min_articles, "max_articles_for_shared": max_shared,
        "concepts": len(concept_sizes),
        "concepts_below_min_in_training_years": int(below.sum()),
        "concepts_absent_from_training_years": int((training == 0).sum()),
        "concepts_kept_whose_shares_concept_status_changes": int((~below & (carries != would_carry)).sum()),
        "has_concept_links": len(concepts),
        "has_concept_links_to_concepts_below_min": int(below[concepts].sum()),
        "has_concept_links_of_training_years_to_concepts_below_min": int((below[concepts] & in_training[articles]).sum()),
    }])
    scope["share_concepts_below_min_in_training_years"] = scope["concepts_below_min_in_training_years"] / scope["concepts"]

    first, second = shares_concept
    once = first < second  # each pair is stored in both directions
    years = pd.DataFrame({"year_a": np.minimum(article_year[first[once]], article_year[second[once]]),
                          "year_b": np.maximum(article_year[first[once]], article_year[second[once]])})
    by_year = years.value_counts().sort_index().rename("pairs").reset_index()
    return scope, by_year


def concept_neighbours(article_year: np.ndarray, has_concept: np.ndarray, shares_concept: np.ndarray, training_years: list[int],
                       populations: dict[str, np.ndarray]) -> pd.DataFrame:
    """Per population of articles and per year: share of the articles linked to a
    concept, to another article by shares_concept, and to an article of the training
    years by shares_concept."""
    article_year = np.asarray(article_year)
    n = len(article_year)
    first, second = shares_concept
    with_concept = np.bincount(has_concept[0], minlength=n) > 0
    with_neighbour = np.bincount(first, minlength=n) > 0
    to_training = np.isin(article_year[second], training_years)
    with_training_neighbour = np.bincount(first[to_training], minlength=n) > 0
    rows = []
    for name, mask in populations.items():
        for year in sorted(np.unique(article_year[mask])):
            chosen = mask & (article_year == year)
            rows.append({"population": name, "year": int(year), "articles": int(chosen.sum()),
                         "share_with_a_concept": with_concept[chosen].mean(),
                         "share_with_a_neighbour": with_neighbour[chosen].mean(),
                         "share_with_a_training_year_neighbour": with_training_neighbour[chosen].mean()})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- Holm
def family_tests(table: pd.DataFrame, spec: dict[str, Any]) -> pd.DataFrame:
    """Tests of one family, one row per test: model, setting, control, split, subset,
    difference, ci_low, ci_high, delong_p. See `sensitivity.holm` in the config."""
    for column, wanted in spec.get("where", {}).items():
        table = table[table[column].isin(wanted)]
    control = spec.get("control")
    if control is not None:  # one column per reference model
        names = {f"auc_minus_{control}": "difference", f"auc_minus_{control}_ci_low": "ci_low",
                 f"auc_minus_{control}_ci_high": "ci_high", f"delong_p_vs_{control}": "delong_p"}
        table = table[table["model"] != control].rename(columns=names).assign(control=control)
    if table.empty:
        raise ValueError(f"no test in the family {spec}")
    columns = ["model", "setting", "control", "split", "subset", "difference", "ci_low", "ci_high", "delong_p"]
    return table.reindex(columns=columns).reset_index(drop=True)


def holm_table(tables: dict[str, pd.DataFrame], families: dict[str, dict[str, Any]], alpha: float) -> pd.DataFrame:
    """Every family with its Holm-adjusted p-values. A test whose p-value is missing
    is kept in the table and not counted in its family."""
    parts = []
    for name, spec in families.items():
        tests = family_tests(tables[spec["file"]], spec)
        tests.insert(0, "file", spec["file"])
        tests.insert(0, "family", name)
        tests["delong_p_holm"] = stats.holm(tests["delong_p"].to_numpy())
        tests["n_tests"] = int(tests["delong_p"].notna().sum())
        tests["ci_excludes_zero"] = [excludes_zero(low, high) for low, high in zip(tests["ci_low"], tests["ci_high"])]
        tests["rejects"] = tests["delong_p"] < alpha
        tests["rejects_holm"] = tests["delong_p_holm"] < alpha
        parts.append(tests)
    return pd.concat(parts, ignore_index=True)


# --------------------------------------------------------------------------- pairs
def score_as_model(papers: pd.DataFrame, score: pd.Series, name: str, setting: str, seeds: list[int]) -> pd.DataFrame:
    """Rows of a prediction table for a score that is not fitted: the same value for
    every seed. `papers`: forum_id, split, label, borderline, text_available (one row
    per paper); `score`: indexed by forum_id, in [0, 1]."""
    values = score.loc[papers["forum_id"]].to_numpy(dtype=float)
    if np.isnan(values).any() or values.min() < 0 or values.max() > 1:
        raise ValueError("a score used as a model must lie in [0, 1]")
    return pd.concat([papers.assign(model=name, setting=setting, seed=seed, probability=values) for seed in seeds], ignore_index=True)


def paired_rows(predictions: pd.DataFrame, subset: str, pairs: list[tuple[Key, Key]], settings: dict[str, Any]) -> list[dict]:
    """AUC of each model minus AUC of its control on one subset of the papers of
    `predictions`: paired bootstrap over the papers and DeLong test."""
    models = list(dict.fromkeys(key for pair in pairs for key in pair))
    papers, labels, matrices, samples = bootstrap(predictions, subset, models, settings)
    rows = []
    for key, control in pairs:
        low, high = stats.interval(samples[key][:, 0], settings["confidence"])
        rows.append({"model": key[0], "setting": key[1], "control": control[0], "control_setting": control[1], "subset": subset,
                     "n_papers": len(papers), "n_accepted": int(labels.sum()), "n_resamples": settings["n_resamples"],
                     "auc_model": mean_auc(labels, matrices[key]), "auc_model_ci_low": low, "auc_model_ci_high": high,
                     "auc_control": mean_auc(labels, matrices[control]),
                     **versus(labels, matrices, samples, key, control, settings["confidence"])})
    return rows
