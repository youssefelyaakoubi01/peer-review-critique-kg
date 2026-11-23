# Critique extraction report (dev_v3)

Sample `dev`, model `Qwen/Qwen3-14B-AWQ` (revision `31c69efc29464b6bb0aee1398b5a7b50a99340c3`), prompts `segment_v3`, `type_v1`, `align_v3`, 32 simultaneous requests, temperature 0.

## Passes and throughput

| step | items | seconds | calls | cache_hits | retries | failures | prompt_tokens | completion_tokens | seconds_per_item | output_tokens_per_second | corpus_items | estimated_corpus_hours |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| segment | 200 | 100.69 | 200 | 0 | 0 | 0 | 401796 | 37661 | 0.503 | 374.0 | 73129 | 10.2 |
| type | 200 | 78.13 | 134 | 66 | 0 | 0 | 265757 | 31626 | 0.583 | 404.8 | 73129 | 11.8 |
| align | 164 | 177.95 | 123 | 45 | 4 | 1 | 640144 | 13335 | 1.495 | 74.9 | 55192 | 22.9 |

Estimated time for the full corpus (73129 reviews, 55192 with author replies): **44.9 hours**, extrapolated from the time per item sent to the model at this concurrency. It does not include the loading of the model.
Some items were served from the cache: the time per item only counts the others.

## Summary

| metric | value |
|---|---|
| reviews | 200 |
| reviews_with_critiques | 200 |
| critiques | 1553 |
| critiques_per_review_mean | 7.76 |
| critiques_per_review_median | 7.0 |
| critiques_per_review_max | 30 |
| share_units_in_critiques | 0.8938 |
| share_units_ignored | 0.0968 |
| share_units_post_rebuttal | 0.0094 |
| reviews_with_post_rebuttal_units | 23 |
| reviews_truncated | 0 |
| replies_truncated | 0 |
| segment_failed | 0 |
| type_failed | 0 |
| align_failed | 1 |
| reviews_with_author_reply | 164 |
| critiques_typed | 1553 |
| critiques_aligned | 1236 |
| critiques_with_a_response | 653 |

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
| critiques | 1553 |
| critiques_like_bibliography_entry | 0 |
| critiques_like_heading | 0 |
| critiques_like_pointer_or_thanks | 0 |
| critiques_like_junk | 0 |
| critiques_shorter_than_45_characters | 56 |
| junk_like_units | 180 |
| share_junk_like_units_kept_in_a_critique | 0.0444 |
| ignored_units | 371 |
| long_ignored_units_not_junk_like | 43 |
| neighbour_units_on_one_line | 1660 |
| share_one_line_neighbours_split | 0.0801 |
| neighbour_units_on_two_lines | 1170 |
| share_two_line_neighbours_merged | 0.2274 |
| critiques_with_a_response | 653 |
| responses_to_positive_critiques | 2 |
| share_aligned_negative_critiques_with_a_response | 0.8285 |
| response_spans_quoting_a_critique | 151 |
| quoting_spans_assigned_to_the_quoted_critique | 99 |
| share_quoting_spans_assigned_to_the_quoted_critique | 0.6556 |
| quote_zones | 370 |
| share_quote_zones_given_to_the_quoted_critique | 0.9405 |
| quotations_followed_by_a_span | 350 |
| share_first_span_after_a_quotation_naming_it | 0.9571 |

## aspect

| aspect | critiques | share |
|---|---|---|
| experimental_comparison | 454 | 0.2923 |
| soundness | 367 | 0.2363 |
| clarity | 271 | 0.1745 |
| significance | 158 | 0.1017 |
| novelty | 147 | 0.0947 |
| related_work | 95 | 0.0612 |
| reproducibility | 53 | 0.0341 |
| other | 8 | 0.0052 |

## severity

| severity | critiques | share |
|---|---|---|
| minor | 936 | 0.6027 |
| major | 595 | 0.3831 |
| blocking | 22 | 0.0142 |

## polarity

| polarity | critiques | share |
|---|---|---|
| negative | 753 | 0.4849 |
| positive | 559 | 0.3599 |
| neutral | 241 | 0.1552 |

## target

| target | critiques | share |
|---|---|---|
| general | 740 | 0.4765 |
| experiment | 459 | 0.2956 |
| section | 225 | 0.1449 |
| figure_table | 98 | 0.0631 |
| reference | 31 | 0.02 |

## actionable

| actionable | critiques | share |
|---|---|---|
| True | 991 | 0.6381 |
| False | 562 | 0.3619 |

## response_type

| response_type | critiques | share |
|---|---|---|
| none | 583 | 0.4717 |
| clarification | 394 | 0.3188 |
| new_experiment | 145 | 0.1173 |
| disagreement | 49 | 0.0396 |
| concession | 36 | 0.0291 |
| promise_to_fix | 29 | 0.0235 |

## response_type_negative_critiques

| response_type | critiques | share |
|---|---|---|
| clarification | 277 | 0.4703 |
| new_experiment | 112 | 0.1902 |
| none | 101 | 0.1715 |
| disagreement | 43 | 0.073 |
| concession | 33 | 0.056 |
| promise_to_fix | 23 | 0.039 |
