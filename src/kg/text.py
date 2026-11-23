"""Texts that enter the graph: what is kept of a review, and keyword normalisation."""

import re

from src.llm.units import Unit

# Mentions that only make sense after the author response. They are searched in the text
# kept for a review, to measure what the removal of post-rebuttal sentences left behind.
POST_REBUTTAL_MARKERS = re.compile(
    r"after (the |reading the )?(rebuttal|discussion|author response|authors'? response)"
    r"|post[- ]rebuttal"
    r"|\b(rais|increas|updat|chang|lower|decreas|keep|maintain)\w* (my|the) (score|rating)"
    r"|\bupdated? (score|rating|review)\b"
    r"|thank(s| you)?( the authors)? for (the|your|their) (rebuttal|response|repl|clarif)"
    r"|(rebuttal|response|revision|revised (version|manuscript|paper)) (has|have) (address|resolv|clarif)",
    re.IGNORECASE,
)

# A final "s" is dropped from the last word of a keyword, except after these endings
# ("analysis", "bias", "robotics", "process" keep their "s").
KEPT_ENDINGS = ("ss", "us", "is", "as", "os", "ics")


def kept_units(units: list[Unit], post_rebuttal: set[int]) -> list[Unit]:
    """Units of a review without those set aside as written after the author response."""
    return [unit for unit in units if unit.id not in post_rebuttal]


def chunks(units: list[Unit], max_chars: int) -> list[str]:
    """Text of the units cut into chunks of whole units of at most `max_chars`
    characters (a unit longer than that is a chunk of its own)."""
    pieces: list[str] = []
    current: list[str] = []
    size = 0
    for unit in units:
        if current and size + len(unit.text) + 1 > max_chars:
            pieces.append(" ".join(current))
            current, size = [], 0
        current.append(unit.text)
        size += len(unit.text) + 1
    if current:
        pieces.append(" ".join(current))
    return pieces


def has_post_rebuttal_marker(text: str) -> bool:
    return bool(POST_REBUTTAL_MARKERS.search(text))


def normalise_keyword(keyword: str) -> str:
    """Lower case, punctuation and hyphens as spaces, simple plural of the last word
    removed: "Large Language Models" and "large-language model" give the same concept.
    No synonyms: "llm" stays a concept of its own."""
    words = re.sub(r"[^a-z0-9]+", " ", keyword.lower()).split()
    if not words:
        return ""
    last = words[-1]
    if len(last) > 3 and last.endswith("s") and not last.endswith(KEPT_ENDINGS):
        words[-1] = last[:-1]
    return " ".join(words)


def concepts_of(keywords: list[str] | None) -> list[str]:
    """Distinct normalised keywords of one article, in alphabetical order."""
    return sorted({k for k in (normalise_keyword(str(raw)) for raw in (keywords if keywords is not None else [])) if k})
