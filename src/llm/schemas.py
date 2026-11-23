"""JSON schemas of the three extraction steps (pydantic).

The same models constrain the generation on the server side (JSON schema) and
validate the answer on the client side.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Aspect = Literal[
    "novelty", "soundness", "experimental_comparison", "clarity",
    "reproducibility", "significance", "related_work", "other",
]
Severity = Literal["blocking", "major", "minor"]
Polarity = Literal["negative", "positive", "neutral"]
Target = Literal["section", "figure_table", "experiment", "reference", "general"]
AnswerType = Literal["new_experiment", "clarification", "disagreement", "concession", "promise_to_fix"]
NO_RESPONSE = "none"  # response_type stored when no passage answers the critique
# Order given to the model when several types apply to one passage; also used to give one
# type to a critique that several blocks answer.
ANSWER_PRIORITY = ("new_experiment", "disagreement", "concession", "promise_to_fix", "clarification")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- 3a
class CritiqueUnits(Strict):
    units: list[int] = Field(min_length=1)


class Segmentation(Strict):
    critiques: list[CritiqueUnits]
    post_rebuttal_units: list[int]


class Partition(Strict):
    """Segmentation in which every unit is classified (format `partition`).

    The fields are generated in this order: what is set aside is decided first.
    """

    post_rebuttal_units: list[int]
    ignored_units: list[int]
    critiques: list[CritiqueUnits]


IGNORED = "ignored"
POST_REBUTTAL = "post_rebuttal"
CRITIQUE_LABEL = "c"  # "c3": third critique of the review


class UnitLabel(Strict):
    unit: int
    label: str = Field(pattern=rf"^({IGNORED}|{POST_REBUTTAL}|{CRITIQUE_LABEL}[1-9]\d*)$")


class Labelling(Strict):
    """Segmentation given as one label per unit, in the order of the review (format `labels`)."""

    units: list[UnitLabel]


# --------------------------------------------------------------------------- 3b
class TypedCritique(Strict):
    id: int
    aspect: Aspect
    severity: Severity
    polarity: Polarity
    target: Target
    actionable: bool


class Typing(Strict):
    critiques: list[TypedCritique]


# --------------------------------------------------------------------------- 3c
class ResponseSpan(Strict):
    """Contiguous units of the author reply that answer a critique, and how they answer it."""

    start: int
    end: int
    type: AnswerType


class AlignedCritique(Strict):
    id: int
    # null when no passage answers the critique: a type can never come without a span.
    response: ResponseSpan | None


class Alignment(Strict):
    critiques: list[AlignedCritique]


class ResponseBlock(Strict):
    """Contiguous units of the author reply and the critique(s) they answer (format `blocks`)."""

    start: int
    end: int
    critiques: list[int] = Field(min_length=1)
    type: AnswerType


class BlockAlignment(Strict):
    blocks: list[ResponseBlock]


# Answer model of each step, by the `format` declared in the prompt file (None: first format).
SCHEMAS: dict[tuple[str, str | None], type[BaseModel]] = {
    ("segment", None): Segmentation,
    ("segment", "partition"): Partition,
    ("segment", "labels"): Labelling,
    ("type", None): Typing,
    ("align", None): Alignment,
    ("align", "blocks"): BlockAlignment,
}


def sized_schema(model: type[BaseModel], n_critiques: int) -> dict:
    """JSON schema of `model` whose `critiques` array has exactly `n_critiques` entries.

    Used for the steps that answer once per critique: the server cannot stop early
    or add entries.
    """
    schema = model.model_json_schema()
    schema["properties"]["critiques"].update(minItems=n_critiques, maxItems=n_critiques)
    return schema


def block_schema(n_critiques: int) -> dict:
    """JSON schema of BlockAlignment that only accepts the critique numbers 1..n_critiques."""
    schema = BlockAlignment.model_json_schema()
    schema["$defs"]["ResponseBlock"]["properties"]["critiques"]["items"] = {
        "type": "integer", "enum": list(range(1, n_critiques + 1)),
    }
    return schema


def label_schema(n_units: int) -> dict:
    """JSON schema of Labelling with exactly `n_units` entries and the labels a review of
    that size can use."""
    schema = Labelling.model_json_schema()
    schema["properties"]["units"].update(minItems=n_units, maxItems=n_units)
    schema["$defs"]["UnitLabel"]["properties"]["label"] = {
        "type": "string",
        "enum": [IGNORED, POST_REBUTTAL] + [f"{CRITIQUE_LABEL}{k}" for k in range(1, n_units + 1)],
    }
    return schema
