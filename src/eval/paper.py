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


def full_name(model: str, setting: str, cfg: dict) -> str:
    """Name of any model of the study: a baseline, a GNN with or without score statistics in either setting, or the mean rating."""
    names, reference_setting = model_names(cfg), cfg["baselines"]["setting"]
    if (model, setting) in names:
        return names[(model, setting)]
    if model == cfg["sensitivity"]["mean_rating"]["name"]:
        return "Mean initial rating, not fitted"
    suffix = cfg["gnn"]["score_variant"]["suffix"]
    name = names[(model.removesuffix(suffix), reference_setting)] + (" + score statistics" if model.endswith(suffix) else "")
    return name if setting == reference_setting else f"{name}, with author responses"


# Abbreviations used in the tables, spelled out in their captions.
ABBREVIATIONS = {"LR": "logistic regression", "MLP": "multilayer perceptron", "GBT": "gradient-boosted trees",
                 "CI": "confidence interval", "MCC": "Matthews correlation coefficient", "ECE": "expected calibration error"}
# Mark of an analysis designed after the first results of the test year (Table of the status of the analyses).
POST_HOC = r"$^{\dagger}$"
STATUS = r"(Table~\ref{tab:analysis-status})"
POST_HOC_NOTE = rf" {POST_HOC}Designed after the first results of the test year {STATUS}."
# Sensitivity analyses: nothing trained, added once the holdout year had been read as well.
POST_HOC_BOTH_NOTE = rf" {POST_HOC}Designed after the test and holdout years were read {STATUS}."
POST_HOC_ROWS_NOTE = rf" {POST_HOC}Model added after the first results of the test year {STATUS}."
# Mark of a protocol check: models trained after the test and holdout years were read, design fixed before the run.
PROTOCOL = r"$^{\ddagger}$"
PROTOCOL_NOTE = (rf" {PROTOCOL}Protocol check added after the test and holdout years were read; its design was fixed "
                 rf"before it was run {STATUS}.")


def post_hoc_models(cfg: dict) -> set[str]:
    """Models added after the first results of the test year (`consolidate.post_hoc_models`)."""
    return set(cfg["consolidate"]["post_hoc_models"])


def abbreviations(*names: str) -> str:
    return " " + "; ".join(f"{name}: {ABBREVIATIONS[name]}" for name in names) + "."


def years(cfg: dict) -> list[int]:
    return [*cfg["splits"]["train"], *cfg["splits"]["test"]]


def joined(values: list) -> str:
    return ", ".join(map(str, values))


# ---------------------------------------------------------------------------- tables


def dataset_table(s: Sources, cfg: dict) -> str:
    name = "clean_report_by_year.csv"
    rows_of = [
        ("Submissions", "papers", L.count),
        ("Withdrawn before a decision", "withdrawn_before_decision", L.count),   # with the next row, sums to the submissions
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
                   caption="Corpus by year, desk rejections excluded. A paper withdrawn after its decision is counted with the "
                   "papers with a decision. The acceptance rate is among the papers with a decision. "
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
        cells = [L.escape(name) + (POST_HOC if not holdout and model in post_hoc_models(cfg) else "")]
        for subset in SUBSETS:
            tests = s.row(year["tests"], model=model, setting=setting, subset=subset)
            # four decimals: a bound of the interval such as +0.0002 decides whether a difference is significant
            cells += [L.number(s.value(year["results"], "auc_mean", model=model, setting=setting, subset=subset, **year["where"])),
                      L.signed(tests[f"auc_minus_{reference}"], 4),
                      L.interval(tests[f"auc_minus_{reference}_ci_low"], tests[f"auc_minus_{reference}_ci_high"], 4, sign=True)]
        rows.append(cells)
    statistics = cfg["gnn"]["statistics"]
    start = (f"Holdout year ({joined(year['years'])}), models frozen after the test year" if holdout
             else f"Test year ({joined(year['years'])})")
    caption = (f"{start}: AUC, mean over {len(cfg['seeds'])} seeds. $\\Delta$: AUC minus the AUC "
               f"of the logistic regression on the initial rating, with its {100 * statistics['confidence']:.0f}\\,\\% confidence "
               f"interval (paired bootstrap over the papers, {L.count(statistics['n_resamples'])} resamples; the interval does not "
               f"count the variability between seeds). AUC: area under the ROC curve; GNN: graph neural network."
               + abbreviations("LR", "MLP", "CI") + ("" if holdout else POST_HOC_ROWS_NOTE))
    return L.table(["Model", *["AUC", r"$\Delta$", r"95\,\% CI of $\Delta$"] * len(SUBSETS)], rows, caption=caption,
                   label="tab:holdout" if holdout else "tab:main", wide=True, header=subset_header(year["sizes"], 3), size="footnotesize")


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
                   f"({years['holdout']}, models frozen after the test year). Paired bootstrap over the papers."
                   + abbreviations("LR", "MLP", "GBT", "CI"))


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
                        "Paired bootstrap over the papers." + abbreviations("LR", "MLP", "GBT", "CI") + POST_HOC_NOTE)


def hetero_vs_gcn_table(s: Sources, cfg: dict) -> str:
    return paired_table(s, cfg, comparison_pairs(cfg)[1], label="tab:hetero-vs-gcn",
                        caption="Heterogeneous GNNs against the homogeneous GCN (setting A, graph alone): AUC difference, "
                        "paired bootstrap over the papers." + abbreviations("CI")
                        + rf" {POST_HOC}Comparison planned; its paired test was computed after the first results of the test year {STATUS}.")


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
                   f"{len(cfg['seeds'])} seeds. $\\Delta$: AUC minus the AUC of the full graph, paired bootstrap over the papers."
                   + abbreviations("CI") + POST_HOC_NOTE)


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
                   "explained papers hold such a critique. Min., Maj., Blo.: minor, major, blocking; Pos.: positive critiques. "
                   f"The values are those of one trained model (seed {cfg['explain']['seed']}), and the bold marks of the "
                   f"{len(rows) * len(groups) * span} cells are not corrected for multiple comparisons. "
                   "Confidence intervals: bootstrap over the explained papers, stratified by group." + abbreviations("CI") + POST_HOC_NOTE)



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
                   f"interval excludes zero; the marks are not corrected for multiple comparisons. One trained model (seed "
                   f"{cfg['explain']['seed']}). "
                   "Confidence intervals: bootstrap over the explained papers, stratified by group." + abbreviations("CI") + POST_HOC_NOTE)


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
                   "(fidelity$^{-}$, lower is better), against $k$ critiques drawn at random. Occlusion ranks the critiques "
                   "by the change that removing each of them alone produces: its fidelity$^{+}$ at $k = 1$ is the largest such "
                   "change by construction, and only the rows $k > 1$ and fidelity$^{-}$ test it. Confidence intervals: bootstrap "
                   "over the explained papers, stratified by group." + abbreviations("CI") + POST_HOC_NOTE)



