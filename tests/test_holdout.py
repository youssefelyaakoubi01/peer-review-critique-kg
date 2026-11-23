"""Holdout year: the frozen models never read it before prediction, and the conclusions
of the test year are checked on it by a rule written before the run."""

import importlib.util
import re

import numpy as np
import pandas as pd
import pytest
import torch
from test_baselines import LAYOUT, SETTINGS, SPECS, make_data, synthetic_graph
from test_leakage import HETERO_PARAMS, HETERO_SETTINGS

from src.kg.build import article_masks
from src.models import baselines, features, hetero
from src.utils.config import REPO_ROOT, load_config


def script(name: str):
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), REPO_ROOT / "scripts" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def with_holdout():
    """The synthetic graph with half of its test articles moved to a holdout split."""
    graph, labels, split = synthetic_graph()
    split = split.copy()
    split[np.flatnonzero(split == "test")[::2]] = "holdout"
    return graph, labels, split


def run(name, graph, labels, split):
    if name in SPECS:
        spec, params = SPECS[name]
        return baselines.run(spec, params, make_data(graph, labels, split), 0, SETTINGS)[0]
    data = baselines.Data(features.article_table(graph, LAYOUT), labels, split)
    return hetero.run(name, HETERO_PARAMS, data, hetero.hetero_views(graph, LAYOUT, split, "cpu"), 0, HETERO_SETTINGS)[0]


@pytest.mark.parametrize("name", ["logistic", "gbt", "mlp", "gcn", "rgcn", "han", "hgt"])
def test_no_model_reads_the_holdout_year_before_prediction(name):
    graph, labels, split = with_holdout()
    holdout = split == "holdout"
    first = run(name, graph, labels, split)
    flipped = labels.copy()
    flipped[holdout] = 1 - flipped[holdout]
    assert np.array_equal(first, run(name, graph, flipped, split))  # holdout labels are never read
    changed = graph.clone()
    masks = article_masks(graph, torch.from_numpy(holdout))
    for node_type in ("article", "review", "critique"):
        changed[node_type].x[masks[node_type]] += 7.0  # everything that belongs to a holdout article
    second = run(name, changed, labels, split)
    known = np.isin(split, ("train", "val"))
    assert np.array_equal(first[known], second[known])  # same training: the holdout nodes are not in the training graph
    assert not np.allclose(first[holdout], second[holdout])  # they are read at prediction time only


def test_the_holdout_scripts_read_graphs_targets_and_saved_models_only():
    cfg = load_config()
    predict = (REPO_ROOT / "scripts" / "07c_holdout.py").read_text()
    assert "interim" not in predict and '"raw"' not in predict and "label_withdrawn_as_reject" not in predict
    assert set(re.findall(r'(?:processed|directory) / f?"([^"]+)"', predict)) == {"graph_{setting}.pt", "graph_features.json", "targets.parquet", "models"}
    assert "hetero.run(" not in predict and "train.fit(" not in predict  # no GNN is trained on the way
    results = (REPO_ROOT / "scripts" / "07d_holdout_results.py").read_text()
    assert "interim" not in results and "processed" not in results
    assert cfg["holdout"]["setting"] == "A" and cfg["splits"]["holdout"] and "grid" not in predict


def test_the_graph_extension_reads_no_outcome_to_build_the_graph():
    text = (REPO_ROOT / "scripts" / "05c_extend_graph.py").read_text()
    assert "outcomes" not in text and "reviews_final" in text  # reviews_final: one column, for the report on leftover markers only
    assert re.findall(r'reviews_final\.parquet", columns=\[([^\]]+)\]', text) == ['"review_id", "modified_after_release"']
    assert text.index("torch.save(graph") < text.index("reviews_final")  # the graph is written before that table is opened
    assert text.count("load_labels(") == 2  # usable papers and their split; the targets, written apart


def readings_inputs(gnn_difference: float, hetero_minus_gcn: float, critiques_gain: tuple[float, float]):
    models = ["rgcn", "rgcn+scores", "han", "han+scores", "hgt", "hgt+scores"]
    tests = pd.DataFrame([{"model": model, "subset": subset, "auc_minus_scores_rating_lr": gnn_difference,
                           "auc_minus_scores_rating_lr_ci_low": gnn_difference - 0.004, "auc_minus_scores_rating_lr_ci_high": gnn_difference + 0.004}
                          for subset in ("all", "borderline") for model in models])
    pairs = {("hgt", "gcn"): hetero_minus_gcn, ("han", "gcn"): hetero_minus_gcn, ("rgcn", "gcn"): -0.01,
             ("scores_critiques_lr", "scores_all_lr"): critiques_gain[0], ("scores_critiques_gbt", "scores_all_gbt"): critiques_gain[1]}
    paired = pd.DataFrame([{"model": model, "control": control, "subset": subset, "difference": value, "ci_low": value - 0.004,
                            "ci_high": value + 0.004} for subset in ("all", "borderline") for (model, control), value in pairs.items()])
    return tests, paired, models


def test_the_three_readings_follow_the_confidence_intervals():
    module = script("07d_holdout_results.py")
    holds = module.readings(*readings_inputs(-0.015, 0.025, (-0.001, 0.001))).set_index(["reading", "subset"])["holds"]
    assert holds.all() and len(holds) == 6
    table = module.readings(*readings_inputs(0.010, 0.002, (0.001, 0.010))).set_index(["reading", "subset"])
    assert not table["holds"].any()  # a GNN above the reference, HAN and HGT not above the GCN, a gain from the critiques
    assert "6 significantly above" in table.loc[("a", "all"), "detail"]
    # a GNN that is neither above nor below the reference: the first reading still holds
    assert module.readings(*readings_inputs(0.002, 0.025, (0.0, 0.0))).set_index(["reading", "subset"]).loc[("a", "all"), "holds"]


def test_a_changed_node_or_edge_of_the_study_is_found():
    module = script("05c_extend_graph.py")
    graph, _, _ = synthetic_graph()
    graph["article"].year = torch.full((graph["article"].num_nodes,), 2024)
    graph["review"].year = torch.full((graph["review"].num_nodes,), 2024)
    assert module.same_prefix(graph, graph) == []
    changed = graph.clone()
    changed["review"].x[0, 0] += 1
    edge_type = graph.edge_types[0]
    changed[edge_type].edge_index = changed[edge_type].edge_index.flip(1)
    problems = module.same_prefix(changed, graph)
    assert "features of 'review'" in problems and f"edges {edge_type}" in problems and len(problems) == 2
