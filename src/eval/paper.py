"""Tables (LaTeX, booktabs) and figures (PDF) of the paper, built from the result tables.

Nothing is trained and no metric is computed here: every number is a cell of a CSV file
of results/tables/, read through `Sources` (src/eval/sources.py).
"""

import json
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.eval import latex as L  # noqa: E402
from src.eval import metrics  # noqa: E402
from src.eval.figures import AXIS, INK, MIDPOINT, MUTED, NEUTRAL, POSITIVE, bar, clean, save, style  # noqa: E402
from src.eval.sources import Sources  # noqa: E402

SUBSETS = {"all": "All papers", "borderline": "Borderline papers"}
GROUPS = {"all": "All", "accepted": "Accepted", "rejected": "Rejected", "borderline": "Borderline"}
SEVERITIES = ("minor", "major", "blocking")
SPLITS = {"train": "Training", "val": "Validation", "test": "Test"}
# Names of the ablation variants, shared with scripts/08b_ablation_results.py.
VARIANT_LABELS = {
    "full": "Full graph",
    "no_shares_concept": "No shares_concept edges",
    "no_critique_labels": "No critique labels (text only)",
    "no_critique_text": "No critique text (labels only)",
    "no_critiques": "No critique nodes",
    "no_scores": "No initial scores",
    "no_scores_no_critiques": "No scores, no critiques",
    "with_responses": "With author responses (setting B)",
}
REFERENCES = {"scores": "Initial scores set to the training mean", "critiques": "All critiques of the paper removed"}
SIDES = {"plus": r"Fidelity$^{+}$ (critiques removed)", "minus": r"Fidelity$^{-}$ (critiques kept alone)"}
METHODS = {"occlusion": "Occlusion", "input_x_gradient": r"Input $\times$ gradient"}


def pretty(name: str) -> str:
    return str(name).replace("_", " ").capitalize()


def model_names(cfg: dict) -> dict[tuple[str, str], str]:
    """Name shown for a (model, setting)."""
    names = {(model, setting): name for model, setting, _, name in cfg["consolidate"]["main_models"]}
    reference_setting = cfg["baselines"]["setting"]
    for model, name in cfg["consolidate"]["other_names"].items():
        names.setdefault((model, reference_setting), name)
    return names


def years(cfg: dict) -> list[int]:
    return [*cfg["splits"]["train"], *cfg["splits"]["test"]]


def joined(values: list) -> str:
    return ", ".join(map(str, values))


# ---------------------------------------------------------------------------- tables


def dataset_table(s: Sources, cfg: dict) -> str:
    name = "clean_report_by_year.csv"
    rows_of = [
        ("Submissions", "papers", L.count),
        ("Withdrawn", "withdrawn", L.count),
        ("With a decision", "papers_with_decision", L.count),
        ("Acceptance rate", "acceptance_rate_with_decision", L.percent),
        ("Reviews", "reviews", L.count),
        (r"\quad with initial scores", "reviews_with_initial_scores", L.count),
        (r"\quad modified after release", "share_reviews_modified_after_release", L.percent),
        ("Mean initial rating", "mean_rating_initial", lambda value: L.number(value, 2)),
        ("Median review length (words)", "median_review_words", L.count),
    ]
    rows = [[label, *[form(s.value(name, column, year=year)) for year in years(cfg)]] for label, column, form in rows_of]
    rows.append(None)
    for label, setting, node in (("Critiques", "A", "critique"), ("Author responses", "B", "response")):
        rows.append([label, *[L.count(s.value("kg_statistics.csv", f"count_{year}", setting=setting, kind="node", type=node))
                              for year in years(cfg)]])
    return L.table(["", *[f"ICLR {year}" for year in years(cfg)]], rows, label="tab:dataset",
                   caption="Corpus by year, desk rejections excluded. The acceptance rate is among the papers with a decision. "
                   "The reviews with initial scores are the ones kept in the graph; critiques and author responses are the "
                   "nodes extracted from them.")



def splits_table(s: Sources, cfg: dict) -> str:
    rows = []
    for withdrawn, title in (("excluded", "Papers with a decision"), ("as_reject", "Withdrawn papers counted as rejected")):
        rows.append(title)
        for split, label in SPLITS.items():
            row = s.row("clean_report_splits.csv", withdrawn=withdrawn, split=split)
            rows.append([label, str(int(row["year"])), L.count(row["papers"]), L.percent(row["acceptance_rate"]), L.count(row["reviews"])])
    fraction = cfg["splits"]["validation"]["fraction"]
    return L.table(["Split", "Year", "Papers", "Accepted", "Reviews"], rows, align="llrrr", label="tab:splits",
                   caption=f"Temporal split. The validation papers are {100 * fraction:.0f}\\,\\% of the training year, "
                   "drawn by a hash of the paper identifier. Second block: robustness check.")