def robustness_table(s: Sources, cfg: dict) -> str:
    name, pairs = "main_results_withdrawn_as_reject.csv", "sensitivity_subgroups.csv"
    setting, reference = cfg["gnn"]["robustness"]["setting"], cfg["consolidate"]["reference"]
    models = list(s.rows(name, split="test", subset="all")["model"])
    rows = []
    for model in models:
        cells = [L.escape(full_name(model, setting, cfg))]
        for subset in SUBSETS:
            row = s.row(name, model=model, split="test", subset=subset)
            cells.append(rf"${row['auc_mean']:.3f} \pm {row['auc_std']:.3f}$")
            if model == reference:
                cells += [L.MISSING, L.MISSING]
            else:
                pair = s.row(pairs, analysis="withdrawn_as_reject", model=model, setting=setting, control=reference, subset=subset)
                cells += [L.signed(pair["difference"]), L.interval(pair["ci_low"], pair["ci_high"], sign=True)]
        rows.append(cells)
    sizes = {subset: int(s.value(name, "n_papers", model=models[0], split="test", subset=subset)) for subset in SUBSETS}
    return L.table(["Model", *["AUC", r"$\Delta$" + POST_HOC, r"95\,\% CI of $\Delta$" + POST_HOC] * len(SUBSETS)], rows, label="tab:robustness-withdrawn",
                   wide=True, header=subset_header(sizes, 3),
                   caption=f"Robustness check on the test year ({joined(cfg['splits']['test'])}): papers withdrawn before a decision "
                   f"counted as rejections. AUC, mean $\\pm$ standard deviation over {len(cfg['seeds'])} seeds. $\\Delta$: AUC minus "
                   "the AUC of the logistic regression on the initial rating, paired bootstrap over the papers."
                   + abbreviations("LR", "CI") + rf" {POST_HOC}Computed after the test and holdout years were read, with the "
                   rf"sensitivity analyses {STATUS}.")


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
        tried = s.rows(table, model=model, stage="selection", **where)["params"].nunique()
        validation = s.value("main_results.csv", "auc_mean", model=model, setting=setting, split="val", subset="all")
        return [L.escape(names[(model, reference_setting)]), setting, str(tried) if tried else L.MISSING, parameters(chosen[0]),
                L.number(validation)]

    for model in cfg["baselines"]["models"]:
        rows.append(line("baselines_selection.csv", model, reference_setting, {}))
    rows.append("Heterogeneous GNNs (the variant with score statistics reuses the configuration of the plain model)")
    for setting in cfg["gnn"]["settings"]:
        for model in cfg["gnn"]["models"]:
            rows.append(line("gnn_selection.csv", model, setting, {"labels": "label", "setting": setting}))
    return L.table(["Model", "Set.", "Tried", "Configuration chosen on validation", "Val. AUC"], rows, align="llrlr", wide=True,
                   label="tab:hyperparameters", size="footnotesize", gap=3,
                   caption=f"Hyper-parameters chosen on the validation AUC with seed {cfg['gnn']['selection_seed']}, and validation "
                   f"AUC of the chosen configuration (mean over {len(cfg['seeds'])} seeds). Set.: setting. Tried: number of configurations of the "
                   "grid; a model without hyper-parameter has none. The weight decay is searched for the MLPs and the GCN and "
                   f"fixed at {cfg['gnn']['training']['weight_decay']:g} for the heterogeneous GNNs."
                   + abbreviations("LR", "MLP", "GBT"))


def main_full_table(s: Sources, cfg: dict) -> str:
    """Every model and every metric on the test year (same rows as results/tables/main_results.tex)."""
    table = s.table("main_results.csv")
    test = table[(table["split"] == "test") & table["subset"].isin(SUBSETS)].copy()
    suffix = cfg["gnn"]["score_variant"]["suffix"]
    names = [*cfg["baselines"]["models"], *[model + end for model in cfg["gnn"]["models"] for end in ("", suffix)]]
    # a GNN is named with its setting; rows: baselines, then the GNNs of setting A, then those of setting B
    test["row"] = [f"{full_name(model, 'A', cfg)} ({setting})" if model.removesuffix(suffix) in cfg["gnn"]["models"]
                   else full_name(model, setting, cfg) for model, setting in zip(test["model"], test["setting"])]
    test["row"] = [name + (POST_HOC if model in post_hoc_models(cfg) else "") for name, model in zip(test["row"], test["model"])]
    test = test.assign(rank=test["model"].map(names.index)).sort_values(["setting", "rank"], kind="stable")
    test = test.sort_values("subset", kind="stable", key=lambda column: column.map(list(SUBSETS).index))
    return metrics.latex_table(
        test, "row", {}, caption=f"Test year ({joined(cfg['splits']['test'])}): every baseline and every GNN in settings A (before the "
        f"author response) and B (with the author responses), mean $\\pm$ standard deviation over {len(cfg['seeds'])} seeds. "
        "The setting of a GNN is given in parentheses." + abbreviations("LR", "MLP", "GBT", "MCC", "ECE") + POST_HOC_ROWS_NOTE,
        label="tab:main-full", group="subset", group_labels=SUBSETS, wide=True, size="footnotesize")


def ablations_full_table(s: Sources, cfg: dict) -> str:
    """Every metric of the ablations on the test year (same rows as results/tables/ablations.tex)."""
    table, settings = s.table("ablations.csv"), cfg["ablations"]
    test = table[(table["split"] == "test") & table["subset"].isin(SUBSETS)]
    test = test.sort_values("subset", kind="stable", key=lambda column: column.map(list(SUBSETS).index))
    return metrics.latex_table(
        test, "model", VARIANT_LABELS, caption=f"Ablations of the {settings['model'].upper()} model in setting {settings['setting']} "
        f"on the test year ({joined(cfg['splits']['test'])}), every metric: mean $\\pm$ standard deviation over "
        f"{len(cfg['seeds'])} seeds." + abbreviations("MCC", "ECE") + POST_HOC_NOTE, label="tab:ablations-full", group="subset", group_labels=SUBSETS, wide=True, size="footnotesize")


# ------------------------------------------------- inputs of the models, sensitivity analyses

