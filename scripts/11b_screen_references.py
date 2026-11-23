"""Phase 11: first screening of a Scopus export for the related work. Calls no service.

    uv run python scripts/11b_screen_references.py

Reads the Scopus exports (CSV with abstracts) found in paper/refs/ or at the root of the
repository (export_*.csv) and writes paper/refs/shortlist.csv: the records whose TITLE or
author keywords are about peer review of scientific papers, each with the themes of the
related work it matches. A record that only mentions "peer-reviewed" literature in its
abstract (systematic reviews) is left out. The rules are the regular expressions below;
nothing is judged by a model. The shortlist is a proposal: the author validates it, and
only validated and verified records enter paper/references.bib.
"""

import re
import sys

import pandas as pd

from src.utils.config import REPO_ROOT, load_config
from src.utils.runlog import setup_run_logging

REFS = REPO_ROOT / "paper" / "refs"
# The record is about peer review of scientific work: looked for in the title and the author keywords only.
CORE = (r"peer[- ]review(?!ed)|openreview|open review|review(?:er)?s?['’]? (?:comment|report|text|score|rating|assignment)|referee report|rebuttal"
        r"|meta-?review|paper acceptance|acceptance (?:prediction|decision)|(?:scientific|scholarly|academic|paper|manuscript) review(?!ed)"
        r"|review generation|automat\w+ (?:scientific |paper |peer )?review(?:ing)?\b|reviewer")
# Themes of the related work: looked for in the title, the abstract and the keywords.
THEMES = {
    "decision_prediction": r"(?:accept\w*|reject\w*|decision\w*|outcome\w*)\W+(?:\w+\W+){0,3}(?:predict\w*|classif\w*|forecast\w*)"
                           r"|(?:predict\w*|classif\w*|forecast\w*)\W+(?:\w+\W+){0,3}(?:accept\w*|reject\w*|decision\w*|outcome\w*)",
    "score_prediction": r"(?:score|rating)s?\W+(?:\w+\W+){0,3}predict\w*|predict\w*\W+(?:\w+\W+){0,3}(?:score|rating)s?",
    "review_text_analysis": r"aspect|argument\w* mining|sentiment|criticism|critique|weakness|constructive|review quality|helpful",
    "rebuttal_discussion": r"rebuttal|author response|meta-?review|discussion phase|score change",
    "llm": r"large language model|\bllms?\b|chatgpt|\bgpt\b|generative ai|language model",
    "graph": r"graph neural|knowledge graph|heterogeneous graph|graph convolution|graph attention",
    "explainability": r"explainab\w*|interpretab\w*",
    "reliability_bias": r"consisten\w*|arbitrar\w*|disagree\w*|inter-rater|borderline|\bbias\w*|fairness|noise",
    "dataset": r"dataset|corpus|benchmark",
}
COLUMNS = ["Authors", "Title", "Year", "Source title", "Document Type", "DOI", "Cited by", "Author Keywords", "Abstract", "EID"]


def main() -> int:
    cfg = load_config()
    log = setup_run_logging("11b_screen_references", cfg["paths"]["logs"])
    exports = sorted([*REFS.glob("*.csv"), *REPO_ROOT.glob("export_*.csv")])
    exports = [path for path in exports if path.name != "shortlist.csv"]
    if not exports:
        log.error("no Scopus export found in %s or at the root of the repository (export_*.csv)", REFS.relative_to(REPO_ROOT))
        return 1
    records = pd.concat([pd.read_csv(path, encoding="utf-8-sig", dtype=str) for path in exports], ignore_index=True).fillna("")
    total = len(records)
    records = records.drop_duplicates(subset="EID")
    log.info("%d records in %d export(s), %d distinct", total, len(exports), len(records))

    head = (records["Title"] + " ; " + records["Author Keywords"]).str.lower()
    everything = (records["Title"] + " ; " + records["Author Keywords"] + " ; " + records["Abstract"]).str.lower()
    kept = records[head.str.contains(CORE, regex=True)].copy()
    for theme, pattern in THEMES.items():
        kept[theme] = everything[kept.index].str.contains(pattern, regex=True)
    kept["themes"] = kept[list(THEMES)].apply(lambda row: ", ".join(theme for theme in THEMES if row[theme]), axis=1)
    kept["n_themes"] = kept[list(THEMES)].sum(axis=1)
    kept["cited_by"] = pd.to_numeric(kept["Cited by"], errors="coerce").fillna(0).astype(int)
    kept = kept.sort_values(["n_themes", "cited_by"], ascending=False)
    log.info("%d records about peer review in their title or author keywords (%d left out)", len(kept), len(records) - len(kept))
    for theme in THEMES:
        log.info("  %-22s %d", theme, int(kept[theme].sum()))
    log.info("  without DOI: %d; by type: %s", int((kept["DOI"] == "").sum()), kept["Document Type"].value_counts().to_dict())

    REFS.mkdir(parents=True, exist_ok=True)
    target = REFS / "shortlist.csv"
    kept[[*[column for column in COLUMNS if column != "Abstract"], "themes", "Abstract"]].to_csv(target, index=False)
    log.info("written: %s", target.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
