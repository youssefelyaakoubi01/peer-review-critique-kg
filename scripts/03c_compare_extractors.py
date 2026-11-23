"""Agreement between two extraction runs on the same reviews (two models, same prompts).

    uv run python scripts/03c_compare_extractors.py --reference check_v3 --other check_v3_deepseek

The units of a review (lines, then sentences) do not depend on the model, so the two
runs can be compared unit by unit:
  - fate of each unit: in a critique, ignored, or set aside as written after the rebuttal;
  - segmentation: critiques of one run found in the other with exactly the same units;
  - labels (aspect, severity, polarity, target, actionable) of the critiques found in both;
  - per review, the counts a model reads: critiques, and critiques by severity and polarity.

Outputs in results/tables/: llm_extractors_<reference>_vs_<other>.md, _summary.csv,
_labels.csv, _counts.csv.
"""

import argparse
import json
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from src.collect import report
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

LABELS = ("aspect", "severity", "polarity", "target", "actionable")
COUNTED = {"severity": ("blocking", "major", "minor"), "polarity": ("negative", "positive", "neutral")}


def load(run_dir) -> tuple[pd.DataFrame, pd.DataFrame]:
    critiques, audit = pd.read_parquet(run_dir / "critiques.parquet"), pd.read_parquet(run_dir / "audit.parquet")
    critiques["unit_set"] = critiques["units"].map(lambda units: tuple(sorted(int(u) for u in units)))
    return critiques, audit.set_index("review_id")


