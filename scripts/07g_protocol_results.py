"""Protocol checks: metrics, paired comparisons, tests and readings. Trains nothing.

    uv run python scripts/07g_protocol_results.py                # every comparison (about an hour: no GPU)
    uv run python scripts/07g_protocol_results.py --only depth   # the follow-up on the depth alone, added to the tables

Reads the predictions of scripts/07f_protocol_checks.py (three stages), of
scripts/08_ablations.py --group encoder_variants, and those of the study (phases 6 to 8
and the holdout year). Comparisons, families of tests and reading rule: section
`protocol` of the config, written before the stages were run. The follow-up of the
ablations of the encoders (scripts/08_ablations.py --group followup) is compared as its
section `followup` of the config says; that section was written after the result of these
ablations was read, and before the follow-up was run. The follow-up of stage `search` on
HAN (scripts/07f_protocol_checks.py --stage depth) is compared as its section
`depth_followup` says; that section was written after the results of the stage were
read, and before the follow-up was run. Everything here is post hoc: the test and
holdout years had been read.

`--only depth` computes the rows of the follow-up on the depth and adds them to the four
tables, whose other rows are left as they are. These rows are the ones a complete run
gives: the bootstrap draws the same papers whatever the models compared (one seed per
subset), and the Holm correction is made within a stage. Only their place in the files
differs: at the end, instead of after the other comparisons of their year.

A model is identified by its name and by where it comes from: "A" for the study (its
setting), the name of the stage otherwise. A stage whose predictions do not exist yet is
left out, with a warning.

Outputs in results/tables/:
    protocol_metrics.csv        metrics of every model of a stage per evaluated year and subset, mean and
                                standard deviation over the seeds
    protocol_comparisons.csv    AUC of a model minus AUC of its control: paired bootstrap over the papers, DeLong
                                test and its Holm correction within the family (stage, year, kind of comparison)
    protocol_readings.csv       conclusions (a) and (b) of the article in each stage, year and subset; reading (d) of the follow-up
                                of the encoders; readings (e) and (f) of the follow-up on the depth
    protocol_seed_signs.csv     per model: AUC of each seed minus the AUC of the reference (study and stages)
"""

import argparse
import sys

import numpy as np
import pandas as pd

from src.eval import metrics, stats
from src.eval.compare import by_seed_metrics
from src.eval.protocol import reading
from src.eval.sensitivity import paired_rows
from src.eval.sources import excludes_zero
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

STUDY = "A"            # where the models of the study come from: their setting
ENCODERS = "encoders"  # the ablations of the pretrained encoders, compared like a stage
FOLLOWUP = "followup"  # their follow-up: where its models come from, and the name of its comparisons
FULL = "full"
DEPTH = "depth"        # the follow-up of stage `search` on HAN: where its models come from, and the name of its comparisons
# Readings of the section `depth_followup`: the cell named by the config is above the reference.
DEPTH_STATEMENTS = {"e": "{model} with the depth of phase 7 and the weight decay kept is above {reference}",
                    "f": "{model} with the depth kept and the weight decay of phase 7 is above {reference}"}
PAPER_COLUMNS = ["forum_id", "split", "label", "borderline", "text_available"]
COLUMNS = ["model", "setting", "seed", *PAPER_COLUMNS, "probability"]


def study_predictions(cfg: dict, log) -> dict[str, pd.DataFrame]:
    """Predictions of the study per evaluated year (name of the split): phases 6 to 8 for
    the test year, the frozen models for the holdout year."""
    directory = cfg["paths"]["predictions"]
    baselines = pd.read_parquet(directory / "baselines.parquet").assign(setting=STUDY)
    gnn = pd.read_parquet(directory / "gnn.parquet")
    gnn = gnn[(gnn["labels"] == "label") & (gnn["setting"] == STUDY)]
    parts = [baselines, gnn]
    full = pd.read_parquet(directory / "ablations.parquet")
    parts.append(full[full["model"] == FULL])
    if (directory / "ablations_encoder.parquet").is_file():
        parts.append(pd.read_parquet(directory / "ablations_encoder.parquet"))
    else:
        log.warning("left out, no prediction yet: the ablations of the encoders")
    test = pd.concat([part[COLUMNS] for part in parts], ignore_index=True)
    holdout = pd.read_parquet(directory / ("holdout_" + "_".join(map(str, cfg["splits"]["holdout"])) + ".parquet"))
    return {"test": test[test["split"] == "test"], "holdout": holdout.loc[holdout["split"] == "holdout", COLUMNS]}


