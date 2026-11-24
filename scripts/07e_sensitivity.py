"""Sensitivity analyses on the stored predictions. Trains nothing, chooses nothing.

    uv run python scripts/07e_sensitivity.py

Reads the predictions of phases 6 and 7, the graph of setting A and the result tables
of phases 7 and 8. Every analysis is post hoc: the test and holdout years had already
been looked at when it was added (`sensitivity` in the config).

Outputs in results/tables/:
    kg_concept_scope.csv            what the concept vocabulary owes to the years after the training years
    kg_shares_concept_by_year.csv   shares_concept pairs per pair of years
    kg_concept_neighbours.csv       per year: articles with a concept, a neighbour, a neighbour of the training years
    sensitivity_mean_rating.csv     AUC of the mean initial rating used as a score (validation and test)
    sensitivity_pairs.csv           pairs of models that had no test: AUC difference, paired bootstrap, DeLong
    sensitivity_subgroups.csv       models against the reference on the test papers with text, and with the
                                    withdrawn papers counted as rejections
    sensitivity_borderline_zones.csv   the borderline zone under other definitions
    sensitivity_borderline.csv      models against the reference inside each of these zones
    tests_holm.csv                  DeLong p-values of each table of the article with their Holm correction
"""

import json
import sys

import numpy as np
import pandas as pd
import torch

from src.eval import borderline, sensitivity, stats
from src.eval.compare import bootstrap
from src.kg.tables import HAS_CONCEPT, SHARES_CONCEPT
from src.models import features
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

TRAIN, VAL, TEST = "train", "val", "test"
STUDY = "study"  # the zone of the article
PAPER_COLUMNS = ["forum_id", "split", "label", "borderline", "text_available"]


def as_keys(pair) -> tuple:
    return tuple(tuple(side) for side in pair)


