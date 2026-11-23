"""Holdout year (ICLR 2026): tables, confidence intervals and tests. Trains nothing.

    uv run python scripts/07d_holdout_results.py

Reads the predictions written by scripts/07c_holdout.py. Same metrics, same subsets of
papers, same reference baselines and same pairs of models as for the test year
(scripts/07b_main_results.py).

Outputs in results/tables/ (<tag> = holdout_<years>):
    <tag>_by_seed.csv       metrics per model, seed and subset of papers
    <tag>.csv               mean and standard deviation over the seeds
    <tag>_tests.csv         bootstrap intervals, AUC difference with the reference baselines, DeLong tests
    <tag>_paired.csv        AUC difference between a model and its control (pairs of `gnn.statistics.comparisons`)
    <tag>_readings.csv      the three conclusions of the test year, set before this run, checked on the holdout year
    <tag>_vs_test_year.csv  AUC of each model on the test year and on the holdout year
    <tag>_graph_growth.csv  graph models: AUC on the test year when its articles are predicted on the extended graph
    <tag>_second_run.csv    only if scripts/07c_holdout.py was run a second time with --suffix _rerun: the models
                            trained again, from one training to the next and against the models of the test year
    <tag>.tex               LaTeX table
"""

import sys

import numpy as np
import pandas as pd

from src.eval import metrics, stats
from src.eval.compare import bootstrap, by_seed_metrics, mean_auc, seed_matrix, versus
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

KEYS = ["model", "setting", "split", "subset"]
SUBSET_LABELS = {"all": "All papers", "borderline": "Borderline papers"}
REFERENCE = "scores_rating_lr"


def readings(tests: pd.DataFrame, paired: pd.DataFrame, gnn_models: list[str]) -> pd.DataFrame:
    """The three conclusions of the test year, as they were written before this run:
    (a) no heterogeneous GNN above the logistic regression on the initial rating;
    (b) HAN and HGT above the GCN; (c) no gain from the critique counts added to the
    scores. A difference counts when its confidence interval excludes zero."""
    rows = []
    for subset in tests["subset"].unique():
        gnns = tests[(tests["subset"] == subset) & tests["model"].isin(gnn_models)]
        low, high = gnns[f"auc_minus_{REFERENCE}_ci_low"], gnns[f"auc_minus_{REFERENCE}_ci_high"]
        best = gnns.loc[gnns[f"auc_minus_{REFERENCE}"].idxmax()]
        rows.append({"reading": "a", "statement": f"no heterogeneous GNN is above {REFERENCE}", "subset": subset,
                     "holds": bool((low <= 0).all()),
                     "detail": f"{int((high < 0).sum())} of {len(gnns)} significantly below, {int((low > 0).sum())} significantly above; "
                               f"closest: {best['model']} {best[f'auc_minus_{REFERENCE}']:+.4f} "
                               f"[{best[f'auc_minus_{REFERENCE}_ci_low']:+.4f}, {best[f'auc_minus_{REFERENCE}_ci_high']:+.4f}]"})
        of_subset = paired[paired["subset"] == subset].set_index(["model", "control"])

        def pair(model: str, control: str) -> str:
            row = of_subset.loc[(model, control)]
            return f"{model} - {control} {row['difference']:+.4f} [{row['ci_low']:+.4f}, {row['ci_high']:+.4f}]"

        above = [of_subset.loc[(model, "gcn"), "ci_low"] > 0 for model in ("han", "hgt")]
        rows.append({"reading": "b", "statement": "HAN and HGT are above the GCN", "subset": subset, "holds": bool(all(above)),
                     "detail": "; ".join(pair(model, "gcn") for model in ("han", "hgt", "rgcn"))})
        added = [("scores_critiques_lr", "scores_all_lr"), ("scores_critiques_gbt", "scores_all_gbt")]
        rows.append({"reading": "c", "statement": "the critique counts added to the scores bring no gain", "subset": subset,
                     "holds": bool(all(of_subset.loc[key, "ci_low"] <= 0 for key in added)),
                     "detail": "; ".join(pair(*key) for key in added)})
    return pd.DataFrame(rows).sort_values(["reading", "subset"], kind="stable")


