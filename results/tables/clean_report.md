# Cleaning report

Tables in `data/interim/` (desk-rejected submissions excluded): `papers` (37859 rows), `reviews` (147887 rows), `reviews_final` (147887 rows), `discussion` (394447 rows), `outcomes` (37859 rows).

## Per year

| metric | 2024 | 2025 | 2026 |
|---|---|---|---|
| release_end_utc | 2023-11-10 17:26 | 2024-11-12 16:41 | 2025-11-12 11:00 |
| desk_rejected_excluded | 53 | 70 | 908 |
| papers | 7351 | 11602 | 18906 |
| decision_oral | 86 | 213 | 224 |
| decision_spotlight | 367 | 380 | 0 |
| decision_poster | 1808 | 3115 | 5133 |
| decision_reject | 3519 | 5019 | 8816 |
| papers_with_decision | 5780 | 8727 | 14173 |
| acceptance_rate_with_decision | 0.3912 | 0.4249 | 0.378 |
| withdrawn | 1661 | 2992 | 5210 |
| withdrawn_before_decision | 1571 | 2875 | 4733 |
| withdrawn_after_decision | 90 | 117 | 477 |
| withdrawn_before_decision_without_review | 108 | 90 | 117 |
| eligible_withdrawn_excluded | 5534 | 8655 | 14169 |
| acceptance_rate_withdrawn_excluded | 0.393 | 0.425 | 0.378 |
| eligible_withdrawn_as_reject | 6954 | 11422 | 18785 |
| acceptance_rate_withdrawn_as_reject | 0.3128 | 0.322 | 0.2851 |
| reviews | 27962 | 46712 | 73213 |
| reviews_before_author_response | 27871 | 46690 | 73201 |
| reviews_after_author_response | 91 | 22 | 12 |
| reviews_with_initial_scores | 26812 | 46317 | 73208 |
| share_reviews_with_initial_scores | 0.9589 | 0.9915 | 0.9999 |
| reviews_created_after_release | 353 | 156 | 153 |
| reviews_modified_after_release | 6056 | 12889 | 5626 |
| share_reviews_modified_after_release | 0.2166 | 0.2759 | 0.0768 |
| reviews_rating_changed | 5007 | 11365 | 0 |
| share_reviews_rating_changed | 0.1867 | 0.2454 | 0.0 |
| mean_rating_initial | 4.87 | 4.782 | 4.884 |
| mean_rating_final_same_reviews | 5.145 | 5.15 | 4.884 |
| papers_with_author_response | 5915 | 8698 | 14090 |
| discussion_notes | 70792 | 149762 | 173893 |
| discussion_before_author_response | 206 | 581 | 315 |
| discussion_after_author_response | 70586 | 149181 | 173578 |
| discussion_by_authors | 55910 | 114945 | 153555 |
| discussion_by_reviewer | 13978 | 32919 | 18847 |
| discussion_by_area_chair | 520 | 1220 | 1089 |
| discussion_by_senior_area_chair | 1 | 4 | 0 |
| discussion_by_program_chairs | 1 | 10 | 3 |
| discussion_by_public | 382 | 664 | 399 |
| author_replies | 55910 | 114945 | 153555 |
| author_replies_aligned_on_a_review | 50245 | 105493 | 136562 |
| share_author_replies_aligned | 0.8987 | 0.9178 | 0.8893 |
| author_replies_to_the_submission | 5645 | 9388 | 16950 |
| author_replies_parent_unknown | 20 | 64 | 43 |
| author_replies_under_meta_review_or_decision | 0 | 0 | 0 |
| reviews_with_an_author_reply | 22308 | 34139 | 53701 |
| share_reviews_with_an_author_reply | 0.7978 | 0.7308 | 0.7335 |
| papers_with_meta_review | 5780 | 8727 | 14173 |
| papers_missing_abstract | 0 | 0 | 0 |
| papers_missing_keywords | 0 | 0 | 0 |
| papers_with_tldr | 4223 | 6700 | 9824 |
| median_abstract_words | 183.0 | 185.0 | 182.0 |
| median_review_words | 372.0 | 388.0 | 391.0 |

## Score scales: distinct values per year