def main() -> int:
    cfg = load_config()
    settings, statistics = cfg["sensitivity"], cfg["gnn"]["statistics"]
    log = setup_run_logging("07e_sensitivity", cfg["paths"]["logs"])
    tables_dir, predictions_dir, processed = cfg["paths"]["tables"], cfg["paths"]["predictions"], cfg["paths"]["processed"]
    setting, reference = settings["setting"], (settings["reference"], settings["setting"])

    # ---- inputs: the graph of setting A, the targets apart, the stored predictions
    graph = torch.load(processed / f"graph_{setting}.pt", weights_only=False)
    layout = json.loads((processed / "graph_features.json").read_text(encoding="utf-8"))[setting]
    targets = pd.read_parquet(processed / "targets.parquet")
    if list(targets["article_index"]) != list(range(graph["article"].num_nodes)):
        raise ValueError("targets are not aligned on the article nodes")
    table = features.article_table(graph, layout)
    labels = targets["label"].to_numpy(dtype=float, na_value=np.nan)
    split = targets["split"].to_numpy(dtype=object)
    mean_rating = pd.Series(table.mean_rating, index=targets["forum_id"])

    baselines = pd.read_parquet(predictions_dir / "baselines.parquet").assign(setting=cfg["baselines"]["setting"])
    gnn = pd.read_parquet(predictions_dir / "gnn.parquet").drop(columns="labels")
    predictions = pd.concat([baselines, gnn], ignore_index=True)
    papers = predictions.drop_duplicates("forum_id")[PAPER_COLUMNS]

    # ---- A1: scope of the concept vocabulary
    year = graph["article"].year.numpy()
    has_concept, shares_concept = graph[HAS_CONCEPT].edge_index.numpy(), graph[SHARES_CONCEPT].edge_index.numpy()
    concept_sizes = pd.read_parquet(processed / "nodes_concept.parquet")["n_articles"].to_numpy()
    training_years, concepts = cfg["splits"]["train"], cfg["kg"]["concepts"]
    scope, by_year = sensitivity.concept_scope(year, has_concept, shares_concept, concept_sizes, training_years,
                                               concepts["min_articles"], concepts["max_articles_for_shared"])
    neighbours = sensitivity.concept_neighbours(year, has_concept, shares_concept, training_years, {
        "articles of the graph": np.ones(len(year), dtype=bool), "papers with a decision": ~np.isnan(labels)})
    scope.round(4).to_csv(tables_dir / "kg_concept_scope.csv", index=False)
    by_year.to_csv(tables_dir / "kg_shares_concept_by_year.csv", index=False)
    neighbours.round(4).to_csv(tables_dir / "kg_concept_neighbours.csv", index=False)
    log.info("concept vocabulary\n%s", scope.T.to_string(header=False))
    log.info("shares_concept pairs by year\n%s", by_year.to_string(index=False))
    log.info("neighbours\n%s", neighbours.round(4).to_string(index=False))

    # ---- the zone of the study, computed again: it must be the one stored with the predictions
    train_rows = (split == TRAIN) & ~np.isnan(labels)
    definitions = {STUDY: cfg["baselines"]["borderline"], **settings["borderline_variants"]}
    _, study_zone = borderline.training_zone(table.mean_rating[train_rows], labels[train_rows], definitions[STUDY])
    inside = borderline.in_zone(mean_rating.loc[papers["forum_id"]].to_numpy(), study_zone)
    if not np.array_equal(inside, papers["borderline"].to_numpy()):
        raise ValueError("the borderline zone computed here is not the one stored with the predictions")

    # ---- A3: the mean initial rating as a score, and the pairs that had no test
    spec = settings["mean_rating"]
    if table.mean_rating.max() > spec["scale_max"]:
        raise ValueError("a mean rating exceeds mean_rating.scale_max")
    rating_rows = sensitivity.score_as_model(papers, mean_rating / spec["scale_max"], spec["name"], setting, cfg["seeds"])
    predictions = pd.concat([predictions, rating_rows], ignore_index=True)
    by_split = {name: predictions[predictions["split"] == name] for name in (VAL, TEST)}

    rating_key, rows = (spec["name"], setting), []
    for name in (VAL, TEST):
        for subset in statistics["subsets"]:
            chosen, chosen_labels, matrices, samples = bootstrap(by_split[name], subset, [rating_key], statistics)
            low, high = stats.interval(samples[rating_key][:, 0], statistics["confidence"])
            rows.append({"split": name, "subset": subset, "n_papers": len(chosen), "n_accepted": int(chosen_labels.sum()),
                         "auc": sensitivity.mean_auc(chosen_labels, matrices[rating_key]), "auc_ci_low": low, "auc_ci_high": high})
    rating = pd.DataFrame(rows)
    rating.to_csv(tables_dir / "sensitivity_mean_rating.csv", index=False)
    log.info("mean initial rating as a score\n%s", rating.round(4).to_string(index=False))

    pairs = [as_keys(pair) for pair in settings["pairs"]]
    rows = [{"split": TEST, **row} for subset in statistics["subsets"]
            for row in sensitivity.paired_rows(by_split[TEST], subset, pairs, statistics)]
    extra = pd.DataFrame(rows)
    extra.to_csv(tables_dir / "sensitivity_pairs.csv", index=False)

    # ---- A4: papers with text; withdrawn papers counted as rejections
    against_reference = [(tuple(model), reference) for model in settings["models"]]
    rows = [{"analysis": "papers_with_text", "labels": "label", "split": TEST, **row} for subset in settings["subgroups"]
            for row in sensitivity.paired_rows(by_split[TEST], subset, against_reference, statistics)]
    other = pd.read_parquet(predictions_dir / "gnn_withdrawn_as_reject.parquet")
    variant = other["labels"].unique()
    if len(variant) != 1:
        raise ValueError("the robustness predictions mix several definitions of the label")
    other = other.drop(columns="labels")
    robust_pairs = [(key, reference) for key in other[["model", "setting"]].drop_duplicates().itertuples(index=False, name=None) if key != reference]
    rows += [{"analysis": "withdrawn_as_reject", "labels": variant[0], "split": TEST, **row} for subset in statistics["subsets"]
             for row in sensitivity.paired_rows(other[other["split"] == TEST], subset, robust_pairs, statistics)]
    subgroups = pd.DataFrame(rows)
    subgroups.to_csv(tables_dir / "sensitivity_subgroups.csv", index=False)

    # ---- A5: other definitions of the borderline zone, each fitted on the training papers
    zones, rows = [], []
    test_rating = mean_rating.loc[by_split[TEST]["forum_id"]].to_numpy()
    test_papers = papers[papers["split"] == TEST]
    for name, definition in definitions.items():
        zone_row = {"variant": name, **definition}
        try:
            _, bounds = borderline.training_zone(table.mean_rating[train_rows], labels[train_rows], definition)
        except ValueError as error:  # the uncertain bins do not form one interval
            zones.append({**zone_row, "status": str(error).splitlines()[0]})
            continue
        inside = borderline.in_zone(mean_rating.loc[test_papers["forum_id"]].to_numpy(), bounds)
        zones.append({**zone_row, "status": "ok", "zone_low": bounds[0], "zone_high": bounds[1],
                      "n_test_papers": int(inside.sum()), "share_of_test_papers": inside.mean(),
                      "acceptance_rate_in_zone": test_papers["label"].to_numpy()[inside].mean()})
        moved = by_split[TEST].assign(borderline=borderline.in_zone(test_rating, bounds))
        rows += [{"variant": name, "zone_low": bounds[0], "zone_high": bounds[1], "split": TEST, **row}
                 for row in sensitivity.paired_rows(moved, "borderline", against_reference, statistics)]
    zones, zone_pairs = pd.DataFrame(zones), pd.DataFrame(rows)
    zones.round(4).to_csv(tables_dir / "sensitivity_borderline_zones.csv", index=False)
    zone_pairs.to_csv(tables_dir / "sensitivity_borderline.csv", index=False)
    # the zone of the study gives back the differences of phase 7 (same papers, same resamples)
    stored = pd.read_csv(tables_dir / "main_results_tests.csv")
    stored = stored[stored["subset"] == "borderline"].set_index(["model", "setting"])[f"auc_minus_{reference[0]}"]
    again = zone_pairs[zone_pairs["variant"] == STUDY].set_index(["model", "setting"])["difference"]
    if not np.allclose(again.to_numpy(), stored.loc[again.index].to_numpy(), atol=1e-12):
        raise ValueError("the zone of the study does not give back the differences of main_results_tests.csv")

    # ---- A2: Holm correction, one family per table of the article
    holm_settings = settings["holm"]
    families = {name: family for name, family in holm_settings["families"].items() if (tables_dir / family["file"]).is_file()}
    skipped = sorted(set(holm_settings["families"]) - set(families))
    if skipped:  # the tables of the holdout year are written by its own chain
        log.warning("families left out, their result table does not exist: %s", ", ".join(skipped))
    files = {family["file"] for family in families.values()}
    holm = sensitivity.holm_table({name: pd.read_csv(tables_dir / name) for name in files}, families, holm_settings["alpha"])
    holm.to_csv(tables_dir / "tests_holm.csv", index=False)

    shown = ["model", "setting", "control", "control_setting", "subset", "n_papers", "auc_model", "auc_control", "difference", "ci_low",
             "ci_high", "delong_p"]
    log.info("pairs that had no test\n%s", extra[shown].round(4).to_string(index=False))
    log.info("subgroups\n%s", subgroups[["analysis", *shown]].round(4).to_string(index=False))
    log.info("borderline zones\n%s", zones.round(4).to_string(index=False))
    log.info("inside each zone\n%s", zone_pairs[["variant", *shown]].round(4).to_string(index=False))
    summary = holm.groupby("family", sort=False).agg(tests=("n_tests", "first"), missing=("delong_p", lambda p: int(p.isna().sum())),
                                                    rejects=("rejects", "sum"), rejects_holm=("rejects_holm", "sum"),
                                                    ci_excludes_zero=("ci_excludes_zero", "sum"))
    log.info("Holm correction (alpha = %s)\n%s", holm_settings["alpha"], summary.to_string())
    changed = holm[holm["rejects"] & ~holm["rejects_holm"]]
    log.info("tests that reject before the correction and not after it\n%s",
             changed[["family", "model", "setting", "control", "subset", "difference", "delong_p", "delong_p_holm"]].round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
