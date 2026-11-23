"""Numbers quoted in the text of the paper, as LaTeX macros read from the result tables.

Every macro is one cell of a CSV file of results/tables/ (or a difference with its
interval, or a count of rows of such a file), read through `Sources`, or one setting of
configs/default.yaml. The text of paper/sections/ never holds a result typed by hand: it
calls these macros, and the file written here names, next to each macro, the file its
value comes from.

Naming: a macro name only holds letters. Subsets of papers are `All` and `Border`; the
years are named by their role (`TrainYear`, `TestYear`, `HoldYear`); a model in setting
B carries a `B` after its name.
"""

import inspect
import re

from src.eval import latex
from src.eval.paper import SEVERITIES, holdout_tag
from src.eval.sources import Sources, verdict
from src.eval.summary import MAIN, TESTS, has_holdout, is_gnn

CONFIG = "configs/default.yaml"
MINUS, PLUS = r"\ensuremath{-}", r"\ensuremath{+}"
SUBSETS = {"all": "All", "borderline": "Border"}
GROUP_NAMES = {"all": "All", "accepted": "Accepted", "rejected": "Rejected", "borderline": "Border"}
WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five"}


# ------------------------------------------------------------------------ formatting

def count(value: float) -> str:
    """Integer with a thin space between thousands, as in the tables."""
    return f"{int(round(value)):,}".replace(",", r"\,")


def plain(value: float, decimals: int = 3) -> str:
    return f"{value:.{decimals}f}"


def signed(value: float, decimals: int = 4) -> str:
    """Number with its sign; a value that rounds to zero carries none."""
    if not round(value, decimals):
        return f"{0:.{decimals}f}"
    return (MINUS if value < 0 else PLUS) + f"{abs(value):.{decimals}f}"


def percent(share: float, decimals: int = 1) -> str:
    return rf"{100 * share:.{decimals}f}\,\%"


def interval(low: float, high: float, decimals: int = 4, sign: bool = True) -> str:
    form = signed if sign else plain
    return f"[{form(low, decimals)}, {form(high, decimals)}]"


def difference(value: float, low: float, high: float, decimals: int = 4) -> str:
    return f"{signed(value, decimals)} {interval(low, high, decimals)}"


def p_value(value: float) -> str:
    return r"\ensuremath{p < 0.001}" if value < 0.001 else rf"\ensuremath{{p = {value:.3f}}}"


def scientific(value: float) -> str:
    mantissa, exponent = f"{value:.1e}".split("e")
    return rf"\ensuremath{{{mantissa} \times 10^{{{int(exponent)}}}}}"


def escape(text: object) -> str:
    return latex.escape(text)


def grid_text(grid: dict) -> str:
    """Values tried for each hyper-parameter: "layers \\{2, 3\\}; hidden \\{64, 128\\}"."""
    return "; ".join(f"{escape(key.replace('_', ' '))} \\{{{', '.join(f'{value:g}' for value in values)}\\}}" for key, values in grid.items())


def camel(*parts: object) -> str:
    """Letters of the parts, each word capitalised: ("scores_rating_lr", "all") -> ScoresRatingLrAll."""
    words = re.split(r"[^A-Za-z]+", " ".join(map(str, parts)))
    return "".join(word[:1].upper() + word[1:] for word in words if word)


class Numbers:
    """Macros in the order they are added, each with the files its value is read in."""

    def __init__(self, sources: Sources):
        self.s = sources
        self.macros: dict[str, tuple[str, list[str]]] = {}

    def add(self, name: str, text: str, *tables: str) -> None:
        """`tables`: the result tables (names in results/tables/) the value is read in, or
        a path of the repository (`CONFIG`, a source file). A table read through `Sources` since the previous macro and not named
        here is an error: a value cannot come from a file that its macro does not name."""
        if not re.fullmatch(r"[A-Za-z]+", name):
            raise ValueError(f"a macro name only holds letters: {name!r}")
        if name in self.macros:
            raise ValueError(f"macro defined twice: {name}")
        if not tables:
            raise ValueError(f"macro {name}: no source")
        named = [table if "/" in table else self.s.path(table) for table in tables]
        unnamed = [path for path in self.s.take_used() if path not in named]
        if unnamed:
            raise ValueError(f"macro {name}: reads {unnamed}, which it does not name")
        self.macros[name] = (text, named)

    def table(self, name: str):
        """A whole table whose rows are gone through one by one: each macro then names the
        tables its own value comes from."""
        table = self.s.table(name)
        self.s.take_used()
        return table


