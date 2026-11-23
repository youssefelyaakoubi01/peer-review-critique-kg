"""Offline tests of the critique extraction: a fake server stands in for vLLM."""

import json
import re

import pandas as pd
import pytest

from src.llm import checks, inputs, pipeline, steps
from src.llm.client import ContextOverflow, LLMClient, ServerDown
from src.llm.schemas import (
    SCHEMAS, Alignment, BlockAlignment, Labelling, Partition, Segmentation, Typing,
    block_schema, label_schema, sized_schema,
)
from src.llm.units import build_units, render_units, split_sentences, split_units, truncate_units
from src.utils.config import load_config

LLM = {
    "model": "fake-model", "revision": "abc", "base_url": "http://fake/v1", "temperature": 0, "seed": 0,
    "timeout_seconds": 5, "concurrency": 2, "max_input_chars": 10_000,
    "retry_wait_seconds": 0, "max_connection_errors": 4, "progress_every": 1, "max_model_len": 1000,
    "max_tokens": {"segment": 100, "type": 100, "align": 100},
}
MESSAGES = [{"role": "user", "content": "1: A point."}]
UNITS = build_units({"weaknesses": "A point.\nAnother point."})


class FakeServer:
    """Returns canned answers in order and records every request."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.requests = []

    def __call__(self, url, payload, timeout):
        self.requests.append(payload)
        content = self.answers.pop(0)
        return {"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}


def make_client(tmp_path, answers):
    server = FakeServer(answers)
    return LLMClient(LLM, tmp_path / "cache", tmp_path / "failures.jsonl", post=server), server


def segment(client, units=UNITS, item="r1"):
    return client.complete("segment", "segment_v1", MESSAGES, Segmentation,
                           lambda a: steps.check_segmentation(a, units), item)


GOOD = '{"critiques": [{"units": [1]}, {"units": [2]}], "post_rebuttal_units": []}'


# --------------------------------------------------------------------------- units
def test_units_are_lines_then_sentences():
    text = "1. First point. It has two sentences.\n\n- Second point, e.g. with an abbreviation. Done?\n-----\n"
    assert split_units(text) == [
        "1. First point.", "It has two sentences.",
        "- Second point, e.g. with an abbreviation.", "Done?",
    ]


@pytest.mark.parametrize("line", [
    "See Fig. 3 and Sec. 4 for details.",
    "As shown by Smith et al. (2020), this is known.",
    "The method of J. Doe is not cited.",
    "1. The idea is not novel enough.",
    "W1. The author should delve into this.",
])
def test_abbreviations_and_list_markers_do_not_end_a_sentence(line):
    assert split_sentences(line) == [line]


def test_after_rebuttal_marker_line_is_kept():
    assert split_units("-----After Rebuttal-----\nThanks.") == ["-----After Rebuttal-----", "Thanks."]


def test_units_are_numbered_across_fields_and_rendered_with_headers():
    units = build_units({"strengths": "Good idea.", "weaknesses": None, "questions": "Why? How?"})
    assert [(u.id, u.field) for u in units] == [(1, "strengths"), (2, "questions"), (3, "questions")]
    assert render_units(units) == "[strengths]\n1: Good idea.\n[questions]\n2: Why?\n3: How?"


def test_units_of_one_source_line_can_be_shown_together():
    units = build_units({"weaknesses": "- No baseline. Please add one.\n\n- Typos.", "questions": "Why? How?\nWhen?"})
    assert [u.line for u in units] == [1, 1, 2, 3, 3, 4]
    assert render_units(units, group_lines=True) == (
        "[weaknesses]\n1: - No baseline.\n2: Please add one.\n\n3: - Typos.\n"
        "[questions]\n4: Why?\n5: How?\n\n6: When?"
    )
    assert "\n\n" not in render_units(units)  # first format: one unit per line, no grouping


def test_long_inputs_are_cut_on_a_unit_boundary():
    units = build_units({"weaknesses": "\n".join(f"Point number {i}." for i in range(100))})
    kept, truncated = truncate_units(units, 300)
    assert truncated and 0 < len(kept) < 100
    assert truncate_units(units, 10**6) == (units, False)


# --------------------------------------------------------------------------- semantic checks
def test_segmentation_rejects_unknown_and_repeated_units():
    steps.check_segmentation(Segmentation.model_validate_json(GOOD), UNITS)
    with pytest.raises(ValueError, match="do not exist"):
        steps.check_segmentation(Segmentation(critiques=[{"units": [7]}], post_rebuttal_units=[]), UNITS)
    with pytest.raises(ValueError, match="more than once"):
        steps.check_segmentation(Segmentation(critiques=[{"units": [1]}], post_rebuttal_units=[1]), UNITS)


def test_a_partition_must_classify_every_unit_exactly_once():
    def partition(ignored, critiques):
        return Partition(post_rebuttal_units=[], ignored_units=ignored, critiques=[{"units": c} for c in critiques])

    steps.check_segmentation(partition([2], [[1]]), UNITS)
    with pytest.raises(ValueError, match="classified nowhere"):
        steps.check_segmentation(partition([], [[1]]), UNITS)
    with pytest.raises(ValueError, match="more than once"):
        steps.check_segmentation(partition([2], [[1, 2]]), UNITS)


def test_labels_give_one_label_per_unit_in_order():
    units = build_units({"weaknesses": "No baseline.\nTypos.\n## ref\nAfter rebuttal: thanks.",
                         "questions": "Can you add a baseline?"})

    def labelling(*labels, numbers=None):
        numbers = numbers or range(1, len(labels) + 1)
        return Labelling(units=[{"unit": n, "label": label} for n, label in zip(numbers, labels)])

    answer = labelling("c1", "c2", "ignored", "post_rebuttal", "c1")
    steps.check_segmentation(answer, units)
    assert steps.segmentation_parts(answer) == ([[1, 5], [2]], [4])
    assert [c["text"] for c in steps.critiques_from_segmentation(answer, units)] == [
        "No baseline. Can you add a baseline?", "Typos."]
    for wrong in (labelling("c1", "c2", "ignored", "ignored"),                        # a unit is missing
                  labelling("c1", "c2", "c3", "c4", "c5", numbers=[1, 2, 3, 5, 4])):  # not in order
        with pytest.raises(ValueError, match="in order"):
            steps.check_segmentation(wrong, units)
    with pytest.raises(ValueError):  # unknown label
        labelling("critique 1")
    schema = label_schema(5)
    assert schema["properties"]["units"]["minItems"] == schema["properties"]["units"]["maxItems"] == 5
    assert schema["$defs"]["UnitLabel"]["properties"]["label"]["enum"][-1] == "c5"


def test_critiques_keep_the_exact_text_of_the_reviewer():
    units = build_units({"weaknesses": "No baseline. Typos.", "questions": "Can you add a baseline?"})
    answer = Segmentation(critiques=[{"units": [2]}, {"units": [3, 1]}], post_rebuttal_units=[])
    critiques = steps.critiques_from_segmentation(answer, units)
    assert critiques == [
        {"id": 1, "units": [1, 3], "fields": ["weaknesses", "questions"], "text": "No baseline. Can you add a baseline?"},
        {"id": 2, "units": [2], "fields": ["weaknesses"], "text": "Typos."},
    ]


def test_alignment_rules():
    critiques = [{"id": 1}, {"id": 2}]
    reply = build_units({"author_response": "We added it. Thanks. See Table 2."})

    def answer(second, first_id=1):
        first = {"id": first_id, "response": {"start": 1, "end": 2, "type": "new_experiment"}}
        return Alignment(critiques=[first, {"id": 2, "response": second}])

    steps.check_alignment(answer(None), critiques, reply)
    for wrong in (answer({"start": 2, "end": 9, "type": "clarification"}),   # outside the reply
                  answer({"start": 3, "end": 2, "type": "clarification"}),   # reversed
                  answer(None, first_id=2)):                                 # ids not 1..n in order
        with pytest.raises(ValueError):
            steps.check_alignment(wrong, critiques, reply)


def test_blocks_follow_the_reply_and_name_existing_critiques():
    critiques = [{"id": 1}, {"id": 2}]
    reply = build_units({"author_response": "Thanks. We added it. See Table 2. We also fixed the typos."})

    def blocks(*spans):
        return BlockAlignment(blocks=[{"start": s, "end": e, "critiques": ids, "type": "clarification"}
                                      for s, e, ids in spans])

    answer = blocks((2, 3, [2]), (4, 4, [1, 2]))
    steps.check_blocks(answer, critiques, reply)
    assert steps.response_spans(answer) == {
        2: [{"block": 1, "start": 2, "end": 3, "type": "clarification"},
            {"block": 2, "start": 4, "end": 4, "type": "clarification"}],
        1: [{"block": 2, "start": 4, "end": 4, "type": "clarification"}],
    }
    for wrong in (blocks((2, 9, [1])),               # outside the reply
                  blocks((2, 3, [1]), (3, 4, [2])),  # overlap
                  blocks((3, 4, [1]), (2, 2, [2])),  # not in the order of the reply
                  blocks((2, 3, [3])),               # unknown critique
                  blocks((2, 3, [1, 1]))):           # repeated critique
        with pytest.raises(ValueError):
            steps.check_blocks(wrong, critiques, reply)
    with pytest.raises(ValueError):  # a block names at least one critique
        blocks((2, 3, []))
    assert block_schema(2)["$defs"]["ResponseBlock"]["properties"]["critiques"]["items"]["enum"] == [1, 2]


def test_both_alignment_formats_give_the_same_spans():
    old = Alignment(critiques=[{"id": 1, "response": None},
                               {"id": 2, "response": {"start": 2, "end": 3, "type": "concession"}}])
    assert steps.response_spans(old) == {2: [{"block": None, "start": 2, "end": 3, "type": "concession"}]}


def test_a_response_type_cannot_come_without_a_span():
    with pytest.raises(ValueError):  # "none" is not a type: no response is null
        Alignment.model_validate({"critiques": [{"id": 1, "response": {"start": 1, "end": 1, "type": "none"}}]})
    with pytest.raises(ValueError):  # a type needs its span
        Alignment.model_validate({"critiques": [{"id": 1, "response": {"type": "clarification"}}]})


def test_sized_schema_fixes_the_number_of_answers():
    schema = sized_schema(Typing, 7)
    assert schema["properties"]["critiques"]["minItems"] == schema["properties"]["critiques"]["maxItems"] == 7
    assert "minItems" not in Typing.model_json_schema()["properties"]["critiques"]


def test_schemas_only_accept_the_specified_labels():
    with pytest.raises(ValueError):
        Typing.model_validate({"critiques": [{"id": 1, "aspect": "style", "severity": "minor",
                                              "polarity": "negative", "target": "general", "actionable": True}]})
    with pytest.raises(ValueError):  # extra field
        Segmentation.model_validate({"critiques": [], "post_rebuttal_units": [], "comment": "x"})
    assert {step for step, _ in SCHEMAS} == {"segment", "type", "align"}


# --------------------------------------------------------------------------- client
def test_request_is_deterministic_and_schema_constrained(tmp_path):
    client, server = make_client(tmp_path, [GOOD])
    assert segment(client).critiques[0].units == [1]
    request = server.requests[0]
    assert request["temperature"] == 0 and request["seed"] == 0
    assert request["response_format"]["type"] == "json_schema"
    assert request["response_format"]["json_schema"]["schema"] == Segmentation.model_json_schema()


def test_same_input_is_never_sent_twice(tmp_path):
    client, server = make_client(tmp_path, [GOOD])
    first = segment(client)
    second = segment(client)
    assert first == second and len(server.requests) == 1
    assert client.stats["cache_hits"] == 1 and client.stats["calls"] == 1
    # Another prompt version is another cache entry.
    schema = Segmentation.model_json_schema()
    key = client.cache_key("segment", "segment_v1", MESSAGES, schema)
    assert key != client.cache_key("segment", "segment_v2", MESSAGES, schema)
    assert key != client.cache_key("type", "segment_v1", MESSAGES, schema)
    # ... and so is another output schema.
    assert key != client.cache_key("segment", "segment_v1", MESSAGES, sized_schema(Typing, 2))


def test_truncated_json_is_retried_with_a_larger_budget(tmp_path):
    client, server = make_client(tmp_path, ['{"critiques": [{"units": [1', GOOD])
    assert segment(client) is not None
    assert [r["max_tokens"] for r in server.requests] == [100, 200]
    assert client.stats["retries"] == 1 and client.stats["failures"] == 0


def test_semantic_error_is_sent_back_with_its_message(tmp_path):
    wrong = '{"critiques": [{"units": [9]}], "post_rebuttal_units": []}'
    client, server = make_client(tmp_path, [wrong, GOOD])
    assert segment(client) is not None
    assert len(server.requests) == 2 and client.stats["retries"] == 1
    assert "do not exist" in server.requests[1]["messages"][-1]["content"]
    assert server.requests[1]["max_tokens"] == server.requests[0]["max_tokens"]  # not a truncation


def test_invalid_json_gets_the_error_message_on_the_second_retry(tmp_path):
    client, server = make_client(tmp_path, ["not json", "not json", GOOD])
    assert segment(client) is not None
    assert [len(r["messages"]) for r in server.requests] == [len(MESSAGES), len(MESSAGES), len(MESSAGES) + 2]


def test_failure_is_logged_after_three_attempts_and_not_cached(tmp_path):
    client, server = make_client(tmp_path, ["not json"] * 3)
    assert segment(client, item="r-bad") is None
    assert len(server.requests) == 3 and client.stats["failures"] == 1
    record = json.loads((tmp_path / "failures.jsonl").read_text().strip())
    assert record["item_id"] == "r-bad" and record["step"] == "segment" and record["last_output"] == "not json"
    assert not list((tmp_path / "cache").rglob("*.json"))


# --------------------------------------------------------------------------- prompts
@pytest.fixture(scope="module")
def cfg():
    return load_config()


# Prompts of the sets that can be run (align_v1 is kept as a file but its format was abandoned).
PROMPT_FILES = sorted({name for names in load_config()["llm"]["prompt_sets"].values() for name in names.values()})


def example_numbers(text: str) -> list[int]:
    """Numbers that open the lines of an example input ("3: ..." units, "3 (field): ..." critiques)."""
    return [int(n) for n in re.findall(r"^(\d+)(?::| \()", text, flags=re.M)]


@pytest.mark.parametrize("name", PROMPT_FILES)
def test_versioned_prompts_have_three_valid_examples(cfg, name):
    prompt = steps.load_prompt(cfg["paths"]["prompts"], name)
    step, model = prompt["step"], steps.answer_model(prompt)
    assert name.startswith(f"{step}_v") and len(prompt["examples"]) == 3
    for example in prompt["examples"]:
        answer = model.model_validate_json(example["output"])
        if step == "segment":
            numbers = example_numbers(example["input"])
            units = build_units({"review": "\n".join("x" for _ in numbers)})  # as many units as the example
            steps.check_segmentation(answer, units)
            critiques, post_rebuttal = steps.segmentation_parts(answer)
            assert critiques and all(critiques)
        elif step == "type":
            assert [c.id for c in answer.critiques] == example_numbers(example["input"])
        else:
            critiques_part, reply_part = example["input"].split("\n[author_response]\n")
            critiques = [{"id": n} for n in example_numbers(critiques_part)]
            reply = [None] * len(example_numbers(reply_part))
            if isinstance(answer, BlockAlignment):
                steps.check_blocks(answer, critiques, reply)
            else:
                steps.check_alignment(answer, critiques, reply)
    chat = steps.messages(prompt, "INPUT")
    assert [m["role"] for m in chat] == ["system"] + ["user", "assistant"] * 3 + ["user"]


def test_every_prompt_set_names_existing_prompts_of_the_right_step(cfg):
    for prompt_set in cfg["llm"]["prompt_sets"].values():
        assert set(prompt_set) == {"segment", "type", "align"}
        for step, name in prompt_set.items():
            assert steps.load_prompt(cfg["paths"]["prompts"], name)["step"] == step


@pytest.mark.parametrize("name", [n for n in PROMPT_FILES if n.startswith("segment")])
def test_prompt_tells_to_set_aside_post_rebuttal_text(cfg, name):
    prompt = steps.load_prompt(cfg["paths"]["prompts"], name)
    assert "post_rebuttal" in prompt["system"]
    model = steps.answer_model(prompt)
    assert any(steps.segmentation_parts(model.model_validate_json(e["output"]))[1] for e in prompt["examples"])


# --------------------------------------------------------------------------- pipeline
def test_pipeline_end_to_end_with_a_fake_server(tmp_path):
    reviews = pd.DataFrame([
        {"review_id": "r1", "forum_id": "f1", "year": 2024, "strengths": "Nice idea.",
         "weaknesses": "No baseline.\n--- After rebuttal ---\nI raise my score.", "questions": None},
        {"review_id": "r2", "forum_id": "f2", "year": 2024, "strengths": None, "weaknesses": None, "questions": None},
    ])
    replies = {"r1": ["Thank you.", "We added a baseline in Table 3."]}
    prompts = {s: {"version": f"{s}_v1", "step": s, "system": "sys", "examples": []}
               for s in ("segment", "type", "align")}

    def post(url, payload, timeout):
        name = payload["response_format"]["json_schema"]["name"]
        if name != "Segmentation":  # one answer per critique, enforced by the schema
            assert payload["response_format"]["json_schema"]["schema"]["properties"]["critiques"]["maxItems"] == 2
        content = {
            "Segmentation": '{"critiques": [{"units": [1]}, {"units": [2]}], "post_rebuttal_units": [3, 4]}',
            "Typing": json.dumps({"critiques": [
                {"id": 1, "aspect": "novelty", "severity": "minor", "polarity": "positive", "target": "general", "actionable": False},
                {"id": 2, "aspect": "experimental_comparison", "severity": "major", "polarity": "negative", "target": "experiment", "actionable": True},
            ]}),
            "Alignment": json.dumps({"critiques": [
                {"id": 1, "response": None},
                {"id": 2, "response": {"start": 2, "end": 2, "type": "new_experiment"}},
            ]}),
        }[name]
        return {"choices": [{"message": {"content": content}}], "usage": {}}

    client = LLMClient(LLM, tmp_path / "cache", tmp_path / "failures.jsonl", post=post)
    critiques, responses, audit, timings = pipeline.extract(client, prompts, LLM, reviews, replies)

    assert list(critiques["critique_id"]) == ["r1:1", "r1:2"]
    assert list(critiques["text"]) == ["Nice idea.", "No baseline."]
    assert list(critiques["aspect"]) == ["novelty", "experimental_comparison"]
    # Text written after the author response is in no critique, only in the audit table.
    assert "raise my score" not in " ".join(critiques["text"])
    row = audit.set_index("review_id").loc["r1"]
    assert row["n_post_rebuttal_units"] == 2 and "raise my score" in row["post_rebuttal_text"]
    assert audit.set_index("review_id").loc["r2", "n_critiques"] == 0  # empty review: no call, no failure

    answered = responses.set_index("critique_id")
    assert answered.loc["r1:2", "response_text"] == "We added a baseline in Table 3."
    assert answered.loc["r1:2", "response_type"] == "new_experiment"
    assert answered.loc["r1:1", "response_type"] == "none"
    assert [t["step"] for t in timings] == ["segment", "type", "align"]
    assert [t["items"] for t in timings] == [2, 1, 1]

    # Second run: everything comes from the cache.
    calls = client.stats["calls"]
    pipeline.extract(client, prompts, LLM, reviews, replies)
    assert client.stats["calls"] == calls


# --------------------------------------------------------------------------- automatic checks
def test_junk_like_critiques_and_units_are_counted():
    critiques = pd.DataFrame({"text": ["See Weaknesses.", "[1] A. Author. A title. 2020", "**Minor**",
                                       "The baseline of Table 2 is missing."]})
    counts = checks.junk_counts(critiques)
    assert counts["critiques_like_junk"] == 3 and counts["critiques_like_pointer_or_thanks"] == 1
    assert all(checks.is_junk_unit(t) for t in ("## Weaknesses", "Strengths:", "Please refer to weaknesses."))
    assert not checks.is_junk_unit("#### Question 1: why is the bound tight in this setting?")


def test_unit_fate_sees_junk_kept_and_long_sentences_ignored():
    units = {"r": build_units({"weaknesses": "## Weaknesses\nThe proposed method is never compared with "
                                             "existing baselines on standard benchmarks.\nSee questions."})}
    kept = checks.unit_fate({"r": [[1, 2]]}, {"r": [3]}, units)      # heading kept, pointer post-rebuttal
    assert kept["junk_like_units"] == 2 and kept["share_junk_like_units_kept_in_a_critique"] == 0.5
    assert kept["ignored_units"] == 0
    lost = checks.unit_fate({"r": []}, {}, units)                    # everything ignored
    assert lost["ignored_units"] == 3 and lost["long_ignored_units_not_junk_like"] == 1


def test_line_structure_counts_split_lines_and_merged_lines():
    units = {"r": build_units({"weaknesses": "No baseline. Please add one.\nTypos. Many of them."})}
    result = checks.line_structure({"r": [[1], [2, 3], [4]]}, units)
    assert result["neighbour_units_on_one_line"] == 2 and result["share_one_line_neighbours_split"] == 1.0
    assert result["neighbour_units_on_two_lines"] == 1 and result["share_two_line_neighbours_merged"] == 1.0


CRITIQUE_TEXTS = {
    "c1": "The proposed method is never compared with existing baselines on standard benchmarks.",
    "c2": "The notation of the third section is confusing and several symbols are undefined.",
}
REPLY = build_units({"author_response": "\n".join([
    "Thank you for the review.",
    "> The proposed method is never compared with existing baselines on standard benchmarks.",
    "We added two baselines in Table 3.",
    "They confirm our claims.",
    "> The notation of the third section is confusing and several symbols are undefined.",
    "We rewrote Section 3.",
])})


def test_a_quotation_opens_a_zone_until_the_next_quotation():
    assert checks.quote_zones(CRITIQUE_TEXTS, REPLY) == [
        {"critique": "c1", "start": 2, "end": 4, "answer_units": 2},
        {"critique": "c2", "start": 5, "end": 6, "answer_units": 1},
    ]
    # A sentence that fits two critiques equally is not taken as a quotation.
    same = {"c1": CRITIQUE_TEXTS["c1"], "c2": CRITIQUE_TEXTS["c1"]}
    assert checks.quote_zones(same, REPLY) == []


def test_zone_consistency_flags_shifted_assignments():
    def run(spans):
        return checks.zone_consistency({"r": CRITIQUE_TEXTS}, {"r": REPLY}, {"r": spans})

    good = run([("c1", 3, 4), ("c2", 6, 6)])
    assert good["quote_zones"] == 2 and good["share_quote_zones_given_to_the_quoted_critique"] == 1.0
    assert good["quotations_followed_by_a_span"] == 2 and good["share_first_span_after_a_quotation_naming_it"] == 1.0
    shifted = run([("c0", 2, 4), ("c1", 5, 6)])  # every answer given to the critique before
    assert shifted["share_quote_zones_given_to_the_quoted_critique"] == 0.0
    assert shifted["share_first_span_after_a_quotation_naming_it"] == 0.0
    both = run([("c1", 3, 4), ("c2", 3, 4)])     # one block naming two critiques
    assert both["quotations_followed_by_a_span"] == 1 and both["share_first_span_after_a_quotation_naming_it"] == 1.0
    later = run([("c1", 3, 3), ("c2", 4, 4)])    # a second span in the zone is not held against the model
    assert later["quotations_followed_by_a_span"] == 1 and later["share_first_span_after_a_quotation_naming_it"] == 1.0


# --------------------------------------------------------------------------- samples
def sample_cfg(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "segment_v1.yaml").write_text("examples:\n  - review_id: r03\n", encoding="utf-8")
    return {"paths": {"prompts": prompts, "llm_samples": tmp_path / "samples"},
            "llm": {"samples": {"split": "train", "size": 4, "seeds": {"dev": 0, "check": 1}}}}


def test_a_sample_is_drawn_once_from_the_training_split_outside_examples_and_other_samples(tmp_path):
    cfg = sample_cfg(tmp_path)
    reviews = pd.DataFrame({"review_id": [f"r{i:02d}" for i in range(20)],
                            "split": ["train"] * 12 + ["test"] * 8})
    dev = inputs.draw_sample(cfg, "dev", reviews)
    check = inputs.draw_sample(cfg, "check", reviews)
    train = set(reviews.loc[reviews["split"] == "train", "review_id"])
    assert len(dev) == len(check) == 4 and set(dev) | set(check) <= train - {"r03"}
    assert not set(dev) & set(check)
    assert inputs.read_sample(inputs.sample_path(cfg, "dev")) == dev  # comment lines are skipped
    with pytest.raises(FileExistsError):
        inputs.draw_sample(cfg, "dev", reviews)


def test_frozen_samples_are_disjoint_and_contain_no_prompt_example(cfg):
    assert cfg["llm"]["samples"]["split"] == "train" and cfg["llm"]["temperature"] == 0
    examples = inputs.prompt_example_ids(cfg["paths"]["prompts"])
    seen: set[str] = set()
    for name in cfg["llm"]["samples"]["seeds"]:
        path = inputs.sample_path(cfg, name)
        if not path.exists():
            continue
        ids = inputs.read_sample(path)
        assert len(ids) == len(set(ids)) == cfg["llm"]["samples"]["size"]
        assert not set(ids) & examples and not set(ids) & seen
        seen |= set(ids)
    assert seen, "no frozen sample found"


def test_pipeline_with_labels_and_blocks(tmp_path):
    reviews = pd.DataFrame([{"review_id": "r1", "forum_id": "f1", "year": 2024, "strengths": "Nice idea.",
                             "weaknesses": "No baseline. Please add one.\nTypos.\nSee questions.", "questions": None}])
    replies = {"r1": ["> No baseline.\nWe added a baseline in Table 3.\nWe thank the reviewer.",
                      "We also fixed the typos and reran the baseline."]}
    prompts = {"segment": {"version": "segment_v3", "step": "segment", "format": "labels", "system": "s", "examples": []},
               "type": {"version": "type_v1", "step": "type", "system": "s", "examples": []},
               "align": {"version": "align_v3", "step": "align", "format": "blocks", "system": "s", "examples": []}}
    seen = {}

    def post(url, payload, timeout):
        name = payload["response_format"]["json_schema"]["name"]
        schema = payload["response_format"]["json_schema"]["schema"]
        seen[name] = payload["messages"][-1]["content"]
        if name == "Labelling":
            assert schema["properties"]["units"]["maxItems"] == 5
            labels = ["c1", "c2", "c2", "c3", "ignored"]
            content = json.dumps({"units": [{"unit": n, "label": label} for n, label in enumerate(labels, 1)]})
        elif name == "Typing":
            content = json.dumps({"critiques": [
                {"id": n, "aspect": "other", "severity": "minor", "polarity": "negative", "target": "general",
                 "actionable": True} for n in (1, 2, 3)]})
        else:
            assert schema["$defs"]["ResponseBlock"]["properties"]["critiques"]["items"]["enum"] == [1, 2, 3]
            content = json.dumps({"blocks": [
                {"start": 2, "end": 2, "critiques": [2], "type": "new_experiment"},
                {"start": 4, "end": 4, "critiques": [3, 2], "type": "concession"}]})
        return {"choices": [{"message": {"content": content}}], "usage": {}}

    client = LLMClient(LLM, tmp_path / "cache", tmp_path / "failures.jsonl", post=post)
    critiques, responses, audit, _ = pipeline.extract(client, prompts, LLM, reviews, replies)

    assert list(critiques["text"]) == ["Nice idea.", "No baseline. Please add one.", "Typos."]
    assert audit.loc[0, "n_units_ignored"] == 1 and audit.loc[0, "n_post_rebuttal_units"] == 0
    # The sentences of one line of the review are shown together.
    assert "2: No baseline.\n3: Please add one.\n\n4: Typos." in seen["Labelling"]
    assert "[author_response]\n1: > No baseline.\n\n2: We added" in seen["BlockAlignment"]
    assert responses.loc[responses["response_type"] == "none", "response_text"].isna().all()
    rows = responses.dropna(subset="response_text")
    assert rows.set_index(["critique_id", "response_type"])["response_text"].to_dict() == {
        ("r1:2", "new_experiment"): "We added a baseline in Table 3.",
        ("r1:2", "concession"): "We also fixed the typos and reran the baseline.",
        ("r1:3", "concession"): "We also fixed the typos and reran the baseline.",
    }
    assert list(responses["block_index"].astype(object).where(responses["block_index"].notna(), None)) == [None, 1, 2, 2]


# --------------------------------------------------------------------------- long runs
def test_server_down_stops_the_run_and_nothing_is_logged_as_a_failure_afterwards(tmp_path):
    import requests

    calls = []

    def post(url, payload, timeout):
        calls.append(1)
        raise requests.ConnectionError("refused")

    client = LLMClient(LLM, tmp_path / "cache", tmp_path / "failures.jsonl", post=post)
    assert segment(client, item="r1") is None          # three attempts: a failure, not yet a dead server
    with pytest.raises(ServerDown):                    # fourth connection error in a row
        segment(client, item="r2")
    with pytest.raises(ServerDown):                    # later calls stop at once, without a request
        segment(client, item="r3")
    assert len(calls) == LLM["max_connection_errors"] and client.stats["failures"] == 1


def test_a_success_resets_the_count_of_connection_errors(tmp_path):
    import requests

    answers = [requests.ConnectionError("x")] * 3 + [GOOD] + [requests.ConnectionError("x")] * 3

    def post(url, payload, timeout):
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return {"choices": [{"message": {"content": answer}}], "usage": {}}

    client = LLMClient(LLM, tmp_path / "cache", tmp_path / "failures.jsonl", post=post)
    units = build_units({"weaknesses": "A point.\nAnother point.\nA third point."})
    assert segment(client, item="r1") is None
    assert client.complete("segment", "segment_v1", MESSAGES + MESSAGES, Segmentation,
                           lambda a: steps.check_segmentation(a, units), "r2") is not None
    assert segment(client, item="r3") is None and not client.down


def test_an_input_too_long_for_the_model_is_shortened_until_it_fits(tmp_path):
    calls = []

    def call(units):
        calls.append(len(units))
        if len(units) > 5:
            raise ContextOverflow("too long")
        return "answer"

    assert pipeline.fit_units(list(range(10)), call) == ([0, 1, 2, 3], True, "answer")
    assert calls == [10, 8, 6, 4]  # a fifth of the units is dropped each time
    assert pipeline.fit_units([1, 2], lambda units: "ok") == ([1, 2], False, "ok")

    def never(units):
        raise ContextOverflow("too long")

    assert pipeline.fit_units([1, 2, 3], never) == ([1], True, None)
    refusals = []
    assert pipeline.fit_units([1, 2, 3], never, refusals.append) == ([1], True, None)
    assert [str(exc) for exc in refusals] == ["too long"]  # told once, when one unit is left


def test_an_alignment_that_never_fits_the_context_is_logged_as_a_failure(tmp_path):
    reviews = pd.DataFrame([{"review_id": "r1", "forum_id": "f1", "year": 2024, "strengths": None,
                             "weaknesses": "No baseline.", "questions": None}])
    prompts = {"segment": {"version": "segment_v3", "step": "segment", "format": "labels", "system": "s", "examples": []},
               "type": {"version": "type_v1", "step": "type", "system": "s", "examples": []},
               "align": {"version": "align_v3", "step": "align", "format": "blocks", "system": "s", "examples": []}}

    def post(url, payload, timeout):
        name = payload["response_format"]["json_schema"]["name"]
        if name == "Labelling":
            content = '{"units": [{"unit": 1, "label": "c1"}]}'
        elif name == "Typing":
            content = json.dumps({"critiques": [{"id": 1, "aspect": "other", "severity": "minor",
                                                 "polarity": "negative", "target": "general", "actionable": True}]})
        else:  # the critiques alone fill the context: no reply is short enough
            raise ContextOverflow("maximum context length")
        return {"choices": [{"message": {"content": content}}], "usage": {}}

    failures = tmp_path / "failures.jsonl"
    client = LLMClient(LLM, tmp_path / "cache", failures, post=post)
    _, responses, audit, timings = pipeline.extract(
        client, prompts, LLM, reviews, {"r1": ["First answer.\nSecond answer.\nThird answer."]})

    assert audit.loc[0, "align_failed"] and audit.loc[0, "reply_truncated"] and responses.empty
    logged = [json.loads(line) for line in failures.read_text().splitlines()]
    assert [(f["item_id"], f["step"]) for f in logged] == [("r1", "align")]
    assert "ContextOverflow with one unit left" in logged[0]["error"] and timings[-1]["failures"] == 1


def test_long_reply_is_cut_and_reported_and_tables_are_saved_after_each_pass(tmp_path, caplog):
    reviews = pd.DataFrame([{"review_id": "r1", "forum_id": "f1", "year": 2024, "strengths": None,
                             "weaknesses": "No baseline.", "questions": None}])
    replies = {"r1": ["\n".join(f"Answer sentence number {i}." for i in range(10))]}
    prompts = {"segment": {"version": "segment_v3", "step": "segment", "format": "labels", "system": "s", "examples": []},
               "type": {"version": "type_v1", "step": "type", "system": "s", "examples": []},
               "align": {"version": "align_v3", "step": "align", "format": "blocks", "system": "s", "examples": []}}

    def post(url, payload, timeout):
        name = payload["response_format"]["json_schema"]["name"]
        if name == "Labelling":
            content = '{"units": [{"unit": 1, "label": "c1"}]}'
        elif name == "Typing":
            content = json.dumps({"critiques": [{"id": 1, "aspect": "other", "severity": "minor",
                                                 "polarity": "negative", "target": "general", "actionable": True}]})
        else:
            if "8: Answer sentence number 7." in payload["messages"][-1]["content"]:
                raise ContextOverflow("maximum context length")
            content = '{"blocks": [{"start": 1, "end": 2, "critiques": [1], "type": "clarification"}]}'
        return {"choices": [{"message": {"content": content}}], "usage": {}}

    saved = []
    client = LLMClient(LLM, tmp_path / "cache", tmp_path / "failures.jsonl", post=post)
    with caplog.at_level("INFO"):
        _, responses, audit, _ = pipeline.extract(
            client, prompts, LLM, reviews, replies,
            checkpoint=lambda tables, timings: saved.append((len(tables[0]), len(tables[1]), len(timings))))

    assert audit.loc[0, "reply_truncated"] and audit.loc[0, "n_reply_units"] == 6 and not audit.loc[0, "align_failed"]
    assert list(responses["response_type"]) == ["clarification"] and client.stats["failures"] == 0
    assert saved == [(1, 0, 1), (1, 0, 2), (1, 1, 3)]  # critiques exist before the alignment is done
    assert "pass align: 1/1 done" in caplog.text


def test_an_answer_cut_because_the_context_is_full_asks_for_a_shorter_input(tmp_path):
    def post(url, payload, timeout):
        return {"choices": [{"message": {"content": '{"critiques": [{"units": [1'}, "finish_reason": "length"}],
                "usage": {"prompt_tokens": 950, "completion_tokens": 50, "total_tokens": 1000}}

    client = LLMClient(LLM, tmp_path / "cache", tmp_path / "failures.jsonl", post=post)
    with pytest.raises(ContextOverflow):
        segment(client)
    assert client.stats["failures"] == 0 and client.stats["retries"] == 0


def test_failures_with_the_same_cause_have_the_same_kind():
    first = checks.failure_kind("ValueError: block 2: starts at 6, the previous block ends at 7")
    assert first == checks.failure_kind("ValueError: block 13: starts at 40, the previous block ends at 41")
    assert first == "ValueError: block N: starts at N, the previous block ends at N"
    assert checks.failure_kind("ValueError: expected the critique ids 1 to 11 in order, got [1, 2, 2]") == \
        "ValueError: expected the critique ids N to N in order, got [...]"


def test_pipeline_without_author_replies_only_segments_and_types(tmp_path):
    """Setting A only (--skip-align): no reply is given, the alignment prompt is never sent."""
    reviews = pd.DataFrame([{"review_id": "r1", "forum_id": "f1", "year": 2026, "strengths": "Nice idea.",
                             "weaknesses": "No baseline.", "questions": None}])
    prompts = {"segment": {"version": "segment_v3", "step": "segment", "format": "labels", "system": "s", "examples": []},
               "type": {"version": "type_v1", "step": "type", "system": "s", "examples": []},
               "align": {"version": "align_v3", "step": "align", "format": "blocks", "system": "s", "examples": []}}
    calls = []

    def post(url, payload, timeout):
        name = payload["response_format"]["json_schema"]["name"]
        calls.append(name)
        if name == "Labelling":
            content = json.dumps({"units": [{"unit": 1, "label": "c1"}, {"unit": 2, "label": "c2"}]})
        else:
            content = json.dumps({"critiques": [
                {"id": n, "aspect": "other", "severity": "minor", "polarity": "negative", "target": "general",
                 "actionable": False} for n in (1, 2)]})
        return {"choices": [{"message": {"content": content}}], "usage": {}}

    client = LLMClient(LLM, tmp_path / "cache", tmp_path / "failures.jsonl", post=post)
    critiques, responses, audit, timings = pipeline.extract(client, prompts, LLM, reviews, {})
    assert calls == ["Labelling", "Typing"]
    assert list(critiques["text"]) == ["Nice idea.", "No baseline."] and list(critiques["year"]) == [2026, 2026]
    assert [t["step"] for t in timings] == ["segment", "type", "align"] and timings[-1]["items"] == 0
    assert len(responses) == 0 and not audit.loc[0, "align_failed"]  # no reply: nothing to align, no failure


# --------------------------------------------------------------------------- hosted backend
HOSTED = {**LLM, "backend": "deepseek", "model": "deepseek-flash", "revision": "v", "api_key_env": "NO_SUCH_KEY",
          "prices": {"off_peak": {"input_cache_hit": 1.0, "input_cache_miss": 10.0, "output": 100.0},
                     "peak": {"input_cache_hit": 2.0, "input_cache_miss": 20.0, "output": 200.0}},
          "peak_hours_utc": [], "off_peak_only": True, "budget_usd": 1.0}


def test_peak_hours_are_weekday_windows_in_utc():
    from datetime import datetime, timezone

    from src.llm.client import is_peak

    hours = [[1, 4], [6, 10]]
    wednesday = lambda hour: datetime(2026, 11, 18, hour, 30, tzinfo=timezone.utc)  # noqa: E731
    assert [is_peak(wednesday(h), hours) for h in (0, 1, 3, 4, 5, 6, 9, 10, 23)] == [False, True, True, False, False, True, True, False, False]
    assert not is_peak(datetime(2026, 11, 21, 7, 0, tzinfo=timezone.utc), hours)  # a Saturday


def test_hosted_backend_states_the_schema_validates_the_answer_and_counts_the_cost(tmp_path):
    payloads = []
    answers = iter([json.dumps({"critiques": [{"units": [1]}], "post_rebuttal_units": "none"}),  # not of the schema
                    json.dumps({"critiques": [{"units": [1]}], "post_rebuttal_units": []})])

    def post(url, payload, timeout, headers):
        payloads.append(payload)
        assert url.endswith("/chat/completions") and headers["Authorization"].startswith("Bearer")
        return {"choices": [{"message": {"content": next(answers)}}], "model": "deepseek-flash", "system_fingerprint": "fp1",
                "usage": {"prompt_tokens": 1000, "prompt_cache_hit_tokens": 600, "prompt_cache_miss_tokens": 400, "completion_tokens": 50}}

    client = LLMClient(HOSTED, tmp_path / "cache", tmp_path / "failures.jsonl", post=post)
    chat = [{"role": "system", "content": "Segment."}, {"role": "user", "content": "1: text"}]
    answer = client.complete("segment", "segment_v1", chat, Segmentation, lambda a: None, "r1")
    assert answer.critiques[0].units == [1] and len(payloads) == 2
    first = payloads[0]
    assert first["response_format"] == {"type": "json_object"} and first["thinking"] == {"type": "disabled"}
    assert first["temperature"] == 0 and "seed" not in first and "chat_template_kwargs" not in first
    assert "JSON schema" in first["messages"][0]["content"] and "post_rebuttal_units" in first["messages"][0]["content"]
    assert "rejected" in payloads[1]["messages"][-1]["content"]  # the invalid answer is sent back with the error
    # two answers: (600 * 1 + 400 * 10 + 50 * 100) / 1e6 USD each
    assert client.stats["cost_usd"] == pytest.approx(2 * 9600 / 1e6) and client.stats["prompt_cache_hit_tokens"] == 1200
    assert client.served == {"deepseek-flash fp1"}
    # same input: served by the cache, nothing is paid; the local model has its own cache entry
    client.complete("segment", "segment_v1", chat, Segmentation, lambda a: None, "r1")
    assert len(payloads) == 2
    assert client.cache_key("segment", "segment_v1", chat, {}) != LLMClient(LLM, tmp_path / "c", tmp_path / "f").cache_key("segment", "segment_v1", chat, {})


def test_hosted_backend_stops_when_the_budget_is_spent(tmp_path):
    from src.llm.client import BudgetExceeded

    def post(url, payload, timeout, headers):
        return {"choices": [{"message": {"content": json.dumps({"critiques": [], "post_rebuttal_units": []})}}],
                "usage": {"prompt_tokens": 60_000, "completion_tokens": 0}}  # 0.6 USD at the miss price

    client = LLMClient(HOSTED, tmp_path / "cache", tmp_path / "failures.jsonl", post=post)
    for item in ("a", "b"):
        client.complete("segment", "segment_v1", [{"role": "system", "content": "s"}, {"role": "user", "content": item}],
                        Segmentation, lambda a: None, item)
    assert client.stats["cost_usd"] == pytest.approx(1.2)
    with pytest.raises(BudgetExceeded, match="budget 1.0 USD"):
        client.complete("segment", "segment_v1", [{"role": "system", "content": "s"}, {"role": "user", "content": "c"}],
                        Segmentation, lambda a: None, "c")
    assert client.down and not (tmp_path / "failures.jsonl").exists()  # a stopped run logs no failure
