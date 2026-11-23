"""A graph of setting A extended with a later year (src/kg/extend.py)."""

import numpy as np
import pandas as pd
import pytest
import torch

from src.kg import build, extend, tables as kg_tables
from src.models import baselines, features, hetero
from tests.test_kg import SETTINGS, synthetic_inputs

NEW = {"P5", "P6"}


def later_year():
    papers = pd.DataFrame({
        "forum_id": ["P5", "P6", "PY"], "year": [2026] * 3, "title": ["t5", "t6", "ty"], "abstract": ["a5", "a6", "ay"],
        "keywords": [["GAN", "A new topic"], ["gans", "a new topic", "Vision"], ["gan"]],
        "text_available": [True] * 3, "text_source": ["s"] * 3})
    reviews = pd.DataFrame({
        "review_id": ["R5", "R6", "R7"], "forum_id": ["P5", "P6", "P6"], "year": [2026] * 3,
        "rating_initial": [5, 8, 3], "confidence_initial": [3, 4, 4], "soundness_initial": [2, 3, 2],
        "contribution_initial": [2, 3, 2], "presentation_initial": [3, 3, 2], "summary": ["The paper does Y."] * 3,
        "strengths": ["Good idea.", "Strong results.", None], "weaknesses": ["No ablation.", None, "Wrong proof."],
        "questions": [None, None, None]})
    critiques = pd.DataFrame({
        "critique_id": ["R5:1", "R5:2", "R6:1", "R7:1"], "review_id": ["R5", "R5", "R6", "R7"], "forum_id": ["P5", "P5", "P6", "P6"],
        "year": [2026] * 4, "critique_index": [1, 2, 1, 1], "text": ["Good idea.", "No ablation.", "Strong results.", "Wrong proof."],
        "aspect": ["novelty", "experimental_comparison", "significance", None], "severity": ["minor", "major", "minor", None],
        "polarity": ["positive", "negative", "positive", None], "target": ["general", "experiment", "general", None],
        "actionable": [False, True, False, None]})
    audit = pd.DataFrame({"review_id": ["R5", "R6", "R7"], "post_rebuttal_units": [[], [], []]})
    return papers, reviews, critiques, audit


@pytest.fixture(scope="module")
def tables():
    papers, reviews, critiques, responses, audit = synthetic_inputs()
    base = kg_tables.build_tables(papers, reviews, critiques, responses, audit, {"P1", "P2", "P3", "P4"}, SETTINGS, 36000).setting("A")
    new_papers, new_reviews, new_critiques, new_audit = later_year()
    extended = extend.extend_tables(base, pd.concat([papers, new_papers]), pd.concat([reviews, new_reviews]), new_critiques, new_audit,
                                    NEW, SETTINGS, 36000)
    return base, extended


def test_new_nodes_are_appended_after_the_nodes_of_the_base_graph(tables):
    base, extended = tables
    assert extended.nodes["article"]["forum_id"].tolist() == ["P1", "P2", "P3", "P4", "P5", "P6"]  # PY is not a usable paper
    assert extended.nodes["review"]["review_id"].tolist() == ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]
    assert extended.nodes["critique"]["critique_id"].tolist()[len(base.nodes["critique"]):] == ["R5:1", "R5:2", "R6:1", "R7:1"]
    for node_type, table in base.nodes.items():
        assert extended.nodes[node_type].iloc[:len(table)].equals(table)
    for relation, (sources, targets) in base.edges.items():
        assert extended.edges[relation][0][:len(sources)].tolist() == sources.tolist()
        assert extended.edges[relation][1][:len(targets)].tolist() == targets.tolist()
    assert extended.edges[kg_tables.HAS_REVIEW][0][-3:].tolist() == [4, 5, 5] and extended.edges[kg_tables.HAS_REVIEW][1][-3:].tolist() == [4, 5, 6]
    assert len(extended.edges[kg_tables.ABOUT][0]) == len(base.edges[kg_tables.ABOUT][0]) + 3  # the untyped critique has no aspect


