"""Three passes over a set of reviews: segment, type, align. Each pass is timed.

Passes are run one after the other (not review by review) so that the time of
each step can be measured and extrapolated to the full corpus.
"""

import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd

from src.llm import steps
from src.llm.client import ContextOverflow, LLMClient
from src.llm.schemas import (
    NO_RESPONSE, Alignment, BlockAlignment, Typing, block_schema, label_schema, sized_schema,
)


SHRINK = 0.8  # share of the units kept each time the server refuses an input as too long


def run_pass(client: LLMClient, name: str, jobs: list[Any], work, concurrency: int,
             progress_every: int, log: logging.Logger) -> tuple[list[Any], dict[str, Any]]:
    """Run `work(job)` for every job with a thread pool; returns results and timing.

    Progress is logged every `progress_every` jobs, with the time left at the current pace.
    """
    before = dict(client.stats)
    started = time.monotonic()
    done, lock = [0], threading.Lock()

    def tracked(job):
        result = work(job)
        with lock:
            done[0] += 1
            count = done[0]
        if count % progress_every == 0 or count == len(jobs):
            elapsed = time.monotonic() - started
            log.info("pass %s: %d/%d done, %d failures, %.1f min elapsed, about %.1f h left",
                     name, count, len(jobs), client.stats["failures"] - before["failures"],
                     elapsed / 60, elapsed / count * (len(jobs) - count) / 3600)
        return result

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(tracked, jobs))
    stats = {key: client.stats[key] - before[key] for key in client.stats}
    stats.update({"step": name, "items": len(jobs), "seconds": round(time.monotonic() - started, 2)})
    return results, stats


def fit_units(units: list, call: Callable[[list], Any],
              give_up: Callable[[ContextOverflow], None] | None = None) -> tuple[list, bool, Any]:
    """`call(units)`, on a shorter and shorter prefix while the server refuses the input
    as too long for the model. Returns (units used, True if shortened, answer).

    The answer is None when `call` failed, or when even one unit does not fit: the rest
    of the input (the critiques, for the alignment) fills the context by itself. `give_up`
    is then called with the last refusal, so that the failure can be logged.
    """
    shortened = False
    while True:
        try:
            return units, shortened, call(units)
        except ContextOverflow as exc:
            if len(units) <= 1:
                if give_up:
                    give_up(exc)
                return units, True, None
            units, shortened = units[:max(1, int(len(units) * SHRINK))], True


def extract(
    client: LLMClient,
    prompts: dict[str, dict[str, Any]],
    cfg: dict[str, Any],
    reviews: pd.DataFrame,
    replies: dict[str, list[str]],
    checkpoint: Callable[[tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame], list[dict[str, Any]]], None] | None = None,
    log: logging.Logger = logging.getLogger(__name__),
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    """(critiques, responses, per-review audit, timing of each pass).

    `checkpoint(tables, timings)` is called after each pass with the tables as they
    stand, so that a long run leaves usable outputs before its last pass. Progress
    goes to `log`.
    """
    max_chars, concurrency, every = cfg["max_input_chars"], cfg["concurrency"], cfg["progress_every"]
    records = reviews.to_dict("records")
    timings = []

    def too_long(step, review_id):
        """Logs the failure of an input that does not fit the context even with one unit."""
        return lambda exc: client.log_failure(
            review_id, step, prompts[step]["version"], f"ContextOverflow with one unit left: {exc}")

    def passed(state, stats):
        timings.append(stats)
        if checkpoint:
            checkpoint(build_tables(state), timings)

    # ---- 3a: segmentation
    segment_format = prompts["segment"].get("format")

    def segment(review):
        units, truncated = steps.review_units(review, max_chars)
        if not units:
            return units, truncated, None, False
        group_lines = segment_format in (steps.PARTITION, steps.LABELS)

        def call(units):
            return client.complete(
                "segment", prompts["segment"]["version"],
                steps.messages(prompts["segment"], steps.segment_input(units, group_lines)),
                steps.answer_model(prompts["segment"]), lambda a: steps.check_segmentation(a, units),
                review["review_id"],
                # one label per unit: the number of entries is fixed by the schema
                json_schema=label_schema(len(units)) if segment_format == steps.LABELS else None,
            )

        units, shortened, answer = fit_units(units, call, too_long("segment", review["review_id"]))
        return units, truncated or shortened, answer, answer is None

    segmented, stats = run_pass(client, "segment", records, segment, concurrency, every, log)

    state = []
    for review, (units, truncated, answer, failed) in zip(records, segmented):
        critiques = steps.critiques_from_segmentation(answer, units) if answer else []
        state.append({"review": review, "units": units, "truncated": truncated, "segment_failed": failed,
                      "post_rebuttal_units": sorted(steps.segmentation_parts(answer)[1]) if answer else [],
                      "critiques": critiques, "typing": None, "alignment": None,
                      "reply_units": [], "reply_truncated": False})
    passed(state, stats)

    # ---- 3b: typing
    with_critiques = [s for s in state if s["critiques"]]

    def label(s):
        try:
            return client.complete(
                "type", prompts["type"]["version"],
                steps.messages(prompts["type"], steps.type_input(s["critiques"])),
                Typing, lambda a: steps.check_typing(a, s["critiques"]), s["review"]["review_id"],
                json_schema=sized_schema(Typing, len(s["critiques"])),
            )
        except ContextOverflow as exc:  # the critiques of one review cannot be cut: logged as a failure
            client.log_failure(s["review"]["review_id"], "type", prompts["type"]["version"], f"ContextOverflow: {exc}")
            return None

    typed, stats = run_pass(client, "type", with_critiques, label, concurrency, every, log)
    for s, answer in zip(with_critiques, typed):
        s["typing"] = answer
    passed(state, stats)

    # ---- 3c: alignment on the author replies
    to_align = []
    for s in with_critiques:
        s["reply_units"], s["reply_truncated"] = steps.response_units(
            replies.get(s["review"]["review_id"], []), max_chars
        )
        if s["reply_units"]:
            to_align.append(s)

    blocks = prompts["align"].get("format") == steps.BLOCKS

    def align(s):
        def call(units):
            chat = steps.messages(prompts["align"], steps.align_input(s["critiques"], units, group_lines=blocks))
            if blocks:  # the reply is cut into blocks, each naming the critiques it answers
                return client.complete(
                    "align", prompts["align"]["version"], chat, BlockAlignment,
                    lambda a: steps.check_blocks(a, s["critiques"], units), s["review"]["review_id"],
                    json_schema=block_schema(len(s["critiques"])),
                )
            return client.complete(  # one answer per critique
                "align", prompts["align"]["version"], chat, Alignment,
                lambda a: steps.check_alignment(a, s["critiques"], units), s["review"]["review_id"],
                json_schema=sized_schema(Alignment, len(s["critiques"])),
            )

        return fit_units(s["reply_units"], call, too_long("align", s["review"]["review_id"]))

    aligned, stats = run_pass(client, "align", to_align, align, concurrency, every, log)
    for s, (units, shortened, answer) in zip(to_align, aligned):
        s["reply_units"], s["alignment"] = units, answer
        s["reply_truncated"] = s["reply_truncated"] or shortened
    passed(state, stats)

    return (*build_tables(state), timings)  # the last checkpoint already holds these tables


