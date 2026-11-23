# Critique extraction report (check_v3)

Sample `check`, model `Qwen/Qwen3-14B-AWQ` (revision `31c69efc29464b6bb0aee1398b5a7b50a99340c3`), prompts `segment_v3`, `type_v1`, `align_v3`, 32 simultaneous requests, temperature 0.

## Passes and throughput

| step | items | seconds | calls | cache_hits | retries | failures | prompt_tokens | completion_tokens | seconds_per_item | output_tokens_per_second | corpus_items | estimated_corpus_hours |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| segment | 200 | 120.93 | 200 | 0 | 0 | 0 | 403521 | 39268 | 0.605 | 324.7 | 73129 | 12.3 |
| type | 200 | 100.9 | 175 | 25 | 0 | 0 | 337353 | 38866 | 0.577 | 385.2 | 73129 | 11.7 |
| align | 161 | 239.09 | 171 | 0 | 10 | 3 | 871317 | 18730 | 1.485 | 78.3 | 55192 | 22.8 |

Estimated time for the full corpus (73129 reviews, 55192 with author replies): **46.8 hours**, extrapolated from the time per item sent to the model at this concurrency. It does not include the loading of the model.
Some items were served from the cache: the time per item only counts the others.

## Summary

| metric | value |
|---|---|
| reviews | 200 |
| reviews_with_critiques | 200 |
| critiques | 1544 |
| critiques_per_review_mean | 7.72 |
| critiques_per_review_median | 7.0 |
| critiques_per_review_max | 29 |
| share_units_in_critiques | 0.8844 |
| share_units_ignored | 0.1079 |
| share_units_post_rebuttal | 0.0077 |
| reviews_with_post_rebuttal_units | 14 |
| reviews_truncated | 0 |
| replies_truncated | 0 |
| segment_failed | 0 |
| type_failed | 0 |
| align_failed | 3 |
| reviews_with_author_reply | 161 |
| critiques_typed | 1544 |
| critiques_aligned | 1238 |
| critiques_with_a_response | 664 |

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
| critiques | 1544 |
| critiques_like_bibliography_entry | 0 |
| critiques_like_heading | 0 |
| critiques_like_pointer_or_thanks | 0 |
| critiques_like_junk | 0 |
| critiques_shorter_than_45_characters | 55 |
| junk_like_units | 199 |
| share_junk_like_units_kept_in_a_critique | 0.0754 |
| ignored_units | 432 |
| long_ignored_units_not_junk_like | 63 |
| neighbour_units_on_one_line | 1647 |
| share_one_line_neighbours_split | 0.0814 |
| neighbour_units_on_two_lines | 1311 |
| share_two_line_neighbours_merged | 0.3066 |
| critiques_with_a_response | 664 |
| responses_to_positive_critiques | 5 |
| share_aligned_negative_critiques_with_a_response | 0.8297 |
| response_spans_quoting_a_critique | 135 |
| quoting_spans_assigned_to_the_quoted_critique | 93 |
| share_quoting_spans_assigned_to_the_quoted_critique | 0.6889 |
| quote_zones | 385 |
| share_quote_zones_given_to_the_quoted_critique | 0.8909 |
| quotations_followed_by_a_span | 373 |
| share_first_span_after_a_quotation_naming_it | 0.882 |

## Logged failures

Failures of the run by step and kind of error (numbers and lists of the messages replaced by `N` and `[...]`). An item that failed has no answer for this step: no critique (segment), no label (type), no aligned author response (align).

| step | error | failures |
|---|---|---|
| align | ValueError: block N: starts at N, the previous block ends at N | 3 |

## aspect

| aspect | critiques | share |
|---|---|---|
| experimental_comparison | 464 | 0.3005 |
| soundness | 353 | 0.2286 |
| clarity | 272 | 0.1762 |
| significance | 175 | 0.1133 |
| novelty | 126 | 0.0816 |
| related_work | 84 | 0.0544 |
| reproducibility | 60 | 0.0389 |
| other | 10 | 0.0065 |

## severity

| severity | critiques | share |
|---|---|---|
| minor | 948 | 0.614 |
| major | 571 | 0.3698 |
| blocking | 25 | 0.0162 |

## polarity

| polarity | critiques | share |
|---|---|---|
| negative | 790 | 0.5117 |
| positive | 549 | 0.3556 |
| neutral | 205 | 0.1328 |

## target

| target | critiques | share |
|---|---|---|
| general | 710 | 0.4598 |
| experiment | 495 | 0.3206 |
| section | 203 | 0.1315 |
| figure_table | 102 | 0.0661 |
| reference | 34 | 0.022 |

## actionable

| actionable | critiques | share |
|---|---|---|
| True | 992 | 0.6425 |
| False | 552 | 0.3575 |

## response_type

| response_type | critiques | share |
|---|---|---|
| none | 574 | 0.4637 |
| clarification | 401 | 0.3239 |
| new_experiment | 170 | 0.1373 |
| disagreement | 42 | 0.0339 |
| promise_to_fix | 28 | 0.0226 |
| concession | 23 | 0.0186 |

## response_type_negative_critiques

| response_type | critiques | share |
|---|---|---|
| clarification | 306 | 0.4826 |
| new_experiment | 137 | 0.2161 |
| none | 108 | 0.1703 |
| disagreement | 40 | 0.0631 |
| promise_to_fix | 23 | 0.0363 |
| concession | 20 | 0.0315 |
