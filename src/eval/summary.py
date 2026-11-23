"""Text of results/RESULTS_SUMMARY.md, written from the result tables.

Every number is read in a CSV file of results/tables/ through `Sources`; the file is
named under each table and after each sentence. A sentence that states a reading
("every GNN is below ...") is guarded by `expect`: if the tables no longer say so, the
summary is not written and the sentence must be revised.
"""

from src.eval.paper import GROUPS, SEVERITIES, SUBSETS, VARIANT_LABELS, ablation_variants, comparison_pairs
from src.eval.sources import Sources, excludes_zero, verdict

MAIN, TESTS, PAIRED = "main_results.csv", "main_results_tests.csv", "paired_comparisons.csv"
ABLATIONS, ABLATIONS_PAIRED, ABLATIONS_RUNS = "ablations.csv", "ablations_paired.csv", "ablations_selection.csv"
EXPLAIN, RELATIONS, FIDELITY = "explainability.csv", "explainability_relations.csv", "explainability_fidelity.csv"
# Result files that do not exist yet: when one appears, its section must be written.
PENDING = {
    "annotation_report.md": "human validation of the LLM labels (phase 4)",
    "explainability_meta_reviews.csv": "comparison of the explanations with the meta-reviews",
}


def holdout_tag(cfg: dict) -> str:
    return "holdout_" + "_".join(map(str, cfg["splits"]["holdout"]))


def has_holdout(s: Sources, cfg: dict) -> bool:
    """The frozen models have been run on the holdout year (scripts/07d_holdout_results.py)."""
    return (s.tables_dir / f"{holdout_tag(cfg)}.csv").is_file()


def expect(condition: bool, statement: str) -> None:
    if not condition:
        raise AssertionError(f"the result tables no longer support this sentence of the summary: {statement}")


def f(value: float, decimals: int = 3) -> str:
    return f"{value:.{decimals}f}"


def d(value: float, decimals: int = 4) -> str:
    return f"{value:+.{decimals}f}"


def ci(low: float, high: float, decimals: int = 4, sign: bool = True) -> str:
    form = f"+.{decimals}f" if sign else f".{decimals}f"
    return f"[{low:{form}}, {high:{form}}]"


def p(value: float) -> str:
    return "p < 0.001" if value < 0.001 else f"p = {value:.3f}"


def n(value: float) -> str:
    return f"{int(value):,}"


def pct(share: float, decimals: int = 1) -> str:
    return f"{100 * share:.{decimals}f} %"


def code(text: str) -> str:
    return f"`{text}`"


def table(columns: list[str], rows: list[list[str]]) -> list[str]:
    return ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns), *["| " + " | ".join(row) + " |" for row in rows], ""]


def source(s: Sources, *names: str) -> str:
    return "Source: " + ", ".join(code(s.path(name)) for name in names) + "."


def is_gnn(model: str, cfg: dict) -> bool:
    return model.removesuffix(cfg["gnn"]["score_variant"]["suffix"]) in cfg["gnn"]["models"]


def difference_cells(row, reference: str) -> list[str]:
    low, high = row[f"auc_minus_{reference}_ci_low"], row[f"auc_minus_{reference}_ci_high"]
    return [d(row[f"auc_minus_{reference}"]), ci(low, high), p(row[f"delong_p_vs_{reference}"]),
            verdict(low, high, row[f"delong_p_vs_{reference}"])]


def auc_table(s: Sources, cfg: dict, subset: str) -> list[str]:
    """Every model on the test year: AUC, interval, difference with the reference baseline."""
    reference, rows = cfg["consolidate"]["reference"], []
    for _, row in s.rows(TESTS, subset=subset).iterrows():
        mean = s.value(MAIN, "auc_mean", model=row["model"], setting=row["setting"], split="test", subset=subset)
        is_reference = row["model"] == reference and row["setting"] == cfg["baselines"]["setting"]
        rows.append([code(row["model"]), row["setting"], f(mean), ci(row["auc_ci_low"], row["auc_ci_high"], 3, sign=False),
                     *(["reference", "", "", ""] if is_reference else difference_cells(row, reference))])
    return table(["Model", "Setting", "AUC", "95 % CI", f"AUC minus {code(reference)}", "95 % CI", "DeLong", "Verdict"], rows)


def paired_rows(s: Sources, name: str, pairs: list, cells: list[tuple[str, str]]) -> list[list[str]]:
    rows = []
    for model, control in pairs:
        for split, subset in cells:
            row = s.row(name, model=model, control=control, split=split, subset=subset)
            rows.append([code(model), code(control), split, subset, f(row["auc_model"], 4), f(row["auc_control"], 4), d(row["difference"]),
                         ci(row["ci_low"], row["ci_high"]), p(row["delong_p"]), verdict(row["ci_low"], row["ci_high"], row["delong_p"])])
    return rows


PAIRED_COLUMNS = ["Model", "Control", "Split", "Papers", "AUC model", "AUC control", "Difference", "95 % CI", "DeLong", "Verdict"]


# --------------------------------------------------------------------------- sections

def protocol(s: Sources, cfg: dict) -> list[str]:
    splits = {split: s.row("clean_report_splits.csv", withdrawn="excluded", split=split) for split in ("train", "val", "test")}
    zone = s.rows("borderline_definition.csv", in_zone=True)
    statistics, limits = cfg["gnn"]["statistics"], cfg["baselines"]["borderline"]
    borderline = int(s.value(MAIN, "n_papers", model=cfg["consolidate"]["reference"], setting="A", split="test", subset="borderline"))
    lines = [
        "## Protocol", "",
        f"- **Data**: ICLR {', '.join(map(str, cfg['splits']['train']))} for training and validation, "
        f"ICLR {', '.join(map(str, cfg['splits']['test']))} for the test. Split by year, never at random.",
        "- **Papers with a decision** (withdrawn papers excluded): "
        + "; ".join(f"{name} {n(row['papers'])} ({pct(row['acceptance_rate'])} accepted)" for name, row in splits.items())
        + f". {source(s, 'clean_report_splits.csv')}",
        f"- **Borderline papers**: mean initial rating in [{zone['bin_start'].min():.2f}, {zone['bin_end'].max():.2f}), the bins "
        f"of the training papers whose acceptance rate lies between {limits['low']} and {limits['high']}; {n(borderline)} test "
        f"papers. {source(s, 'borderline_definition.csv', MAIN)}",
        "- **Setting A**: what exists before the author response (initial scores, review text, critiques). "
        "**Setting B**: setting A plus the author responses.",
        f"- **Runs**: {len(cfg['seeds'])} seeds per model; an AUC is the mean over the seeds.",
        f"- **Intervals and tests**: {100 * statistics['confidence']:.0f} % confidence intervals by bootstrap over the papers "
        f"({n(statistics['n_resamples'])} resamples), paired for a difference between two models; DeLong test on the probability "
        "averaged over the seeds. The intervals count the draw of the papers, not the variability between seeds.",
        "- **Reading rule**: a difference is called *significant* when its confidence interval excludes zero. When the "
        "DeLong test does not reject at 0.05 although the interval excludes zero, the verdict says so: the interval is on the "
        "mean of the AUCs of the seeds, the test on the AUC of the probability averaged over the seeds. "
        "No correction for multiple comparisons is applied.", "",
    ]
    return lines


