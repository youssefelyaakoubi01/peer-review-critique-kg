"""Phase 9: tables and figures of the explanations. Computes no explanation.

    uv run python scripts/09b_explain_results.py

Reads the files written by scripts/09_explain.py (one per article and seed) and, for
the four case studies only, the text of their critiques.

Every average is weighted back to the test year (the sample has as many articles in
each group) and comes with a 95 % bootstrap interval over the articles, drawn inside
each group (src/explain/aggregate.py).

Outputs in results/tables/:
    explainability.csv             importance of a critique by aspect x severity (negative critiques), by aspect
                                   (positive ones) and by polarity, for all / accepted / rejected / borderline papers
    explainability_relations.csv   importance of each relation, of the scores and of all the critiques of an article
    explainability_fidelity.csv    fidelity+ and fidelity- of the k most important critiques against k random ones
    explainability_methods.csv     agreement between occlusion and the gradient attributions
    explainability_seeds.csv       agreement between the models of different seeds
    explainability_cases.csv       the four case studies, critique by critique
    explainability_runs.csv        one row per explained article (time, size, gap with the stored prediction)
and in results/figures/: explain_aspect_severity.pdf, explain_relations.pdf, explain_fidelity.pdf,
explain_case_<name>.pdf.
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from src.collect.store import read_json  # noqa: E402
from src.eval import figures  # noqa: E402
from src.explain import aggregate  # noqa: E402
from src.kg.tables import CRITIQUE_LABELS  # noqa: E402
from src.utils.config import load_config  # noqa: E402
from src.utils.runlog import setup_run_logging  # noqa: E402

METHODS = ("occlusion", "input_x_gradient", "integrated_gradients")
GROUPS = {  # reporting group -> articles that belong to it
    "all": lambda a: np.ones(len(a), dtype=bool),
    "accepted": lambda a: (a["label"] == 1).to_numpy(),
    "rejected": lambda a: (a["label"] == 0).to_numpy(),
    "borderline": lambda a: a["borderline"].to_numpy(),
}
CASES = {  # case study -> (outcome, predicted outcome)
    "accepted_predicted_accept": (1, 1), "rejected_predicted_reject": (0, 0),
    "rejected_predicted_accept": (0, 1), "accepted_predicted_reject": (1, 0),
}
CASE_TITLES = {"accepted_predicted_accept": "Accepted, predicted accept", "rejected_predicted_reject": "Rejected, predicted reject",
               "rejected_predicted_accept": "Rejected, predicted accept", "accepted_predicted_reject": "Accepted, predicted reject"}
MIN_CRITIQUES_FOR_RANKS = 5   # rank correlations are computed on articles with at least this many critiques
MIN_CRITIQUES_SHOWN = 30      # a cell of the heat map with fewer critiques is left empty
EXCERPT = 80


def load(directory) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(articles, critiques, fidelity rows) of one seed."""
    articles, critiques, fidelity = [], [], []
    for path in sorted(directory.glob("*.json")):
        record = read_json(path)
        for row in record.pop("critiques"):
            critiques.append({"forum_id": record["forum_id"], **row})
        for row in record.pop("fidelity", []):
            fidelity.append({"forum_id": record["forum_id"], **row})
        relations, references = record.pop("relations", {}), record.pop("references", {})
        articles.append({**record, **{f"relation_{k}": v for k, v in relations.items()}, **{f"reference_{k}": v for k, v in references.items()}})
    return pd.DataFrame(articles), pd.DataFrame(critiques), pd.DataFrame(fidelity)


def per_article(articles: pd.DataFrame, critiques: pd.DataFrame, values: pd.Series) -> np.ndarray:
    """Sum of `values` (one per critique row) for each article, in the order of `articles`."""
    return values.groupby(critiques.loc[values.index, "forum_id"]).sum().reindex(articles["forum_id"], fill_value=0.0).to_numpy(dtype=float)


