"""Inputs shown to the LLM and semantic checks of its answers, for each step.

3a segment: units of a review        -> critiques (lists of unit numbers)
3b type:    critiques of a review    -> aspect, severity, polarity, target, actionable
3c align:   critiques + author reply -> span of the reply answering each critique, type
"""

from pathlib import Path
from typing import Any

import yaml

from pydantic import BaseModel

from src.llm.schemas import (
    IGNORED, POST_REBUTTAL, SCHEMAS, Alignment, BlockAlignment, Labelling, Partition, Segmentation, Typing,
)
from src.llm.units import Unit, build_units, render_units, truncate_units

REVIEW_FIELDS = ("strengths", "weaknesses", "questions")  # `summary` restates the paper: not sent
RESPONSE_FIELD = "author_response"
PARTITION = "partition"  # segment format: every unit is classified, source lines are shown
LABELS = "labels"        # segment format: one label per unit, in order; source lines are shown
BLOCKS = "blocks"        # align format: the author reply is cut into blocks


def load_prompt(prompts_dir: Path, name: str) -> dict[str, Any]:
    with open(prompts_dir / f"{name}.yaml", encoding="utf-8") as f:
        prompt = yaml.safe_load(f)
    if prompt["version"] != name:
        raise ValueError(f"{name}.yaml declares version {prompt['version']!r}")
    answer_model(prompt)  # fails on an unknown format
    return prompt


def answer_model(prompt: dict[str, Any]) -> type[BaseModel]:
    """Pydantic model of the answers expected by a prompt (its step and `format`)."""
    return SCHEMAS[(prompt["step"], prompt.get("format"))]


def messages(prompt: dict[str, Any], user_input: str) -> list[dict[str, str]]:
    """System instruction, few-shot examples as chat turns, then the input to process."""
    chat = [{"role": "system", "content": prompt["system"].strip()}]
    for example in prompt["examples"]:
        chat.append({"role": "user", "content": example["input"].strip()})
        chat.append({"role": "assistant", "content": example["output"].strip()})
    chat.append({"role": "user", "content": user_input})
    return chat


# --------------------------------------------------------------------------- 3a
def review_units(review: dict[str, Any], max_chars: int) -> tuple[list[Unit], bool]:
    """Numbered units of a review (strengths, weaknesses, questions); True if truncated."""
    return truncate_units(build_units({f: review.get(f) for f in REVIEW_FIELDS}), max_chars)


def segment_input(units: list[Unit], group_lines: bool = False) -> str:
    return render_units(units, group_lines)


def segmentation_parts(answer: Segmentation | Partition | Labelling) -> tuple[list[list[int]], list[int]]:
    """(unit numbers of each critique, post-rebuttal unit numbers), whatever the format."""
    if not isinstance(answer, Labelling):
        return [list(c.units) for c in answer.critiques], list(answer.post_rebuttal_units)
    groups: dict[str, list[int]] = {}
    for entry in answer.units:
        groups.setdefault(entry.label, []).append(entry.unit)
    post_rebuttal = groups.pop(POST_REBUTTAL, [])
    groups.pop(IGNORED, None)
    return list(groups.values()), post_rebuttal


def check_segmentation(answer: Segmentation | Partition | Labelling, units: list[Unit]) -> None:
    """Every unit number exists and is used at most once.

    Formats `partition` and `labels` must also classify every unit.
    """
    valid = [u.id for u in units]
    if isinstance(answer, Labelling):
        given = [entry.unit for entry in answer.units]
        if given != valid:
            raise ValueError(f"expected one label for each unit 1 to {len(valid)} in order, got units {given}")
        return
    used: list[int] = [n for c in answer.critiques for n in c.units] + answer.post_rebuttal_units
    if isinstance(answer, Partition):
        used += answer.ignored_units
    unknown = sorted(set(used) - set(valid))
    if unknown:
        raise ValueError(f"unit numbers that do not exist: {unknown}")
    duplicates = sorted({n for n in used if used.count(n) > 1})
    if duplicates:
        raise ValueError(f"unit numbers used more than once: {duplicates}")
    missing = sorted(set(valid) - set(used))
    if isinstance(answer, Partition) and missing:
        raise ValueError(f"unit numbers that are classified nowhere: {missing}")