def status(s: Sources, cfg: dict) -> list[str]:
    existing = [name for name in PENDING if (s.tables_dir / name).exists()]
    expect(not existing, f"{existing} now exist: their sections are to be written")
    sampled = int(s.table("annotation_sample_strata.csv")["sampled"].sum())
    lines = ["## Status", "",
             "Final on ICLR 2024 and 2025: collection, cleaning, critique extraction, graph, baselines, GNNs, ablations, "
             "explanations.", "", "Not available, hence no number below:", "",
             f"- **Human validation of the LLM labels** (phase 4): {sampled} critiques are drawn and the annotation files are "
             f"written; they are not annotated yet. {source(s, 'annotation_sample_strata.csv')}",
             *([] if has_holdout(s, cfg) else
               ["- **ICLR 2026 as a fresh test year**: critique extraction not finished; no model has been run on 2026."]),
             *(["- **Split train 2024 / validation 2025 / test 2026** (models trained again): not done. On ICLR 2026, only the "
                "models frozen after the test year have been run (section *Holdout year*)."] if has_holdout(s, cfg) else []),
             "- **Comparison of the explanations with the meta-reviews**: not done.", ""]
    return lines


def rq1(s: Sources, cfg: dict) -> list[str]:
    reference, base = cfg["consolidate"]["reference"], cfg["baselines"]["setting"]
    tests = s.rows(TESTS, subset="all")
    gnns = tests[[is_gnn(model, cfg) for model in tests["model"]]]
    references = [column.removeprefix("auc_minus_") for column in tests.columns
                  if column.startswith("auc_minus_") and not column.endswith(("_ci_low", "_ci_high"))]
    lines = ["## RQ1 — Does a heterogeneous GNN predict the decision better than the baselines?", "",
             f"Test year, all papers. {source(s, MAIN, TESTS)}", "", *auc_table(s, cfg, "all")]

    # (a) and (b): against the initial scores and against the text models
    for name in references:
        expect((gnns[f"auc_minus_{name}_ci_high"] < 0).all(), f"every heterogeneous GNN is significantly below {name}")
    closest = gnns.loc[gnns[f"auc_minus_{reference}"].idxmax()]
    farthest = gnns.loc[gnns[f"auc_minus_{reference}"].idxmin()]
    text = s.row(TESTS, model="text_mlp", setting=base, subset="all")
    expect(gnns["auc_ci_low"].min() > text["auc_ci_high"], "the interval of every heterogeneous GNN lies above that of text_mlp")
    others = [name for name in references if name != reference]
    baselines = tests[~tests["model"].isin([*gnns["model"], "gcn"]) & (tests["model"] != reference)]
    better = baselines[baselines[f"auc_minus_{reference}_ci_low"] > 0]
    expect(len(better) > 0 and bool((better[f"auc_minus_{reference}"] < 0.005).all()),
           "some baselines are significantly above the reference, by less than 0.005")
    lines += [
        f"- **(a) Against the mean of the initial ratings: no.** All {len(gnns)} heterogeneous GNN models (three architectures, "
        f"with and without score statistics on the article node, settings A and B) are significantly below {code(reference)}. "
        f"The closest is {code(closest['model'])} in setting {closest['setting']}: {d(closest[f'auc_minus_{reference}'])} "
        f"{ci(closest[f'auc_minus_{reference}_ci_low'], closest[f'auc_minus_{reference}_ci_high'])}; the farthest is "
        f"{code(farthest['model'])} in setting {farthest['setting']}: {d(farthest[f'auc_minus_{reference}'])}. ({code(s.path(TESTS))})",
        f"- **What does better than the initial ratings alone.** Only {' and '.join(code(model) for model in better['model'])}, "
        "which add the review text (and the article text) to the scores, are significantly above "
        f"{code(reference)}, by {' and '.join(d(value) for value in better[f'auc_minus_{reference}'])}: a gain of less than "
        "0.005 AUC, on all papers only (see RQ4).",
        f"- **(b) Against the text models: above the text alone, below the text with the scores.** {code('text_mlp')} reaches "
        f"{f(s.value(MAIN, 'auc_mean', model='text_mlp', setting=base, split='test', subset='all'))}; the confidence interval of "
        "every heterogeneous GNN lies above its interval (no paired test was computed for this pair). Every heterogeneous GNN is "
        f"significantly below {' and '.join(code(name) for name in others)} "
        f"(columns {code('auc_minus_*')} of {code(s.path(TESTS))}).",
    ]

    # (c): against the homogeneous GNN
    _, heterogeneous = comparison_pairs(cfg)
    rows = paired_rows(s, PAIRED, heterogeneous, [("test", "all"), ("test", "borderline")])
    above = [model for model, control in heterogeneous
             if s.value(PAIRED, "ci_low", model=model, control=control, split="test", subset="all") > 0]
    below = [model for model, control in heterogeneous
             if s.value(PAIRED, "ci_high", model=model, control=control, split="test", subset="all") < 0]
    expect(sorted(above) == ["han", "hgt"] and below == ["rgcn"], "HAN and HGT are significantly above the GCN, R-GCN significantly below")
    lines += [
        "- **(c) Against a homogeneous GNN: yes for HAN and HGT, no for R-GCN.** In setting A, graph alone, HAN and HGT are "
        "significantly above the GCN trained on the same graph without node and relation types, on all papers and on borderline "
        "papers; R-GCN is significantly below it on all papers.",
        "", f"{source(s, PAIRED)}", "", *table(PAIRED_COLUMNS, rows),
    ]

    # settings A and B, score variant
    rows = []
    for model in cfg["gnn"]["models"]:
        for name in (model, model + cfg["gnn"]["score_variant"]["suffix"]):
            values = [s.value(MAIN, "auc_mean", model=name, setting=setting, split="test", subset="all") for setting in cfg["gnn"]["settings"]]
            rows.append([code(name), *[f(value, 4) for value in values]])
    responses = s.row(ABLATIONS, model="with_responses", split="test", subset="all")
    lines += [
        "**Author responses (setting B) and score statistics on the article node.** No gain is measured from the author "
        "responses: for the main model (HGT), setting B minus setting A is "
        f"{d(responses['auc_minus_full'])} {ci(responses['auc_minus_full_ci_low'], responses['auc_minus_full_ci_high'])}, "
        f"DeLong {p(responses['delong_p_vs_full'])} ({code(s.path(ABLATIONS))}). The other pairs of this table were not tested.",
        "", *table(["Model", *[f"Test AUC, setting {setting}" for setting in cfg["gnn"]["settings"]]], rows), source(s, MAIN), "",
    ]

    # critique counts without the graph
    with_critiques, _ = comparison_pairs(cfg)
    cells = [("test", "all"), ("test", "borderline"), ("val", "all"), ("val", "borderline")]
    lines += ["**Critique counts without the graph.** A model that reads the critique counts is set against its control "
              "of the same family that does not.", "", *table(PAIRED_COLUMNS, paired_rows(s, PAIRED, with_critiques, cells)),
              source(s, PAIRED), ""]
    added = [pair for pair in with_critiques if pair[1] != "text_mlp"]
    for model, control in added:
        for subset in SUBSETS:
            row = s.row(PAIRED, model=model, control=control, split="test", subset=subset)
            expect(not excludes_zero(row["ci_low"], row["ci_high"]), f"{model} is not significantly different from {control} on the test ({subset})")
    alone = s.row(PAIRED, model="critiques_lr", control="text_mlp", split="test", subset="all")
    expect(alone["ci_low"] > 0, "critiques_lr is significantly above text_mlp")
    gains = [s.value(PAIRED, "difference", model=model, control=control, split="val", subset="all") for model, control in added]
    lines += [
        f"- The critique counts alone carry signal: {code('critiques_lr')} is significantly above the review text alone "
        f"({d(alone['difference'])} {ci(alone['ci_low'], alone['ci_high'])}).",
        "- Added to the initial scores, they bring nothing measurable on the test year: no difference is significant, on all "
        "papers or on borderline papers.",
        f"- The gains seen on validation ({', '.join(d(gain) for gain in gains)}) are not found on the test year.", "",
    ]

    # calibration, validation against test, robustness
    rows = []
    for model, setting, _, _ in cfg["consolidate"]["main_models"]:
        validation, test = (s.row(MAIN, model=model, setting=setting, split=split, subset="all") for split in ("val", "test"))
        rows.append([code(model), setting, f(validation["auc_mean"], 4), f(test["auc_mean"], 4), d(test["auc_mean"] - validation["auc_mean"]),
                     f(test["ece_mean"])])
    lines += ["**Validation against test, and calibration.** The GNNs lose more AUC between validation and test than the "
              "score baselines, and are less well calibrated (expected calibration error, ECE).", "",
              *table(["Model", "Setting", "Validation AUC", "Test AUC", "Test minus validation", "Test ECE"], rows), source(s, MAIN), ""]
    name = "main_results_withdrawn_as_reject.csv"
    robust = {model: s.row(name, model=model, split="test", subset="all") for model in ("hgt", reference)}
    expect(robust["hgt"]["auc_mean"] < robust[reference]["auc_mean"], "with withdrawn papers as rejections, HGT stays below the reference")
    lines += [f"**Robustness: withdrawn papers counted as rejections** ({n(robust['hgt']['n_papers'])} test papers). "
              f"{code('hgt')} {f(robust['hgt']['auc_mean'], 4)} against {code(reference)} {f(robust[reference]['auc_mean'], 4)}: "
              f"same order. No interval nor test was computed for this variant. {source(s, name)}", ""]
    return lines