def input_audit_table(s: Sources, cfg: dict) -> str:
    """Each input of the models: where it comes from, when it was fixed, what remains uncertain."""
    train, test, holdout = cfg["splits"]["train"][0], cfg["splits"]["test"][0], cfg["splits"]["holdout"][0]
    dates = {year: s.row("input_dates.csv", year=year) for year in (train, test, holdout)}
    markers = [L.percent(s.value("kg_post_rebuttal_markers.csv", "share_with_a_marker_left", year=year, modified_after_release=True), 2)
               for year in (train, test)]
    papers = {subset: s.value("baselines.csv", "n_papers", model="majority", split="test", subset=subset) for subset in ("all", "with_text")}
    scope = s.row("kg_concept_scope.csv")
    replies = [int(dates[year]["author_replies_from_first_decision_day"]) for year in (train, test)]
    gaps = {year: abs(int(dates[year]["days_from_first_decision_to_commit"])) for year in dates}
    kg = cfg["kg"]
    # holdout year: current scores and text, after the conference reverted the reviews
    modified_holdout = L.percent(s.value("clean_report_by_year.csv", "share_reviews_modified_after_release", year=holdout))
    marker_holdout = L.percent(s.value("kg_post_rebuttal_markers_holdout.csv", "share_with_a_marker_left", year=holdout,
                                       modified_after_release=True), 2)
    # values of the decision field in the text files committed before the decisions
    statuses = {year: str(dates[year]["archive_decision_values"]).lower() for year in (test, holdout)}
    found = {part.split(":")[0].strip() for text in statuses.values() for part in text.split(";")}
    if not found <= {"withdrawn", "desk rejected"}:  # anything else would be an outcome of the review process
        raise ValueError(f"a text file committed before the decisions holds other values than withdrawals and desk rejections: {found}")
    # weights of the pretrained models against the first review and the first decision of each year
    weights = {role: {year: s.row("pretrained_model_dates.csv", role=role, year=year) for year in (train, test, holdout)}
               for role in ("article encoder, base model", "text encoder", "LLM typing the critiques")}
    llm, encoders = weights["LLM typing the critiques"], [weights["article encoder, base model"], weights["text encoder"]]
    if any(llm[year]["weights_before_first_decision"] for year in (train, test)) or not llm[holdout]["weights_before_first_review"]:
        raise ValueError("the sentence of the audit table on the date of the LLM no longer holds")
    if not all(rows[year]["weights_before_first_review"] for rows in encoders for year in rows):
        raise ValueError("the sentence of the audit table on the dates of the encoders no longer holds")
    rows = [
        ["Initial scores of the reviews",
         r"Archive of the scores recorded when the reviews were released~\cite{kargaran2025insights}",
         "Release of the reviews, before the author response",
         "None identified. A paper is left out when one of its reviews posted before the author response has no initial score. "
         f"{holdout}: no such archive; the current scores are read, after the conference reverted the reviews to their state at the "
         f"start of the discussion, and {modified_holdout} of the reviews of that year were modified after their release."],
        ["Text of the reviews",
         "OpenReview, current text",
         "Final state; the earlier versions cannot be read",
         "Text added after the author response. The LLM sets such sentences aside where it identifies them; an explicit mention of "
         f"the discussion remains in {markers[0]} ({train}), {markers[1]} ({test}) and {marker_holdout} ({holdout}) of the reviews "
         "modified after their release."],
        ["Critiques and their labels",
         rf"\texttt{{{L.escape(cfg['llm']['model'])}}} applied to the text of the reviews",
         "As the text of the reviews",
         f"Inherit the risk of the review text. The training data of the LLM are not known. Its weights are dated "
         f"{llm[train]['weights_dated']}: after the decisions of {train} and {test}, whose public reviews and decisions it may have "
         f"read, and {int(llm[holdout]['days_from_weights_to_first_review'])} days before the first review of {holdout}. It reads "
         "the review alone, never a title, a score or a decision. Labels not validated by humans."],
        ["Title and abstract of the paper",
         r"Archive of the submissions under review~\cite{gonzalez2024iclr}, earliest version of each year",
         f"{train}: committed {gaps[train]} days after the first decision note, no decision in the file. {test}, {holdout}: committed "
         f"{gaps[test]} and {gaps[holdout]} days before it",
         f"{train}: an abstract edited between the decisions and the commit cannot be excluded (inputs of the training year only). "
         f"{L.count(papers['all'] - papers['with_text'])} test papers are absent from the archive and have no text. The decision "
         f"field of the files of {test} and {holdout} only holds withdrawals and desk rejections ({statuses[test]}; "
         f"{statuses[holdout]})."],
        [r"Keyword concepts and \texttt{shares\_concept} edges",
         "Keywords of the same archive",
         "Counted on the training and test years together",
         f"The graph used for training depends on the keywords of the test year: {L.count(scope['concepts_below_min_in_training_years'])} "
         f"of {L.count(scope['concepts'])} concepts would not exist with the training year alone. No label is involved. "
         "None for the holdout year, appended with the vocabulary frozen."],
        ["Embeddings of the texts",
         rf"\texttt{{{L.escape(kg['article_model']['base'].split('/')[-1])}}} with its adapter "
         rf"\texttt{{{L.escape(kg['article_model']['adapter'].split('/')[-1])}}} (papers) and "
         rf"\texttt{{{L.escape(kg['text_model']['name'].split('/')[-1])}}} (other texts), frozen; full identifiers in Section~\ref{{sec:features}}",
         "Pinned revisions of the pretrained models",
         f"Their training data were not audited. Their weights are dated {encoders[0][train]['weights_dated']} (papers) and "
         f"{encoders[1][train]['weights_dated']} (other texts), {int(encoders[0][train]['days_from_weights_to_first_review'])} and "
         f"{int(encoders[1][train]['days_from_weights_to_first_review'])} days before the first review of {train}: they can encode "
         "no review and no decision of the three years, and no citation made after these dates. The base model of SPECTER2 is "
         rf"trained on citation links between papers, according to its model card (\url{{https://huggingface.co/{kg['article_model']['adapter']}}})."],
        ["Author responses (setting B only)",
         "OpenReview, replies of the authors to a review",
         "Discussion period",
         f"None identified: {replies[0]} ({train}) and {replies[1]} ({test}) of these replies were created on or after the day of the "
         "first decision note."],
    ]
    return L.table(["Input", "Source", "Fixed at", "What remains uncertain"], rows, label="tab:input-audit", wide=True, size="footnotesize",
                   align=r">{\raggedright\arraybackslash}p{0.15\linewidth}>{\raggedright\arraybackslash}p{0.21\linewidth}"
                   r">{\raggedright\arraybackslash}p{0.21\linewidth}>{\raggedright\arraybackslash}p{0.35\linewidth}",
                   caption="Inputs of the models in the two settings: source, date at which each input was fixed, and residual risk "
                   "of leakage. The reference baseline reads the first row only. The weights of a pretrained model are dated by the "
                   "last commit that changed its weight files in the pinned revision.")


INPUT_COLUMNS = ["Rating", "Other scores", "Review text", "Critiques", "Paper text", "Keywords", "Graph", "Responses"]
BLOCK_CELLS = {"rating": (0, "S"), "other_scores": (1, "S"), "review_text": (2, "M"), "article_text": (4, "E"),
               "critique_marginals": (3, "C"), "critique_aspect_severity": (3, "C"), "critique_worst_review": (3, "C")}


