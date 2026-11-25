"""Protocol checks: three limitations of the article measured instead of stated.

    uv run python scripts/05f_inductive_graph.py                     # graph with the vocabulary of the training years
    uv run python scripts/07f_protocol_checks.py --stage vocabulary  # 1. vocabulary of concepts counted on the training years
    uv run python scripts/07f_protocol_checks.py --stage search      # 2. equal and wider hyper-parameter search
    uv run python scripts/07f_protocol_checks.py --stage rolling     # 3. validation on the following year, test on the year after
    uv run python scripts/07f_protocol_checks.py --stage depth       # follow-up of 2 on HAN: depth and weight decay
    uv run python scripts/07g_protocol_results.py                    # tables, intervals, tests

All three are post hoc: the test and holdout years had been read. Their design is the
section `protocol` of the config, written and committed before the first run. Setting A
only. A stage reads one graph and the targets, never an outcome as an input.

  vocabulary  The graph models with the configurations and training settings of phases
              6 and 7, on the graph whose vocabulary of concepts is counted on the
              training years. Nothing is searched.
  search      Every model searched again with the same budget in a wider space, on the
              graph of the study; the models kept are applied, frozen, to the holdout year.
  rolling     Trained on the training years, selected and stopped on the test year, tested
              on the holdout year, on the graph of stage `vocabulary`, with the search of
              stage `search`.

  depth       Follow-up of stage `search` (section `depth_followup` of the config, written
              after its results were read): HAN with the configuration kept by that
              stage, in which the depth and the weight decay each take the value kept
              and the value of phase 7. Nothing is searched; the configuration kept
              itself is not trained again.

The script can be interrupted: every finished training is recorded and is not run again.

Outputs (<stage> in the names):
    results/tables/protocol_<stage>_selection.csv   every training run
    results/tables/protocol_<stage>_chosen.csv      configuration kept for each model
    results/predictions/protocol_<stage>.parquet    probability per paper, model and seed
    data/processed/models/protocol/                 weights of the final graph models
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
from src.kg.build import article_subgraph
from src.models import baselines, features, hetero, search, staged
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

GIB = 2**30
TRAIN, VAL, TEST, HOLDOUT = "train", "val", "test", "holdout"
KEY = ["stage", "model", "phase", "params", "seed"]
DETERMINISTIC_KINDS = {"logistic", "gbt"}  # no random number: every seed gives the same model
DEPTH = "depth"  # the follow-up of stage `search` on HAN: its stage is in the section `depth_followup`


def stored_configuration(table: pd.DataFrame, what: str) -> dict:
    chosen = table["params"].unique()
    if len(chosen) != 1:
        raise SystemExit(f"expected one configuration of {what}, found {len(chosen)}")
    return json.loads(chosen[0])


def main() -> int:
    cfg = load_config()
    protocol = cfg["protocol"]
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    follow = cfg["depth_followup"]
    stage_specs = {**protocol["stages"], DEPTH: follow["stage"]}
    parser.add_argument("--stage", required=True, choices=list(stage_specs))
    args = parser.parse_args()
    stage, spec, setting = args.stage, stage_specs[args.stage], protocol["setting"]
    log = setup_run_logging(f"07f_protocol_{stage}", cfg["paths"]["logs"])
    tables_dir, processed, predictions_dir = cfg["paths"]["tables"], cfg["paths"]["processed"], cfg["paths"]["predictions"]
    runs_dir, models_dir = predictions_dir / "protocol" / stage, processed / "models" / "protocol"
    runs_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    suffix, score_blocks = cfg["gnn"]["score_variant"]["suffix"], cfg["gnn"]["score_variant"]["features"]
    started = time.time()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        free, total = torch.cuda.mem_get_info()
        log.info("GPU memory: %.1f GiB free of %.1f", free / GIB, total / GIB)
        if free < protocol["gpu"]["min_free_gb"] * GIB:
            log.error("stopped: %.1f GiB free on the GPU, %s needed (another job is using it)", free / GIB, protocol["gpu"]["min_free_gb"])
            return 3
        torch.cuda.set_per_process_memory_fraction((free - protocol["gpu"]["margin_gb"] * GIB) / total)

    # ---- the graph of the stage, its targets apart, the role of each article
    directory = processed / cfg["kg"][spec["graph"]]["dir"]
    graph = torch.load(directory / f"graph_{setting}.pt", weights_only=False)
    layout = json.loads((directory / "graph_features.json").read_text(encoding="utf-8"))[setting]
    targets = pd.read_parquet(directory / "targets.parquet")
    if list(targets["article_index"]) != list(range(graph["article"].num_nodes)):
        raise ValueError("targets are not aligned on the article nodes")
    split = targets["split"].to_numpy(dtype=object)
    labels = targets["label"].to_numpy(dtype=float, na_value=np.nan)
    year, forum_ids = graph["article"].year.numpy(), targets["forum_id"].to_numpy()
    if not np.array_equal(year, targets["year"].to_numpy()):
        raise ValueError("the years of the article nodes are not those of the targets")
    roles = staged.roles_of(spec["roles"], split)
    data = baselines.Data(features.article_table(graph, layout), labels, roles, device)
    rows = {role: data.rows(role) for role in (TRAIN, VAL, *spec["predict"])}
    log.info("stage %s on the graph '%s': papers with a decision by role %s", stage, spec["graph"], {r: len(v) for r, v in rows.items()})

    def of_years(names: list[str]) -> np.ndarray:
        """Mask of the articles of the years of some splits of the config."""
        return np.isin(year, [y for name in names for y in cfg["splits"][name]])

    # the validation papers of a stage never come after its test papers
    last = {role: year[rows[role]].max() for role in rows if len(rows[role])}
    if not last[TRAIN] <= last[VAL] <= min(last[r] for r in spec["predict"] if r != VAL):
        raise SystemExit(f"the roles of stage {stage} do not follow the order of the years: {last}")

    # ---- borderline zone of the study: fitted on the training papers of the study
    study_train = np.flatnonzero((split == TRAIN) & ~np.isnan(labels))
    _, zone = borderline.training_zone(data.table.mean_rating[study_train], labels[study_train], cfg["baselines"]["borderline"])
    masks = borderline.subsets(data.table.mean_rating, data.table.text_available, zone)
    log.info("borderline zone: mean initial rating in [%.2f, %.2f)", *zone)

    # ---- stage `search` reads the graph of the study through the extended graph: check that it is the same
    if spec["graph"] == "holdout":
        study = torch.load(processed / f"graph_{setting}.pt", weights_only=False)
        part = article_subgraph(graph, torch.from_numpy(of_years(["train", "test"])))
        same = all(torch.equal(part[t].x, study[t].x) for t in study.node_types) and all(
            torch.equal(part[e].edge_index, study[e].edge_index) for e in study.edge_types)
        if not same or set(part.edge_types) != set(study.edge_types):
            raise SystemExit("the training and test years of the extended graph are not the graph of the study")
        log.info("the training and test years of the extended graph are the graph of the study, node by node and edge by edge")
        del study, part

    # ---- stage `depth`: configurations fixed in advance around the one kept by another stage, which must be the one written
    named: dict[str, dict] = {}
    if stage == DEPTH:
        origin = follow["reference_stage"]  # the stage whose kept configuration is the stored cell: its table of configurations is read
        kept = pd.read_csv(tables_dir / f"protocol_{origin}_chosen.csv")
        kept = json.loads(kept.loc[kept["model"] == follow["model"], "params"].iloc[0])
        stored = search.named_configurations(follow["model"], follow["base"], follow["cells"], stored=True)
        if list(stored.values()) != [kept]:  # one stored cell, with the values kept (the order of the keys does not count)
            raise SystemExit(f"the stored cell {stored} is not the configuration kept by stage {follow['reference_stage']}: {kept}")
        named = search.named_configurations(follow["model"], follow["base"], follow["cells"])
        log.info("configurations fixed in advance: %s (stored, not trained: %s)", named, list(stored))

    records = search.Records(tables_dir / f"protocol_{stage}_selection.csv", KEY)
    seeds, selection = cfg["seeds"], protocol["selection"]
    kinds = {name: cfg["baselines"]["models"][name]["kind"] if name in cfg["baselines"]["models"] else "hetero" for name in spec["models"]}

    def candidates(name: str) -> list[dict]:
        if not spec["search"]:
            if kinds[name] == "hetero":
                table = pd.read_csv(tables_dir / "gnn_selection.csv")
                table = table[(table["labels"] == "label") & (table["setting"] == setting)]
            else:
                table = pd.read_csv(tables_dir / "baselines_selection.csv")
            return [stored_configuration(table[(table["model"] == name) & (table["stage"] == "final")], name)]
        return search.sample_configurations(protocol["spaces"][kinds[name]], protocol["budget"], protocol["sample_seed"])

    def training_of(name: str, params: dict) -> dict:
        """Training settings: those of phases 6 and 7 without a search, those of the protocol with one
        or when the stage asks for them."""
        if not spec["search"] and spec.get("training") != "protocol":
            if kinds[name] == "hetero":
                return dict(cfg["gnn"]["training"])
            return {**cfg["baselines"]["training"], "weight_decay": params.get("weight_decay")}
        return {**protocol["training"], "weight_decay": params.get("weight_decay")}

    planned = {}  # training runs of each model: selection, confirmation, then the seeds of the model and of its variant
    for name in spec["models"]:
        n = len(candidates(name))
        confirm = 0 if n == 1 or kinds[name] in DETERMINISTIC_KINDS else min(selection["top"], n) * len(selection["confirm_seeds"])
        planned[name] = (n if n > 1 else 0) + confirm + len(seeds) * (2 if kinds[name] == "hetero" else 1)
        if named:
            planned[name] = len(named) * len(seeds)

    def check_budget(name: str) -> None:
        """Stops the stage when the time already spent plus what the current model still needs, at the mean time of its
        own runs, exceeds the limit. (The first version projected every remaining run of the stage at the mean time of the
        current model, and stopped the search stage on its first GCN run; the models still to come have no measured time.)"""
        spent = records.seconds(stage=stage)
        own = [float(r["seconds"]) for r in records.rows if r["model"] in (name, name + suffix, *named)]
        projected = sum(spent) + max(planned[name] - len(own), 0) * float(np.mean(own or spent))
        if projected > spec["max_hours"] * 3600:
            raise SystemExit(f"stopped: {sum(spent) / 3600:.1f} h spent, {projected / 3600:.1f} h with the remaining runs of {name}: "
                             f"over the limit of {spec['max_hours']} h ({len(spent)} of {sum(planned.values())} runs done)")

    # ---- graph stages, built when the first graph model needs them
    cache: dict = {}

    def graph_stages(kind: str, with_scores: bool) -> dict:
        """Stages of a kind of graph model: the training graph and the validation graph on
        the device, the graphs of the predictions on the CPU until they are needed."""
        key = ("gcn" if kind == "gcn" else "hetero", with_scores)
        if key in cache:
            return cache[key]
        if "scaled" not in cache:
            start = time.time()
            cache["scaled"] = staged.scaled_graph(graph, layout, roles == TRAIN)
            cache["extra"] = data.table.design(score_blocks, rows[TRAIN])
            log.info("graph scaled with the training nodes (%.0f s)", time.time() - start)
        scaled = cache["scaled"]
        wanted = {tuple(spec["train_graph"]), tuple(spec["validation_graph"]), *(tuple(names) for names in spec["predict"].values())}
        on_device = {tuple(spec["train_graph"]), tuple(spec["validation_graph"])}
        if key[0] == "gcn":
            if "flat" not in cache:
                cache["flat"] = features.flatten(graph, scaled.x_dict, layout)
            built = {names: staged.flat_stage(graph, cache["flat"], of_years(list(names))) for names in wanted}
        else:
            plain = cache.get(("hetero", False))
            if with_scores and plain is not None:  # the same graphs with columns added to the articles
                built = {names: staged.with_article_columns(stage_, cache["extra"]) for names, stage_ in plain.items()}
                cache[key] = built
                return built
            built = {names: staged.hetero_stage(scaled, of_years(list(names)), cache["extra"] if with_scores else None) for names in wanted}
        cache[key] = {names: stage_.to(device) if names in on_device else stage_ for names, stage_ in built.items()}
        log.info("stages of %s%s: %s", key[0], suffix if with_scores else "",
                 {"+".join(names): len(stage_.articles) for names, stage_ in cache[key].items()})
        return cache[key]

    def release(key: tuple) -> None:
        cache.pop(key, None)
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

    def train_once(name: str, variant: str, params: dict, seed: int, phase: str) -> float:
        """Validation AUC of one training; trains only if it is not recorded yet. A final
        run writes the predictions of every role of the stage."""
        key = {"stage": stage, "model": variant, "phase": phase, "params": params, "seed": seed}
        file = runs_dir / f"{variant}_seed{seed}.parquet"
        # a configuration of the selection that failed stays failed: starting a finished stage again changes nothing
        found = records.find(key, failed=phase == "selection")
        if found is not None and (phase != "final" or file.exists()):
            return float(found["val_auc"]) if found["status"] == "ok" else float("nan")
        start, kind, model = time.time(), kinds[name], None
        training = training_of(name, params)
        try:
            if kind in ("gcn", "hetero"):
                stages = graph_stages(name if kind == "hetero" else "gcn", variant.endswith(suffix))
                plan = [(stages[tuple(names)], rows[role]) for role, names in spec["predict"].items()] if phase == "final" else []
                probabilities, fitted, model = staged.run(
                    name, params, training, seed, labels, stages[tuple(spec["train_graph"])], rows[TRAIN],
                    stages[tuple(spec["validation_graph"])], rows[VAL], plan, device, log)
                val_auc = fitted.best_val_auc
            else:
                settings = {k: training[k] for k in ("max_epochs", "patience")} if kind == "mlp" else {}
                probabilities, fitted = baselines.run(cfg["baselines"]["models"][name], params, data, seed, settings)
                val_auc = metrics.classification_metrics(labels[rows[VAL]], probabilities[rows[VAL]])["auc"]
        except torch.OutOfMemoryError:
            log.warning("out of memory: %s", key)
            records.add({**key, "val_auc": np.nan, "best_epoch": None, "epochs": None, "seconds": round(time.time() - start, 1),
                         "status": "out_of_memory"})
        else:
            if phase == "final":
                scored = np.concatenate([rows[role] for role in spec["predict"]])
                if np.isnan(probabilities[scored]).any():
                    raise SystemExit(f"{variant}, seed {seed}: a paper to predict has no probability")
                pd.DataFrame({"model": variant, "setting": stage, "seed": seed, "forum_id": forum_ids[scored], "year": year[scored],
                              "split": split[scored], "role": roles[scored], "label": labels[scored].astype(int),
                              "probability": probabilities[scored], "borderline": masks["borderline"][scored],
                              "text_available": masks["with_text"][scored]}).to_parquet(file, index=False)
                if model is not None:
                    torch.save({"state_dict": model.state_dict(), "kind": name, "params": params, "training": training},
                               models_dir / f"{stage}_{variant}_seed{seed}.pt")
            records.add({**key, "val_auc": val_auc, "best_epoch": fitted.best_epoch if fitted else None,
                         "epochs": fitted.epochs if fitted else None, "seconds": round(time.time() - start, 1), "status": "ok"})
        del model
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
        check_budget(name)
        last_record = records.rows[-1]
        return float(last_record["val_auc"]) if last_record["status"] == "ok" else float("nan")

    # ---- models: search (if the stage has one), then the five seeds
    chosen_rows = []
    for name in spec["models"]:
        kind, options = kinds[name], candidates(name)
        if kind == "hetero":  # the graphs of one family of models at a time on the GPU
            release(("gcn", False))
            cache.pop("flat", None)
        elif kind == "gcn":
            release(("hetero", False))
            release(("hetero", True))
        if named:  # every configuration fixed in advance is trained with every seed: nothing is selected
            for label, params in named.items():
                finals = [train_once(name, label, params, seed, "final") for seed in seeds]
                chosen_rows.append({
                    "stage": stage, "model": label, "family": kind, "searched": False, "configurations_in_space": None,
                    "configurations_tried": None, "runs_failed": None, "params": json.dumps(params), "at_edge_of_space": None,
                    "val_auc_selection_seed": float("nan"), "val_auc_selection_seeds_mean": float("nan"),
                    "val_auc_final_mean": float(np.nanmean(finals)), "training": json.dumps(training_of(name, params))})
                log.info("%s: validation AUC %.4f over %d seeds; %.0f min of training so far", label, chosen_rows[-1]["val_auc_final_mean"],
                         len(finals), sum(records.seconds(stage=stage)) / 60)
            continue
        chosen, first, confirmed = options[0], float("nan"), float("nan")
        if len(options) > 1:
            scores = [train_once(name, name, params, selection["seed"], "selection") for params in options]
            if np.isnan(scores).all():
                raise SystemExit(f"every configuration of {name} failed in stage {stage}")
            best = search.best_first(scores, selection["top"])
            means = {}
            for index in best:
                again = [] if kind in DETERMINISTIC_KINDS else [
                    train_once(name, name, options[index], seed, "selection") for seed in selection["confirm_seeds"]]
                means[index] = float(np.mean([scores[index], *again]))  # a failed run leaves the configuration out
            kept = max(best, key=lambda index: -np.inf if np.isnan(means[index]) else means[index])  # first of the best on a tie
            chosen, first, confirmed = options[kept], scores[kept], means[kept]
            log.info("%s: %d configurations, %d failed, chosen %s (validation AUC %.4f with seed %d, %.4f over the selection seeds)",
                     name, len(options), int(np.isnan(scores).sum()), chosen, first, selection["seed"], confirmed)
        variants = [name, name + suffix] if kind == "hetero" else [name]
        for variant in variants:
            finals = [train_once(name, variant, chosen, seed, "final") for seed in seeds]
            space = protocol["spaces"][kinds[name]] if spec["search"] else {}
            failed = sum(1 for r in records.rows if r["model"] == name and r["phase"] == "selection" and r["status"] != "ok")
            chosen_rows.append({
                "stage": stage, "model": variant, "family": kinds[name], "searched": bool(spec["search"]) and variant == name,
                "configurations_in_space": len(baselines.grid({"grid": space})) if space else None,
                "configurations_tried": len(options) if len(options) > 1 else None, "runs_failed": failed if len(options) > 1 else None,
                "params": json.dumps(chosen), "at_edge_of_space": " ".join(search.at_edge(chosen, space)) if space else None,
                "val_auc_selection_seed": first, "val_auc_selection_seeds_mean": confirmed, "val_auc_final_mean": float(np.nanmean(finals)),
                "training": json.dumps(training_of(name, chosen))})
            log.info("%s: validation AUC %.4f over %d seeds; %.0f min of training so far", variant, chosen_rows[-1]["val_auc_final_mean"],
                     len(finals), sum(records.seconds(stage=stage)) / 60)

    # ---- outputs
    pd.DataFrame(chosen_rows).to_csv(tables_dir / f"protocol_{stage}_chosen.csv", index=False)
    names = [row["model"] for row in chosen_rows]
    files = [runs_dir / f"{name}_seed{seed}.parquet" for name in names for seed in seeds]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        log.error("%d final runs are missing: %s", len(missing), missing)
        return 1
    pd.concat([pd.read_parquet(f) for f in files], ignore_index=True).to_parquet(predictions_dir / f"protocol_{stage}.parquet", index=False)
    table = pd.DataFrame(records.rows)
    log.info("stage %s: %d runs, %.2f h of training, %d failed, %.1f min since the start", stage, len(table), table["seconds"].sum() / 3600,
             int((table["status"] != "ok").sum()), (time.time() - started) / 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
