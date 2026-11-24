"""Phase 8: ablations of the best plain model (config `ablations`).

    uv run python scripts/08_ablations.py
    uv run python scripts/08b_ablation_results.py      # tables, tests, figure

Each variant removes something from the graph (src/models/ablation.py); the model is
trained again with the hyper-parameters chosen in phase 7 and the five seeds. Nothing
is searched or tuned here.

The script can be interrupted: every finished training is recorded in
results/tables/ablations_selection.csv and is not run again.

The GPU is shared: the script stops at once if less than `ablations.gpu.min_free_gb` is
free, and caps its own memory at the free memory minus `margin_gb`, so that a wrong
estimate makes this script fail rather than the job of another user.

Outputs:
    results/tables/ablations_selection.csv   every training run (validation AUC, epochs, time, peak GPU memory)
    results/predictions/ablations.parquet    probability per article, variant and seed

Other groups of variants (--group), each with its own files (`ablations_<group>` in the names above):
    encoder_variants   `ablations.encoder_variants`: the model without the pretrained text encoders
    followup           `followup.variants`: written after the result of the previous group was read; each trained
                       model is also applied, frozen, to the holdout year on the extended graph with the same
                       elements removed (results/predictions/ablations_followup_holdout.parquet)
"""

import argparse
import gc
import json
import sys
import time

import numpy as np
import pandas as pd
import torch

from src.eval import borderline, metrics
from src.models import baselines, features, hetero, staged
from src.models.ablation import ablated_graph
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

