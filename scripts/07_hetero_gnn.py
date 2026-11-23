"""Phase 7: heterogeneous GNNs (R-GCN, HAN, HGT) in settings A and B.

    uv run python scripts/07_hetero_gnn.py
    uv run python scripts/07b_main_results.py        # tables, confidence intervals, tests

For each setting and architecture: hyper-parameters chosen on the validation AUC with
one seed (grid of the config), then five seeds for the plain model and for its variant
with the score statistics on the article node. Then, as a robustness check, the best
plain model and one baseline with the withdrawn papers counted as rejections.

The script can be interrupted: every finished training is recorded in
results/tables/gnn_selection.csv and is not run again.

Outputs:
    results/tables/gnn_selection.csv                     every training run
    results/predictions/gnn.parquet                      probability per article, model, setting and seed
    results/predictions/gnn_withdrawn_as_reject.parquet  the same for the robustness check
    data/processed/models/                               weights of the final models
"""

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from src.eval import borderline, metrics
from src.models import baselines, features, hetero
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

KEY = ["labels", "setting", "model", "stage", "params", "seed"]
PRIMARY, AS_REJECT = "label", "label_withdrawn_as_reject"


def main() -> int:
    cfg = load_config()
    settings = cfg["gnn"]
    log = setup_run_logging("07_hetero_gnn", cfg["paths"]["logs"])
    tables_dir, processed = cfg["paths"]["tables"], cfg["paths"]["processed"]
    runs_dir, models_dir = cfg["paths"]["predictions"] / "gnn", processed / "models"
    runs_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    suffix = settings["score_variant"]["suffix"]

    targets = pd.read_parquet(processed / "targets.parquet")
    split = targets["split"].to_numpy(dtype=object)
    labels = {name: targets[name].to_numpy(dtype=float, na_value=np.nan) for name in (PRIMARY, AS_REJECT)}

    selection_file = tables_dir / "gnn_selection.csv"
    records = pd.read_csv(selection_file).to_dict("records") if selection_file.exists() else []
    planned = sum(len(baselines.grid({"grid": settings["grid"][s]})) + 2 * len(cfg["seeds"]) for s in settings["settings"]) \
        * len(settings["models"]) + len(cfg["seeds"])

    def projected_seconds(setting: str, kind: str) -> float:
        """Time already spent plus the remaining runs at the mean time of the runs of this architecture."""
        spent = [r["seconds"] for r in records]
        same = [r["seconds"] for r in records if r["setting"] == setting and r["model"].removesuffix(suffix) == kind]
        return sum(spent) + max(planned - len(records), 0) * float(np.mean(same or spent))

    def prediction_file(key: dict) -> Path:
        return runs_dir / f"{key['labels']}_{key['setting']}_{key['model']}_seed{key['seed']}.parquet"

    def run_once(key: dict, data: baselines.Data, views: hetero.HeteroViews, masks: dict, kind: str, params: dict) -> float:
        """Validation AUC of one training; trains only if it is not recorded yet."""
        key = {**key, "params": json.dumps(params)}
        for record in records:
            if all(record[k] == key[k] for k in KEY) and (key["stage"] == "selection" or prediction_file(key).exists()):
                return record["val_auc"]
        start = time.time()
        try:
            probabilities, fitted, model = hetero.run(kind, params, data, views, key["seed"], settings["training"])
        except torch.OutOfMemoryError:
            log.warning("out of memory: %s", key)
            records.append({**key, "val_auc": np.nan, "best_epoch": None, "epochs": None,
                            "seconds": round(time.time() - start, 1), "status": "out_of_memory"})
        else:
            val = data.rows(baselines.VAL)
            val_auc = metrics.classification_metrics(data.labels[val], probabilities[val])["auc"]
            if key["stage"] == "final":
                scored = np.concatenate([val, data.rows(baselines.TEST)])
                pd.DataFrame({**{k: key[k] for k in ("model", "setting", "labels", "seed")},
                              "forum_id": targets["forum_id"].to_numpy()[scored], "split": split[scored],
                              "label": data.labels[scored].astype(int), "probability": probabilities[scored],
                              "borderline": masks["borderline"][scored], "text_available": masks["with_text"][scored],
                              }).to_parquet(prediction_file(key), index=False)
                torch.save({"state_dict": model.state_dict(), "kind": kind, "params": params, "in_dims": views.in_dims,
                            "metadata": views.metadata, "training": settings["training"]},
                           models_dir / (prediction_file(key).stem + ".pt"))
            records.append({**key, "val_auc": val_auc, "best_epoch": fitted.best_epoch, "epochs": fitted.epochs,
                            "seconds": round(time.time() - start, 1), "status": "ok"})
            del model, probabilities
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
        pd.DataFrame(records).to_csv(selection_file, index=False)
        projected = projected_seconds(key["setting"], kind)
        if projected > settings["max_hours"] * 3600:
            raise SystemExit(f"stopped: projected run time {projected / 3600:.1f} h exceeds {settings['max_hours']} h")
        return records[-1]["val_auc"]

    for setting in settings["settings"]:
        graph = torch.load(processed / f"graph_{setting}.pt", weights_only=False)
        layout = json.loads((processed / "graph_features.json").read_text(encoding="utf-8"))[setting]
        if list(targets["article_index"]) != list(range(graph["article"].num_nodes)):
            raise ValueError("targets are not aligned on the article nodes")
        data = baselines.Data(features.article_table(graph, layout), labels[PRIMARY], split, device)
        train_rows = data.rows(baselines.TRAIN)
        _, zone = borderline.training_zone(data.table.mean_rating[train_rows], data.labels[train_rows], cfg["baselines"]["borderline"])
        masks = borderline.subsets(data.table.mean_rating, data.table.text_available, zone)
        views = hetero.hetero_views(graph, layout, split, device)
        with_scores = hetero.with_article_columns(views, data.table.design(settings["score_variant"]["features"], train_rows), device)
        del graph
        log.info("setting %s: training graph of %d nodes, whole graph of %d nodes", setting,
                 sum(len(x) for x in views.train_inputs[0].values()), sum(len(x) for x in views.full_inputs[0].values()))

        chosen, validation = {}, {}
        for kind in settings["models"]:
            key = {"labels": PRIMARY, "setting": setting, "model": kind}
            candidates = baselines.grid({"grid": settings["grid"][setting]})
            scores = [run_once({**key, "stage": "selection", "seed": settings["selection_seed"]}, data, views, masks, kind, params)
                      for params in candidates]
            if np.isnan(scores).all():
                raise SystemExit(f"every configuration of {kind} failed in setting {setting}")
            chosen[kind] = candidates[int(np.nanargmax(scores))]
            log.info("%s, setting %s: chosen %s (validation AUC %.4f)", kind, setting, chosen[kind], np.nanmax(scores))
            for name, variant in ((kind, views), (kind + suffix, with_scores)):
                finals = [run_once({**key, "model": name, "stage": "final", "seed": seed}, data, variant, masks, kind, chosen[kind])
                          for seed in cfg["seeds"]]
                validation[name] = float(np.nanmean(finals))
                log.info("%s, setting %s: validation AUC %.4f over %d seeds; %.0f min of training so far, projected total %.1f h",
                         name, setting, validation[name], len(finals), sum(r["seconds"] for r in records) / 60,
                         projected_seconds(setting, kind) / 3600)

        # ---- robustness: withdrawn papers counted as rejections
        if setting == settings["robustness"]["setting"]:
            best = max(settings["models"], key=lambda kind: validation[kind])
            other = baselines.Data(data.table, labels[AS_REJECT], split, device)
            log.info("robustness: %s and %s with the withdrawn papers counted as rejections", best, settings["robustness"]["baseline"])
            for seed in cfg["seeds"]:
                run_once({"labels": AS_REJECT, "setting": setting, "model": best, "stage": "final", "seed": seed},
                         other, views, masks, best, chosen[best])
            name = settings["robustness"]["baseline"]
            final = pd.read_csv(tables_dir / "baselines_selection.csv").query("model == @name and stage == 'final'")
            scored = np.concatenate([other.rows(baselines.VAL), other.rows(baselines.TEST)])
            for seed in cfg["seeds"]:
                probabilities, _ = baselines.run(cfg["baselines"]["models"][name], json.loads(final["params"].iloc[0]), other, seed, {})
                pd.DataFrame({"model": name, "setting": setting, "labels": AS_REJECT, "seed": seed,
                              "forum_id": targets["forum_id"].to_numpy()[scored], "split": split[scored],
                              "label": other.labels[scored].astype(int), "probability": probabilities[scored],
                              "borderline": masks["borderline"][scored], "text_available": masks["with_text"][scored],
                              }).to_parquet(runs_dir / f"{AS_REJECT}_{setting}_{name}_seed{seed}.parquet", index=False)
        del views, with_scores, data
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

    for name, out in ((PRIMARY, "gnn.parquet"), (AS_REJECT, "gnn_withdrawn_as_reject.parquet")):
        files = sorted(runs_dir.glob(f"{name}_[AB]_*.parquet"))
        pd.concat([pd.read_parquet(f) for f in files], ignore_index=True).to_parquet(cfg["paths"]["predictions"] / out, index=False)
        log.info("%s: %d prediction files", out, len(files))
    table = pd.DataFrame(records)
    log.info("%d runs, %.1f h of training, %d failed", len(table), table["seconds"].sum() / 3600, int((table["status"] != "ok").sum()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
