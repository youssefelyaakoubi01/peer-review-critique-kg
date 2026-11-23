# Archive

Snapshot of the development repository at commit `63091551bdfb8f028360e634545cb22a22cef4e6`, without its history.

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
bibliographic exports used for the related work, and the data (deposited separately, see README.md; `data/` holds the folder structure only).
The tests that read the manuscript are skipped in this archive, and so are, without the data,
the anti-leakage tests that run on the real tables and graphs (those on synthetic inputs run).
