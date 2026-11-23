# A critique-level knowledge graph of peer review

Code and result files of a study that asks what a knowledge graph of peer review, built
at the level of the individual critique, adds to the prediction of acceptance decisions.
Reviews of ICLR submissions (OpenReview) are split into critiques by an open-source
language model; each critique receives an aspect, a severity and a polarity; papers,
reviews, critiques, aspects and keyword concepts form a heterogeneous graph; heterogeneous
graph neural networks are compared with baselines that read the same information without
the graph. Models are trained on one year, tested on the next and confirmed on a third
year that was kept apart.

The results are in [`results/RESULTS_SUMMARY.md`](results/RESULTS_SUMMARY.md), which is
generated from the tables of `results/tables/`. In short, the main hypothesis is not
supported: the graph models did not do better than a logistic regression on the initial
ratings of the reviewers. The summary gives the figures, their intervals and the limits
of the study.

## What the models may read

Every model input exists before the author response. The decision, the meta-review, the
scores after the discussion, the fields of the platform that encode the outcome, later
versions of the paper, citations received and anything about the authors are never given
to a model. `tests/test_leakage.py` fails if one of them reaches a model input.

## Layout

| Path | Content |
|---|---|
| `configs/` | configuration (years, split, hyperparameter grids) and the versioned prompts |
| `src/collect`, `src/clean` | collection from OpenReview and cleaning |
| `src/llm` | segmentation and typing of the critiques |
| `src/kg` | construction of the graph, RDF export |
| `src/models` | baselines, homogeneous and heterogeneous GNNs |
| `src/explain` | occlusion and gradient explanations |
| `src/eval` | metrics, statistical tests, tables, figures, numbers quoted in the article |
| `src/paper` | verification of the references against Crossref and arXiv |
| `scripts/` | one entry point per phase; `scripts/reproduce_all.sh` lists the chain |
| `results/tables/`, `results/figures/` | result files (CSV, LaTeX, Markdown) and figures |
| `paper/` | verified references and the numbers quoted in the article, generated from the result files |
| `data/annotation/GUIDE.md` | annotation guide for the human validation of the labels |
| `tests/` | tests, among which the anti-leakage tests |

## Running

```bash
uv sync                               # Python 3.11, versions pinned in uv.lock
scripts/reproduce_all.sh              # lists the stages, what each needs and how long it took
scripts/reproduce_all.sh results      # tables, tests, figures and summary from the stored results
uv run pytest
```

The collection needs OpenReview credentials in a `.env` file. The extraction of the
critiques and the trainings need a GPU. The stages that train nothing were run again from
the stored result files; the complete chain has not been run again end to end in one
pass, and neither the answers of the language model nor the trainings on the GPU are
bit-for-bit reproducible.

## Data and licences

The reviews, scores and decisions come from the public pages of ICLR on OpenReview; the
review notes carry the licence CC BY 4.0. Initial scores come from the archive of
Kargaran et al. (arXiv:2511.15462, <https://github.com/papercopilot/iclr-insights>) and
the text of the submissions under review from the ICLR dataset of González-Márquez and
Kobak (arXiv:2404.08403, <https://github.com/berenslab/iclr-dataset>). Short excerpts of
reviews appear in the prompts and in some result files; they remain under the licence of
their source. No attempt is made to identify reviewers.

## Status

The human validation of the labels produced by the language model is prepared but not
done; until then the quality of these labels is not measured against human annotators.