def model_inputs_table(s: Sources, cfg: dict) -> str:
    """What each model reads, from the feature blocks of the configuration."""
    reference_setting, suffix = cfg["baselines"]["setting"], cfg["gnn"]["score_variant"]["suffix"]
    nodes = ["N", "N", "N", "N", "E", "N"]   # every node feature of the graph of setting A
    rows = ["Baselines without the graph"]
    for model, spec in cfg["baselines"]["models"].items():
        if spec["kind"] == "gcn":
            continue
        cells = [L.MISSING] * len(INPUT_COLUMNS)
        for block in spec.get("features") or []:
            column, mark = BLOCK_CELLS[block]
            cells[column] = mark
        rows.append([L.escape(full_name(model, reference_setting, cfg)), *cells])
    rows.append("Graph models")
    rows.append([L.escape(full_name("gcn", reference_setting, cfg)), *nodes, "untyped", L.MISSING])
    architectures = ", ".join(full_name(model, reference_setting, cfg) for model in cfg["gnn"]["models"])
    with_scores = ["N + S" if INPUT_COLUMNS[position] in ("Rating", "Other scores") else mark for position, mark in enumerate(nodes)]
    rows.append([f"{architectures} (setting A)", *nodes, "typed", L.MISSING])
    rows.append([rf"\quad with score statistics ({L.escape(suffix)})", *with_scores, "typed", L.MISSING])
    rows.append([f"{architectures} (setting B)", *nodes, "typed", "N"])
    rows.append([r"\quad with score statistics", *with_scores, "typed", "N"])
    return L.table(["Model", *INPUT_COLUMNS], rows, label="tab:model-inputs", wide=True, size="footnotesize", align="l" + "c" * len(INPUT_COLUMNS), gap=2,
                   caption="Information read by each model. S: statistics per paper (mean, minimum, maximum, standard deviation; "
                   "number of reviews with the other scores); M: mean embedding of the reviews of the paper; C: counts of the labels "
                   "of the critiques per paper; E: embedding of the title and abstract; N: feature of a node of the graph (the scores "
                   "and the text of each review, the text and the labels of each critique, the keyword concepts). No baseline reads "
                   "the keywords, and no graph model without the score statistics receives the scores aggregated per paper."
                   + abbreviations("LR", "MLP", "GBT"))


def pair_cells(row) -> list[str]:
    return [L.number(row["auc_model"], 4), L.number(row["auc_control"], 4), L.signed(row["difference"], 4),
            L.interval(row["ci_low"], row["ci_high"], 4, sign=True)]


def sensitivity_pairs_table(s: Sources, cfg: dict) -> str:
    """Pairs of models that the first version of the analysis mentioned without a test."""
    name, family = "sensitivity_pairs.csv", "pairs_added_afterwards"
    rows = []
    for subset, title in SUBSETS.items():
        rows.append(f"Test year, {title.lower()}")
        for (model, setting), (control, control_setting) in cfg["sensitivity"]["pairs"]:
            row = s.row(name, model=model, setting=setting, control=control, control_setting=control_setting, subset=subset)
            adjusted = s.value("tests_holm.csv", "delong_p_holm", family=family, model=model, setting=setting, control=control, subset=subset)
            rows.append([L.escape(full_name(model, setting, cfg)), L.escape(full_name(control, control_setting, cfg)), *pair_cells(row),
                         "$<0.001$" if adjusted < 0.001 else L.number(adjusted)])
    return L.table(["Model", "Control", "AUC", "Control AUC", r"$\Delta$", r"95\,\% CI of $\Delta$", "Holm $p$"], rows, wide=True,
                   label="tab:sensitivity-pairs", align="llrrrrr", size="footnotesize",
                   caption="Pairs of models compared afterwards on the test year: AUC of a model minus AUC of its control, paired "
                   "bootstrap over the papers, and $p$-value of the DeLong test after the Holm correction within this table. The mean "
                   "initial rating is used as a score, without any fitting." + abbreviations("LR", "MLP", "CI") + POST_HOC_BOTH_NOTE)


def against_reference_rows(s: Sources, cfg: dict, name: str, where: dict) -> list[list[str]]:
    reference = cfg["sensitivity"]["reference"]
    return [[L.escape(full_name(model, setting, cfg)),
             *pair_cells(s.row(name, model=model, setting=setting, control=reference, **where))] for model, setting in cfg["sensitivity"]["models"]]


def sensitivity_subgroups_table(s: Sources, cfg: dict) -> str:
    """Models against the reference on the test papers whose text from before the decisions is available."""
    name = "sensitivity_subgroups.csv"
    titles = {"with_text": "Test papers with text", "borderline_with_text": "Borderline test papers with text"}
    rows = []
    for subset in cfg["sensitivity"]["subgroups"]:
        where = {"analysis": "papers_with_text", "subset": subset}
        size = int(s.rows(name, **where)["n_papers"].iloc[0])
        rows.append(f"{titles[subset]} ($n = {L.count(size)[1:-1]}$)")
        rows += against_reference_rows(s, cfg, name, where)
    return L.table(["Model", "AUC", "Reference AUC", r"$\Delta$", r"95\,\% CI of $\Delta$"], rows, wide=True,
                   label="tab:sensitivity-text", align="lrrrr", size="footnotesize",
                   caption="Test papers whose title and abstract from before the decisions are available: AUC of a model minus AUC of "
                   "the logistic regression on the initial rating, paired bootstrap over the papers." + abbreviations("LR", "MLP", "CI")
                   + POST_HOC_BOTH_NOTE)


def sensitivity_zones_table(s: Sources, cfg: dict) -> str:
    """Borderline papers under other definitions of the zone."""
    zones, name = s.table("sensitivity_borderline_zones.csv"), "sensitivity_borderline.csv"
    rows = []
    for _, zone in zones.iterrows():
        definition = (f"{'Study' if zone['variant'] == 'study' else 'Variant'}: bins of {zone['bin_width']:g}, $\\geq$ "
                      f"{int(zone['min_papers'])} papers, rate in [{zone['low']:g}, {zone['high']:g}]")
        if zone["status"] != "ok":
            rows.append(f"{definition}; the uncertain bins do not form one interval, not evaluated")
            continue
        rows.append(f"{definition}; zone $[{zone['zone_low']:.2f}, {zone['zone_high']:.2f})$, "
                    f"$n = {L.count(zone['n_test_papers'])[1:-1]}$, {L.percent(zone['acceptance_rate_in_zone'])} accepted")
        rows += against_reference_rows(s, cfg, name, {"variant": zone["variant"]})
    return L.table(["Model", "AUC", "Reference AUC", r"$\Delta$", r"95\,\% CI of $\Delta$"], rows, wide=True,
                   label="tab:sensitivity-zones", align="lrrrr", size="footnotesize",
                   caption="Borderline test papers under other definitions of the zone, each fitted on the training papers only: AUC "
                   "of a model minus AUC of the logistic regression on the initial rating, paired bootstrap over the papers. A "
                   "definition gives the width of the bins of mean initial rating, the minimum number of training papers of a bin and "
                   "the range of acceptance rates in which a bin is uncertain; $n$ is the number of test papers in the zone."
                   + abbreviations("LR", "MLP", "CI") + POST_HOC_BOTH_NOTE)