def render(macros: dict[str, tuple[str, list[str]]]) -> str:
    lines = ["% Written by scripts/11_paper.py (src/eval/numbers.py) from the result tables and the configuration.",
             "% Do not edit by hand: every macro is followed by the file its value is read in.", ""]
    lines += [rf"\newcommand{{\{name}}}{{{text}}}% {', '.join(sources)}" for name, (text, sources) in macros.items()]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- sections

def roles(cfg: dict) -> dict[int, str]:
    """Role of each year: {2024: "TrainYear", 2025: "TestYear", 2026: "HoldYear"}."""
    splits = cfg["splits"]
    names = {year: "TrainYear" for year in splits["train"]} | {year: "TestYear" for year in splits["test"]}
    return names | {year: "HoldYear" for year in splits.get("holdout", [])}


def configuration(n: Numbers, cfg: dict) -> None:
    borderline, gnn, explain, kg = cfg["baselines"]["borderline"], cfg["gnn"], cfg["explain"], cfg["kg"]
    values = {
        "NSeeds": str(len(cfg["seeds"])),
        "NResamples": count(gnn["statistics"]["n_resamples"]),
        "ValFraction": percent(cfg["splits"]["validation"]["fraction"], 0),
        "BorderBinWidth": plain(borderline["bin_width"], 2),
        "BorderMinPapers": str(borderline["min_papers"]),
        "BorderLow": plain(borderline["low"], 1),
        "BorderHigh": plain(borderline["high"], 1),
        "ExplainPerGroup": str(explain["sample"]["per_group"]),
        "StabilityPerGroup": str(explain["stability"]["per_group"]),
        "IgPerGroup": str(explain["integrated_gradients"]["per_group"]),
        "IgSteps": str(explain["integrated_gradients"]["steps"]),
        "MinArticles": str(cfg["consolidate"]["min_articles"]),
        "ConceptMinArticles": str(kg["concepts"]["min_articles"]),
        "ConceptMaxShared": str(kg["concepts"]["max_articles_for_shared"]),
        "ReviewChunkChars": count(kg["review_chunk_chars"]),
        "MaxModelLen": count(cfg["llm"]["max_model_len"]),
        "GnnHeads": str(gnn["training"]["heads"]),
        "GnnMaxEpochs": str(gnn["training"]["max_epochs"]),
        "GnnPatience": str(gnn["training"]["patience"]),
        "BaseMaxEpochs": str(cfg["baselines"]["training"]["max_epochs"]),
        "BasePatience": str(cfg["baselines"]["training"]["patience"]),
        "AnnotationSize": str(cfg["annotation"]["size"]),
        "PilotSize": str(cfg["llm"]["samples"]["size"]),
        "CollectRate": str(cfg["collect"]["max_requests_per_minute"]),
    }
    statistics, external = gnn["statistics"], cfg["external"]
    values |= {
        "ConfLevel": percent(statistics["confidence"], 0),
        "LlmModel": escape(cfg["llm"]["model"]),
        "TextModel": escape(kg["text_model"]["name"]),
        "ArticleModel": escape(kg["article_model"]["base"]),
        "ArticleAdapter": escape(kg["article_model"]["adapter"]),
        "ArticleMaxLength": str(kg["article_model"]["max_length"]),
        "InsightsPaper": escape(external["iclr_insights"]["paper"]),
        "InsightsUrl": rf"\url{{{external['iclr_insights']['url']}}}",
        "IclrDatasetPaper": escape(external["iclr_dataset"]["paper"]),
        "IclrDatasetUrl": rf"\url{{{external['iclr_dataset']['url']}}}",
        "GridLr": grid_text(cfg["baselines"]["models"]["scores_rating_lr"]["grid"]),
        "GridMlp": grid_text(cfg["baselines"]["models"]["text_scores_mlp"]["grid"]),
        "GridGbt": grid_text(cfg["baselines"]["models"]["scores_all_gbt"]["grid"]),
        "GridGcn": grid_text(cfg["baselines"]["models"]["gcn"]["grid"]),
        "GnnWeightDecay": f"{gnn['training']['weight_decay']:g}",
    }
    for setting, grid in gnn["grid"].items():
        values[f"GridGnn{setting}"] = grid_text(grid)
    for year, levels in cfg["clean"]["rating_levels"].items():
        values[f"RatingLevels{roles(cfg)[year]}"] = ", ".join(map(str, levels))
        values[f"RatingLevelsMappedTo{roles(cfg)[year]}"] = ", ".join(map(str, levels.values()))
    for name, text in values.items():
        n.add(name, text, CONFIG)
    n.add("Alpha", plain(inspect.signature(verdict).parameters["alpha"].default, 2), "src/eval/sources.py")