def rq2(s: Sources, cfg: dict) -> list[str]:
    settings = cfg["ablations"]
    variants = ablation_variants(cfg)
    lines = ["## RQ2 — Which nodes and relations contribute to the performance?", "",
             f"Ablations of {code(settings['model'])} in setting {settings['setting']}: one element removed, model trained again "
             f"with the same hyper-parameters and {len(cfg['seeds'])} seeds. An element contributes when removing it lowers the "
             f"test AUC with an interval that excludes zero. {source(s, ABLATIONS)}", ""]
    rows = []
    for variant in variants:
        cells = [VARIANT_LABELS[variant], code(variant)]
        for subset in SUBSETS:
            row = s.row(ABLATIONS, model=variant, split="test", subset=subset)
            cells.append(f"{f(row['auc_mean'], 4)} ± {f(row['auc_std'], 4)}")
            if variant == "full":
                cells += ["reference", "", ""]
            else:
                low, high = row["auc_minus_full_ci_low"], row["auc_minus_full_ci_high"]
                cells += [f"{d(row['auc_minus_full'])} {ci(low, high)}", p(row["delong_p_vs_full"]), verdict(low, high, row["delong_p_vs_full"])]
        rows.append(cells)
    columns = ["Variant", "Name"]
    for title in SUBSETS.values():
        columns += [f"AUC ± std over seeds ({title.lower()})", "Minus full graph, 95 % CI", "DeLong", "Verdict"]
    lines += table(columns, rows)

    at = {variant: s.row(ABLATIONS, model=variant, split="test", subset="all") for variant in variants}
    expect(all(at[variant]["auc_minus_full_ci_high"] < 0 for variant in ("no_scores", "no_critiques", "no_critique_labels", "no_shares_concept")),
           "removing the scores, the critique nodes, the critique labels or shares_concept lowers the AUC significantly")
    expect(not excludes_zero(at["no_critique_text"]["auc_minus_full_ci_low"], at["no_critique_text"]["auc_minus_full_ci_high"]),
           "removing the critique text changes nothing measurable")
    fragile = [variant for variant in variants if variant != "full"
               and excludes_zero(at[variant]["auc_minus_full_ci_low"], at[variant]["auc_minus_full_ci_high"])
               and abs(at[variant]["auc_minus_full"]) < 2 * max(at[variant]["auc_std"], at["full"]["auc_std"])]
    responses = at["with_responses"]
    gcn = s.value(MAIN, "auc_mean", model="gcn", setting=settings["setting"], split="test", subset="all")
    lines += [
        f"- **Initial scores: most of the performance.** Without them the AUC falls to {f(at['no_scores']['auc_mean'], 4)}.",
        f"- **Critique nodes: a clear contribution**, {d(at['no_critiques']['auc_minus_full'])} on all papers and "
        f"{d(s.value(ABLATIONS, 'auc_minus_full', model='no_critiques', split='test', subset='borderline'))} on borderline papers. "
        f"Without them, HGT ({f(at['no_critiques']['auc_mean'], 4)}) is at the level of the GCN ({f(gcn, 4)}, {code(s.path(MAIN))}).",
        f"- **Typed labels of the critiques: a small contribution** ({d(at['no_critique_labels']['auc_minus_full'])}). "
        f"**Text of the critiques: none measured** ({d(at['no_critique_text']['auc_minus_full'])}): with the labels alone the "
        "model does as well as with the text added.",
        f"- **`shares_concept` edges: a small contribution** on all papers ({d(at['no_shares_concept']['auc_minus_full'])}).",
        f"- **Author responses (setting B): no gain.** The AUC changes by {d(responses['auc_minus_full'])}; the interval "
        f"excludes zero but the DeLong test does not reject ({p(responses['delong_p_vs_full'])}).",
        "- **Fragile differences.** The intervals do not count the variability between seeds (standard deviations in the "
        f"table). For {', '.join(code(variant) for variant in fragile)}, the difference is smaller than twice the standard "
        "deviation between seeds of the variant: to be read with caution, although the interval excludes zero.", "",
    ]

    rows = paired_rows(s, ABLATIONS_PAIRED, [tuple(pair) for pair in settings["comparisons"]], [("test", "all"), ("test", "borderline")])
    runs = s.table(ABLATIONS_RUNS)
    without_scores = runs[runs["variant"].isin(["no_scores", "no_scores_no_critiques"])]
    stalled = int((without_scores["best_epoch"] <= 2).sum())
    control = s.row(ABLATIONS_PAIRED, model="full", control="full_phase7", split="test", subset="all")
    expect(all(s.value(ABLATIONS_PAIRED, "ci_high", model=model, control=other, split="test", subset="all") < 0
               for model, other in settings["comparisons"]), "HGT without scores is significantly below the baselines that read no score")
    lines += [
        "**Without the scores, the graph model fails.** It is significantly below a logistic regression on critique counts and "
        "below an MLP on the review text, although it reads the same critiques and the same text.", "",
        *table(PAIRED_COLUMNS, rows), source(s, ABLATIONS_PAIRED), "",
        f"- {stalled} of the {len(without_scores)} trainings without scores stopped early, with their best validation epoch at 1 or 2 "
        f"({code(s.path(ABLATIONS_RUNS))}). Untested hypothesis: a training failure with hyper-parameters chosen for the model "
        "with scores, not a limit of the information held in the graph.",
        f"- Control: the full model trained again in phase 8 against the same model of phase 7, {d(control['difference'])} "
        f"{ci(control['ci_low'], control['ci_high'])}.", "",
    ]
    return lines