HOLM_FAMILIES = {
    "main_vs_initial_rating": r"Every model against the initial rating, test year (Tables~\ref{tab:main} and~\ref{tab:main-full})",
    "hetero_vs_gcn": r"Heterogeneous GNNs against the GCN, test year (Table~\ref{tab:hetero-vs-gcn})",
    "critique_counts": r"Critique counts against their controls, test year (Table~\ref{tab:critique-baselines})",
    "ablations": r"Ablations against the full graph (Table~\ref{tab:ablations-delta})",
    "holdout_vs_initial_rating": r"Every model against the initial rating, holdout year (Table~\ref{tab:holdout})",
    "holdout_paired": r"Models against their controls, holdout year (Table~\ref{tab:holdout-paired})",
    "pairs_added_afterwards": r"Pairs compared afterwards (Table~\ref{tab:sensitivity-pairs})",
}


def holm_table(s: Sources, cfg: dict) -> str:
    """Per family of tests: how many DeLong tests reject before and after the Holm correction."""
    table, alpha = s.table("tests_holm.csv"), cfg["sensitivity"]["holm"]["alpha"]
    rows = []
    for family in cfg["sensitivity"]["holm"]["families"]:
        tests = table[table["family"] == family]
        counted = tests[tests["delong_p"].notna()]
        rows.append([HOLM_FAMILIES[family], str(len(counted)), str(int(counted["rejects"].sum())), str(int(counted["rejects_holm"].sum())),
                     str(int(counted["ci_excludes_zero"].sum()))])
    return L.table(["Family of tests", "Tests", f"$p < {alpha:g}$", "After Holm", "CI excludes zero"], rows, wide=True, label="tab:holm",
                   align=r">{\raggedright\arraybackslash}p{0.52\linewidth}rrrr", size="footnotesize",
                   caption="DeLong tests of each table, on all papers and on borderline papers: number of tests, number that reject "
                   f"at {alpha:g} before and after the Holm correction applied within the family, and number of differences whose "
                   "bootstrap confidence interval excludes zero." + abbreviations("CI") + POST_HOC_BOTH_NOTE)


# ------------------------------------------------- protocol checks (scripts/07f, 07g)

PROTOCOL_COMPARISONS, PROTOCOL_READINGS = "protocol_comparisons.csv", "protocol_readings.csv"
PROTOCOL_STAGES = {"vocabulary": "Vocabulary of the training year", "search": "Equal and wider search",
                   "rolling": "Validation on the following year"}
PROTOCOL_SHORT = {"vocabulary": "Vocabulary", "search": "Search", "rolling": "Following year"}  # column headings
ENCODER_LABELS = {"no_article_text": "No embedding of the paper", "no_text_embeddings": "No pretrained embedding at all"}


def has_protocol(s: Sources, cfg: dict) -> bool:
    """The three stages of the protocol checks and the ablations of the encoders have been run and compared."""
    path = s.tables_dir / PROTOCOL_COMPARISONS
    if not path.is_file():
        return False
    done = set(s.table(PROTOCOL_COMPARISONS)["stage"])
    s.take_used()
    return done >= {*cfg["protocol"]["stages"], "encoders"}


def protocol_rows(cfg: dict, stage: str = "search") -> list[str]:
    """Models of a stage in the order of the tables: baselines, GCN, then each heterogeneous GNN followed by its variant with
    the score statistics."""
    suffix, hetero = cfg["gnn"]["score_variant"]["suffix"], cfg["protocol"]["comparisons"]["hetero"]
    return [name + end for name in cfg["protocol"]["stages"][stage]["models"] for end in (("", suffix) if name in hetero else ("",))]


def protocol_stages(cfg: dict, evaluated: str) -> list[str]:
    return [stage for stage in cfg["protocol"]["stages"] if evaluated in cfg["protocol"]["comparisons"][stage]["evaluated"]]


def study_tests(cfg: dict, evaluated: str) -> tuple[str, str]:
    """(results file, tests file) of the study for an evaluated year."""
    return ("main_results.csv", "main_results_tests.csv") if evaluated == "test" else (f"{holdout_tag(cfg)}.csv", f"{holdout_tag(cfg)}_tests.csv")


def study_difference(s: Sources, cfg: dict, evaluated: str, model: str, subset: str) -> list[str]:
    """Difference with the reference in the study: the test year, or the frozen models on the holdout year."""
    reference, setting = cfg["protocol"]["reference"], cfg["protocol"]["setting"]
    row = s.row(study_tests(cfg, evaluated)[1], model=model, setting=setting, subset=subset)
    return [L.signed(row[f"auc_minus_{reference}"], 4),
            L.interval(row[f"auc_minus_{reference}_ci_low"], row[f"auc_minus_{reference}_ci_high"], 4, sign=True)]


def stage_difference(s: Sources, stage: str, evaluated: str, comparison: str, model: str, subset: str) -> list[str]:
    """Difference and interval of one comparison of a check; missing when the model is not part of it."""
    found = s.rows(PROTOCOL_COMPARISONS, stage=stage, evaluated=evaluated, comparison=comparison, model=model, subset=subset)
    if len(found) == 0:
        return [L.MISSING, L.MISSING]
    if len(found) != 1:
        raise LookupError(f"{len(found)} comparisons for {stage}, {evaluated}, {comparison}, {model}, {subset}")
    row = found.iloc[0]
    return [L.signed(row["difference"], 4), L.interval(row["ci_low"], row["ci_high"], 4, sign=True)]