def corpus(n: Numbers, cfg: dict) -> None:
    s, year_names = n.s, roles(cfg)
    splits, by_year, check, markers = "clean_report_splits.csv", "clean_report_by_year.csv", "initial_scores_check_full.csv", "kg_post_rebuttal_markers.csv"
    for withdrawn, tag in (("excluded", ""), ("as_reject", "AsReject")):
        for split, name in (("train", "Train"), ("val", "Val"), ("test", "Test"), ("holdout", "Hold")):
            found = s.rows(splits, withdrawn=withdrawn, split=split)
            if len(found) != 1:
                continue  # no holdout year
            row = found.iloc[0]
            n.add(f"Papers{tag}{name}", count(row["papers"]), splits)
            n.add(f"Accept{tag}{name}", percent(row["acceptance_rate"]), splits)
            n.add(f"Reviews{tag}{name}", count(row["reviews"]), splits)
    for year, name in year_names.items():
        row = s.row(by_year, year=year)
        n.add(f"Submissions{name}", count(row["papers"]), by_year)
        n.add(f"Decided{name}", count(row["papers_with_decision"]), by_year)
        n.add(f"Withdrawn{name}", count(row["withdrawn"]), by_year)
        n.add(f"AllReviews{name}", count(row["reviews"]), by_year)
        n.add(f"InitialReviews{name}", count(row["reviews_with_initial_scores"]), by_year)
        n.add(f"Modified{name}", percent(row["share_reviews_modified_after_release"]), by_year)
    for year in (*cfg["splits"]["train"], *cfg["splits"]["test"]):
        row, name = s.row(check, year=year), year_names[year]
        n.add(f"ScoresMatched{name}", count(row["reviews_matched"]), check)
        n.add(f"ScoresMatchedShare{name}", percent(row["share_reviews_matched"]), check)
        n.add(f"ScoresEqualFinal{name}", percent(row["share_post_rating_equals_final"], 0), check)
        n.add(f"RatingChanged{name}", percent(row["share_matched_rating_changed"]), check)
        n.add(f"RatingRaised{name}", count(row["matched_rating_increased"]), check)
        n.add(f"RatingLowered{name}", count(row["matched_rating_decreased"]), check)
        for modified, tag in ((True, "Modified"), (False, "Unmodified")):
            n.add(f"Marker{tag}{name}", percent(s.value(markers, "share_with_a_marker_left", year=year, modified_after_release=modified), 2), markers)
    zone = s.table("borderline_definition.csv")
    zone = zone[zone["in_zone"]]
    n.add("ZoneLow", plain(zone["bin_start"].min(), 2), "borderline_definition.csv")
    n.add("ZoneHigh", plain(zone["bin_end"].max(), 2), "borderline_definition.csv")
    reference, setting = cfg["consolidate"]["reference"], cfg["baselines"]["setting"]
    for split, name in (("val", "Val"), ("test", "Test")):
        inside = s.value(MAIN, "n_papers", model=reference, setting=setting, split=split, subset="borderline")
        everyone = s.value(MAIN, "n_papers", model=reference, setting=setting, split=split, subset="all")
        n.add(f"Borderline{name}", count(inside), MAIN)
        n.add(f"BorderlineShare{name}", percent(inside / everyone), MAIN)
    papers = {subset: s.value("baselines.csv", "n_papers", model="majority", split="test", subset=subset) for subset in ("all", "with_text")}
    n.add("TestWithoutText", count(papers["all"] - papers["with_text"]), "baselines.csv")


