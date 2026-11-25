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
generated from the tables of `results/tables/`. In short, the answer has two parts.
As the study was first designed (text embeddings on the nodes, hyper-parameters selected
on a part of the training year), no graph model did better than a logistic regression on
the initial ratings of the reviewers, and this held on the third year. Checks of that
design, added afterwards with a design committed before their runs, show that this
negative result is not robust: with a wider hyper-parameter search, or without the text
embeddings, one heterogeneous model passes above the initial ratings on both later years,
by a few thousandths of AUC. The critiques themselves account for about one thousandth.
The summary gives the figures, their intervals and the limits of the study.

## What the models may read

In the main setting, the model inputs are restricted to what exists before the author
response. The decision, the meta-review, the scores after the discussion, the fields of
the platform that encode the outcome, later versions of the paper, citations received and
anything about the authors are never given to a model. `tests/test_leakage.py` fails if
one of them reaches a model input.

This control is not complete, and three points remain. The text of a review edited after
the author response is only available in its final state: the sentences attributed to the
discussion are set aside, and what an edit rewrote without saying so cannot be detected.
The vocabulary of keyword concepts is counted on the training and test years together, so
the graph used for training depends on the keywords of the test year, without any label
(`results/tables/kg_concept_scope.csv`); a graph whose vocabulary is counted on the
training year alone was built afterwards and gives the same conclusions
(`scripts/05f_inductive_graph.py`, `results/tables/protocol_readings.csv`). And the version of the submission texts used for
ICLR 2024 was committed after the decisions of that year, although it carries none
(`results/tables/input_dates.csv`).

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
| `data/annotation/GUIDE.md` | annotation guide prepared for a human validation of the labels, which was not carried out |
| `tests/` | tests, among which the anti-leakage tests |

## Protocol checks

`configs/default.yaml` holds, in its sections `protocol`, `followup` and `depth_followup`,
the design of the checks made after the test and holdout years had been read: what is
searched, with which budget, how a model is selected, what is compared and how a
conclusion is read. Each section was committed before its runs.
`scripts/07_run_protocol.sh` runs them (its step `depth` is the follow-up of the wider
search on HAN: depth and weight decay), `scripts/08_ablations.py --group followup` the
follow-up of the encoders, and
`scripts/07g_protocol_results.py` writes `results/tables/protocol_*.csv`.
`scripts/05e_model_dates.py` dates the weights of the pretrained models against the
reviews and decisions of each year (`results/tables/pretrained_model_dates.csv`).

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

The code is at <https://github.com/youssefelyaakoubi01/peer-review-critique-kg>, under the MIT licence (`LICENSE`). The data (cleaned tables, typed critiques, answers of the language model, embeddings,
graphs, saved models and predictions per paper) are archived on Zenodo under CC BY 4.0:
<https://doi.org/10.5281/zenodo.24544681> (version 3; the earlier versions are 10.5281/zenodo.24485276 and
10.5281/zenodo.24505447). Each archive unpacks at the root of this
repository; `scripts/12b_zenodo.py` is the script that built and deposited them.

The reviews, scores and decisions come from the public pages of ICLR on OpenReview; the
review notes carry the licence CC BY 4.0. Initial scores come from the archive of
Kargaran et al. (arXiv:2511.15462, <https://github.com/papercopilot/iclr-insights>) and
the text of the submissions under review from the ICLR dataset of González-Márquez and
Kobak (arXiv:2404.08403, <https://github.com/berenslab/iclr-dataset>). Short excerpts of
reviews appear in the prompts and in some result files; they remain under the licence of
their source. No attempt is made to identify reviewers.

## Status

The labels produced by the language model were not validated against human annotators:
their quality is not measured. The annotation guide and the scripts of phase 4 are kept
for whoever wants to do it.
