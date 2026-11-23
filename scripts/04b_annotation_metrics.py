"""Phase 4: agreement between the annotators and labels of the LLM against their consensus.

    uv run python scripts/04b_annotation_metrics.py

To run once the files data/annotation/to_annotate_<annotator>.csv are filled.

1. Agreement between the two annotators: raw agreement and Cohen's kappa per label.
2. Their disagreements are written to data/annotation/disagreements.csv, with an empty
   `consensus` column that the annotators fill together. Nothing is settled here.
3. The labels of the LLM are scored against the consensus (precision, recall, F1 per
   category, confusion matrices). While disagreements are open, the scores only cover
   the items on which the annotators agree, and the report says so.

Outputs: results/tables/annotation_*.csv and annotation_report.md.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from src.collect import report
from src.eval import annotation
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

DISAGREEMENTS = "disagreements.csv"


def load_resolutions(path: Path, disagreements: pd.DataFrame, log) -> pd.DataFrame | None:
    """Consensus values already filled in the disagreement file; the file is (re)written
    as long as nothing is filled in it."""
    if path.exists():
        resolutions = annotation.read_resolutions(path)
        if len(resolutions):
            log.info("%s: %d of %d disagreements settled", path.name, len(resolutions), len(disagreements))
            return resolutions
    disagreements.to_csv(path, index=False, encoding=annotation.ENCODING)
    log.info("%d disagreements written to %s (column `consensus` to fill)", len(disagreements), path)
    return None


def write_report(tables_dir: Path, names: tuple[str, str], agreement: pd.DataFrame,
                 n_disagreements: int, scores: dict[str, pd.DataFrame]) -> str:
    summary = scores["summary"]
    still_open = int(summary["items_without_consensus"].sum())
    text = [
        "# Human validation of the critique labels", "",
        f"Annotators `{names[0]}` and `{names[1]}`, {int(agreement['items'].iloc[0])} critiques "
        "(stratified sample, `results/tables/annotation_sample_strata.csv`).", "",
        "## Agreement between the annotators", "", report.to_markdown(agreement), "",
        "## Labels of the LLM against the consensus", "",
        f"The annotators differ on {n_disagreements} (item, label) pairs. ",
    ]
    if still_open:
        text += [f"**{still_open} of them are not settled yet: the scores below only cover the items with a "
                 "consensus, which are easier than the others. They are provisional.**", ""]
    else:
        text += ["All of them are settled: the consensus covers every item.", ""]
    text += ["`sample`: figures on the annotated sample, in which rare categories are over-represented. "
             "`corpus`: the same figures weighted by the sampling weights, an estimate for the whole corpus. "
             "Macro F1 is the mean over the categories present in the consensus.", "",
             report.to_markdown(summary), "",
             "### Per category", "", report.to_markdown(scores["categories"]), ""]
    for label in annotation.LABELS:
        text += [f"### Confusion matrix: {label} (rows: consensus, columns: LLM)", "",
                 report.to_markdown(scores[f"confusion_{label}"]), ""]
    (tables_dir / "annotation_report.md").write_text("\n".join(text), encoding="utf-8")
    return "\n".join(text)


def main() -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--annotation-dir", type=Path, default=cfg["paths"]["annotation"])
    parser.add_argument("--tables-dir", type=Path, default=cfg["paths"]["tables"])
    args = parser.parse_args()
    log = setup_run_logging("04b_annotation_metrics", cfg["paths"]["logs"])

    names = tuple(cfg["annotation"]["annotators"])
    if len(names) != 2:
        raise SystemExit(f"the agreement is computed between two annotators, the config names {len(names)}")
    key = pd.read_parquet(args.annotation_dir / "sample_key.parquet")
    item_ids = list(key["item_id"])
    paths = [args.annotation_dir / f"to_annotate_{name}.csv" for name in names]
    try:
        first, second = (annotation.read_annotations(path, item_ids) for path in paths)
    except ValueError as exc:
        raise SystemExit(f"annotations not usable yet: {exc}") from exc

    args.tables_dir.mkdir(parents=True, exist_ok=True)
    agreement = annotation.agreement_table(first, second)
    agreement.to_csv(args.tables_dir / "annotation_agreement.csv", index=False)

    items = annotation.read_csv(paths[0])[["item_id", "critique", "context"]]
    disagreements = annotation.disagreement_table(first, second, names, items)
    try:
        resolutions = load_resolutions(args.annotation_dir / DISAGREEMENTS, disagreements, log)
        consensus = annotation.consensus_labels(first, second, resolutions)
    except ValueError as exc:
        raise SystemExit(f"disagreement file not usable: {exc}") from exc

    scores = annotation.llm_scores(consensus, key)
    for name, table in scores.items():
        table.to_csv(args.tables_dir / f"annotation_llm_{name}.csv", index=False)
    print(write_report(args.tables_dir, names, agreement, len(disagreements), scores))
    log.info("items=%d disagreements=%d still_open=%d tables=%s", len(item_ids), len(disagreements),
             int(scores["summary"]["items_without_consensus"].sum()), args.tables_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