def extraction(n: Numbers, cfg: dict) -> None:
    s = n.s
    for run, tag in (("llm_full_v3", ""), ("llm_full_v3_2026", "Hold")):
        name = f"{run}_summary.csv"
        if not (s.tables_dir / name).is_file():
            continue
        summary = dict(s.table(name).itertuples(index=False, name=None))
        values = {
            "Reviews": count(summary["reviews"]),
            "ReviewsWithCritiques": count(summary["reviews_with_critiques"]),
            "Critiques": count(summary["critiques"]),
            "Typed": count(summary["critiques_typed"]),
            "PerReviewMean": plain(summary["critiques_per_review_mean"], 1),
            "PerReviewMedian": count(summary["critiques_per_review_median"]),
            "PerReviewMax": count(summary["critiques_per_review_max"]),
            "UnitsInCritiques": percent(summary["share_units_in_critiques"]),
            "UnitsIgnored": percent(summary["share_units_ignored"]),
            "UnitsPostRebuttal": percent(summary["share_units_post_rebuttal"]),
            "ReviewsPostRebuttal": count(summary["reviews_with_post_rebuttal_units"]),
            "SegmentFailed": count(summary["segment_failed"]),
            "TypeFailed": count(summary["type_failed"]),
        }
        if not tag:  # the author responses were only extracted for the years of the study
            values |= {"AlignFailed": count(summary["align_failed"]), "ReviewsWithReply": count(summary["reviews_with_author_reply"]),
                       "Aligned": count(summary["critiques_aligned"]), "WithResponse": count(summary["critiques_with_a_response"]),
                       "RepliesTruncated": count(summary["replies_truncated"]), "ReviewsTruncated": count(summary["reviews_truncated"])}
        for key, text in values.items():
            n.add(f"Llm{tag}{key}", text, name)
        for label in ("aspect", "severity", "polarity"):
            for _, row in s.table(f"{run}_{label}.csv").iterrows():
                if not str(row[label]).startswith("("):  # the row of missing labels
                    n.add(camel("Share", tag, label, row[label]), percent(row["share"]), f"{run}_{label}.csv")
    passes = s.table("llm_full_v3_passes.csv")
    n.add("LlmHours", plain(passes["seconds"].sum() / 3600, 1), "llm_full_v3_passes.csv")
    for _, row in passes.iterrows():
        n.add(camel("LlmHours", row["step"]), plain(row["seconds"] / 3600, 1), "llm_full_v3_passes.csv")
    name = "llm_extractors_check_v3_vs_check_v3_deepseek"
    labels = s.table(f"{name}_labels.csv")
    for _, row in labels.iterrows():
        n.add(camel("Kappa", row["label"]), plain(row["cohen_kappa"], 2), f"{name}_labels.csv")
        n.add(camel("Agreement", row["label"]), percent(row["agreement"]), f"{name}_labels.csv")
    if labels["critiques_compared"].nunique() != 1:
        raise LookupError(f"{name}_labels.csv: the labels are not compared on the same critiques")
    n.add("KappaCritiques", count(labels["critiques_compared"].iloc[0]), f"{name}_labels.csv")
    compared = dict(s.table(f"{name}_summary.csv").itertuples(index=False, name=None))
    n.add("KappaReviews", count(float(compared["reviews segmented and typed by both"])), f"{name}_summary.csv")
    n.add("KappaSameFate", percent(float(compared["share of units with the same fate (critique / ignored / post-rebuttal)"])), f"{name}_summary.csv")
    n.add("KappaFoundInOther", percent(float(compared["share of the critiques of check_v3 found in check_v3_deepseek"])), f"{name}_summary.csv")
    strata = s.table("annotation_sample_strata.csv")
    n.add("AnnotationStrata", str(len(strata)), "annotation_sample_strata.csv")
    n.add("AnnotationSampled", count(strata["sampled"].sum()), "annotation_sample_strata.csv")