def graph_table(s: Sources, cfg: dict) -> str:
    table = s.table("kg_statistics.csv")
    rows = []
    for kind, title in (("node", "Nodes"), ("edge", "Edges (source $\\to$ target)")):
        rows.append(title)
        for element in table.loc[table["kind"] == kind, "type"].drop_duplicates():
            counts = [s.rows("kg_statistics.csv", setting=setting, kind=kind, type=element) for setting in ("A", "B")]
            label = rf"\texttt{{{L.escape(element)}}}"
            if kind == "edge":  # "article -has_review-> review"
                source, relation, target = re.fullmatch(r"(\w+) -(\w+)-> (\w+)", element).groups()
                label = rf"\texttt{{{L.escape(relation)}}} ({source} $\to$ {target})"
            rows.append([label, *[L.count(found["count"].iloc[0]) if len(found) == 1 else L.MISSING for found in counts]])
    return L.table(["", "Setting A", "Setting B"], rows, label="tab:graph",
                   caption=f"Knowledge graph of ICLR {joined(years(cfg))}. Setting A holds what exists before the author "
                   "response; setting B adds the author responses. Inverse relations are not counted.")


def critique_labels_table(s: Sources, cfg: dict) -> str:
    rows = []
    for label in ("aspect", "severity", "polarity"):
        rows.append(pretty(label))
        for _, row in s.table(f"llm_full_v3_{label}.csv").iterrows():
            rows.append([L.escape(pretty(row[label].strip("()"))), L.count(row["critiques"]), L.percent(row["share"])])
    return L.table(["Label", "Critiques", "Share"], rows,
                   caption=f"Labels given by the LLM to the critiques of ICLR {joined(years(cfg))}.", label="tab:critique-labels")


def test_sizes(s: Sources, cfg: dict) -> dict[str, int]:
    return {subset: int(s.value("main_results.csv", "n_papers", model=cfg["consolidate"]["reference"],
                                setting=cfg["baselines"]["setting"], split="test", subset=subset)) for subset in SUBSETS}


def holdout_tag(cfg: dict) -> str:
    return "holdout_" + "_".join(map(str, cfg["splits"]["holdout"]))


def year_results(s: Sources, cfg: dict, holdout: bool) -> dict:
    """Where the results of a year are read: the test year, or the holdout year
    (frozen models, setting of `holdout.setting` only)."""
    if not holdout:
        return {"results": "main_results.csv", "tests": "main_results_tests.csv", "where": {"split": "test"}, "sizes": test_sizes(s, cfg),
                "models": cfg["consolidate"]["main_models"], "years": cfg["splits"]["test"]}
    tag, setting = holdout_tag(cfg), cfg["holdout"]["setting"]
    sizes = {subset: int(s.value(f"{tag}.csv", "n_papers", model=cfg["consolidate"]["reference"], subset=subset)) for subset in SUBSETS}
    return {"results": f"{tag}.csv", "tests": f"{tag}_tests.csv", "where": {"split": "holdout"}, "sizes": sizes,
            "models": [row for row in cfg["consolidate"]["main_models"] if row[1] == setting], "years": cfg["splits"]["holdout"]}


def subset_header(sizes: dict[str, int], span: int, first: int = 2) -> list[str]:
    """Heading over the columns of each subset of papers."""
    cells = [rf"\multicolumn{{{span}}}{{c}}{{{title} ($n = {sizes[subset]:,}$)}}".replace(",", r"\,") for subset, title in SUBSETS.items()]
    rules = [rf"\cmidrule(lr){{{first + i * span}-{first + (i + 1) * span - 1}}}" for i in range(len(SUBSETS))]
    return [" & " * (first - 1) + " & ".join(cells) + r" \\", " ".join(rules)]



