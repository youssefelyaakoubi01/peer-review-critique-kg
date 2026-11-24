# Results summary

Written by `scripts/10_consolidate.py` from the files of `results/tables/`. Do not edit by hand: change the script or the text in `src/eval/summary.py` and run it again. Every number is followed by the file it is read in.

## Protocol

- **Data**: ICLR 2024 for training and validation, ICLR 2025 for the test. Split by year, never at random.
- **Papers with a decision** (withdrawn papers excluded): train 4,695 (39.6 % accepted); val 839 (37.4 % accepted); test 8,655 (42.5 % accepted). Source: `results/tables/clean_report_splits.csv`.
- **Borderline papers**: mean initial rating in [5.00, 6.25), the bins of the training papers whose acceptance rate lies between 0.2 and 0.8; 4,049 test papers. Source: `results/tables/borderline_definition.csv`, `results/tables/main_results.csv`.
- **Setting A**: what exists before the author response (initial scores, review text, critiques). **Setting B**: setting A plus the author responses.
- **Runs**: 5 seeds per model; an AUC is the mean over the seeds.
- **Intervals and tests**: 95 % confidence intervals by bootstrap over the papers (1,000 resamples), paired for a difference between two models; DeLong test on the probability averaged over the seeds. The intervals count the draw of the papers, not the variability between seeds.
- **Reading rule**: a difference is called *significant* when its confidence interval excludes zero. When the DeLong test does not reject at 0.05 although the interval excludes zero, the verdict says so: the interval is on the mean of the AUCs of the seeds, the test on the AUC of the probability averaged over the seeds. The tests of the sections RQ1 to *Holdout year* are given without correction for multiple comparisons; the section *Sensitivity analyses* gives the Holm correction within each table.

## Status

Final on ICLR 2024 and 2025: collection, cleaning, critique extraction, graph, baselines, GNNs, ablations, explanations.

Not available, hence no number below:

- **Human validation of the LLM labels** (phase 4): not done; no human annotation was made for this study. A sample of 500 critiques and the annotation files exist and were not annotated. Source: `results/tables/annotation_sample_strata.csv`.
- **Comparison of the explanations with the meta-reviews**: not done.

**How to read the sections below.** RQ1 to RQ4, the holdout year and the sensitivity analyses report the study as it was designed: graph models that read the embeddings of the texts, selected on a part of the training year. The section *Protocol checks*, added afterwards, tests this design; some of its checks contradict the main negative conclusion of the study, and it must be read with the sections that precede it.

## RQ1 — Does a heterogeneous GNN predict the decision better than the baselines?

Test year, all papers. Source: `results/tables/main_results.csv`, `results/tables/main_results_tests.csv`.

| Model | Setting | AUC | 95 % CI | AUC minus `scores_rating_lr` | 95 % CI | DeLong | Verdict |
|---|---|---|---|---|---|---|---|
| `majority` | A | 0.500 | [0.500, 0.500] | -0.3733 | [-0.3807, -0.3658] | p < 0.001 | significant |
| `scores_rating_lr` | A | 0.873 | [0.866, 0.881] | reference |  |  |  |
| `scores_all_lr` | A | 0.874 | [0.867, 0.881] | +0.0007 | [-0.0013, +0.0026] | p = 0.463 | not significant |
| `text_mlp` | A | 0.609 | [0.597, 0.621] | -0.2640 | [-0.2769, -0.2518] | p < 0.001 | significant |
| `text_scores_mlp` | A | 0.876 | [0.869, 0.883] | +0.0026 | [+0.0002, +0.0049] | p = 0.016 | significant |
| `text_scores_article_mlp` | A | 0.876 | [0.869, 0.883] | +0.0028 | [+0.0005, +0.0053] | p = 0.006 | significant |
| `critiques_lr` | A | 0.760 | [0.750, 0.770] | -0.1133 | [-0.1222, -0.1043] | p < 0.001 | significant |
| `scores_critiques_lr` | A | 0.873 | [0.865, 0.880] | -0.0007 | [-0.0032, +0.0019] | p = 0.622 | not significant |
| `scores_all_gbt` | A | 0.873 | [0.866, 0.880] | -0.0004 | [-0.0028, +0.0021] | p = 0.749 | not significant |
| `scores_critiques_gbt` | A | 0.874 | [0.866, 0.881] | +0.0002 | [-0.0024, +0.0028] | p = 0.878 | not significant |
| `gcn` | A | 0.831 | [0.823, 0.839] | -0.0425 | [-0.0481, -0.0366] | p < 0.001 | significant |
| `han+scores` | A | 0.859 | [0.851, 0.867] | -0.0144 | [-0.0187, -0.0101] | p < 0.001 | significant |
| `han` | A | 0.856 | [0.848, 0.864] | -0.0177 | [-0.0223, -0.0132] | p < 0.001 | significant |
| `hgt+scores` | A | 0.858 | [0.851, 0.866] | -0.0150 | [-0.0193, -0.0107] | p < 0.001 | significant |
| `hgt` | A | 0.858 | [0.850, 0.866] | -0.0152 | [-0.0198, -0.0108] | p < 0.001 | significant |
| `rgcn+scores` | A | 0.856 | [0.848, 0.864] | -0.0175 | [-0.0220, -0.0133] | p < 0.001 | significant |
| `rgcn` | A | 0.820 | [0.811, 0.829] | -0.0537 | [-0.0602, -0.0474] | p < 0.001 | significant |
| `han+scores` | B | 0.860 | [0.852, 0.867] | -0.0138 | [-0.0180, -0.0094] | p < 0.001 | significant |
| `han` | B | 0.854 | [0.847, 0.862] | -0.0191 | [-0.0237, -0.0144] | p < 0.001 | significant |
| `hgt+scores` | B | 0.857 | [0.850, 0.865] | -0.0162 | [-0.0206, -0.0118] | p < 0.001 | significant |
| `hgt` | B | 0.855 | [0.848, 0.863] | -0.0179 | [-0.0223, -0.0137] | p < 0.001 | significant |
| `rgcn+scores` | B | 0.856 | [0.848, 0.863] | -0.0177 | [-0.0222, -0.0135] | p < 0.001 | significant |
| `rgcn` | B | 0.825 | [0.817, 0.833] | -0.0483 | [-0.0541, -0.0421] | p < 0.001 | significant |

- **(a) Against the mean of the initial ratings: no.** All 12 heterogeneous GNN models (three architectures, with and without score statistics on the article node, settings A and B) are significantly below `scores_rating_lr`. The closest is `han+scores` in setting B: -0.0138 [-0.0180, -0.0094]; the farthest is `rgcn` in setting A: -0.0537. (`results/tables/main_results_tests.csv`)
- **What does better than the initial ratings alone.** Only `text_scores_mlp` and `text_scores_article_mlp`, which add the review text (and the article text) to the scores, are significantly above `scores_rating_lr`, by +0.0026 and +0.0028: a gain of less than 0.005 AUC, on all papers only (see RQ4).
- **(b) Against the text models: above the text alone, below the text with the scores.** `text_mlp` reaches 0.609; the confidence interval of every heterogeneous GNN lies above its interval (no paired test was computed for this pair). Every heterogeneous GNN is significantly below `text_scores_mlp` and `scores_critiques_lr` (columns `auc_minus_*` of `results/tables/main_results_tests.csv`).
- **(c) Against a homogeneous GNN: yes for HAN and HGT, no for R-GCN.** In setting A, graph alone, HAN and HGT are significantly above the GCN trained on the same graph without node and relation types, on all papers and on borderline papers; R-GCN is significantly below it on all papers.

Source: `results/tables/paired_comparisons.csv`.

| Model | Control | Split | Papers | AUC model | AUC control | Difference | 95 % CI | DeLong | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `hgt` | `gcn` | test | all | 0.8581 | 0.8308 | +0.0272 | [+0.0222, +0.0324] | p < 0.001 | significant |
| `hgt` | `gcn` | test | borderline | 0.6947 | 0.6610 | +0.0337 | [+0.0200, +0.0472] | p < 0.001 | significant |
| `han` | `gcn` | test | all | 0.8556 | 0.8308 | +0.0247 | [+0.0202, +0.0295] | p < 0.001 | significant |
| `han` | `gcn` | test | borderline | 0.6832 | 0.6610 | +0.0222 | [+0.0099, +0.0348] | p < 0.001 | significant |
| `rgcn` | `gcn` | test | all | 0.8196 | 0.8308 | -0.0112 | [-0.0164, -0.0058] | p < 0.001 | significant |
| `rgcn` | `gcn` | test | borderline | 0.6461 | 0.6610 | -0.0149 | [-0.0281, -0.0006] | p = 0.059 | interval excludes zero, test does not reject |

**Author responses (setting B) and score statistics on the article node.** No gain is measured from the author responses: for the main model (HGT), setting B minus setting A is -0.0028 [-0.0043, -0.0013], DeLong p = 0.391 (`results/tables/ablations.csv`). The other pairs of this table were not tested.

| Model | Test AUC, setting A | Test AUC, setting B |
|---|---|---|
| `rgcn` | 0.8196 | 0.8250 |
| `rgcn+scores` | 0.8558 | 0.8556 |
| `han` | 0.8556 | 0.8542 |
| `han+scores` | 0.8589 | 0.8595 |
| `hgt` | 0.8581 | 0.8554 |
| `hgt+scores` | 0.8583 | 0.8571 |

Source: `results/tables/main_results.csv`.

**Critique counts without the graph.** A model that reads the critique counts is set against its control of the same family that does not.

| Model | Control | Split | Papers | AUC model | AUC control | Difference | 95 % CI | DeLong | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `scores_critiques_lr` | `scores_all_lr` | test | all | 0.8726 | 0.8740 | -0.0014 | [-0.0033, +0.0005] | p = 0.154 | not significant |
| `scores_critiques_lr` | `scores_all_lr` | test | borderline | 0.7150 | 0.7190 | -0.0040 | [-0.0107, +0.0027] | p = 0.244 | not significant |
| `scores_critiques_lr` | `scores_all_lr` | val | all | 0.8894 | 0.8839 | +0.0055 | [-0.0003, +0.0120] | p = 0.070 | not significant |
| `scores_critiques_lr` | `scores_all_lr` | val | borderline | 0.7679 | 0.7584 | +0.0095 | [-0.0109, +0.0303] | p = 0.362 | not significant |
| `scores_critiques_gbt` | `scores_all_gbt` | test | all | 0.8735 | 0.8729 | +0.0006 | [-0.0014, +0.0028] | p = 0.553 | not significant |
| `scores_critiques_gbt` | `scores_all_gbt` | test | borderline | 0.7162 | 0.7138 | +0.0024 | [-0.0045, +0.0093] | p = 0.494 | not significant |
| `scores_critiques_gbt` | `scores_all_gbt` | val | all | 0.8890 | 0.8816 | +0.0073 | [+0.0011, +0.0140] | p = 0.031 | significant |
| `scores_critiques_gbt` | `scores_all_gbt` | val | borderline | 0.7586 | 0.7479 | +0.0107 | [-0.0107, +0.0339] | p = 0.334 | not significant |
| `critiques_lr` | `text_mlp` | test | all | 0.7600 | 0.6093 | +0.1507 | [+0.1366, +0.1654] | p < 0.001 | significant |
| `critiques_lr` | `text_mlp` | test | borderline | 0.6167 | 0.5345 | +0.0822 | [+0.0588, +0.1061] | p < 0.001 | significant |
| `critiques_lr` | `text_mlp` | val | all | 0.7915 | 0.6317 | +0.1598 | [+0.1092, +0.2085] | p < 0.001 | significant |
| `critiques_lr` | `text_mlp` | val | borderline | 0.6600 | 0.5915 | +0.0685 | [-0.0066, +0.1499] | p = 0.085 | not significant |