def test_the_vocabulary_of_concepts_is_frozen(tables):
    base, extended = tables
    assert extended.nodes["concept"].equals(base.nodes["concept"])  # "a new topic" is used by two new articles: still no concept
    concepts = extended.nodes["concept"]["concept"].tolist()
    assert concepts == ["gan", "vision"]
    sources, targets = extended.edges[kg_tables.HAS_CONCEPT]
    added = sorted(zip(sources[len(base.edges[kg_tables.HAS_CONCEPT][0]):].tolist(), targets[len(base.edges[kg_tables.HAS_CONCEPT][0]):].tolist()))
    assert added == [(4, 0), (5, 0), (5, 1)]  # P5: gan; P6: gan and vision


def test_shares_concept_reaches_the_new_articles_through_the_concepts_that_carried_it(tables):
    base, extended = tables
    # in the base graph "gan" has 2 articles (carries the relation), "vision" has 3 (does not, limit of 2)
    n = len(base.edges[kg_tables.SHARES_CONCEPT][0])
    sources, targets = extended.edges[kg_tables.SHARES_CONCEPT]
    pairs = set(zip(sources[n:].tolist(), targets[n:].tolist()))
    expected = {(0, 4), (1, 4), (0, 5), (1, 5), (4, 5)}  # P1, P2, P5, P6 share "gan"; P3 only shares "vision" with P6
    assert pairs == expected | {(j, i) for i, j in expected}
    assert extended.edge_weights[kg_tables.SHARES_CONCEPT][n:].tolist() == [1.0] * 10
    coverage = extend.concept_coverage(extended, SETTINGS["concepts"]["max_articles_for_shared"]).set_index("year")
    assert coverage.loc[2026, "articles"] == 2 and coverage.loc[2026, "keywords"] == 5 and coverage.loc[2026, "keywords_in_vocabulary"] == 3
    assert coverage.loc[2026, "share_articles_with_a_neighbour"] == 1.0 and coverage.loc[2025, "share_articles_with_a_neighbour"] == 0.0


def test_the_extended_graph_holds_the_base_graph_unchanged(tables):
    base, extended = tables
    rng = np.random.default_rng(0)
    vectors = {t: rng.normal(size=(len(table), 4)).astype(np.float32) for t, table in extended.nodes.items()}
    graph, layout = build.build_graph(extended, vectors)
    reference, reference_layout = build.build_graph(base, {t: vectors[t][:len(table)] for t, table in base.nodes.items()})
    assert layout == reference_layout
    for node_type in reference.node_types:
        assert torch.equal(graph[node_type].x[:reference[node_type].num_nodes], reference[node_type].x)
    for edge_type in reference.edge_types:
        assert torch.equal(graph[edge_type].edge_index[:, :reference[edge_type].edge_index.shape[1]], reference[edge_type].edge_index)
    assert graph["article"].year.tolist() == [2024, 2024, 2025, 2025, 2026, 2026]


def test_only_new_papers_extend_a_graph_of_setting_a(tables):
    base, _ = tables
    papers, reviews, critiques, responses, audit = synthetic_inputs()
    new_papers, new_reviews, new_critiques, new_audit = later_year()
    with pytest.raises(ValueError, match="already in the graph"):
        extend.extend_tables(base, papers, reviews, critiques, audit, {"P1"}, SETTINGS, 36000)
    with_responses = kg_tables.build_tables(papers, reviews, critiques, responses, audit, {"P1", "P2", "P3", "P4"}, SETTINGS, 36000)
    with pytest.raises(ValueError, match="setting A"):
        extend.extend_tables(with_responses, pd.concat([papers, new_papers]), pd.concat([reviews, new_reviews]), new_critiques,
                             new_audit, NEW, SETTINGS, 36000)


def test_holdout_articles_are_never_in_the_graph_a_model_is_trained_on(tables):
    _, extended = tables
    rng = np.random.default_rng(0)
    graph, layout = build.build_graph(extended, {t: rng.normal(size=(len(table), 4)).astype(np.float32) for t, table in extended.nodes.items()})
    split = np.array(["train", "val", "test", "test", "holdout", "holdout"], dtype=object)
    views = hetero.hetero_views(graph, layout, split, "cpu")
    assert views.train_articles.tolist() == [0, 1]
    assert views.train_inputs[0]["article"].shape[0] == 2 and views.train_inputs[0]["review"].shape[0] == 3
    assert views.full_inputs[0]["article"].shape[0] == 6
    flat = baselines.graph_views(graph, layout, split, "cpu")
    assert flat.train_articles.tolist() == [0, 1]
