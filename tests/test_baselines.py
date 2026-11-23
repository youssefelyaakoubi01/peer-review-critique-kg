"""Phase 6: features taken from the graph, flattened graph, training loop, baselines.

Everything runs on a small random graph, on CPU.
"""

import numpy as np
import pytest
import torch
from torch_geometric.data import HeteroData

from src.models import baselines, features, train

TEXT = 6
LAYOUT = {
    "article": [{"name": "specter2", "start": 0, "end": TEXT}, {"name": "text_missing", "start": TEXT, "end": TEXT + 1}],
    "review": [*({"name": f"{score}_initial", "start": i, "end": i + 1}
                 for i, score in enumerate(("rating", "confidence", "soundness", "contribution"))),
               {"name": "text", "start": 4, "end": 4 + TEXT}],
    "critique": [{"name": "text", "start": 0, "end": TEXT}, {"name": "aspect", "start": TEXT, "end": TEXT + 8},
                 {"name": "severity", "start": TEXT + 8, "end": TEXT + 11}, {"name": "polarity", "start": TEXT + 11, "end": TEXT + 14},
                 {"name": "target", "start": TEXT + 14, "end": TEXT + 19}, {"name": "actionable", "start": TEXT + 19, "end": TEXT + 20}],
    "aspect": [{"name": "identity", "start": 0, "end": 8}],
    "concept": [{"name": "text", "start": 0, "end": TEXT}],
}
SETTINGS = {"max_epochs": 60, "patience": 15}
SPECS = {
    "majority": ({"kind": "majority"}, {}),
    "logistic": ({"kind": "logistic", "features": ["rating", "other_scores"]}, {"C": 1}),
    "gbt": ({"kind": "gbt", "features": ["rating", "other_scores", "critique_marginals"]},
            {"learning_rate": 0.1, "max_iter": 30, "max_leaf_nodes": 7}),
    "mlp": ({"kind": "mlp", "features": ["review_text", "rating", "other_scores", "article_text"]},
            {"hidden": 16, "dropout": 0.0, "lr": 0.01, "weight_decay": 0.0}),
    "gcn": ({"kind": "gcn"}, {"layers": 2, "hidden": 16, "dropout": 0.0, "lr": 0.01, "weight_decay": 0.0}),
}


def synthetic_graph(n_train=80, n_val=30, n_test=40, seed=0):
    """(graph, labels, split). Accepted articles have higher ratings; a few test
    articles have no text; one training article has no decision."""
    rng = np.random.default_rng(seed)
    n = n_train + n_val + n_test
    split = np.array(["train"] * n_train + ["val"] * n_val + ["test"] * n_test, dtype=object)
    labels = rng.integers(0, 2, size=n).astype(float)
    article_x = np.c_[rng.normal(size=(n, TEXT)) + 3, np.zeros(n)].astype(np.float32)
    article_x[-5:] = [0] * TEXT + [1]  # no text before the decisions

    review_article, review_x = [], []
    for article in range(n):
        for _ in range(rng.integers(2, 5)):
            rating = np.clip(np.round(5 + 2 * (labels[article] - 0.5) + rng.normal()), 1, 10)
            review_article.append(article)
            review_x.append([rating, rng.integers(1, 6), rng.integers(1, 5), rng.integers(1, 5), *rng.normal(size=TEXT)])
    review_article, review_x = np.array(review_article), np.array(review_x, dtype=np.float32)
    critique_review = np.repeat(np.arange(len(review_article)), 2)
    aspects = rng.integers(0, 8, size=len(critique_review))
    severity = rng.integers(0, 3, size=len(critique_review))
    other = np.random.default_rng(seed + 1)  # its own generator: the draws above and below do not move
    polarity, target = other.integers(0, 3, size=len(critique_review)), other.integers(0, 5, size=len(critique_review))
    actionable = other.integers(0, 2, size=len(critique_review))
    critique_x = np.c_[rng.normal(size=(len(critique_review), TEXT)), np.eye(8)[aspects], np.eye(3)[severity],
                       np.eye(3)[polarity], np.eye(5)[target], actionable].astype(np.float32)
    concepts = rng.integers(0, 4, size=n - 5)  # the articles without text have no concept
    pairs = np.array([(a, b) for a in range(n - 5) for b in range(n - 5) if a != b and concepts[a] == concepts[b] and abs(a - b) < 3])

    data = HeteroData()
    data["article"].x, data["review"].x = torch.from_numpy(article_x), torch.from_numpy(review_x)
    data["critique"].x, data["aspect"].x = torch.from_numpy(critique_x), torch.eye(8)
    data["concept"].x = torch.from_numpy(rng.normal(size=(4, TEXT)).astype(np.float32))
    edges = {("article", "has_review", "review"): (review_article, np.arange(len(review_article))),
             ("review", "contains", "critique"): (critique_review, np.arange(len(critique_review))),
             ("critique", "about", "aspect"): (np.arange(len(critique_review)), aspects),
             ("article", "has_concept", "concept"): (np.arange(n - 5), concepts)}
    for (source, relation, target), (rows, cols) in edges.items():
        index = torch.from_numpy(np.stack([rows, cols])).long()
        data[source, relation, target].edge_index = index
        data[target, "rev_" + relation, source].edge_index = index.flip(0)
    data["article", "shares_concept", "article"].edge_index = torch.from_numpy(pairs.T.copy()).long()
    labels[0] = np.nan  # withdrawn before a decision
    return data, labels, split