def main_table(s: Sources, cfg: dict, holdout: bool = False) -> str:
    settings, year = cfg["consolidate"], year_results(s, cfg, holdout)
    reference = settings["reference"]
    rows, family = [], None
    for model, setting, group, name in year["models"]:
        if group != family:
            rows.append(L.escape(group))
            family = group
        cells = [L.escape(name)]
        for subset in SUBSETS:
            tests = s.row(year["tests"], model=model, setting=setting, subset=subset)
            cells += [L.number(s.value(year["results"], "auc_mean", model=model, setting=setting, subset=subset, **year["where"])),
                      L.signed(tests[f"auc_minus_{reference}"]),
                      L.interval(tests[f"auc_minus_{reference}_ci_low"], tests[f"auc_minus_{reference}_ci_high"], sign=True)]
        rows.append(cells)
    statistics = cfg["gnn"]["statistics"]
    start = (f"Holdout year ({joined(year['years'])}), models frozen after the test year" if holdout
             else f"Test year ({joined(year['years'])})")
    caption = (f"{start}: AUC, mean over {len(cfg['seeds'])} seeds. $\\Delta$: AUC minus the AUC "
               f"of the logistic regression on the initial rating, with its {100 * statistics['confidence']:.0f}\\,\\% confidence "
               f"interval (paired bootstrap over the papers, {L.count(statistics['n_resamples'])} resamples).")
    return L.table(["Model", *["AUC", r"$\Delta$", r"95\,\% CI of $\Delta$"] * len(SUBSETS)], rows, caption=caption,
                   label="tab:holdout" if holdout else "tab:main", wide=True, header=subset_header(year["sizes"], 3))


def holdout_table(s: Sources, cfg: dict) -> str:
    return main_table(s, cfg, holdout=True)


def holdout_readings_table(s: Sources, cfg: dict) -> str:
    """Models against their controls on the holdout year, next to the test year."""
    names, setting, tag = model_names(cfg), cfg["holdout"]["setting"], holdout_tag(cfg)
    years = {"test": joined(cfg["splits"]["test"]), "holdout": joined(cfg["splits"]["holdout"])}
    rows = []
    for subset, title in SUBSETS.items():
        rows.append(title)
        for model, control in cfg["gnn"]["statistics"]["comparisons"]:
            cells = [L.escape(names[(model, setting)]), L.escape(names[(control, setting)])]
            for table, split in (("paired_comparisons.csv", "test"), (f"{tag}_paired.csv", "holdout")):
                row = s.row(table, model=model, control=control, split=split, subset=subset)
                cells += [L.signed(row["difference"], 4), L.interval(row["ci_low"], row["ci_high"], 4, sign=True)]
            rows.append(cells)
    header = [" & & " + " & ".join(rf"\multicolumn{{2}}{{c}}{{ICLR {year}}}" for year in years.values()) + r" \\",
              r"\cmidrule(lr){3-4} \cmidrule(lr){5-6}"]
    return L.table(["Model", "Control", *[r"$\Delta$AUC", r"95\,\% CI"] * 2], rows, align="llrrrr", wide=True, header=header,
                   label="tab:holdout-paired", gap=3, size="footnotesize",
                   caption=f"AUC of a model minus AUC of its control on the test year ({years['test']}) and on the holdout year "
                   f"({years['holdout']}, models frozen after the test year). Paired bootstrap over the papers.")


def paired_table(s: Sources, cfg: dict, pairs: list, caption: str, label: str) -> str:
    """AUC of a model minus AUC of its control: test year (all, borderline), validation."""
    names, setting = model_names(cfg), cfg["baselines"]["setting"]
    blocks = [("test", "all", "Test year, all papers"), ("test", "borderline", "Test year, borderline papers"),
              ("val", "all", "Validation, all papers")]
    rows = []
    for split, subset, title in blocks:
        rows.append(title)
        for model, control in pairs:
            row = s.row("paired_comparisons.csv", model=model, control=control, split=split, subset=subset)
            rows.append([L.escape(names[(model, setting)]), L.escape(names[(control, setting)]), L.number(row["auc_model"], 4),
                         L.number(row["auc_control"], 4), L.signed(row["difference"], 4),
                         L.interval(row["ci_low"], row["ci_high"], 4, sign=True)])
    return L.table(["Model", "Control", "AUC", "Control AUC", r"$\Delta$", r"95\,\% CI of $\Delta$"], rows, caption=caption,
                   label=label, align="llrrrr", wide=True)


