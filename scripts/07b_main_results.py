"""Phase 7: main results table, confidence intervals and significance tests.

    uv run python scripts/07b_main_results.py

Reads the predictions of the baselines (scripts/06_baselines.py) and of the
heterogeneous GNNs (scripts/07_hetero_gnn.py); trains nothing.

Outputs in results/tables/:
    main_results_by_seed.csv   metrics per model, setting, seed, split and subset of papers
    main_results.csv           mean and standard deviation over the seeds
    main_results.tex           LaTeX table of the test split (all papers, borderline papers)
    main_results_tests.csv     test split: bootstrap confidence intervals of every metric, AUC
                               difference with the reference baselines (paired bootstrap), DeLong test
    paired_comparisons.csv     validation and test: AUC difference between a model and its control
                               (pairs of `gnn.statistics.comparisons`), paired bootstrap, DeLong test
    main_results_withdrawn_as_reject.csv   robustness: withdrawn papers counted as rejections
"""

import sys

import numpy as np
import pandas as pd

from src.eval import metrics, stats
from src.eval.compare import bootstrap, by_seed_metrics, mean_auc, versus
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

SUBSET_LABELS = {"all": "All papers", "borderline": "Borderline papers"}
KEYS = ["model", "setting", "split", "subset"]


def main() -> int:
    cfg = load_config()
    settings = cfg["gnn"]["statistics"]
    log = setup_run_logging("07b_main_results", cfg["paths"]["logs"])
    tables_dir, predictions_dir = cfg["paths"]["tables"], cfg["paths"]["predictions"]

    baselines = pd.read_parquet(predictions_dir / "baselines.parquet").assign(setting=cfg["baselines"]["setting"])
    gnn = pd.read_parquet(predictions_dir / "gnn.parquet").drop(columns="labels")
    predictions = pd.concat([baselines, gnn], ignore_index=True)

    # ---- metrics
    by_seed = by_seed_metrics(predictions)
    by_seed.to_csv(tables_dir / "main_results_by_seed.csv", index=False)
    summary = metrics.summarise(by_seed, KEYS)
    summary.to_csv(tables_dir / "main_results.csv", index=False)
    # the rows of the baselines must be those of phase 6
    reference = pd.read_csv(tables_dir / "baselines.csv").set_index(["model", "split", "subset"])
    ours = summary[summary["model"].isin(baselines["model"].unique())].set_index(["model", "split", "subset"])
    columns = [f"{m}_{s}" for m in metrics.METRICS for s in ("mean", "std")]
    if not np.allclose(ours.loc[reference.index, columns].to_numpy(), reference[columns].to_numpy(), atol=1e-12, equal_nan=True):
        raise ValueError("baseline rows differ from results/tables/baselines.csv")

    test = summary[(summary["split"] == "test") & summary["subset"].isin(SUBSET_LABELS)].copy()
    test["row"] = test["model"] + np.where(test["model"].isin(gnn["model"].unique()), " (" + test["setting"] + ")", "")
    # rows: baselines, then the GNNs of setting A, then those of setting B, each architecture next to its variant
    order = [*baselines["model"].unique(), *[kind + end for kind in cfg["gnn"]["models"] for end in ("", cfg["gnn"]["score_variant"]["suffix"])]]
    test = test.assign(subset_rank=test["subset"].map(list(SUBSET_LABELS).index), model_rank=test["model"].map(order.index))
    test = test.sort_values(["subset_rank", "setting", "model_rank"]).drop(columns=["subset_rank", "model_rank"])
    (tables_dir / "main_results.tex").write_text(metrics.latex_table(
        test, "row", {}, caption=f"Test year ({', '.join(map(str, cfg['splits']['test']))}): baselines and heterogeneous GNNs in "
        f"settings A (before the author response) and B (with the author responses), mean $\\pm$ standard deviation over "
        f"{len(cfg['seeds'])} seeds.", label="tab:main-results", group="subset", group_labels=SUBSET_LABELS), encoding="utf-8")

    # ---- confidence intervals and tests, on the test split
    setting_a = cfg["baselines"]["setting"]
    validation = summary[(summary["split"] == "val") & (summary["subset"] == "all") & summary["model"].isin(baselines["model"].unique())]
    best_baseline = validation.loc[validation["auc_mean"].idxmax(), "model"]
    references = list(dict.fromkeys([*settings["reference_baselines"], best_baseline]))
    log.info("best baseline on validation: %s; references of the tests: %s", best_baseline, references)
    by_split = {split: predictions[predictions["split"] == split] for split in ("val", "test")}
    models = list(by_split["test"][["model", "setting"]].drop_duplicates().itertuples(index=False, name=None))
    pairs = [((model, setting_a), (control, setting_a)) for model, control in settings["comparisons"]]
    rows, comparisons = [], []
    for subset in settings["subsets"]:
        papers, labels, matrices, samples = bootstrap(by_split["test"], subset, models, settings)
        for key in models:
            row = {"model": key[0], "setting": key[1], "subset": subset, "n_papers": len(papers), "n_resamples": settings["n_resamples"]}
            for column, metric in enumerate(metrics.METRICS):
                row[f"{metric}_ci_low"], row[f"{metric}_ci_high"] = stats.interval(samples[key][:, column], settings["confidence"])
            for name in references:
                if key == (name, setting_a):
                    continue
                result = versus(labels, matrices, samples, key, (name, setting_a), settings["confidence"])
                row.update({f"auc_minus_{name}": result["difference"], f"auc_minus_{name}_ci_low": result["ci_low"],
                            f"auc_minus_{name}_ci_high": result["ci_high"],
                            f"delong_auc_mean_probability_vs_{name}": result["delong_auc_mean_probability"],
                            f"delong_z_vs_{name}": result["delong_z"], f"delong_p_vs_{name}": result["delong_p"]})
            rows.append(row)
        # a model against its control: test (samples already drawn), then validation
        for split in ("test", "val"):
            if split == "val":
                papers, labels, matrices, samples = bootstrap(by_split["val"], subset, sorted({key for pair in pairs for key in pair}), settings)
            for key, control in pairs:
                comparisons.append({"model": key[0], "control": control[0], "setting": setting_a, "split": split, "subset": subset,
                                    "n_papers": len(papers), "n_resamples": settings["n_resamples"],
                                    "auc_model": mean_auc(labels, matrices[key]), "auc_control": mean_auc(labels, matrices[control]),
                                    **versus(labels, matrices, samples, key, control, settings["confidence"])})
    tests = pd.DataFrame(rows)
    tests.to_csv(tables_dir / "main_results_tests.csv", index=False)
    comparisons = pd.DataFrame(comparisons).sort_values(["split", "subset"], kind="stable")
    comparisons.to_csv(tables_dir / "paired_comparisons.csv", index=False)

    # ---- robustness
    other = pd.read_parquet(predictions_dir / "gnn_withdrawn_as_reject.parquet").drop(columns="labels")
    metrics.summarise(by_seed_metrics(other), KEYS).to_csv(tables_dir / "main_results_withdrawn_as_reject.csv", index=False)

    shown = ["model", "setting", "subset", "n_papers", *[f"{m}_mean" for m in metrics.METRICS], "auc_std"]
    log.info("test split\n%s", test[shown].round(4).to_string(index=False))
    columns = ["model", "setting", "subset", "auc_ci_low", "auc_ci_high", *[c for c in tests.columns if c.startswith(("auc_minus", "delong_p"))]]
    log.info("tests\n%s", tests[columns].round(4).to_string(index=False))
    log.info("paired comparisons\n%s", comparisons.drop(columns=["setting", "n_resamples"]).round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
