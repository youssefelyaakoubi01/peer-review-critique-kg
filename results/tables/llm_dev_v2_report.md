# Critique extraction report (dev_v2)

Sample `dev`, model `Qwen/Qwen3-14B-AWQ` (revision `31c69efc29464b6bb0aee1398b5a7b50a99340c3`), prompts `segment_v2`, `type_v1`, `align_v3`, 32 simultaneous requests, temperature 0.

## Passes and throughput

| step | items | seconds | calls | cache_hits | retries | failures | prompt_tokens | completion_tokens | seconds_per_item | output_tokens_per_second | corpus_items | estimated_corpus_hours |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| segment | 200 | 101.67 | 268 | 0 | 68 | 10 | 505838 | 31581 | 0.508 | 310.6 | 73129 | 10.3 |
| type | 190 | 81.29 | 151 | 39 | 0 | 0 | 286280 | 36471 | 0.538 | 448.7 | 73129 | 10.9 |
| align | 156 | 218.38 | 170 | 0 | 14 | 2 | 849567 | 17604 | 1.4 | 80.6 | 55192 | 21.5 |

Estimated time for the full corpus (73129 reviews, 55192 with author replies): **42.7 hours**, extrapolated from the time per item sent to the model at this concurrency. It does not include the loading of the model.
Some items were served from the cache: the time per item only counts the others.

## Summary

| metric | value |
|---|---|
| reviews | 200 |
| reviews_with_critiques | 190 |
| critiques | 1557 |
| critiques_per_review_mean | 7.79 |
| critiques_per_review_median | 7.0 |
| critiques_per_review_max | 34 |
| share_units_in_critiques | 0.7746 |
| share_units_ignored | 0.2222 |
| share_units_post_rebuttal | 0.0031 |
| reviews_with_post_rebuttal_units | 6 |
| reviews_truncated | 0 |
| replies_truncated | 0 |
| segment_failed | 10 |
| type_failed | 0 |
| align_failed | 2 |
| reviews_with_author_reply | 156 |
| critiques_typed | 1557 |
| critiques_aligned | 1207 |
| critiques_with_a_response | 599 |

## Automatic sanity checks

No human label is involved: these checks flag problems, they do not measure accuracy (definitions in `src/llm/checks.py`).
- `critiques_like_*`: critiques that look like something the prompt says to leave out.
- `junk_like_units`: sentences of the reviews that look like a bibliography entry, a pointer, thanks or a bare heading, and the share of them kept inside a critique.
- `long_ignored_units_not_junk_like`: ignored sentences of at least 8 content words that do not look like junk: possibly a point that was lost.
- `share_one_line_neighbours_split`: neighbouring sentences of one line of the review (a paragraph or a bullet point) put in two critiques.
- `response_spans_quoting_a_critique`: spans containing at least 60 % of the words of a critique; that critique should be the one the span is assigned to (indicator of the first pilot).
- `quote_zones`: a sentence of the reply that quotes a critique opens a zone running until the quotation of another critique. The quoted critique should be given a span touching its zone, and the first span that starts in the zone should name the quoted critique.

| check | value |
|---|---|
| critiques | 1557 |
| critiques_like_bibliography_entry | 0 |
| critiques_like_heading | 3 |
| critiques_like_pointer_or_thanks | 0 |
| critiques_like_junk | 3 |
| critiques_shorter_than_45_characters | 79 |
| junk_like_units | 180 |
| share_junk_like_units_kept_in_a_critique | 0.1111 |
| ignored_units | 852 |
| long_ignored_units_not_junk_like | 325 |
| neighbour_units_on_one_line | 1419 |
| share_one_line_neighbours_split | 0.1515 |
| neighbour_units_on_two_lines | 1028 |
| share_two_line_neighbours_merged | 0.1994 |
| critiques_with_a_response | 599 |
| responses_to_positive_critiques | 9 |
| share_aligned_negative_critiques_with_a_response | 0.7947 |
| response_spans_quoting_a_critique | 145 |
| quoting_spans_assigned_to_the_quoted_critique | 90 |
| share_quoting_spans_assigned_to_the_quoted_critique | 0.6207 |
| quote_zones | 293 |
| share_quote_zones_given_to_the_quoted_critique | 0.9317 |
| quotations_followed_by_a_span | 275 |
| share_first_span_after_a_quotation_naming_it | 0.9236 |

## aspect

| aspect | critiques | share |
|---|---|---|
| experimental_comparison | 454 | 0.2916 |
| soundness | 366 | 0.2351 |
| clarity | 268 | 0.1721 |
| significance | 178 | 0.1143 |
| novelty | 138 | 0.0886 |
| related_work | 90 | 0.0578 |
| reproducibility | 50 | 0.0321 |
| other | 13 | 0.0083 |

## severity

| severity | critiques | share |
|---|---|---|
| minor | 916 | 0.5883 |
| major | 614 | 0.3943 |
| blocking | 27 | 0.0173 |

## polarity

| polarity | critiques | share |
|---|---|---|
| negative | 774 | 0.4971 |
| positive | 573 | 0.368 |
| neutral | 210 | 0.1349 |

## target

| target | critiques | share |
|---|---|---|
| general | 763 | 0.49 |
| experiment | 473 | 0.3038 |
| section | 200 | 0.1285 |
| figure_table | 98 | 0.0629 |
| reference | 23 | 0.0148 |

## actionable

| actionable | critiques | share |
|---|---|---|
| True | 966 | 0.6204 |
| False | 591 | 0.3796 |

## response_type

| response_type | critiques | share |
|---|---|---|
| none | 608 | 0.5037 |
| clarification | 354 | 0.2933 |
| new_experiment | 142 | 0.1176 |
| disagreement | 45 | 0.0373 |
| concession | 37 | 0.0307 |
| promise_to_fix | 21 | 0.0174 |

## response_type_negative_critiques

| response_type | critiques | share |
|---|---|---|
| clarification | 251 | 0.4442 |
| none | 116 | 0.2053 |
| new_experiment | 110 | 0.1947 |
| disagreement | 37 | 0.0655 |
| concession | 34 | 0.0602 |
| promise_to_fix | 17 | 0.0301 |