def comparison_pairs(cfg: dict) -> tuple[list, list]:
    """Pairs of `gnn.statistics.comparisons`: (same family with and without an input, heterogeneous against homogeneous)."""
    pairs = [tuple(pair) for pair in cfg["gnn"]["statistics"]["comparisons"]]
    heterogeneous = [pair for pair in pairs if pair[0] in cfg["gnn"]["models"]]
    return [pair for pair in pairs if pair not in heterogeneous], heterogeneous


def critique_baselines_table(s: Sources, cfg: dict) -> str:
    return paired_table(s, cfg, comparison_pairs(cfg)[0], label="tab:critique-baselines",
                        caption="Critique counts without the graph: AUC of a model minus AUC of its control, which reads the "
                        "same inputs without the critique counts (first two rows) or the review text instead of them (last row). "
                        "Paired bootstrap over the papers.")


def hetero_vs_gcn_table(s: Sources, cfg: dict) -> str:
    return paired_table(s, cfg, comparison_pairs(cfg)[1], label="tab:hetero-vs-gcn",
                        caption="Heterogeneous GNNs against the homogeneous GCN (setting A, graph alone): AUC difference, "
                        "paired bootstrap over the papers.")


def ablation_variants(cfg: dict) -> list[str]:
    return [*cfg["ablations"]["variants"], *cfg["ablations"]["from_phase7"]]


def ablations_table(s: Sources, cfg: dict) -> str:
    rows = []
    for variant in ablation_variants(cfg):
        cells = [L.escape(VARIANT_LABELS[variant])]
        for subset in SUBSETS:
            row = s.row("ablations.csv", model=variant, split="test", subset=subset)
            cells += [L.number(row["auc_mean"]), L.signed(row["auc_minus_full"]),
                      L.interval(row["auc_minus_full_ci_low"], row["auc_minus_full_ci_high"], sign=True)]
        rows.append(cells)
    sizes = {subset: int(s.value("ablations.csv", "n_papers", model="full", split="test", subset=subset)) for subset in SUBSETS}
    settings = cfg["ablations"]
    return L.table(["Variant", *["AUC", r"$\Delta$", r"95\,\% CI"] * len(SUBSETS)], rows, wide=True, label="tab:ablations-delta",
                   header=subset_header(sizes, 3),
                   caption=f"Ablations of the {settings['model'].upper()} model (setting {settings['setting']}) on the test year "
                   f"({joined(cfg['splits']['test'])}): one element removed at a time, same hyper-parameters, "
                   f"{len(cfg['seeds'])} seeds. $\\Delta$: AUC minus the AUC of the full graph, paired bootstrap over the papers.")


def supported(row, cfg: dict) -> bool:
    """Enough explained papers hold such a critique for its mean importance to be read."""
    return bool(row["n_articles_with_such_a_critique"] >= cfg["consolidate"]["min_articles"])


def importance_cell(row, cfg: dict) -> str:
    """Importance per critique in hundredths of a logit: bold when its confidence
    interval excludes zero, in parentheses when too few papers hold such a critique."""
    cell = L.signed(100 * row["importance_per_critique"], 1)
    if not supported(row, cfg):
        return f"({cell})"
    return L.bold(cell) if row["ci_excludes_zero"] else cell



def explain_aspect_severity_table(s: Sources, cfg: dict) -> str:
    name, groups = "explainability.csv", ("accepted", "rejected", "borderline")
    aspects = s.rows(name, group="all", method="occlusion", kind="negative_aspect_severity")["aspect"].drop_duplicates()
    rows = []
    for aspect in aspects:
        cells = [L.escape(pretty(aspect))]
        for group in groups:
            cells += [importance_cell(s.row(name, group=group, method="occlusion", kind="negative_aspect_severity",
                                            aspect=aspect, severity=severity), cfg) for severity in SEVERITIES]
            cells.append(importance_cell(s.row(name, group=group, method="occlusion", kind="positive_aspect", aspect=aspect), cfg))
        rows.append(cells)
    span = len(SEVERITIES) + 1
    header = [" & " + " & ".join(rf"\multicolumn{{{span}}}{{c}}{{{GROUPS[group]} papers}}" for group in groups) + r" \\",
              " ".join(rf"\cmidrule(lr){{{2 + i * span}-{1 + (i + 1) * span}}}" for i in range(len(groups)))]
    explained = int(s.value("explainability_relations.csv", "n_articles", group="all", kind="reference", removed="scores"))
    return L.table(["Aspect", *[*[f"{severity[:3].capitalize()}." for severity in SEVERITIES], "Pos."] * len(groups)], rows, wide=True,
                   header=header, label="tab:explain-aspect-severity", size="footnotesize", gap=3,
                   caption="Mean importance of one critique for the prediction of its paper, by occlusion, in hundredths of a "
                   "logit (positive: the critique pushes towards acceptance). Negative critiques by aspect and severity (minor, "
                   f"major, blocking) and positive critiques by aspect; {L.count(explained)} explained test papers. Bold: the "
                   f"95\\,\\% confidence interval excludes zero. In parentheses: fewer than {cfg['consolidate']['min_articles']} "
                   "explained papers hold such a critique.")