Source: `results/tables/paired_comparisons.csv`.

- The critique counts alone carry signal: `critiques_lr` is significantly above the review text alone (+0.1507 [+0.1366, +0.1654]).
- Added to the initial scores, they bring nothing measurable on the test year: no difference is significant, on all papers or on borderline papers.
- The gains seen on validation (+0.0055, +0.0073) are not found on the test year.

**Validation against test, and calibration.** The GNNs lose more AUC between validation and test than the score baselines, and are less well calibrated (expected calibration error, ECE).

| Model | Setting | Validation AUC | Test AUC | Test minus validation | Test ECE |
|---|---|---|---|---|---|
| `majority` | A | 0.5000 | 0.5000 | +0.0000 | 0.029 |
| `scores_rating_lr` | A | 0.8795 | 0.8733 | -0.0062 | 0.020 |
| `scores_all_lr` | A | 0.8839 | 0.8740 | -0.0099 | 0.014 |
| `text_mlp` | A | 0.6317 | 0.6093 | -0.0224 | 0.135 |
| `text_scores_mlp` | A | 0.8871 | 0.8759 | -0.0111 | 0.019 |
| `critiques_lr` | A | 0.7915 | 0.7600 | -0.0315 | 0.045 |
| `scores_critiques_lr` | A | 0.8894 | 0.8726 | -0.0168 | 0.009 |
| `gcn` | A | 0.8532 | 0.8308 | -0.0223 | 0.044 |
| `rgcn` | A | 0.8575 | 0.8196 | -0.0379 | 0.063 |
| `han` | A | 0.8736 | 0.8556 | -0.0180 | 0.048 |
| `hgt` | A | 0.8765 | 0.8581 | -0.0184 | 0.065 |
| `hgt+scores` | A | 0.8780 | 0.8583 | -0.0197 | 0.054 |
| `hgt` | B | 0.8739 | 0.8554 | -0.0185 | 0.057 |

Source: `results/tables/main_results.csv`.

**Robustness: withdrawn papers counted as rejections** (11,422 test papers). `hgt` 0.8885 against `scores_rating_lr` 0.9029: same order. No interval nor test was computed for this variant. Source: `results/tables/main_results_withdrawn_as_reject.csv`.

## RQ2 — Which nodes and relations contribute to the performance?

Ablations of `hgt` in setting A: one element removed, model trained again with the same hyper-parameters and 5 seeds. An element contributes when removing it lowers the test AUC with an interval that excludes zero. Source: `results/tables/ablations.csv`.

| Variant | Name | AUC ± std over seeds (all papers) | Minus full graph, 95 % CI | DeLong | Verdict | AUC ± std over seeds (borderline papers) | Minus full graph, 95 % CI | DeLong | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Full graph | `full` | 0.8582 ± 0.0006 | reference |  |  | 0.6951 ± 0.0009 | reference |  |  |
| No shares_concept edges | `no_shares_concept` | 0.8556 ± 0.0010 | -0.0026 [-0.0042, -0.0010] | p = 0.004 | significant | 0.6910 ± 0.0038 | -0.0041 [-0.0090, +0.0004] | p = 0.122 | not significant |
| No critique labels (text only) | `no_critique_labels` | 0.8561 ± 0.0021 | -0.0021 [-0.0031, -0.0012] | p < 0.001 | significant | 0.6911 ± 0.0036 | -0.0040 [-0.0066, -0.0012] | p < 0.001 | significant |
| No critique text (labels only) | `no_critique_text` | 0.8581 ± 0.0015 | -0.0002 [-0.0011, +0.0007] | p = 0.358 | not significant | 0.6940 ± 0.0022 | -0.0011 [-0.0038, +0.0016] | p = 0.166 | not significant |
| No critique nodes | `no_critiques` | 0.8334 ± 0.0069 | -0.0249 [-0.0287, -0.0210] | p < 0.001 | significant | 0.6590 ± 0.0062 | -0.0361 [-0.0484, -0.0258] | p < 0.001 | significant |
| No initial scores | `no_scores` | 0.5380 ± 0.0234 | -0.3202 [-0.3323, -0.3071] | p < 0.001 | significant | 0.5132 ± 0.0132 | -0.1819 [-0.2033, -0.1609] | p < 0.001 | significant |
| No scores, no critiques | `no_scores_no_critiques` | 0.5335 ± 0.0251 | -0.3248 [-0.3353, -0.3149] | p < 0.001 | significant | 0.5123 ± 0.0152 | -0.1829 [-0.2019, -0.1647] | p < 0.001 | significant |
| With author responses (setting B) | `with_responses` | 0.8554 ± 0.0030 | -0.0028 [-0.0043, -0.0013] | p = 0.391 | interval excludes zero, test does not reject | 0.6886 ± 0.0051 | -0.0065 [-0.0110, -0.0019] | p = 0.809 | interval excludes zero, test does not reject |

- **Initial scores: most of the performance.** Without them the AUC falls to 0.5380.
- **Critique nodes: a clear contribution**, -0.0249 on all papers and -0.0361 on borderline papers. Without them, HGT (0.8334) is at the level of the GCN (0.8308, `results/tables/main_results.csv`).
- **Typed labels of the critiques: a small contribution** (-0.0021). **Text of the critiques: none measured** (-0.0002): with the labels alone the model does as well as with the text added.
- **`shares_concept` edges: a small contribution** on all papers (-0.0026).
- **Author responses (setting B): no gain.** The AUC changes by -0.0028; the interval excludes zero but the DeLong test does not reject (p = 0.391).
- **Fragile differences.** The intervals do not count the variability between seeds (standard deviations in the table). For `no_critique_labels`, `with_responses`, the difference is smaller than twice the standard deviation between seeds of the variant: to be read with caution, although the interval excludes zero.

**Without the scores, the graph model fails.** It is significantly below a logistic regression on critique counts and below an MLP on the review text, although it reads the same critiques and the same text.

| Model | Control | Split | Papers | AUC model | AUC control | Difference | 95 % CI | DeLong | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `no_scores` | `critiques_lr` | test | all | 0.5380 | 0.7600 | -0.2220 | [-0.2357, -0.2077] | p < 0.001 | significant |
| `no_scores` | `critiques_lr` | test | borderline | 0.5132 | 0.6167 | -0.1035 | [-0.1269, -0.0797] | p < 0.001 | significant |
| `no_scores` | `text_mlp` | test | all | 0.5380 | 0.6093 | -0.0713 | [-0.0851, -0.0567] | p < 0.001 | significant |
| `no_scores` | `text_mlp` | test | borderline | 0.5132 | 0.5345 | -0.0212 | [-0.0431, +0.0026] | p = 0.179 | not significant |
| `no_scores_no_critiques` | `text_mlp` | test | all | 0.5335 | 0.6093 | -0.0758 | [-0.0881, -0.0638] | p < 0.001 | significant |
| `no_scores_no_critiques` | `text_mlp` | test | borderline | 0.5123 | 0.5345 | -0.0222 | [-0.0419, -0.0013] | p = 0.216 | interval excludes zero, test does not reject |

Source: `results/tables/ablations_paired.csv`.

- 3 of the 10 trainings without scores stopped early, with their best validation epoch at 1 or 2 (`results/tables/ablations_selection.csv`). Untested hypothesis: a training failure with hyper-parameters chosen for the model with scores, not a limit of the information held in the graph.
- Control: the full model trained again in phase 8 against the same model of phase 7, +0.0002 [-0.0001, +0.0004].

## RQ3 — Which critiques explain the predictions?

Explanations of `hgt` in setting A, seed 0, on 1,200 test papers (300 per group: accepted or rejected, borderline or not), weighted back to the test year. The explanations describe the model, not the area chairs. Importance of a critique by occlusion: logit of its paper with the critique minus logit without it (positive: pushes towards acceptance). Largest gap between a recomputed probability and the one stored in phase 7: 1.8e-07 (`results/tables/explainability_runs.csv`).

**Importance per critique, by polarity and severity** (mean, 95 % CI).

|  | All papers | Accepted papers | Rejected papers | Borderline papers |
|---|---|---|---|---|
| Positive critique | +0.0306 [+0.0285, +0.0332] | +0.0224 [+0.0209, +0.0240] | +0.0375 [+0.0336, +0.0422] | +0.0219 [+0.0206, +0.0234] |
| Neutral critique | +0.0155 [+0.0138, +0.0174] | +0.0105 [+0.0095, +0.0115] | +0.0196 [+0.0166, +0.0230] | +0.0108 [+0.0098, +0.0118] |
| Negative critique | +0.0033 [+0.0016, +0.0053] | -0.0052 [-0.0062, -0.0043] | +0.0090 [+0.0061, +0.0125] | -0.0045 [-0.0054, -0.0037] |
| Negative, blocking | +0.0028 [-0.0006, +0.0071] | -0.0049 [-0.0095, -0.0001] | +0.0058 [+0.0014, +0.0115] | -0.0062 [-0.0097, -0.0022] |
| Negative, major | +0.0011 [-0.0009, +0.0037] | -0.0086 [-0.0098, -0.0072] | +0.0068 [+0.0038, +0.0108] | -0.0079 [-0.0089, -0.0068] |
| Negative, minor | +0.0077 [+0.0059, +0.0097] | +0.0001 [-0.0009, +0.0011] | +0.0144 [+0.0110, +0.0182] | +0.0015 [+0.0004, +0.0026] |

Source: `results/tables/explainability.csv`.

**Negative critiques by aspect × severity.** A cell is read only when at least 20 explained papers hold such a critique; it *explains* the predictions when its interval excludes zero.

| Papers | Cells | Read (≥ 20 papers) | Interval excludes zero | of which negative | of which positive | Not read, although their interval excludes zero |
|---|---|---|---|---|---|---|
| Accepted | 24 | 17 | 10 | 8 | 2 | 4 |
| Rejected | 24 | 18 | 13 | 1 | 12 | 4 |
| Borderline | 24 | 17 | 13 | 9 | 4 | 4 |

- **What the model keeps of a critique is mostly its polarity**: a positive critique pushes towards acceptance for every aspect, in every group.
- **Accepted papers**, strongest cells: novelty / major -0.0199 [-0.0229, -0.0170]; significance / major -0.0145 [-0.0176, -0.0116]; soundness / major -0.0108 [-0.0132, -0.0079].
- **Borderline papers**, strongest cells: novelty / major -0.0201 [-0.0233, -0.0168]; novelty / blocking -0.0169 [-0.0295, -0.0063]; significance / major -0.0127 [-0.0165, -0.0083].
- **Rejected papers**: the cells that explain are almost all positive (reproducibility / major +0.0303 [+0.0099, +0.0575]; reproducibility / minor +0.0294 [+0.0186, +0.0440]; related_work / minor +0.0214 [+0.0119, +0.0366]). Removing a negative critique from a rejected paper lowers its prediction further. Untested hypothesis: the model reacts in part to the number of critiques and not to their content.
- All cells: `results/tables/explainability.csv`; table `results/tables/paper/explain_aspect_severity.tex`; figure `results/figures/explain_aspect_severity.pdf`.

