"""Phase 11: verify the references of the paper against Crossref and arXiv.

    uv run python scripts/11c_references.py             # fetch what is new or changed
    uv run python scripts/11c_references.py --refresh   # fetch every reference again

Reads paper/references.yaml (key -> DOI or arXiv number, and an expected fragment of the
title), asks the public API of Crossref or of arXiv for each record (free, one request per
second, no personal data in the requests) and writes
    paper/references.json   the fetched records, the only source of the reference list
    paper/references.bib    the same records in BibTeX
A reference whose record does not carry the expected title is refused and the script
fails: no entry of the reference list is typed from memory (src/paper/references.py).
"""

import argparse
import json
import sys
import time

import yaml

from src.paper import references
from src.utils.config import REPO_ROOT, load_config
from src.utils.runlog import setup_run_logging

PAPER = REPO_ROOT / "paper"
PAUSE = 1.0   # seconds between two requests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refresh", action="store_true", help="fetch every reference again")
    args = parser.parse_args()
    cfg = load_config()
    log = setup_run_logging("11c_references", cfg["paths"]["logs"])

    declared = yaml.safe_load((PAPER / "references.yaml").read_text(encoding="utf-8"))
    stored = PAPER / "references.json"
    known = json.loads(stored.read_text(encoding="utf-8")) if stored.is_file() and not args.refresh else {}
    records, failed, fetched = {}, [], 0
    s = references.session()
    for key, entry in declared.items():
        if key in known:
            try:   # kept only if it still is the declared record
                references.check(key, entry, known[key])
                records[key] = known[key] | {"expected_title": entry["title"]}
                continue
            except ValueError:
                pass
        try:
            records[key] = references.fetch(key, entry, s)
            fetched += 1
            log.info("verified %-22s %s (%s)", key, records[key]["title"][:70], records[key]["year"])
        except Exception as error:   # a refused or unreachable record is reported, never guessed
            failed.append(key)
            log.error("REFUSED %s: %s", key, error)
        time.sleep(PAUSE)

    stored.write_text(json.dumps(records, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (PAPER / "references.bib").write_text(references.bibtex(records), encoding="utf-8")
    log.info("%d references declared, %d verified (%d fetched now), %d refused%s", len(declared), len(records), fetched,
             len(failed), f": {failed}" if failed else "")
    log.info("written: paper/references.json, paper/references.bib")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