def explain_relations_table(s: Sources, cfg: dict) -> str:
    """Importance of each relation: all explained papers with the interval, then each
    group (bold when its interval excludes zero)."""
    name = "explainability_relations.csv"
    rows = []
    for kind, title in (("relation", "One relation removed"), ("reference", "Scale of the importances")):
        rows.append(title)
        for removed in s.rows(name, kind=kind, group="all")["removed"]:
            overall = s.row(name, group="all", kind=kind, removed=removed)
            cells = [REFERENCES[removed] if kind == "reference" else rf"\texttt{{{L.escape(removed)}}}",
                     L.signed(overall["importance"], 2), L.interval(overall["ci_low"], overall["ci_high"], 2, sign=True)]
            for group in [group for group in GROUPS if group != "all"]:
                row = s.row(name, group=group, kind=kind, removed=removed)
                cell = L.signed(row["importance"], 2)
                cells.append(L.bold(cell) if row["ci_low"] > 0 or row["ci_high"] < 0 else cell)
            rows.append(cells)
    return L.table(["Removed", "All papers", r"95\,\% CI", *[title for group, title in GROUPS.items() if group != "all"]], rows,
                   wide=True, label="tab:explain-relations",
                   caption="Logit of a paper with an element of its computation graph minus logit without it, mean over the "
                   "explained test papers (positive: the element pushes towards acceptance). Bold: the 95\\,\\% confidence "
                   "interval excludes zero.")


def explain_fidelity_table(s: Sources, cfg: dict) -> str:
    name = "explainability_fidelity.csv"
    rows = []
    for method, label in METHODS.items():
        for k in cfg["explain"]["fidelity_k"]:
            row = s.row(name, group="all", method=method, k=k)
            cells = [label, str(k)]
            for side in ("plus", "minus"):
                cells += [L.number(row[f"fidelity_{side}_top"], 4), L.number(row[f"fidelity_{side}_random"], 4),
                          L.interval(row[f"fidelity_{side}_difference_ci_low"], row[f"fidelity_{side}_difference_ci_high"], 4, sign=True)]
            rows.append(cells)
    header = [" & & " + " & ".join(rf"\multicolumn{{3}}{{c}}{{{title}}}" for title in SIDES.values()) + r" \\",
              r"\cmidrule(lr){3-5} \cmidrule(lr){6-8}"]
    return L.table(["Method", "$k$", *["Top $k$", "Random", r"95\,\% CI, top $-$ random"] * 2], rows, wide=True, header=header,
                   align="lrrrrrrr", label="tab:explain-fidelity",
                   caption="Fidelity of the explanations: mean absolute change of the predicted probability when the $k$ most "
                   "important critiques of a paper are removed (fidelity$^{+}$, higher is better) or kept alone "
                   "(fidelity$^{-}$, lower is better), against $k$ critiques drawn at random.")



def robustness_table(s: Sources, cfg: dict) -> str:
    name, names = "main_results_withdrawn_as_reject.csv", model_names(cfg)
    setting = cfg["gnn"]["robustness"]["setting"]
    models = list(s.rows(name, split="test", subset="all")["model"])
    rows = []
    for model in models:
        cells = [L.escape(names[(model, setting)])]
        for subset in SUBSETS:
            row = s.row(name, model=model, split="test", subset=subset)
            cells.append(rf"${row['auc_mean']:.3f} \pm {row['auc_std']:.3f}$")
        rows.append(cells)
    sizes = [L.count(s.value(name, "n_papers", model=models[0], split="test", subset=subset)) for subset in SUBSETS]
    return L.table(["Model", "All papers", "Borderline"], rows, label="tab:robustness-withdrawn",
                   caption=f"Robustness check on the test year ({joined(cfg['splits']['test'])}): papers withdrawn before a decision "
                   f"counted as rejections ({sizes[0]} papers, {sizes[1]} of them borderline). AUC, mean $\\pm$ standard deviation "
                   f"over {len(cfg['seeds'])} seeds.")