**Relations and scale of the importances** (logit with the element minus logit without it).

| Removed | All papers | Accepted papers | Rejected papers | Borderline papers |
|---|---|---|---|---|
| `has_review` | -1.77 [-1.91, -1.64] | +0.23 [+0.08, +0.36] | -3.24 [-3.45, -3.06] | -0.31 [-0.42, -0.20] |
| `contains` | +3.92 [+3.47, +4.39] | +2.32 [+2.12, +2.53] | +5.10 [+4.34, +5.91] | +2.21 [+2.01, +2.42] |
| `about` | -0.24 [-0.27, -0.19] | -0.66 [-0.72, -0.60] | +0.08 [+0.02, +0.15] | -0.43 [-0.48, -0.38] |
| `has_concept` | +0.32 [+0.26, +0.39] | -0.35 [-0.41, -0.30] | +0.82 [+0.73, +0.93] | -0.12 [-0.16, -0.09] |
| `shares_concept` | +0.25 [+0.23, +0.28] | +0.26 [+0.23, +0.29] | +0.25 [+0.21, +0.29] | +0.19 [+0.16, +0.22] |
| initial scores set to the training mean | +1.18 [+1.05, +1.31] | +3.05 [+2.90, +3.20] | -0.20 [-0.40, -0.02] | +2.56 [+2.44, +2.70] |
| all critiques of the paper removed | +3.92 [+3.47, +4.39] | +2.31 [+2.11, +2.53] | +5.10 [+4.35, +5.92] | +2.21 [+2.01, +2.42] |

Source: `results/tables/explainability_relations.csv`.

- Removing every critique of a paper moves the prediction more than neutralising its scores, but the two are not comparable: a review without any critique almost never exists in the graph, so the model is then outside what it has seen. The clean measure of what the critiques bring is the ablation of RQ2 (model trained again without them).

**Fidelity** (mean absolute change of the probability; all explained papers). Fidelity+ removes the k most important critiques (higher is better); fidelity− keeps them alone (lower is better); the control draws k critiques at random.

| Method | k | Fidelity+ top k | Fidelity+ random | Difference: 95 % CI, verdict | Fidelity− top k | Fidelity− random | Difference: 95 % CI, verdict |
|---|---|---|---|---|---|---|---|
| `occlusion` | 1 | 0.0092 | 0.0022 | [+0.0065, +0.0075], significant | 0.1798 | 0.1934 | [-0.0174, -0.0095], significant |
| `occlusion` | 3 | 0.0239 | 0.0053 | [+0.0167, +0.0206], significant | 0.1372 | 0.1498 | [-0.0177, -0.0075], significant |
| `occlusion` | 5 | 0.0372 | 0.0094 | [+0.0251, +0.0306], significant | 0.1034 | 0.1191 | [-0.0217, -0.0098], significant |
| `input_x_gradient` | 1 | 0.0048 | 0.0022 | [+0.0023, +0.0030], significant | 0.2028 | 0.1934 | [+0.0058, +0.0130], significant |
| `input_x_gradient` | 3 | 0.0116 | 0.0053 | [+0.0055, +0.0072], significant | 0.1722 | 0.1498 | [+0.0173, +0.0271], significant |
| `input_x_gradient` | 5 | 0.0167 | 0.0094 | [+0.0061, +0.0085], significant | 0.1483 | 0.1191 | [+0.0245, +0.0342], significant |

Source: `results/tables/explainability_fidelity.csv`.

- **Occlusion is faithful**: better than random critiques on both measures, for every k.
- **Gradient attributions are only half faithful**: better than random on fidelity+, *worse* than random on fidelity−.

**Agreement between methods and between seeds** (Spearman rank correlation of the importances of the critiques of a paper).

- Occlusion against input × gradient: 0.683 [0.667, 0.698]; same most important critique in 19.4 % of the papers. Source: `results/tables/explainability_methods.csv`.
- Seed 0 against each other seed (200 papers): from 0.426 to 0.661; same most important critique in 11.3 % to 40.2 % of the papers, while the two models predict the same outcome for 93.0 % to 95.5 % of them. Source: `results/tables/explainability_seeds.csv`.
- **The ranking of the critiques of a paper is not stable across seeds**: an explanation critique by critique holds for one trained model, not for the architecture. The means per cell above were computed for one seed only.

**Case studies**: four borderline papers chosen by a rule fixed before the computation (probability closest to the median of their group).

| Case | Paper | Predicted probability | Reviews | Critiques | Figure |
|---|---|---|---|---|---|
| accepted predicted accept | `7UqQJUKaLM` | 0.811 | 4 | 28 | `results/figures/explain_case_accepted_predicted_accept.pdf` |
| rejected predicted reject | `lXv9DTw650` | 0.285 | 4 | 30 | `results/figures/explain_case_rejected_predicted_reject.pdf` |
| rejected predicted accept | `85WHuB5CUK` | 0.741 | 4 | 27 | `results/figures/explain_case_rejected_predicted_accept.pdf` |
| accepted predicted reject | `6ycX677p2l` | 0.300 | 5 | 54 | `results/figures/explain_case_accepted_predicted_reject.pdf` |

Source: `results/tables/explainability_cases.csv`.

## RQ4 — Is the model useful on borderline papers?

Test year, borderline papers. Source: `results/tables/main_results.csv`, `results/tables/main_results_tests.csv`.

| Model | Setting | AUC | 95 % CI | AUC minus `scores_rating_lr` | 95 % CI | DeLong | Verdict |
|---|---|---|---|---|---|---|---|
| `majority` | A | 0.500 | [0.500, 0.500] | -0.2216 | [-0.2378, -0.2066] | p < 0.001 | significant |
| `scores_rating_lr` | A | 0.722 | [0.707, 0.738] | reference |  |  |  |
| `scores_all_lr` | A | 0.719 | [0.704, 0.735] | -0.0027 | [-0.0100, +0.0050] | p = 0.479 | not significant |
| `text_mlp` | A | 0.534 | [0.516, 0.552] | -0.1872 | [-0.2097, -0.1658] | p < 0.001 | significant |
| `text_scores_mlp` | A | 0.724 | [0.709, 0.740] | +0.0027 | [-0.0054, +0.0112] | p = 0.419 | not significant |
| `text_scores_article_mlp` | A | 0.724 | [0.709, 0.740] | +0.0025 | [-0.0056, +0.0110] | p = 0.379 | not significant |
| `critiques_lr` | A | 0.617 | [0.600, 0.633] | -0.1050 | [-0.1259, -0.0844] | p < 0.001 | significant |
| `scores_critiques_lr` | A | 0.715 | [0.700, 0.731] | -0.0067 | [-0.0163, +0.0034] | p = 0.179 | not significant |
| `scores_all_gbt` | A | 0.714 | [0.698, 0.729] | -0.0078 | [-0.0165, +0.0011] | p = 0.073 | not significant |
| `scores_critiques_gbt` | A | 0.716 | [0.700, 0.733] | -0.0055 | [-0.0153, +0.0054] | p = 0.280 | not significant |
| `gcn` | A | 0.661 | [0.645, 0.678] | -0.0606 | [-0.0753, -0.0442] | p < 0.001 | significant |
| `han+scores` | A | 0.686 | [0.670, 0.702] | -0.0361 | [-0.0492, -0.0228] | p < 0.001 | significant |
| `han` | A | 0.683 | [0.668, 0.700] | -0.0384 | [-0.0525, -0.0244] | p < 0.001 | significant |
| `hgt+scores` | A | 0.689 | [0.673, 0.704] | -0.0324 | [-0.0451, -0.0193] | p < 0.001 | significant |
| `hgt` | A | 0.695 | [0.680, 0.711] | -0.0269 | [-0.0396, -0.0132] | p < 0.001 | significant |
| `rgcn+scores` | A | 0.680 | [0.664, 0.695] | -0.0420 | [-0.0545, -0.0291] | p < 0.001 | significant |
| `rgcn` | A | 0.646 | [0.630, 0.662] | -0.0755 | [-0.0919, -0.0596] | p < 0.001 | significant |
| `han+scores` | B | 0.689 | [0.675, 0.705] | -0.0326 | [-0.0450, -0.0199] | p < 0.001 | significant |
| `han` | B | 0.680 | [0.664, 0.696] | -0.0418 | [-0.0566, -0.0269] | p < 0.001 | significant |
| `hgt+scores` | B | 0.687 | [0.670, 0.702] | -0.0349 | [-0.0478, -0.0218] | p < 0.001 | significant |
| `hgt` | B | 0.689 | [0.674, 0.704] | -0.0331 | [-0.0462, -0.0198] | p < 0.001 | significant |
| `rgcn+scores` | B | 0.681 | [0.664, 0.696] | -0.0410 | [-0.0541, -0.0273] | p < 0.001 | significant |
| `rgcn` | B | 0.650 | [0.636, 0.667] | -0.0714 | [-0.0871, -0.0559] | p < 0.001 | significant |

- **No.** Borderline papers are hard for every model: `scores_rating_lr` falls from 0.873 on all papers to 0.722 on them. No model is significantly above it.
- Every heterogeneous GNN is significantly below it; the closest is `hgt` in setting A (-0.0269 [-0.0396, -0.0132]).
- Models whose difference with `scores_rating_lr` is not significant: `scores_all_lr`, `text_scores_mlp`, `text_scores_article_mlp`, `scores_critiques_lr`, `scores_all_gbt`, `scores_critiques_gbt`. None of them reads the graph.
- Inside the graph model, removing the critique nodes costs -0.0361 [-0.0484, -0.0258] on borderline papers, against -0.0249 on all papers (`results/tables/ablations.csv`); the two were not compared by a test. This does not make the graph model better than the scores.

## Holdout year — ICLR 2026, models frozen after the test year

ICLR 2025 has been looked at many times; this year had never been used. Nothing was chosen or tuned on it.

- **Heterogeneous GNNs** (setting A): the weights saved in phase 7. On the graph of the study they give back the stored probabilities of the test year (largest gap 3.0e-07, 30 models and seeds).
- **Baselines**: fitted again on the training year with the configurations kept in phase 6, without any search. The ones without random number give back the stored probabilities of the test year (largest gap 6.0e-08). The MLPs and the GCN are trained again and do not: largest gap 0.586 on a probability (`text_mlp`, `text_scores_mlp`, `text_scores_article_mlp`, `gcn`).
- **Graph**: the articles of 2026, their reviews and their critiques are appended to the graph of the study, which is unchanged; the concepts are those of 2024–2025 (frozen vocabulary). The holdout articles are predicted on this extended graph, as the test articles were on the graph of the study.
- **Papers**: 14,169 with a decision (37.8 % accepted), 7,534 of them borderline (same zone of ratings). Source: `results/tables/holdout_2026.csv`, `results/tables/holdout_2026_checks.csv`.