def build_tables(state: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    critiques, responses, audit = [], [], []
    for s in state:
        review = s["review"]
        ids = {"review_id": review["review_id"], "forum_id": review["forum_id"], "year": review["year"]}
        labels = {c.id: c for c in s["typing"].critiques} if s["typing"] else {}
        spans = steps.response_spans(s["alignment"]) if s["alignment"] else {}
        for c in s["critiques"]:
            critique_id = f"{review['review_id']}:{c['id']}"
            label = labels.get(c["id"])
            critiques.append({
                "critique_id": critique_id, **ids, "critique_index": c["id"],
                "units": c["units"], "fields": c["fields"], "text": c["text"],
                "aspect": label.aspect if label else None,
                "severity": label.severity if label else None,
                "polarity": label.polarity if label else None,
                "target": label.target if label else None,
                "actionable": label.actionable if label else None,
            })
            if s["alignment"]:  # one row per span answering the critique, or one row `none`
                for span in spans.get(c["id"]) or [None]:
                    responses.append({
                        "critique_id": critique_id, **ids,
                        "block_index": span["block"] if span else None,
                        "response_start": span["start"] if span else None,
                        "response_end": span["end"] if span else None,
                        "response_text": (
                            " ".join(u.text for u in s["reply_units"][span["start"] - 1:span["end"]])
                            if span else None
                        ),
                        "response_type": span["type"] if span else NO_RESPONSE,
                    })
        in_critiques = sum(len(c["units"]) for c in s["critiques"])
        audit.append({
            **ids,
            "n_units": len(s["units"]),
            "n_units_in_critiques": in_critiques,
            "n_post_rebuttal_units": len(s["post_rebuttal_units"]),
            "post_rebuttal_units": s["post_rebuttal_units"],
            "post_rebuttal_text": " ".join(s["units"][n - 1].text for n in s["post_rebuttal_units"]) or None,
            "n_units_ignored": len(s["units"]) - in_critiques - len(s["post_rebuttal_units"]),
            "n_critiques": len(s["critiques"]),
            "review_truncated": s["truncated"],
            "segment_failed": s["segment_failed"],
            "type_failed": bool(s["critiques"]) and s["typing"] is None,
            "n_reply_units": len(s["reply_units"]),
            "reply_truncated": s["reply_truncated"],
            "align_failed": bool(s["reply_units"]) and s["alignment"] is None,
        })
    responses = pd.DataFrame(responses)
    if len(responses):  # nullable integers: these columns are empty for the critiques without answer
        columns = ["block_index", "response_start", "response_end"]
        responses[columns] = responses[columns].astype("Int64")
    return pd.DataFrame(critiques), responses, pd.DataFrame(audit)