@pytest.fixture(scope="module")
def synthetic():
    return synthetic_graph()


def make_data(graph, labels, split, with_graph=True):
    data = baselines.Data(features.article_table(graph, LAYOUT), labels.copy(), split)
    if with_graph:
        data.graph = baselines.graph_views(graph, LAYOUT, split, "cpu")
    return data


# --------------------------------------------------------------------------- one row per article
def test_article_features_are_statistics_of_its_initial_reviews(synthetic):
    graph, _, _ = synthetic
    table = features.article_table(graph, LAYOUT)
    articles, reviews = graph["article", "has_review", "review"].edge_index.numpy()
    own = graph["review"].x.numpy()[reviews[articles == 7]]
    assert table.names["rating"] == ["rating_initial_mean", "rating_initial_min", "rating_initial_max", "rating_initial_std"]
    expected = [own[:, 0].mean(), own[:, 0].min(), own[:, 0].max(), own[:, 0].std()]
    assert table.blocks["rating"][7] == pytest.approx(expected)
    assert table.mean_rating[7] == pytest.approx(own[:, 0].mean())
    assert table.names["other_scores"][-1] == "n_reviews" and table.blocks["other_scores"][7, -1] == len(own)
    assert table.blocks["other_scores"][7, :4] == pytest.approx([own[:, 1].mean(), own[:, 1].min(), own[:, 1].max(), own[:, 1].std()])
    assert table.blocks["review_text"][7] == pytest.approx(own[:, 4:].mean(axis=0), abs=1e-6)
    assert table.text_available.sum() == len(table.text_available) - 5 and not table.text_available[-5:].any()
    assert {name: block.shape[1] for name, block in table.blocks.items()} == {
        "rating": 4, "other_scores": 13, "review_text": TEXT, "article_text": TEXT + 1,
        "critique_marginals": 21, "critique_aspect_severity": 32, "critique_worst_review": 3}
    assert all(len(table.names[name]) == block.shape[1] for name, block in table.blocks.items())


def test_critique_counts_are_means_over_the_reviews_of_the_article():
    """Two articles; the first has two reviews (three critiques, then none), the second one review."""
    graph = HeteroData()
    graph["article"].x = torch.zeros(2, TEXT + 1)
    graph["review"].x = torch.ones(3, 4 + TEXT)
    #            aspect            severity     polarity     target    actionable
    critiques = [("novelty", "blocking", "negative", "general", 1),       # review 0
                 ("novelty", "major", "negative", "experiment", 0),       # review 0
                 ("clarity", "minor", "positive", "section", 0),          # review 0
                 ("soundness", "blocking", "negative", "general", 1),     # review 2
                 ("soundness", "blocking", "negative", "general", 1)]     # review 2
    labels = features.CRITIQUE_LABELS
    rows = [np.concatenate([np.zeros(TEXT), *[np.eye(len(labels[name]))[labels[name].index(value)]
                                               for name, value in zip(labels, critique[:4])], [critique[4]]]) for critique in critiques]
    graph["critique"].x = torch.from_numpy(np.array(rows, dtype=np.float32))
    graph["article", "has_review", "review"].edge_index = torch.tensor([[0, 0, 1], [0, 1, 2]])
    graph["review", "contains", "critique"].edge_index = torch.tensor([[0, 0, 0, 2, 2], [0, 1, 2, 3, 4]])
    table = features.article_table(graph, LAYOUT)
    value = lambda block, column: table.blocks[block][:, table.names[block].index(column)].tolist()  # noqa: E731
    assert value("critique_marginals", "critiques_per_review") == [1.5, 2.0]  # (3 + 0) / 2 reviews, 2 / 1 review
    assert value("critique_marginals", "critique_aspect_novelty") == [1.0, 0.0]
    assert value("critique_marginals", "critique_severity_blocking") == [0.5, 2.0]
    assert value("critique_marginals", "critique_polarity_positive") == [0.5, 0.0]
    assert value("critique_marginals", "critique_target_general") == [0.5, 2.0]
    assert value("critique_marginals", "critique_actionable") == [0.5, 2.0]
    assert value("critique_aspect_severity", "critique_negative_novelty_blocking") == [0.5, 0.0]
    assert value("critique_aspect_severity", "critique_negative_novelty_major") == [0.5, 0.0]
    assert value("critique_aspect_severity", "critique_negative_soundness_blocking") == [0.0, 2.0]
    assert value("critique_aspect_severity", "critique_negative_clarity_minor") == [0.0, 0.0]  # that critique is positive
    assert value("critique_aspect_severity", "critique_positive_clarity") == [0.5, 0.0]
    assert table.names["critique_worst_review"] == ["critique_negative_blocking_max", "critique_negative_major_max", "critique_positive_min"]
    assert table.blocks["critique_worst_review"].tolist() == [[1.0, 1.0, 0.0], [2.0, 0.0, 0.0]]  # the review without critique counts
    # every critique is counted once in each family of labels
    marginals = table.blocks["critique_marginals"]
    assert marginals[:, 1:9].sum(axis=1).tolist() == marginals[:, 0].tolist() == marginals[:, 9:12].sum(axis=1).tolist()