**ICLR 2026 is not an ordinary year.** After a security incident during the discussion, the conference reverted the reviews to their state at the start of the discussion and gave every paper to a new area chair (announcement of the conference). The scores and the text used here are the current ones, taken as initial; 7.7 % of the 2026 reviews were modified after their release (`results/tables/clean_report_by_year.csv`). The rating scale changed (0, 2, 4, 6, 8, 10): each level was mapped to the level of the same rank of the earlier scale (1, 3, 5, 6, 8, 10), a rule fixed before any decision of that year was read.

**The models trained again, checked by a second run** (the tables of this section come from the first run). `text_mlp`: AUC on the test year 0.6074 trained again, 0.6093 stored; `text_scores_mlp`: AUC on the test year 0.8759 trained again, 0.8759 stored; `text_scores_article_mlp`: AUC on the test year 0.8761 trained again, 0.8761 stored. From one run to the next, every model gives the same predictions except `gcn` (AUC on 2026: 0.8105 then 0.8113). Source: `results/tables/holdout_2026_second_run.csv`.

**All papers** (14,169 papers of 2026).

| Model | AUC, test year | AUC, 2026 | 95 % CI | AUC minus `scores_rating_lr` | 95 % CI | DeLong | Verdict |
|---|---|---|---|---|---|---|---|
| `majority` | 0.500 | 0.500 | [0.500, 0.500] | -0.3866 | [-0.3919, -0.3810] | p < 0.001 | significant |
| `scores_rating_lr` | 0.873 | 0.887 | [0.881, 0.892] | reference |  |  |  |
| `scores_all_lr` | 0.874 | 0.886 | [0.881, 0.892] | -0.0002 | [-0.0018, +0.0014] | p = 0.821 | not significant |
| `text_mlp` | 0.609 | 0.595 | [0.586, 0.604] | -0.2915 | [-0.3018, -0.2819] | p < 0.001 | significant |
| `text_scores_mlp` | 0.876 | 0.888 | [0.882, 0.893] | +0.0012 | [-0.0007, +0.0032] | p = 0.171 | not significant |
| `text_scores_article_mlp` | 0.876 | 0.888 | [0.882, 0.893] | +0.0010 | [-0.0010, +0.0032] | p = 0.159 | not significant |
| `critiques_lr` | 0.760 | 0.744 | [0.735, 0.752] | -0.1430 | [-0.1511, -0.1351] | p < 0.001 | significant |
| `scores_critiques_lr` | 0.873 | 0.881 | [0.876, 0.887] | -0.0054 | [-0.0079, -0.0028] | p < 0.001 | significant |
| `scores_all_gbt` | 0.873 | 0.884 | [0.879, 0.889] | -0.0025 | [-0.0045, -0.0005] | p = 0.013 | significant |
| `scores_critiques_gbt` | 0.874 | 0.881 | [0.876, 0.886] | -0.0055 | [-0.0080, -0.0031] | p < 0.001 | significant |
| `gcn` | 0.831 | 0.810 | [0.803, 0.817] | -0.0761 | [-0.0815, -0.0707] | p < 0.001 | significant |
| `rgcn` | 0.820 | 0.777 | [0.770, 0.784] | -0.1093 | [-0.1157, -0.1029] | p < 0.001 | significant |
| `rgcn+scores` | 0.856 | 0.860 | [0.854, 0.866] | -0.0264 | [-0.0298, -0.0232] | p < 0.001 | significant |
| `han` | 0.856 | 0.857 | [0.851, 0.863] | -0.0293 | [-0.0335, -0.0254] | p < 0.001 | significant |
| `han+scores` | 0.859 | 0.859 | [0.853, 0.865] | -0.0277 | [-0.0313, -0.0242] | p < 0.001 | significant |
| `hgt` | 0.858 | 0.862 | [0.856, 0.868] | -0.0246 | [-0.0288, -0.0207] | p < 0.001 | significant |
| `hgt+scores` | 0.858 | 0.865 | [0.859, 0.871] | -0.0215 | [-0.0250, -0.0182] | p < 0.001 | significant |

**Borderline papers** (7,534 papers of 2026).

| Model | AUC, test year | AUC, 2026 | 95 % CI | AUC minus `scores_rating_lr` | 95 % CI | DeLong | Verdict |
|---|---|---|---|---|---|---|---|
| `majority` | 0.500 | 0.500 | [0.500, 0.500] | -0.2563 | [-0.2671, -0.2453] | p < 0.001 | significant |
| `scores_rating_lr` | 0.722 | 0.756 | [0.745, 0.767] | reference |  |  |  |
| `scores_all_lr` | 0.719 | 0.753 | [0.741, 0.763] | -0.0033 | [-0.0086, +0.0018] | p = 0.207 | not significant |
| `text_mlp` | 0.534 | 0.538 | [0.525, 0.551] | -0.2188 | [-0.2347, -0.2007] | p < 0.001 | significant |
| `text_scores_mlp` | 0.724 | 0.757 | [0.746, 0.768] | +0.0008 | [-0.0047, +0.0063] | p = 0.634 | not significant |
| `text_scores_article_mlp` | 0.724 | 0.757 | [0.746, 0.768] | +0.0008 | [-0.0050, +0.0067] | p = 0.487 | not significant |
| `critiques_lr` | 0.617 | 0.607 | [0.594, 0.620] | -0.1498 | [-0.1634, -0.1341] | p < 0.001 | significant |
| `scores_critiques_lr` | 0.715 | 0.740 | [0.728, 0.750] | -0.0168 | [-0.0236, -0.0099] | p < 0.001 | significant |
| `scores_all_gbt` | 0.714 | 0.746 | [0.735, 0.757] | -0.0101 | [-0.0161, -0.0046] | p < 0.001 | significant |
| `scores_critiques_gbt` | 0.716 | 0.737 | [0.725, 0.748] | -0.0193 | [-0.0259, -0.0123] | p < 0.001 | significant |
| `gcn` | 0.661 | 0.649 | [0.638, 0.661] | -0.1074 | [-0.1191, -0.0945] | p < 0.001 | significant |
| `rgcn` | 0.646 | 0.634 | [0.623, 0.646] | -0.1226 | [-0.1350, -0.1097] | p < 0.001 | significant |
| `rgcn+scores` | 0.680 | 0.697 | [0.686, 0.709] | -0.0591 | [-0.0677, -0.0503] | p < 0.001 | significant |
| `han` | 0.683 | 0.698 | [0.687, 0.710] | -0.0579 | [-0.0684, -0.0477] | p < 0.001 | significant |
| `han+scores` | 0.686 | 0.693 | [0.682, 0.704] | -0.0637 | [-0.0737, -0.0540] | p < 0.001 | significant |
| `hgt` | 0.695 | 0.714 | [0.704, 0.725] | -0.0420 | [-0.0515, -0.0323] | p < 0.001 | significant |
| `hgt+scores` | 0.689 | 0.709 | [0.698, 0.720] | -0.0474 | [-0.0562, -0.0383] | p < 0.001 | significant |

Source: `results/tables/holdout_2026_tests.csv`, `results/tables/holdout_2026_vs_test_year.csv`.

**A model against its control.**

| Model | Control | Split | Papers | AUC model | AUC control | Difference | 95 % CI | DeLong | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `scores_critiques_lr` | `scores_all_lr` | holdout | all | 0.8812 | 0.8864 | -0.0052 | [-0.0072, -0.0033] | p < 0.001 | significant |
| `scores_critiques_lr` | `scores_all_lr` | holdout | borderline | 0.7395 | 0.7530 | -0.0135 | [-0.0180, -0.0085] | p < 0.001 | significant |
| `scores_critiques_gbt` | `scores_all_gbt` | holdout | all | 0.8811 | 0.8841 | -0.0030 | [-0.0050, -0.0013] | p < 0.001 | significant |
| `scores_critiques_gbt` | `scores_all_gbt` | holdout | borderline | 0.7370 | 0.7462 | -0.0092 | [-0.0139, -0.0045] | p < 0.001 | significant |
| `critiques_lr` | `text_mlp` | holdout | all | 0.7436 | 0.5951 | +0.1485 | [+0.1374, +0.1599] | p < 0.001 | significant |
| `critiques_lr` | `text_mlp` | holdout | borderline | 0.6065 | 0.5375 | +0.0690 | [+0.0513, +0.0868] | p < 0.001 | significant |
| `hgt` | `gcn` | holdout | all | 0.8620 | 0.8105 | +0.0515 | [+0.0464, +0.0564] | p < 0.001 | significant |
| `hgt` | `gcn` | holdout | borderline | 0.7143 | 0.6490 | +0.0653 | [+0.0547, +0.0762] | p < 0.001 | significant |
| `han` | `gcn` | holdout | all | 0.8573 | 0.8105 | +0.0468 | [+0.0422, +0.0512] | p < 0.001 | significant |
| `han` | `gcn` | holdout | borderline | 0.6984 | 0.6490 | +0.0494 | [+0.0393, +0.0581] | p < 0.001 | significant |
| `rgcn` | `gcn` | holdout | all | 0.7773 | 0.8105 | -0.0332 | [-0.0391, -0.0267] | p < 0.001 | significant |
| `rgcn` | `gcn` | holdout | borderline | 0.6337 | 0.6490 | -0.0152 | [-0.0260, -0.0041] | p = 0.037 | significant |

Source: `results/tables/holdout_2026_paired.csv`.

**The three conclusions of the test year, written before this run.** A conclusion holds when the confidence intervals say so (rule in the protocol).

|  | Conclusion of the test year | Papers | On 2026 | Detail |
|---|---|---|---|---|
| (a) | no heterogeneous GNN is above `scores_rating_lr` | all | **holds** | 6 of 6 significantly below, 0 significantly above; closest: hgt+scores -0.0215 [-0.0250, -0.0182] |
| (a) | no heterogeneous GNN is above `scores_rating_lr` | borderline | **holds** | 6 of 6 significantly below, 0 significantly above; closest: hgt -0.0420 [-0.0515, -0.0323] |
| (b) | HAN and HGT are above the GCN | all | **holds** | han - gcn +0.0468 [+0.0422, +0.0512]; hgt - gcn +0.0515 [+0.0464, +0.0564]; rgcn - gcn -0.0332 [-0.0391, -0.0267] |
| (b) | HAN and HGT are above the GCN | borderline | **holds** | han - gcn +0.0494 [+0.0393, +0.0581]; hgt - gcn +0.0653 [+0.0547, +0.0762]; rgcn - gcn -0.0152 [-0.0260, -0.0041] |
| (c) | the critique counts added to the scores bring no gain | all | **holds** | scores_critiques_lr - scores_all_lr -0.0052 [-0.0072, -0.0033]; scores_critiques_gbt - scores_all_gbt -0.0030 [-0.0050, -0.0013] |
| (c) | the critique counts added to the scores bring no gain | borderline | **holds** | scores_critiques_lr - scores_all_lr -0.0135 [-0.0180, -0.0085]; scores_critiques_gbt - scores_all_gbt -0.0092 [-0.0139, -0.0045] |

- On all papers, 3 of the 3 conclusions hold.
Source: `results/tables/holdout_2026_readings.csv`.

