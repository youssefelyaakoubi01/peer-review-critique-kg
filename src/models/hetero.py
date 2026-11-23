"""Heterogeneous GNNs on the knowledge graph: R-GCN, HAN and HGT.

Every model projects the features of each node type to a common size, applies its
layers, and reads the article nodes with a linear head. Training only sees the articles
of the training years; the test articles are predicted on the whole graph.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.data import HeteroData
from torch_geometric.nn import HANConv, HGTConv, RGCNConv

from src.kg.build import article_subgraph
from src.models import features, train
from src.models.baselines import TRAIN, VAL, Data
from src.utils.seed import set_seed

KINDS = ("rgcn", "han", "hgt")
Inputs = tuple[dict[str, torch.Tensor], dict[tuple[str, str, str], torch.Tensor]]


class HeteroGNN(nn.Module):
    def __init__(self, kind: str, metadata: tuple[list[str], list[tuple[str, str, str]]], in_dims: dict[str, int],
                 hidden: int, layers: int, dropout: float, heads: int = 4):
        super().__init__()
        if kind not in KINDS:
            raise ValueError(f"unknown kind of heterogeneous GNN: {kind!r}")
        self.kind, self.node_types, self.edge_types, self.dropout = kind, list(metadata[0]), list(metadata[1]), dropout
        self.inputs = nn.ModuleDict({node_type: nn.Linear(in_dims[node_type], hidden) for node_type in self.node_types})
        if kind == "rgcn":  # one weight matrix per relation, no basis decomposition
            self.convs = nn.ModuleList([RGCNConv(hidden, hidden, len(self.edge_types)) for _ in range(layers)])
        elif kind == "han":  # attention over the neighbours of each relation, then over the relations; residual connection
            self.convs = nn.ModuleList([HANConv(hidden, hidden, metadata, heads=heads) for _ in range(layers)])
        else:
            self.convs = nn.ModuleList([HGTConv(hidden, hidden, metadata, heads=heads) for _ in range(layers)])
        self.head = nn.Linear(hidden, 1)

    def regularise(self, h: torch.Tensor) -> torch.Tensor:
        return F.dropout(F.relu(h), self.dropout, self.training)

    def forward(self, x: dict[str, torch.Tensor],
                edges: dict[tuple[str, str, str], torch.Tensor] | list[dict[tuple[str, str, str], torch.Tensor]]) -> torch.Tensor:
        """One logit per article node. `edges`: the edges of the graph, or one set of
        edges per layer (explanations only give each layer the edges it needs)."""
        per_layer = list(edges) if isinstance(edges, (list, tuple)) else [edges] * len(self.convs)
        if len(per_layer) != len(self.convs):
            raise ValueError(f"{len(per_layer)} sets of edges for {len(self.convs)} layers")
        h = {node_type: self.regularise(self.inputs[node_type](x[node_type])) for node_type in self.node_types}
        if self.kind == "rgcn":
            offsets, total = {}, 0
            for node_type in self.node_types:
                offsets[node_type], total = total, total + h[node_type].shape[0]
            z = torch.cat([h[node_type] for node_type in self.node_types])
            merged = {}  # merged edge index of each distinct set of edges
            for conv, layer_edges in zip(self.convs, per_layer):
                if id(layer_edges) not in merged:
                    index = torch.cat([layer_edges[e] + torch.tensor([[offsets[e[0]]], [offsets[e[2]]]], device=z.device)
                                       for e in self.edge_types], dim=1)
                    relation = torch.cat([torch.full((layer_edges[e].shape[1],), i, device=z.device) for i, e in enumerate(self.edge_types)])
                    merged[id(layer_edges)] = (index, relation)
                z = self.regularise(conv(z, *merged[id(layer_edges)]))
            articles = z[offsets["article"]:offsets["article"] + h["article"].shape[0]]
        else:
            # HANConv only returns what a node receives from its neighbours: without the
            # residual connection, a node would lose its own features at every layer (the
            # scores of a review would never reach its article with two layers). HGTConv
            # has its own skip connection.
            residual = self.kind == "han"
            for conv, layer_edges in zip(self.convs, per_layer):
                out = conv(h, layer_edges)
                h = {node_type: h[node_type] if out.get(node_type) is None
                     else self.regularise(out[node_type]) + (h[node_type] if residual else 0)
                     for node_type in self.node_types}
            articles = h["article"]
        return self.head(articles).squeeze(-1)


@dataclass
class HeteroViews:
    train_inputs: Inputs           # graph of the training years, on the training device
    train_articles: np.ndarray     # article index of each article node of that graph
    full_inputs: Inputs            # whole graph, kept on CPU until a prediction needs it
    metadata: tuple[list[str], list[tuple[str, str, str]]]
    in_dims: dict[str, int]


def hetero_views(graph: HeteroData, layout: features.Layout, split: np.ndarray, device: str,
                 article_extra: np.ndarray | None = None) -> HeteroViews:
    """Standardised graph (statistics of the training articles) and its restriction to
    the training years. `article_extra`: columns added to the features of the articles."""
    # the graph a model is trained on: the articles of the training years (training and
    # validation splits); test and holdout articles are never in it
    is_train, known = torch.from_numpy(split == TRAIN), torch.from_numpy(np.isin(split, (TRAIN, VAL)))
    x = features.standardise(graph, layout, features.training_nodes(graph, is_train))
    if article_extra is not None:
        x["article"] = torch.cat([x["article"], torch.from_numpy(article_extra).float()], dim=1)
    scaled = HeteroData()
    for node_type in graph.node_types:
        scaled[node_type].x = x[node_type]
    for edge_type in graph.edge_types:
        scaled[edge_type].edge_index = graph[edge_type].edge_index
    training = article_subgraph(scaled, known)
    return HeteroViews(
        train_inputs=({t: v.to(device) for t, v in training.x_dict.items()}, {e: v.to(device) for e, v in training.edge_index_dict.items()}),
        train_articles=np.flatnonzero(known.numpy()),
        full_inputs=(dict(scaled.x_dict), dict(scaled.edge_index_dict)),
        metadata=scaled.metadata(), in_dims={t: v.shape[1] for t, v in x.items()})


def with_article_columns(views: HeteroViews, extra: np.ndarray, device: str) -> HeteroViews:
    """The same views with columns added to the article features (everything else is shared)."""
    extra = torch.from_numpy(extra).float()
    train_x, full_x = dict(views.train_inputs[0]), dict(views.full_inputs[0])
    train_x["article"] = torch.cat([train_x["article"], extra[views.train_articles].to(device)], dim=1)
    full_x["article"] = torch.cat([full_x["article"], extra], dim=1)
    return HeteroViews((train_x, views.train_inputs[1]), views.train_articles, (full_x, views.full_inputs[1]), views.metadata,
                       {**views.in_dims, "article": full_x["article"].shape[1]})


def run(kind: str, params: dict[str, Any], data: Data, views: HeteroViews, seed: int,
        settings: dict[str, Any]) -> tuple[np.ndarray, train.Fit, HeteroGNN]:
    """(probability of acceptance of every article, training summary, trained model).
    Articles of the training years are predicted on the graph of these years (the one
    the validation AUC is computed on); test articles on the whole graph."""
    set_seed(seed)
    position = np.full(len(data.labels), -1)
    position[views.train_articles] = np.arange(len(views.train_articles))
    labels = torch.from_numpy(data.labels[views.train_articles]).float().to(data.device)
    model = HeteroGNN(kind, views.metadata, views.in_dims, params["hidden"], params["layers"], params["dropout"],
                      settings["heads"]).to(data.device)
    fitted = train.fit(model, views.train_inputs, labels, torch.from_numpy(position[data.rows(TRAIN)]).to(data.device),
                       torch.from_numpy(position[data.rows(VAL)]).to(data.device), lr=params["lr"],
                       weight_decay=settings["weight_decay"], max_epochs=settings["max_epochs"], patience=settings["patience"])
    known = train.predict(model, views.train_inputs)
    if data.device != "cpu":
        torch.cuda.empty_cache()
    full = tuple({key: value.to(data.device) for key, value in part.items()} for part in views.full_inputs)
    probabilities = train.predict(model, full)
    probabilities[views.train_articles] = known
    return probabilities, fitted, model
