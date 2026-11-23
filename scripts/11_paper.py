"""Phase 11: numbers of the text of the paper, then its compilation. Trains nothing.

    uv run python scripts/11_paper.py                # macros, then paper/main.pdf
    uv run python scripts/11_paper.py --no-compile   # macros only

Reads the CSV files of results/tables/ and configs/default.yaml and writes
    paper/generated/numbers.tex    one LaTeX macro per number quoted in the text, each
                                   followed by the file it is read in (src/eval/numbers.py)
and, from the records verified by scripts/11c_references.py (paper/references.json),
    paper/generated/references.tex the reference list, in the order of first citation
then compiles paper/main.tex with latexmk and reports what is left to do in the text:
undefined references, lines that overflow, and the markers of missing citations, of the
pending human annotation and of the points to confirm.
"""

import argparse
import json
import re
import subprocess
import sys

from src.eval import numbers
from src.eval.sources import Sources
from src.paper import references
from src.utils.config import REPO_ROOT, load_config
from src.utils.runlog import setup_run_logging

PAPER = REPO_ROOT / "paper"
MARKERS = {r"\needcite": "citations to find", r"\pending": "results waiting for the human annotation", r"\toconfirm": "points to confirm"}


def write_numbers(cfg: dict, log) -> None:
    sources = Sources(cfg["paths"]["tables"], REPO_ROOT)
    macros = numbers.build(sources, cfg)
    target = PAPER / "generated" / "numbers.tex"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(numbers.render(macros), encoding="utf-8")
    files = sorted({source for _, read in macros.values() for source in read})
    log.info("%d macros written to %s, read in %d files", len(macros), target.relative_to(REPO_ROOT), len(files))


def body_texts() -> list[str]:
    """Texts of the paper in the order they are printed: the sections as main.tex includes them."""
    main = re.sub(r"(?<!\\)%.*", "", (PAPER / "main.tex").read_text(encoding="utf-8"))
    return [(PAPER / f"{name}.tex").read_text(encoding="utf-8") for name in re.findall(r"\\input\{(sections/[^}]+)\}", main)]


def write_references(log) -> None:
    records = json.loads((PAPER / "references.json").read_text(encoding="utf-8"))
    keys = references.cited_keys(body_texts())
    target = PAPER / "generated" / "references.tex"
    target.write_text(references.thebibliography(keys, records), encoding="utf-8")
    unused = sorted(set(records) - set(keys))
    log.info("%d references cited, written to %s; verified but not cited: %s", len(keys), target.relative_to(REPO_ROOT),
             ", ".join(unused) or "none")


def compile_paper(log) -> int:
    done = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], cwd=PAPER,
                          capture_output=True, encoding="utf-8", errors="replace")   # the output of TeX is not always UTF-8
    text = (PAPER / "main.log").read_text(encoding="utf-8", errors="replace") if (PAPER / "main.log").is_file() else ""
    if done.returncode:
        log.error("latexmk failed:\n%s", "\n".join(line for line in text.splitlines() if line.startswith("!") or line.startswith("l."))[:4000])
        return done.returncode
    undefined = sorted(set(re.findall(r"(?:Reference|Citation) `([^']+)' on page", text)))
    overfull = re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)[^\n]*", text)
    pages = re.search(r"Output written on main\.pdf \((\d+) pages", text)
    log.info("paper/main.pdf written (%s pages)", pages.group(1) if pages else "?")
    log.info("undefined references or citations: %s", ", ".join(undefined) or "none")
    log.info("overfull lines: %d%s", len(overfull), f" (largest {max(map(float, overfull)):.1f} pt)" if overfull else "")
    return 0


def report_markers(log) -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(PAPER.glob("sections/*.tex")))
    for marker, meaning in MARKERS.items():
        log.info("%s: %d (%s)", marker, len(re.findall(re.escape(marker) + r"(?![A-Za-z])", text)), meaning)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-compile", action="store_true", help="write the macros only")
    args = parser.parse_args()
    cfg = load_config()
    log = setup_run_logging("11_paper", cfg["paths"]["logs"])
    write_numbers(cfg, log)
    write_references(log)
    report_markers(log)
    return 0 if args.no_compile else compile_paper(log)


if __name__ == "__main__":
    sys.exit(main())