def cells(critiques: pd.DataFrame) -> list[dict]:
    """Cells of the importance table: a description and the mask of their critiques."""
    negative, positive = critiques["polarity"] == "negative", critiques["polarity"] == "positive"
    out = [{"kind": "polarity", "polarity": p, "mask": critiques["polarity"] == p} for p in CRITIQUE_LABELS["polarity"]]
    out += [{"kind": "negative_severity", "polarity": "negative", "severity": s, "mask": negative & (critiques["severity"] == s)}
            for s in CRITIQUE_LABELS["severity"]]
    out += [{"kind": "negative_aspect", "polarity": "negative", "aspect": a, "mask": negative & (critiques["aspect"] == a)}
            for a in CRITIQUE_LABELS["aspect"]]
    out += [{"kind": "negative_aspect_severity", "polarity": "negative", "aspect": a, "severity": s,
             "mask": negative & (critiques["aspect"] == a) & (critiques["severity"] == s)}
            for a in CRITIQUE_LABELS["aspect"] for s in CRITIQUE_LABELS["severity"]]
    out += [{"kind": "positive_aspect", "polarity": "positive", "aspect": a, "mask": positive & (critiques["aspect"] == a)}
            for a in CRITIQUE_LABELS["aspect"]]
    return out


def importance_table(articles, critiques, weight, counts, confidence) -> pd.DataFrame:
    rows = []
    members = {group: select(articles).astype(float) for group, select in GROUPS.items()}
    for cell in cells(critiques):
        mask = cell.pop("mask")
        n = per_article(articles, critiques, mask[mask].astype(float))
        for method in METHODS[:2]:
            value = critiques.loc[mask, method]
            signed, absolute = per_article(articles, critiques, value), per_article(articles, critiques, value.abs())
            for group, inside in members.items():
                mean, low, high = aggregate.ratio(signed * inside, n * inside, weight, counts, confidence)
                per_paper, paper_low, paper_high = aggregate.ratio(signed * inside, inside, weight, counts, confidence)
                rows.append({"group": group, "method": method, **cell, "n_articles_with_such_a_critique": int(((n > 0) & (inside > 0)).sum()),
                             "n_critiques": int((n * inside).sum()),
                             "importance_per_critique": mean, "ci_low": low, "ci_high": high,
                             "abs_importance_per_critique": aggregate.ratio(absolute * inside, n * inside, weight, counts, confidence)[0],
                             "importance_per_article": per_paper, "per_article_ci_low": paper_low, "per_article_ci_high": paper_high})
    table = pd.DataFrame(rows)
    table["ci_excludes_zero"] = (table["ci_low"] > 0) | (table["ci_high"] < 0)
    labels = ["group", "method", "kind", "polarity", "aspect", "severity"]
    return table[labels + [column for column in table.columns if column not in labels]]


def relation_table(articles, weight, counts, confidence) -> pd.DataFrame:
    rows = []
    for column in [c for c in articles.columns if c.startswith(("relation_", "reference_"))]:
        kind, name = column.split("_", 1)
        values = articles[column].to_numpy(dtype=float)
        for group, select in GROUPS.items():
            inside = select(articles).astype(float)
            mean, low, high = aggregate.ratio(values * inside, inside, weight, counts, confidence)
            rows.append({"group": group, "kind": kind, "removed": name, "n_articles": int(inside.sum()), "importance": mean,
                         "ci_low": low, "ci_high": high,
                         "abs_importance": aggregate.ratio(np.abs(values) * inside, inside, weight, counts, confidence)[0]})
    return pd.DataFrame(rows)


def fidelity_table(articles, fidelity, weight, counts, confidence) -> pd.DataFrame:
    """Change of the probability of acceptance, and share of flipped predictions, when the
    k most important critiques are removed (fidelity+) or kept alone (fidelity-), against
    k random critiques. Articles with fewer than k critiques are left out."""
    base = articles.set_index("forum_id")["probability"]
    rows = []
    for (method, k), part in fidelity.groupby(["method", "k"]):
        part = part.set_index("forum_id").reindex(articles["forum_id"])
        present = part["top_removed"].notna().to_numpy().astype(float)
        probability = base.reindex(articles["forum_id"]).to_numpy()
        for group, select in GROUPS.items():
            inside = select(articles).astype(float) * present
            row = {"group": group, "method": method, "k": int(k), "n_articles": int(inside.sum())}
            for measure, column in (("fidelity_plus", "removed"), ("fidelity_minus", "kept")):
                change = {name: np.nan_to_num(np.abs(part[f"{name}_{column}"].to_numpy() - probability)) for name in ("top", "random")}
                flip = {name: np.nan_to_num(((part[f"{name}_{column}"].to_numpy() >= 0.5) != (probability >= 0.5)).astype(float)) * present
                        for name in ("top", "random")}
                for name in ("top", "random"):
                    row[f"{measure}_{name}"] = aggregate.ratio(change[name] * inside, inside, weight, counts, confidence)[0]
                    row[f"{measure}_flips_{name}"] = aggregate.ratio(flip[name] * inside, inside, weight, counts, confidence)[0]
                difference = aggregate.ratio((change["top"] - change["random"]) * inside, inside, weight, counts, confidence)
                row[f"{measure}_top_minus_random"], row[f"{measure}_difference_ci_low"], row[f"{measure}_difference_ci_high"] = difference
            rows.append(row)
    return pd.DataFrame(rows)