def protocol_table(s: Sources, cfg: dict, evaluated: str) -> str:
    """Every model against the initial rating under each protocol, for one evaluated year."""
    protocol, reference = cfg["protocol"], cfg["protocol"]["reference"]
    stages, year, word = protocol_stages(cfg, evaluated), joined(cfg["splits"][evaluated]), "holdout" if evaluated == "holdout" else "test"
    short = {stage: name.lower() for stage, name in PROTOCOL_SHORT.items()}
    rows = []
    for subset, title in SUBSETS.items():
        size = s.rows(PROTOCOL_COMPARISONS, evaluated=evaluated, subset=subset)["n_papers"].unique()
        if len(size) != 1:
            raise LookupError(f"the checks of the {evaluated} year are not computed on the same papers")
        aucs = [f"{s.value(study_tests(cfg, evaluated)[0], 'auc_mean', model=reference, setting=protocol['setting'], subset=subset, split=evaluated):.4f} (study)"]
        for stage in stages:
            controls = s.rows(PROTOCOL_COMPARISONS, stage=stage, evaluated=evaluated, comparison="vs_reference", subset=subset)["auc_control"].unique()
            if len(controls) != 1:
                raise LookupError(f"{len(controls)} references for stage {stage}")
            aucs.append(f"{controls[0]:.4f} ({short[stage]})")
        rows.append(f"{title} ($n = {L.count(size[0])[1:-1]}$); AUC of the reference: {', '.join(aucs)}")
        for model in protocol_rows(cfg):
            if model == reference:
                continue
            cells = [L.escape(full_name(model, protocol["setting"], cfg)), *study_difference(s, cfg, evaluated, model, subset)]
            for stage in stages:
                cells += stage_difference(s, stage, evaluated, "vs_reference", model, subset)
            rows.append(cells)
    titles = ["Study, frozen" if evaluated == "holdout" else "Study", *[PROTOCOL_SHORT[stage] for stage in stages]]
    header = [" & " + " & ".join(rf"\multicolumn{{2}}{{c}}{{{title}}}" for title in titles) + r" \\",
              " ".join(rf"\cmidrule(lr){{{2 + 2 * i}-{3 + 2 * i}}}" for i in range(len(titles)))]
    explained = {
        "vocabulary": "Vocabulary: the graph models with the configurations of the study, on the graph whose concepts are counted on "
                      "the training year; the baselines read no keyword and are not run again (--).",
        "search": f"Search: the models searched again in a wider space, {protocol['budget']} configurations for each family trained by "
                  "epochs, on the graph of the study; a variant with score statistics reuses the configuration kept for its plain model"
                  + ("; the models kept are applied, frozen, to the holdout year." if evaluated == "holdout" else "."),
        "rolling": "Following year: trained on the training year, selected and stopped on the whole test year, on the graph of the "
                   "vocabulary check, with the same search.",
    }
    own = [stage for stage in stages if protocol["comparisons"][stage]["vs_reference"] == "stage"]
    caption = (f"Protocol checks on the {word} year ({year}): AUC of a model minus AUC of the logistic regression on the initial rating, "
               f"mean over {len(cfg['seeds'])} seeds, with its 95\\,\\% confidence interval (paired bootstrap over the papers; the interval "
               f"does not count the variability between seeds). Study: the models of Table~\\ref{{tab:{'holdout' if evaluated == 'holdout' else 'main'}}}. "
               + " ".join(explained[stage] for stage in stages) + " The reference is the one of the study, except in the column groups "
               + " and ".join(f"``{PROTOCOL_SHORT[stage]}''" for stage in own) + ", where it is searched and trained again like the other models."
               + abbreviations("LR", "MLP", "GBT", "CI") + PROTOCOL_NOTE)
    return L.table(["Model", *[r"$\Delta$", r"95\,\% CI"] * len(titles)], rows, wide=True, header=header, size="footnotesize", gap=1.2,
                   label=f"tab:protocol-{evaluated}", caption=caption)


def protocol_test_table(s: Sources, cfg: dict) -> str:
    return protocol_table(s, cfg, "test")


def protocol_holdout_table(s: Sources, cfg: dict) -> str:
    return protocol_table(s, cfg, "holdout")


def protocol_readings_table(s: Sources, cfg: dict) -> str:
    """Conclusions (a) and (b) of the article in each check, with the rule fixed before the runs."""
    protocol, rows = cfg["protocol"], []
    for stage in protocol["stages"]:
        for evaluated in protocol["comparisons"][stage]["evaluated"]:
            for subset, title in SUBSETS.items():
                a = s.row(PROTOCOL_READINGS, stage=stage, evaluated=evaluated, subset=subset, reading="a")
                b = s.row(PROTOCOL_READINGS, stage=stage, evaluated=evaluated, subset=subset, reading="b")
                rows.append([PROTOCOL_SHORT[stage], joined(cfg["splits"][evaluated]), title.split()[0], a["outcome"],
                             f"{int(a['significantly_below'])} / {int(a['significantly_above'])} of {int(a['variants'])}",
                             L.escape(full_name(a["closest"], protocol["setting"], cfg)) + " " + L.signed(a["closest_difference"], 4) + " "
                             + L.interval(a["closest_ci_low"], a["closest_ci_high"], 4, sign=True), b["outcome"]])
    return L.table(["Check", "Year", "Papers", "(a)", "Below / above", "Closest heterogeneous variant", "(b)"], rows, wide=True,
                   label="tab:protocol-readings", align="lllllll", size="footnotesize", gap=2.5,
                   caption="Conclusions of the article under each protocol check, read with the rule fixed before the runs. (a): no "
                   "heterogeneous GNN is above the logistic regression on the initial rating; confirmed if the confidence interval of "
                   "the difference is below zero for every heterogeneous variant, contradicted if it is above zero for at least one, "
                   "not separated otherwise. Below / above: variants whose interval is below or above zero. (b): HAN and HGT are above "
                   "the GCN, read in the same way. Checks: vocabulary of concepts counted on the training year; equal and wider "
                   "hyper-parameter search; validation on the following year (Section~\\ref{sec:protocol})." + abbreviations("LR", "CI")
                   + PROTOCOL_NOTE)


def protocol_vs_study_table(s: Sources, cfg: dict, evaluated: str) -> str:
    """Each model of a check against the same model of the study."""
    protocol, rows = cfg["protocol"], []
    for stage in protocol_stages(cfg, evaluated):
        rows.append(PROTOCOL_STAGES[stage])
        for model in protocol_rows(cfg, stage):
            found = s.rows(PROTOCOL_COMPARISONS, stage=stage, evaluated=evaluated, comparison="vs_study", model=model, subset="all")
            if len(found) != 1:
                raise LookupError(f"{len(found)} comparisons of {model} with the study in stage {stage}")
            row = found.iloc[0]
            rows.append([L.escape(full_name(model, protocol["setting"], cfg)), L.number(row["auc_model"], 4), L.number(row["auc_control"], 4),
                         L.signed(row["difference"], 4), L.interval(row["ci_low"], row["ci_high"], 4, sign=True),
                         *stage_difference(s, stage, evaluated, "vs_study", model, "borderline")])
    header = [r" & \multicolumn{4}{c}{All papers} & \multicolumn{2}{c}{Borderline papers} \\", r"\cmidrule(lr){2-5} \cmidrule(lr){6-7}"]
    word = "holdout" if evaluated == "holdout" else "test"
    return L.table(["Model", "AUC", "Study AUC", r"$\Delta$", r"95\,\% CI", r"$\Delta$", r"95\,\% CI"], rows, wide=True, header=header,
                   label=f"tab:protocol-vs-study-{evaluated}", size="footnotesize",
                   caption=f"Protocol checks on the {word} year ({joined(cfg['splits'][evaluated])}): AUC of a model of a check minus AUC "
                   "of the same model of the study" + (" (its frozen predictions)" if evaluated == "holdout" else "")
                   + ", paired bootstrap over the papers." + abbreviations("LR", "MLP", "GBT", "CI") + PROTOCOL_NOTE)