def importance(row) -> str:
    return f"{d(row['importance_per_critique'])} {ci(row['ci_low'], row['ci_high'])}"


def rq3(s: Sources, cfg: dict) -> list[str]:
    settings, minimum = cfg["explain"], cfg["consolidate"]["min_articles"]
    runs = s.table("explainability_runs.csv")
    lines = ["## RQ3 — Which critiques explain the predictions?", "",
             f"Explanations of {code(settings['model'])} in setting {settings['setting']}, seed {settings['seed']}, on "
             f"{n(len(runs))} test papers ({settings['sample']['per_group']} per group: accepted or rejected, borderline or not), "
             "weighted back to the test year. The explanations describe the model, not the area chairs. Importance of a critique "
             "by occlusion: logit of its paper with the critique minus logit without it (positive: pushes towards acceptance). "
             f"Largest gap between a recomputed probability and the one stored in phase 7: "
             f"{runs['gap_with_stored_probability'].max():.1e} ({code(s.path('explainability_runs.csv'))}).", ""]

    def cells(kind: str, **where) -> list[str]:
        return [importance(s.row(EXPLAIN, group=group, method="occlusion", kind=kind, **where)) for group in GROUPS]

    rows = [[f"{polarity.capitalize()} critique", *cells("polarity", polarity=polarity)] for polarity in ("positive", "neutral", "negative")]
    rows += [[f"Negative, {severity}", *cells("negative_severity", severity=severity)] for severity in reversed(SEVERITIES)]
    lines += ["**Importance per critique, by polarity and severity** (mean, 95 % CI).", "",
              *table(["", *[f"{title} papers" for title in GROUPS.values()]], rows), source(s, EXPLAIN), ""]
    positive = s.rows(EXPLAIN, method="occlusion", kind="positive_aspect")
    positive = positive[positive["n_articles_with_such_a_critique"] >= minimum]
    expect(bool((positive["ci_low"] > 0).all()), "a positive critique pushes towards acceptance for every aspect and group")

    lines += [f"**Negative critiques by aspect × severity.** A cell is read only when at least {minimum} explained papers hold "
              "such a critique; it *explains* the predictions when its interval excludes zero.", ""]
    rows, strongest = [], {}
    for group in ("accepted", "rejected", "borderline"):
        found = s.rows(EXPLAIN, group=group, method="occlusion", kind="negative_aspect_severity")
        read = found[found["n_articles_with_such_a_critique"] >= minimum]
        explaining = read[read["ci_excludes_zero"]]
        unread = found[found["n_articles_with_such_a_critique"] < minimum]
        rows.append([GROUPS[group], str(len(found)), str(len(read)), str(len(explaining)), str(int((explaining["importance_per_critique"] < 0).sum())),
                     str(int((explaining["importance_per_critique"] > 0).sum())), str(int(unread["ci_excludes_zero"].sum()))])
        if group == "rejected":
            expect(int((explaining["importance_per_critique"] > 0).sum()) >= len(explaining) - 1, "in rejected papers the cells that explain are almost all positive")
        order = explaining.sort_values("importance_per_critique", ascending=group != "rejected")
        strongest[group] = "; ".join(f"{row['aspect']} / {row['severity']} {importance(row)}" for _, row in order.head(3).iterrows())
    lines += table(["Papers", "Cells", f"Read (≥ {minimum} papers)", "Interval excludes zero", "of which negative", "of which positive",
                    "Not read, although their interval excludes zero"], rows)
    lines += [
        "- **What the model keeps of a critique is mostly its polarity**: a positive critique pushes towards acceptance for every "
        "aspect, in every group.",
        f"- **Accepted papers**, strongest cells: {strongest['accepted']}.",
        f"- **Borderline papers**, strongest cells: {strongest['borderline']}.",
        f"- **Rejected papers**: the cells that explain are almost all positive ({strongest['rejected']}). Removing a negative "
        "critique from a rejected paper lowers its prediction further. Untested hypothesis: the model reacts in part to the "
        "number of critiques and not to their content.",
        f"- All cells: {code(s.path(EXPLAIN))}; table {code('results/tables/paper/explain_aspect_severity.tex')}; figure "
        f"{code('results/figures/explain_aspect_severity.pdf')}.", "",
    ]

    rows = []
    for kind in ("relation", "reference"):
        for removed in s.rows(RELATIONS, kind=kind, group="all")["removed"]:
            label = code(removed) if kind == "relation" else {"scores": "initial scores set to the training mean",
                                                              "critiques": "all critiques of the paper removed"}[removed]
            found = [s.row(RELATIONS, group=group, kind=kind, removed=removed) for group in GROUPS]
            rows.append([label, *[f"{d(row['importance'], 2)} {ci(row['ci_low'], row['ci_high'], 2)}" for row in found]])
    lines += ["**Relations and scale of the importances** (logit with the element minus logit without it).", "",
              *table(["Removed", *[f"{title} papers" for title in GROUPS.values()]], rows), source(s, RELATIONS), "",
              "- Removing every critique of a paper moves the prediction more than neutralising its scores, but the two are not "
              "comparable: a review without any critique almost never exists in the graph, so the model is then outside what it "
              "has seen. The clean measure of what the critiques bring is the ablation of RQ2 (model trained again without them).", ""]

    rows = []
    for method in ("occlusion", "input_x_gradient"):
        for k in settings["fidelity_k"]:
            row = s.row(FIDELITY, group="all", method=method, k=k)
            cells_ = [code(method), str(k)]
            for side in ("plus", "minus"):
                low, high = row[f"fidelity_{side}_difference_ci_low"], row[f"fidelity_{side}_difference_ci_high"]
                cells_ += [f(row[f"fidelity_{side}_top"], 4), f(row[f"fidelity_{side}_random"], 4), f"{ci(low, high)}, {verdict(low, high)}"]
            rows.append(cells_)
    occlusion = s.rows(FIDELITY, group="all", method="occlusion")
    gradients = s.rows(FIDELITY, group="all", method="input_x_gradient")
    expect(bool((occlusion["fidelity_plus_difference_ci_low"] > 0).all() and (occlusion["fidelity_minus_difference_ci_high"] < 0).all()),
           "occlusion is more faithful than random critiques on both fidelity measures")
    expect(bool((gradients["fidelity_plus_difference_ci_low"] > 0).all() and (gradients["fidelity_minus_difference_ci_low"] > 0).all()),
           "gradients beat random critiques on fidelity+ and are worse than them on fidelity-")
    lines += ["**Fidelity** (mean absolute change of the probability; all explained papers). Fidelity+ removes the k most "
              "important critiques (higher is better); fidelity− keeps them alone (lower is better); the control draws k critiques "
              "at random.", "",
              *table(["Method", "k", "Fidelity+ top k", "Fidelity+ random", "Difference: 95 % CI, verdict", "Fidelity− top k",
                      "Fidelity− random", "Difference: 95 % CI, verdict"], rows), source(s, FIDELITY), "",
              "- **Occlusion is faithful**: better than random critiques on both measures, for every k.",
              "- **Gradient attributions are only half faithful**: better than random on fidelity+, *worse* than random on "
              "fidelity−.", ""]

    agreement = s.row("explainability_methods.csv", first="occlusion", second="input_x_gradient")
    seeds = s.table("explainability_seeds.csv")
    lines += [
        "**Agreement between methods and between seeds** (Spearman rank correlation of the importances of the critiques of a paper).",
        "",
        f"- Occlusion against input × gradient: {f(agreement['mean_spearman'])} {ci(agreement['ci_low'], agreement['ci_high'], 3, False)}; "
        f"same most important critique in {pct(agreement['share_same_most_important_critique'])} of the papers. "
        f"{source(s, 'explainability_methods.csv')}",
        f"- Seed {settings['seed']} against each other seed ({n(seeds['n_articles'].iloc[0])} papers): from "
        f"{f(seeds['mean_spearman'].min())} to {f(seeds['mean_spearman'].max())}; same most important critique in "
        f"{pct(seeds['share_same_most_important_critique'].min())} to {pct(seeds['share_same_most_important_critique'].max())} of the "
        f"papers, while the two models predict the same outcome for {pct(seeds['share_same_predicted_outcome'].min())} to "
        f"{pct(seeds['share_same_predicted_outcome'].max())} of them. {source(s, 'explainability_seeds.csv')}",
        "- **The ranking of the critiques of a paper is not stable across seeds**: an explanation critique by critique holds for "
        "one trained model, not for the architecture. The means per cell above were computed for one seed only.", "",
    ]
    cases = s.table("explainability_cases.csv").drop_duplicates("case")
    lines += ["**Case studies**: four borderline papers chosen by a rule fixed before the computation (probability closest to "
              "the median of their group).", "",
              *table(["Case", "Paper", "Predicted probability", "Reviews", "Critiques", "Figure"],
                     [[row["case"].replace("_", " "), code(row["forum_id"]), f(row["probability"]), str(int(row["n_reviews"])),
                       str(int(row["n_critiques"])), code(f"results/figures/explain_case_{row['case']}.pdf")] for _, row in cases.iterrows()]),
              source(s, "explainability_cases.csv"), ""]
    return lines


