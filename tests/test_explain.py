"""Phase 9: computation graph of an article, occlusion, fidelity, gradient attributions."""

import numpy as np
import pytest
import torch
from test_baselines import LAYOUT, synthetic_graph
from test_hetero import PARAMS, SETTINGS

from src.explain import gradients, occlusion, sample, subgraph
from src.models import baselines, features, hetero


@pytest.fixture(scope="module")
def task():
    graph, labels, split = synthetic_graph()
    data = baselines.Data(features.article_table(graph, LAYOUT), labels, split)
    views = hetero.hetero_views(graph, LAYOUT, split, "cpu")
    params = {**PARAMS, "layers": 3}
    probabilities, _, model = hetero.run("hgt", params, data, views, seed=0, settings=SETTINGS)
    model.eval()
    index = subgraph.GraphIndex(*views.full_inputs)
    return graph, views, model, index, probabilities, split


@pytest.mark.parametrize("kind", hetero.KINDS)
def test_one_set_of_edges_per_layer_gives_the_same_logits(kind):
    graph, _, split = synthetic_graph()
    views = hetero.hetero_views(graph, LAYOUT, split, "cpu")
    torch.manual_seed(0)
    model = hetero.HeteroGNN(kind, views.metadata, views.in_dims, 16, 2, 0.0, 2).eval()
    x, edges = views.full_inputs
    with torch.no_grad():
        assert torch.equal(model(x, edges), model(x, [edges, dict(edges)]))
        with pytest.raises(ValueError, match="sets of edges"):
            model(x, [edges])


def test_the_neighbourhood_reproduces_the_prediction_on_the_whole_graph(task):
    graph, views, model, index, probabilities, split = task
    with torch.no_grad():
        whole = model(*views.full_inputs)
    for article in np.flatnonzero(split == "test")[:8]:
        hood = index.neighbourhood(int(article), layers=3)
        with torch.no_grad():
            value = subgraph.logit(model, hood)
        assert float(value) == pytest.approx(float(whole[article]), abs=1e-5)
        assert float(torch.sigmoid(value)) == pytest.approx(float(probabilities[article]), abs=1e-5)
        # the reviews of the article and their critiques, read from the graph
        articles, reviews = graph["article", "has_review", "review"].edge_index
        own = reviews[articles == article]
        assert sorted(hood.nodes["review"][hood.reviews].tolist()) == sorted(own.tolist())
        owners, critiques = graph["review", "contains", "critique"].edge_index
        assert sorted(hood.nodes["critique"][hood.critiques].tolist()) == sorted(critiques[torch.isin(owners, own)].tolist())
        # the last layer only reads the edges into the article
        assert all((edges[1] == hood.target).all() for (_, _, target), edges in hood.layer_edges[-1].items() if target == "article")
        assert sum(edges.shape[1] for edges in hood.layer_edges[-1].values()) < sum(edges.shape[1] for edges in hood.layer_edges[0].values())


def test_removing_a_critique_by_occlusion_is_deleting_it_from_the_graph(task):
    graph, views, model, index, _, split = task
    article = int(np.flatnonzero(split == "test")[0])
    hood = index.neighbourhood(article, layers=3)
    base, importances = occlusion.critique_importances(model, hood)
    assert len(importances) == len(hood.critiques) > 0 and np.abs(importances).max() > 0
    x, edges = views.full_inputs
    for position in (0, len(hood.critiques) - 1):
        removed = int(hood.nodes["critique"][hood.critiques[position]])
        keep = torch.ones(x["critique"].shape[0], dtype=torch.bool)
        keep[removed] = False
        renumber = torch.cumsum(keep.long(), 0) - 1
        smaller_x = {**x, "critique": x["critique"][keep]}
        smaller_edges = {}
        for (source, relation, target), pairs in edges.items():
            kept = torch.ones(pairs.shape[1], dtype=torch.bool)
            pairs = pairs.clone()
            for row, node_type in ((0, source), (1, target)):
                if node_type == "critique":
                    kept &= keep[pairs[row]]
                    pairs[row] = renumber[pairs[row]]
            smaller_edges[(source, relation, target)] = pairs[:, kept]
        with torch.no_grad():
            deleted = float(model(smaller_x, smaller_edges)[article])
        assert base - importances[position] == pytest.approx(deleted, abs=1e-5)


def test_relations_and_references_are_removed_as_announced(task):
    graph, _, model, index, _, split = task
    hood = index.neighbourhood(int(np.flatnonzero(split == "test")[1]), layers=3)
    names = subgraph.relations(graph.edge_types)
    assert names == ["has_review", "contains", "about", "has_concept", "shares_concept"]
    without = subgraph.drop_relation(hood.layer_edges, "contains")
    assert all(edges[("review", "contains", "critique")].shape[1] == 0 and edges[("critique", "rev_contains", "review")].shape[1] == 0
               and edges[("article", "has_review", "review")].equal(original[("article", "has_review", "review")])
               for edges, original in zip(without, hood.layer_edges))
    with torch.no_grad():
        base = float(subgraph.logit(model, hood))
    by_relation = occlusion.relation_importances(model, hood, base, names)
    assert set(by_relation) == set(names) and by_relation["has_review"] != 0
    references = occlusion.reference_importances(model, hood, base, [0, 1, 2, 3])
    # all the critiques removed: nothing reaches the article through `contains` either
    assert references["critiques"] == pytest.approx(by_relation["contains"], abs=1e-5)
    assert references["scores"] != 0 and torch.equal(hood.x["review"], index.x["review"][hood.nodes["review"]])  # the input is untouched
    assert subgraph.drop_nodes(hood.layer_edges, "critique", torch.empty(0, dtype=torch.long)) is hood.layer_edges


