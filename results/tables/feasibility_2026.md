# Feasibility of ICLR 2026 (raw collection only)

Manifest: `full_20261118_231715.json`. API v2. Text archive: `data/iclr26v1.parquet` at commit `04f114e` (2025-10-10).

## Papers

| status | papers |
|---|---|
| rejected | 8345 |
| accepted | 5351 |
| withdrawn | 5210 |
| desk_rejected | 908 |

- Papers that are not desk rejected: 18906, of which with at least one review: 18789.
- Papers with an author reply: 14654.

Decision notes (text as stored):

| decision | papers |
|---|---|
| Reject | 8816 |
| (no decision note) | 5639 |
| Accept (Poster) | 5134 |
| Accept (Oral) | 225 |

## Reviews

- Reviews in total: 75859; of papers that are not desk rejected: 73213 (what the critique extraction would read, before the eligibility rules of the cleaning step).
- By status of the paper: {'rejected': 32509, 'accepted': 20903, 'withdrawn': 19801}.
- Posted after the first author reply of their forum: 12 (0.0002).

Content fields (share of these reviews):

| field | share |
|---|---|
| code_of_conduct | 1.0 |
| confidence | 1.0 |
| contribution | 1.0 |
| flag_for_ethics_review | 1.0 |
| presentation | 1.0 |
| questions | 1.0 |
| rating | 1.0 |
| soundness | 1.0 |
| strengths | 1.0 |
| summary | 1.0 |
| weaknesses | 1.0 |
| details_of_ethics_concerns | 0.0796 |

## Score scales (values as stored)

| field | value_as_stored | parsed | n_reviews | share |
|---|---|---|---|---|
| confidence | 1 | 1 | 272 | 0.0037 |
| confidence | 2 | 2 | 4983 | 0.0681 |
| confidence | 3 | 3 | 25127 | 0.3432 |
| confidence | 4 | 4 | 34305 | 0.4686 |
| confidence | 5 | 5 | 8526 | 0.1165 |
| contribution | 1 | 1 | 6416 | 0.0876 |
| contribution | 2 | 2 | 37692 | 0.5148 |
| contribution | 3 | 3 | 26635 | 0.3638 |
| contribution | 4 | 4 | 2470 | 0.0337 |
| presentation | 1 | 1 | 4954 | 0.0677 |
| presentation | 2 | 2 | 24066 | 0.3287 |
| presentation | 3 | 3 | 39030 | 0.5331 |
| presentation | 4 | 4 | 5163 | 0.0705 |
| rating | 0 | 0 | 1208 | 0.0165 |
| rating | 2 | 2 | 19071 | 0.2605 |
| rating | 4 | 4 | 28837 | 0.3939 |
| rating | 6 | 6 | 19099 | 0.2609 |
| rating | 8 | 8 | 4813 | 0.0657 |
| rating | 10 | 10 | 185 | 0.0025 |
| soundness | 1 | 1 | 4107 | 0.0561 |
| soundness | 2 | 2 | 28818 | 0.3936 |
| soundness | 3 | 3 | 36417 | 0.4974 |
| soundness | 4 | 4 | 3871 | 0.0529 |

Rating: share of each level, in the order of the scale; initial ratings for the study years (`data/interim/reviews.parquet`), current ratings for the candidate year.

| level | value_2024 | value_2025 | value_2026 | share_2024 | share_2025 | share_2026 |
|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 0 | 0.0237 | 0.0241 | 0.0165 |
| 2 | 3 | 3 | 2 | 0.2942 | 0.302 | 0.2605 |
| 3 | 5 | 5 | 4 | 0.3391 | 0.3563 | 0.3939 |
| 4 | 6 | 6 | 6 | 0.2413 | 0.2372 | 0.2609 |
| 5 | 8 | 8 | 8 | 0.0985 | 0.0779 | 0.0657 |
| 6 | 10 | 10 | 10 | 0.0032 | 0.0024 | 0.0025 |

Mean rating: {2024: 4.87, 2025: 4.782, 2026: 4.213}.

## Dates of the reviews (UTC)

- End of the densest burst of last modifications (estimated release, `report.release_burst_end`): 2025-11-12 06:21.
- Reviews last modified after that burst, and more than a minute after their creation: 22032 (0.3009).

Hours with at least 20 last modifications:

