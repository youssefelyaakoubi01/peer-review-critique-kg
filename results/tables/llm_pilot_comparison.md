# Comparison of critique-extraction runs

One column per run (`data/interim/llm/<run>/`). The checks flag problems, they do not measure accuracy; see `src/llm/checks.py` and the report of each run. A time estimate is missing when a pass was entirely served from the cache.

| figure | pilot | dev_v2 | dev_v3 | dev_v4 | check_v1 | check_v3 |
|---|---|---|---|---|---|---|
| sample | dev | dev | dev | dev | check | check |
| prompts | segment_v1, type_v1, align_v2 | segment_v2, type_v1, align_v3 | segment_v3, type_v1, align_v3 | segment_v4, type_v1, align_v3 | segment_v1, type_v1, align_v2 | segment_v3, type_v1, align_v3 |
| reviews | 200 | 200 | 200 | 200 | 200 | 200 |
| critiques | 1740 | 1557 | 1553 | 1587 | 1805 | 1544 |
| critiques_per_review_mean | 8.7 | 7.79 | 7.76 | 7.93 | 9.03 | 7.72 |
| critiques_per_review_median | 7.5 | 7.0 | 7.0 | 7.0 | 8.0 | 7.0 |
| share_units_ignored | 0.0363 | 0.2222 | 0.0968 | 0.1012 | 0.0459 | 0.1079 |
| share_units_post_rebuttal | 0.0037 | 0.0031 | 0.0094 | 0.0052 | 0.0052 | 0.0077 |
| critiques_like_bibliography_entry | 12 | 0 | 0 | 0 | 17 | 0 |
| critiques_like_heading | 13 | 3 | 0 | 0 | 7 | 0 |
| critiques_like_pointer_or_thanks | 25 | 0 | 0 | 0 | 28 | 0 |
| critiques_like_junk | 50 | 3 | 0 | 0 | 52 | 0 |
| junk_like_units | 180 | 180 | 180 | 180 | 199 | 199 |
| share_junk_like_units_kept_in_a_critique | 0.6389 | 0.1111 | 0.0444 | 0.0333 | 0.5528 | 0.0754 |
| ignored_units | 139 | 852 | 371 | 388 | 184 | 432 |
| long_ignored_units_not_junk_like | 26 | 325 | 43 | 52 | 24 | 63 |
| share_one_line_neighbours_split | 0.1582 | 0.1515 | 0.0801 | 0.0598 | 0.1733 | 0.0814 |
| share_two_line_neighbours_merged | 0.3503 | 0.1994 | 0.2274 | 0.2221 | 0.3798 | 0.3066 |
| reviews_with_author_reply | 164 | 156 | 164 | 164 | 161 | 161 |
| critiques_with_a_response | 660 | 599 | 653 | 685 | 693 | 664 |
| responses_to_positive_critiques | 29 | 9 | 2 | 2 | 19 | 5 |
| share_aligned_negative_critiques_with_a_response | 0.7311 | 0.7947 | 0.8285 | 0.8377 | 0.8269 | 0.8297 |
| response_spans_quoting_a_critique | 302 | 145 | 151 | 167 | 300 | 135 |
| share_quoting_spans_assigned_to_the_quoted_critique | 0.4801 | 0.6207 | 0.6556 | 0.6527 | 0.5567 | 0.6889 |
| quote_zones | 368 | 293 | 370 | 365 | 350 | 385 |
| share_quote_zones_given_to_the_quoted_critique | 0.663 | 0.9317 | 0.9405 | 0.9397 | 0.7886 | 0.8909 |
| quotations_followed_by_a_span | 306 | 275 | 350 | 342 | 299 | 373 |
| share_first_span_after_a_quotation_naming_it | 0.6438 | 0.9236 | 0.9571 | 0.962 | 0.7224 | 0.882 |
| segment_retries | 0 | 68 | 0 | 0 | 1 | 0 |
| segment_failures | 0 | 10 | 0 | 0 | 0 | 0 |
| type_retries | 0 | 0 | 0 | 0 | 2 | 0 |
| type_failures | 0 | 0 | 0 | 0 | 0 | 0 |
| align_retries | 2 | 14 | 4 | 7 | 3 | 10 |
| align_failures | 0 | 2 | 1 | 2 | 1 | 3 |
| segment_estimated_corpus_hours | 7.0 | 10.3 | 10.2 | 10.6 | 8.6 | 12.3 |
| type_estimated_corpus_hours | 11.5 | 10.9 | 11.8 | 12.2 | 20.6 | 11.7 |
| align_estimated_corpus_hours | 21.2 | 21.5 | 22.9 | 23.4 | 26.5 | 22.8 |
| estimated_corpus_hours | 39.7 | 42.7 | 44.9 | 46.2 | 55.7 | 46.8 |
