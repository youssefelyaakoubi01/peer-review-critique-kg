# Critique extraction report (full_v3)

Sample `full`, model `Qwen/Qwen3-14B-AWQ` (revision `31c69efc29464b6bb0aee1398b5a7b50a99340c3`), prompts `segment_v3`, `type_v1`, `align_v3`, 32 simultaneous requests, temperature 0.

## Passes and throughput

| step | items | seconds | calls | cache_hits | retries | failures | prompt_tokens | completion_tokens | seconds_per_item | output_tokens_per_second | corpus_items | estimated_corpus_hours |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| segment | 73129 | 41125.72 | 72673 | 454 | 5 | 1 | 149812778 | 14868025 | 0.566 | 361.5 | 73129 | 11.5 |
| type | 73005 | 38147.38 | 72620 | 401 | 16 | 1 | 140782478 | 16141448 | 0.525 | 423.1 | 73129 | 10.7 |
| align | 55113 | 98093.6 | 59176 | 321 | 4434 | 1156 | 323017704 | 7121676 | 1.79 | 72.6 | 55192 | 27.4 |

Estimated time for the full corpus (73129 reviews, 55192 with author replies): **49.6 hours**, extrapolated from the time per item sent to the model at this concurrency. It does not include the loading of the model.
Some items were served from the cache: the time per item only counts the others.

## Summary

| metric | value |
|---|---|
| reviews | 73129 |
| reviews_with_critiques | 73005 |
| critiques | 577815 |
| critiques_per_review_mean | 7.9 |
| critiques_per_review_median | 7.0 |
| critiques_per_review_max | 51 |
| share_units_in_critiques | 0.8715 |
| share_units_ignored | 0.1184 |
| share_units_post_rebuttal | 0.0101 |
| reviews_with_post_rebuttal_units | 5912 |
| reviews_truncated | 1 |
| replies_truncated | 197 |
| segment_failed | 1 |
| type_failed | 1 |
| align_failed | 1157 |
| reviews_with_author_reply | 55113 |
| critiques_typed | 577804 |
| critiques_aligned | 426273 |
| critiques_with_a_response | 238872 |

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
| critiques | 577815 |
| critiques_like_bibliography_entry | 386 |
| critiques_like_heading | 606 |
| critiques_like_pointer_or_thanks | 7 |
| critiques_like_junk | 999 |
| critiques_shorter_than_45_characters | 18427 |
| junk_like_units | 78790 |
| share_junk_like_units_kept_in_a_critique | 0.0654 |
| ignored_units | 180271 |
| long_ignored_units_not_junk_like | 30248 |
| neighbour_units_on_one_line | 634006 |
| share_one_line_neighbours_split | 0.0726 |
| neighbour_units_on_two_lines | 468511 |
| share_two_line_neighbours_merged | 0.2761 |
| critiques_with_a_response | 238872 |
| responses_to_positive_critiques | 2780 |
| share_aligned_negative_critiques_with_a_response | 0.86 |
| response_spans_quoting_a_critique | 54653 |
| quoting_spans_assigned_to_the_quoted_critique | 35366 |
| share_quoting_spans_assigned_to_the_quoted_critique | 0.6471 |
| quote_zones | 132464 |
| share_quote_zones_given_to_the_quoted_critique | 0.9301 |
| quotations_followed_by_a_span | 125203 |
| share_first_span_after_a_quotation_naming_it | 0.9319 |

## Logged failures

Failures of the run by step and kind of error (numbers and lists of the messages replaced by `N` and `[...]`). An item that failed has no answer for this step: no critique (segment), no label (type), no aligned author response (align).

| step | error | failures |
|---|---|---|
| segment | ReadTimeout: HTTPConnectionPool(host='N.N.N.N', port=N): Read timed out. (read timeout=N) | 1 |
| type | ValueError: expected the critique ids N to N in order, got [...] | 1 |
| align | ValueError: block N: starts at N, the previous block ends at N | 1087 |
| align | ValueError: block N: span N-N outside N-N | 44 |
| align | ReadTimeout: HTTPConnectionPool(host='N.N.N.N', port=N): Read timed out. (read timeout=N) | 24 |
| align | ValueError: block N: a critique number is repeated | 1 |

## aspect

| aspect | critiques | share |
|---|---|---|
| experimental_comparison | 174780 | 0.3025 |
| soundness | 134918 | 0.2335 |
| clarity | 96714 | 0.1674 |
| significance | 67638 | 0.1171 |
| novelty | 50374 | 0.0872 |
| related_work | 31404 | 0.0543 |
| reproducibility | 20053 | 0.0347 |
| other | 1923 | 0.0033 |
| (missing) | 11 | 0.0 |

## severity

| severity | critiques | share |
|---|---|---|
| minor | 337180 | 0.5835 |
| major | 230363 | 0.3987 |
| blocking | 10261 | 0.0178 |
| (missing) | 11 | 0.0 |

## polarity

| polarity | critiques | share |
|---|---|---|
| negative | 291049 | 0.5037 |
| positive | 202795 | 0.351 |
| neutral | 83960 | 0.1453 |
| (missing) | 11 | 0.0 |

## target

| target | critiques | share |
|---|---|---|
| general | 271059 | 0.4691 |
| experiment | 184751 | 0.3197 |
| section | 75561 | 0.1308 |
| figure_table | 34878 | 0.0604 |
| reference | 11555 | 0.02 |
| (missing) | 11 | 0.0 |

## actionable

| actionable | critiques | share |
|---|---|---|
| True | 374010 | 0.6473 |
| False | 203794 | 0.3527 |
| (missing) | 11 | 0.0 |

## response_type

| response_type | critiques | share |
|---|---|---|
| none | 187401 | 0.4396 |
| clarification | 136818 | 0.321 |
| new_experiment | 65617 | 0.1539 |
| disagreement | 16167 | 0.0379 |
| concession | 10953 | 0.0257 |
| promise_to_fix | 9317 | 0.0219 |

## response_type_negative_critiques

| response_type | critiques | share |
|---|---|---|
| clarification | 95153 | 0.4568 |
| new_experiment | 52277 | 0.2509 |
| none | 29162 | 0.14 |
| disagreement | 14480 | 0.0695 |
| concession | 9916 | 0.0476 |
| promise_to_fix | 7330 | 0.0352 |