| score | version | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| rating | initial | 1 3 5 6 8 10 | 1 3 5 6 8 10 | 1 3 5 6 8 10 |
| rating | final | 1 3 5 6 8 10 | 1 3 5 6 8 10 | 1 3 5 6 8 10 |
| confidence | initial | 1 2 3 4 5 | 1 2 3 4 5 | 1 2 3 4 5 |
| confidence | final | 1 2 3 4 5 | 1 2 3 4 5 | 1 2 3 4 5 |
| soundness | initial | 1 2 3 4 | 1 2 3 4 | 1 2 3 4 |
| soundness | final | 1 2 3 4 | 1 2 3 4 | 1 2 3 4 |
| presentation | initial | not available | 1 2 3 4 | 1 2 3 4 |
| presentation | final | 1 2 3 4 | 1 2 3 4 | 1 2 3 4 |
| contribution | initial | 1 2 3 4 | 1 2 3 4 | 1 2 3 4 |
| contribution | final | 1 2 3 4 | 1 2 3 4 | 1 2 3 4 |

## Score scales: value stored by OpenReview and integer kept

(Stored values are cut at 70 characters.)

| score | year | integer | stored_value |
|---|---|---|---|
| confidence | 2024 | 1 | 1: You are unable to assess this paper and have alerted the ACs to see |
| confidence | 2024 | 2 | 2: You are willing to defend your assessment, but it is quite likely t |
| confidence | 2024 | 3 | 3: You are fairly confident in your assessment. It is possible that yo |
| confidence | 2024 | 4 | 4: You are confident in your assessment, but not absolutely certain. I |
| confidence | 2024 | 5 | 5: You are absolutely certain about your assessment. You are very fami |
| confidence | 2025 | 1 | 1 |
| confidence | 2025 | 2 | 2 |
| confidence | 2025 | 3 | 3 |
| confidence | 2025 | 4 | 4 |
| confidence | 2025 | 5 | 5 |
| confidence | 2026 | 1 | 1 |
| confidence | 2026 | 2 | 2 |
| confidence | 2026 | 3 | 3 |
| confidence | 2026 | 4 | 4 |
| confidence | 2026 | 5 | 5 |
| contribution | 2024 | 1 | 1 poor |
| contribution | 2024 | 2 | 2 fair |
| contribution | 2024 | 3 | 3 good |
| contribution | 2024 | 4 | 4 excellent |
| contribution | 2025 | 1 | 1 |
| contribution | 2025 | 2 | 2 |
| contribution | 2025 | 3 | 3 |
| contribution | 2025 | 4 | 4 |
| contribution | 2026 | 1 | 1 |
| contribution | 2026 | 2 | 2 |
| contribution | 2026 | 3 | 3 |
| contribution | 2026 | 4 | 4 |
| presentation | 2024 | 1 | 1 poor |
| presentation | 2024 | 2 | 2 fair |
| presentation | 2024 | 3 | 3 good |
| presentation | 2024 | 4 | 4 excellent |
| presentation | 2025 | 1 | 1 |
| presentation | 2025 | 2 | 2 |
| presentation | 2025 | 3 | 3 |
| presentation | 2025 | 4 | 4 |
| presentation | 2026 | 1 | 1 |
| presentation | 2026 | 2 | 2 |
| presentation | 2026 | 3 | 3 |
| presentation | 2026 | 4 | 4 |
| rating | 2024 | 1 | 1: strong reject |
| rating | 2024 | 3 | 3: reject, not good enough |
| rating | 2024 | 5 | 5: marginally below the acceptance threshold |
| rating | 2024 | 6 | 6: marginally above the acceptance threshold |
| rating | 2024 | 8 | 8: accept, good paper |
| rating | 2024 | 10 | 10: strong accept, should be highlighted at the conference |
| rating | 2025 | 1 | 1 |
| rating | 2025 | 3 | 3 |
| rating | 2025 | 5 | 5 |
| rating | 2025 | 6 | 6 |
| rating | 2025 | 8 | 8 |
| rating | 2025 | 10 | 10 |
| rating | 2026 | 1 | 0 |
| rating | 2026 | 3 | 2 |
| rating | 2026 | 5 | 4 |
| rating | 2026 | 6 | 6 |
| rating | 2026 | 8 | 8 |
| rating | 2026 | 10 | 10 |
| soundness | 2024 | 1 | 1 poor |
| soundness | 2024 | 2 | 2 fair |
| soundness | 2024 | 3 | 3 good |
| soundness | 2024 | 4 | 4 excellent |
| soundness | 2025 | 1 | 1 |
| soundness | 2025 | 2 | 2 |
| soundness | 2025 | 3 | 3 |
| soundness | 2025 | 4 | 4 |
| soundness | 2026 | 1 | 1 |
| soundness | 2026 | 2 | 2 |
| soundness | 2026 | 3 | 3 |
| soundness | 2026 | 4 | 4 |