**What the larger graph changes.** The articles of the test year, predicted again on the extended graph by the same frozen GNNs: their AUC on the test year changes by -0.0276 to +0.0000, and 0.0 % to 5.1 % of the predicted outcomes change. This measures how much a prediction depends on the size of the graph around it, without any outcome of the holdout year.

| Model | Trained again | AUC, graph of the study | AUC, extended graph | Difference | Mean change of probability | Predicted outcomes changed |
|---|---|---|---|---|---|---|
| `gcn` | yes | 0.8308 | 0.8206 | -0.0103 | 0.0405 | 4.3 % |
| `rgcn` | no | 0.8196 | 0.7920 | -0.0276 | 0.0431 | 5.1 % |
| `rgcn+scores` | no | 0.8558 | 0.8546 | -0.0012 | 0.0090 | 0.9 % |
| `han` | no | 0.8556 | 0.8556 | +0.0000 | 0.0001 | 0.0 % |
| `han+scores` | no | 0.8589 | 0.8589 | -0.0000 | 0.0001 | 0.0 % |
| `hgt` | no | 0.8581 | 0.8546 | -0.0035 | 0.0155 | 1.6 % |
| `hgt+scores` | no | 0.8583 | 0.8577 | -0.0006 | 0.0117 | 1.2 % |

Source: `results/tables/holdout_2026_graph_growth.csv`.

**Limits of this test.**

- An atypical year (see above): a difference with the test year can come from the year as much as from the models.
- The vocabulary of concepts is frozen: 74.7 % of the keywords of 2024 are concepts of the graph; 73.6 % of the keywords of 2025 are concepts of the graph; 62.5 % of the keywords of 2026 are concepts of the graph (`results/tables/kg_concept_coverage_holdout.csv`).
- The baselines trained by epochs (MLPs, GCN) are not the very models of the test year: they are trained again with the same configuration and seeds.
- Setting A only: the author responses of this year were not extracted.
- The models are not trained again with the test year as validation; that protocol is not run yet.

## Sensitivity analyses

Added on 2026-11-24, after the test and holdout years had been read: every result of this section is post hoc. Nothing is trained; the pairs, subsets, zones and families of tests were written in `configs/default.yaml` (`sensitivity`) before the computation.

### Scope of the concept vocabulary

The vocabulary is counted on every paper of the graph. 2,754 of the 5,073 concepts (54.3 %) have fewer than 2 papers of the training year and would not be concepts with a vocabulary counted on that year alone; 1,073 have none. 1,681 `has_concept` links of papers of the training year lead to such concepts, and 28 other concepts would change whether they carry `shares_concept`. Source: `results/tables/kg_concept_scope.csv`.

| Years | `shares_concept` pairs |
|---|---|
| 2024–2024 | 68,656 |
| 2024–2025 | 175,575 |
| 2025–2025 | 141,283 |

Source: `results/tables/kg_shares_concept_by_year.csv`.

| Papers | Year | Count | With a concept | With a neighbour | With a neighbour of the training year |
|---|---|---|---|---|---|
| articles of the graph | 2024 | 6,954 | 91.5 % | 84.9 % | 81.2 % |
| articles of the graph | 2025 | 11,422 | 78.5 % | 73.9 % | 69.5 % |
| papers with a decision | 2024 | 5,534 | 92.1 % | 85.7 % | 82.0 % |
| papers with a decision | 2025 | 8,655 | 79.8 % | 75.3 % | 70.9 % |

Source: `results/tables/kg_concept_neighbours.csv`.

### Dates of the text archive against the decisions

| Year | First decision note | Text archive committed | Days from first decision to commit | Submissions in the file | With a decision in the file | Author replies to a review | Created from the first decision day |
|---|---|---|---|---|---|---|---|
| 2024 | 2024-01-16 | 2024-02-09 | 24 | 7,304 | 0 | 50,245 | 0 |
| 2025 | 2025-01-22 | 2024-10-16 | -98 | 10,079 | 79 | 105,493 | 0 |
| 2026 | 2026-01-26 | 2025-10-10 | -108 | 19,793 | 120 | 136,562 | 0 |

The version of the text archive used for 2024 was committed after the first decision note of that year: its date does not establish that the text precedes the decisions; the file carries no decision. Source: `results/tables/input_dates.csv`.

### Mean initial rating used as a score (RQ1 a)

The mean of the initial ratings of a paper, without any fitting.

| Split | Papers | Subset | AUC | 95 % CI |
|---|---|---|---|---|
| val | 839 | all | 0.8763 | [0.8517, 0.8966] |
| val | 382 | borderline | 0.7290 | [0.6821, 0.7761] |
| test | 8,655 | all | 0.8701 | [0.8626, 0.8775] |
| test | 4,049 | borderline | 0.7073 | [0.6924, 0.7230] |

Source: `results/tables/sensitivity_mean_rating.csv`.

### Pairs compared afterwards (test year)

All papers:

| Model | Control | Papers | AUC | Control AUC | Δ | 95 % CI | DeLong | Holm |
|---|---|---|---|---|---|---|---|---|
| HGT + score statistics | HGT | 8,655 | 0.8583 | 0.8581 | +0.0002 | [-0.0034, +0.0037] | p = 0.948 | p = 1.000 |
| HAN + score statistics | HAN | 8,655 | 0.8589 | 0.8556 | +0.0033 | [+0.0013, +0.0056] | p = 0.015 | p = 0.075 |
| R-GCN + score statistics | R-GCN | 8,655 | 0.8558 | 0.8196 | +0.0362 | [+0.0317, +0.0413] | p < 0.001 | p < 0.001 |
| HAN, with author responses | HAN | 8,655 | 0.8542 | 0.8556 | -0.0013 | [-0.0023, -0.0004] | p < 0.001 | p < 0.001 |
| R-GCN, with author responses | R-GCN | 8,655 | 0.8250 | 0.8196 | +0.0054 | [+0.0036, +0.0072] | p < 0.001 | p < 0.001 |
| HGT | Review text (MLP) | 8,655 | 0.8581 | 0.6093 | +0.2488 | [+0.2373, +0.2609] | p < 0.001 | p < 0.001 |
| HAN | Review text (MLP) | 8,655 | 0.8556 | 0.6093 | +0.2463 | [+0.2344, +0.2581] | p < 0.001 | p < 0.001 |
| R-GCN | Review text (MLP) | 8,655 | 0.8196 | 0.6093 | +0.2103 | [+0.1991, +0.2226] | p < 0.001 | p < 0.001 |
| Initial rating (LR) | Mean initial rating, not fitted | 8,655 | 0.8733 | 0.8701 | +0.0032 | [+0.0017, +0.0047] | p < 0.001 | p < 0.001 |
| HGT | Mean initial rating, not fitted | 8,655 | 0.8581 | 0.8701 | -0.0121 | [-0.0167, -0.0074] | p < 0.001 | p < 0.001 |
| HAN | Mean initial rating, not fitted | 8,655 | 0.8556 | 0.8701 | -0.0146 | [-0.0191, -0.0100] | p < 0.001 | p < 0.001 |
| R-GCN | Mean initial rating, not fitted | 8,655 | 0.8196 | 0.8701 | -0.0505 | [-0.0571, -0.0441] | p < 0.001 | p < 0.001 |

Borderline papers:

| Model | Control | Papers | AUC | Control AUC | Δ | 95 % CI | DeLong | Holm |
|---|---|---|---|---|---|---|---|---|
| HGT + score statistics | HGT | 4,049 | 0.6892 | 0.6947 | -0.0055 | [-0.0152, +0.0040] | p = 0.299 | p = 0.971 |
| HAN + score statistics | HAN | 4,049 | 0.6856 | 0.6832 | +0.0024 | [-0.0043, +0.0092] | p = 0.662 | p = 1.000 |
| R-GCN + score statistics | R-GCN | 4,049 | 0.6796 | 0.6461 | +0.0335 | [+0.0215, +0.0445] | p < 0.001 | p < 0.001 |
| HAN, with author responses | HAN | 4,049 | 0.6799 | 0.6832 | -0.0034 | [-0.0062, -0.0006] | p = 0.002 | p = 0.014 |
| R-GCN, with author responses | R-GCN | 4,049 | 0.6503 | 0.6461 | +0.0042 | [-0.0003, +0.0083] | p = 0.003 | p = 0.022 |
| HGT | Review text (MLP) | 4,049 | 0.6947 | 0.5345 | +0.1603 | [+0.1421, +0.1789] | p < 0.001 | p < 0.001 |
| HAN | Review text (MLP) | 4,049 | 0.6832 | 0.5345 | +0.1488 | [+0.1299, +0.1674] | p < 0.001 | p < 0.001 |
| R-GCN | Review text (MLP) | 4,049 | 0.6461 | 0.5345 | +0.1117 | [+0.0924, +0.1309] | p < 0.001 | p < 0.001 |
| Initial rating (LR) | Mean initial rating, not fitted | 4,049 | 0.7216 | 0.7073 | +0.0144 | [+0.0085, +0.0204] | p < 0.001 | p < 0.001 |
| HGT | Mean initial rating, not fitted | 4,049 | 0.6947 | 0.7073 | -0.0126 | [-0.0260, +0.0017] | p = 0.243 | p = 0.971 |
| HAN | Mean initial rating, not fitted | 4,049 | 0.6832 | 0.7073 | -0.0241 | [-0.0384, -0.0097] | p = 0.004 | p = 0.024 |
| R-GCN | Mean initial rating, not fitted | 4,049 | 0.6461 | 0.7073 | -0.0612 | [-0.0780, -0.0452] | p < 0.001 | p < 0.001 |

Source: `results/tables/sensitivity_pairs.csv`, `results/tables/tests_holm.csv`.

### Test papers with text; withdrawn papers counted as rejections

