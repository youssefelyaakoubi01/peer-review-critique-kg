# Critique extraction report (full_v3_2026)

Sample `full`, model `Qwen/Qwen3-14B-AWQ` (revision `31c69efc29464b6bb0aee1398b5a7b50a99340c3`), prompts `segment_v3`, `type_v1`, `align_v3`, 32 simultaneous requests, temperature 0.

## Passes and throughput

| step | items | seconds | calls | cache_hits | retries | failures | prompt_tokens | completion_tokens | seconds_per_item | output_tokens_per_second | corpus_items | estimated_corpus_hours |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| segment | 73185 | 42743.67 | 73055 | 126 | 1 | 0 | 151220851 | 14621981 | 0.585 | 342.1 | 146314 | 23.8 |
| type | 73053 | 40006.81 | 73019 | 47 | 13 | 3 | 143287046 | 16844891 | 0.548 | 421.1 | 146314 | 22.3 |
| align | 0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | — | — | 108865 | — |

At least one pass was entirely served from the cache: no time estimate for this run.

## Summary

| metric | value |
|---|---|
| reviews | 73185 |
| reviews_with_critiques | 73053 |
| critiques | 600286 |
| critiques_per_review_mean | 8.2 |
| critiques_per_review_median | 8.0 |
| critiques_per_review_max | 46 |
| share_units_in_critiques | 0.8998 |
| share_units_ignored | 0.0947 |
| share_units_post_rebuttal | 0.0055 |
| reviews_with_post_rebuttal_units | 4186 |
| reviews_truncated | 0 |
| replies_truncated | 0 |
| segment_failed | 0 |
| type_failed | 3 |
| align_failed | 0 |
| reviews_with_author_reply | 0 |
| critiques_typed | 600266 |
| critiques_aligned | 0 |
| critiques_with_a_response | 0 |

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
| critiques | 600286 |
| critiques_like_bibliography_entry | 423 |
| critiques_like_heading | 609 |
| critiques_like_pointer_or_thanks | 3 |
| critiques_like_junk | 1035 |
| critiques_shorter_than_45_characters | 13803 |
| junk_like_units | 67768 |
| share_junk_like_units_kept_in_a_critique | 0.0683 |
| ignored_units | 140933 |
| long_ignored_units_not_junk_like | 21273 |
| neighbour_units_on_one_line | 612099 |
| share_one_line_neighbours_split | 0.0653 |
| neighbour_units_on_two_lines | 508477 |
| share_two_line_neighbours_merged | 0.2493 |
| critiques_with_a_response | 0 |
| responses_to_positive_critiques | 0 |
| share_aligned_negative_critiques_with_a_response | — |

## Logged failures

Failures of the run by step and kind of error (numbers and lists of the messages replaced by `N` and `[...]`). An item that failed has no answer for this step: no critique (segment), no label (type), no aligned author response (align).

| step | error | failures |
|---|---|---|
| type | ValueError: expected the critique ids N to N in order, got [...] | 3 |

## aspect

| aspect | critiques | share |
|---|---|---|
| experimental_comparison | 200655 | 0.3343 |
| soundness | 151020 | 0.2516 |
| clarity | 70759 | 0.1179 |
| significance | 67845 | 0.113 |
| novelty | 51161 | 0.0852 |
| reproducibility | 30125 | 0.0502 |
| related_work | 27080 | 0.0451 |
| other | 1621 | 0.0027 |
| (missing) | 20 | 0.0 |

## severity

| severity | critiques | share |
|---|---|---|
| minor | 302018 | 0.5031 |
| major | 285939 | 0.4763 |
| blocking | 12309 | 0.0205 |
| (missing) | 20 | 0.0 |

## polarity

| polarity | critiques | share |
|---|---|---|
| negative | 303514 | 0.5056 |
| positive | 213331 | 0.3554 |
| neutral | 83421 | 0.139 |
| (missing) | 20 | 0.0 |

## target

| target | critiques | share |
|---|---|---|
| general | 283442 | 0.4722 |
| experiment | 226092 | 0.3766 |
| section | 53014 | 0.0883 |
| figure_table | 27950 | 0.0466 |
| reference | 9768 | 0.0163 |
| (missing) | 20 | 0.0 |

## actionable

| actionable | critiques | share |
|---|---|---|
| True | 385765 | 0.6426 |
| False | 214501 | 0.3573 |
| (missing) | 20 | 0.0 |