def protocol_vs_study_test_table(s: Sources, cfg: dict) -> str:
    return protocol_vs_study_table(s, cfg, "test")


def protocol_vs_study_holdout_table(s: Sources, cfg: dict) -> str:
    return protocol_vs_study_table(s, cfg, "holdout")


def protocol_configurations_table(s: Sources, cfg: dict) -> str:
    """Configurations kept by the two checks that search."""
    protocol, rows = cfg["protocol"], []
    for stage, spec in protocol["stages"].items():
        if not spec["search"]:
            continue
        rows.append(PROTOCOL_STAGES[stage])
        for model in spec["models"]:
            row = s.row(f"protocol_{stage}_chosen.csv", model=model)
            edge = "" if L.is_missing(row["at_edge_of_space"]) else str(row["at_edge_of_space"]).replace("_", " ")
            rows.append([L.escape(full_name(model, protocol["setting"], cfg)),
                         f"{int(row['configurations_tried'])} of {int(row['configurations_in_space'])}", str(int(row["runs_failed"])),
                         parameters(row["params"]), L.escape(edge) if edge else L.MISSING, L.number(row["val_auc_final_mean"])])
    selection = protocol["selection"]
    return L.table(["Model", "Tried", "Failed", "Configuration kept", "At an edge", "Val. AUC"], rows, wide=True, size="footnotesize", gap=3,
                   label="tab:protocol-configurations",
                   align=r"llr>{\raggedright\arraybackslash}p{0.30\linewidth}>{\raggedright\arraybackslash}p{0.13\linewidth}r",
                   caption="Configurations kept by the two protocol checks that search. Tried: configurations drawn in the space of "
                   "the family (Section~\\ref{sec:protocol}); a space smaller than the budget is searched entirely. Failed: training "
                   f"runs of the selection that did not end (GPU memory). The {selection['top']} best configurations with seed "
                   f"{selection['seed']} are trained again with {len(selection['confirm_seeds'])} other seeds, and the best mean validation "
                   "AUC is kept. At an edge: hyper-parameters whose kept value is the smallest or the largest of the space. Val. AUC: "
                   f"mean over {len(cfg['seeds'])} seeds, on the validation papers of the check (a part of the training year, or the whole "
                   "following year)." + abbreviations("LR", "MLP", "GBT") + PROTOCOL_NOTE)


def protocol_encoders_table(s: Sources, cfg: dict) -> str:
    """The main model without the pretrained encoders, against the full graph and against the reference."""
    settings, rows = cfg["ablations"], []
    for subset, title in SUBSETS.items():
        rows.append(title)
        for variant in settings["encoder_variants"]:
            full = s.row(PROTOCOL_COMPARISONS, stage="encoders", comparison="vs_full", model=variant, subset=subset)
            rows.append([ENCODER_LABELS[variant], L.number(full["auc_model"], 4), L.signed(full["difference"], 4),
                         L.interval(full["ci_low"], full["ci_high"], 4, sign=True),
                         *stage_difference(s, "encoders", "test", "vs_reference", variant, subset)])
    header = [r" & & \multicolumn{2}{c}{Against the full graph} & \multicolumn{2}{c}{Against the initial rating (LR)} \\",
              r"\cmidrule(lr){3-4} \cmidrule(lr){5-6}"]
    return L.table(["Variant", "AUC", r"$\Delta$", r"95\,\% CI", r"$\Delta$", r"95\,\% CI"], rows, wide=True, header=header,
                   label="tab:protocol-encoders", size="footnotesize",
                   caption=f"The {settings['model'].upper()} model of the study without the pretrained text encoders, on the test year "
                   f"({joined(cfg['splits']['test'])}): same hyper-parameters, {len(cfg['seeds'])} seeds. First variant: the embedding "
                   "of the title and abstract is removed from the paper node. Second variant: every embedding is removed; a review keeps "
                   "its scores, a critique its labels, and the concept nodes, whose only feature is an embedding, are removed. Paired "
                   "bootstrap over the papers." + abbreviations("LR", "CI") + PROTOCOL_NOTE)


FOLLOWUP_LABELS = {"no_text_embeddings": "NE", "no_text_no_critiques": "NE, no critiques",
                   "no_text_no_shares_concept": r"NE, no \texttt{shares\_concept}"}
FOLLOWUP_CONTROLS = {"scores_rating_lr": "Initial rating (LR)", "scores_all_lr": "All scores (LR)", "scores_critiques_lr": "Scores + critiques (LR)",
                     "scores_all_gbt": "All scores (GBT)", "scores_critiques_gbt": "Scores + critiques (GBT)",
                     "text_scores_mlp": "Text + scores (MLP)", "hgt": "HGT with embeddings"}


def has_followup(s: Sources, cfg: dict) -> bool:
    """The follow-up of the ablations of the encoders has been run and compared."""
    if not (s.tables_dir / PROTOCOL_COMPARISONS).is_file():
        return False
    done = (s.table(PROTOCOL_COMPARISONS)["stage"] == "followup").any()
    s.take_used()
    return bool(done)