| hour_utc | reviews_last_modified |
|---|---|
| 2025-11-12 02:00 | 6399 |
| 2025-11-12 03:00 | 13612 |
| 2025-11-12 04:00 | 13906 |
| 2025-11-12 05:00 | 12913 |
| 2025-11-12 06:00 | 4250 |
| 2025-11-12 07:00 | 5180 |
| 2025-11-12 08:00 | 176 |
| 2025-11-12 09:00 | 653 |
| 2025-11-12 10:00 | 9938 |
| 2025-11-13 02:00 | 433 |
| 2025-11-28 19:00 | 4376 |
| 2025-11-28 20:00 | 1175 |
| 2025-11-28 21:00 | 42 |
| 2025-11-29 02:00 | 28 |

Last modification of each review (windows of `collect.review_events` in the config):

| last_modification | reviews | share |
|---|---|---|
| release | 67433 | 0.92105 |
| revert | 5621 | 0.07678 |
| never_modified | 154 | 0.0021 |
| other | 5 | 7e-05 |

Per day:

| day_utc | reviews_created | reviews_last_modified |
|---|---|---|
| 2025-10-14 | 165 | 0 |
| 2025-10-15 | 557 | 0 |
| 2025-10-16 | 619 | 0 |
| 2025-10-17 | 626 | 0 |
| 2025-10-18 | 489 | 0 |
| 2025-10-19 | 595 | 0 |
| 2025-10-20 | 854 | 0 |
| 2025-10-21 | 871 | 0 |
| 2025-10-22 | 722 | 0 |
| 2025-10-23 | 1020 | 0 |
| 2025-10-24 | 1143 | 0 |
| 2025-10-25 | 1707 | 0 |
| 2025-10-26 | 2432 | 0 |
| 2025-10-27 | 3823 | 0 |
| 2025-10-28 | 4290 | 0 |
| 2025-10-29 | 5409 | 0 |
| 2025-10-30 | 8258 | 0 |
| 2025-10-31 | 14552 | 0 |
| 2025-11-01 | 14581 | 0 |
| 2025-11-02 | 3062 | 0 |
| 2025-11-03 | 2825 | 0 |
| 2025-11-04 | 1449 | 0 |
| 2025-11-05 | 741 | 0 |
| 2025-11-06 | 549 | 0 |
| 2025-11-07 | 412 | 0 |
| 2025-11-08 | 315 | 0 |
| 2025-11-09 | 267 | 0 |
| 2025-11-10 | 353 | 0 |
| 2025-11-11 | 295 | 0 |
| 2025-11-12 | 129 | 67068 |
| 2025-11-13 | 24 | 451 |
| 2025-11-14 | 26 | 23 |
| 2025-11-15 | 5 | 4 |
| 2025-11-16 | 10 | 9 |
| 2025-11-17 | 9 | 8 |
| 2025-11-18 | 4 | 3 |
| 2025-11-19 | 3 | 3 |
| 2025-11-20 | 5 | 4 |
| 2025-11-21 | 8 | 8 |
| 2025-11-22 | 1 | 1 |
| 2025-11-23 | 2 | 1 |
| 2025-11-24 | 1 | 1 |
| 2025-11-25 | 2 | 1 |
| 2025-11-26 | 2 | 2 |
| 2025-11-27 | 1 | 1 |
| 2025-11-28 | 0 | 5595 |
| 2025-11-29 | 0 | 29 |
| 2025-12-17 | 0 | 1 |

## Replies by kind

| kind | by_authors | n | first_day | last_day |
|---|---|---|---|---|
| decision | False | 14175 | 2026-01-26 | 2026-01-26 |
| desk_rejection | False | 908 | 2025-10-04 | 2026-04-18 |
| meta_review | False | 14175 | 2025-12-02 | 2026-01-25 |
| official_comment | False | 20692 | 2025-10-18 | 2026-04-18 |
| official_comment | True | 159454 | 2025-11-12 | 2025-12-04 |
| public_comment | False | 404 | 2025-11-12 | 2026-11-16 |
| review | False | 75859 | 2025-10-14 | 2025-11-27 |
| withdrawal | False | 6 | 2025-10-30 | 2026-03-31 |
| withdrawal | True | 5221 | 2025-09-25 | 2026-11-12 |

## Text of the submissions before the decisions

Archive rows for 2026: 19793.

| status | papers | found_in_archive | current_abstracts_with_link | archive_abstracts_with_link | title_differs_from_current | abstract_differs_from_current | archive_without_keywords |
|---|---|---|---|---|---|---|---|
| accepted | 5351 | 1.0 | 0.2304 | 0.0725 | 0.0848 | 0.504 | 0.0 |
| rejected | 8345 | 1.0 | 0.0635 | 0.062 | 0.0 | 0.1566 | 0.0 |
| withdrawn | 5210 | 0.9998 | 0.0735 | 0.0733 | 0.0 | 0.0447 | 0.0 |