def graph(n: Numbers, cfg: dict) -> None:
    s, year_names = n.s, roles(cfg)
    names = {"article": "Articles", "review": "Reviews", "critique": "Critiques", "aspect": "Aspects", "concept": "Concepts",
             "response": "Responses", "article -has_concept-> concept": "HasConcept", "article -shares_concept-> article": "SharesConcept",
             "critique -about-> aspect": "About", "response -responds_to-> critique": "RespondsTo"}
    for element, name in names.items():
        n.add(f"Kg{name}", count(s.value("kg_statistics.csv", "count", setting="B", type=element)), "kg_statistics.csv")
    extended, coverage = "kg_statistics_holdout.csv", "kg_concept_coverage_holdout.csv"
    if (s.tables_dir / extended).is_file():
        for element in ("article", "review", "critique"):
            row = s.row(extended, setting="A", type=element)
            n.add(f"KgExtended{names[element]}", count(row["count"]), extended)
            for year in cfg["splits"]["holdout"]:
                n.add(f"Kg{year_names[year]}{names[element]}", count(row[f"count_{year}"]), extended)
        for _, row in s.table(coverage).iterrows():
            name = year_names[int(row["year"])]
            n.add(f"KeywordsCovered{name}", percent(row["share_keywords_in_vocabulary"]), coverage)
            n.add(f"WithConcept{name}", percent(row["share_articles_with_a_concept"]), coverage)
            n.add(f"ConceptNeighbours{name}", plain(row["mean_shares_concept_neighbours"], 1), coverage)


def model_name(model: str, setting: str, cfg: dict) -> str:
    return camel(model) + ("" if setting == cfg["baselines"]["setting"] else setting)


