"""Phase 6: baselines on the temporal split (train 2024, validation carved out of 2024, test 2025).

    uv run python scripts/06_baselines.py

Reads the graph of setting A and the targets, nothing else. For each model of
`baselines.models` in the config: hyper-parameters chosen on the validation AUC with
one seed, then five seeds with the chosen configuration.

Outputs in results/tables/:
    borderline_definition.csv     acceptance rate of the training papers per bin of mean initial rating
    baselines_selection.csv       every run: configuration, seed, validation AUC, epochs, time
    baselines_by_seed.csv         metrics per model, seed, split and subset of papers
    baselines.csv                 mean and standard deviation over the seeds
    baselines.tex                 LaTeX table of the test split
and results/predictions/baselines.parquet (probability per article, model and seed).
"""

import json
import sys
import time

import numpy as np
import pandas as pd
import torch

from src.eval import borderline, metrics
from src.models import baselines, features
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

DETERMINISTIC_KINDS = {"majority", "logistic", "gbt"}  # no random number: the five seeds give the same result
SUBSET_LABELS = {"all": "All papers", "borderline": "Borderline papers"}


def evaluate(probabilities: np.ndarray, data: baselines.Data, masks: dict[str, np.ndarray]) -> list[dict]:
    rows = []
    for split in (baselines.VAL, baselines.TEST):
        for subset, mask in masks.items():
            chosen = data.rows(split)
            chosen = chosen[mask[chosen]]
            rows.append({"split": split, "subset": subset, "n_papers": len(chosen), "n_accepted": int(data.labels[chosen].sum()),
                         **metrics.classification_metrics(data.labels[chosen], probabilities[chosen])})
    return rows


