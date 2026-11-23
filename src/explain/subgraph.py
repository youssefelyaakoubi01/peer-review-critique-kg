"""Computation graph of one article: what its prediction depends on, and nothing else.

With L layers, the logit of an article only depends on the nodes within L hops (along
incoming edges). Layer l (0-based) only needs the edges that point to a node within
L - 1 - l hops: the last layer only the edges into the article itself. Giving each layer
these edges, and no other, reproduces the prediction made on the whole graph exactly,
at a small fraction of its cost.

Occlusion: an element is removed from this computation graph and the logit is computed
again. A removed node keeps its row of features but loses every edge, which for the
article is the same as deleting it.
"""

from dataclasses import dataclass

import torch
from torch import Tensor

from src.kg.build import REVERSE_PREFIX

EdgeType = tuple[str, str, str]
LayerEdges = list[dict[EdgeType, Tensor]]


@dataclass
class Neighbourhood:
    x: dict[str, Tensor]          # features of the nodes within L hops, per node type
    layer_edges: LayerEdges       # edges needed by each layer, in local indices
    nodes: dict[str, Tensor]      # index in the whole graph of each local node
    target: int                   # local index of the article
    reviews: Tensor               # local index of the reviews of the article
    critiques: Tensor             # local index of the critiques of these reviews

    @property
    def n_nodes(self) -> int:
        return sum(len(index) for index in self.nodes.values())


class GraphIndex:
    """Features and edges of the whole graph, from which neighbourhoods are cut."""

    def __init__(self, x: dict[str, Tensor], edges: dict[EdgeType, Tensor]):
        self.x, self.edges = x, edges
        self.sizes = {node_type: len(features) for node_type, features in x.items()}

    def hops(self, article: int, n: int) -> list[dict[str, Tensor]]:
        """masks[k]: nodes within k hops of the article (along incoming edges), k = 0..n."""
        masks = {node_type: torch.zeros(size, dtype=torch.bool) for node_type, size in self.sizes.items()}
        masks["article"][article] = True
        out = [masks]
        for _ in range(n):
            new = {node_type: mask.clone() for node_type, mask in masks.items()}
            for (source, _, target), index in self.edges.items():
                new[source][index[0][masks[target][index[1]]]] = True
            masks = new
            out.append(masks)
        return out

    def neighbourhood(self, article: int, layers: int) -> Neighbourhood:
        masks = self.hops(article, layers)
        everything = masks[layers]
        local = {node_type: torch.cumsum(mask.long(), 0) - 1 for node_type, mask in everything.items()}
        layer_edges = []
        for layer in range(layers):
            reached = masks[layers - 1 - layer]
            edges = {}
            for edge_type, index in self.edges.items():
                source, _, target = edge_type
                keep = reached[target][index[1]] & everything[source][index[0]]
                edges[edge_type] = torch.stack([local[source][index[0][keep]], local[target][index[1][keep]]])
            layer_edges.append(edges)
        return Neighbourhood(
            x={node_type: self.x[node_type][mask] for node_type, mask in everything.items()},
            layer_edges=layer_edges,
            nodes={node_type: mask.nonzero().squeeze(1) for node_type, mask in everything.items()},
            target=int(local["article"][article]),
            # one hop: the reviews of the article; two hops: the critiques of these reviews
            reviews=local["review"][masks[1]["review"]],
            critiques=local["critique"][masks[2]["critique"]] if "critique" in masks[2] else torch.empty(0, dtype=torch.long))


def logit(model: torch.nn.Module, hood: Neighbourhood, x: dict[str, Tensor] | None = None,
          layer_edges: LayerEdges | None = None) -> Tensor:
    """Logit of the article (scalar tensor), on the neighbourhood or a modified copy of it."""
    return model(hood.x if x is None else x, hood.layer_edges if layer_edges is None else layer_edges)[hood.target]


def drop_nodes(layer_edges: LayerEdges, node_type: str, local_ids: Tensor) -> LayerEdges:
    """Edges without those that leave or enter the given nodes."""
    if len(local_ids) == 0:
        return layer_edges
    out = []
    for edges in layer_edges:
        kept = {}
        for edge_type, index in edges.items():
            source, _, target = edge_type
            if node_type in (source, target) and index.shape[1]:
                keep = torch.ones(index.shape[1], dtype=torch.bool)
                if source == node_type:
                    keep &= ~torch.isin(index[0], local_ids)
                if target == node_type:
                    keep &= ~torch.isin(index[1], local_ids)
                index = index[:, keep]
            kept[edge_type] = index
        out.append(kept)
    return out


def drop_relation(layer_edges: LayerEdges, relation: str) -> LayerEdges:
    """Edges without a relation and its inverse (`rev_<relation>`)."""
    return [{edge_type: index[:, :0] if edge_type[1].removeprefix(REVERSE_PREFIX) == relation else index
             for edge_type, index in edges.items()} for edges in layer_edges]


def relations(edge_types: list[EdgeType]) -> list[str]:
    """Names of the relations, without their inverses, in the order of the graph."""
    return list(dict.fromkeys(relation.removeprefix(REVERSE_PREFIX) for _, relation, _ in edge_types))
