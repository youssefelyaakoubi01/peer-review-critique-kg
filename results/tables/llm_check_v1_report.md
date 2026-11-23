# Critique extraction report (check_v1)

Sample `check`, model `Qwen/Qwen3-14B-AWQ` (revision `31c69efc29464b6bb0aee1398b5a7b50a99340c3`), prompts `segment_v1`, `type_v1`, `align_v2`, 32 simultaneous requests, temperature 0.

## Passes and throughput

| step | items | seconds | calls | cache_hits | retries | failures | prompt_tokens | completion_tokens | seconds_per_item | output_tokens_per_second | corpus_items | estimated_corpus_hours |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| segment | 200 | 84.63 | 201 | 0 | 1 | 0 | 306195 | 18396 | 0.423 | 217.4 | 73129 | 8.6 |
| type | 200 | 203.12 | 202 | 0 | 2 | 0 | 393153 | 52733 | 1.016 | 259.6 | 73129 | 20.6 |
| align | 161 | 277.92 | 163 | 0 | 3 | 1 | 829958 | 24053 | 1.726 | 86.5 | 55192 | 26.5 |

Estimated time for the full corpus (73129 reviews, 55192 with author replies): **55.7 hours**, extrapolated from the time per item sent to the model at this concurrency. It does not include the loading of the model.

## Summary

| metric | value |
|---|---|
| reviews | 200 |
| reviews_with_critiques | 200 |
| critiques | 1805 |
| critiques_per_review_mean | 9.03 |
| critiques_per_review_median | 8.0 |
| critiques_per_review_max | 114 |
| share_units_in_critiques | 0.9488 |
| share_units_ignored | 0.0459 |
| share_units_post_rebuttal | 0.0052 |
| reviews_with_post_rebuttal_units | 8 |
| reviews_truncated | 0 |
| replies_truncated | 0 |
| segment_failed | 0 |
| type_failed | 0 |
| align_failed | 1 |
| reviews_with_author_reply | 161 |
| critiques_typed | 1805 |
| critiques_aligned | 1365 |
| critiques_with_a_response | 693 |

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
| critiques | 1805 |
| critiques_like_bibliography_entry | 17 |
| critiques_like_heading | 7 |
| critiques_like_pointer_or_thanks | 28 |
| critiques_like_junk | 52 |
| critiques_shorter_than_45_characters | 146 |
| junk_like_units | 199 |
| share_junk_like_units_kept_in_a_critique | 0.5528 |
| ignored_units | 184 |
| long_ignored_units_not_junk_like | 24 |
| neighbour_units_on_one_line | 1702 |
| share_one_line_neighbours_split | 0.1733 |
| neighbour_units_on_two_lines | 1498 |
| share_two_line_neighbours_merged | 0.3798 |
| critiques_with_a_response | 693 |
| responses_to_positive_critiques | 19 |
| share_aligned_negative_critiques_with_a_response | 0.8269 |
| response_spans_quoting_a_critique | 300 |
| quoting_spans_assigned_to_the_quoted_critique | 167 |
| share_quoting_spans_assigned_to_the_quoted_critique | 0.5567 |
| quote_zones | 350 |
| share_quote_zones_given_to_the_quoted_critique | 0.7886 |
| quotations_followed_by_a_span | 299 |
| share_first_span_after_a_quotation_naming_it | 0.7224 |

## aspect

| aspect | critiques | share |
|---|---|---|
| experimental_comparison | 494 | 0.2737 |
| soundness | 431 | 0.2388 |
| clarity | 306 | 0.1695 |
| significance | 199 | 0.1102 |
| novelty | 136 | 0.0753 |
| related_work | 125 | 0.0693 |
| reproducibility | 62 | 0.0343 |
| other | 52 | 0.0288 |

## severity

| severity | critiques | share |
|---|---|---|
| minor | 1118 | 0.6194 |
| major | 650 | 0.3601 |
| blocking | 37 | 0.0205 |

## polarity

| polarity | critiques | share |
|---|---|---|
| negative | 860 | 0.4765 |
| positive | 625 | 0.3463 |
| neutral | 320 | 0.1773 |

## target

| target | critiques | share |
|---|---|---|
| general | 854 | 0.4731 |
| experiment | 522 | 0.2892 |
| section | 266 | 0.1474 |
| figure_table | 99 | 0.0548 |
| reference | 64 | 0.0355 |

## actionable

| actionable | critiques | share |
|---|---|---|
| True | 1100 | 0.6094 |
| False | 705 | 0.3906 |

## response_type

| response_type | critiques | share |
|---|---|---|
| none | 672 | 0.4923 |
| clarification | 417 | 0.3055 |
| new_experiment | 156 | 0.1143 |
| disagreement | 70 | 0.0513 |
| concession | 28 | 0.0205 |
| promise_to_fix | 22 | 0.0161 |

## response_type_negative_critiques

| response_type | critiques | share |
|---|---|---|
| clarification | 302 | 0.484 |
| new_experiment | 115 | 0.1843 |
| none | 108 | 0.1731 |
| disagreement | 57 | 0.0913 |
| concession | 25 | 0.0401 |
| promise_to_fix | 17 | 0.0272 |