| Analysis | Subset | Model | Control | Papers | AUC | Control AUC | Δ | 95 % CI | DeLong |
|---|---|---|---|---|---|---|---|---|---|
| papers_with_text | with_text | Review text + scores (MLP) | Initial rating (LR) | 7,540 | 0.8775 | 0.8741 | +0.0034 | [+0.0009, +0.0059] | p = 0.005 |
| papers_with_text | with_text | GCN, untyped graph | Initial rating (LR) | 7,540 | 0.8326 | 0.8741 | -0.0415 | [-0.0478, -0.0352] | p < 0.001 |
| papers_with_text | with_text | R-GCN | Initial rating (LR) | 7,540 | 0.8175 | 0.8741 | -0.0566 | [-0.0637, -0.0495] | p < 0.001 |
| papers_with_text | with_text | HAN | Initial rating (LR) | 7,540 | 0.8575 | 0.8741 | -0.0166 | [-0.0213, -0.0117] | p < 0.001 |
| papers_with_text | with_text | HGT | Initial rating (LR) | 7,540 | 0.8611 | 0.8741 | -0.0131 | [-0.0175, -0.0084] | p < 0.001 |
| papers_with_text | with_text | HGT + score statistics | Initial rating (LR) | 7,540 | 0.8617 | 0.8741 | -0.0124 | [-0.0171, -0.0078] | p < 0.001 |
| papers_with_text | with_text | HGT, with author responses | Initial rating (LR) | 7,540 | 0.8580 | 0.8741 | -0.0161 | [-0.0202, -0.0115] | p < 0.001 |
| papers_with_text | borderline_with_text | Review text + scores (MLP) | Initial rating (LR) | 3,480 | 0.7252 | 0.7214 | +0.0038 | [-0.0049, +0.0132] | p = 0.331 |
| papers_with_text | borderline_with_text | GCN, untyped graph | Initial rating (LR) | 3,480 | 0.6596 | 0.7214 | -0.0618 | [-0.0786, -0.0445] | p < 0.001 |
| papers_with_text | borderline_with_text | R-GCN | Initial rating (LR) | 3,480 | 0.6425 | 0.7214 | -0.0789 | [-0.0974, -0.0593] | p < 0.001 |
| papers_with_text | borderline_with_text | HAN | Initial rating (LR) | 3,480 | 0.6857 | 0.7214 | -0.0358 | [-0.0524, -0.0188] | p < 0.001 |
| papers_with_text | borderline_with_text | HGT | Initial rating (LR) | 3,480 | 0.6976 | 0.7214 | -0.0238 | [-0.0389, -0.0076] | p = 0.007 |
| papers_with_text | borderline_with_text | HGT + score statistics | Initial rating (LR) | 3,480 | 0.6939 | 0.7214 | -0.0276 | [-0.0421, -0.0136] | p < 0.001 |
| papers_with_text | borderline_with_text | HGT, with author responses | Initial rating (LR) | 3,480 | 0.6908 | 0.7214 | -0.0306 | [-0.0450, -0.0152] | p = 0.005 |
| withdrawn_as_reject | all | HGT | Initial rating (LR) | 11,422 | 0.8885 | 0.9029 | -0.0144 | [-0.0180, -0.0106] | p < 0.001 |
| withdrawn_as_reject | borderline | HGT | Initial rating (LR) | 4,365 | 0.7062 | 0.7366 | -0.0304 | [-0.0429, -0.0170] | p < 0.001 |

Source: `results/tables/sensitivity_subgroups.csv`.

### Other definitions of the borderline zone

Each zone is fitted on the training papers only; `study` is the zone of the other sections.

| Definition | Bin width | Min. papers | Rates | Status | Zone | Test papers | Accepted |
|---|---|---|---|---|---|---|---|
| study | 0.25 | 20 | [0.2, 0.8] | ok | [5.00, 6.25) | 4,049 | 58.5 % |
| bin_width_0.5 | 0.5 | 20 | [0.2, 0.8] | ok | [5.00, 6.00) | 3,476 | 54.2 % |
| rates_0.3_0.7 | 0.25 | 20 | [0.3, 0.7] | ok | [5.00, 6.00) | 3,476 | 54.2 % |
| rates_0.1_0.9 | 0.25 | 20 | [0.1, 0.9] | ok | [4.50, 6.50) | 6,010 | 51.3 % |
| min_papers_50 | 0.25 | 50 | [0.2, 0.8] | ok | [5.00, 6.25) | 4,049 | 58.5 % |

| Definition | Model | Control | Papers | AUC | Control AUC | Δ | 95 % CI | DeLong |
|---|---|---|---|---|---|---|---|---|
| study | Review text + scores (MLP) | Initial rating (LR) | 4,049 | 0.7244 | 0.7216 | +0.0027 | [-0.0054, +0.0112] | p = 0.419 |
| study | GCN, untyped graph | Initial rating (LR) | 4,049 | 0.6610 | 0.7216 | -0.0606 | [-0.0753, -0.0442] | p < 0.001 |
| study | R-GCN | Initial rating (LR) | 4,049 | 0.6461 | 0.7216 | -0.0755 | [-0.0919, -0.0596] | p < 0.001 |
| study | HAN | Initial rating (LR) | 4,049 | 0.6832 | 0.7216 | -0.0384 | [-0.0525, -0.0244] | p < 0.001 |
| study | HGT | Initial rating (LR) | 4,049 | 0.6947 | 0.7216 | -0.0269 | [-0.0396, -0.0132] | p < 0.001 |
| study | HGT + score statistics | Initial rating (LR) | 4,049 | 0.6892 | 0.7216 | -0.0324 | [-0.0451, -0.0193] | p < 0.001 |
| study | HGT, with author responses | Initial rating (LR) | 4,049 | 0.6886 | 0.7216 | -0.0331 | [-0.0462, -0.0198] | p < 0.001 |
| bin_width_0.5 | Review text + scores (MLP) | Initial rating (LR) | 3,476 | 0.6938 | 0.6920 | +0.0018 | [-0.0084, +0.0118] | p = 0.629 |
| bin_width_0.5 | GCN, untyped graph | Initial rating (LR) | 3,476 | 0.6398 | 0.6920 | -0.0522 | [-0.0703, -0.0341] | p < 0.001 |
| bin_width_0.5 | R-GCN | Initial rating (LR) | 3,476 | 0.6196 | 0.6920 | -0.0724 | [-0.0917, -0.0524] | p < 0.001 |
| bin_width_0.5 | HAN | Initial rating (LR) | 3,476 | 0.6521 | 0.6920 | -0.0399 | [-0.0574, -0.0224] | p < 0.001 |
| bin_width_0.5 | HGT | Initial rating (LR) | 3,476 | 0.6636 | 0.6920 | -0.0285 | [-0.0430, -0.0132] | p = 0.002 |
| bin_width_0.5 | HGT + score statistics | Initial rating (LR) | 3,476 | 0.6543 | 0.6920 | -0.0377 | [-0.0550, -0.0213] | p < 0.001 |
| bin_width_0.5 | HGT, with author responses | Initial rating (LR) | 3,476 | 0.6587 | 0.6920 | -0.0333 | [-0.0483, -0.0174] | p = 0.002 |
| rates_0.3_0.7 | Review text + scores (MLP) | Initial rating (LR) | 3,476 | 0.6938 | 0.6920 | +0.0018 | [-0.0084, +0.0118] | p = 0.629 |
| rates_0.3_0.7 | GCN, untyped graph | Initial rating (LR) | 3,476 | 0.6398 | 0.6920 | -0.0522 | [-0.0703, -0.0341] | p < 0.001 |
| rates_0.3_0.7 | R-GCN | Initial rating (LR) | 3,476 | 0.6196 | 0.6920 | -0.0724 | [-0.0917, -0.0524] | p < 0.001 |
| rates_0.3_0.7 | HAN | Initial rating (LR) | 3,476 | 0.6521 | 0.6920 | -0.0399 | [-0.0574, -0.0224] | p < 0.001 |
| rates_0.3_0.7 | HGT | Initial rating (LR) | 3,476 | 0.6636 | 0.6920 | -0.0285 | [-0.0430, -0.0132] | p = 0.002 |
| rates_0.3_0.7 | HGT + score statistics | Initial rating (LR) | 3,476 | 0.6543 | 0.6920 | -0.0377 | [-0.0550, -0.0213] | p < 0.001 |
| rates_0.3_0.7 | HGT, with author responses | Initial rating (LR) | 3,476 | 0.6587 | 0.6920 | -0.0333 | [-0.0483, -0.0174] | p = 0.002 |
| rates_0.1_0.9 | Review text + scores (MLP) | Initial rating (LR) | 6,010 | 0.7917 | 0.7869 | +0.0048 | [+0.0001, +0.0093] | p = 0.024 |
| rates_0.1_0.9 | GCN, untyped graph | Initial rating (LR) | 6,010 | 0.7336 | 0.7869 | -0.0534 | [-0.0637, -0.0433] | p < 0.001 |
| rates_0.1_0.9 | R-GCN | Initial rating (LR) | 6,010 | 0.7193 | 0.7869 | -0.0677 | [-0.0786, -0.0565] | p < 0.001 |
| rates_0.1_0.9 | HAN | Initial rating (LR) | 6,010 | 0.7586 | 0.7869 | -0.0283 | [-0.0372, -0.0195] | p < 0.001 |
| rates_0.1_0.9 | HGT | Initial rating (LR) | 6,010 | 0.7654 | 0.7869 | -0.0215 | [-0.0299, -0.0136] | p < 0.001 |
| rates_0.1_0.9 | HGT + score statistics | Initial rating (LR) | 6,010 | 0.7648 | 0.7869 | -0.0221 | [-0.0303, -0.0147] | p < 0.001 |
| rates_0.1_0.9 | HGT, with author responses | Initial rating (LR) | 6,010 | 0.7610 | 0.7869 | -0.0259 | [-0.0340, -0.0178] | p < 0.001 |
| min_papers_50 | Review text + scores (MLP) | Initial rating (LR) | 4,049 | 0.7244 | 0.7216 | +0.0027 | [-0.0054, +0.0112] | p = 0.419 |
| min_papers_50 | GCN, untyped graph | Initial rating (LR) | 4,049 | 0.6610 | 0.7216 | -0.0606 | [-0.0753, -0.0442] | p < 0.001 |
| min_papers_50 | R-GCN | Initial rating (LR) | 4,049 | 0.6461 | 0.7216 | -0.0755 | [-0.0919, -0.0596] | p < 0.001 |
| min_papers_50 | HAN | Initial rating (LR) | 4,049 | 0.6832 | 0.7216 | -0.0384 | [-0.0525, -0.0244] | p < 0.001 |
| min_papers_50 | HGT | Initial rating (LR) | 4,049 | 0.6947 | 0.7216 | -0.0269 | [-0.0396, -0.0132] | p < 0.001 |
| min_papers_50 | HGT + score statistics | Initial rating (LR) | 4,049 | 0.6892 | 0.7216 | -0.0324 | [-0.0451, -0.0193] | p < 0.001 |
| min_papers_50 | HGT, with author responses | Initial rating (LR) | 4,049 | 0.6886 | 0.7216 | -0.0331 | [-0.0462, -0.0198] | p < 0.001 |

Source: `results/tables/sensitivity_borderline_zones.csv`, `results/tables/sensitivity_borderline.csv`.

### Holm correction, one family of tests per table

| Family | File | Tests | p < 0.05 | After Holm | Interval excludes zero |
|---|---|---|---|---|---|
| main_vs_initial_rating | `results/tables/main_results_tests.csv` | 44 | 34 | 32 | 34 |
| hetero_vs_gcn | `results/tables/paired_comparisons.csv` | 6 | 5 | 5 | 6 |
| critique_counts | `results/tables/paired_comparisons.csv` | 6 | 2 | 2 | 2 |
| ablations | `results/tables/ablations.csv` | 14 | 9 | 9 | 11 |
| holdout_vs_initial_rating | `results/tables/holdout_2026_tests.csv` | 32 | 26 | 25 | 26 |
| holdout_paired | `results/tables/holdout_2026_paired.csv` | 12 | 12 | 12 | 12 |
| pairs_added_afterwards | `results/tables/sensitivity_pairs.csv` | 24 | 20 | 19 | 19 |

4 of the 108 tests that reject at 0.05 no longer reject after the correction:

| Family | Model | Setting | Control | Subset | Δ | 95 % CI | DeLong | Holm |
|---|---|---|---|---|---|---|---|---|
| main_vs_initial_rating | text_scores_mlp | A | scores_rating_lr | all | +0.0026 | [+0.0002, +0.0049] | p = 0.016 | p = 0.172 |
| main_vs_initial_rating | text_scores_article_mlp | A | scores_rating_lr | all | +0.0028 | [+0.0005, +0.0053] | p = 0.006 | p = 0.076 |
| holdout_vs_initial_rating | scores_all_gbt | A | scores_rating_lr | all | -0.0025 | [-0.0045, -0.0005] | p = 0.013 | p = 0.091 |
| pairs_added_afterwards | han+scores | A | han | all | +0.0033 | [+0.0013, +0.0056] | p = 0.015 | p = 0.075 |

