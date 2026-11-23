"""Phase 10: tables of the paper, figures and summary of the results. Trains nothing.

    uv run python scripts/10_consolidate.py

Reads the CSV files of results/tables/ written by the scripts of phases 1 to 9 and
writes:
    results/tables/paper/*.tex     booktabs tables of the paper
    results/figures/*.pdf          main results, borderline zone, labels of the critiques
    results/RESULTS_SUMMARY.md     key numbers of each research question, each with the
                                   file it is read in; negative results; limitations;
                                   index of every table and figure with its sources
No metric is computed here. The summary is not written if a sentence it holds is no
longer supported by the tables (src/eval/summary.py).
"""

import sys

from src.eval import paper, summary
from src.eval.sources import Sources
from src.utils.config import REPO_ROOT, load_config
from src.utils.runlog import setup_run_logging

SCRIPT = "scripts/10_consolidate.py"
# Tables and figures written by the scripts of the other phases: (file, content, script, tables or data read).
OTHER_ARTEFACTS = [
    ("results/tables/baselines.tex", "Baselines, every metric (appendix)", "scripts/06_baselines.py", ["results/predictions/baselines.parquet"]),
    ("results/tables/main_results.tex", "Baselines and GNNs, every metric (appendix)", "scripts/07b_main_results.py",
     ["results/predictions/baselines.parquet", "results/predictions/gnn.parquet"]),
    ("results/tables/ablations.tex", "Ablations, every metric (appendix)", "scripts/08b_ablation_results.py",
     ["results/predictions/ablations.parquet", "results/predictions/gnn.parquet", "results/predictions/baselines.parquet"]),
    ("results/figures/ablations.pdf", "RQ2: AUC difference of each ablation with the full graph", "scripts/08b_ablation_results.py",
     ["results/tables/ablations.csv"]),
    ("results/figures/explain_aspect_severity.pdf", "RQ3: importance of a critique by aspect and severity", "scripts/09b_explain_results.py",
     ["results/tables/explainability.csv"]),
    ("results/figures/explain_relations.pdf", "RQ3: importance of the relations", "scripts/09b_explain_results.py",
     ["results/tables/explainability_relations.csv"]),
    ("results/figures/explain_fidelity.pdf", "RQ3: fidelity of the explanations", "scripts/09b_explain_results.py",
     ["results/tables/explainability_fidelity.csv"]),
    *[(f"results/figures/explain_case_{case}.pdf", f"RQ3: case study, {case.replace('_', ' ')}", "scripts/09b_explain_results.py",
       ["results/tables/explainability_cases.csv"])
      for case in ("accepted_predicted_accept", "accepted_predicted_reject", "rejected_predicted_accept", "rejected_predicted_reject")],
]


def main() -> int:
    cfg = load_config()
    log = setup_run_logging("10_consolidate", cfg["paths"]["logs"])
    tables_dir, figures_dir = cfg["paths"]["tables"], cfg["paths"]["figures"]
    out_dir = tables_dir / "paper"
    out_dir.mkdir(parents=True, exist_ok=True)
    sources = Sources(tables_dir, REPO_ROOT)
    artefacts = []

    tables, figures = dict(paper.TABLES), dict(paper.FIGURES)
    if summary.has_holdout(sources, cfg):  # the frozen models have been run on the holdout year
        tables.update(paper.HOLDOUT_TABLES)
        figures.update(paper.HOLDOUT_FIGURES)
        tag = summary.holdout_tag(cfg)
        OTHER_ARTEFACTS.append((f"results/tables/{tag}.tex", "Holdout year: every model, every metric", "scripts/07d_holdout_results.py",
                                [f"results/predictions/{tag}.parquet"]))
    for name, (build, description) in tables.items():
        path = out_dir / f"{name}.tex"
        path.write_text(build(sources, cfg), encoding="utf-8")
        artefacts.append({"path": path.relative_to(REPO_ROOT).as_posix(), "description": description, "script": SCRIPT,
                          "sources": sources.take_used()})
    for name, (draw, description) in figures.items():
        path = figures_dir / f"{name}.pdf"
        draw(sources, cfg, path)
        artefacts.append({"path": path.relative_to(REPO_ROOT).as_posix(), "description": description, "script": SCRIPT,
                          "sources": sources.take_used()})
    for path, description, script, read in OTHER_ARTEFACTS:
        artefacts.append({"path": path, "description": description, "script": script, "sources": read})
    missing = [item["path"] for item in artefacts if not (REPO_ROOT / item["path"]).is_file()]
    missing += [path for item in artefacts for path in item["sources"] if not (REPO_ROOT / path).exists()]
    if missing:
        raise FileNotFoundError(f"files named in the index do not exist: {sorted(set(missing))}")
    log.info("%d tables and %d figures written; %d artefacts in the index", len(tables), len(figures), len(artefacts))

    text = summary.build(sources, cfg, artefacts)
    target = REPO_ROOT / "results" / "RESULTS_SUMMARY.md"
    target.write_text(text, encoding="utf-8")
    log.info("summary written: %s (%d lines), from %d result tables", target.relative_to(REPO_ROOT), text.count("\n"), len(sources.take_used()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
