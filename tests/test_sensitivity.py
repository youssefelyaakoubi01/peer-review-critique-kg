"""Sensitivity analyses on stored predictions (src/eval/sensitivity.py)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from src.eval import sensitivity

SETTINGS = {"n_resamples": 200, "seed": 0, "confidence": 0.95}


def toy_graph():
    """Five articles (three of 2024, two of 2025) and four concepts.
    c0: a0 a1 (2024 only); c1: a2, a3 (one article of each year); c2: a3 a4 (2025 only); c3: a0 a1 a2 a3."""
    year = np.array([2024, 2024, 2024, 2025, 2025])
    links = [(0, 0), (1, 0), (2, 1), (3, 1), (3, 2), (4, 2), (0, 3), (1, 3), (2, 3), (3, 3)]
    has_concept = np.array(links).T
    sizes = np.bincount(has_concept[1], minlength=4)
    # shares_concept through the concepts used by at most 3 articles: c0 (a0-a1), c1 (a2-a3), c2 (a3-a4)
    pairs = [(0, 1), (2, 3), (3, 4)]
    shares = np.array([*pairs, *[(b, a) for a, b in pairs]]).T
    return year, has_concept, shares, sizes


def test_concept_scope_counts_what_the_later_years_bring():
    year, has_concept, shares, sizes = toy_graph()
    scope, by_year = sensitivity.concept_scope(year, has_concept, shares, sizes, [2024], min_articles=2, max_shared=3)
    row = scope.iloc[0]
    assert row["concepts"] == 4
    assert row["concepts_below_min_in_training_years"] == 2   # c1 (one article of 2024) and c2 (none)
    assert row["concepts_absent_from_training_years"] == 1    # c2
    # c3 has 4 articles in the graph (too many to carry shares_concept) and 3 in 2024 (it would carry it)
    assert row["concepts_kept_whose_shares_concept_status_changes"] == 1
    assert row["has_concept_links"] == 10 and row["has_concept_links_to_concepts_below_min"] == 4
    assert row["has_concept_links_of_training_years_to_concepts_below_min"] == 1   # a2-c1
    assert row["share_concepts_below_min_in_training_years"] == pytest.approx(0.5)
    assert by_year.to_dict("records") == [{"year_a": 2024, "year_b": 2024, "pairs": 1}, {"year_a": 2024, "year_b": 2025, "pairs": 1},
                                          {"year_a": 2025, "year_b": 2025, "pairs": 1}]


def test_concept_scope_refuses_edges_that_do_not_match_the_concept_sizes():
    year, has_concept, shares, sizes = toy_graph()
    with pytest.raises(ValueError, match="number of articles"):
        sensitivity.concept_scope(year, has_concept, shares, sizes + 1, [2024], 2, 3)


def test_concept_neighbours_by_year_and_population():
    year, has_concept, shares, _ = toy_graph()
    table = sensitivity.concept_neighbours(year, has_concept, shares, [2024], {
        "all": np.ones(5, dtype=bool), "some": np.array([False, False, False, True, False])})
    rows = table.set_index(["population", "year"])
    assert rows.loc[("all", 2024), "articles"] == 3 and rows.loc[("all", 2025), "articles"] == 2
    assert rows.loc[("all", 2025), "share_with_a_neighbour"] == 1.0
    assert rows.loc[("all", 2025), "share_with_a_training_year_neighbour"] == 0.5   # a3 is linked to a2, a4 to a3 only
    assert rows.loc[("some", 2025), "share_with_a_training_year_neighbour"] == 1.0 and ("some", 2024) not in rows.index


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


def test_a_score_is_compared_like_a_model_with_identical_seeds():
    table = predictions()
    papers = table.drop_duplicates("forum_id")[["forum_id", "split", "label", "borderline", "text_available"]]
    score = pd.Series(np.linspace(0, 1, len(papers)), index=papers["forum_id"].to_numpy()).sample(frac=1.0, random_state=0)
    rows = sensitivity.score_as_model(papers, score, "score", "A", [0, 1])
    assert len(rows) == 2 * len(papers) and rows.groupby("forum_id")["probability"].nunique().eq(1).all()
    assert rows.set_index("forum_id").loc["f7", "probability"].iloc[0] == score["f7"]   # aligned on the paper, not on the position
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        sensitivity.score_as_model(papers, score * 10, "score", "A", [0, 1])

    both = pd.concat([table, rows], ignore_index=True)
    result = sensitivity.paired_rows(both, "all", [(("good", "A"), ("score", "A")), (("good", "A"), ("weak", "A"))], SETTINGS)
    first = result[0]
    labels = papers["label"].to_numpy()
    assert first["auc_control"] == pytest.approx(roc_auc_score(labels, score.loc[papers["forum_id"]]))
    assert first["difference"] == pytest.approx(first["auc_model"] - first["auc_control"])
    assert first["n_papers"] == len(papers) and first["n_accepted"] == labels.sum()
    assert first["auc_model_ci_low"] < first["auc_model"] < first["auc_model_ci_high"]
    assert result[1]["control"] == "weak" and result[1]["ci_low"] > 0


def test_holm_table_corrects_each_family_apart():
    wide = pd.DataFrame({"model": ["ref", "a", "b", "c"], "setting": "A", "subset": "all",
                         "auc_minus_ref": [np.nan, 0.02, -0.01, 0.0], "auc_minus_ref_ci_low": [np.nan, 0.01, -0.03, -0.01],
                         "auc_minus_ref_ci_high": [np.nan, 0.03, 0.01, 0.01], "delong_p_vs_ref": [np.nan, 0.01, 0.04, np.nan]})
    long = pd.DataFrame({"model": ["a", "b", "a"], "control": ["x", "x", "y"], "setting": "A", "split": ["test", "test", "val"],
                         "subset": "all", "difference": [0.1, 0.2, 0.3], "ci_low": [0.0, 0.1, 0.2], "ci_high": [0.2, 0.3, 0.4],
                         "delong_p": [0.03, 0.04, 0.001]})
    families = {"against_ref": {"file": "wide.csv", "control": "ref"},
                "pairs": {"file": "long.csv", "where": {"split": ["test"]}}}
    table = sensitivity.holm_table({"wide.csv": wide, "long.csv": long}, families, alpha=0.05)
    first = table[table["family"] == "against_ref"].set_index("model")
    assert list(first.index) == ["a", "b", "c"] and (first["control"] == "ref").all()   # the reference is not tested against itself
    assert (first["n_tests"] == 2).all()                                                # the missing test is not counted
    assert first.loc["a", "delong_p_holm"] == pytest.approx(0.02) and first.loc["b", "delong_p_holm"] == pytest.approx(0.04)
    assert np.isnan(first.loc["c", "delong_p_holm"]) and not first.loc["c", "rejects_holm"]
    assert first["ci_excludes_zero"].tolist() == [True, False, False]
    second = table[table["family"] == "pairs"]
    assert len(second) == 2 and second["delong_p_holm"].tolist() == pytest.approx([0.06, 0.06])
    assert second["rejects"].all() and not second["rejects_holm"].any()
    with pytest.raises(ValueError, match="no test"):
        sensitivity.holm_table({"long.csv": long}, {"empty": {"file": "long.csv", "where": {"split": ["holdout"]}}}, 0.05)
