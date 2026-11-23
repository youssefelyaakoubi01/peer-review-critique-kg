"""Phase 12: deposit of the data on Zenodo, as a draft. Never publishes.

    uv run python scripts/12b_zenodo.py                                  # lists the bundles and their size; writes nothing
    uv run python scripts/12b_zenodo.py --stage                          # packs the bundles in build/zenodo/
    uv run --env-file .env python scripts/12b_zenodo.py --upload --licence cc-by-4.0
    uv run --env-file .env python scripts/12b_zenodo.py --upload --licence cc-by-4.0 --deposition <id>   # resume

The data are too large for a git repository (files of several GB), so they go to Zenodo
through its REST API (token in ZENODO_TOKEN, scope deposit:write). A Zenodo record is a
flat list of at most 100 files: each folder is packed in one tar file (not compressed,
the tables and arrays already are). The upload creates a DRAFT deposit, sends the files
that are not there yet (checked by MD5) and sets the metadata. Publishing cannot be
undone and is left to the authors, on the page of the draft.

The titles, abstracts and one-line summaries of the papers of the years listed in
release.text_removed_years (their submission notes carry no licence on OpenReview) are
emptied in the copies that are deposited: tables of papers and RDF export.

Not deposited: the raw OpenReview records (data/raw: they hold the identity of the
authors of the papers; scripts/01_collect.py collects them again), the clones of the two
external archives (they are public), the annotation sample and its key (the human
annotation is not done), the bibliographic exports.
"""

import argparse
import gzip
import hashlib
import os
import re
import sys
import tarfile
from pathlib import Path

import requests

from src.utils.config import REPO_ROOT, load_config
from src.utils.runlog import setup_run_logging

API = "https://zenodo.org/api/deposit/depositions"
STAGE = REPO_ROOT / "build" / "zenodo"
CODE = "https://github.com/youssefelyaakoubi01/peer-review-critique-kg"

# name of the deposited file -> (what it holds, paths of the repository packed in it)
BUNDLES = {
    "interim_tables.tar": ("cleaned tables: papers, reviews with their initial scores, discussion, outcomes and split",
                           ["data/interim/*.parquet", "data/interim/*.stats.md"]),
    "llm_critiques.tar": ("critiques extracted and typed by the language model (ICLR 2024, 2025 and 2026), with the development and check sets",
                          ["data/interim/llm/full_v3", "data/interim/llm/full_v3_2026", "data/interim/llm/pilot", "data/interim/llm/check_v*",
                           "data/interim/llm/dev_v*"]),
    "llm_cache.tar": ("answers of the language model, one file per request: with it the extraction gives the same critiques again",
                      ["data/interim/llm/cache"]),
    "embeddings.tar": ("embeddings of the papers (SPECTER2) and of the texts (all-mpnet-base-v2)", ["data/interim/kg"]),
    "graphs_2024_2025.tar": ("graphs of settings A and B (PyTorch Geometric), node tables, targets and split",
                             ["data/processed/*.pt", "data/processed/*.parquet", "data/processed/graph_features.json", "data/processed/graph.stats.md"]),
    "graph_2026.tar": ("extended graph of the holdout year, node tables and targets", ["data/processed/holdout"]),
    "peer_review_kg.ttl.gz": ("the knowledge graph in RDF (Turtle), gzip", ["data/processed/peer_review_kg.ttl"]),
    "models.tar": ("saved models: every seed of the GNNs evaluated on the holdout year", ["data/processed/models"]),
    "predictions.tar": ("predictions per paper of every model and seed, and explanations per paper", ["results/predictions"]),
}

