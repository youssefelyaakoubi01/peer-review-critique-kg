"""Models of phases 6 and 7, frozen, on the holdout year (ICLR 2026).

    uv run python scripts/05c_extend_graph.py        # graph of setting A with the holdout year
    uv run python scripts/07c_holdout.py             # predictions
    uv run python scripts/07d_holdout_results.py     # tables, confidence intervals, tests

Nothing is chosen or tuned on the holdout year.
  - Heterogeneous GNNs (setting A, plain and with score statistics, five seeds): the
    weights saved in phase 7 are read; the articles of the holdout year are predicted on
    the graph that holds the three years, as the test articles were on the graph of the
    study.
  - Baselines: their weights were not saved. They are fitted again on the training year
    with the configuration kept in phase 6, without any search.
Checks made before a prediction of the holdout year is written (the script stops if one
fails):
  - the features of the training and test years are scaled exactly as in the study;
  - each GNN gives back, on the graph of the study, the probabilities stored for the
    test year;
  - each baseline without random number gives back the probabilities stored for the
    test year. The MLPs and the GCN are trained again: their gap is recorded, not required.

Outputs:
    results/predictions/holdout_<years>.parquet            probability per article of the holdout year, model and seed
    results/predictions/holdout_<years>_test_year.parquet  test articles predicted again: graph models (on the extended
                                                           graph) and baselines trained again
    results/tables/holdout_<years>_checks.csv              gap with the stored predictions, per model and seed
"""

import argparse
import gc
import json
import sys
import time

import numpy as np
import pandas as pd
import torch

from src.eval import borderline
from src.models import baselines, features, hetero, train
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

GIB = 2**30
HOLDOUT = "holdout"
DETERMINISTIC_KINDS = {"majority", "logistic", "gbt"}  # no random number: fitted again, they give the same model


def load(directory, setting):
    graph = torch.load(directory / f"graph_{setting}.pt", weights_only=False)
    layout = json.loads((directory / "graph_features.json").read_text(encoding="utf-8"))[setting]
    targets = pd.read_parquet(directory / "targets.parquet")
    if list(targets["article_index"]) != list(range(graph["article"].num_nodes)):
        raise ValueError("targets are not aligned on the article nodes")
    return graph, layout, targets


def scaled_inputs(graph, layout, split) -> hetero.Inputs:
    """Whole graph, features scaled with the training nodes (on CPU)."""
    x = features.standardise(graph, layout, features.training_nodes(graph, torch.from_numpy(split == baselines.TRAIN)))
    return x, {edge_type: graph[edge_type].edge_index for edge_type in graph.edge_types}


def with_columns(inputs: hetero.Inputs, extra: np.ndarray) -> hetero.Inputs:
    x = dict(inputs[0])
    x["article"] = torch.cat([x["article"], torch.from_numpy(extra).float().to(x["article"].device)], dim=1)
    return x, inputs[1]


def to_device(inputs: hetero.Inputs, device: str) -> hetero.Inputs:
    return tuple({key: value.to(device) for key, value in part.items()} for part in inputs)


