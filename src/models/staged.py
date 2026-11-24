"""Graph models trained on one graph, validated on a second and applied to others.

In phases 6 and 7 a graph model is trained and validated on the graph of the training
years and applied to the whole graph (src/models/hetero.py, src/models/baselines.py).
The protocol checks need the same thing with other graphs: a validation year predicted
on the graph that holds it, a holdout year predicted on a third graph. A `Stage` is one
such graph, restricted to the articles of some years, with the inputs a model reads.

With the stages of phases 6 and 7 (training and validation on the graph of the training
years, test on the whole graph), `run` gives the predictions of `hetero.run` and
`baselines.run_gcn` (tests/test_protocol.py).
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import nn
from torch_geometric.data import HeteroData

from src.kg.build import article_masks, article_subgraph
from src.models import features, train
from src.models.baselines import GCN
from src.models.hetero import KINDS, HeteroGNN
from src.utils.seed import set_seed


TRAIN, VAL, TEST, HOLDOUT = "train", "val", "test", "holdout"
# Role of a paper in a stage, from its split in the study. `rolling`: every paper of the
# training years is a training paper, the test year is the validation year and the
# holdout year is the test year.
ROLES = {"study": {TRAIN: TRAIN, VAL: VAL, TEST: TEST, HOLDOUT: HOLDOUT},
         "rolling": {TRAIN: TRAIN, VAL: TRAIN, TEST: VAL, HOLDOUT: TEST}}


def roles_of(scheme: str, split: np.ndarray) -> np.ndarray:
    """Role of each article in a stage of the protocol checks."""
    if scheme not in ROLES:
        raise ValueError(f"unknown scheme of roles: {scheme!r}")
    return np.array([ROLES[scheme][name] for name in split], dtype=object)


def move(inputs: Any, device: str) -> Any:
    """Tensors of nested tuples and dictionaries moved to a device."""
    if isinstance(inputs, torch.Tensor):
        return inputs.to(device)
    if isinstance(inputs, dict):
        return {key: move(value, device) for key, value in inputs.items()}
    return tuple(move(value, device) for value in inputs)


@dataclass
class Stage:
    inputs: tuple          # what the model is called with; it returns one logit per entry of `articles`
    articles: np.ndarray   # article index, in the whole graph, of each of these logits

    def to(self, device: str) -> "Stage":
        return Stage(move(self.inputs, device), self.articles)

    def position(self, rows: np.ndarray, n_articles: int) -> np.ndarray:
        """Where the articles `rows` are in the output of the model on this stage."""
        index = np.full(n_articles, -1)
        index[self.articles] = np.arange(len(self.articles))
        found = index[rows]
        if (found < 0).any():
            raise ValueError("an article to read is not in the graph of this stage")
        return found


def scaled_graph(graph: HeteroData, layout: features.Layout, fit_articles: np.ndarray) -> HeteroData:
    """The graph with its features scaled by the statistics of the articles `fit_articles`
    (a mask) and of the nodes that belong to them. Edges are shared with `graph`."""
    x = features.standardise(graph, layout, features.training_nodes(graph, torch.from_numpy(fit_articles)))
    scaled = HeteroData()
    for node_type in graph.node_types:
        scaled[node_type].x = x[node_type]
    for edge_type in graph.edge_types:
        scaled[edge_type].edge_index = graph[edge_type].edge_index
    return scaled


def hetero_stage(scaled: HeteroData, articles: np.ndarray, extra: np.ndarray | None = None) -> Stage:
    """Heterogeneous graph restricted to the articles of a mask, with what belongs to
    them. `extra`: columns added to the features of the articles (one row per article of
    the whole graph)."""
    mask = torch.from_numpy(articles)
    part = scaled if bool(mask.all()) else article_subgraph(scaled, mask)
    x = dict(part.x_dict)
    if extra is not None:
        x["article"] = torch.cat([x["article"], torch.from_numpy(extra[articles]).float()], dim=1)
    return Stage((x, dict(part.edge_index_dict)), np.flatnonzero(articles))


def with_article_columns(stage: Stage, extra: np.ndarray) -> Stage:
    """The same stage with columns added to the article features; everything else is shared."""
    x, edges = stage.inputs
    x = dict(x)
    x["article"] = torch.cat([x["article"], torch.from_numpy(extra[stage.articles]).float().to(x["article"].device)], dim=1)
    return Stage((x, edges), stage.articles)


def flat_stage(graph: HeteroData, flat: features.FlatGraph, articles: np.ndarray) -> Stage:
    """Flattened graph (the one the GCN reads) restricted to the articles of a mask."""
    everyone = torch.arange(graph["article"].num_nodes)
    mask = torch.from_numpy(articles)
    if bool(mask.all()):
        return Stage((flat.x, flat.edge_index, flat.nodes("article", everyone)), np.flatnonzero(articles))
    x, edges, new_index = features.flat_subgraph(flat, features.flat_mask(flat, article_masks(graph, mask)))
    return Stage((x, edges, new_index[flat.nodes("article", everyone[mask])]), np.flatnonzero(articles))


def build_model(kind: str, params: dict[str, Any], stage: Stage, heads: int) -> nn.Module:
    """An untrained model of `kind` ("gcn" or a heterogeneous architecture) for the inputs of a stage."""
    if kind == "gcn":
        return GCN(stage.inputs[0].shape[1], params["hidden"], params["layers"], params["dropout"])
    if kind not in KINDS:
        raise ValueError(f"unknown kind of graph model: {kind!r}")
    x, edges = stage.inputs
    metadata = (list(x), list(edges))
    return HeteroGNN(kind, metadata, {node_type: value.shape[1] for node_type, value in x.items()},
                     params["hidden"], params["layers"], params["dropout"], heads)


def predict(model: nn.Module, stage: Stage, device: str, log=None) -> np.ndarray:
    """Probability of each article of a stage. The stage is moved to `device` for the
    prediction; if the GPU runs out of memory, the prediction is computed on the CPU."""
    try:
        return train.predict(model.to(device), move(stage.inputs, device))
    except torch.OutOfMemoryError:
        if log is not None:
            log.warning("out of memory on the GPU: this prediction is computed on the CPU")
        torch.cuda.empty_cache()
        probabilities = train.predict(model.to("cpu"), move(stage.inputs, "cpu"))
        model.to(device)
        return probabilities


def run(kind: str, params: dict[str, Any], training: dict[str, Any], seed: int, labels: np.ndarray,
        train_stage: Stage, train_rows: np.ndarray, val_stage: Stage, val_rows: np.ndarray,
        plan: list[tuple[Stage, np.ndarray]], device: str, log=None) -> tuple[np.ndarray, train.Fit, nn.Module]:
    """(probability of acceptance of the articles read in `plan`, missing elsewhere;
    training summary; trained model).

    `train_stage` and `val_stage` must already be on `device` (they are used at every
    epoch); they are the same object when the validation articles are in the training
    graph. `plan`: (stage, articles to read from it), applied in order. `training`:
    weight_decay, max_epochs, patience, and heads for a heterogeneous model. `labels`:
    one value per article of the whole graph, only read on the training and validation rows.
    """
    set_seed(seed)
    n = len(labels)
    model = build_model(kind, params, train_stage, training.get("heads", 1)).to(device)
    train_labels = torch.from_numpy(labels[train_stage.articles]).float().to(device)
    validation = None
    if val_stage is not train_stage:
        validation = (val_stage.inputs, torch.from_numpy(labels[val_stage.articles]).float().to(device))
    fitted = train.fit(model, train_stage.inputs, train_labels, torch.from_numpy(train_stage.position(train_rows, n)).to(device),
                       torch.from_numpy(val_stage.position(val_rows, n)).to(device), lr=params["lr"],
                       weight_decay=training["weight_decay"], max_epochs=training["max_epochs"], patience=training["patience"],
                       validation=validation)
    probabilities = np.full(n, np.nan)
    for stage, rows in plan:
        if len(rows) == 0:
            continue
        if device != "cpu":
            torch.cuda.empty_cache()
        probabilities[rows] = predict(model, stage, device, log)[stage.position(rows, n)]
    return probabilities, fitted, model