def rank_agreement(articles, left: pd.DataFrame, right: pd.DataFrame, a: str, b: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per article (order of `articles`): Spearman correlation between two importances of
    its critiques, whether both name the same most important critique, and whether the
    article enters (enough critiques, no constant column)."""
    merged = left[["forum_id", "critique_id", a]].merge(right[["forum_id", "critique_id", b]], on=["forum_id", "critique_id"],
                                                        suffixes=("_left", "_right")).dropna()
    first, second = (a + "_left", b + "_right") if a == b else (a, b)
    rho, same_top = {}, {}
    for forum_id, part in merged.groupby("forum_id"):
        if len(part) < MIN_CRITIQUES_FOR_RANKS or part[first].nunique() < 2 or part[second].nunique() < 2:
            continue
        rho[forum_id] = spearmanr(part[first], part[second]).statistic
        same_top[forum_id] = float(part[first].abs().idxmax() == part[second].abs().idxmax())
    present = articles["forum_id"].isin(rho).to_numpy().astype(float)
    return (articles["forum_id"].map(rho).fillna(0.0).to_numpy(), articles["forum_id"].map(same_top).fillna(0.0).to_numpy(), present)


def agreement_row(label: dict, articles, weight, counts, confidence, values) -> dict:
    rho, same_top, present = values
    mean, low, high = aggregate.ratio(rho * present, present, weight, counts, confidence)
    return {**label, "n_articles": int(present.sum()), "mean_spearman": mean, "ci_low": low, "ci_high": high,
            "share_same_most_important_critique": aggregate.ratio(same_top * present, present, weight, counts, confidence)[0]}


def choose_cases(articles: pd.DataFrame) -> pd.DataFrame:
    """Among the explained borderline articles, for each pair (outcome, prediction): the
    article whose probability is closest to the median of its group (first id on a tie)."""
    chosen = []
    pool = articles[articles["borderline"]].sort_values("forum_id")
    for name, (label, predicted) in CASES.items():
        group = pool[(pool["label"] == label) & ((pool["probability"] >= 0.5).astype(int) == predicted)]
        if group.empty:
            continue
        nearest = (group["probability"] - group["probability"].median()).abs().idxmin()
        chosen.append({"case": name, "articles_in_group": len(group), "median_probability_of_group": float(group["probability"].median()),
                       **group.loc[nearest, ["forum_id", "label", "probability", "n_reviews", "n_critiques", "reference_scores",
                                             "reference_critiques"]].to_dict()})
    return pd.DataFrame(chosen)


# --------------------------------------------------------------------------- figures
def heat_map(table: pd.DataFrame, path) -> None:
    """Importance of one critique (occlusion), by aspect and by severity for negative
    critiques, and for positive critiques by aspect; one panel per group of papers."""
    figures.style()
    groups = ["accepted", "rejected", "borderline"]
    aspects, severities = list(CRITIQUE_LABELS["aspect"]), list(CRITIQUE_LABELS["severity"])
    columns = [*severities, "positive"]
    data = table[table["method"] == "occlusion"]
    grids, shown = {}, []
    for group in groups:
        of_group = data[data["group"] == group]
        grid = np.full((len(aspects), len(columns)), np.nan)
        sure = np.zeros_like(grid, dtype=bool)
        for i, aspect in enumerate(aspects):
            for j, severity in enumerate(severities):
                row = of_group[(of_group["kind"] == "negative_aspect_severity") & (of_group["aspect"] == aspect) & (of_group["severity"] == severity)].iloc[0]
                if row["n_critiques"] >= MIN_CRITIQUES_SHOWN:
                    grid[i, j], sure[i, j] = row["importance_per_critique"], row["ci_excludes_zero"]
            row = of_group[(of_group["kind"] == "positive_aspect") & (of_group["aspect"] == aspect)].iloc[0]
            if row["n_critiques"] >= MIN_CRITIQUES_SHOWN:
                grid[i, -1], sure[i, -1] = row["importance_per_critique"], row["ci_excludes_zero"]
        grids[group] = (grid, sure)
        shown.append(np.nanmax(np.abs(grid)))
    limit = max(shown)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.3), sharey=True)
    for ax, group in zip(axes, groups):
        grid, sure = grids[group]
        image = ax.imshow(grid, cmap=figures.DIVERGING, vmin=-limit, vmax=limit, aspect="auto")
        ax.set_title(f"{group.capitalize()} papers", loc="left", color=figures.INK, fontsize=8.5)
        figures.clean(ax, grid_axis=None)
        ax.set_xticks(range(len(columns)), columns, color=figures.INK, fontsize=7)
        ax.set_yticks(range(len(aspects)), [a.replace("_", " ") for a in aspects], color=figures.INK)
        ax.annotate("negative critiques", xy=((len(severities) / 2) / len(columns), -0.13), xycoords="axes fraction", ha="center",
                    va="top", color=figures.MUTED, fontsize=7)
        ax.set_xticks(np.arange(-0.5, len(columns)), minor=True)
        ax.set_yticks(np.arange(-0.5, len(aspects)), minor=True)
        ax.grid(which="minor", color="white", linewidth=2)  # surface gap between the cells
        ax.tick_params(which="minor", length=0)
        for (i, j), value in np.ndenumerate(grid):
            if np.isnan(value):
                ax.text(j, i, "–", ha="center", va="center", color=figures.MUTED, fontsize=7)
                continue
            dark = abs(value) > 0.6 * limit
            ax.text(j, i, f"{value:+.3f}" + ("" if sure[i, j] else "°"), ha="center", va="center", fontsize=6.5,
                    color="white" if dark else figures.INK)
    bar = fig.colorbar(image, ax=axes, fraction=0.025, pad=0.02)
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=0, colors=figures.MUTED)
    bar.set_label("Logit with the critique minus logit without it", color=figures.MUTED)
    fig.text(0.01, -0.06, f"° 95 % interval includes zero    – fewer than {MIN_CRITIQUES_SHOWN} critiques", color=figures.MUTED, fontsize=7)
    figures.save(fig, path, bbox_inches="tight")
    plt.close(fig)


def relation_figure(table: pd.DataFrame, path) -> None:
    figures.style()
    names = {"scores": "Scores of its reviews\n(set to the training mean)", "critiques": "All its critiques", "has_review": "has_review",
             "contains": "contains", "about": "about", "has_concept": "has_concept", "shares_concept": "shares_concept"}
    order = [name for name in names if name in set(table["removed"])]
    groups = {"all": "All papers", "borderline": "Borderline papers"}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 0.4 * len(order) + 1.0), sharey=True, sharex=True)
    of_groups = table[table["group"].isin(groups)]
    low, high = min(of_groups["ci_low"].min(), 0.0), max(of_groups["ci_high"].max(), 0.0)
    span = high - low
    for ax, (group, title) in zip(axes, groups.items()):
        rows = table[table["group"] == group].set_index("removed").loc[order]
        ax.set_xlim(low - 0.05 * span, high + 0.22 * span)
        ax.set_ylim(len(order) - 0.5, -0.5)
        ax.set_title(title, loc="left", color=figures.INK, fontsize=8.5)
        figures.clean(ax)
        ax.axvline(0, color=figures.AXIS, linewidth=0.8, zorder=1)
        fig.canvas.draw()
        for position, (name, row) in enumerate(rows.iterrows()):
            value = row["importance"]
            figures.bar(ax, position, value, 0.5, figures.POSITIVE if value >= 0 else figures.NEGATIVE)
            ax.plot([row["ci_low"], row["ci_high"]], [position, position], color=figures.INK, linewidth=0.8, zorder=3)
            ax.text(max(row["ci_high"], 0) + 0.015 * span, position, f"{value:+.2f}", va="center", ha="left", color=figures.INK, fontsize=7.5)
        ax.set_yticks(range(len(order)), [names[name] for name in order], color=figures.INK)
        ax.set_xlabel("Logit with the element minus logit without it", color=figures.MUTED)
    fig.tight_layout()
    figures.save(fig, path)
    plt.close(fig)


def fidelity_figure(table: pd.DataFrame, path) -> None:
    figures.style()
    data = table[table["group"] == "all"]
    panels = {"fidelity_plus": "Fidelity+: the k critiques are removed", "fidelity_minus": "Fidelity−: only the k critiques are kept"}
    series = [("occlusion", "top", figures.POSITIVE, "o", "k most important (occlusion)"),
              ("input_x_gradient", "top", figures.SECOND, "s", "k most important (input × gradient)"),
              ("occlusion", "random", figures.NEUTRAL, "D", "k random critiques")]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharex=True)
    for ax, (measure, title) in zip(axes, panels.items()):
        for method, which, colour, marker, label in series:
            rows = data[data["method"] == method].sort_values("k")
            ax.plot(rows["k"], rows[f"{measure}_{which}"], color=colour, linewidth=2, marker=marker, markersize=6,
                    markeredgecolor="white", markeredgewidth=1.5, label=label, zorder=3)
        ax.set_title(title, loc="left", color=figures.INK, fontsize=8.5)
        ax.set_xticks(sorted(data["k"].unique()))
        ax.set_xlabel("k", color=figures.MUTED)
        ax.set_ylim(bottom=0)
        figures.clean(ax, grid_axis="y")
    axes[0].set_ylabel("Mean change of P(accept)", color=figures.MUTED)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=7.5, labelcolor=figures.INK)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    figures.save(fig, path)
    plt.close(fig)


def case_figure(case: pd.Series, critiques: pd.DataFrame, path, top: int = 10) -> None:
    figures.style()
    rows = critiques.reindex(critiques["occlusion"].abs().sort_values(ascending=False).index).head(top)
    labels = [f"“{row.excerpt}”\n{row.aspect.replace('_', ' ')} · {row.severity} · {row.polarity}" for row in rows.itertuples()]
    fig, ax = plt.subplots(figsize=(7.2, 0.52 * len(rows) + 0.9))
    extreme = max(rows["occlusion"].abs().max(), 1e-6)
    ax.set_xlim(-1.45 * extreme, 1.45 * extreme)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    figures.clean(ax)
    ax.axvline(0, color=figures.AXIS, linewidth=0.8, zorder=1)
    fig.canvas.draw()
    for position, value in enumerate(rows["occlusion"]):
        figures.bar(ax, position, value, 0.45, figures.POSITIVE if value >= 0 else figures.NEGATIVE)
        ax.text(value + (0.03 if value >= 0 else -0.03) * extreme, position, f"{value:+.3f}", va="center",
                ha="left" if value >= 0 else "right", color=figures.INK, fontsize=7)
    ax.set_yticks(range(len(rows)), labels, color=figures.INK, fontsize=6.5)
    ax.set_xlabel("Logit with the critique minus logit without it", color=figures.MUTED)
    fig.suptitle(f"{CASE_TITLES[case['case']]} (probability of acceptance {case['probability']:.2f}); the {len(rows)} most important "
                 f"of its {int(case['n_critiques'])} critiques", x=0.01, ha="left", color=figures.INK, fontsize=8.5)
    fig.tight_layout()
    figures.save(fig, path)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--partial", type=Path, metavar="DIR",
                        help="check the script on an unfinished run: everything is written to DIR, never to results/")
    args = parser.parse_args()
    cfg = load_config()
    settings = cfg["explain"]
    statistics = settings["statistics"]
    log = setup_run_logging("09b_explain_results", cfg["paths"]["logs"])
    tables_dir, figures_dir = (args.partial, args.partial) if args.partial else (cfg["paths"]["tables"], cfg["paths"]["figures"])
    tables_dir.mkdir(parents=True, exist_ok=True)
    directory = cfg["paths"]["predictions"] / "explanations"
    confidence = statistics["confidence"]

    articles, critiques, fidelity = load(directory / f"seed{settings['seed']}")
    expected = 4 * settings["sample"]["per_group"]
    if not args.partial and (len(articles) != expected or articles["group"].value_counts().nunique() != 1):
        raise SystemExit(f"{len(articles)} explained articles, {expected} expected in equal groups: is scripts/09_explain.py finished?")
    articles = articles.sort_values("forum_id").reset_index(drop=True)
    untyped = critiques["aspect"].isna()
    critiques = critiques[~untyped].reset_index(drop=True)
    weight = aggregate.weights(articles["group"].to_numpy(), articles["population"].to_numpy())
    counts = aggregate.bootstrap_counts(articles["group"].to_numpy(), statistics["n_resamples"], statistics["seed"])
    log.info("articles %d, critiques %d (%d without label left out), test papers represented %d", len(articles), len(critiques),
             int(untyped.sum()), int(weight.sum()))

    importance = importance_table(articles, critiques, weight, counts, confidence)
    importance.to_csv(tables_dir / "explainability.csv", index=False)
    relations = relation_table(articles, weight, counts, confidence)
    relations.to_csv(tables_dir / "explainability_relations.csv", index=False)
    fidelity_rows = fidelity_table(articles, fidelity, weight, counts, confidence)
    fidelity_rows.to_csv(tables_dir / "explainability_fidelity.csv", index=False)

    # ---- agreement between methods (same model) and between seeds (same method)
    methods = []
    for a, b in (("occlusion", "input_x_gradient"), ("occlusion", "integrated_gradients"), ("input_x_gradient", "integrated_gradients")):
        methods.append(agreement_row({"first": a, "second": b}, articles, weight, counts, confidence,
                                     rank_agreement(articles, critiques, critiques, a, b)))
    pd.DataFrame(methods).to_csv(tables_dir / "explainability_methods.csv", index=False)
    seeds = []
    for seed in settings["stability"]["seeds"]:
        if not (directory / f"seed{seed}").exists() and args.partial:
            continue
        other_articles, other_critiques, _ = load(directory / f"seed{seed}")
        values = rank_agreement(articles, critiques, other_critiques, "occlusion", "occlusion")
        row = agreement_row({"first_seed": settings["seed"], "second_seed": seed}, articles, weight, counts, confidence, values)
        both = articles.merge(other_articles[["forum_id", "probability"]], on="forum_id", suffixes=("", "_other"))
        row["articles_explained_by_both"] = len(both)
        row["share_same_predicted_outcome"] = float(((both["probability"] >= 0.5) == (both["probability_other"] >= 0.5)).mean())
        seeds.append(row)
    pd.DataFrame(seeds).to_csv(tables_dir / "explainability_seeds.csv", index=False)

    # ---- case studies (the text of the critiques is read here only)
    cases = choose_cases(articles)
    text = pd.read_parquet(cfg["paths"]["llm"] / cfg["kg"]["run"] / "critiques.parquet", columns=["critique_id", "text"])
    case_rows = []
    for case in cases.to_dict("records"):
        own = critiques[critiques["forum_id"] == case["forum_id"]].merge(text, on="critique_id", how="left")
        own["excerpt"] = own["text"].str.replace(r"\s+", " ", regex=True).str.strip().map(
            lambda t: t if len(t) <= EXCERPT else t[:EXCERPT - 1].rstrip() + "…")
        own = own.sort_values("occlusion", key=lambda v: -v.abs()).reset_index(drop=True)
        case_figure(pd.Series(case), own, figures_dir / f"explain_case_{case['case']}.pdf")
        for rank, row in enumerate(own.itertuples(), start=1):
            case_rows.append({**case, "rank": rank, "critique_id": row.critique_id, "occlusion": row.occlusion,
                              "input_x_gradient": row.input_x_gradient, "aspect": row.aspect, "severity": row.severity,
                              "polarity": row.polarity, "target": row.target, "actionable": row.actionable, "excerpt": row.excerpt})
    pd.DataFrame(case_rows).to_csv(tables_dir / "explainability_cases.csv", index=False)

    runs = articles[["forum_id", "group", "label", "borderline", "probability", "stored_probability", "n_nodes", "n_edges_first_layer",
                     "n_reviews", "n_critiques", "seconds"]].copy()
    runs["gap_with_stored_probability"] = (runs["probability"] - runs["stored_probability"]).abs()
    runs.to_csv(tables_dir / "explainability_runs.csv", index=False)

    heat_map(importance, figures_dir / "explain_aspect_severity.pdf")
    relation_figure(relations, figures_dir / "explain_relations.pdf")
    fidelity_figure(fidelity_rows, figures_dir / "explain_fidelity.pdf")

    pd.set_option("display.width", 250)
    shown = importance[(importance["method"] == "occlusion") & (importance["group"] == "all") & importance["kind"].isin(["polarity", "negative_severity"])]
    log.info("importance of one critique, all papers\n%s", shown.drop(columns=["group", "method"]).round(4).to_string(index=False))
    log.info("relations and references\n%s", relations[relations["group"].isin(["all", "borderline"])].round(3).to_string(index=False))
    log.info("fidelity\n%s", fidelity_rows[fidelity_rows["group"] == "all"].round(4).to_string(index=False))
    log.info("methods\n%s\nseeds\n%s", pd.DataFrame(methods).round(3).to_string(index=False), pd.DataFrame(seeds).round(3).to_string(index=False))
    log.info("cases\n%s", cases.round(3).to_string(index=False))
    log.info("largest gap with a stored probability: %.2e; explanation time: %.1f h in total", runs["gap_with_stored_probability"].max(),
             runs["seconds"].sum() / 3600)
    return 0


if __name__ == "__main__":
    sys.exit(main())
