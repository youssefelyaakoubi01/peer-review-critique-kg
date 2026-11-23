"""Automatic checks of an extraction run. They need no human label: they flag
problems, they do not measure accuracy.

Segmentation
- critiques that look like something the prompt says to leave out (heading, pointer,
  bibliography entry);
- how the critiques follow the lines of the review: sentences of one line (a paragraph
  or a bullet point) usually make one point.

Alignment
- authors often quote the point they answer. A quotation opens a zone of the reply that
  runs until the quotation of another critique; this zone should be assigned to the
  quoted critique. The check does not depend on where the model puts the span borders.
"""

import re
from typing import Any

import pandas as pd

from src.llm.units import Unit

SPAN_QUOTE_SHARE = 0.6   # first pilot: share of a critique's words found in its response span
UNIT_QUOTE_SHARE = 0.8   # share of a reply unit's words found in a critique to call it a quotation
UNIT_QUOTE_MIN_WORDS = 5

BIBLIOGRAPHY = r"^\[\d+\]"
HEADING = r"^(#+\s|\*\*[^*]{1,40}\*\*:?$)"
POINTER = r"(?i)^(see|please (see|refer)|refer to|as above|same as|thanks|thank you|n/?a|none)\b.{0,60}$"
# A unit that is only a heading or a label: "## Weaknesses", "**Minor**", "Strengths:".
UNIT_HEADING = r"^(#+\s*[^.?!]{1,40}|\*\*[^*]{1,40}\*\*:?|[A-Za-z][A-Za-z ]{2,24}:)$"
LONG_UNIT_WORDS = 8      # content words from which an ignored unit is worth a look


def share(numerator: float, denominator: float) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def content_words(text: str | None) -> set[str]:
    return set(re.findall(r"[a-z]{4,}", (text or "").lower()))


def failure_kind(error: str) -> str:
    """Kind of a logged failure: its message without what is specific to one item
    (numbers, lists), so that failures with the same cause can be counted together."""
    kind = re.sub(r"\[.*?\]", "[...]", error)
    return re.sub(r"\d+", "N", kind)[:100]


# --------------------------------------------------------------------------- segmentation
def junk_counts(critiques: pd.DataFrame) -> dict[str, int]:
    text = critiques["text"].str.strip()
    counts = {
        "critiques_like_bibliography_entry": int(text.str.match(BIBLIOGRAPHY).sum()),
        "critiques_like_heading": int(text.str.match(HEADING).sum()),
        "critiques_like_pointer_or_thanks": int(text.str.match(POINTER).sum()),
    }
    counts["critiques_like_junk"] = sum(counts.values())
    counts["critiques_shorter_than_45_characters"] = int((text.str.len() < 45).sum())
    return counts


def is_junk_unit(text: str) -> bool:
    """A unit that looks like a bibliography entry, a pointer, thanks, or a bare heading."""
    text = text.strip()
    return bool(re.match(BIBLIOGRAPHY, text) or re.match(POINTER, text) or re.match(UNIT_HEADING, text))


def unit_fate(critique_units: dict[str, list[list[int]]], set_aside: dict[str, list[int]],
              units: dict[str, list[Unit]]) -> dict[str, Any]:
    """What happens to the units of the reviews, seen from both sides.

    - junk-looking units (bibliography entry, pointer, bare heading) kept inside a critique;
    - ignored units that do not look like junk and are long: possibly a point that was lost.
    `set_aside`: post-rebuttal units of each review (neither in a critique nor ignored).
    """
    junk = junk_kept = ignored = long_ignored = 0
    for review_id, review_units in units.items():
        in_critique = {n for ids in critique_units.get(review_id, []) for n in ids}
        aside = set(set_aside.get(review_id, []))
        for unit in review_units:
            looks_junk = is_junk_unit(unit.text)
            junk += looks_junk
            junk_kept += looks_junk and unit.id in in_critique
            if unit.id not in in_critique and unit.id not in aside:
                ignored += 1
                long_ignored += not looks_junk and len(content_words(unit.text)) >= LONG_UNIT_WORDS
    return {
        "junk_like_units": junk,
        "share_junk_like_units_kept_in_a_critique": share(junk_kept, junk),
        "ignored_units": ignored,
        "long_ignored_units_not_junk_like": long_ignored,
    }


