"""Phase 8: ablated graphs remove what they announce and nothing else."""

import numpy as np
import pytest
import torch
from test_baselines import LAYOUT, synthetic_graph
from test_hetero import PARAMS, SETTINGS

from src.models import baselines, features, hetero
from src.models.ablation import ablated_graph
from src.utils.config import load_config

SCORES = ["rating_initial", "confidence_initial", "soundness_initial", "contribution_initial"]


@pytest.fixture(scope="module")
def synthetic():
    return synthetic_graph()


def test_an_empty_ablation_returns_the_graph_itself(synthetic):
    graph = synthetic[0]
    same, layout = ablated_graph(graph, LAYOUT, {})
    assert same is graph and layout is LAYOUT and ablated_graph(graph, LAYOUT, None)[0] is graph


def test_a_relation_is_removed_with_its_inverse_and_nothing_else(synthetic):
    graph = synthetic[0]
    out, layout = ablated_graph(graph, LAYOUT, {"drop_edges": ["about"]})
    assert set(graph.edge_types) - set(out.edge_types) == {("critique", "about", "aspect"), ("aspect", "rev_about", "critique")}
    assert out.node_types == graph.node_types and layout == LAYOUT
    assert all(out[t].x.equal(graph[t].x) for t in graph.node_types)
    assert all(out[e].edge_index.equal(graph[e].edge_index) for e in out.edge_types)
    lonely, _ = ablated_graph(graph, LAYOUT, {"drop_edges": ["shares_concept"]})  # a relation without an inverse
    assert set(graph.edge_types) - set(lonely.edge_types) == {("article", "shares_concept", "article")}


def test_a_node_type_is_removed_with_every_relation_that_touches_it(synthetic):
    graph = synthetic[0]
    out, layout = ablated_graph(graph, LAYOUT, {"drop_nodes": ["critique", "aspect"]})
    assert set(out.node_types) == {"article", "review", "concept"} and set(layout) == set(out.node_types)
    assert all("critique" not in edge and "aspect" not in edge for edge in out.edge_types)
    assert ("article", "has_review", "review") in out.edge_types and ("article", "shares_concept", "article") in out.edge_types


def test_feature_blocks_are_removed_and_the_layout_follows(synthetic):
    graph = synthetic[0]
    out, layout = ablated_graph(graph, LAYOUT, {"drop_features": {"review": SCORES[:1] + SCORES[2:]}})
    assert [block["name"] for block in layout["review"]] == ["confidence_initial", "text"]
    assert layout["review"][0] == {"name": "confidence_initial", "start": 0, "end": 1}
    assert out["review"].x.equal(graph["review"].x[:, [1, *range(4, graph["review"].x.shape[1])]])
    assert out["critique"].x.equal(graph["critique"].x) and layout["critique"] == LAYOUT["critique"]
    assert features.columns(layout, "review", "text") == slice(1, out["review"].x.shape[1])
    assert graph["review"].x.shape[1] == 4 + 6  # the original graph is untouched


def test_an_ablation_that_names_something_absent_or_empties_a_node_type_is_refused(synthetic):
    graph = synthetic[0]
    for spec, message in (({"drop_nodes": ["author"]}, "does not have"), ({"drop_edges": ["cites"]}, "does not have"),
                          ({"drop_features": {"review": ["decision"]}}, "does not have"), ({"remove": ["x"]}, "unknown keys"),
                          ({"drop_features": {"concept": ["text"]}}, "no feature left"),
                          ({"drop_nodes": ["critique"], "drop_features": {"critique": ["text"]}}, "both")):
        with pytest.raises(ValueError, match=message):
            ablated_graph(graph, LAYOUT, spec)


def test_configured_variants_remove_what_they_announce():
    variants = load_config()["ablations"]["variants"]
    assert variants["full"] == {}
    assert variants["no_shares_concept"] == {"drop_edges": ["shares_concept"]}
    labels = variants["no_critique_labels"]
    assert labels["drop_nodes"] == ["aspect"] and set(labels["drop_features"]["critique"]) == {"aspect", "severity", "polarity", "target", "actionable"}
    assert variants["no_critique_text"] == {"drop_features": {"critique": ["text"]}}
    assert set(variants["no_critiques"]["drop_nodes"]) == {"critique", "aspect"}
    assert variants["no_scores"] == {"drop_features": {"review": SCORES}}
    both = variants["no_scores_no_critiques"]
    assert set(both["drop_nodes"]) == {"critique", "aspect"} and both["drop_features"] == {"review": SCORES}


@pytest.mark.parametrize("spec", [{"drop_nodes": ["critique", "aspect"]}, {"drop_features": {"review": SCORES}},
                                  {"drop_nodes": ["aspect"], "drop_features": {"critique": ["aspect", "severity"]}}])
def test_a_model_trains_on_an_ablated_graph_without_the_test_year(synthetic, spec):
    graph, labels, split = synthetic
    ablated, layout = ablated_graph(graph, LAYOUT, spec)
    data = baselines.Data(features.article_table(graph, LAYOUT), labels, split)  # labels and subsets: the whole graph
    views = hetero.hetero_views(ablated, layout, split, "cpu")
    assert set(views.in_dims) == set(ablated.node_types)
    first, fitted, _ = hetero.run("hgt", PARAMS, data, views, seed=0, settings=SETTINGS)
    assert first.shape == labels.shape and np.isfinite(first).all() and fitted.epochs > 0
    # everything that belongs to a test article is changed: training and the other predictions do not move
    from src.kg.build import article_masks

    changed = ablated.clone()
    masks = article_masks(ablated, torch.from_numpy(split == "test"))
    for node_type in ("article", "review", "critique"):
        if node_type in changed.node_types:
            changed[node_type].x[masks[node_type]] += 7.0
    other = hetero.hetero_views(changed, layout, split, "cpu")
    # what the training reads is exactly the same ...
    assert all(torch.equal(views.train_inputs[0][t], other.train_inputs[0][t]) for t in views.train_inputs[0])
    assert all(torch.equal(views.train_inputs[1][e], other.train_inputs[1][e]) for e in views.train_inputs[1])
    # ... so the predictions of the training years are the same (up to the rounding of two
    # trainings on separate copies of the data), and those of the test year move
    second, _, _ = hetero.run("hgt", PARAMS, data, other, seed=0, settings=SETTINGS)
    known = split != "test"
    assert np.abs(first[known] - second[known]).max() < 1e-4 and np.abs(first[~known] - second[~known]).max() > 1e-2