def main_results(n: Numbers, cfg: dict) -> None:
    s, reference = n.s, cfg["consolidate"]["reference"]
    tests = n.table(TESTS)
    for _, row in tests.iterrows():
        name, subset = model_name(row["model"], row["setting"], cfg), SUBSETS[row["subset"]]
        where = {"model": row["model"], "setting": row["setting"], "subset": row["subset"]}
        test, validation = s.row(MAIN, split="test", **where), s.row(MAIN, split="val", **where)
        n.add(f"Auc{name}{subset}", plain(test["auc_mean"]), MAIN)
        n.add(f"AucCi{name}{subset}", interval(row["auc_ci_low"], row["auc_ci_high"], 3, sign=False), TESTS)
        if not (row["model"] == reference and row["setting"] == cfg["baselines"]["setting"]):
            n.add(f"Delta{name}{subset}", difference(row[f"auc_minus_{reference}"], row[f"auc_minus_{reference}_ci_low"],
                                                      row[f"auc_minus_{reference}_ci_high"]), TESTS)
            n.add(f"P{name}{subset}", p_value(row[f"delong_p_vs_{reference}"]), TESTS)
        n.add(f"AucVal{name}{subset}", plain(validation["auc_mean"]), MAIN)
        if row["subset"] == "all":
            n.add(f"ValToTest{name}", signed(test["auc_mean"] - validation["auc_mean"]), MAIN)
            n.add(f"Ece{name}", plain(test["ece_mean"]), MAIN)
    hetero = tests["model"].map(lambda model: is_gnn(model, cfg))
    below = tests[f"auc_minus_{reference}_ci_high"] < 0
    n.add("NHetero", str(int((hetero & (tests["subset"] == "all")).sum())), TESTS)
    n.add("NHeteroBelow", str(int((hetero & below & (tests["subset"] == "all")).sum())), TESTS)
    n.add("NHeteroBelowBorder", str(int((hetero & below & (tests["subset"] == "borderline")).sum())), TESTS)
    n.add("NHeteroBelowTextScores", str(int((hetero & (tests["auc_minus_text_scores_mlp_ci_high"] < 0) & (tests["subset"] == "all")).sum())), TESTS)
    n.add("NDelongTests", str(int(sum(tests[column].notna().sum() for column in tests.columns if column.startswith("delong_p_vs_")))), TESTS)
    selection = s.table("gnn_selection.csv")
    searched = selection[selection["stage"] == "selection"]
    n.add("GnnConfigsTried", str(len(searched)), "gnn_selection.csv")
    n.add("GnnConfigsFailed", str(int((searched["status"] != "ok").sum())), "gnn_selection.csv")
    name = "main_results_withdrawn_as_reject.csv"
    for model in s.rows(name, split="test", subset="all")["model"]:
        for subset, tag in SUBSETS.items():
            row = s.row(name, model=model, split="test", subset=subset)
            n.add(f"AucAsReject{camel(model)}{tag}", plain(row["auc_mean"]), name)
            n.add(f"PapersAsRejectScored{camel(model)}{tag}", count(row["n_papers"]), name)


def paired(n: Numbers, cfg: dict) -> None:
    table = "paired_comparisons.csv"
    for _, row in n.s.table(table).iterrows():
        name = camel(row["model"], row["control"], row["split"]) + SUBSETS[row["subset"]]
        n.add(f"Pair{name}", difference(row["difference"], row["ci_low"], row["ci_high"]), table)
        n.add(f"PairP{name}", p_value(row["delong_p"]), table)


def ablations(n: Numbers, cfg: dict) -> None:
    s = n.s
    table, pairs, runs_table = "ablations.csv", "ablations_paired.csv", "ablations_selection.csv"
    for _, row in s.rows(table, split="test").iterrows():
        if row["subset"] not in SUBSETS:
            continue
        name = camel(row["model"]) + SUBSETS[row["subset"]]
        n.add(f"AblAuc{name}", plain(row["auc_mean"], 4), table)
        n.add(f"AblStd{name}", plain(row["auc_std"], 4), table)
        if row["model"] != "full":
            n.add(f"AblDelta{name}", difference(row["auc_minus_full"], row["auc_minus_full_ci_low"], row["auc_minus_full_ci_high"]), table)
            n.add(f"AblP{name}", p_value(row["delong_p_vs_full"]), table)
    for _, row in s.rows(pairs, split="test").iterrows():
        n.add(camel("AblPair", row["model"], row["control"]) + SUBSETS[row["subset"]],
              difference(row["difference"], row["ci_low"], row["ci_high"]), pairs)
    runs = s.table(runs_table)
    without_scores = runs[runs["variant"].isin(["no_scores", "no_scores_no_critiques"])]
    n.add("AblRunsWithoutScores", str(len(without_scores)), runs_table)
    n.add("AblRunsStoppedEarly", str(int((without_scores["best_epoch"] <= 2).sum())), runs_table)


def importance(row, decimals: int = 1) -> str:
    """Importance per critique in hundredths of a logit, with its interval."""
    return difference(100 * row["importance_per_critique"], 100 * row["ci_low"], 100 * row["ci_high"], decimals)