def rq4(s: Sources, cfg: dict) -> list[str]:
    reference, base = cfg["consolidate"]["reference"], cfg["baselines"]["setting"]
    tests = s.rows(TESTS, subset="borderline")
    others = tests[~((tests["model"] == reference) & (tests["setting"] == base))]
    above = others[others[f"auc_minus_{reference}_ci_low"] > 0]
    expect(above.empty, "no model is significantly above the reference on borderline papers")
    level = others[(others[f"auc_minus_{reference}_ci_low"] <= 0) & (others[f"auc_minus_{reference}_ci_high"] >= 0) & (others["model"] != "majority")]
    gnns = tests[[is_gnn(model, cfg) for model in tests["model"]]]
    expect(bool((gnns[f"auc_minus_{reference}_ci_high"] < 0).all()), "every heterogeneous GNN is significantly below the reference on borderline papers")
    best = gnns.loc[gnns[f"auc_minus_{reference}"].idxmax()]
    at_reference = s.value(MAIN, "auc_mean", model=reference, setting=base, split="test", subset="borderline")
    at_all = s.value(MAIN, "auc_mean", model=reference, setting=base, split="test", subset="all")
    critiques = s.row(ABLATIONS, model="no_critiques", split="test", subset="borderline")
    lines = ["## RQ4 — Is the model useful on borderline papers?", "",
             f"Test year, borderline papers. {source(s, MAIN, TESTS)}", "", *auc_table(s, cfg, "borderline"),
             f"- **No.** Borderline papers are hard for every model: {code(reference)} falls from {f(at_all)} on all papers to "
             f"{f(at_reference)} on them. No model is significantly above it.",
             f"- Every heterogeneous GNN is significantly below it; the closest is {code(best['model'])} in setting {best['setting']} "
             f"({d(best[f'auc_minus_{reference}'])} "
             f"{ci(best[f'auc_minus_{reference}_ci_low'], best[f'auc_minus_{reference}_ci_high'])}).",
             f"- Models whose difference with {code(reference)} is not significant: "
             f"{', '.join(code(model) for model in level['model'])}. None of them reads the graph.",
             f"- Inside the graph model, removing the critique nodes costs {d(critiques['auc_minus_full'])} "
             f"{ci(critiques['auc_minus_full_ci_low'], critiques['auc_minus_full_ci_high'])} on borderline papers, against "
             f"{d(s.value(ABLATIONS, 'auc_minus_full', model='no_critiques', split='test', subset='all'))} on all papers "
             f"({code(s.path(ABLATIONS))}); the two were not compared by a test. This does not make the graph model better "
             "than the scores.", ""]
    expect(not any(is_gnn(model, cfg) or model == "gcn" for model in level["model"]), "no graph model is at the level of the reference on borderline papers")
    return lines


