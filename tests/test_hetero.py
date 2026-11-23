"""Phase 7: heterogeneous GNNs on a small random graph, on CPU."""

import numpy as np
import pytest
import torch
from sklearn.metrics import roc_auc_score
from test_baselines import LAYOUT, synthetic_graph

from src.models import baselines, features, hetero

SETTINGS = {"heads": 2, "weight_decay": 0.0, "max_epochs": 100, "patience": 40}
PARAMS = {"layers": 2, "hidden": 16, "dropout": 0.0, "lr": 0.01}


@pytest.fixture(scope="module")
def task():
    graph, labels, split = synthetic_graph()
    data = baselines.Data(features.article_table(graph, LAYOUT), labels, split)
    return graph, data, hetero.hetero_views(graph, LAYOUT, split, "cpu")


def test_views_keep_the_training_years_for_training_and_everything_for_prediction(task):
    graph, data, views = task
    known = data.split != "test"
    assert views.train_articles.tolist() == np.flatnonzero(known).tolist()
    assert views.train_inputs[0]["article"].shape[0] == known.sum()
    assert views.full_inputs[0]["article"].shape[0] == len(known)
    assert views.in_dims == {node_type: graph[node_type].x.shape[1] for node_type in graph.node_types}
    assert set(views.metadata[1]) == set(graph.edge_types)
    # the training graph only holds reviews of the training years
    articles, _ = graph["article", "has_review", "review"].edge_index.numpy()
    assert views.train_inputs[0]["review"].shape[0] == known[articles].sum()
    assert torch.equal(views.train_inputs[0]["article"], views.full_inputs[0]["article"][torch.from_numpy(known)])


def test_score_statistics_can_be_added_to_the_article_nodes(task):
    _, data, views = task
    extra = data.table.design(["rating", "other_scores"], data.rows("train"))
    wider = hetero.with_article_columns(views, extra, "cpu")
    assert wider.in_dims["article"] == views.in_dims["article"] + 17 and wider.in_dims["review"] == views.in_dims["review"]
    assert torch.equal(wider.full_inputs[0]["article"][:, -17:], torch.from_numpy(extra))
    assert torch.equal(wider.train_inputs[0]["article"][:, -17:], torch.from_numpy(extra[views.train_articles]))
    assert views.full_inputs[0]["article"].shape[1] == views.in_dims["article"]  # the plain views are untouched
    assert wider.train_inputs[0]["review"] is views.train_inputs[0]["review"]


@pytest.mark.parametrize("kind", hetero.KINDS)
def test_every_architecture_learns_and_is_reproducible(task, kind):
    _, data, views = task
    probabilities, fitted, model = hetero.run(kind, PARAMS, data, views, seed=0, settings=SETTINGS)
    assert probabilities.shape == data.labels.shape and ((probabilities >= 0) & (probabilities <= 1)).all()
    test = data.rows("test")
    assert roc_auc_score(data.labels[test], probabilities[test]) > 0.7  # ratings carry the outcome in this graph
    assert fitted.best_val_auc > 0.7 and len(model.convs) == PARAMS["layers"]
    again, _, _ = hetero.run(kind, PARAMS, data, views, seed=0, settings=SETTINGS)
    assert np.array_equal(probabilities, again)
    # the saved weights give the same predictions
    clone = hetero.HeteroGNN(kind, views.metadata, views.in_dims, PARAMS["hidden"], PARAMS["layers"], PARAMS["dropout"], SETTINGS["heads"])
    clone.load_state_dict(model.state_dict())
    from src.models import train

    assert np.array_equal(train.predict(clone, views.full_inputs)[test], probabilities[test])


def test_unknown_architecture_is_refused(task):
    _, _, views = task
    with pytest.raises(ValueError, match="unknown kind"):
        hetero.HeteroGNN("gat", views.metadata, views.in_dims, 8, 2, 0.0)