def line_structure(critique_units: dict[str, list[list[int]]], units: dict[str, list[Unit]]) -> dict[str, Any]:
    """Neighbouring units of a review that are both in a critique: same critique or not,
    for neighbours on the same source line and on two lines of the same field.

    `critique_units`: unit numbers of each critique, per review. `units`: units of each review.
    """
    same_line = same_line_split = other_line = other_line_merged = 0
    for review_id, review_units in units.items():
        critique_of = {n: index for index, ids in enumerate(critique_units.get(review_id, [])) for n in ids}
        for first, second in zip(review_units, review_units[1:]):
            if first.id not in critique_of or second.id not in critique_of or first.field != second.field:
                continue
            together = critique_of[first.id] == critique_of[second.id]
            if first.line == second.line:
                same_line += 1
                same_line_split += not together
            else:
                other_line += 1
                other_line_merged += together
    return {
        "neighbour_units_on_one_line": same_line,
        "share_one_line_neighbours_split": share(same_line_split, same_line),
        "neighbour_units_on_two_lines": other_line,
        "share_two_line_neighbours_merged": share(other_line_merged, other_line),
    }


# --------------------------------------------------------------------------- alignment
def span_quote_consistency(critiques: pd.DataFrame, answered: pd.DataFrame) -> dict[str, Any]:
    """Indicator of the first pilot: when a response span contains most of the words of
    one critique of the review, that critique should be the one the span is assigned to."""
    words = {row.critique_id: content_words(row.text) for row in critiques.itertuples()}
    by_review = critiques.groupby("review_id")["critique_id"].apply(list)
    quoting = consistent = 0
    for row in answered.itertuples():
        span = content_words(row.response_text)
        overlap = {cid: len(words[cid] & span) / max(1, len(words[cid])) for cid in by_review[row.review_id]}
        best = max(overlap, key=overlap.get)
        if overlap[best] >= SPAN_QUOTE_SHARE:
            quoting += 1
            consistent += best == row.critique_id
    return {
        "response_spans_quoting_a_critique": quoting,
        "quoting_spans_assigned_to_the_quoted_critique": int(consistent),
        "share_quoting_spans_assigned_to_the_quoted_critique": share(consistent, quoting),
    }


def quoted_critique(unit_text: str, critique_words: dict[Any, set[str]]) -> Any | None:
    """The critique a reply unit quotes, if most of its words come from exactly one critique."""
    words = content_words(unit_text)
    if len(words) < UNIT_QUOTE_MIN_WORDS or not critique_words:
        return None
    common = sorted(((len(words & w), cid) for cid, w in critique_words.items()), key=lambda x: -x[0])
    best, best_id = common[0]
    if best / len(words) < UNIT_QUOTE_SHARE or (len(common) > 1 and common[1][0] == best):
        return None  # not a quotation, or one that fits two critiques equally
    return best_id


def quote_zones(critique_texts: dict[Any, str], reply_units: list[Unit]) -> list[dict[str, Any]]:
    """Zones of an author reply opened by the quotation of a critique.

    A zone starts at the first unit quoting a critique and ends before the first unit
    quoting another critique (or at the end of the reply). `answer_units` counts its
    units that are not quotations: a zone without any is a quotation with no answer
    after it, and is not checked.
    """
    critique_words = {cid: content_words(text) for cid, text in critique_texts.items()}
    zones: list[dict[str, Any]] = []
    for unit in reply_units:
        quoted = quoted_critique(unit.text, critique_words)
        if quoted is not None and (not zones or zones[-1]["critique"] != quoted):
            zones.append({"critique": quoted, "start": unit.id, "end": unit.id, "answer_units": 0})
        elif zones:
            zones[-1]["end"] = unit.id
            zones[-1]["answer_units"] += quoted is None
    return [zone for zone in zones if zone["answer_units"]]


def zone_consistency(
    critique_texts: dict[str, dict[Any, str]],
    reply_units: dict[str, list[Unit]],
    spans: dict[str, list[tuple[Any, int, int]]],
) -> dict[str, Any]:
    """Compare the zones opened by quotations with the spans given by the model.

    All arguments are keyed by review. `spans`: (critique, start, end) of every
    response span. Two questions:
    - is the quoted critique given a span that touches its zone?
    - does the first span that starts inside a zone, the one that follows the quotation,
      name the quoted critique? (spans with the same start are taken together: a block
      may name several critiques)
    Only the first span is looked at: later in the zone the authors may answer another
    critique that they restate in their own words, which is not seen as a quotation.
    """
    zones_total = zones_ok = followed = followed_ok = 0
    for review_id, units in reply_units.items():
        review_spans = spans.get(review_id, [])
        for zone in quote_zones(critique_texts[review_id], units):
            zones_total += 1
            zones_ok += any(c == zone["critique"] and start <= zone["end"] and end >= zone["start"]
                            for c, start, end in review_spans)
            starts = [start for _, start, _ in review_spans if zone["start"] <= start <= zone["end"]]
            if starts:
                followed += 1
                followed_ok += zone["critique"] in {c for c, start, _ in review_spans if start == min(starts)}
    return {
        "quote_zones": zones_total,
        "share_quote_zones_given_to_the_quoted_critique": share(zones_ok, zones_total),
        "quotations_followed_by_a_span": followed,
        "share_first_span_after_a_quotation_naming_it": share(followed_ok, followed),
    }