def holdout(s: Sources, cfg: dict) -> list[str]:
    """Frozen models on the holdout year. Every sentence follows the tables: what holds
    and what does not is read in the table of readings written by the results script."""
    if not has_holdout(s, cfg):
        return []
    tag, setting, reference = holdout_tag(cfg), cfg["holdout"]["setting"], cfg["consolidate"]["reference"]
    years = ", ".join(map(str, cfg["splits"]["holdout"]))
    name = lambda end: f"{tag}{end}.csv"  # noqa: E731
    checks = s.table(name("_checks"))
    required, others = checks[checks["required"]], checks[~checks["required"]]
    expect(bool(required["passed"].all()), "every required check of the frozen models passed")
    sizes = {subset: int(s.value(name(""), "n_papers", model=reference, subset=subset)) for subset in SUBSETS}
    accepted = int(s.value(name(""), "n_accepted", model=reference, subset="all"))
    by_year = {year: s.row("clean_report_by_year.csv", year=year) for year in cfg["splits"]["holdout"]}
    lines = [
        f"## Holdout year — ICLR {years}, models frozen after the test year", "",
        "ICLR 2025 has been looked at many times; this year had never been used. Nothing was chosen or tuned on it.", "",
        f"- **Heterogeneous GNNs** (setting {setting}): the weights saved in phase 7. On the graph of the study they give back the "
        f"stored probabilities of the test year (largest gap {required.loc[required['kind'] == 'gnn', 'max_gap_on_test_year'].max():.1e}, "
        f"{int((required['kind'] == 'gnn').sum())} models and seeds).",
        "- **Baselines**: fitted again on the training year with the configurations kept in phase 6, without any search. The "
        f"ones without random number give back the stored probabilities of the test year (largest gap "
        f"{required.loc[required['kind'] != 'gnn', 'max_gap_on_test_year'].max():.1e}). The MLPs and the GCN are trained again and "
        f"do not: largest gap {others['max_gap_on_test_year'].max():.3f} on a probability "
        f"({', '.join(code(model) for model in others['model'].unique())}).",
        f"- **Graph**: the articles of {years}, their reviews and their critiques are appended to the graph of the study, which is "
        "unchanged; the concepts are those of 2024–2025 (frozen vocabulary). The holdout articles are predicted on this extended "
        "graph, as the test articles were on the graph of the study.",
        f"- **Papers**: {n(sizes['all'])} with a decision ({pct(accepted / sizes['all'])} accepted), {n(sizes['borderline'])} of them "
        f"borderline (same zone of ratings). {source(s, name(''), name('_checks'))}", "",
        f"**ICLR {years} is not an ordinary year.** After a security incident during the discussion, the conference reverted the "
        "reviews to their state at the start of the discussion and gave every paper to a new area chair (announcement of the "
        "conference). The scores and the text used here are the current ones, taken as initial; "
        + "; ".join(f"{pct(row['share_reviews_modified_after_release'])} of the {year} reviews were modified after their release"
                    for year, row in by_year.items())
        + f" ({code(s.path('clean_report_by_year.csv'))}). The rating scale changed (0, 2, 4, 6, 8, 10): each level was mapped to "
        "the level of the same rank of the earlier scale (1, 3, 5, 6, 8, 10), a rule fixed before any decision of that year was read.", "",
    ]

    if (s.tables_dir / name("_second_run")).is_file():
        second = s.table(name("_second_run"))
        again = second[second["trained_again"]]
        moved = again[again["max_gap_between_runs_on_holdout"] > cfg["holdout"]["max_gap"]]
        expect(bool((second.loc[~second["trained_again"], "max_gap_between_runs_on_holdout"] <= cfg["holdout"]["max_gap"]).all()),
               "the frozen models give the same predictions in a second run")
        without_graph = again[again["test_articles_predicted_on"] == "no graph"]
        lines += [
            "**The models trained again, checked by a second run** (the tables of this section come from the first run). "
            + "; ".join(f"{code(row['model'])}: AUC on the test year {f(row['auc_test_year_second_run'], 4)} trained again, "
                        f"{f(row['auc_test_year_stored'], 4)} stored" for _, row in without_graph.iterrows())
            + ". From one run to the next, "
            + ("every model gives the same predictions." if moved.empty else
               "every model gives the same predictions except "
               + ", ".join(f"{code(row['model'])} (AUC on {years}: {f(row['auc_holdout_first_run'], 4)} then "
                           f"{f(row['auc_holdout_second_run'], 4)})" for _, row in moved.iterrows()) + ".")
            + f" {source(s, name('_second_run'))}", "",
        ]

    for subset, title in SUBSETS.items():
        rows = []
        for _, row in s.rows(name("_tests"), subset=subset).iterrows():
            both = s.row(name("_vs_test_year"), model=row["model"], subset=subset)
            is_reference = row["model"] == reference
            rows.append([code(row["model"]), f(both["auc_test_year"]), f(both["auc_holdout"]),
                         ci(row["auc_ci_low"], row["auc_ci_high"], 3, sign=False),
                         *(["reference", "", "", ""] if is_reference else difference_cells(row, reference))])
        lines += [f"**{title}** ({n(sizes[subset])} papers of {years}).", "",
                  *table(["Model", "AUC, test year", f"AUC, {years}", "95 % CI", f"AUC minus {code(reference)}", "95 % CI", "DeLong", "Verdict"], rows)]
    lines += [source(s, name("_tests"), name("_vs_test_year")), ""]

    rows = paired_rows(s, name("_paired"), [tuple(pair) for pair in cfg["gnn"]["statistics"]["comparisons"]],
                       [("holdout", "all"), ("holdout", "borderline")])
    lines += ["**A model against its control.**", "", *table(PAIRED_COLUMNS, rows), source(s, name("_paired")), ""]

    lines += ["**The three conclusions of the test year, written before this run.** A conclusion holds when the confidence "
              "intervals say so (rule in the protocol).", ""]
    readings = s.table(name("_readings"))
    lines += table(["", "Conclusion of the test year", "Papers", f"On {years}", "Detail"],
                   [[f"({row['reading']})", row["statement"].replace(reference, code(reference)), row["subset"],
                     "**holds**" if row["holds"] else "**does not hold**", row["detail"]] for _, row in readings.iterrows()])
    held = readings[readings["subset"] == "all"].set_index("reading")["holds"]
    lines += [f"- On all papers, {int(held.sum())} of the {len(held)} conclusions hold"
              + ("." if held.all() else f"; not ({', '.join(held.index[~held])})."), source(s, name("_readings")), ""]

    growth = s.table(name("_graph_growth"))
    frozen = growth[~growth["trained_again"]]
    lines += [
        "**What the larger graph changes.** The articles of the test year, predicted again on the extended graph by the same "
        "frozen GNNs: their AUC on the test year changes by "
        f"{d(frozen['auc_difference'].min())} to {d(frozen['auc_difference'].max())}, and "
        f"{pct(frozen['share_of_predicted_outcomes_changed'].min())} to {pct(frozen['share_of_predicted_outcomes_changed'].max())} of "
        "the predicted outcomes change. This measures how much a prediction depends on the size of the graph around it, "
        "without any outcome of the holdout year.", "",
        *table(["Model", "Trained again", "AUC, graph of the study", "AUC, extended graph", "Difference", "Mean change of probability",
                "Predicted outcomes changed"],
               [[code(row["model"]), "yes" if row["trained_again"] else "no", f(row["auc_on_the_graph_of_the_study"], 4),
                 f(row["auc_on_the_extended_graph"], 4), d(row["auc_difference"]), f(row["mean_absolute_change_of_probability"], 4),
                 pct(row["share_of_predicted_outcomes_changed"])] for _, row in growth.iterrows()]),
        source(s, name("_graph_growth")), "",
    ]
    coverage = s.table("kg_concept_coverage_holdout.csv").set_index("year")
    lines += [
        "**Limits of this test.**", "",
        "- An atypical year (see above): a difference with the test year can come from the year as much as from the models.",
        "- The vocabulary of concepts is frozen: "
        + "; ".join(f"{pct(row['share_keywords_in_vocabulary'])} of the keywords of {int(year)} are concepts of the graph" for year, row in coverage.iterrows())
        + f" ({code(s.path('kg_concept_coverage_holdout.csv'))}).",
        "- The baselines trained by epochs (MLPs, GCN) are not the very models of the test year: they are trained again with the "
        "same configuration and seeds.",
        "- Setting A only: the author responses of this year were not extracted.",
        "- The models are not trained again with the test year as validation; that protocol is not run yet.", "",
    ]
    return lines


