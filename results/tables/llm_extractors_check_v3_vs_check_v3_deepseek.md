# Two extraction runs on the same reviews: `check_v3` (reference) and `check_v3_deepseek`

| metric | value |
|---|---|
| reviews in both runs | 200.0 |
| reviews segmented and typed by both | 198.0 |
| failures of check_v3 (segmentation or typing) | 0.0 |
| failures of check_v3_deepseek (segmentation or typing) | 2.0 |
| units compared | 3944.0 |
| share of units with the same fate (critique / ignored / post-rebuttal) | 0.9698 |
| critiques of check_v3 | 1528.0 |
| critiques of check_v3_deepseek | 1637.0 |
| critiques with exactly the same units in both runs | 1144.0 |
| share of the critiques of check_v3 found in check_v3_deepseek | 0.7487 |
| share of the critiques of check_v3_deepseek found in check_v3 | 0.6988 |
| check_v3_deepseek: model served | deepseek-flash bc19ba97cbe016479903222bb1578db6 |
| check_v3_deepseek: reviews, seconds, concurrency | 200, 24.7, 48 |
| check_v3_deepseek: cost of the run (USD) | 0.1244 |
| check_v3_deepseek: share of the prompt tokens served from the provider's cache | 0.524 |
| check_v3_deepseek: time extrapolated to 73185 reviews (hours, same pace) | 2.51 |
| check_v3_deepseek: cost extrapolated to 73185 reviews (USD, same prices and cache share) | 45.5 |

## Fate of each unit (rows: reference, columns: other)

| reference | critique | ignored | post_rebuttal |
|---|---|---|---|
| critique | 3437 | 46 | 0 |
| ignored | 60 | 370 | 0 |
| post_rebuttal | 1 | 12 | 18 |

## Labels of the critiques that have the same units in both runs

| label | critiques_compared | agreement | cohen_kappa |
|---|---|---|---|
| aspect | 1144 | 0.7692 | 0.7142 |
| severity | 1144 | 0.8357 | 0.6515 |
| polarity | 1144 | 0.9196 | 0.8669 |
| target | 1144 | 0.8191 | 0.7339 |
| actionable | 1144 | 0.9747 | 0.9471 |

## Counts per review

| count_per_review | mean_reference | mean_other | pearson | share_of_reviews_equal |
|---|---|---|---|---|
| critiques | 7.717 | 8.268 | 0.7766 | 0.404 |
| severity_blocking | 0.121 | 0.056 | 0.5514 | 0.9141 |
| severity_major | 2.859 | 3.51 | 0.6242 | 0.2626 |
| severity_minor | 4.737 | 4.702 | 0.6209 | 0.2475 |
| polarity_negative | 3.934 | 4.419 | 0.6735 | 0.4646 |
| polarity_positive | 2.753 | 2.692 | 0.7048 | 0.7071 |
| polarity_neutral | 1.03 | 1.157 | 0.4701 | 0.5606 |
| negative_blocking_or_major | 2.515 | 2.808 | 0.7289 | 0.5152 |