def explanations(n: Numbers, cfg: dict) -> None:
    s, minimum = n.s, cfg["consolidate"]["min_articles"]
    name, runs_table = "explainability.csv", "explainability_runs.csv"
    runs = s.table(runs_table)
    n.add("ExplainedPapers", count(len(runs)), runs_table)
    n.add("ExplainMaxGap", scientific(runs["gap_with_stored_probability"].max()), runs_table)
    n.add("ExplainedCritiques", count(runs["n_critiques"].sum()), runs_table)
    for group, tag in GROUP_NAMES.items():
        for polarity in ("positive", "neutral", "negative"):
            n.add(camel("Imp", polarity) + tag, importance(s.row(name, group=group, method="occlusion", kind="polarity", polarity=polarity)), name)
        for severity in SEVERITIES:
            n.add(camel("ImpNegative", severity) + tag,
                  importance(s.row(name, group=group, method="occlusion", kind="negative_severity", severity=severity)), name)
    for group in ("accepted", "rejected", "borderline"):
        tag = GROUP_NAMES[group]
        found = s.rows(name, group=group, method="occlusion", kind="negative_aspect_severity")
        for _, row in found.iterrows():
            n.add(camel("ImpNeg", row["aspect"], row["severity"]) + tag, importance(row), name)
        for _, row in s.rows(name, group=group, method="occlusion", kind="positive_aspect").iterrows():
            n.add(camel("ImpPos", row["aspect"]) + tag, importance(row), name)
        read = found[found["n_articles_with_such_a_critique"] >= minimum]
        explaining = read[read["ci_excludes_zero"]]
        n.add(f"Cells{tag}", str(len(found)), name)
        n.add(f"CellsRead{tag}", str(len(read)), name)
        n.add(f"CellsExplain{tag}", str(len(explaining)), name)
        n.add(f"CellsExplainNegative{tag}", str(int((explaining["importance_per_critique"] < 0).sum())), name)
        n.add(f"CellsExplainPositive{tag}", str(int((explaining["importance_per_critique"] > 0).sum())), name)
    relations = "explainability_relations.csv"
    for _, row in s.table(relations).iterrows():
        prefix = "Rel" if row["kind"] == "relation" else "Ref"
        n.add(camel(prefix, row["removed"]) + GROUP_NAMES[row["group"]], difference(row["importance"], row["ci_low"], row["ci_high"], 2), relations)
    methods, methods_table = {"occlusion": "Occ", "input_x_gradient": "Grad", "integrated_gradients": "Ig"}, "explainability_methods.csv"
    for _, row in s.table(methods_table).iterrows():
        tag = methods[row["first"]] + methods[row["second"]]
        n.add(f"Spearman{tag}", plain(row["mean_spearman"]), methods_table)
        n.add(f"SpearmanCi{tag}", interval(row["ci_low"], row["ci_high"], 3, sign=False), methods_table)
        n.add(f"SameTop{tag}", percent(row["share_same_most_important_critique"]), methods_table)
        n.add(f"MethodPapers{tag}", count(row["n_articles"]), methods_table)
    seeds_table = "explainability_seeds.csv"
    seeds = s.table(seeds_table)
    if seeds["n_articles"].nunique() != 1:
        raise LookupError(f"{seeds_table}: the seeds are not compared on the same number of papers")
    n.add("SeedPapers", count(seeds["n_articles"].iloc[0]), seeds_table)
    for column, tag, form in (("mean_spearman", "SeedSpearman", plain), ("share_same_most_important_critique", "SeedSameTop", percent),
                              ("share_same_predicted_outcome", "SeedSameOutcome", percent)):
        n.add(f"{tag}Min", form(seeds[column].min()), seeds_table)
        n.add(f"{tag}Max", form(seeds[column].max()), seeds_table)
    fidelity_table = "explainability_fidelity.csv"
    fidelity = s.rows(fidelity_table, group="all", method="input_x_gradient")
    n.add("GradFidelityMinusMin", signed(fidelity["fidelity_minus_top_minus_random"].min()), fidelity_table)
    n.add("GradFidelityMinusMax", signed(fidelity["fidelity_minus_top_minus_random"].max()), fidelity_table)
    cases_table = "explainability_cases.csv"
    for case, rows in s.table(cases_table).groupby("case", sort=False):
        first = rows.iloc[0]
        if rows["probability"].nunique() != 1:
            raise LookupError(f"{cases_table}: several probabilities for the case {case}")
        n.add(camel("CaseProbability", case), plain(first["probability"]), cases_table)
        n.add(camel("CaseCritiques", case), count(first["n_critiques"]), cases_table)
        n.add(camel("CaseReviews", case), count(first["n_reviews"]), cases_table)