## Splits of the papers usable in setting A, by treatment of withdrawn papers

A paper is usable if it has a label and an initial rating for every review posted before the first author response. Reviews: those posted before the author response.

| withdrawn | split | year | papers | accepted | rejected | acceptance_rate | reviews |
|---|---|---|---|---|---|---|---|
| excluded | holdout | 2026 | 14169 | 5356 | 8813 | 0.378 | 55215 |
| excluded | test | 2025 | 8655 | 3678 | 4977 | 0.425 | 35035 |
| excluded | train | 2024 | 4695 | 1861 | 2834 | 0.3964 | 18149 |
| excluded | val | 2024 | 839 | 314 | 525 | 0.3743 | 3229 |
| as_reject | holdout | 2026 | 18785 | 5356 | 13429 | 0.2851 | 73185 |
| as_reject | test | 2025 | 11422 | 3678 | 7744 | 0.322 | 46317 |
| as_reject | train | 2024 | 5906 | 1861 | 4045 | 0.3151 | 22779 |
| as_reject | val | 2024 | 1048 | 314 | 734 | 0.2996 | 4033 |

## Discussion notes by role and phase

| year | role | after_author_response | before_author_response |
|---|---|---|---|
| 2024 | area_chair | 478 | 42 |
| 2024 | authors | 55910 | 0 |
| 2024 | program_chairs | 1 | 0 |
| 2024 | public | 312 | 70 |
| 2024 | reviewer | 13884 | 94 |
| 2024 | senior_area_chair | 1 | 0 |
| 2025 | area_chair | 1128 | 92 |
| 2025 | authors | 114945 | 0 |
| 2025 | program_chairs | 10 | 0 |
| 2025 | public | 564 | 100 |
| 2025 | reviewer | 32531 | 388 |
| 2025 | senior_area_chair | 3 | 1 |
| 2026 | area_chair | 1017 | 72 |
| 2026 | authors | 153555 | 0 |
| 2026 | program_chairs | 3 | 0 |
| 2026 | public | 306 | 93 |
| 2026 | reviewer | 18697 | 150 |

## Initial scores available, by paper status

| year | status | reviews | with_initial_scores | share_with_initial_scores |
|---|---|---|---|---|
| 2024 | accepted | 8742 | 8407 | 0.9617 |
| 2024 | rejected | 13269 | 12639 | 0.9525 |
| 2024 | withdrawn | 5951 | 5766 | 0.9689 |
| 2025 | accepted | 14936 | 14800 | 0.9909 |
| 2025 | rejected | 19944 | 19768 | 0.9912 |
| 2025 | withdrawn | 11832 | 11749 | 0.993 |
| 2026 | accepted | 20903 | 20901 | 0.9999 |
| 2026 | rejected | 32509 | 32506 | 0.9999 |
| 2026 | withdrawn | 19801 | 19801 | 1.0 |

## Score fields: external post-rebuttal value versus our final value

| year | field | reviews_compared | initial_available | share_ext_post_equals_final |
|---|---|---|---|---|
| 2024 | rating | 26812 | 26812 | 1.0 |
| 2024 | confidence | 26812 | 26812 | 1.0 |
| 2024 | soundness | 26812 | 26812 | 1.0 |
| 2024 | presentation | 0 | 0 | — |
| 2024 | contribution | 26812 | 26812 | 1.0 |
| 2025 | rating | 46317 | 46317 | 1.0 |
| 2025 | confidence | 46317 | 46317 | 1.0 |
| 2025 | soundness | 46317 | 46317 | 1.0 |
| 2025 | presentation | 46317 | 46317 | 1.0 |
| 2025 | contribution | 46317 | 46317 | 1.0 |
| 2026 | rating | 0 | 73208 | — |
| 2026 | confidence | 0 | 73208 | — |
| 2026 | soundness | 0 | 73208 | — |
| 2026 | presentation | 0 | 73208 | — |
| 2026 | contribution | 0 | 73208 | — |