def predict(model, inputs: hetero.Inputs, device: str, log) -> np.ndarray:
    """Probabilities on `device`; on the CPU if the GPU runs out of memory."""
    try:
        return train.predict(model.to(device), inputs)
    except torch.OutOfMemoryError:
        log.warning("out of memory on the GPU: this prediction is computed on the CPU")
        torch.cuda.empty_cache()
        return train.predict(model.to("cpu"), to_device(inputs, "cpu"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--suffix", default="", help="added to the names of the outputs: a second run that does not replace the first")
    args = parser.parse_args()
    cfg = load_config()
    settings, gnn = cfg["holdout"], cfg["gnn"]
    log = setup_run_logging("07c_holdout", cfg["paths"]["logs"])
    tables_dir, processed, predictions_dir = cfg["paths"]["tables"], cfg["paths"]["processed"], cfg["paths"]["predictions"]
    setting, suffix = settings["setting"], gnn["score_variant"]["suffix"]
    tag = "holdout_" + "_".join(map(str, cfg["splits"]["holdout"])) + args.suffix
    started = time.time()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        free, total = torch.cuda.mem_get_info()
        log.info("GPU memory: %.1f GiB free of %.1f", free / GIB, total / GIB)
        if free < settings["gpu"]["min_free_gb"] * GIB:
            log.error("stopped: %.1f GiB free on the GPU, %s needed (another job is using it)", free / GIB, settings["gpu"]["min_free_gb"])
            return 3
        torch.cuda.set_per_process_memory_fraction((free - settings["gpu"]["margin_gb"] * GIB) / total)

    # ---- the graph of the study and the graph extended with the holdout year
    study_graph, layout, study_targets = load(processed, setting)
    graph, extended_layout, targets = load(processed / cfg["kg"]["holdout"]["dir"], setting)
    n_study = len(study_targets)
    if extended_layout != layout or not targets.iloc[:n_study].equals(study_targets):
        raise SystemExit("the extended graph does not follow the graph of the study")
    split = targets["split"].to_numpy(dtype=object)
    labels = targets["label"].to_numpy(dtype=float, na_value=np.nan)
    if set(split[n_study:]) != {HOLDOUT} or HOLDOUT in set(split[:n_study]):
        raise SystemExit("the holdout articles are not exactly the articles added to the graph")

    study = baselines.Data(features.article_table(study_graph, layout), labels[:n_study], split[:n_study], device)
    data = baselines.Data(features.article_table(graph, layout), labels, split, device)
    train_rows, test_rows, holdout_rows = data.rows(baselines.TRAIN), data.rows(baselines.TEST), data.rows(HOLDOUT)
    if not np.array_equal(train_rows, study.rows(baselines.TRAIN)) or not np.array_equal(test_rows, study.rows(baselines.TEST)):
        raise SystemExit("training or test rows differ between the two graphs")
    _, zone = borderline.training_zone(data.table.mean_rating[train_rows], data.labels[train_rows], cfg["baselines"]["borderline"])
    if zone != borderline.training_zone(study.table.mean_rating[train_rows], study.labels[train_rows], cfg["baselines"]["borderline"])[1]:
        raise SystemExit("the borderline zone changed")
    masks = borderline.subsets(data.table.mean_rating, data.table.text_available, zone)
    forum_ids = targets["forum_id"].to_numpy()
    log.info("papers with a decision: training %d, test %d, holdout %d (of which %d borderline, zone [%.2f, %.2f))",
             len(train_rows), len(test_rows), len(holdout_rows), int(masks["borderline"][holdout_rows].sum()), *zone)

    def rows_table(model: str, seed: int, rows: np.ndarray, probabilities: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame({"model": model, "setting": setting, "seed": seed, "forum_id": forum_ids[rows], "split": split[rows],
                             "label": labels[rows].astype(int), "probability": probabilities[rows],
                             "borderline": masks["borderline"][rows], "text_available": masks["with_text"][rows]})

    checks, predictions, test_year = [], [], []

    def check(model: str, kind: str, seed: int, stored: pd.Series, probabilities: np.ndarray, required: bool, what: str) -> None:
        """Gap between the probabilities stored for the test year and those computed here."""
        gap = float(np.abs(stored.loc[forum_ids[test_rows]].to_numpy() - probabilities[test_rows]).max())
        passed = gap <= settings["max_gap"]
        checks.append({"model": model, "kind": kind, "seed": seed, "check": what, "required": required,
                       "max_gap_on_test_year": gap, "passed": passed})
        if required and not passed:
            pd.DataFrame(checks).to_csv(tables_dir / f"{tag}_checks.csv", index=False)
            raise SystemExit(f"{model}, seed {seed}: the stored probabilities of the test year are not reproduced (gap {gap:.2e}); "
                             "no prediction of the holdout year was written")

    # ---- heterogeneous GNNs: saved weights, first on the graph of the study (check), then on the extended graph
    study_inputs, inputs = scaled_inputs(study_graph, layout, split[:n_study]), scaled_inputs(graph, layout, split)
    for node_type, x in study_inputs[0].items():
        if not torch.equal(inputs[0][node_type][:len(x)], x):
            raise SystemExit(f"the features of '{node_type}' are not scaled as in the study")
    score_blocks = gnn["score_variant"]["features"]
    extras = {"study": study.table.design(score_blocks, train_rows), "extended": data.table.design(score_blocks, train_rows)}
    if not np.array_equal(extras["extended"][:n_study], extras["study"]):
        raise SystemExit("the score statistics of the articles are not scaled as in the study")
    names = [kind + end for kind in gnn["models"] for end in ("", suffix)]

    def saved_model(name: str, seed: int) -> hetero.HeteroGNN:
        saved = torch.load(processed / "models" / f"label_{setting}_{name}_seed{seed}.pt", weights_only=False, map_location="cpu")
        model = hetero.HeteroGNN(saved["kind"], saved["metadata"], saved["in_dims"], saved["params"]["hidden"], saved["params"]["layers"],
                                 saved["params"]["dropout"], saved["training"]["heads"])
        model.load_state_dict(saved["state_dict"])
        return model

    for where, (plain, extra) in (("study", (study_inputs, extras["study"])), ("extended", (inputs, extras["extended"]))):
        on_device = {False: to_device(plain, device)}
        on_device[True] = with_columns(on_device[False], extra)
        for name in names:
            for seed in cfg["seeds"]:
                probabilities = predict(saved_model(name, seed), on_device[name.endswith(suffix)], device, log)
                if where == "study":
                    stored = pd.read_parquet(predictions_dir / "gnn" / f"label_{setting}_{name}_seed{seed}.parquet")
                    check(name, "gnn", seed, stored.set_index("forum_id")["probability"], probabilities, True,
                          "saved weights on the graph of the study")
                else:
                    predictions.append(rows_table(name, seed, holdout_rows, probabilities))
                    test_year.append(rows_table(name, seed, test_rows, probabilities))
            log.info("%s on the %s graph: done (%.0f s since the start)", name, where, time.time() - started)
        del on_device
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
    del study_inputs, inputs, study_graph
    log.info("GNNs: every stored probability of the test year is reproduced within %s", settings["max_gap"])

    # ---- baselines: fitted again on the training year with the configurations kept in phase 6
    stored = pd.read_parquet(predictions_dir / "baselines.parquet")
    final = pd.read_csv(tables_dir / "baselines_selection.csv").query("stage == 'final'")
    for name, spec in cfg["baselines"]["models"].items():
        chosen = final.loc[final["model"] == name, "params"].unique()
        if len(chosen) != 1:
            raise SystemExit(f"expected one configuration of {name}, found {len(chosen)}")
        if spec["kind"] == "gcn" and data.graph is None:
            # trained on the GPU on the graph of the training year; the extended graph does not fit in the
            # memory of the GPU for a prediction (one message per edge), so it is predicted on the CPU
            data.graph = baselines.graph_views(graph, layout, split, device, full_device="cpu")
        for seed in cfg["seeds"]:
            probabilities, _ = baselines.run(spec, json.loads(chosen[0]), data, seed, cfg["baselines"]["training"])
            of_seed = stored[(stored["model"] == name) & (stored["seed"] == seed)].set_index("forum_id")["probability"]
            deterministic = spec["kind"] in DETERMINISTIC_KINDS
            check(name, spec["kind"], seed, of_seed, probabilities, deterministic,
                  "fitted again, no random number" if deterministic else
                  "trained again, test articles predicted on the extended graph" if spec["kind"] == "gcn" else "trained again")
            predictions.append(rows_table(name, seed, holdout_rows, probabilities))
            if not deterministic:  # trained again: its predictions of the test year are kept, to compare with the stored ones
                test_year.append(rows_table(name, seed, test_rows, probabilities))
        log.info("%s: done (%.0f s since the start)", name, time.time() - started)

    # ---- outputs
    checks = pd.DataFrame(checks)
    checks.to_csv(tables_dir / f"{tag}_checks.csv", index=False)
    pd.concat(predictions, ignore_index=True).to_parquet(predictions_dir / f"{tag}.parquet", index=False)
    pd.concat(test_year, ignore_index=True).to_parquet(predictions_dir / f"{tag}_test_year.parquet", index=False)
    summary = checks.groupby(["kind", "check", "required"])["max_gap_on_test_year"].agg(["size", "max"]).reset_index()
    log.info("checks against the stored predictions of the test year\n%s", summary.to_string(index=False))
    log.info("%d models x %d seeds predicted on %d holdout papers in %.1f min", checks["model"].nunique(), len(cfg["seeds"]),
             len(holdout_rows), (time.time() - started) / 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