def main() -> int:
    cfg = load_config()
    statistics, setting = cfg["gnn"]["statistics"], cfg["holdout"]["setting"]
    log = setup_run_logging("07d_holdout_results", cfg["paths"]["logs"])
    tables_dir, predictions_dir = cfg["paths"]["tables"], cfg["paths"]["predictions"]
    years = cfg["splits"]["holdout"]
    tag = "holdout_" + "_".join(map(str, years))
    suffix = cfg["gnn"]["score_variant"]["suffix"]
    gnn_models = [kind + end for kind in cfg["gnn"]["models"] for end in ("", suffix)]

    predictions = pd.read_parquet(predictions_dir / f"{tag}.parquet")
    order = [*cfg["baselines"]["models"], *gnn_models]
    counts = predictions.groupby("model")["seed"].nunique()
    if set(counts.index) != set(order) or (counts != len(cfg["seeds"])).any() or set(predictions["split"]) != {"holdout"}:
        raise ValueError(f"unexpected predictions: {counts.to_dict()}")
    checks = pd.read_csv(tables_dir / f"{tag}_checks.csv")
    if not checks.loc[checks["required"], "passed"].all():
        raise ValueError("a required check of scripts/07c_holdout.py failed")

    # ---- metrics
    by_seed = by_seed_metrics(predictions)
    by_seed.to_csv(tables_dir / f"{tag}_by_seed.csv", index=False)
    summary = metrics.summarise(by_seed, KEYS)
    summary = summary.assign(rank=summary["model"].map(order.index)).sort_values(["subset", "rank"], kind="stable").drop(columns="rank")
    summary.to_csv(tables_dir / f"{tag}.csv", index=False)

    # ---- intervals and tests: the references and the pairs of the test year
    test_year = pd.read_csv(tables_dir / "main_results_tests.csv")
    references = [column.removeprefix("auc_minus_") for column in test_year.columns
                  if column.startswith("auc_minus_") and not column.endswith(("_ci_low", "_ci_high"))]
    models = [(name, setting) for name in order]
    pairs = [((model, setting), (control, setting)) for model, control in statistics["comparisons"]]
    rows, paired = [], []
    for subset in statistics["subsets"]:
        papers, labels, matrices, samples = bootstrap(predictions, subset, models, statistics)
        for key in models:
            row = {"model": key[0], "setting": key[1], "subset": subset, "n_papers": len(papers), "n_resamples": statistics["n_resamples"]}
            for column, metric in enumerate(metrics.METRICS):
                row[f"{metric}_ci_low"], row[f"{metric}_ci_high"] = stats.interval(samples[key][:, column], statistics["confidence"])
            for name in references:
                if key == (name, setting):
                    continue
                result = versus(labels, matrices, samples, key, (name, setting), statistics["confidence"])
                row.update({f"auc_minus_{name}": result["difference"], f"auc_minus_{name}_ci_low": result["ci_low"],
                            f"auc_minus_{name}_ci_high": result["ci_high"],
                            f"delong_auc_mean_probability_vs_{name}": result["delong_auc_mean_probability"],
                            f"delong_z_vs_{name}": result["delong_z"], f"delong_p_vs_{name}": result["delong_p"]})
            rows.append(row)
        for key, control in pairs:
            paired.append({"model": key[0], "control": control[0], "setting": setting, "split": "holdout", "subset": subset,
                           "n_papers": len(papers), "n_resamples": statistics["n_resamples"],
                           "auc_model": mean_auc(labels, matrices[key]), "auc_control": mean_auc(labels, matrices[control]),
                           **versus(labels, matrices, samples, key, control, statistics["confidence"])})
    tests, paired = pd.DataFrame(rows), pd.DataFrame(paired)
    tests.to_csv(tables_dir / f"{tag}_tests.csv", index=False)
    paired.to_csv(tables_dir / f"{tag}_paired.csv", index=False)
    read = readings(tests, paired, gnn_models)
    read.to_csv(tables_dir / f"{tag}_readings.csv", index=False)

    # ---- the test year next to the holdout year
    main = pd.read_csv(tables_dir / "main_results.csv")
    main = main[(main["split"] == "test") & (main["setting"] == setting)].set_index(["model", "subset"])
    of_holdout = summary.set_index(["model", "subset"])
    both = pd.DataFrame([{"model": model, "subset": subset, "n_test_year": int(main.loc[(model, subset), "n_papers"]),
                          "auc_test_year": main.loc[(model, subset), "auc_mean"], "n_holdout": int(of_holdout.loc[(model, subset), "n_papers"]),
                          "auc_holdout": of_holdout.loc[(model, subset), "auc_mean"],
                          "auc_holdout_minus_test_year": of_holdout.loc[(model, subset), "auc_mean"] - main.loc[(model, subset), "auc_mean"],
                          "ece_test_year": main.loc[(model, subset), "ece_mean"], "ece_holdout": of_holdout.loc[(model, subset), "ece_mean"]}
                         for subset in SUBSET_LABELS for model in order])
    both.to_csv(tables_dir / f"{tag}_vs_test_year.csv", index=False)

    # ---- graph models: what the larger graph changes for the articles of the test year
    extended = pd.read_parquet(predictions_dir / f"{tag}_test_year.parquet")
    stored = pd.concat([pd.read_parquet(predictions_dir / "gnn.parquet").drop(columns="labels").query("setting == @setting"),
                        pd.read_parquet(predictions_dir / "baselines.parquet").assign(setting=setting)], ignore_index=True)
    stored = stored[(stored["split"] == "test") & stored["model"].isin(extended["model"].unique())]
    papers = stored.drop_duplicates("forum_id").set_index("forum_id")
    growth = []
    for model in [name for name in order if name in set(extended["model"])]:
        before, after = seed_matrix(stored, model, setting, papers.index), seed_matrix(extended, model, setting, papers.index)
        labels = papers["label"].to_numpy()
        growth.append({"model": model, "n_papers": len(papers), "trained_again": model not in gnn_models,
                       "auc_on_the_graph_of_the_study": mean_auc(labels, before), "auc_on_the_extended_graph": mean_auc(labels, after),
                       "mean_absolute_change_of_probability": float(np.abs(after - before).mean()),
                       "share_of_predicted_outcomes_changed": float(((after >= 0.5) != (before >= 0.5)).mean())})
    growth = pd.DataFrame(growth)
    growth["auc_difference"] = growth["auc_on_the_extended_graph"] - growth["auc_on_the_graph_of_the_study"]
    growth.to_csv(tables_dir / f"{tag}_graph_growth.csv", index=False)

    # ---- models trained again (MLPs, GCN): a second run of scripts/07c_holdout.py (--suffix _rerun), if there is one,
    # tells how far they are from the models of the test year and how much they move from one training to the next.
    # The tables above always come from the first run.
    rerun_file = predictions_dir / f"{tag}_rerun.parquet"
    if rerun_file.exists():
        second = pd.read_parquet(rerun_file)
        second_test = pd.read_parquet(predictions_dir / f"{tag}_rerun_test_year.parquet")
        first_checks = checks.groupby("model")["required"].first()
        stored_all = pd.concat([pd.read_parquet(predictions_dir / "gnn.parquet").drop(columns="labels").query("setting == @setting"),
                                pd.read_parquet(predictions_dir / "baselines.parquet").assign(setting=setting)], ignore_index=True)
        stored_all = stored_all[stored_all["split"] == "test"]
        test_papers = stored_all.drop_duplicates("forum_id").set_index("forum_id")
        holdout_papers = predictions.drop_duplicates("forum_id").set_index("forum_id")
        rows = []
        for model in order:
            one, two = (seed_matrix(table, model, setting, holdout_papers.index) for table in (predictions, second))
            row = {"model": model, "trained_again": not bool(first_checks[model]),
                   "auc_holdout_first_run": mean_auc(holdout_papers["label"].to_numpy(), one),
                   "auc_holdout_second_run": mean_auc(holdout_papers["label"].to_numpy(), two),
                   "max_gap_between_runs_on_holdout": float(np.abs(one - two).max())}
            if model in set(second_test["model"]):
                before, after = seed_matrix(stored_all, model, setting, test_papers.index), seed_matrix(second_test, model, setting, test_papers.index)
                row.update({"auc_test_year_stored": mean_auc(test_papers["label"].to_numpy(), before),
                            "auc_test_year_second_run": mean_auc(test_papers["label"].to_numpy(), after),
                            "test_articles_predicted_on": "extended graph" if model in set(extended["model"]) else "no graph"})
            rows.append(row)
        retrained = pd.DataFrame(rows)
        retrained.to_csv(tables_dir / f"{tag}_second_run.csv", index=False)
        log.info("first run against a second run\n%s", retrained.round(4).to_string(index=False))

    # ---- LaTeX
    shown = summary[summary["subset"].isin(SUBSET_LABELS)]
    shown = shown.sort_values("subset", kind="stable", key=lambda s: s.map(list(SUBSET_LABELS).index))
    (tables_dir / f"{tag}.tex").write_text(metrics.latex_table(
        shown, "model", {}, caption=f"Holdout year ({', '.join(map(str, years))}), models frozen after the test year: baselines "
        f"fitted on the training year with the configurations already chosen, GNNs of setting {setting} with their saved weights. "
        f"Mean $\\pm$ standard deviation over {len(cfg['seeds'])} seeds.", label="tab:holdout", group="subset",
        group_labels=SUBSET_LABELS, wide=True), encoding="utf-8")

    columns = ["model", "subset", "n_papers", "auc_mean", "auc_std", "macro_f1_mean", "mcc_mean", "accuracy_mean", "ece_mean"]
    log.info("holdout year\n%s", shown[columns].round(4).to_string(index=False))
    log.info("tests\n%s", tests[["model", "subset", "auc_ci_low", "auc_ci_high",
                                 *[c for c in tests.columns if c.startswith(("auc_minus", "delong_p"))]]].round(4).to_string(index=False))
    log.info("paired comparisons\n%s", paired.drop(columns=["setting", "n_resamples", "delong_auc_mean_probability"]).round(4).to_string(index=False))
    log.info("test year and holdout year\n%s", both.round(4).to_string(index=False))
    log.info("graph growth\n%s", growth.round(4).to_string(index=False))
    log.info("readings set before this run\n%s", read.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
