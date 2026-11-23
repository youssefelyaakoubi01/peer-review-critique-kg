"""Baselines: majority class, logistic regression, gradient boosting, MLP, and a GCN on
the flattened graph.

Every baseline returns the probability of acceptance of every article. Labels are
only read on the training rows (loss) and on the validation rows (early stopping).
"""

import itertools
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from torch import nn
from torch_geometric.data import HeteroData
from torch_geometric.nn import GCNConv

from src.kg.build import article_masks
from src.models import features, train
from src.utils.seed import set_seed

TRAIN, VAL, TEST = "train", "val", "test"


@dataclass
class GraphViews:
    """Flattened graph, as the GCN reads it. Training only sees the articles of the
    training years; the test articles are predicted on the whole graph."""
    train_inputs: tuple            # features, edges, rows of the articles: training years only
    train_articles: np.ndarray     # article index of each of these rows
    full_inputs: tuple             # the same for the whole graph, every article


@dataclass
class Data:
    table: features.ArticleTable
    labels: np.ndarray             # 1 accepted, 0 rejected, nan without a decision
    split: np.ndarray              # "train", "val" or "test" for each article
    device: str = "cpu"
    graph: GraphViews | None = None

    def rows(self, split: str) -> np.ndarray:
        """Articles of a split that have a decision."""
        return np.flatnonzero((self.split == split) & ~np.isnan(self.labels))


def graph_views(graph: HeteroData, layout: features.Layout, split: np.ndarray, device: str, full_device: str | None = None) -> GraphViews:
    """`full_device`: where the whole graph is kept for the predictions (default: `device`).
    A graph too large for the GPU is predicted on the CPU; the training graph stays on `device`."""
    full_device = full_device or device
    # the graph a model is trained on: the articles of the training years (training and
    # validation splits); test and holdout articles are never in it
    is_train, known = torch.from_numpy(split == TRAIN), torch.from_numpy(np.isin(split, (TRAIN, VAL)))
    x = features.standardise(graph, layout, features.training_nodes(graph, is_train))
    flat = features.flatten(graph, x, layout)
    sub_x, sub_edges, new_index = features.flat_subgraph(flat, features.flat_mask(flat, article_masks(graph, known)))
    everyone = torch.arange(graph["article"].num_nodes)
    return GraphViews(
        train_inputs=(sub_x.to(device), sub_edges.to(device), new_index[flat.nodes("article", everyone[known])].to(device)),
        train_articles=everyone[known].numpy(),
        full_inputs=(flat.x.to(full_device), flat.edge_index.to(full_device), flat.nodes("article", everyone).to(full_device)))


class MLP(nn.Module):
    def __init__(self, in_dim: int, hidden: int, dropout: float):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(in_dim, hidden), nn.ReLU(), nn.Dropout(dropout),
                                    nn.Linear(hidden, hidden), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x).squeeze(-1)


class GCN(nn.Module):
    """One weight matrix per layer for all nodes and all edges; a linear head on the articles."""

    def __init__(self, in_dim: int, hidden: int, layers: int, dropout: float):
        super().__init__()
        self.convs = nn.ModuleList([GCNConv(in_dim if i == 0 else hidden, hidden) for i in range(layers)])
        self.head = nn.Linear(hidden, 1)
        self.dropout = dropout

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, rows: torch.Tensor) -> torch.Tensor:
        for conv in self.convs:
            x = F.dropout(F.relu(conv(x, edge_index)), self.dropout, self.training)
        return self.head(x[rows]).squeeze(-1)


def grid(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Every combination of the hyper-parameter values listed in `spec["grid"]`."""
    names = list(spec.get("grid", {}))
    return [dict(zip(names, values)) for values in itertools.product(*(spec["grid"][name] for name in names))]


def run_majority(data: Data) -> np.ndarray:
    return np.full(len(data.labels), data.labels[data.rows(TRAIN)].mean())


def run_logistic(data: Data, blocks: list[str], params: dict[str, Any], seed: int) -> np.ndarray:
    train_rows = data.rows(TRAIN)
    x = data.table.design(blocks, train_rows)
    model = LogisticRegression(C=params["C"], class_weight="balanced", max_iter=5000, random_state=seed)
    model.fit(x[train_rows], data.labels[train_rows].astype(int))
    return model.predict_proba(x)[:, 1]


def run_gbt(data: Data, blocks: list[str], params: dict[str, Any], seed: int) -> np.ndarray:
    """Gradient-boosted trees; no early stopping, so no row is held out of the training set."""
    train_rows = data.rows(TRAIN)
    x = data.table.design(blocks, train_rows)
    model = HistGradientBoostingClassifier(learning_rate=params["learning_rate"], max_iter=params["max_iter"],
                                           max_leaf_nodes=params["max_leaf_nodes"], class_weight="balanced",
                                           early_stopping=False, random_state=seed)
    model.fit(x[train_rows], data.labels[train_rows].astype(int))
    return model.predict_proba(x)[:, 1]


def run_mlp(data: Data, blocks: list[str], params: dict[str, Any], seed: int, settings: dict[str, Any]) -> tuple[np.ndarray, train.Fit]:
    set_seed(seed)
    x = torch.from_numpy(data.table.design(blocks, data.rows(TRAIN))).to(data.device)
    labels = torch.from_numpy(data.labels).float().to(data.device)
    model = MLP(x.shape[1], params["hidden"], params["dropout"]).to(data.device)
    fitted = train.fit(model, (x,), labels, torch.from_numpy(data.rows(TRAIN)).to(data.device),
                       torch.from_numpy(data.rows(VAL)).to(data.device), lr=params["lr"],
                       weight_decay=params["weight_decay"], **settings)
    return train.predict(model, (x,)), fitted


def run_gcn(data: Data, params: dict[str, Any], seed: int, settings: dict[str, Any]) -> tuple[np.ndarray, train.Fit]:
    """Articles of the training years are predicted on the graph of these years (the one
    the validation AUC is computed on); test articles on the whole graph."""
    set_seed(seed)
    views = data.graph
    position = np.full(len(data.labels), -1)
    position[views.train_articles] = np.arange(len(views.train_articles))
    labels = torch.from_numpy(data.labels[views.train_articles]).float().to(data.device)
    model = GCN(views.train_inputs[0].shape[1], params["hidden"], params["layers"], params["dropout"]).to(data.device)
    fitted = train.fit(model, views.train_inputs, labels, torch.from_numpy(position[data.rows(TRAIN)]).to(data.device),
                       torch.from_numpy(position[data.rows(VAL)]).to(data.device), lr=params["lr"],
                       weight_decay=params["weight_decay"], **settings)
    probabilities = train.predict(model.to(views.full_inputs[0].device), views.full_inputs)  # the whole graph may be on another device
    probabilities[views.train_articles] = train.predict(model.to(data.device), views.train_inputs)
    return probabilities, fitted


def run(spec: dict[str, Any], params: dict[str, Any], data: Data, seed: int, settings: dict[str, Any]) -> tuple[np.ndarray, train.Fit | None]:
    """(probability of acceptance of every article, training summary if the model is trained by epochs)."""
    kind = spec["kind"]
    if kind == "majority":
        return run_majority(data), None
    if kind == "logistic":
        return run_logistic(data, spec["features"], params, seed), None
    if kind == "gbt":
        return run_gbt(data, spec["features"], params, seed), None
    if kind == "mlp":
        return run_mlp(data, spec["features"], params, seed, settings)
    if kind == "gcn":
        return run_gcn(data, params, seed, settings)
    raise ValueError(f"unknown kind of baseline: {kind!r}")
