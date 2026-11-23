# Archive

Snapshot of the development repository at commit `5f20c3aab7707112faca35b9f12b5db75908dc30`, without its history.

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
bibliographic exports used for the related work, and the data (collected records, critiques, embeddings, graphs and saved models; `data/` holds the folder structure only).
The tests that read the manuscript are skipped in this archive, and so are, without the data,
the anti-leakage tests that run on the real tables and graphs (those on synthetic inputs run).
