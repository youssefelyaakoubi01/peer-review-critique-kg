"""Phase 8: tables, tests and figure of the ablations. Trains nothing.

    uv run python scripts/08b_ablation_results.py

Reads the predictions of the ablated models (scripts/08_ablations.py), of the same
model with the author responses (phase 7, setting B) and of the baselines that read no
score (phase 6).

Outputs:
    results/tables/ablations_by_seed.csv   metrics per variant, seed, split and subset of papers
    results/tables/ablations.csv           mean and standard deviation over the seeds; on the validation and
                                           test splits, all papers and borderline papers: confidence interval of
                                           the AUC, AUC difference with the full model (paired bootstrap), DeLong test
    results/tables/ablations_paired.csv    other pairs: variants without scores against baselines without scores,
                                           and the full model trained here against the same model of phase 7
    results/tables/ablations.tex           LaTeX table of the test split
    results/figures/ablations.pdf          AUC difference with the full model on the test split
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.eval import metrics, stats  # noqa: E402
from src.eval.compare import bootstrap, by_seed_metrics, mean_auc, versus  # noqa: E402
from src.eval.figures import AXIS, INK, MUTED, bar, clean, save, style  # noqa: E402
from src.eval.figures import NEGATIVE as WORSE  # noqa: E402
from src.eval.figures import POSITIVE as BETTER  # noqa: E402
from src.eval.paper import VARIANT_LABELS as LABELS  # noqa: E402  (names shown in the figure and in the LaTeX table)
from src.utils.config import load_config  # noqa: E402
from src.utils.runlog import setup_run_logging  # noqa: E402

FULL, PHASE7 = "full", "full_phase7"
SUBSET_LABELS = {"all": "All papers", "borderline": "Borderline papers"}
KEYS = ["model", "setting", "split", "subset"]


def removed(spec: dict) -> str:
    parts = [f"nodes {', '.join(spec['drop_nodes'])}"] if spec.get("drop_nodes") else []
    parts += [f"edges {', '.join(spec['drop_edges'])}"] if spec.get("drop_edges") else []
    parts += [f"{node_type} features {', '.join(blocks)}" for node_type, blocks in spec.get("drop_features", {}).items()]
    return "; ".join(parts) or "nothing"


def figure(table: pd.DataFrame, variants: list[str], path) -> None:
    """Two panels (all papers, borderline papers): AUC of each variant minus AUC of the
    full model on the test split, with its 95 % confidence interval."""
    style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 0.36 * len(variants) + 1.0), sharey=True, sharex=True)
    low = min(table["auc_minus_full_ci_low"].min(), -0.01)
    high = max(table["auc_minus_full_ci_high"].max(), 0.01)
    span = high - low
    for ax, (subset, title) in zip(axes, SUBSET_LABELS.items()):
        rows = table[table["subset"] == subset].set_index("model").loc[variants]
        ax.set_xlim(low - 0.27 * span, high + 0.06 * span)  # room for the value labels on the left
        ax.set_ylim(len(variants) - 0.5, -0.5)
        ax.set_title(f"{title} (n = {int(rows['n_papers'].iloc[0]):,})".replace(",", " "), loc="left", color=INK, fontsize=8.5)
        clean(ax)
        ax.axvline(0, color=AXIS, linewidth=0.8, zorder=1)
        fig.canvas.draw()  # the bars are shaped in pixels: the axes must have their final size
        for position, (name, row) in enumerate(rows.iterrows()):
            value = row["auc_minus_full"]
            bar(ax, position, value, 0.5, WORSE if value < 0 else BETTER)
            ax.plot([row["auc_minus_full_ci_low"], row["auc_minus_full_ci_high"]], [position, position], color=INK, linewidth=0.8, zorder=3)
            ax.text(row["auc_minus_full_ci_low"] - 0.015 * span, position, f"{value:+.3f}", va="center", ha="right", color=INK, fontsize=7.5)
        ax.set_yticks(range(len(variants)), [LABELS[name] for name in variants], color=INK)
        ax.set_xlabel("Test AUC minus test AUC of the full graph", color=MUTED)
    fig.tight_layout()
    save(fig, path)
    plt.close(fig)


def main() -> int:
    cfg = load_config()
    settings, statistics = cfg["ablations"], cfg["gnn"]["statistics"]
    log = setup_run_logging("08b_ablation_results", cfg["paths"]["logs"])
    tables_dir, predictions_dir, figures_dir = cfg["paths"]["tables"], cfg["paths"]["predictions"], cfg["paths"]["figures"]
    figures_dir.mkdir(parents=True, exist_ok=True)
    setting, kind = settings["setting"], settings["model"]

    # ---- predictions: the variants, the same model of phase 7 (both settings), baselines without scores
    ablated = pd.read_parquet(predictions_dir / "ablations.parquet")
    gnn = pd.read_parquet(predictions_dir / "gnn.parquet").drop(columns="labels")
    phase7 = gnn[(gnn["model"] == kind) & (gnn["setting"] == setting)].assign(model=PHASE7)
    others = [gnn[(gnn["model"] == source["model"]) & (gnn["setting"] == source["setting"])].assign(model=name, setting=setting)
              for name, source in settings["from_phase7"].items()]
    controls = sorted({control for _, control in settings["comparisons"]})
    baselines = pd.read_parquet(predictions_dir / "baselines.parquet").assign(setting=setting)
    predictions = pd.concat([ablated, *others, phase7, baselines[baselines["model"].isin(controls)]], ignore_index=True)
    variants = [*settings["variants"], *settings["from_phase7"]]
    counts = predictions.groupby("model")["seed"].nunique()
    if set(counts.index) != {*variants, PHASE7, *controls} or (counts != len(cfg["seeds"])).any():
        raise ValueError(f"predictions are missing: {counts.to_dict()}")

    # ---- metrics
    by_seed = by_seed_metrics(predictions)
    by_seed.to_csv(tables_dir / "ablations_by_seed.csv", index=False)
    summary = metrics.summarise(by_seed, KEYS)

    # ---- confidence intervals and tests
    models = [(name, setting) for name in [*variants, PHASE7, *controls]]
    pairs = [(model, control) for model, control in settings["comparisons"]] + [(FULL, PHASE7)]
    tests, paired = [], []
    for split in ("test", "val"):
        of_split = predictions[predictions["split"] == split]
        for subset in statistics["subsets"]:
            papers, labels, matrices, samples = bootstrap(of_split, subset, models, statistics)
            for name in variants:
                row = {"model": name, "split": split, "subset": subset}
                row["auc_ci_low"], row["auc_ci_high"] = stats.interval(samples[(name, setting)][:, 0], statistics["confidence"])
                if name != FULL:
                    result = versus(labels, matrices, samples, (name, setting), (FULL, setting), statistics["confidence"])
                    row.update({"auc_minus_full": result["difference"], "auc_minus_full_ci_low": result["ci_low"],
                                "auc_minus_full_ci_high": result["ci_high"], "delong_z_vs_full": result["delong_z"],
                                "delong_p_vs_full": result["delong_p"]})
                tests.append(row)
            for model, control in pairs:
                paired.append({"model": model, "control": control, "split": split, "subset": subset, "n_papers": len(papers),
                               "auc_model": mean_auc(labels, matrices[(model, setting)]),
                               "auc_control": mean_auc(labels, matrices[(control, setting)]),
                               **versus(labels, matrices, samples, (model, setting), (control, setting), statistics["confidence"])})
    tests, paired = pd.DataFrame(tests), pd.DataFrame(paired)
    paired.to_csv(tables_dir / "ablations_paired.csv", index=False)

    table = summary[summary["model"].isin(variants)].merge(tests, on=["model", "split", "subset"], how="left")
    specs = {**settings["variants"], **{name: None for name in settings["from_phase7"]}}
    table.insert(1, "removed", table["model"].map(lambda name: "nothing; author responses added (setting B, phase 7)"
                                                  if specs[name] is None else removed(specs[name])))
    table["model_rank"] = table["model"].map(variants.index)
    table = table.sort_values(["split", "subset", "model_rank"], kind="stable").drop(columns="model_rank")
    table.to_csv(tables_dir / "ablations.csv", index=False)

    test = table[(table["split"] == "test") & table["subset"].isin(SUBSET_LABELS)]
    test = test.sort_values("subset", kind="stable", key=lambda s: s.map(list(SUBSET_LABELS).index))
    (tables_dir / "ablations.tex").write_text(metrics.latex_table(
        test, "model", LABELS, caption=f"Ablations of the {kind.upper()} model in setting {setting} on the test year "
        f"({', '.join(map(str, cfg['splits']['test']))}): one element of the graph removed at a time, same hyper-parameters, "
        f"mean $\\pm$ standard deviation over {len(cfg['seeds'])} seeds.", label="tab:ablations", group="subset",
        group_labels=SUBSET_LABELS), encoding="utf-8")
    figure(test, [name for name in variants if name != FULL], figures_dir / "ablations.pdf")

    shown = ["model", "subset", "n_papers", "auc_mean", "auc_std", "auc_minus_full", "auc_minus_full_ci_low", "auc_minus_full_ci_high",
             "delong_p_vs_full"]
    log.info("test split\n%s", test[shown].round(4).to_string(index=False))
    log.info("other pairs\n%s", paired.drop(columns=["delong_auc_mean_probability", "delong_z"]).round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