def holdout(n: Numbers, cfg: dict) -> None:
    s, tag, reference = n.s, holdout_tag(cfg), cfg["consolidate"]["reference"]
    if not has_holdout(s, cfg):
        return
    results, tests = f"{tag}.csv", f"{tag}_tests.csv"
    for _, row in n.table(tests).iterrows():
        name, subset = camel(row["model"]), SUBSETS[row["subset"]]
        n.add(f"AucHold{name}{subset}", plain(s.value(results, "auc_mean", model=row["model"], subset=row["subset"], split="holdout")), results)
        if row["model"] != reference:
            n.add(f"DeltaHold{name}{subset}", difference(row[f"auc_minus_{reference}"], row[f"auc_minus_{reference}_ci_low"],
                                                          row[f"auc_minus_{reference}_ci_high"]), tests)
            n.add(f"PHold{name}{subset}", p_value(row[f"delong_p_vs_{reference}"]), tests)
    for subset, name in SUBSETS.items():
        n.add(f"PapersHoldScored{name}", count(s.value(results, "n_papers", model=reference, subset=subset, split="holdout")), results)
    pairs = f"{tag}_paired.csv"
    for _, row in s.table(pairs).iterrows():
        n.add(camel("PairHold", row["model"], row["control"]) + SUBSETS[row["subset"]],
              difference(row["difference"], row["ci_low"], row["ci_high"]), pairs)
    calibration_table = f"{tag}_vs_test_year.csv"
    calibration = s.row(calibration_table, model=reference, subset="all")
    n.add("EceReferenceTest", plain(calibration["ece_test_year"]), calibration_table)
    n.add("EceReferenceHold", plain(calibration["ece_holdout"]), calibration_table)
    growth_table = f"{tag}_graph_growth.csv"
    growth = s.table(growth_table)
    for _, row in growth.iterrows():
        n.add(camel("Growth", row["model"]), signed(row["auc_difference"]), growth_table)
        n.add(camel("GrowthChanged", row["model"]), percent(row["share_of_predicted_outcomes_changed"]), growth_table)
    frozen = growth[~growth["trained_again"]]
    n.add("GrowthWorst", signed(frozen["auc_difference"].min()), growth_table)
    n.add("GrowthChangedMax", percent(frozen["share_of_predicted_outcomes_changed"].max()), growth_table)
    second_table = f"{tag}_second_run.csv"
    second = s.row(second_table, model="gcn")
    n.add("AucHoldGcnFirstRun", plain(second["auc_holdout_first_run"], 4), second_table)
    n.add("AucHoldGcnSecondRun", plain(second["auc_holdout_second_run"], 4), second_table)
    readings_table = f"{tag}_readings.csv"
    readings = s.table(readings_table)
    n.add("ReadingsChecked", str(len(readings)), readings_table)
    n.add("ReadingsHolding", str(int(readings["holds"].sum())), readings_table)


def build(s: Sources, cfg: dict) -> dict[str, tuple[str, list[str]]]:
    """Every macro of the paper: {name: (LaTeX text, files read)}."""
    n = Numbers(s)
    for section in (configuration, corpus, extraction, graph, main_results, paired, ablations, explanations, holdout):
        section(n, cfg)
    return n.macros