Source: `results/tables/tests_holm.csv`.

## Protocol checks

Added on 2026-11-24, after the test and holdout years had been read: every result of this section is post hoc. Unlike the sensitivity analyses, these checks train models. Their design (spaces searched, budget of 48 configurations per family trained by epochs, selection rule, comparisons, reading rule) is the section `protocol` of `configs/default.yaml`, committed before the first run; each stage was trained once.

Reading rule. (a) *no heterogeneous GNN is above the logistic regression on the initial rating*: confirmed if the interval of the difference is below zero for every heterogeneous variant, contradicted if it is above zero for at least one, not separated otherwise. (b) *HAN and HGT are above the GCN*: read in the same way.

| Check | Year | Papers | (a) | Variants below / above | Closest heterogeneous variant | (b) |
|---|---|---|---|---|---|---|
| Vocabulary of the training year | 2025 | All papers | confirmed | 6 / 0 of 6 | HAN + score statistics -0.0145 [-0.0188, -0.0103] | confirmed |
| Vocabulary of the training year | 2025 | Borderline papers | confirmed | 6 / 0 of 6 | HGT -0.0267 [-0.0383, -0.0141] | confirmed |
| Equal and wider search | 2025 | All papers | contradicted | 4 / 1 of 6 | HAN +0.0041 [+0.0017, +0.0065] | confirmed |
| Equal and wider search | 2025 | Borderline papers | not separated | 4 / 0 of 6 | HAN +0.0066 [-0.0014, +0.0161] | confirmed |
| Equal and wider search | 2026 | All papers | contradicted | 4 / 1 of 6 | HAN +0.0024 [+0.0004, +0.0044] | confirmed |
| Equal and wider search | 2026 | Borderline papers | not separated | 4 / 0 of 6 | HAN +0.0028 [-0.0029, +0.0088] | confirmed |
| Validation on the following year | 2026 | All papers | contradicted | 4 / 1 of 6 | HAN +0.0031 [+0.0012, +0.0049] | confirmed |
| Validation on the following year | 2026 | Borderline papers | not separated | 4 / 0 of 6 | HAN +0.0048 [-0.0007, +0.0106] | confirmed |

Source: `results/tables/protocol_readings.csv`, `results/tables/protocol_comparisons.csv`.

### The main model without the pretrained text encoders

HGT of the study, same hyper-parameters, test year.

| Papers | Variant | AUC | Δ with the full graph | Δ with Initial rating (LR) |
|---|---|---|---|---|
| All papers | No embedding of the paper | 0.8617 | +0.0034 [+0.0023, +0.0046] | -0.0116 [-0.0159, -0.0076] |
| All papers | No pretrained embedding at all | 0.8786 | +0.0204 [+0.0166, +0.0242] | +0.0053 [+0.0028, +0.0080] |
| Borderline papers | No embedding of the paper | 0.6970 | +0.0019 [-0.0013, +0.0050] | -0.0247 [-0.0367, -0.0115] |
| Borderline papers | No pretrained embedding at all | 0.7341 | +0.0390 [+0.0277, +0.0506] | +0.0124 [+0.0039, +0.0217] |

Source: `results/tables/protocol_comparisons.csv`.

### Follow-up: the model without embeddings on the holdout year

Section `followup` of `configs/default.yaml`, written after the result above was read and before its own runs. The variants are trained again on the training year and applied, frozen, to the holdout year.

| Year | Papers | Variant | AUC | AUC of Initial rating (LR) | Δ | DeLong, Holm |
|---|---|---|---|---|---|---|
| 2025 | All papers | no_text_embeddings | 0.8788 | 0.8733 | +0.0055 [+0.0030, +0.0082] | p < 0.001 |
| 2025 | All papers | no_text_no_critiques | 0.8775 | 0.8733 | +0.0042 [+0.0020, +0.0065] | p < 0.001 |
| 2025 | All papers | no_text_no_shares_concept | 0.8799 | 0.8733 | +0.0066 [+0.0043, +0.0090] | p < 0.001 |
| 2025 | Borderline papers | no_text_embeddings | 0.7346 | 0.7216 | +0.0130 [+0.0044, +0.0221] | p = 0.001 |
| 2025 | Borderline papers | no_text_no_critiques | 0.7303 | 0.7216 | +0.0087 [+0.0014, +0.0172] | p = 0.011 |
| 2025 | Borderline papers | no_text_no_shares_concept | 0.7378 | 0.7216 | +0.0162 [+0.0084, +0.0247] | p < 0.001 |
| 2026 | All papers | no_text_embeddings | 0.8917 | 0.8866 | +0.0051 [+0.0027, +0.0073] | p < 0.001 |
| 2026 | All papers | no_text_no_critiques | 0.8907 | 0.8866 | +0.0041 [+0.0022, +0.0060] | p < 0.001 |
| 2026 | All papers | no_text_no_shares_concept | 0.8928 | 0.8866 | +0.0062 [+0.0040, +0.0082] | p < 0.001 |
| 2026 | Borderline papers | no_text_embeddings | 0.7672 | 0.7563 | +0.0109 [+0.0045, +0.0165] | p < 0.001 |
| 2026 | Borderline papers | no_text_no_critiques | 0.7641 | 0.7563 | +0.0077 [+0.0019, +0.0130] | p < 0.001 |
| 2026 | Borderline papers | no_text_no_shares_concept | 0.7696 | 0.7563 | +0.0133 [+0.0072, +0.0189] | p < 0.001 |

Reading (d), *the model without pretrained embeddings is above the logistic regression on the initial rating*:

| Year | Papers | (d) |
|---|---|---|
| 2025 | All papers | confirmed |
| 2025 | Borderline papers | confirmed |
| 2026 | All papers | confirmed |
| 2026 | Borderline papers | confirmed |

Source: `results/tables/protocol_comparisons.csv`, `results/tables/protocol_readings.csv`.

## Negative and unexpected results

1. **The main hypothesis is not supported.** No heterogeneous GNN reaches a logistic regression on the mean, minimum, maximum and standard deviation of the initial ratings: `hgt` 0.858 against `scores_rating_lr` 0.873 on all papers, 0.695 against 0.722 on borderline papers. (`results/tables/main_results.csv`)
2. **The critiques add nothing measurable to the scores.** Without the graph: -0.0014 [-0.0033, +0.0005] for the logistic regression (`results/tables/paired_comparisons.csv`). The gains seen on validation do not transfer to the test year.
3. **R-GCN is below the untyped GCN** (0.8196 against 0.8308), while HAN and HGT are above it: typing the relations is not enough by itself.
4. **The author responses bring no gain** (setting B against setting A).
5. **Without the scores the graph model fails** (0.5380), below a logistic regression on critique counts (0.7600) and below an MLP on the review text (0.6093). (`results/tables/ablations.csv`, `results/tables/main_results.csv`)
6. **The text of the critiques brings nothing once their typed labels are there** (ablation `no_critique_text`).
7. **The GNNs generalise less well from 2024 to 2025 than the score baselines**, and are less well calibrated.
8. **Gradient attributions are worse than random on fidelity−** (difference from +0.0094 to +0.0292; `results/tables/explainability_fidelity.csv`).
9. **Explanations are unstable across seeds** (rank correlation from 0.426 to 0.661; `results/tables/explainability_seeds.csv`).
10. **In rejected papers, negative critiques push the prediction up**, not down (RQ3).
11. **On the holdout year (2026) the gap between the graph model and the initial ratings is wider**: `hgt` -0.0246 [-0.0288, -0.0207], against -0.0152 on the test year (`results/tables/holdout_2026_tests.csv`).
12. **On 2026 the critique counts added to the scores lower the AUC**: -0.0052 [-0.0072, -0.0033] for the logistic regression (`results/tables/holdout_2026_paired.csv`).
13. **The small gain of the review text over the initial ratings is not found again on 2026**: `text_scores_mlp` +0.0012 [-0.0007, +0.0032].
14. **Calibration does not transfer to 2026**: the expected calibration error of `scores_rating_lr` goes from 0.020 to 0.089 (`results/tables/holdout_2026_vs_test_year.csv`).
15. **Predictions depend on the size of the graph**: predicted again on the extended graph by the same frozen model, the AUC of the test articles changes by up to -0.0276 (`rgcn`; `results/tables/holdout_2026_graph_growth.csv`).

## Limitations

1. **One venue, one field, two years.** Every paper is a machine-learning submission to ICLR; nothing is measured on another field, another venue or another review form. The model is trained on one year and tested on the next.
2. **The labels of the critiques are not validated by humans.** They come from one LLM (Qwen3-14B, temperature 0); no human annotation was made, so their accuracy is not measured. Everything that reads the labels (critique counts, ablations of labels, importance by aspect × severity) inherits this.
3. **Extraction failures.** 1,157 reviews whose author responses could not be aligned, 1 review not segmented, 1 not typed, out of 73,129 (`results/tables/llm_full_v3_summary.csv`; causes in `results/tables/llm_full_v3_failures.csv`). The detailed log of these failures was deleted by mistake on 2026-11-18; only the aggregated causes remain.
4. **Initial text of the reviews.** 21.7 % of the 2024 reviews; 27.6 % of the 2025 reviews were modified after their release (`results/tables/clean_report_by_year.csv`). Their initial scores are known from an external archive, but their text is only available in its final state: OpenReview does not expose earlier versions (answer of its support, 2026-11-19). The LLM sets aside the sentences written after the discussion; a marker of the discussion is still found in 1.8 % of the modified reviews of 2024 and 1.7 % of the modified reviews of 2025 (`results/tables/kg_post_rebuttal_markers.csv`).
5. **Test papers without text.** 1,115 of the 8,655 test papers have no title, abstract nor concept: they are not in the archive taken before the decisions, where every paper of the training year is found (`results/tables/baselines.csv`, `results/tables/article_text_coverage.csv`). The model never sees a paper without text in training.
6. **The test year has been looked at several times.** The critique baselines, the ablations and the explanations were designed after the first test results. ICLR 2026 is the fresh test: the models were frozen before it was looked at (section *Holdout year*).
7. **Multiple comparisons.** 132 DeLong tests in `results/tables/main_results_tests.csv`, plus the paired comparisons and the ablations, first read without correction. The Holm correction of the section *Sensitivity analyses* is applied within each table, not over the whole study.
8. **Hyper-parameter search.** One seed, 839 validation papers of the training year; 8 of the 96 configurations tried for the GNNs ran out of memory (`results/tables/gnn_selection.csv`); the chosen configurations are at the edge of the grid. Full-batch training only.
9. **Intervals.** They count the draw of the papers, not the variability between seeds nor between runs on the GPU.
10. **Explanations.** One architecture, one seed for the means per cell, 1,200 of the 8,655 test papers; occlusion removes one critique at a time, so redundant critiques look unimportant; GNNExplainer was not used (its edge masks do not reach the HGT layers in PyTorch Geometric).
11. **Ablations.** Hyper-parameters are not tuned again for each variant, which makes the variants without scores hard to interpret.
12. **Concept vocabulary counted with the test year.** The keyword concepts and the `shares_concept` edges are counted on the training and test years together, without any label: the graph a model is trained on depends on the keywords of the test papers (section *Sensitivity analyses*). The graph models were trained again on a graph whose vocabulary is counted on the training year alone (section *Protocol checks*). The holdout year was appended with the vocabulary frozen.
13. **Validation and test on different graphs.** Validation papers are predicted on the graph of the training year, test papers on the whole graph, where they are also linked to one another. The check with the following year as validation year predicts both on a graph that holds their year (section *Protocol checks*).
14. **Pretrained models.** The LLM that types the critiques and the two text encoders were trained on data that were not audited. Their weights are dated (`results/tables/pretrained_model_dates.csv`): those of the encoders precede the first review of every year; those of the LLM are later than the decisions of the training and test years, whose public reviews and decisions it may have read, and earlier than the reviews of the holdout year. The reference baseline uses none of them.
15. **Unequal hyper-parameter searches.** In the study, the grids do not have the same size for every family of models, and the weight decay is fixed for the heterogeneous GNNs. An equal and wider search was run afterwards (section *Protocol checks*); the variants without pretrained embeddings were not searched and use the configuration chosen for the model with embeddings.
16. **Status of the protocol checks.** They were added after the test and holdout years had been read. Their design was committed before the runs and each stage was trained once, but they are not confirmations on unseen data, except the reading (d) of the follow-up, written down before the variant was applied to the holdout year.

