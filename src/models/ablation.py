"""Ablated copies of a graph: node types, relations or feature blocks taken out.

A variant is described by what it removes:
    drop_nodes     node types; every relation that touches them goes with them
    drop_edges     relation names; the inverse relation (`rev_<name>`) goes with it
    drop_features  {node type: [feature blocks]}; the remaining blocks are moved up
Nothing else changes: the other nodes, edges, features and node attributes are those of
the original graph.
"""

from typing import Any

import torch
from torch_geometric.data import HeteroData

from src.kg.build import REVERSE_PREFIX
from src.models.features import Layout


def ablated_graph(graph: HeteroData, layout: Layout, spec: dict[str, Any] | None) -> tuple[HeteroData, Layout]:
    """(graph without what `spec` removes, its feature layout). An empty spec returns
    the graph itself."""
    spec = spec or {}
    unknown = sorted(set(spec) - {"drop_nodes", "drop_edges", "drop_features"})
    if unknown:
        raise ValueError(f"unknown keys in an ablation: {unknown}")
    drop_nodes, drop_edges = set(spec.get("drop_nodes", [])), set(spec.get("drop_edges", []))
    drop_features = {node_type: set(blocks) for node_type, blocks in spec.get("drop_features", {}).items()}
    if not (drop_nodes or drop_edges or drop_features):
        return graph, layout

    relations = {relation.removeprefix(REVERSE_PREFIX) for _, relation, _ in graph.edge_types}
    missing = sorted(drop_nodes - set(graph.node_types)) + sorted(drop_edges - relations)
    for node_type, blocks in drop_features.items():
        known = {block["name"] for block in layout.get(node_type, [])}
        missing += sorted(f"{node_type}.{block}" for block in blocks - known)
    if missing:
        raise ValueError(f"an ablation removes what the graph does not have: {missing}")
    if drop_nodes & set(drop_features):
        raise ValueError(f"an ablation removes both the nodes and features of {sorted(drop_nodes & set(drop_features))}")

    out, new_layout = HeteroData(), {}
    for node_type in graph.node_types:
        if node_type in drop_nodes:
            continue
        kept = [block for block in layout[node_type] if block["name"] not in drop_features.get(node_type, set())]
        if not kept:
            raise ValueError(f"no feature left on the nodes '{node_type}': remove the node type instead")
        for key, value in graph[node_type].items():
            if key != "x":
                out[node_type][key] = value
        out[node_type].x = torch.cat([graph[node_type].x[:, block["start"]:block["end"]] for block in kept], dim=1)
        new_layout[node_type], start = [], 0
        for block in kept:
            width = block["end"] - block["start"]
            new_layout[node_type].append({"name": block["name"], "start": start, "end": start + width})
            start += width
    for edge_type in graph.edge_types:
        source, relation, target = edge_type
        if source in drop_nodes or target in drop_nodes or relation.removeprefix(REVERSE_PREFIX) in drop_edges:
            continue
        for key, value in graph[edge_type].items():
            out[edge_type][key] = value
    return out, new_layout