def unit_fates(critiques: pd.DataFrame, audit: pd.Series) -> dict[int, str]:
    fates = {unit: "ignored" for unit in range(1, int(audit["n_units"]) + 1)}
    for unit in audit["post_rebuttal_units"]:
        fates[int(unit)] = "post_rebuttal"
    for units in critiques["unit_set"]:
        for unit in units:
            fates[unit] = "critique"
    return fates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--reference", required=True, help="run directory under data/interim/llm")
    parser.add_argument("--other", required=True)
    parser.add_argument("--extrapolate-to", type=int, help="number of reviews the cost and time of `other` are extrapolated to")
    args = parser.parse_args()
    cfg = load_config()
    log = setup_run_logging(f"03c_compare_extractors_{args.other}", cfg["paths"]["logs"])
    (ref, ref_audit), (other, other_audit) = load(cfg["paths"]["llm"] / args.reference), load(cfg["paths"]["llm"] / args.other)

    failed = lambda audit: audit["segment_failed"] | audit["type_failed"]  # noqa: E731
    common = sorted(set(ref_audit.index[~failed(ref_audit)]) & set(other_audit.index[~failed(other_audit)]))
    ref, other = ref[ref["review_id"].isin(common)], other[other["review_id"].isin(common)]

    # ---- units
    fates = []
    for review_id in common:
        a = unit_fates(ref[ref["review_id"] == review_id], ref_audit.loc[review_id])
        b = unit_fates(other[other["review_id"] == review_id], other_audit.loc[review_id])
        if a.keys() != b.keys():
            raise ValueError(f"review {review_id}: the two runs do not have the same units")
        fates += [(a[unit], b[unit]) for unit in a]
    fates = pd.DataFrame(fates, columns=["reference", "other"])
    confusion = pd.crosstab(fates["reference"], fates["other"])

    # ---- segmentation and labels
    merged = ref.merge(other, on=["review_id", "unit_set"], suffixes=("_reference", "_other"))
    label_rows = []
    for label in LABELS:
        a, b = merged[f"{label}_reference"].astype(str), merged[f"{label}_other"].astype(str)
        label_rows.append({"label": label, "critiques_compared": len(merged), "agreement": round(float((a == b).mean()), 4),
                           "cohen_kappa": round(float(cohen_kappa_score(a, b)), 4)})
    labels = pd.DataFrame(label_rows)

    # ---- per-review counts read by the models
    def counts(critiques: pd.DataFrame) -> pd.DataFrame:
        table = pd.DataFrame({"critiques": critiques.groupby("review_id").size()})
        for label, values in COUNTED.items():
            for value in values:
                table[f"{label}_{value}"] = critiques[critiques[label] == value].groupby("review_id").size()
        table["negative_blocking_or_major"] = critiques[(critiques["polarity"] == "negative")
                                                        & critiques["severity"].isin(["blocking", "major"])].groupby("review_id").size()
        return table.reindex(common).fillna(0)

    a, b = counts(ref), counts(other)
    count_rows = [{"count_per_review": column, "mean_reference": round(float(a[column].mean()), 3),
                   "mean_other": round(float(b[column].mean()), 3),
                   "pearson": round(float(np.corrcoef(a[column], b[column])[0, 1]), 4),
                   "share_of_reviews_equal": round(float((a[column] == b[column]).mean()), 4)} for column in a.columns]
    count_table = pd.DataFrame(count_rows)

    summary = pd.DataFrame([
        ("reviews in both runs", len(set(ref_audit.index) & set(other_audit.index))),
        ("reviews segmented and typed by both", len(common)),
        (f"failures of {args.reference} (segmentation or typing)", int(failed(ref_audit).sum())),
        (f"failures of {args.other} (segmentation or typing)", int(failed(other_audit).sum())),
        ("units compared", len(fates)),
        ("share of units with the same fate (critique / ignored / post-rebuttal)", round(float((fates["reference"] == fates["other"]).mean()), 4)),
        (f"critiques of {args.reference}", len(ref)),
        (f"critiques of {args.other}", len(other)),
        ("critiques with exactly the same units in both runs", len(merged)),
        (f"share of the critiques of {args.reference} found in {args.other}", round(len(merged) / len(ref), 4)),
        (f"share of the critiques of {args.other} found in {args.reference}", round(len(merged) / len(other), 4)),
    ], columns=["metric", "value"])

    # ---- cost and time of the other run (hosted API), from its run statistics
    stats = json.loads((cfg["paths"]["llm"] / args.other / "run_stats.json").read_text(encoding="utf-8"))
    seconds, cost = sum(p["seconds"] for p in stats["passes"]), stats["totals"].get("cost_usd")
    extra = [(f"{args.other}: model served", "; ".join(stats.get("served") or [stats["model"]])),
             (f"{args.other}: reviews, seconds, concurrency", f"{stats['reviews']}, {seconds:.1f}, {stats['concurrency']}")]
    if cost is not None:
        totals = stats["totals"]
        extra += [(f"{args.other}: cost of the run (USD)", round(cost, 4)),
                  (f"{args.other}: share of the prompt tokens served from the provider's cache", round(totals["prompt_cache_hit_tokens"] / totals["prompt_tokens"], 3))]
    if args.extrapolate_to:
        ratio = args.extrapolate_to / stats["reviews"]
        extra.append((f"{args.other}: time extrapolated to {args.extrapolate_to} reviews (hours, same pace)", round(seconds * ratio / 3600, 2)))
        if cost is not None:
            extra.append((f"{args.other}: cost extrapolated to {args.extrapolate_to} reviews (USD, same prices and cache share)", round(cost * ratio, 1)))
    summary = pd.concat([summary.astype({"value": object}), pd.DataFrame(extra, columns=["metric", "value"])], ignore_index=True)

    tables_dir = cfg["paths"]["tables"]
    prefix = f"llm_extractors_{args.reference}_vs_{args.other}"
    summary.to_csv(tables_dir / f"{prefix}_summary.csv", index=False)
    labels.to_csv(tables_dir / f"{prefix}_labels.csv", index=False)
    count_table.to_csv(tables_dir / f"{prefix}_counts.csv", index=False)
    text = "\n".join([
        f"# Two extraction runs on the same reviews: `{args.reference}` (reference) and `{args.other}`", "",
        report.to_markdown(summary.astype({"value": object})), "",
        "## Fate of each unit (rows: reference, columns: other)", "",
        report.to_markdown(confusion.reset_index()), "",
        "## Labels of the critiques that have the same units in both runs", "",
        report.to_markdown(labels), "",
        "## Counts per review", "",
        report.to_markdown(count_table), "",
    ])
    (tables_dir / f"{prefix}.md").write_text(text, encoding="utf-8")
    log.info("report written to %s\n%s", tables_dir / f"{prefix}.md", text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