def parameters(text: str) -> str:
    values = json.loads(text)
    return L.escape(", ".join(f"{key} {value}" for key, value in values.items())) if values else L.MISSING


def hyperparameters_table(s: Sources, cfg: dict) -> str:
    names, reference_setting = model_names(cfg), cfg["baselines"]["setting"]
    rows = ["Baselines"]

    def line(table: str, model: str, setting: str, where: dict) -> list[str]:
        chosen = s.rows(table, model=model, stage="final", **where)["params"].unique()
        if len(chosen) != 1:
            raise LookupError(f"{model} ({setting}): {len(chosen)} final configurations in {table}")
        validation = s.value("main_results.csv", "auc_mean", model=model, setting=setting, split="val", subset="all")
        return [L.escape(names[(model, reference_setting)]), setting, parameters(chosen[0]), L.number(validation)]

    for model in cfg["baselines"]["models"]:
        rows.append(line("baselines_selection.csv", model, reference_setting, {}))
    rows.append("Heterogeneous GNNs (the variant with score statistics reuses the configuration of the plain model)")
    for setting in cfg["gnn"]["settings"]:
        for model in cfg["gnn"]["models"]:
            rows.append(line("gnn_selection.csv", model, setting, {"labels": "label", "setting": setting}))
    return L.table(["Model", "Setting", "Configuration chosen on validation", "Val. AUC"], rows, align="lllr", wide=True,
                   label="tab:hyperparameters", size="footnotesize",
                   caption=f"Hyper-parameters chosen on the validation AUC with seed {cfg['gnn']['selection_seed']}, and validation "
                   f"AUC of the chosen configuration (mean over {len(cfg['seeds'])} seeds).")


def main_full_table(s: Sources, cfg: dict) -> str:
    """Every model and every metric on the test year (same rows as results/tables/main_results.tex)."""
    table = s.table("main_results.csv")
    test = table[(table["split"] == "test") & table["subset"].isin(SUBSETS)].copy()
    suffix = cfg["gnn"]["score_variant"]["suffix"]
    names = [*cfg["baselines"]["models"], *[model + end for model in cfg["gnn"]["models"] for end in ("", suffix)]]
    # a GNN is named with its setting; rows: baselines, then the GNNs of setting A, then those of setting B
    test["row"] = [f"{model} ({setting})" if model.removesuffix(suffix) in cfg["gnn"]["models"] else model
                   for model, setting in zip(test["model"], test["setting"])]
    test = test.assign(rank=test["model"].map(names.index)).sort_values(["setting", "rank"], kind="stable")
    test = test.sort_values("subset", kind="stable", key=lambda column: column.map(list(SUBSETS).index))
    return metrics.latex_table(
        test, "row", {}, caption=f"Test year ({joined(cfg['splits']['test'])}): every baseline and every GNN in settings A (before the "
        f"author response) and B (with the author responses), mean $\\pm$ standard deviation over {len(cfg['seeds'])} seeds.",
        label="tab:main-full", group="subset", group_labels=SUBSETS, wide=True, size="footnotesize")


def ablations_full_table(s: Sources, cfg: dict) -> str:
    """Every metric of the ablations on the test year (same rows as results/tables/ablations.tex)."""
    table, settings = s.table("ablations.csv"), cfg["ablations"]
    test = table[(table["split"] == "test") & table["subset"].isin(SUBSETS)]
    test = test.sort_values("subset", kind="stable", key=lambda column: column.map(list(SUBSETS).index))
    return metrics.latex_table(
        test, "model", VARIANT_LABELS, caption=f"Ablations of the {settings['model'].upper()} model in setting {settings['setting']} "
        f"on the test year ({joined(cfg['splits']['test'])}), every metric: mean $\\pm$ standard deviation over "
        f"{len(cfg['seeds'])} seeds.", label="tab:ablations-full", group="subset", group_labels=SUBSETS, wide=True, size="footnotesize")