def holdout_negative_results(s: Sources, cfg: dict) -> list[str]:
    """What the holdout year adds to the list of negative results (nothing before it is run)."""
    if not has_holdout(s, cfg):
        return []
    tag, reference, years = holdout_tag(cfg), cfg["consolidate"]["reference"], ", ".join(map(str, cfg["splits"]["holdout"]))
    full = cfg["consolidate"]["full_model"]
    at = lambda table, model: s.row(table, model=model, subset="all")  # noqa: E731
    now, before = at(f"{tag}_tests.csv", full["model"]), s.row(TESTS, model=full["model"], setting=full["setting"], subset="all")
    added = s.row(f"{tag}_paired.csv", model="scores_critiques_lr", control="scores_all_lr", subset="all")
    text = at(f"{tag}_tests.csv", "text_scores_mlp")
    calibration = s.row(f"{tag}_vs_test_year.csv", model=reference, subset="all")
    growth = s.table(f"{tag}_graph_growth.csv")
    worst = growth.loc[growth.loc[~growth["trained_again"], "auc_difference"].idxmin()]
    lines = [
        f"11. **On the holdout year ({years}) the gap between the graph model and the initial ratings is "
        + ("wider" if now[f"auc_minus_{reference}"] < before[f"auc_minus_{reference}"] else "narrower")
        + f"**: {code(full['model'])} {d(now[f'auc_minus_{reference}'])} "
        f"{ci(now[f'auc_minus_{reference}_ci_low'], now[f'auc_minus_{reference}_ci_high'])}, against "
        f"{d(before[f'auc_minus_{reference}'])} on the test year ({code(s.path(f'{tag}_tests.csv'))}).",
        f"12. **On {years} the critique counts added to the scores "
        + ("lower the AUC" if added["ci_high"] < 0 else "raise the AUC" if added["ci_low"] > 0 else "change nothing measurable")
        + f"**: {d(added['difference'])} {ci(added['ci_low'], added['ci_high'])} for the logistic regression "
        f"({code(s.path(f'{tag}_paired.csv'))}).",
        f"13. **The small gain of the review text over the initial ratings "
        + ("is found again" if text[f"auc_minus_{reference}_ci_low"] > 0 else "is not found again")
        + f" on {years}**: {code('text_scores_mlp')} {d(text[f'auc_minus_{reference}'])} "
        f"{ci(text[f'auc_minus_{reference}_ci_low'], text[f'auc_minus_{reference}_ci_high'])}.",
        f"14. **Calibration does not transfer to {years}**: the expected calibration error of {code(reference)} goes from "
        f"{f(calibration['ece_test_year'])} to {f(calibration['ece_holdout'])} ({code(s.path(f'{tag}_vs_test_year.csv'))}).",
        f"15. **Predictions depend on the size of the graph**: predicted again on the extended graph by the same frozen model, the "
        f"AUC of the test articles changes by up to {d(worst['auc_difference'])} ({code(worst['model'])}; "
        f"{code(s.path(f'{tag}_graph_growth.csv'))}).",
    ]
    return lines


def negative_results(s: Sources, cfg: dict) -> list[str]:
    reference, base = cfg["consolidate"]["reference"], cfg["baselines"]["setting"]
    at = lambda model, setting="A", subset="all": s.value(MAIN, "auc_mean", model=model, setting=setting, split="test", subset=subset)  # noqa: E731
    full = cfg["consolidate"]["full_model"]
    no_scores = s.row(ABLATIONS, model="no_scores", split="test", subset="all")
    minus = s.rows(FIDELITY, group="all", method="input_x_gradient")
    seeds = s.table("explainability_seeds.csv")
    added = s.row(PAIRED, model="scores_critiques_lr", control="scores_all_lr", split="test", subset="all")
    return [
        "## Negative and unexpected results", "",
        f"1. **The main hypothesis is not supported.** No heterogeneous GNN reaches a logistic regression on the mean, minimum, "
        f"maximum and standard deviation of the initial ratings: {code(full['model'])} {f(at(full['model'], full['setting']))} against "
        f"{code(reference)} {f(at(reference, base))} on all papers, {f(at(full['model'], full['setting'], 'borderline'))} against "
        f"{f(at(reference, base, 'borderline'))} on borderline papers. ({code(s.path(MAIN))})",
        f"2. **The critiques add nothing measurable to the scores.** Without the graph: {d(added['difference'])} "
        f"{ci(added['ci_low'], added['ci_high'])} for the logistic regression ({code(s.path(PAIRED))}). The gains seen on "
        "validation do not transfer to the test year.",
        f"3. **R-GCN is below the untyped GCN** ({f(at('rgcn'), 4)} against {f(at('gcn'), 4)}), while HAN and HGT are above it: "
        "typing the relations is not enough by itself.",
        "4. **The author responses bring no gain** (setting B against setting A).",
        f"5. **Without the scores the graph model fails** ({f(no_scores['auc_mean'], 4)}), below a logistic regression on critique "
        f"counts ({f(at('critiques_lr'), 4)}) and below an MLP on the review text ({f(at('text_mlp'), 4)}). "
        f"({code(s.path(ABLATIONS))}, {code(s.path(MAIN))})",
        "6. **The text of the critiques brings nothing once their typed labels are there** (ablation `no_critique_text`).",
        "7. **The GNNs generalise less well from 2024 to 2025 than the score baselines**, and are less well calibrated.",
        f"8. **Gradient attributions are worse than random on fidelity−** (difference from "
        f"{d(minus['fidelity_minus_top_minus_random'].min())} to {d(minus['fidelity_minus_top_minus_random'].max())}; "
        f"{code(s.path(FIDELITY))}).",
        f"9. **Explanations are unstable across seeds** (rank correlation from {f(seeds['mean_spearman'].min())} to "
        f"{f(seeds['mean_spearman'].max())}; {code(s.path('explainability_seeds.csv'))}).",
        "10. **In rejected papers, negative critiques push the prediction up**, not down (RQ3).",
        *holdout_negative_results(s, cfg), "",
    ]


