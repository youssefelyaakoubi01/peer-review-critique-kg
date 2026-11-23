"""Assembly of the PyTorch Geometric graphs from the node/edge tables and the embeddings.

A graph only holds model inputs: features, edges, and the year of each article and
review (needed to train on the training years only). Outcomes and splits are in the
separate targets file.
"""

from typing import Any

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import HeteroData

from src.kg.tables import (CRITIQUE_LABELS, HAS_REVIEW, CONTAINS, RESPONDS_TO, HAS_CONCEPT, SHARES_CONCEPT,
                           RESPONSE_TYPES, REVIEW_SCORES, GraphTables)

REVERSE_PREFIX = "rev_"


def one_hot(values: pd.Series, categories: tuple[str, ...]) -> np.ndarray:
    """One column per category; a missing value gives a row of zeros."""
    return np.stack([(values == category).to_numpy(dtype=np.float32) for category in categories], axis=1)


def feature_blocks(tables: GraphTables, embeddings: dict[str, np.ndarray]) -> dict[str, list[tuple[str, np.ndarray]]]:
    """Named blocks of columns of each node type, in the order they are concatenated."""
    nodes = tables.nodes
    critique = nodes["critique"]
    blocks = {
        "article": [("specter2", embeddings["article"]),
                    ("text_missing", (~nodes["article"]["text_available"]).to_numpy(dtype=np.float32)[:, None])],
        "review": [(score, nodes["review"][score].to_numpy(dtype=np.float32)[:, None]) for score in REVIEW_SCORES]
                  + [("text", embeddings["review"])],
        "critique": [("text", embeddings["critique"])]
                    + [(label, one_hot(critique[label], categories)) for label, categories in CRITIQUE_LABELS.items()]
                    + [("actionable", (critique["actionable"] == True).to_numpy(dtype=np.float32)[:, None])],  # noqa: E712
        "aspect": [("identity", np.eye(len(nodes["aspect"]), dtype=np.float32))],
        "concept": [("text", embeddings["concept"])],
    }
    if "response" in nodes:
        blocks["response"] = [("text", embeddings["response"]),
                              ("response_type", one_hot(nodes["response"]["response_type"], RESPONSE_TYPES))]
    return blocks


def feature_layout(blocks: dict[str, list[tuple[str, np.ndarray]]]) -> dict[str, list[dict[str, Any]]]:
    """Columns of each block in the feature matrix `x` of each node type."""
    layout = {}
    for node_type, parts in blocks.items():
        start, rows = 0, []
        for name, block in parts:
            rows.append({"name": name, "start": start, "end": start + block.shape[1]})
            start += block.shape[1]
        layout[node_type] = rows
    return layout


def build_graph(tables: GraphTables, embeddings: dict[str, np.ndarray]) -> tuple[HeteroData, dict[str, list[dict[str, Any]]]]:
    """(graph, feature layout). Every relation gets its inverse (`rev_<name>`), except
    the symmetric relation between articles, which already holds both directions."""
    blocks = feature_blocks(tables, embeddings)
    data = HeteroData()
    for node_type, parts in blocks.items():
        if {len(block) for _, block in parts} != {len(tables.nodes[node_type])}:
            raise ValueError(f"features of '{node_type}' are misaligned with its nodes")
        x = np.concatenate([block for _, block in parts], axis=1)
        if not np.isfinite(x).all():
            raise ValueError(f"features of '{node_type}' are not finite")
        data[node_type].x = torch.from_numpy(x)
    for node_type in ("article", "review"):
        data[node_type].year = torch.from_numpy(tables.nodes[node_type]["year"].to_numpy(dtype=np.int64))
    for (source, relation, target), (rows, cols) in tables.edges.items():
        index = torch.from_numpy(np.stack([rows, cols]))
        data[source, relation, target].edge_index = index
        weight = tables.edge_weights.get((source, relation, target))
        if weight is not None:
            data[source, relation, target].edge_weight = torch.from_numpy(weight)
        if source != target:
            data[target, REVERSE_PREFIX + relation, source].edge_index = index.flip(0)
    data.validate(raise_on_error=True)
    return data, feature_layout(blocks)


def member_of(parent_mask: torch.Tensor, edge_index: torch.Tensor, n_children: int) -> torch.Tensor:
    """Mask of the children (targets of the edges) whose parent (source) is kept."""
    mask = torch.zeros(n_children, dtype=torch.bool)
    mask[edge_index[1][parent_mask[edge_index[0]]]] = True
    return mask


def article_masks(data: HeteroData, article_mask: torch.Tensor) -> dict[str, torch.Tensor]:
    """Mask of the nodes of each type that belong to some articles: these articles,
    their reviews, the critiques of these reviews and the author responses to these
    critiques. Aspects and concepts are all kept. A node type the graph does not have
    (ablated graphs) is left out."""
    masks = {"article": article_mask}
    masks["review"] = member_of(article_mask, data[HAS_REVIEW].edge_index, data["review"].num_nodes)
    if "critique" in data.node_types:
        masks["critique"] = member_of(masks["review"], data[CONTAINS].edge_index, data["critique"].num_nodes)
    if "response" in data.node_types:
        reverse = data[RESPONDS_TO].edge_index.flip(0)  # critique -> response
        masks["response"] = member_of(masks["critique"], reverse, data["response"].num_nodes)
    for node_type in ("aspect", "concept"):
        if node_type in data.node_types:
            masks[node_type] = torch.ones(data[node_type].num_nodes, dtype=torch.bool)
    return masks


def article_subgraph(data: HeteroData, article_mask: torch.Tensor) -> HeteroData:
    """Graph restricted to some articles (see `article_masks`). Used to train on the
    training years without seeing the others."""
    return data.subgraph(article_masks(data, article_mask))


def statistics(tables: GraphTables, setting: str) -> pd.DataFrame:
    """Nodes and edges of a setting, by type, in total and by year where a year exists.
    Edges are counted once: inverse relations are not listed, and a pair of articles
    that share a concept counts for one."""
    rows = []
    for node_type, table in tables.nodes.items():
        by_year = table["year"].value_counts().sort_index().to_dict() if "year" in table.columns else {}
        rows.append({"setting": setting, "kind": "node", "type": node_type, "count": len(table),
                     **{f"count_{year}": n for year, n in by_year.items()}})
    for relation, (sources, _) in tables.edges.items():
        count = len(sources) // 2 if relation == SHARES_CONCEPT else len(sources)
        rows.append({"setting": setting, "kind": "edge", "type": " -".join((relation[0], relation[1])) + "-> " + relation[2],
                     "count": count})
    return pd.DataFrame(rows)


__all__ = ["build_graph", "article_masks", "article_subgraph", "feature_layout", "statistics", "HAS_CONCEPT"]
