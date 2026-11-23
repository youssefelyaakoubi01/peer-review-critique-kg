"""Phase 12: tree of the public archive of the study. Uploads nothing.

    uv run python scripts/12_release.py --out build/public/peer-review-critique-kg

Writes, in the directory given, the files of the current commit (code, tests,
configuration, result files, verified references) without the history, plus
    ARCHIVE.md    what the archive holds and what it does not
    SHA256SUMS    checksum of every file
Left out: the manuscript (paper/main.tex, paper/sections, paper/figures, paper/main.pdf),
the lab notebook and the instructions of the development repository. The data are not in
this tree: they are not tracked by git (data/ holds the folder structure only).

The working tree must be clean, so that the archive is exactly one commit. A `.git`
folder already present in the output directory is kept: a new release becomes a new
commit of the public repository. The deposit itself is made by the authors.
"""

import argparse
import hashlib
import io
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from src.utils.config import REPO_ROOT, load_config
from src.utils.runlog import setup_run_logging

# Paths of the development repository that are not part of the public archive.
EXCLUDED = ("JOURNAL.md", "CLAUDE.md", "paper/main.tex", "paper/main.pdf", "paper/sections/", "paper/figures/")

ARCHIVE = """# Archive

Snapshot of the development repository at commit `{commit}`, without its history.

| Path | Content |
|---|---|
| `configs/`, `src/`, `scripts/`, `tests/` | configuration, versioned prompts, code and tests |
| `results/tables/`, `results/figures/` | result files and figures, and `results/RESULTS_SUMMARY.md` generated from them |
| `paper/references.yaml`, `paper/references.json`, `paper/references.bib` | references of the article, each fetched from Crossref or arXiv |
| `paper/generated/` | numbers quoted in the article, each with the result file it is read in, and the reference list |
| `data/annotation/GUIDE.md` | annotation guide for the human validation of the labels |
| `uv.lock`, `envs/` | pinned packages of the main environment and of the two auxiliary ones |
| `SHA256SUMS` | checksum of every file |

Not included: the manuscript, the lab notebook of the development repository, the
bibliographic exports used for the related work, and the data ({data}).
The tests that read the manuscript are skipped in this archive, and so are, without the data,
the anti-leakage tests that run on the real tables and graphs (those on synthetic inputs run).
"""
NO_DATA = "deposited separately, see README.md; `data/` holds the folder structure only"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.strip()


def excluded(name: str) -> bool:
    return any(name == path or (path.endswith("/") and name.startswith(path)) for path in EXCLUDED)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="directory of the public tree")
    args = parser.parse_args()
    cfg = load_config()
    log = setup_run_logging("12_release", cfg["paths"]["logs"])

    dirty = git("status", "--porcelain", "--untracked-files=no")
    if dirty:
        log.error("the working tree has uncommitted changes; commit first:\n%s", dirty)
        return 1
    commit = git("rev-parse", "HEAD")
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for child in out.iterdir():   # a previous release is replaced; the history of the public repository is kept
        if child.name != ".git":
            shutil.rmtree(child) if child.is_dir() else child.unlink()

    packed = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True).stdout
    kept = left = 0
    with tarfile.open(fileobj=io.BytesIO(packed)) as tar:
        for member in tar.getmembers():
            if member.isfile() and excluded(member.name):
                left += 1
            elif member.isfile():
                tar.extract(member, out, filter="data")
                kept += 1
    (out / "ARCHIVE.md").write_text(ARCHIVE.format(commit=commit, data=NO_DATA), encoding="utf-8")

    files = sorted(path for path in out.rglob("*") if path.is_file() and ".git" not in path.relative_to(out).parts)
    (out / "SHA256SUMS").write_text("".join(f"{sha256(path)}  {path.relative_to(out).as_posix()}\n" for path in files), encoding="utf-8")
    size = sum(path.stat().st_size for path in files)
    log.info("commit %s: %d files written to %s (%.1f MB), %d left out (%s)", commit[:7], kept, out, size / 1e6, left,
             ", ".join(EXCLUDED))
    log.info("written: ARCHIVE.md, SHA256SUMS (%d files)", len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