def test_fidelity_removes_and_keeps_the_most_important_critiques(task):
    _, _, model, index, _, split = task
    hood = index.neighbourhood(int(np.flatnonzero(split == "test")[2]), layers=3)
    base, importances = occlusion.critique_importances(model, hood)
    n = len(importances)
    assert occlusion.top(np.array([0.1, -0.5, 0.3, 0.5]), 2).tolist() == [1, 3]
    rows = occlusion.fidelity(model, hood, importances, [1, n, n + 1], np.random.default_rng(0))
    assert [row["k"] for row in rows] == [1, n]  # k larger than the number of critiques is skipped
    first, everything = rows
    strongest = int(np.argmax(np.abs(importances)))
    assert first["top_removed"] == pytest.approx(float(torch.sigmoid(torch.tensor(base - importances[strongest]))), abs=1e-6)
    probability = float(torch.sigmoid(torch.tensor(base)))
    # k = all the critiques: keeping them all changes nothing, removing them all is the same for top and random
    assert everything["top_kept"] == pytest.approx(probability, abs=1e-6) == pytest.approx(everything["random_kept"], abs=1e-6)
    assert everything["top_removed"] == pytest.approx(everything["random_removed"], abs=1e-6)
    again = occlusion.fidelity(model, hood, importances, [1], np.random.default_rng(0))
    assert again[0] == first


def test_gradient_attributions_are_complete_and_follow_the_critiques(task):
    _, _, model, index, _, split = task
    hood = index.neighbourhood(int(np.flatnonzero(split == "test")[0]), layers=3)
    integrated = gradients.critique_attributions(model, hood, "integrated_gradients", steps=64)
    assert integrated.shape == (hood.x["critique"].shape[0],)
    with torch.no_grad():
        full = float(subgraph.logit(model, hood))
        empty = float(subgraph.logit(model, hood, x={**hood.x, "critique": torch.zeros_like(hood.x["critique"])}))
    assert integrated.sum() == pytest.approx(full - empty, abs=0.05 * max(1.0, abs(full - empty)))  # completeness
    simple = gradients.critique_attributions(model, hood, "input_x_gradient")
    assert simple.shape == integrated.shape and np.abs(simple[hood.critiques.numpy()]).sum() > 0
    with pytest.raises(ValueError, match="unknown attribution"):
        gradients.critique_attributions(model, hood, "lime")
    assert not hood.x["critique"].requires_grad


def test_explained_articles_are_balanced_and_do_not_depend_on_a_seed():
    rng = np.random.default_rng(0)
    n = 400
    forum_ids = np.array([f"f{i}" for i in range(n)], dtype=object)
    labels = rng.integers(0, 2, size=n).astype(float)
    borderline = rng.random(n) < 0.5
    candidates = np.arange(50, n)
    table = sample.explained_articles(forum_ids, labels, borderline, candidates, per_group=20, salt="s")
    assert table["group"].value_counts().to_dict() == {group: 20 for group in sample.GROUPS}
    assert table["article_index"].min() >= 50 and table["forum_id"].is_unique
    assert (table["population"] == table["group"].map(pd_counts(labels, borderline, candidates))).all()
    smaller = sample.explained_articles(forum_ids, labels, borderline, candidates, per_group=5, salt="s")
    assert set(smaller["forum_id"]) <= set(table["forum_id"]) and (smaller["rank"] < 5).all()
    other = sample.explained_articles(forum_ids, labels, borderline, candidates, per_group=20, salt="t")
    assert set(other["forum_id"]) != set(table["forum_id"])


def pd_counts(labels, borderline, candidates):
    names = np.where(labels[candidates] == 1, "accepted", "rejected") + np.where(borderline[candidates], "_borderline", "_other")
    return {name: int((names == name).sum()) for name in set(names)}


def test_weighted_ratio_and_its_stratified_bootstrap():
    from src.explain import aggregate

    strata = np.array(["a"] * 4 + ["b"] * 2, dtype=object)
    populations = np.array([40] * 4 + [100] * 2)
    weight = aggregate.weights(strata, populations)
    assert weight.tolist() == [10.0] * 4 + [50.0] * 2
    counts = aggregate.bootstrap_counts(strata, 500, seed=0)
    assert counts.shape == (500, 6) and (counts[:, :4].sum(axis=1) == 4).all() and (counts[:, 4:].sum(axis=1) == 2).all()
    assert np.array_equal(counts, aggregate.bootstrap_counts(strata, 500, seed=0))
    values = np.array([1.0, 2.0, 3.0, 4.0, 10.0, 20.0])
    mean, low, high = aggregate.ratio(values, np.ones(6), weight, counts, 0.95)
    assert mean == pytest.approx((10 * 10 + 50 * 30) / 140) and low < mean < high
    # a group is selected with zeros: the other stratum does not enter
    in_a = (strata == "a").astype(float)
    only_a, low_a, high_a = aggregate.ratio(values * in_a, in_a, weight, counts, 0.95)
    assert only_a == pytest.approx(2.5) and 1.0 <= low_a < high_a <= 4.0
    # per-critique mean: sums of importances over sums of numbers of critiques
    assert aggregate.ratio(np.array([3.0, 0, 0, 0, 0, 0]), np.array([2.0, 1, 0, 0, 0, 0]), weight, counts, 0.95)[0] == pytest.approx(1.0)
    assert np.isnan(aggregate.ratio(np.zeros(6), np.zeros(6), weight, counts, 0.95)[0])