TABLES = {
    "dataset": (dataset_table, "Corpus by year"),
    "splits": (splits_table, "Temporal split"),
    "graph": (graph_table, "Nodes and edges of the knowledge graph"),
    "critique_labels": (critique_labels_table, "Labels of the critiques"),
    "main": (main_table, "RQ1, RQ4: AUC of the main models with confidence intervals"),
    "hetero_vs_gcn": (hetero_vs_gcn_table, "RQ1 (c): heterogeneous GNNs against the GCN"),
    "critique_baselines": (critique_baselines_table, "Critique counts without the graph"),
    "ablations_delta": (ablations_table, "RQ2: ablations, difference with the full graph"),
    "explain_aspect_severity": (explain_aspect_severity_table, "RQ3: importance of a critique by aspect and severity"),
    "explain_relations": (explain_relations_table, "RQ3: importance of the relations"),
    "explain_fidelity": (explain_fidelity_table, "RQ3: fidelity of the explanations"),
    "robustness_withdrawn": (robustness_table, "Robustness: withdrawn papers counted as rejections"),
    "hyperparameters": (hyperparameters_table, "Chosen hyper-parameters"),
    "main_full": (main_full_table, "Appendix: every model, every metric"),
    "ablations_full": (ablations_full_table, "Appendix: ablations, every metric"),
}


# --------------------------------------------------------------------------- figures

def main_results_figure(s: Sources, cfg: dict, path, holdout: bool = False) -> None:
    """AUC of each model with its confidence interval on the test year (or on the holdout
    year), all papers and borderline papers. A dot plot: the AUC axis does not start at zero."""
    settings, year = cfg["consolidate"], year_results(s, cfg, holdout)
    reference, reference_setting = settings["reference"], cfg["baselines"]["setting"]
    sizes = year["sizes"]
    positions, labels, headings, position, family = [], [], [], 0.0, None
    for model, setting, group, name in year["models"]:
        if group != family:
            position += 0.6 if family is not None else 0.0
            headings.append((position, group))
            position += 1.0
            family = group
        positions.append(position)
        labels.append(name)
        position += 1.0
    style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 0.21 * position + 0.7), sharey=True)
    for ax, (subset, title) in zip(axes, SUBSETS.items()):
        clean(ax)
        ax.set_title(f"{title} (n = {sizes[subset]:,})".replace(",", " "), loc="left", color=INK, fontsize=8.5)
        at_reference = s.value(year["results"], "auc_mean", model=reference, setting=reference_setting, subset=subset, **year["where"])
        ax.axvline(at_reference, color=AXIS, linewidth=0.8, zorder=1)
        highest = 0.0
        for y, (model, setting, group, _) in zip(positions, year["models"]):
            mean = s.value(year["results"], "auc_mean", model=model, setting=setting, subset=subset, **year["where"])
            tests = s.row(year["tests"], model=model, setting=setting, subset=subset)
            ax.plot([tests["auc_ci_low"], tests["auc_ci_high"]], [y, y], color=INK, linewidth=0.8, zorder=2)
            ax.plot([mean], [y], "o", markersize=5, color=NEUTRAL if group == "Baselines" else POSITIVE,
                    markeredgecolor="white", markeredgewidth=0.6, zorder=3)
            ax.annotate(f"{mean:.3f}", (1, y), xycoords=("axes fraction", "data"), ha="right", va="center", color=INK, fontsize=7.5)
            highest = max(highest, tests["auc_ci_high"])
        ax.set_xlim(0.48, highest + 0.2 * (highest - 0.48))  # room for the column of values on the right
        ax.set_ylim(position - 0.4, -0.8)
        ax.set_xlabel(f"AUC on ICLR {joined(year['years'])} (95 % confidence interval)", color=MUTED)
        for y, heading in headings:
            if ax is axes[0]:
                ax.annotate(heading, (0, y), xycoords=("axes fraction", "data"), xytext=(-6, 0), textcoords="offset points",
                            ha="right", va="center", color=INK, fontsize=8, fontweight="bold")
    axes[0].set_yticks(positions, labels, color=INK)
    reference_name = model_names(cfg)[(reference, reference_setting)]
    axes[0].annotate(f"vertical line: {reference_name}", (0, 0), xycoords="figure fraction", xytext=(6, 4), textcoords="offset points",
                     color=MUTED, fontsize=7)
    fig.tight_layout()
    save(fig, path)
    plt.close(fig)