def main() -> int:
    cfg = load_config()
    settings = cfg["baselines"]
    log = setup_run_logging("06_baselines", cfg["paths"]["logs"])
    tables_dir, processed = cfg["paths"]["tables"], cfg["paths"]["processed"]
    tables_dir.mkdir(parents=True, exist_ok=True)
    cfg["paths"]["predictions"].mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    started = time.time()

    # ---- inputs: the graph of setting A; targets apart
    setting = settings["setting"]
    graph = torch.load(processed / f"graph_{setting}.pt", weights_only=False)
    layout = json.loads((processed / "graph_features.json").read_text(encoding="utf-8"))[setting]
    targets = pd.read_parquet(processed / "targets.parquet")
    if list(targets["article_index"]) != list(range(graph["article"].num_nodes)):
        raise ValueError("targets are not aligned on the article nodes")
    data = baselines.Data(table=features.article_table(graph, layout),
                          labels=targets["label"].to_numpy(dtype=float, na_value=np.nan),
                          split=targets["split"].to_numpy(dtype=object), device=device)
    log.info("papers with a decision: %s", {s: len(data.rows(s)) for s in (baselines.TRAIN, baselines.VAL, baselines.TEST)})

    # ---- borderline zone, from the training papers only
    train_rows = data.rows(baselines.TRAIN)
    rates, zone = borderline.training_zone(data.table.mean_rating[train_rows], data.labels[train_rows], settings["borderline"])
    rates.round(4).to_csv(tables_dir / "borderline_definition.csv", index=False)
    masks = borderline.subsets(data.table.mean_rating, data.table.text_available, zone)
    log.info("borderline zone: mean initial rating in [%.2f, %.2f)", *zone)

    if any(spec["kind"] == "gcn" for spec in settings["models"].values()):
        start = time.time()
        data.graph = baselines.graph_views(graph, layout, data.split, device)
        log.info("flattened graph: %d nodes, %d edges, %d columns (%.0f s)", data.graph.full_inputs[0].shape[0],
                 data.graph.full_inputs[1].shape[1], data.graph.full_inputs[0].shape[1], time.time() - start)

    # ---- models
    runs, by_seed, predictions = [], [], []
    scored = np.concatenate([data.rows(baselines.VAL), data.rows(baselines.TEST)])
    for name, spec in settings["models"].items():
        candidates = baselines.grid(spec)

        def one_run(params: dict, seed: int, stage: str) -> tuple[np.ndarray, float]:
            start = time.time()
            probabilities, fitted = baselines.run(spec, params, data, seed, settings["training"])
            val = data.rows(baselines.VAL)
            val_auc = metrics.classification_metrics(data.labels[val], probabilities[val])["auc"]
            runs.append({"model": name, "stage": stage, "params": json.dumps(params), "seed": seed, "val_auc": val_auc,
                         "best_epoch": fitted.best_epoch if fitted else None, "epochs": fitted.epochs if fitted else None,
                         "seconds": round(time.time() - start, 2)})
            return probabilities, val_auc

        chosen = candidates[0]
        if len(candidates) > 1:
            scores = []
            for index, params in enumerate(candidates):
                scores.append(one_run(params, settings["selection_seed"], "selection")[1])
                if index == 0:  # cost rule: project the run time of this model from its first run
                    projected = time.time() - started + runs[-1]["seconds"] * (len(candidates) - 1 + len(cfg["seeds"]))
                    if projected > settings["max_minutes"] * 60:
                        log.error("stopped: projected run time %.0f min exceeds %d min (model %s, first run %.0f s)",
                                  projected / 60, settings["max_minutes"], name, runs[-1]["seconds"])
                        return 2
            chosen = candidates[int(np.argmax(scores))]  # first of the best on a tie
        log.info("%s: %d configuration(s), chosen %s", name, len(candidates), chosen)

        for seed in cfg["seeds"]:
            probabilities, val_auc = one_run(chosen, seed, "final")
            for row in evaluate(probabilities, data, masks):
                by_seed.append({"model": name, "kind": spec["kind"], "params": json.dumps(chosen),
                                "deterministic": spec["kind"] in DETERMINISTIC_KINDS, "seed": seed, **row})
            predictions.append(pd.DataFrame({
                "model": name, "seed": seed, "forum_id": targets["forum_id"].to_numpy()[scored], "split": data.split[scored],
                "label": data.labels[scored].astype(int), "probability": probabilities[scored],
                "borderline": masks["borderline"][scored], "text_available": masks["with_text"][scored]}))
        log.info("%s: validation AUC of the last seed %.4f, %.0f s since the start", name, val_auc, time.time() - started)

    # ---- tables
    runs = pd.DataFrame(runs)
    runs["best_epoch"], runs["epochs"] = runs["best_epoch"].astype("Int64"), runs["epochs"].astype("Int64")
    runs.to_csv(tables_dir / "baselines_selection.csv", index=False)
    by_seed = pd.DataFrame(by_seed)
    by_seed.to_csv(tables_dir / "baselines_by_seed.csv", index=False)
    summary = metrics.summarise(by_seed, ["model", "split", "subset"])
    summary.to_csv(tables_dir / "baselines.csv", index=False)
    pd.concat(predictions, ignore_index=True).to_parquet(cfg["paths"]["predictions"] / "baselines.parquet", index=False)
    test = summary[(summary["split"] == baselines.TEST) & summary["subset"].isin(SUBSET_LABELS)]
    test = test.sort_values("subset", kind="stable", key=lambda s: s.map(list(SUBSET_LABELS).index))
    (tables_dir / "baselines.tex").write_text(metrics.latex_table(
        test, "model", {}, caption=f"Baselines on the test year ({', '.join(map(str, cfg['splits']['test']))}), "
        f"mean $\\pm$ standard deviation over {len(cfg['seeds'])} seeds. Borderline papers: mean initial rating in "
        f"$[{zone[0]:g}, {zone[1]:g})$.", label="tab:baselines", group="subset", group_labels=SUBSET_LABELS), encoding="utf-8")
    shown = ["model", "subset", "n_papers", *[f"{m}_{s}" for m in metrics.METRICS for s in ("mean", "std")]]
    log.info("test split\n%s", test[shown].round(4).to_string(index=False))
    log.info("done in %.1f min", (time.time() - started) / 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