GIB = 2**30


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--group", default="variants", choices=["variants", "encoder_variants", "followup"],
                        help="group of variants of the config; another group than `variants` has its own output files")
    args = parser.parse_args()
    tag = "ablations" if args.group == "variants" else "ablations_" + args.group.removesuffix("_variants")
    cfg = load_config()
    on_holdout = args.group == "followup"  # the trained models are also applied to the holdout year
    settings = cfg["followup"] if on_holdout else cfg["ablations"]
    variants = settings["variants"] if on_holdout else settings[args.group]
    log = setup_run_logging("08_ablations", cfg["paths"]["logs"])
    tables_dir, processed = cfg["paths"]["tables"], cfg["paths"]["processed"]
    runs_dir = cfg["paths"]["predictions"] / tag
    runs_dir.mkdir(parents=True, exist_ok=True)
    setting, kind = settings["setting"], settings["model"]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        free, total = torch.cuda.mem_get_info()
        log.info("GPU memory: %.1f GiB free of %.1f", free / GIB, total / GIB)
        if free < settings["gpu"]["min_free_gb"] * GIB:
            log.error("stopped: %.1f GiB free on the GPU, %s needed (another job is using it)", free / GIB, settings["gpu"]["min_free_gb"])
            return 3
        torch.cuda.set_per_process_memory_fraction((free - settings["gpu"]["margin_gb"] * GIB) / total)

    # hyper-parameters of the model chosen in phase 7
    chosen = pd.read_csv(tables_dir / "gnn_selection.csv").query(
        "labels == 'label' and setting == @setting and model == @kind and stage == 'final'")["params"].unique()
    if len(chosen) != 1:
        raise SystemExit(f"expected one configuration of {kind} in setting {setting}, found {len(chosen)}")
    params = json.loads(chosen[0])
    log.info("%s, setting %s, hyper-parameters of phase 7: %s", kind, setting, params)

    graph = torch.load(processed / f"graph_{setting}.pt", weights_only=False)
    layout = json.loads((processed / "graph_features.json").read_text(encoding="utf-8"))[setting]
    targets = pd.read_parquet(processed / "targets.parquet")
    if list(targets["article_index"]) != list(range(graph["article"].num_nodes)):
        raise ValueError("targets are not aligned on the article nodes")
    split = targets["split"].to_numpy(dtype=object)
    # labels, borderline zone and subsets come from the whole graph, whatever the variant
    data = baselines.Data(features.article_table(graph, layout), targets["label"].to_numpy(dtype=float, na_value=np.nan), split, device)
    train_rows = data.rows(baselines.TRAIN)
    _, zone = borderline.training_zone(data.table.mean_rating[train_rows], data.labels[train_rows], cfg["baselines"]["borderline"])
    masks = borderline.subsets(data.table.mean_rating, data.table.text_available, zone)
    scored = np.concatenate([data.rows(baselines.VAL), data.rows(baselines.TEST)])

    # ---- holdout year: the extended graph, its targets apart, the same borderline zone
    extended = None
    if on_holdout:
        directory = processed / cfg["kg"]["holdout"]["dir"]
        extended = {"graph": torch.load(directory / f"graph_{setting}.pt", weights_only=False),
                    "targets": pd.read_parquet(directory / "targets.parquet")}
        if json.loads((directory / "graph_features.json").read_text(encoding="utf-8"))[setting] != layout or not extended["targets"].iloc[
                :len(targets)].equals(targets):
            raise SystemExit("the extended graph does not follow the graph of the study")
        extended["split"] = extended["targets"]["split"].to_numpy(dtype=object)
        extended["labels"] = extended["targets"]["label"].to_numpy(dtype=float, na_value=np.nan)
        extended["rows"] = np.flatnonzero((extended["split"] == "holdout") & ~np.isnan(extended["labels"]))
        table = features.article_table(extended["graph"], layout)
        extended["masks"] = borderline.subsets(table.mean_rating, table.text_available, zone)
        log.info("holdout year: %d papers with a decision, %d of them borderline", len(extended["rows"]),
                 int(extended["masks"]["borderline"][extended["rows"]].sum()))
    first_run = cfg["paths"]["predictions"] / "ablations_encoder"  # first predictions of a variant trained again here

    selection_file = tables_dir / f"{tag}_selection.csv"
    records = pd.read_csv(selection_file).to_dict("records") if selection_file.exists() else []
    done = {(r["variant"], r["seed"]) for r in records if r["status"] == "ok"}

    for variant, spec in variants.items():
        pending = [seed for seed in cfg["seeds"] if (variant, seed) not in done or not (runs_dir / f"{variant}_seed{seed}.parquet").exists()
                   or (on_holdout and not (runs_dir / f"{variant}_seed{seed}_holdout.parquet").exists())]
        if not pending:
            continue
        ablated, ablated_layout = ablated_graph(graph, layout, spec)
        views = hetero.hetero_views(ablated, ablated_layout, split, device)
        holdout_stage = None
        if on_holdout:  # the extended graph without the same elements, scaled with the same training nodes
            wider, wider_layout = ablated_graph(extended["graph"], layout, spec)
            x = features.standardise(wider, wider_layout, features.training_nodes(wider, torch.from_numpy(extended["split"] == baselines.TRAIN)))
            for node_type, values in views.full_inputs[0].items():
                if not torch.equal(x[node_type][:len(values)], values):
                    raise SystemExit(f"{variant}: the features of '{node_type}' are not scaled as on the graph of the study")
            holdout_stage = staged.Stage((x, {edge_type: wider[edge_type].edge_index for edge_type in wider.edge_types}),
                                         np.arange(wider["article"].num_nodes))
            del wider
        log.info("%s: node types %s, %d relations, feature sizes %s", variant, ablated.node_types, len(ablated.edge_types), views.in_dims)
        for seed in pending:
            records = [r for r in records if (r["variant"], r["seed"]) != (variant, seed)]  # a failed run is tried again
            if device == "cuda":
                torch.cuda.reset_peak_memory_stats()
            start = time.time()
            row = {"variant": variant, "setting": setting, "model": kind, "params": json.dumps(params), "seed": seed}
            try:
                probabilities, fitted, model = hetero.run(kind, params, data, views, seed, cfg["gnn"]["training"])
            except torch.OutOfMemoryError:
                log.warning("out of memory: %s, seed %d", variant, seed)
                records.append({**row, "val_auc": np.nan, "best_epoch": None, "epochs": None,
                                "seconds": round(time.time() - start, 1), "peak_gpu_gb": None, "status": "out_of_memory"})
            else:
                val = data.rows(baselines.VAL)
                pd.DataFrame({"model": variant, "setting": setting, "seed": seed, "forum_id": targets["forum_id"].to_numpy()[scored],
                              "split": split[scored], "label": data.labels[scored].astype(int), "probability": probabilities[scored],
                              "borderline": masks["borderline"][scored], "text_available": masks["with_text"][scored],
                              }).to_parquet(runs_dir / f"{variant}_seed{seed}.parquet", index=False)
                if on_holdout:
                    held, rows = staged.predict(model, holdout_stage, device, log), extended["rows"]
                    pd.DataFrame({"model": variant, "setting": setting, "seed": seed, "forum_id": extended["targets"]["forum_id"].to_numpy()[rows],
                                  "split": extended["split"][rows], "label": extended["labels"][rows].astype(int), "probability": held[rows],
                                  "borderline": extended["masks"]["borderline"][rows], "text_available": extended["masks"]["with_text"][rows],
                                  }).to_parquet(runs_dir / f"{variant}_seed{seed}_holdout.parquet", index=False)
                    earlier = first_run / f"{variant}_seed{seed}.parquet"
                    if earlier.exists():  # trained a second time: largest gap with the first predictions of the validation and test papers
                        stored = pd.read_parquet(earlier).set_index("forum_id")["probability"]
                        row["max_gap_with_first_run"] = float(np.abs(stored.loc[targets["forum_id"].to_numpy()[scored]].to_numpy() - probabilities[scored]).max())
                records.append({**row, "val_auc": metrics.classification_metrics(data.labels[val], probabilities[val])["auc"],
                                "best_epoch": fitted.best_epoch, "epochs": fitted.epochs, "seconds": round(time.time() - start, 1),
                                "peak_gpu_gb": round(torch.cuda.max_memory_allocated() / GIB, 2) if device == "cuda" else None,
                                "status": "ok"})
                log.info("%s, seed %d: validation AUC %.4f, %d epochs, %.0f s, peak GPU memory %s GiB", variant, seed,
                         records[-1]["val_auc"], fitted.epochs, records[-1]["seconds"], records[-1]["peak_gpu_gb"])
                del model, probabilities
            gc.collect()
            if device == "cuda":
                torch.cuda.empty_cache()
            pd.DataFrame(records).to_csv(selection_file, index=False)
        del views, ablated
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

    table = pd.DataFrame(records)
    failed = table[table["status"] != "ok"]
    files = [runs_dir / f"{variant}_seed{seed}.parquet" for variant in variants for seed in cfg["seeds"]]
    held_files = [runs_dir / f"{variant}_seed{seed}_holdout.parquet" for variant in variants for seed in cfg["seeds"]] if on_holdout else []
    missing = [f.name for f in [*files, *held_files] if not f.exists()]
    if missing:
        log.error("%d runs are missing (%d failed): %s", len(missing), len(failed), missing)
        return 1
    pd.concat([pd.read_parquet(f) for f in files], ignore_index=True).to_parquet(cfg["paths"]["predictions"] / f"{tag}.parquet", index=False)
    if held_files:
        pd.concat([pd.read_parquet(f) for f in held_files], ignore_index=True).to_parquet(
            cfg["paths"]["predictions"] / f"{tag}_holdout.parquet", index=False)
    log.info("%d runs, %.1f min of training, peak GPU memory %.2f GiB", len(table), table["seconds"].sum() / 60,
             table["peak_gpu_gb"].max() if device == "cuda" else float("nan"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