def borderline_zone_figure(s: Sources, cfg: dict, path) -> None:
    """Acceptance rate of the training papers by bin of mean initial rating, and the
    zone of ratings called borderline."""
    table = s.table("borderline_definition.csv")
    limits = cfg["baselines"]["borderline"]
    zone = table[table["in_zone"]]
    low, high = zone["bin_start"].min(), zone["bin_end"].max()
    centre = (table["bin_start"] + table["bin_end"]) / 2
    enough = table["enough_papers"]
    style()
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    clean(ax, "y")
    ax.axvspan(low, high, color=MIDPOINT, zorder=0)
    for level in (limits["low"], limits["high"]):
        ax.axhline(level, color=AXIS, linewidth=0.8, linestyle=(0, (3, 2)), zorder=1)
    ax.plot(centre[enough], table.loc[enough, "acceptance_rate"], "-o", color=POSITIVE, linewidth=1.5, markersize=4,
            markeredgecolor="white", markeredgewidth=0.6, zorder=3)
    ax.plot(centre[~enough], table.loc[~enough, "acceptance_rate"], "o", color=NEUTRAL, markersize=3, zorder=2)
    ax.annotate(f"borderline zone\n[{low:.2f}, {high:.2f})", (high, 0.3), xytext=(5, 0), textcoords="offset points",
                ha="left", va="center", color=INK, fontsize=7.5)
    ax.annotate(f"fewer than {limits['min_papers']} papers", (centre[~enough].min(), 0.0), xytext=(0, 7), textcoords="offset points",
                ha="left", va="bottom", color=MUTED, fontsize=7)
    ax.set_ylim(-0.03, 1.03)
    ax.set_yticks([0, limits["low"], 0.5, limits["high"], 1.0])
    ax.set_xlabel("Mean initial rating of the paper", color=MUTED)
    ax.set_title(f"Acceptance rate of the training papers ({joined(cfg['splits']['train'])})", loc="left", color=INK, fontsize=8.5)
    fig.tight_layout()
    save(fig, path)
    plt.close(fig)


def critique_labels_figure(s: Sources, cfg: dict, path) -> None:
    """Share of the critiques by aspect, severity and polarity: three panels, one scale."""
    tables = {label: s.table(f"llm_full_v3_{label}.csv") for label in ("aspect", "severity", "polarity")}
    tables = {label: table[~table[label].str.startswith("(")] for label, table in tables.items()}  # the row of missing labels
    style()
    fig, axes = plt.subplots(len(tables), 1, figsize=(3.5, 0.2 * sum(map(len, tables.values())) + 1.3), sharex=True,
                             gridspec_kw={"height_ratios": [len(table) + 0.6 for table in tables.values()]})
    highest = max(table["share"].max() for table in tables.values())
    for ax, (label, table) in zip(axes, tables.items()):
        clean(ax)
        ax.set_xlim(0, highest * 1.2)
        ax.set_ylim(len(table) - 0.5, -0.5)
        ax.set_title(pretty(label), loc="left", color=INK, fontsize=8.5)
    fig.tight_layout()
    fig.canvas.draw()  # the bars are shaped in pixels: the axes must have their final size
    for ax, (label, table) in zip(axes, tables.items()):
        for position, (_, row) in enumerate(table.iterrows()):
            bar(ax, position, row["share"], 0.6, POSITIVE)
            ax.annotate(f"{100 * row['share']:.1f} %", (row["share"], position), xytext=(4, 0), textcoords="offset points",
                        va="center", color=INK, fontsize=7.5)
        ax.set_yticks(range(len(table)), [pretty(value) for value in table[label]], color=INK)
        ax.xaxis.set_major_formatter(lambda value, _: f"{100 * value:.0f} %")
    axes[-1].set_xlabel("Share of the critiques", color=MUTED)
    fig.tight_layout()
    save(fig, path)
    plt.close(fig)


def holdout_results_figure(s: Sources, cfg: dict, path) -> None:
    main_results_figure(s, cfg, path, holdout=True)


FIGURES = {
    "main_results": (main_results_figure, "RQ1, RQ4: test AUC of the main models with confidence intervals"),
    "borderline_zone": (borderline_zone_figure, "Definition of the borderline zone on the training papers"),
    "critique_labels": (critique_labels_figure, "Labels of the critiques"),
}

# Written only once the frozen models have been run on the holdout year.
HOLDOUT_TABLES = {
    "holdout": (holdout_table, "Holdout year: AUC of the frozen models"),
    "holdout_paired": (holdout_readings_table, "Holdout year: models against their controls, next to the test year"),
}
HOLDOUT_FIGURES = {
    "holdout_results": (holdout_results_figure, "Holdout year: AUC of the frozen models with confidence intervals"),
}
