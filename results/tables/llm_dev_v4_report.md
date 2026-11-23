# Critique extraction report (dev_v4)

Sample `dev`, model `Qwen/Qwen3-14B-AWQ` (revision `31c69efc29464b6bb0aee1398b5a7b50a99340c3`), prompts `segment_v4`, `type_v1`, `align_v3`, 32 simultaneous requests, temperature 0.

## Passes and throughput

| step | items | seconds | calls | cache_hits | retries | failures | prompt_tokens | completion_tokens | seconds_per_item | output_tokens_per_second | corpus_items | estimated_corpus_hours |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| segment | 200 | 104.67 | 200 | 0 | 0 | 0 | 462196 | 37611 | 0.523 | 359.3 | 73129 | 10.6 |
| type | 200 | 47.63 | 79 | 121 | 0 | 0 | 156092 | 19880 | 0.603 | 417.4 | 73129 | 12.2 |
| align | 164 | 103.91 | 75 | 96 | 7 | 2 | 382615 | 8451 | 1.528 | 81.3 | 55192 | 23.4 |

Estimated time for the full corpus (73129 reviews, 55192 with author replies): **46.2 hours**, extrapolated from the time per item sent to the model at this concurrency. It does not include the loading of the model.
Some items were served from the cache: the time per item only counts the others.

## Summary

| metric | value |
|---|---|
| reviews | 200 |
| reviews_with_critiques | 200 |
| critiques | 1587 |
| critiques_per_review_mean | 7.93 |
| critiques_per_review_median | 7.0 |
| critiques_per_review_max | 27 |
| share_units_in_critiques | 0.8936 |
| share_units_ignored | 0.1012 |
| share_units_post_rebuttal | 0.0052 |
| reviews_with_post_rebuttal_units | 13 |
| reviews_truncated | 0 |
| replies_truncated | 0 |
| segment_failed | 0 |
| type_failed | 0 |
| align_failed | 2 |
| reviews_with_author_reply | 164 |
| critiques_typed | 1587 |
| critiques_aligned | 1253 |
| critiques_with_a_response | 685 |

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
| critiques | 1587 |
| critiques_like_bibliography_entry | 0 |
| critiques_like_heading | 0 |
| critiques_like_pointer_or_thanks | 0 |
| critiques_like_junk | 0 |
| critiques_shorter_than_45_characters | 62 |
| junk_like_units | 180 |
| share_junk_like_units_kept_in_a_critique | 0.0333 |
| ignored_units | 388 |
| long_ignored_units_not_junk_like | 52 |
| neighbour_units_on_one_line | 1656 |
| share_one_line_neighbours_split | 0.0598 |
| neighbour_units_on_two_lines | 1166 |
| share_two_line_neighbours_merged | 0.2221 |
| critiques_with_a_response | 685 |
| responses_to_positive_critiques | 2 |
| share_aligned_negative_critiques_with_a_response | 0.8377 |
| response_spans_quoting_a_critique | 167 |
| quoting_spans_assigned_to_the_quoted_critique | 109 |
| share_quoting_spans_assigned_to_the_quoted_critique | 0.6527 |
| quote_zones | 365 |
| share_quote_zones_given_to_the_quoted_critique | 0.9397 |
| quotations_followed_by_a_span | 342 |
| share_first_span_after_a_quotation_naming_it | 0.962 |

## aspect

| aspect | critiques | share |
|---|---|---|
| experimental_comparison | 469 | 0.2955 |
| soundness | 379 | 0.2388 |
| clarity | 287 | 0.1808 |
| significance | 149 | 0.0939 |
| novelty | 147 | 0.0926 |
| related_work | 98 | 0.0618 |
| reproducibility | 52 | 0.0328 |
| other | 6 | 0.0038 |

## severity

| severity | critiques | share |
|---|---|---|
| minor | 947 | 0.5967 |
| major | 620 | 0.3907 |
| blocking | 20 | 0.0126 |

## polarity

| polarity | critiques | share |
|---|---|---|
| negative | 785 | 0.4946 |
| positive | 537 | 0.3384 |
| neutral | 265 | 0.167 |

## target

| target | critiques | share |
|---|---|---|
| general | 725 | 0.4568 |
| experiment | 497 | 0.3132 |
| section | 233 | 0.1468 |
| figure_table | 100 | 0.063 |
| reference | 32 | 0.0202 |

## actionable

| actionable | critiques | share |
|---|---|---|
| True | 1047 | 0.6597 |
| False | 540 | 0.3403 |

## response_type

| response_type | critiques | share |
|---|---|---|
| none | 568 | 0.4533 |
| clarification | 413 | 0.3296 |
| new_experiment | 153 | 0.1221 |
| disagreement | 50 | 0.0399 |
| concession | 40 | 0.0319 |
| promise_to_fix | 29 | 0.0231 |

## response_type_negative_critiques

| response_type | critiques | share |
|---|---|---|
| clarification | 299 | 0.4902 |
| new_experiment | 114 | 0.1869 |
| none | 99 | 0.1623 |
| disagreement | 40 | 0.0656 |
| concession | 35 | 0.0574 |
| promise_to_fix | 23 | 0.0377 |