def main() -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--only", choices=[DEPTH], help="compute the rows of this follow-up alone and add them to the existing tables")
    args = parser.parse_args()
    protocol, statistics = cfg["protocol"], cfg["gnn"]["statistics"]
    log = setup_run_logging("07g_protocol_results", cfg["paths"]["logs"])
    tables_dir, predictions_dir = cfg["paths"]["tables"], cfg["paths"]["predictions"]
    reference, rules, suffix = protocol["reference"], protocol["comparisons"], cfg["gnn"]["score_variant"]["suffix"]
    hetero = rules["hetero"]
    hetero_variants = [name + end for name in hetero for end in ("", suffix)]

    study = study_predictions(cfg, log)
    stages = {}
    for stage in protocol["stages"]:
        path = predictions_dir / f"protocol_{stage}.parquet"
        if path.is_file():
            stages[stage] = pd.read_parquet(path)[COLUMNS]
        else:
            log.warning("left out, no prediction yet: stage %s", stage)

    # ---- pairs to compare, per evaluated year: (stage, kind of comparison, model, control)
    wanted: dict[str, list[tuple]] = {"test": [], "holdout": []}
    for stage, table in stages.items():
        rule, names = rules[stage], list(dict.fromkeys(table["model"]))
        control = (reference, STUDY if rule["vs_reference"] == "study" else stage)
        for evaluated in rule["evaluated"]:
            known = set(study[evaluated]["model"])
            pairs = wanted[evaluated]
            pairs += [(stage, "vs_reference", (name, stage), control) for name in names if (name, stage) != control]
            if rule["vs_study"]:
                pairs += [(stage, "vs_study", (name, stage), (name, STUDY)) for name in names if name in known]
            if rule["hetero_vs_gcn"]:
                pairs += [(stage, "hetero_vs_gcn", (name, stage), ("gcn", stage)) for name in hetero if name in names]
    encoder_variants = [name for name in cfg["ablations"]["encoder_variants"] if name in set(study["test"]["model"])]
    for name in encoder_variants:
        wanted["test"] += [(ENCODERS, "vs_full", (name, STUDY), (FULL, STUDY)), (ENCODERS, "vs_reference", (name, STUDY), (reference, STUDY))]

    # ---- follow-up of the ablations of the encoders: test year (trained again) and holdout year (frozen)
    followup, extra = cfg["followup"], {}
    files = {"test": predictions_dir / "ablations_followup.parquet", "holdout": predictions_dir / "ablations_followup_holdout.parquet"}
    if all(path.is_file() for path in files.values()):
        for evaluated, path in files.items():
            table = pd.read_parquet(path).assign(setting=FOLLOWUP)
            extra[evaluated] = table.loc[table["split"] == evaluated, COLUMNS]
            main = (followup["main"], FOLLOWUP)
            for name in followup["variants"]:
                wanted[evaluated] += [(FOLLOWUP, "vs_reference" if other == reference else "vs_study_model", (name, FOLLOWUP), (other, STUDY))
                                      for other in followup["against"]]
            wanted[evaluated] += [(FOLLOWUP, "within", main, (name, FOLLOWUP)) for name in followup["within"]]
        wanted["test"].append((FOLLOWUP, "vs_first_run", main, (followup["main"], STUDY)))  # the same variant, trained the first time
    else:
        log.warning("left out, no prediction yet: the follow-up of the ablations of the encoders")

    # ---- follow-up of stage `search` on HAN: each cell of its design against the reference of that stage, and between cells
    depth, depth_table = cfg["depth_followup"], None
    origin, depth_path = depth["reference_stage"], predictions_dir / f"protocol_{DEPTH}.parquet"
    if depth_path.is_file() and origin in stages:
        depth_table = pd.read_parquet(depth_path)[COLUMNS]
        cell = {name: (depth["model"], origin) if values.get("stored") else (f"{depth['model']}_{name}", DEPTH)
                for name, values in depth["cells"].items()}  # the stored cell is the model kept by the stage
        for evaluated in depth["evaluated"]:
            wanted[evaluated] += [(DEPTH, "vs_reference", key, (reference, origin)) for key in cell.values() if key[1] == DEPTH]
            wanted[evaluated] += [(DEPTH, "within", cell[first], cell[second]) for first, second in depth["within"]]
    else:
        log.warning("left out, no prediction yet: the follow-up of stage %s on the depth", origin)

    if args.only:
        if depth_table is None:
            log.error("--only %s: its predictions do not exist", args.only)
            return 1
        wanted = {evaluated: [pair for pair in pairs if pair[0] == args.only] for evaluated, pairs in wanted.items()}

    # ---- one table of predictions per evaluated year: the study and the stages, on the same papers
    comparisons, summaries, signs = [], [], []
    for evaluated, pairs in wanted.items():
        if not pairs:
            continue
        parts = [study[evaluated]] + [table[table["split"] == evaluated] for stage, table in stages.items()
                                      if evaluated in rules[stage]["evaluated"]] + ([extra[evaluated]] if evaluated in extra else [])
        if depth_table is not None and evaluated in depth["evaluated"]:
            parts.append(depth_table[depth_table["split"] == evaluated])
        predictions = pd.concat(parts, ignore_index=True)
        if args.only:  # the models of these comparisons alone
            keys = {key for _, _, model, control in pairs for key in (model, control)}
            predictions = predictions[[key in keys for key in zip(predictions["model"], predictions["setting"])]].reset_index(drop=True)
        papers = predictions.drop_duplicates("forum_id")[PAPER_COLUMNS].set_index("forum_id").sort_index()
        for (model, setting), table in predictions.groupby(["model", "setting"], sort=False):
            if table["seed"].nunique() != len(cfg["seeds"]) or len(table) != len(cfg["seeds"]) * len(papers):
                raise SystemExit(f"{model} ({setting}) is not predicted on the {len(papers)} papers of the {evaluated} year with every seed")
            own = table.drop_duplicates("forum_id")[PAPER_COLUMNS].set_index("forum_id").sort_index()
            if not own.index.equals(papers.index) or not (own.to_numpy() == papers.to_numpy()).all():  # same papers, labels, zone
                raise SystemExit(f"{model} ({setting}): the papers of the {evaluated} year differ from those of the other models")
        log.info("%s year: %d papers, %d models, %d comparisons", evaluated, len(papers), predictions.groupby(["model", "setting"]).ngroups, len(pairs))

        unique = list(dict.fromkeys((key, control) for _, _, key, control in pairs))
        for subset in statistics["subsets"]:
            rows = {(row["model"], row["setting"], row["control"], row["control_setting"]): row
                    for row in paired_rows(predictions, subset, unique, statistics)}
            comparisons += [{"stage": stage, "evaluated": evaluated, "comparison": kind, **rows[(*key, *control)]}
                            for stage, kind, key, control in pairs]

        by_seed = by_seed_metrics(predictions)
        by_seed = by_seed[by_seed["subset"].isin(statistics["subsets"])]
        summary = metrics.summarise(by_seed, ["model", "setting", "split", "subset"])
        summaries.append(summary.rename(columns={"split": "evaluated"}))
        # per seed: AUC minus the mean AUC of the reference the model is compared with
        auc = by_seed.set_index(["model", "setting", "subset", "seed"])["auc"]
        for (model, setting, subset), values in auc.groupby(level=[0, 1, 2], sort=False):
            where = setting if setting in stages and rules[setting]["vs_reference"] == "stage" else STUDY
            if setting == DEPTH:
                where = origin
            if (model, setting) == (reference, where):
                continue
            base = float(auc.loc[(reference, where, subset)].mean())
            gaps = values.to_numpy() - base
            signs.append({"evaluated": evaluated, "model": model, "setting": setting, "subset": subset, "reference": reference,
                          "reference_setting": where, "n_seeds": len(gaps), "seeds_below_reference": int((gaps < 0).sum()),
                          "seeds_above_reference": int((gaps > 0).sum()), "difference_min": gaps.min(), "difference_max": gaps.max(),
                          "difference_mean": gaps.mean(), "auc_std_over_seeds": values.std(ddof=1)})

    if not comparisons:
        log.error("nothing to compare: no stage has predictions")
        return 1
    table = pd.DataFrame(comparisons)
    family = ["stage", "evaluated", "comparison"]  # all papers and borderline papers together
    table["delong_p_holm"] = table.groupby(family, sort=False)["delong_p"].transform(lambda p: stats.holm(p.to_numpy()))
    table["n_tests_in_family"] = table.groupby(family, sort=False)["delong_p"].transform(lambda p: int(p.notna().sum()))
    table["ci_excludes_zero"] = [excludes_zero(low, high) for low, high in zip(table["ci_low"], table["ci_high"])]
    table["rejects"], table["rejects_holm"] = table["delong_p"] < rules["alpha"], table["delong_p_holm"] < rules["alpha"]
    measures, by_seed_signs = pd.concat(summaries, ignore_index=True), pd.DataFrame(signs)
    if args.only:  # the other rows of the tables are the stored ones
        stored = {name: pd.read_csv(tables_dir / name) for name in ("protocol_comparisons.csv", "protocol_metrics.csv", "protocol_seed_signs.csv")}
        own = [table, measures[measures["setting"] == args.only], by_seed_signs[by_seed_signs["setting"] == args.only]]
        column = {"protocol_comparisons.csv": "stage", "protocol_metrics.csv": "setting", "protocol_seed_signs.csv": "setting"}
        merged = []
        for (name, previous), new in zip(stored.items(), own):
            if list(previous.columns) != list(new.columns):
                raise SystemExit(f"{name}: the columns of the stored table are not those computed now")
            merged.append(pd.concat([previous[previous[column[name]] != args.only], new], ignore_index=True))
        table, measures, by_seed_signs = merged
        log.info("--only %s: %d comparisons, %d rows of metrics and %d rows of seeds added to the stored tables", args.only, *map(len, own))
    table.to_csv(tables_dir / "protocol_comparisons.csv", index=False)
    measures.to_csv(tables_dir / "protocol_metrics.csv", index=False)
    by_seed_signs.to_csv(tables_dir / "protocol_seed_signs.csv", index=False)

    # ---- conclusions (a) and (b) of the article, read with the rule written in the config
    rows = []
    for (stage, evaluated, subset), group in table[table["stage"].isin(stages)].groupby(["stage", "evaluated", "subset"], sort=False):
        against = group[(group["comparison"] == "vs_reference") & group["model"].isin(hetero_variants)]
        closest = against.loc[against["difference"].idxmax()]
        rows.append({"stage": stage, "evaluated": evaluated, "subset": subset, "reading": "a",
                     "statement": f"no heterogeneous GNN is above {reference}", "outcome": reading(against["ci_low"], against["ci_high"], -1),
                     "variants": len(against), "significantly_below": int((against["ci_high"] < 0).sum()),
                     "significantly_above": int((against["ci_low"] > 0).sum()), "rejects_after_holm": int(against["rejects_holm"].sum()),
                     "closest": closest["model"], "closest_difference": closest["difference"], "closest_ci_low": closest["ci_low"],
                     "closest_ci_high": closest["ci_high"]})
        graph = group[(group["comparison"] == "hetero_vs_gcn") & group["model"].isin(["han", "hgt"])]
        if len(graph):
            closest = graph.loc[graph["difference"].idxmin()]
            rows.append({"stage": stage, "evaluated": evaluated, "subset": subset, "reading": "b",
                         "statement": "HAN and HGT are above the GCN", "outcome": reading(graph["ci_low"], graph["ci_high"], +1),
                         "variants": len(graph), "significantly_below": int((graph["ci_high"] < 0).sum()),
                         "significantly_above": int((graph["ci_low"] > 0).sum()), "rejects_after_holm": int(graph["rejects_holm"].sum()),
                         "closest": closest["model"], "closest_difference": closest["difference"], "closest_ci_low": closest["ci_low"],
                         "closest_ci_high": closest["ci_high"]})
    # reading (d) of the follow-up: the variant without embeddings above the reference (rule of the section `followup`)
    for _, row in table[(table["stage"] == FOLLOWUP) & (table["comparison"] == "vs_reference") & (table["model"] == followup["main"])].iterrows():
        rows.append({"stage": FOLLOWUP, "evaluated": row["evaluated"], "subset": row["subset"], "reading": "d",
                     "statement": f"{cfg['followup']['model']} without pretrained embeddings is above {reference}",
                     "outcome": reading([row["ci_low"]], [row["ci_high"]], +1), "variants": 1,
                     "significantly_below": int(row["ci_high"] < 0), "significantly_above": int(row["ci_low"] > 0),
                     "rejects_after_holm": int(row["rejects_holm"]), "closest": row["model"], "closest_difference": row["difference"],
                     "closest_ci_low": row["ci_low"], "closest_ci_high": row["ci_high"]})
    # readings (e) and (f) of the follow-up on the depth (rule of the section `depth_followup`)
    for letter, name in depth["readings"].items():
        of_cell = (table["stage"] == DEPTH) & (table["comparison"] == "vs_reference") & (table["model"] == f"{depth['model']}_{name}")
        for _, row in table[of_cell].iterrows():
            rows.append({"stage": DEPTH, "evaluated": row["evaluated"], "subset": row["subset"], "reading": letter,
                         "statement": DEPTH_STATEMENTS[letter].format(model=depth["model"], reference=reference),
                         "outcome": reading([row["ci_low"]], [row["ci_high"]], +1), "variants": 1,
                         "significantly_below": int(row["ci_high"] < 0), "significantly_above": int(row["ci_low"] > 0),
                         "rejects_after_holm": int(row["rejects_holm"]), "closest": row["model"], "closest_difference": row["difference"],
                         "closest_ci_low": row["ci_low"], "closest_ci_high": row["ci_high"]})
    readings = pd.DataFrame(rows)
    readings.to_csv(tables_dir / "protocol_readings.csv", index=False)

    shown = ["stage", "evaluated", "comparison", "model", "control", "control_setting", "subset", "n_papers", "auc_model", "auc_control",
             "difference", "ci_low", "ci_high", "delong_p", "delong_p_holm"]
    log.info("comparisons\n%s", table[shown].round(4).to_string(index=False))
    log.info("readings\n%s", readings.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