def followup_table(s: Sources, cfg: dict) -> str:
    """The graph model without pretrained embeddings on the test year (trained again) and on the holdout year (frozen)."""
    settings, setting = cfg["followup"], cfg["followup"]["setting"]
    main, years = settings["main"], {"test": joined(cfg["splits"]["test"]), "holdout": joined(cfg["splits"]["holdout"])}

    def cells(kind: str, model: str, control: str, subset: str) -> list[str]:
        out = []
        for evaluated in years:
            row = s.row(PROTOCOL_COMPARISONS, stage="followup", evaluated=evaluated, comparison=kind, model=model, control=control, subset=subset)
            out += [L.number(row["auc_model"], 4), L.signed(row["difference"], 4), L.interval(row["ci_low"], row["ci_high"], 4, sign=True)]
        return out

    reference, rows = cfg["protocol"]["reference"], []
    for subset, title in SUBSETS.items():
        rows.append(title)
        for name in settings["variants"]:
            rows.append([FOLLOWUP_LABELS[name], FOLLOWUP_CONTROLS[reference], *cells("vs_reference", name, reference, subset)])
        for other in settings["against"]:
            if other != reference:
                rows.append([FOLLOWUP_LABELS[main], FOLLOWUP_CONTROLS[other], *cells("vs_study_model", main, other, subset)])
        for other in settings["within"]:
            rows.append([FOLLOWUP_LABELS[main], FOLLOWUP_LABELS[other], *cells("within", main, other, subset)])
    header = [" & & " + " & ".join(rf"\multicolumn{{3}}{{c}}{{ICLR {year}{', frozen' if evaluated == 'holdout' else ''}}}"
                                   for evaluated, year in years.items()) + r" \\", r"\cmidrule(lr){3-5} \cmidrule(lr){6-8}"]
    return L.table(["Model", "Control", *["AUC", r"$\Delta$", r"95\,\% CI"] * 2], rows, wide=True, header=header,
                   label="tab:followup", size="footnotesize", gap=1.5, align="llrrrrrr",
                   caption=f"The {settings['model'].upper()} model without pretrained embeddings and two variants of it, on the test year "
                   "(trained again) and on the holdout year (the same models, frozen, on the extended graph with the same elements "
                   "removed): AUC of the model, and AUC of the model minus AUC of its control, paired bootstrap over the papers. NE: "
                   "HGT without any pretrained embedding. The controls are models of the study, read from their stored predictions, "
                   "or another variant; critiques stands for critique counts in the names of the baselines. Same hyper-parameters, "
                   f"{len(cfg['seeds'])} seeds."
                   + abbreviations("LR", "MLP", "GBT", "CI")
                   + rf" {PROTOCOL}Designed after the result of Table~\ref{{tab:protocol-encoders}} was read and before its own runs {STATUS}.")


FOLLOWUP_TABLES = {"followup": (followup_table, "Follow-up: the graph model without pretrained embeddings on the test and holdout years")}


def has_depth_followup(s: Sources, cfg: dict) -> bool:
    """The follow-up of the wider search on the depth and the weight decay has been run and compared."""
    if not (s.tables_dir / PROTOCOL_COMPARISONS).is_file():
        return False
    done = (s.table(PROTOCOL_COMPARISONS)["stage"] == "depth").any()
    s.take_used()
    return bool(done)


def depth_table(s: Sources, cfg: dict) -> str:
    """The configuration kept for one architecture by the wider search, with the depth and the weight decay of the study."""
    settings, reference = cfg["depth_followup"], cfg["protocol"]["reference"]
    origin, model = settings["reference_stage"], settings["model"]
    years = {"test": joined(cfg["splits"]["test"]), "holdout": joined(cfg["splits"]["holdout"])}
    stored = {name: bool(values.get("stored")) for name, values in settings["cells"].items()}
    label = {name: f"{values['layers']} layers, {values['weight_decay']:g}" + (" (kept)" if stored[name] else "")
             for name, values in settings["cells"].items()}
    key = {name: model if stored[name] else f"{model}_{name}" for name in settings["cells"]}

    def cells(stage: str, kind: str, name: str, control: str, subset: str) -> list[str]:
        out = []
        for evaluated in years:
            row = s.row(PROTOCOL_COMPARISONS, stage=stage, evaluated=evaluated, comparison=kind, model=key[name], control=control, subset=subset)
            out += [L.number(row["auc_model"], 4), L.signed(row["difference"], 4), L.interval(row["ci_low"], row["ci_high"], 4, sign=True)]
        return out

    rows = []
    for subset, title in SUBSETS.items():
        rows.append(title)
        for name in settings["cells"]:
            rows.append([label[name], FOLLOWUP_CONTROLS[reference], *cells(origin if stored[name] else "depth", "vs_reference", name, reference, subset)])
        for first, second in settings["within"]:
            rows.append([label[first], label[second], *cells("depth", "within", first, key[second], subset)])
    header = [" & & " + " & ".join(rf"\multicolumn{{3}}{{c}}{{ICLR {year}{', frozen' if evaluated == 'holdout' else ''}}}"
                                   for evaluated, year in years.items()) + r" \\", r"\cmidrule(lr){3-5} \cmidrule(lr){6-8}"]
    base = ", ".join(f"{name.replace('lr', 'learning rate')} {value:g}" for name, value in settings["base"].items())
    return L.table(["Configuration", "Control", *["AUC", r"$\Delta$", r"95\,\% CI"] * 2], rows, wide=True, header=header,
                   label="tab:depth", size="footnotesize", gap=1.5, align="llrrrrrr",
                   caption=f"{model.upper()} in the equal and wider search: depth and weight decay. A configuration "
                   "is named by its number of layers and its weight decay; the first is the one kept by the search, the others give to "
                   f"the depth, to the weight decay or to both the value of the {model.upper()} of the study. "
                   f"Everything else is that of the search ({base}; training settings, graph and validation papers). AUC of the "
                   "configuration, and AUC of the configuration minus AUC of its control, the logistic regression on the initial rating "
                   "of the same check or another configuration: paired bootstrap over the papers. Test year, and the same models, "
                   f"frozen, on the holdout year. {len(cfg['seeds'])} seeds."
                   + abbreviations("LR", "CI")
                   + rf" {PROTOCOL}Designed after the results of the search were read and before its own runs {STATUS}.")


DEPTH_TABLES = {"depth": (depth_table, "Follow-up: depth and weight decay of the model kept by the wider search")}

PROTOCOL_TABLES = {
    "protocol_test": (protocol_test_table, "Protocol checks: every model against the initial rating, test year"),
    "protocol_holdout": (protocol_holdout_table, "Protocol checks: every model against the initial rating, holdout year"),
    "protocol_readings": (protocol_readings_table, "Protocol checks: conclusions (a) and (b) under each check"),
    "protocol_vs_study_test": (protocol_vs_study_test_table, "Protocol checks: each model against the same model of the study, test year"),
    "protocol_vs_study_holdout": (protocol_vs_study_holdout_table, "Protocol checks: each model against the same model of the study, holdout year"),
    "protocol_configurations": (protocol_configurations_table, "Protocol checks: configurations kept by the searches"),
    "protocol_encoders": (protocol_encoders_table, "Protocol checks: the main model without the pretrained encoders"),
}

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
    "input_audit": (input_audit_table, "Inputs of the models: source, date and residual risk"),
    "model_inputs": (model_inputs_table, "Information read by each model"),
    "sensitivity_pairs": (sensitivity_pairs_table, "Sensitivity: pairs of models compared afterwards"),
    "sensitivity_text": (sensitivity_subgroups_table, "Sensitivity: test papers with text"),
    "sensitivity_zones": (sensitivity_zones_table, "Sensitivity: other definitions of the borderline zone"),
    "holm": (holm_table, "Sensitivity: Holm correction of the tests of each table"),
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
        labels.append(name + (r"$^{\dagger}$" if not holdout and model in post_hoc_models(cfg) else ""))
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