def critiques_from_segmentation(answer: Segmentation | Partition | Labelling, units: list[Unit]) -> list[dict[str, Any]]:
    """Critiques with their exact text, numbered from 1 in order of first unit."""
    by_id = {u.id: u for u in units}
    ordered = sorted((sorted(ids) for ids in segmentation_parts(answer)[0]), key=lambda ids: ids[0])
    return [
        {
            "id": index,
            "units": ids,
            "fields": list(dict.fromkeys(by_id[n].field for n in ids)),
            "text": " ".join(by_id[n].text for n in ids),
        }
        for index, ids in enumerate(ordered, start=1)
    ]


# --------------------------------------------------------------------------- 3b
def render_critiques(critiques: list[dict[str, Any]]) -> str:
    return "\n".join(f"{c['id']} ({', '.join(c['fields'])}): {c['text']}" for c in critiques)


def type_input(critiques: list[dict[str, Any]]) -> str:
    return render_critiques(critiques)


def check_ids(answer_ids: list[int], critiques: list[dict[str, Any]]) -> None:
    expected = [c["id"] for c in critiques]
    if answer_ids != expected:
        raise ValueError(f"expected the critique ids 1 to {len(expected)} in order, got {answer_ids}")


def check_typing(answer: Typing, critiques: list[dict[str, Any]]) -> None:
    check_ids([c.id for c in answer.critiques], critiques)


# --------------------------------------------------------------------------- 3c
def response_units(replies: list[str], max_chars: int) -> tuple[list[Unit], bool]:
    """Numbered units of the author replies to one review, in posting order."""
    return truncate_units(build_units({RESPONSE_FIELD: "\n".join(r for r in replies if r)}), max_chars)


def align_input(critiques: list[dict[str, Any]], units: list[Unit], group_lines: bool = False) -> str:
    return f"[critiques]\n{render_critiques(critiques)}\n{render_units(units, group_lines)}"


def check_alignment(answer: Alignment, critiques: list[dict[str, Any]], units: list[Unit]) -> None:
    """One answer per critique, in order; every span lies inside the author reply."""
    check_ids([c.id for c in answer.critiques], critiques)
    last = len(units)
    for c in answer.critiques:
        if c.response is not None and not 1 <= c.response.start <= c.response.end <= last:
            raise ValueError(f"critique {c.id}: span {c.response.start}-{c.response.end} outside 1-{last}")


def check_blocks(answer: BlockAlignment, critiques: list[dict[str, Any]], units: list[Unit]) -> None:
    """Blocks lie inside the author reply, in order, without overlap, and name existing critiques."""
    ids = {c["id"] for c in critiques}
    last, previous_end = len(units), 0
    for index, block in enumerate(answer.blocks, start=1):
        if not 1 <= block.start <= block.end <= last:
            raise ValueError(f"block {index}: span {block.start}-{block.end} outside 1-{last}")
        if block.start <= previous_end:
            raise ValueError(f"block {index}: starts at {block.start}, the previous block ends at {previous_end}")
        previous_end = block.end
        unknown = sorted(set(block.critiques) - ids)
        if unknown:
            raise ValueError(f"block {index}: critique numbers that do not exist: {unknown}")
        if len(set(block.critiques)) != len(block.critiques):
            raise ValueError(f"block {index}: a critique number is repeated")


def response_spans(answer: Alignment | BlockAlignment) -> dict[int, list[dict[str, Any]]]:
    """Spans of the author reply answering each critique id: {id: [{block, start, end, type}]}.

    Same structure for both alignment formats; a critique without span is absent.
    """
    spans: dict[int, list[dict[str, Any]]] = {}
    if isinstance(answer, BlockAlignment):
        for index, block in enumerate(answer.blocks, start=1):
            for critique_id in block.critiques:
                spans.setdefault(critique_id, []).append(
                    {"block": index, "start": block.start, "end": block.end, "type": block.type})
    else:
        for c in answer.critiques:
            if c.response is not None:
                spans[c.id] = [{"block": None, "start": c.response.start, "end": c.response.end,
                                "type": c.response.type}]
    return spans
