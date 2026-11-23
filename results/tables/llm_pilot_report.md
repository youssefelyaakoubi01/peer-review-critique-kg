# Critique extraction report (pilot)

Sample `dev`, model `Qwen/Qwen3-14B-AWQ` (revision `31c69efc29464b6bb0aee1398b5a7b50a99340c3`), prompts `segment_v1`, `type_v1`, `align_v2`, 32 simultaneous requests, temperature 0.

## Passes and throughput

| step | items | seconds | calls | cache_hits | retries | failures | prompt_tokens | completion_tokens | seconds_per_item | output_tokens_per_second | corpus_items | estimated_corpus_hours |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| segment | 200 | 68.74 | 200 | 0 | 0 | 0 | 302997 | 17689 | 0.344 | 257.3 | 73129 | 7.0 |
| type | 200 | 113.3 | 200 | 0 | 0 | 0 | 385137 | 48789 | 0.566 | 430.6 | 73129 | 11.5 |
| align | 164 | 226.59 | 166 | 0 | 2 | 0 | 810733 | 21579 | 1.382 | 95.2 | 55192 | 21.2 |

Estimated time for the full corpus (73129 reviews, 55192 with author replies): **39.7 hours**, extrapolated from the time per item sent to the model at this concurrency. It does not include the loading of the model.

## Summary

| metric | value |
|---|---|
| reviews | 200 |
| reviews_with_critiques | 200 |
| critiques | 1740 |
| critiques_per_review_mean | 8.7 |
| critiques_per_review_median | 7.5 |
| critiques_per_review_max | 54 |
| share_units_in_critiques | 0.9601 |
| share_units_ignored | 0.0363 |
| share_units_post_rebuttal | 0.0037 |
| reviews_with_post_rebuttal_units | 6 |
| reviews_truncated | 0 |
| replies_truncated | 0 |
| segment_failed | 0 |
| type_failed | 0 |
| align_failed | 0 |
| reviews_with_author_reply | 164 |
| critiques_typed | 1740 |
| critiques_aligned | 1396 |
| critiques_with_a_response | 660 |

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
| critiques | 1740 |
| critiques_like_bibliography_entry | 12 |
| critiques_like_heading | 13 |
| critiques_like_pointer_or_thanks | 25 |
| critiques_like_junk | 50 |
| critiques_shorter_than_45_characters | 135 |
| junk_like_units | 180 |
| share_junk_like_units_kept_in_a_critique | 0.6389 |
| ignored_units | 139 |
| long_ignored_units_not_junk_like | 26 |
| neighbour_units_on_one_line | 1713 |
| share_one_line_neighbours_split | 0.1582 |
| neighbour_units_on_two_lines | 1373 |
| share_two_line_neighbours_merged | 0.3503 |
| critiques_with_a_response | 660 |
| responses_to_positive_critiques | 29 |
| share_aligned_negative_critiques_with_a_response | 0.7311 |
| response_spans_quoting_a_critique | 302 |
| quoting_spans_assigned_to_the_quoted_critique | 145 |
| share_quoting_spans_assigned_to_the_quoted_critique | 0.4801 |
| quote_zones | 368 |
| share_quote_zones_given_to_the_quoted_critique | 0.663 |
| quotations_followed_by_a_span | 306 |
| share_first_span_after_a_quotation_naming_it | 0.6438 |

## aspect

| aspect | critiques | share |
|---|---|---|
| experimental_comparison | 490 | 0.2816 |
| soundness | 418 | 0.2402 |
| clarity | 289 | 0.1661 |
| significance | 185 | 0.1063 |
| novelty | 144 | 0.0828 |
| related_work | 103 | 0.0592 |
| reproducibility | 59 | 0.0339 |
| other | 52 | 0.0299 |

## severity

| severity | critiques | share |
|---|---|---|
| minor | 1120 | 0.6437 |
| major | 590 | 0.3391 |
| blocking | 30 | 0.0172 |

## polarity

| polarity | critiques | share |
|---|---|---|
| negative | 797 | 0.458 |
| positive | 607 | 0.3489 |
| neutral | 336 | 0.1931 |

## target

| target | critiques | share |
|---|---|---|
| general | 838 | 0.4816 |
| experiment | 530 | 0.3046 |
| section | 245 | 0.1408 |
| figure_table | 90 | 0.0517 |
| reference | 37 | 0.0213 |

## actionable

| actionable | critiques | share |
|---|---|---|
| True | 1094 | 0.6287 |
| False | 646 | 0.3713 |

## response_type

| response_type | critiques | share |
|---|---|---|
| none | 736 | 0.5272 |
| clarification | 409 | 0.293 |
| new_experiment | 129 | 0.0924 |
| disagreement | 66 | 0.0473 |
| concession | 37 | 0.0265 |
| promise_to_fix | 19 | 0.0136 |

## response_type_negative_critiques

| response_type | critiques | share |
|---|---|---|
| clarification | 268 | 0.4316 |
| none | 167 | 0.2689 |
| new_experiment | 84 | 0.1353 |
| disagreement | 53 | 0.0853 |
| concession | 33 | 0.0531 |
| promise_to_fix | 16 | 0.0258 |