def test_an_article_without_review_is_refused(synthetic):
    graph = synthetic[0].clone()
    edge = graph["article", "has_review", "review"]
    edge.edge_index = edge.edge_index[:, edge.edge_index[0] != 3]
    with pytest.raises(ValueError, match="no review"):
        features.article_table(graph, LAYOUT)


def test_features_are_scaled_with_the_training_rows_only(synthetic):
    graph, _, split = synthetic
    table = features.article_table(graph, LAYOUT)
    train_rows = np.flatnonzero(split == "train")
    design = table.design(["rating", "article_text"], train_rows)
    assert design.shape == (len(split), 4 + TEXT + 1)
    assert design[train_rows].mean(axis=0) == pytest.approx(np.zeros(design.shape[1]), abs=1e-4)
    assert design[train_rows, :4].std(axis=0) == pytest.approx(np.ones(4), abs=1e-4)
    # an embedding weighs as much as one score: its columns share a total variance of one
    assert design[train_rows, 4:-1].var(axis=0).sum() == pytest.approx(1.0, abs=1e-3)
    # no text: the embedding sits at the training mean (zero), the flag is kept
    assert not design[-5:, 4:-1].any() and (design[-5:, -1] == 1).all() and not design[:-5, -1].any()
    # values of other rows do not move the scaling
    table.blocks["rating"][split == "test"] += 100
    assert table.design(["rating"], train_rows)[train_rows] == pytest.approx(design[train_rows, :4])


# --------------------------------------------------------------------------- the graph
def test_graph_features_are_scaled_with_the_training_nodes_only(synthetic):
    graph, _, split = synthetic
    is_train = torch.from_numpy(split == "train")
    fit_on = features.training_nodes(graph, is_train)
    assert fit_on["article"].equal(is_train) and fit_on["aspect"].all()
    articles, reviews = graph["article", "has_review", "review"].edge_index
    assert fit_on["review"].equal(torch.isin(torch.arange(graph["review"].num_nodes), reviews[is_train[articles]]))
    x = features.standardise(graph, LAYOUT, fit_on)
    assert x["review"][fit_on["review"]].mean(dim=0).abs().max() < 1e-4
    variance = x["review"][fit_on["review"]].var(dim=0, correction=0)
    assert variance[:4] == pytest.approx(torch.ones(4), abs=1e-4)  # each score: unit variance
    assert float(variance[4:].sum()) == pytest.approx(1.0, abs=1e-3)  # the whole embedding: unit variance
    assert x["critique"][:, TEXT:].equal(graph["critique"].x[:, TEXT:])  # one-hot blocks are unchanged
    assert x["aspect"].equal(graph["aspect"].x)
    assert not x["article"][-5:, :TEXT].any() and (x["article"][:, TEXT] == graph["article"].x[:, TEXT]).all()

    moved = graph.clone()
    moved["review"].x[~fit_on["review"]] += 50  # reviews of validation and test articles
    again = features.standardise(moved, LAYOUT, fit_on)
    assert again["review"][fit_on["review"]].equal(x["review"][fit_on["review"]])


