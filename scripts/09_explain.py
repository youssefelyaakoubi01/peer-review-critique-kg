"""Phase 9: explanations of the main model on test articles, on CPU.

    uv run python scripts/09_explain.py                         # everything, one process
    uv run python scripts/09_explain.py --shard 0 --shards 3    # one of three processes run side by side
    uv run python scripts/09b_explain_results.py                # tables and figures

For each explained article (config `explain`): its prediction is computed again on its
own computation graph and compared with the one stored in phase 7; then
  - each critique of its reviews is removed in turn (importance by occlusion),
  - each relation is removed, the scores of its reviews are set to the training mean,
    all its critiques are removed (scale of the importances),
  - the critique features are attributed with captum (input x gradient; integrated
    gradients on a sub-sample),
  - the k most important critiques are removed, or kept alone, and so are k random ones
    (fidelity).
The models of the other seeds explain a sub-sample (occlusion of the critiques only).

The outcome of a paper is only used to choose the sample (same number of accepted and
rejected papers) and is written next to its explanation; no explanation depends on it.

One JSON file per article and seed in results/predictions/explanations/: a run that is
interrupted, or split in several processes, never computes an article twice.
"""

import argparse
import hashlib
import json
import sys
import time

import numpy as np
import pandas as pd
import torch

from src.collect.store import write_json
from src.eval import borderline
from src.explain import gradients, occlusion, sample, subgraph
from src.kg.tables import CRITIQUE_LABELS, REVIEW_SCORES
from src.models import baselines, features, hetero
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1, help="number of processes that share the articles")
    parser.add_argument("--limit", type=int, help="only the first tasks of this process (dry run)")
    args = parser.parse_args()
    cfg = load_config()
    settings = cfg["explain"]
    log = setup_run_logging(f"09_explain_{args.shard}of{args.shards}", cfg["paths"]["logs"])
    torch.set_num_threads(settings["threads"])
    processed, out_dir = cfg["paths"]["processed"], cfg["paths"]["predictions"] / "explanations"
    setting, kind = settings["setting"], settings["model"]

    # ---- graph, features scaled as for the model, targets
    graph = torch.load(processed / f"graph_{setting}.pt", weights_only=False)
    layout = json.loads((processed / "graph_features.json").read_text(encoding="utf-8"))[setting]
    targets = pd.read_parquet(processed / "targets.parquet")
    if list(targets["article_index"]) != list(range(graph["article"].num_nodes)):
        raise ValueError("targets are not aligned on the article nodes")
    split = targets["split"].to_numpy(dtype=object)
    labels = targets["label"].to_numpy(dtype=float, na_value=np.nan)
    table = features.article_table(graph, layout)
    train_rows = np.flatnonzero((split == baselines.TRAIN) & ~np.isnan(labels))
    _, zone = borderline.training_zone(table.mean_rating[train_rows], labels[train_rows], cfg["baselines"]["borderline"])
    in_zone = borderline.subsets(table.mean_rating, table.text_available, zone)["borderline"]
    x = features.standardise(graph, layout, features.training_nodes(graph, torch.from_numpy(split == baselines.TRAIN)))
    index = subgraph.GraphIndex(x, {edge_type: graph[edge_type].edge_index for edge_type in graph.edge_types})
    relations = subgraph.relations(graph.edge_types)
    score_columns = [features.columns(layout, "review", score).start for score in REVIEW_SCORES]
    # labels of each critique, read from its one-hot blocks
    raw = graph["critique"].x
    critique_labels = {}
    for name, values in CRITIQUE_LABELS.items():
        block = raw[:, features.columns(layout, "critique", name)]
        critique_labels[name] = np.where(block.sum(dim=1).numpy() > 0, np.array(values, dtype=object)[block.argmax(dim=1).numpy()], None)
    critique_labels["actionable"] = raw[:, features.columns(layout, "critique", "actionable")].squeeze(1).numpy() > 0
    critique_ids = pd.read_parquet(processed / "nodes_critique.parquet")["critique_id"].to_numpy()

    # ---- articles to explain
    candidates = np.flatnonzero((split == baselines.TEST) & ~np.isnan(labels))
    chosen = sample.explained_articles(targets["forum_id"].to_numpy(), labels, in_zone, candidates,
                                       settings["sample"]["per_group"], settings["sample"]["salt"])
    main_seed = settings["seed"]
    tasks = [(main_seed, row) for row in chosen.itertuples()]
    tasks += [(seed, row) for seed in settings["stability"]["seeds"] for row in chosen.itertuples() if row.rank < settings["stability"]["per_group"]]
    tasks = [task for position, task in enumerate(tasks) if position % args.shards == args.shard][:args.limit]
    log.info("articles explained: %s; tasks of this process: %d", chosen["group"].value_counts().to_dict(), len(tasks))

    models, stored = {}, {}

    def model_of(seed: int) -> torch.nn.Module:
        if seed not in models:
            # the weights were saved from the GPU: without map_location they would be loaded there
            saved = torch.load(processed / "models" / f"label_{setting}_{kind}_seed{seed}.pt", weights_only=False, map_location="cpu")
            model = hetero.HeteroGNN(saved["kind"], saved["metadata"], saved["in_dims"], saved["params"]["hidden"],
                                     saved["params"]["layers"], saved["params"]["dropout"], saved["training"]["heads"])
            model.load_state_dict(saved["state_dict"])
            models[seed] = model.eval()
            predictions = pd.read_parquet(cfg["paths"]["predictions"] / "gnn" / f"label_{setting}_{kind}_seed{seed}.parquet")
            stored[seed] = predictions.set_index("forum_id")["probability"]
        return models[seed]

    started, done = time.time(), 0
    for seed, row in tasks:
        path = out_dir / f"seed{seed}" / f"{row.forum_id}.json"
        if path.exists():
            continue
        start = time.time()
        model = model_of(seed)
        hood = index.neighbourhood(int(row.article_index), len(model.convs))
        base, importances = occlusion.critique_importances(model, hood)
        probability = float(torch.sigmoid(torch.tensor(base)))
        gap = abs(probability - float(stored[seed][row.forum_id]))
        if gap > settings["max_prediction_gap"]:
            raise SystemExit(f"article {row.forum_id}, seed {seed}: probability {probability:.6f} differs from the stored one by {gap:.6f}")
        nodes = hood.nodes["critique"][hood.critiques].numpy()
        record = {"forum_id": row.forum_id, "seed": seed, "article_index": int(row.article_index), "label": int(row.label),
                  "borderline": bool(row.borderline), "group": row.group, "rank": int(row.rank), "population": int(row.population),
                  "logit": base, "probability": probability, "stored_probability": float(stored[seed][row.forum_id]),
                  "n_nodes": hood.n_nodes, "n_edges_first_layer": int(sum(e.shape[1] for e in hood.layer_edges[0].values())),
                  "n_reviews": len(hood.reviews), "n_critiques": len(hood.critiques)}
        critiques = [{"critique_id": critique_ids[node], "occlusion": float(value),
                      **{name: (bool(values[node]) if name == "actionable" else values[node]) for name, values in critique_labels.items()}}
                     for node, value in zip(nodes, importances)]
        if seed == main_seed:
            record["relations"] = occlusion.relation_importances(model, hood, base, relations)
            record["references"] = occlusion.reference_importances(model, hood, base, score_columns)
            attributions = {"input_x_gradient": gradients.critique_attributions(model, hood, "input_x_gradient")[hood.critiques.numpy()]}
            if row.rank < settings["integrated_gradients"]["per_group"]:
                attributions["integrated_gradients"] = gradients.critique_attributions(
                    model, hood, "integrated_gradients", settings["integrated_gradients"]["steps"])[hood.critiques.numpy()]
            for method, values in attributions.items():
                for critique, value in zip(critiques, values):
                    critique[method] = float(value)
            record["fidelity"] = []
            for method, scores in (("occlusion", importances), ("input_x_gradient", attributions["input_x_gradient"])):
                rng = np.random.default_rng(int(hashlib.sha256(row.forum_id.encode()).hexdigest()[:8], 16))  # same random critiques for both
                record["fidelity"] += [{"method": method, **values} for values in occlusion.fidelity(model, hood, scores, settings["fidelity_k"], rng)]
        record["critiques"] = critiques
        record["seconds"] = round(time.time() - start, 2)
        write_json(path, record)
        done += 1
        if done == 20 or done % 100 == 0:
            elapsed = time.time() - started
            projected = elapsed / done * len(tasks) / 3600  # upper bound: the first tasks are the longest ones
            log.info("%d tasks done in %.1f min; projected total of this process at this pace: %.1f h", done, elapsed / 60, projected)
            if done == 20 and projected > settings["max_hours"]:
                log.error("stopped: projected run time %.1f h exceeds %s h", projected, settings["max_hours"])
                return 2
    log.info("process %d of %d finished: %d tasks computed in %.1f min", args.shard, args.shards, done, (time.time() - started) / 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