## Index of tables and figures

| File | Content | Written by | Read from |
|---|---|---|---|
| `results/tables/paper/dataset.tex` | Corpus by year | `scripts/10_consolidate.py` | `results/tables/clean_report_by_year.csv`, `results/tables/kg_statistics.csv` |
| `results/tables/paper/splits.tex` | Temporal split | `scripts/10_consolidate.py` | `results/tables/clean_report_splits.csv` |
| `results/tables/paper/graph.tex` | Nodes and edges of the knowledge graph | `scripts/10_consolidate.py` | `results/tables/kg_statistics.csv` |
| `results/tables/paper/critique_labels.tex` | Labels of the critiques | `scripts/10_consolidate.py` | `results/tables/llm_full_v3_aspect.csv`, `results/tables/llm_full_v3_severity.csv`, `results/tables/llm_full_v3_polarity.csv` |
| `results/tables/paper/main.tex` | RQ1, RQ4: AUC of the main models with confidence intervals | `scripts/10_consolidate.py` | `results/tables/main_results.csv`, `results/tables/main_results_tests.csv` |
| `results/tables/paper/hetero_vs_gcn.tex` | RQ1 (c): heterogeneous GNNs against the GCN | `scripts/10_consolidate.py` | `results/tables/paired_comparisons.csv` |
| `results/tables/paper/critique_baselines.tex` | Critique counts without the graph | `scripts/10_consolidate.py` | `results/tables/paired_comparisons.csv` |
| `results/tables/paper/ablations_delta.tex` | RQ2: ablations, difference with the full graph | `scripts/10_consolidate.py` | `results/tables/ablations.csv` |
| `results/tables/paper/explain_aspect_severity.tex` | RQ3: importance of a critique by aspect and severity | `scripts/10_consolidate.py` | `results/tables/explainability.csv`, `results/tables/explainability_relations.csv` |
| `results/tables/paper/explain_relations.tex` | RQ3: importance of the relations | `scripts/10_consolidate.py` | `results/tables/explainability_relations.csv` |
| `results/tables/paper/explain_fidelity.tex` | RQ3: fidelity of the explanations | `scripts/10_consolidate.py` | `results/tables/explainability_fidelity.csv` |
| `results/tables/paper/robustness_withdrawn.tex` | Robustness: withdrawn papers counted as rejections | `scripts/10_consolidate.py` | `results/tables/main_results_withdrawn_as_reject.csv`, `results/tables/sensitivity_subgroups.csv` |
| `results/tables/paper/hyperparameters.tex` | Chosen hyper-parameters | `scripts/10_consolidate.py` | `results/tables/baselines_selection.csv`, `results/tables/main_results.csv`, `results/tables/gnn_selection.csv` |
| `results/tables/paper/main_full.tex` | Appendix: every model, every metric | `scripts/10_consolidate.py` | `results/tables/main_results.csv` |
| `results/tables/paper/ablations_full.tex` | Appendix: ablations, every metric | `scripts/10_consolidate.py` | `results/tables/ablations.csv` |
| `results/tables/paper/input_audit.tex` | Inputs of the models: source, date and residual risk | `scripts/10_consolidate.py` | `results/tables/input_dates.csv`, `results/tables/kg_post_rebuttal_markers.csv`, `results/tables/baselines.csv`, `results/tables/kg_concept_scope.csv`, `results/tables/clean_report_by_year.csv`, `results/tables/kg_post_rebuttal_markers_holdout.csv`, `results/tables/pretrained_model_dates.csv` |
| `results/tables/paper/model_inputs.tex` | Information read by each model | `scripts/10_consolidate.py` |  |
| `results/tables/paper/sensitivity_pairs.tex` | Sensitivity: pairs of models compared afterwards | `scripts/10_consolidate.py` | `results/tables/sensitivity_pairs.csv`, `results/tables/tests_holm.csv` |
| `results/tables/paper/sensitivity_text.tex` | Sensitivity: test papers with text | `scripts/10_consolidate.py` | `results/tables/sensitivity_subgroups.csv` |
| `results/tables/paper/sensitivity_zones.tex` | Sensitivity: other definitions of the borderline zone | `scripts/10_consolidate.py` | `results/tables/sensitivity_borderline_zones.csv`, `results/tables/sensitivity_borderline.csv` |
| `results/tables/paper/holm.tex` | Sensitivity: Holm correction of the tests of each table | `scripts/10_consolidate.py` | `results/tables/tests_holm.csv` |
| `results/tables/paper/holdout.tex` | Holdout year: AUC of the frozen models | `scripts/10_consolidate.py` | `results/tables/holdout_2026.csv`, `results/tables/holdout_2026_tests.csv` |
| `results/tables/paper/holdout_paired.tex` | Holdout year: models against their controls, next to the test year | `scripts/10_consolidate.py` | `results/tables/paired_comparisons.csv`, `results/tables/holdout_2026_paired.csv` |
| `results/tables/paper/protocol_test.tex` | Protocol checks: every model against the initial rating, test year | `scripts/10_consolidate.py` | `results/tables/protocol_comparisons.csv`, `results/tables/main_results.csv`, `results/tables/main_results_tests.csv` |
| `results/tables/paper/protocol_holdout.tex` | Protocol checks: every model against the initial rating, holdout year | `scripts/10_consolidate.py` | `results/tables/protocol_comparisons.csv`, `results/tables/holdout_2026.csv`, `results/tables/holdout_2026_tests.csv` |
| `results/tables/paper/protocol_readings.tex` | Protocol checks: conclusions (a) and (b) under each check | `scripts/10_consolidate.py` | `results/tables/protocol_readings.csv` |
| `results/tables/paper/protocol_vs_study_test.tex` | Protocol checks: each model against the same model of the study, test year | `scripts/10_consolidate.py` | `results/tables/protocol_comparisons.csv` |
| `results/tables/paper/protocol_vs_study_holdout.tex` | Protocol checks: each model against the same model of the study, holdout year | `scripts/10_consolidate.py` | `results/tables/protocol_comparisons.csv` |
| `results/tables/paper/protocol_configurations.tex` | Protocol checks: configurations kept by the searches | `scripts/10_consolidate.py` | `results/tables/protocol_search_chosen.csv`, `results/tables/protocol_rolling_chosen.csv` |
| `results/tables/paper/protocol_encoders.tex` | Protocol checks: the main model without the pretrained encoders | `scripts/10_consolidate.py` | `results/tables/protocol_comparisons.csv` |
| `results/tables/paper/followup.tex` | Follow-up: the graph model without pretrained embeddings on the test and holdout years | `scripts/10_consolidate.py` | `results/tables/protocol_comparisons.csv` |
| `results/figures/main_results.pdf` | RQ1, RQ4: test AUC of the main models with confidence intervals | `scripts/10_consolidate.py` | `results/tables/main_results.csv`, `results/tables/main_results_tests.csv` |
| `results/figures/borderline_zone.pdf` | Definition of the borderline zone on the training papers | `scripts/10_consolidate.py` | `results/tables/borderline_definition.csv` |
| `results/figures/critique_labels.pdf` | Labels of the critiques | `scripts/10_consolidate.py` | `results/tables/llm_full_v3_aspect.csv`, `results/tables/llm_full_v3_severity.csv`, `results/tables/llm_full_v3_polarity.csv` |
| `results/figures/holdout_results.pdf` | Holdout year: AUC of the frozen models with confidence intervals | `scripts/10_consolidate.py` | `results/tables/holdout_2026.csv`, `results/tables/holdout_2026_tests.csv` |
| `results/tables/baselines.tex` | Baselines, every metric (appendix) | `scripts/06_baselines.py` | `results/predictions/baselines.parquet` |
| `results/tables/main_results.tex` | Baselines and GNNs, every metric (appendix) | `scripts/07b_main_results.py` | `results/predictions/baselines.parquet`, `results/predictions/gnn.parquet` |
| `results/tables/ablations.tex` | Ablations, every metric (appendix) | `scripts/08b_ablation_results.py` | `results/predictions/ablations.parquet`, `results/predictions/gnn.parquet`, `results/predictions/baselines.parquet` |
| `results/figures/ablations.pdf` | RQ2: AUC difference of each ablation with the full graph | `scripts/08b_ablation_results.py` | `results/tables/ablations.csv` |
| `results/figures/explain_aspect_severity.pdf` | RQ3: importance of a critique by aspect and severity | `scripts/09b_explain_results.py` | `results/tables/explainability.csv` |
| `results/figures/explain_relations.pdf` | RQ3: importance of the relations | `scripts/09b_explain_results.py` | `results/tables/explainability_relations.csv` |
| `results/figures/explain_fidelity.pdf` | RQ3: fidelity of the explanations | `scripts/09b_explain_results.py` | `results/tables/explainability_fidelity.csv` |
| `results/figures/explain_case_accepted_predicted_accept.pdf` | RQ3: case study, accepted predicted accept | `scripts/09b_explain_results.py` | `results/tables/explainability_cases.csv` |
| `results/figures/explain_case_accepted_predicted_reject.pdf` | RQ3: case study, accepted predicted reject | `scripts/09b_explain_results.py` | `results/tables/explainability_cases.csv` |
| `results/figures/explain_case_rejected_predicted_accept.pdf` | RQ3: case study, rejected predicted accept | `scripts/09b_explain_results.py` | `results/tables/explainability_cases.csv` |
| `results/figures/explain_case_rejected_predicted_reject.pdf` | RQ3: case study, rejected predicted reject | `scripts/09b_explain_results.py` | `results/tables/explainability_cases.csv` |
| `results/tables/holdout_2026.tex` | Holdout year: every model, every metric | `scripts/07d_holdout_results.py` | `results/predictions/holdout_2026.parquet` |