def test_the_flattened_graph_has_one_feature_space_and_one_kind_of_edge(synthetic):
    graph, _, _ = synthetic
    x = {node_type: graph[node_type].x for node_type in graph.node_types}
    flat = features.flatten(graph, x, LAYOUT)
    names = [block["name"] for block in flat.columns]
    assert names[0] == "text" and "specter2" not in names and len(names) == len(set(names))
    assert flat.x.shape == (graph.num_nodes, TEXT + 1 + 4 + 8 + 3 + 3 + 5 + 1 + 8)
    where = {block["name"]: slice(block["start"], block["end"]) for block in flat.columns}
    reviews = slice(flat.offsets["review"], flat.offsets["review"] + flat.sizes["review"])
    assert flat.x[reviews, where["text"]].equal(graph["review"].x[:, 4:])
    assert flat.x[reviews, where["rating_initial"]].equal(graph["review"].x[:, :1])
    assert not flat.x[reviews, where["aspect"]].any() and not flat.x[reviews, where["identity"]].any()
    articles = slice(0, flat.sizes["article"])
    assert flat.x[articles, where["text"]].equal(graph["article"].x[:, :TEXT])  # SPECTER2 shares the text columns
    assert flat.edge_index.shape[1] == sum(graph[edge_type].edge_index.shape[1] for edge_type in graph.edge_types)
    pairs = set(map(tuple, flat.edge_index.t().tolist()))
    assert all((target, source) in pairs for source, target in pairs)  # every edge has its inverse
    # an edge joins the nodes it joined before
    first = graph["review", "contains", "critique"].edge_index[:, 0]
    assert (flat.offsets["review"] + int(first[0]), flat.offsets["critique"] + int(first[1])) in pairs


def test_training_view_of_the_graph_holds_no_node_of_the_test_year(synthetic):
    graph, _, split = synthetic
    views = baselines.graph_views(graph, LAYOUT, split, "cpu")
    known = split != "test"
    assert views.train_articles.tolist() == np.flatnonzero(known).tolist()
    articles, reviews = graph["article", "has_review", "review"].edge_index.numpy()
    n_reviews = int(known[articles].sum())
    expected = int(known.sum()) + n_reviews + 2 * n_reviews + 8 + 4
    x, edge_index, rows = views.train_inputs
    assert x.shape[0] == expected and int(edge_index.max()) < expected
    full_x, _, full_rows = views.full_inputs
    assert full_x.shape[0] == graph.num_nodes and len(full_rows) == len(split)
    assert x[rows].equal(full_x[full_rows][torch.from_numpy(known)])  # the same articles, in the same order


# --------------------------------------------------------------------------- training
def test_training_keeps_the_best_validation_epoch():
    torch.manual_seed(0)
    x = torch.randn(200, 5)
    labels = (x[:, 0] + 0.5 * torch.randn(200) > 0).float()
    train_rows, val_rows = torch.arange(0, 120), torch.arange(120, 200)
    model = baselines.MLP(5, 16, 0.0)
    fitted = train.fit(model, (x,), labels, train_rows, val_rows, lr=0.05, weight_decay=0.0, max_epochs=300, patience=10)
    assert fitted.best_val_auc > 0.85 and fitted.epochs < 300  # stopped before the last epoch
    assert fitted.epochs - fitted.best_epoch == 10
    from sklearn.metrics import roc_auc_score

    probabilities = train.predict(model, (x,))
    assert roc_auc_score(labels[val_rows].numpy(), probabilities[val_rows.numpy()]) == pytest.approx(fitted.best_val_auc)
    assert train.positive_weight(torch.tensor([1.0, 0.0, 0.0, 0.0])) == pytest.approx(3.0)


def test_grid_lists_every_combination():
    spec = {"kind": "mlp", "grid": {"hidden": [8, 16], "lr": [0.1]}}
    assert baselines.grid(spec) == [{"hidden": 8, "lr": 0.1}, {"hidden": 16, "lr": 0.1}]
    assert baselines.grid({"kind": "majority"}) == [{}]


@pytest.mark.parametrize("name", list(SPECS))
def test_every_baseline_gives_a_probability_for_every_article(synthetic, name):
    graph, labels, split = synthetic
    data = make_data(graph, labels, split, with_graph=name == "gcn")
    spec, params = SPECS[name]
    probabilities, fitted = baselines.run(spec, params, data, seed=0, settings=SETTINGS)
    assert probabilities.shape == labels.shape and ((probabilities >= 0) & (probabilities <= 1)).all()
    assert (fitted is None) == (name in ("majority", "logistic", "gbt"))
    assert 0 not in data.rows("train")  # the article without a decision is never a target
    if name == "majority":
        assert np.unique(probabilities).tolist() == [pytest.approx(np.nanmean(labels[split == "train"]))]
    else:
        from sklearn.metrics import roc_auc_score

        test = data.rows("test")
        assert roc_auc_score(labels[test], probabilities[test]) > 0.7  # ratings carry the outcome in this graph
    again, _ = baselines.run(spec, params, data, seed=0, settings=SETTINGS)
    assert np.array_equal(probabilities, again)  # same seed, same result (CPU)


def test_unknown_kind_is_refused(synthetic):
    data = make_data(*synthetic, with_graph=False)
    with pytest.raises(ValueError, match="unknown kind"):
        baselines.run({"kind": "forest"}, {}, data, 0, SETTINGS)