README = """# Data of the critique-level knowledge graph of peer review

Data of the study whose code and result files are at {code}.
Each `.tar` file unpacks at the root of that repository, at the paths the code expects.

| File | Content |
|---|---|
{rows}

`SHA256SUMS` gives the checksum of every file of this deposit.

## Sources and licences

The reviews, scores, discussions and decisions come from the public pages of ICLR 2024,
2025 and 2026 on OpenReview, where the review notes carry the licence CC BY 4.0. The
initial scores of ICLR 2024 and 2025 come from the archive of Kargaran et al.
(arXiv:2511.15462, https://github.com/papercopilot/iclr-insights, CC BY 4.0 according to
its README). The text of the submissions under review comes from the ICLR dataset of
González-Márquez and Kobak (arXiv:2404.08403, https://github.com/berenslab/iclr-dataset).
The labels of the critiques (aspect, severity, polarity, target, actionable) were produced
by an open-source language model and have not been validated by human annotators.

## Text removed

The submission notes of ICLR {years} carry no licence field on OpenReview (those of the
other years and every review note carry CC BY 4.0). For the papers
of {years}, the columns {columns} of `data/interim/papers.parquet` and
`data/interim/papers_initial.parquet` are empty in this deposit, and the RDF file gives
neither their title nor their abstract ({removed} papers). Their identifiers, keywords,
embeddings, reviews and critiques are kept. The other files are those the study used.

## Not in this deposit

The raw OpenReview records, which hold the identity of the authors of the papers (the
collection script downloads them again); the clones of the two external archives; the
sample prepared for the human annotation and its key. No table of this deposit has a
column that identifies an author, and reviewers appear only under the anonymous key that
OpenReview gives them; the texts of reviews and discussions are those published on the platform.
"""


def members(patterns: list[str]) -> list[Path]:
    """Files named by the patterns of a bundle, sorted."""
    found = []
    for pattern in patterns:
        for path in sorted(REPO_ROOT.glob(pattern)):
            found += sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
    if not found:
        raise FileNotFoundError(f"nothing matches {patterns}")
    return found


def digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def without_text(path: Path, release: dict) -> Path:
    """Copy of a table of papers in which the text columns of the years without licence are empty."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    table = pq.read_table(path)
    listed = pc.is_in(table["year"], value_set=pa.array(release["text_removed_years"], type=table["year"].type))
    for name in release["text_columns"]:
        if name in table.schema.names:
            column = pc.if_else(listed, pa.scalar("", type=table[name].type), table[name])
            table = table.set_column(table.schema.get_field_index(name), name, column)
    target = STAGE / "text_removed" / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, target, compression="zstd")
    return target


ARTICLE = re.compile(rb"^<[^>]*/article/([^>/]+)> a prkg:Article")
TEXT = re.compile(rb"^    dcterms:(?:abstract|title) ")
PREDICATE = re.compile(rb"^    (?!dcterms:)[A-Za-z]+:[A-Za-z]+ ")


def rdf_without_text(source: Path, target: Path, forums: set[bytes]) -> int:
    """Gzip copy of the Turtle file without the title and the abstract of the listed articles.
    rdflib writes the predicates of a subject one per indented line, the two text predicates
    first: from the first of them, lines are dropped up to the next predicate of the subject
    (the lines of a literal on several lines are not indented, so they are dropped with it).
    Returns the number of articles from which text was removed."""
    removed, listed, dropping = 0, False, False
    with source.open("rb") as lines, gzip.open(target, "wb", compresslevel=6) as packed:
        for line in lines:
            if dropping:
                if not PREDICATE.match(line):
                    continue
                listed = dropping = False
            elif line.startswith(b"<"):
                subject = ARTICLE.match(line)
                listed = bool(subject) and subject.group(1) in forums
            elif listed and TEXT.match(line):
                removed, dropping = removed + 1, True
                continue
            packed.write(line)
    return removed


def stage(cfg: dict, log) -> None:
    """Packs every bundle in build/zenodo/, with the description and the checksums of the deposit."""
    import pyarrow.parquet as pq
    release = cfg["release"]
    years = release["text_removed_years"]
    papers = pq.read_table(REPO_ROOT / "data/interim/papers.parquet", columns=["forum_id", "year"]).to_pandas()
    forums = {forum.encode() for forum in papers.loc[papers["year"].isin(years), "forum_id"]}
    removed = None
    STAGE.mkdir(parents=True, exist_ok=True)
    for name, (_, patterns) in BUNDLES.items():
        target, files = STAGE / name, members(patterns)
        if name.endswith(".gz"):   # always written again: it gives the number of papers whose text is removed
            removed = rdf_without_text(files[0], target, forums)
        elif target.is_file() and target.stat().st_mtime > max(f.stat().st_mtime for f in files):
            log.info("up to date: %s", name)
            continue
        else:
            with tarfile.open(target, "w") as tar:
                for path in files:
                    arcname = path.relative_to(REPO_ROOT).as_posix()
                    if arcname in ("data/interim/papers.parquet", "data/interim/papers_initial.parquet"):
                        path = without_text(path, release)
                    tar.add(path, arcname=arcname, recursive=False)
        log.info("packed %s: %d files, %.2f GB", name, len(files), target.stat().st_size / 1e9)
    rows = "\n".join(f"| `{name}` | {what} |" for name, (what, _) in BUNDLES.items())
    (STAGE / "README.md").write_text(README.format(
        code=CODE, rows=rows, years=", ".join(map(str, years)), removed=removed,
        columns=", ".join(f"`{name}`" for name in release["text_columns"])), encoding="utf-8")
    names = [*BUNDLES, "README.md"]
    (STAGE / "SHA256SUMS").write_text("".join(f"{digest(STAGE / n, 'sha256')}  {n}\n" for n in names), encoding="utf-8")
    log.info("staged in %s: %.2f GB", STAGE.relative_to(REPO_ROOT), sum((STAGE / n).stat().st_size for n in names) / 1e9)


def metadata(cfg: dict, licence: str) -> dict:
    release = cfg["release"]
    return {"metadata": {
        "upload_type": "dataset", "title": release["title"], "description": release["description"],
        "creators": release["creators"], "license": licence, "access_right": "open", "keywords": release["keywords"],
        "related_identifiers": [{"identifier": CODE, "relation": "isSupplementTo", "resource_type": "software"}]}}


def upload(cfg: dict, licence: str, deposition: str | None, log) -> int:
    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        log.error("ZENODO_TOKEN is not set: run with `uv run --env-file .env`")
        return 1
    names = [*BUNDLES, "README.md", "SHA256SUMS"]
    missing = [n for n in names if not (STAGE / n).is_file()]
    if missing:
        log.error("not staged yet (run --stage first): %s", missing)
        return 1
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {token}"
    answer = s.get(f"{API}/{deposition}", timeout=60) if deposition else s.post(API, json={}, timeout=60)
    answer.raise_for_status()
    draft = answer.json()
    if draft.get("submitted"):
        log.error("deposit %s is already published; a published record is not modified by this script", draft["id"])
        return 1
    present = {f["filename"]: f["checksum"] for f in draft.get("files", [])}
    log.info("draft %s, %d file(s) already there", draft["id"], len(present))
    for name in names:
        path = STAGE / name
        if present.get(name, "").removeprefix("md5:") == digest(path, "md5"):
            log.info("already uploaded: %s", name)
            continue
        with path.open("rb") as handle:
            sent = s.put(f"{draft['links']['bucket']}/{name}", data=handle, timeout=None)
        sent.raise_for_status()
        if sent.json()["checksum"].removeprefix("md5:") != digest(path, "md5"):
            log.error("checksum of %s differs after upload", name)
            return 1
        log.info("uploaded %s (%.2f GB)", name, path.stat().st_size / 1e9)
    s.put(f"{API}/{draft['id']}", json=metadata(cfg, licence), timeout=60).raise_for_status()
    log.info("metadata set (licence %s). DRAFT, not published: %s", licence, draft["links"].get("html", draft["id"]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stage", action="store_true", help="pack the bundles in build/zenodo/")
    parser.add_argument("--upload", action="store_true", help="send the staged files to a draft deposit")
    parser.add_argument("--licence", help="licence identifier of the deposit on Zenodo (required with --upload)")
    parser.add_argument("--deposition", help="identifier of an existing draft to complete")
    args = parser.parse_args()
    cfg = load_config()
    log = setup_run_logging("12b_zenodo", cfg["paths"]["logs"])
    if args.upload and not args.licence:
        parser.error("--upload needs --licence")
    if not (args.stage or args.upload):
        total = 0
        for name, (what, patterns) in BUNDLES.items():
            files = members(patterns)
            size = sum(f.stat().st_size for f in files)
            total += size
            log.info("%-24s %7.2f GB  %7d files  %s", name, size / 1e9, len(files), what)
        log.info("total before packing: %.2f GB in %d bundles (the RDF file is smaller once compressed)", total / 1e9, len(BUNDLES))
        return 0
    if args.stage:
        stage(cfg, log)
    return upload(cfg, args.licence, args.deposition, log) if args.upload else 0


if __name__ == "__main__":
    sys.exit(main())
