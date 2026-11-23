"""Importance by occlusion, and fidelity of an explanation.

Importance of an element = logit of the article with the element minus its logit
without it: positive when the element pushes the prediction towards acceptance.
"""

import numpy as np
import torch
from torch import Tensor

from src.explain import subgraph
from src.explain.subgraph import Neighbourhood


@torch.no_grad()
def critique_importances(model: torch.nn.Module, hood: Neighbourhood) -> tuple[float, np.ndarray]:
    """(logit of the article, importance of each of its critiques, removed one at a time)."""
    base = float(subgraph.logit(model, hood))
    without = [float(subgraph.logit(model, hood, layer_edges=subgraph.drop_nodes(hood.layer_edges, "critique", critique.view(1))))
               for critique in hood.critiques]
    return base, base - np.array(without, dtype=float)


@torch.no_grad()
def relation_importances(model: torch.nn.Module, hood: Neighbourhood, base: float, relations: list[str]) -> dict[str, float]:
    """Importance of each relation, removed entirely (with its inverse)."""
    return {relation: base - float(subgraph.logit(model, hood, layer_edges=subgraph.drop_relation(hood.layer_edges, relation)))
            for relation in relations}


@torch.no_grad()
def reference_importances(model: torch.nn.Module, hood: Neighbourhood, base: float, score_columns: list[int]) -> dict[str, float]:
    """Scale of the importances: the scores of the reviews of the article set to the
    training mean (zero after standardisation), and all its critiques removed at once."""
    x = dict(hood.x)
    x["review"] = hood.x["review"].clone()
    rows = hood.reviews.repeat_interleave(len(score_columns))
    x["review"][rows, torch.tensor(score_columns).repeat(len(hood.reviews))] = 0.0
    no_critique = subgraph.drop_nodes(hood.layer_edges, "critique", hood.critiques)
    return {"scores": base - float(subgraph.logit(model, hood, x=x)),
            "critiques": base - float(subgraph.logit(model, hood, layer_edges=no_critique))}


def top(scores: np.ndarray, k: int) -> np.ndarray:
    """Positions of the k largest scores in absolute value (first position wins a tie)."""
    return np.argsort(-np.abs(scores), kind="stable")[:k]


@torch.no_grad()
def fidelity(model: torch.nn.Module, hood: Neighbourhood, scores: np.ndarray, ks: list[int],
             rng: np.random.Generator) -> list[dict[str, float]]:
    """For each k not larger than the number of critiques: probability of acceptance when
    the k most important critiques are removed (fidelity+), when only they are kept
    (fidelity-), and the same for k critiques drawn at random."""
    def probability(removed: Tensor) -> float:
        edges = subgraph.drop_nodes(hood.layer_edges, "critique", removed)
        return float(torch.sigmoid(subgraph.logit(model, hood, layer_edges=edges)))

    n, rows = len(hood.critiques), []
    for k in ks:
        if k > n:
            continue
        chosen = {"top": top(scores, k), "random": rng.choice(n, size=k, replace=False)}
        row = {"k": k}
        for name, positions in chosen.items():
            others = np.setdiff1d(np.arange(n), positions)
            row[f"{name}_removed"] = probability(hood.critiques[torch.from_numpy(positions)])
            row[f"{name}_kept"] = probability(hood.critiques[torch.from_numpy(others)])
        rows.append(row)
    return rows
