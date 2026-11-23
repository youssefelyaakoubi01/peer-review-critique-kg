"""Deterministic split of a text into numbered units (lines, then sentences).

The LLM never copies text: it answers with unit numbers. A critique is therefore
made of the reviewer's exact words, and an answer that points to a unit that
does not exist is detected.
"""

import re
from dataclasses import dataclass

# A sentence ends with . ! or ? followed by whitespace and something that looks
# like the start of a new sentence.
BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[\"“'*$\\-])")
# Words after which a period does not end a sentence.
ABBREVIATIONS = {
    "e.g", "i.e", "et al", "etc", "fig", "figs", "eq", "eqs", "sec", "tab", "vs", "cf",
    "resp", "approx", "w.r.t", "a.k.a", "no", "ref", "refs", "thm", "prop", "def", "app",
}
LIST_MARKER = re.compile(r"^\s*(?:\(?\d{1,2}[.)]|[A-Za-z][.)]|[SWQ]\d{1,2}[.:)])\s*$")


@dataclass(frozen=True)
class Unit:
    id: int
    field: str
    text: str
    line: int = 0  # index of the source line (paragraph or bullet point) the unit comes from


def ends_with_abbreviation(fragment: str) -> bool:
    """True if the fragment stops on an abbreviation, an initial or a bare list marker."""
    body = fragment.rstrip()
    if not body.endswith("."):
        return False
    body = body[:-1]
    if LIST_MARKER.match(fragment):
        return True
    words = body.split()
    if not words:
        return True
    last = words[-1].lower().strip("([\"'")
    if last in ABBREVIATIONS or (len(words) > 1 and f"{words[-2].lower()} {last}" in ABBREVIATIONS):
        return True
    return len(last) == 1 and last.isalpha()  # an initial, e.g. "J."


def split_sentences(line: str) -> list[str]:
    """Sentences of one line; abbreviations and list markers do not end a sentence."""
    pieces: list[str] = []
    start = 0
    for match in BOUNDARY.finditer(line):
        candidate = line[start:match.start()]
        if ends_with_abbreviation(candidate):
            continue
        pieces.append(candidate)
        start = match.end()
    pieces.append(line[start:])
    return [p.strip() for p in pieces if p.strip()]


def split_lines(text: str | None) -> list[list[str]]:
    """Sentences of each kept line of a text.

    Lines without any letter or digit (rules, blank bullets) are dropped. A line
    such as "----- After Rebuttal -----" is kept: it marks later additions.
    """
    if not isinstance(text, str):  # missing field: None, or NaN when read from a table
        return []
    lines = (line.strip() for line in text.splitlines())
    return [split_sentences(line) for line in lines if any(c.isalnum() for c in line)]


def split_units(text: str | None) -> list[str]:
    """Units of a text: non-empty lines, each cut into sentences."""
    return [sentence for line in split_lines(text) for sentence in line]


def build_units(fields: dict[str, str | None]) -> list[Unit]:
    """Units of several named fields, numbered from 1 across the fields in the given order."""
    units: list[Unit] = []
    line = 0
    for field, text in fields.items():
        for sentences in split_lines(text):
            line += 1
            for sentence in sentences:
                units.append(Unit(len(units) + 1, field, sentence, line))
    return units


def render_units(units: list[Unit], group_lines: bool = False) -> str:
    """Numbered listing shown to the LLM, with one header per field.

    With `group_lines`, a blank line separates the units of two source lines, so
    that the sentences of one paragraph or bullet point are seen together.
    """
    lines: list[str] = []
    field = line = None
    for unit in units:
        if unit.field != field:
            field = unit.field
            lines.append(f"[{field}]")
        elif group_lines and unit.line != line:
            lines.append("")
        line = unit.line
        lines.append(f"{unit.id}: {unit.text}")
    return "\n".join(lines)


def truncate_units(units: list[Unit], max_chars: int) -> tuple[list[Unit], bool]:
    """Longest prefix of units whose rendering fits in `max_chars`; True if something was cut."""
    total = 0
    for index, unit in enumerate(units):
        total += len(unit.text) + 8  # room for the number and the separators
        if total > max_chars:
            return units[:index], True
    return units, False