def limitations(s: Sources, cfg: dict) -> list[str]:
    by_year = {year: s.row("clean_report_by_year.csv", year=year) for year in (*cfg["splits"]["train"], *cfg["splits"]["test"])}
    extraction = dict(s.table("llm_full_v3_summary.csv").itertuples(index=False, name=None))
    markers = s.rows("kg_post_rebuttal_markers.csv", modified_after_release=True)
    without_text = {subset: int(s.value("baselines.csv", "n_papers", model="majority", split="test", subset=subset)) for subset in ("all", "with_text")}
    coverage = s.table("article_text_coverage.csv")
    expect(bool((coverage.loc[coverage["year"].isin(cfg["splits"]["train"]), "found_in_archive"] == 1).all()),
           "every paper of the training year is found in the archive of texts")
    selection = s.table("gnn_selection.csv")
    searched = selection[selection["stage"] == "selection"]
    tests = s.table(TESTS)
    n_tests = int(sum(tests[column].notna().sum() for column in tests.columns if column.startswith("delong_p_vs_")))
    return [
        "## Limitations", "",
        "1. **One venue, one field, two years.** Every paper is a machine-learning submission to ICLR; nothing is measured on "
        "another field, another venue or another review form. The model is trained on one year and tested on the next.",
        "2. **The labels of the critiques are not validated by humans.** They come from one LLM (Qwen3-14B, temperature 0); the "
        "annotation of phase 4 is not done. Everything that reads the labels (critique counts, ablations of labels, "
        "importance by aspect × severity) inherits this.",
        f"3. **Extraction failures.** {n(extraction['align_failed'])} reviews whose author responses could not be aligned, "
        f"{n(extraction['segment_failed'])} review not segmented, {n(extraction['type_failed'])} not typed, out of "
        f"{n(extraction['reviews'])} ({code(s.path('llm_full_v3_summary.csv'))}; causes in {code(s.path('llm_full_v3_failures.csv'))}). "
        "The detailed log of these failures was deleted by mistake on 2026-11-18; only the aggregated causes remain.",
        "4. **Initial text of the reviews.** "
        + "; ".join(f"{pct(row['share_reviews_modified_after_release'])} of the {year} reviews" for year, row in by_year.items())
        + f" were modified after their release ({code(s.path('clean_report_by_year.csv'))}). Their initial scores are known from an "
        "external archive, but their text is only available in its final state: OpenReview does not expose earlier versions "
        "(answer of its support, 2026-11-19). The LLM sets aside the sentences written after the discussion; a marker of the "
        "discussion is still found in "
        + " and ".join(f"{pct(row['share_with_a_marker_left'])} of the modified reviews of {int(row['year'])}" for _, row in markers.iterrows())
        + f" ({code(s.path('kg_post_rebuttal_markers.csv'))}).",
        f"5. **Test papers without text.** {n(without_text['all'] - without_text['with_text'])} of the {n(without_text['all'])} test "
        f"papers have no title, abstract nor concept: they are not in the archive taken before the decisions, where every "
        f"paper of the training year is found ({code(s.path('baselines.csv'))}, {code(s.path('article_text_coverage.csv'))}). "
        "The model never sees a paper without text in training.",
        "6. **The test year has been looked at several times.** The critique baselines, the ablations and the explanations were "
        "designed after the first test results. "
        + ("ICLR 2026 is the fresh test: the models were frozen before it was looked at (section *Holdout year*)."
           if has_holdout(s, cfg) else "ICLR 2026 is meant to be the fresh test; it is not available yet."),
        f"7. **Multiple comparisons.** {n_tests} DeLong tests in {code(s.path(TESTS))}, plus the paired comparisons and the "
        "ablations, without correction.",
        f"8. **Hyper-parameter search.** One seed, {n(s.value('clean_report_splits.csv', 'papers', withdrawn='excluded', split='val'))} "
        f"validation papers of the training year; {int((searched['status'] != 'ok').sum())} of the {len(searched)} configurations "
        f"tried for the GNNs ran out of memory ({code(s.path('gnn_selection.csv'))}); the chosen configurations are at the edge "
        "of the grid. Full-batch training only.",
        "9. **Intervals.** They count the draw of the papers, not the variability between seeds nor between runs on the GPU.",
        f"10. **Explanations.** One architecture, one seed for the means per cell, {n(len(s.table('explainability_runs.csv')))} of "
        f"the {n(without_text['all'])} test papers; occlusion removes "
        "one critique at a time, so redundant critiques look unimportant; GNNExplainer was not used (its edge masks do not "
        "reach the HGT layers in PyTorch Geometric).",
        "11. **Ablations.** Hyper-parameters are not tuned again for each variant, which makes the variants without scores hard "
        "to interpret.", "",
    ]


def index(artefacts: list[dict]) -> list[str]:
    rows = [[code(item["path"]), item["description"], code(item["script"]), ", ".join(code(path) for path in item["sources"])]
            for item in artefacts]
    return ["## Index of tables and figures", "", *table(["File", "Content", "Written by", "Read from"], rows)]


def build(s: Sources, cfg: dict, artefacts: list[dict]) -> str:
    lines = ["# Results summary", "",
             "Written by `scripts/10_consolidate.py` from the files of `results/tables/`. Do not edit by hand: change the "
             "script or the text in `src/eval/summary.py` and run it again. Every number is followed by the file it is read in.", ""]
    for section in (protocol, status, rq1, rq2, rq3, rq4, holdout, negative_results, limitations):
        lines += section(s, cfg)
    return "\n".join(lines + index(artefacts)) + "\n"
