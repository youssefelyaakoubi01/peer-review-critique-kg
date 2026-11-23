"""Phase 3: report of a critique-extraction run, with random examples; comparison of runs.

Usage:
    uv run python scripts/03b_llm_report.py --tag dev_v2
    uv run python scripts/03b_llm_report.py --compare pilot dev_v2 check_v1 check_v2

--tag writes results/tables/llm_<tag>_report.md, llm_<tag>_*.csv and llm_<tag>_examples.md
(the examples show public review text from OpenReview). --compare writes
results/tables/llm_pilot_comparison.md and .csv with the main figures of several runs.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from src.collect import report
from src.llm import checks, inputs, steps
from src.llm.schemas import ANSWER_PRIORITY, NO_RESPONSE
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

LABELS = ("aspect", "severity", "polarity", "target", "actionable")
STEPS = ("segment", "type", "align")


def distribution(values: pd.Series, name: str) -> pd.DataFrame:
    counts = values.astype("string").fillna("(missing)").value_counts()
    table = counts.rename("critiques").rename_axis(name).reset_index()
    table["share"] = (table["critiques"] / len(values)).round(4)
    return table


def critique_response_types(responses: pd.DataFrame) -> pd.Series:
    """One response type per aligned critique. A critique answered by several blocks
    gets the first of their types in the priority order given to the model."""
    rank = {name: index for index, name in enumerate((*ANSWER_PRIORITY, NO_RESPONSE))}
    return responses.groupby("critique_id")["response_type"].agg(lambda types: min(types, key=rank.get))


# --------------------------------------------------------------------------- loading
def read_failures(path: Path) -> list[dict[str, Any]]:
    """Failures logged by the run (none if the run logged no failure)."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_run(cfg: dict[str, Any], tag: str) -> dict[str, Any]:
    """Tables of a run, with the units of its reviews and of their author replies."""
    run_dir = cfg["paths"]["llm"] / tag
    run = {
        "tag": tag,
        "critiques": pd.read_parquet(run_dir / "critiques.parquet"),
        "responses": pd.read_parquet(run_dir / "critique_responses.parquet"),
        "audit": pd.read_parquet(run_dir / "audit.parquet"),
        "stats": json.loads((run_dir / "run_stats.json").read_text()),
        "failures": read_failures(run_dir / "failures.jsonl"),
    }
    max_chars = cfg["llm"]["max_input_chars"]
    ids = set(run["audit"]["review_id"])
    reviews = inputs.usable_reviews(cfg)
    reviews = reviews[reviews["review_id"].isin(ids)]
    run["review_units"] = {r["review_id"]: steps.review_units(r, max_chars)[0] for r in reviews.to_dict("records")}
    replies = inputs.author_replies(cfg, ids)
    run["reply_units"] = {rid: steps.response_units(texts, max_chars)[0] for rid, texts in replies.items()}
    return run


def corpus_size(cfg: dict[str, Any]) -> tuple[int, int]:
    """Reviews of the full corpus, and how many of them have aligned author replies."""
    ids = set(inputs.usable_reviews(cfg)["review_id"])
    return len(ids), len(inputs.author_replies(cfg, ids))


# --------------------------------------------------------------------------- tables
def passes_table(stats: dict[str, Any], n_corpus: int, n_corpus_answered: int) -> pd.DataFrame:
    """Throughput of each pass and its extrapolation to the corpus.

    The time per item only counts the items actually sent to the model: an item
    served from the cache costs nothing. A pass entirely served from the cache
    measures nothing.
    """
    passes = pd.DataFrame(stats["passes"]).set_index("step").loc[list(STEPS)].reset_index()
    computed = (passes["items"] - passes["cache_hits"]).where(lambda n: n > 0)
    passes["seconds_per_item"] = (passes["seconds"] / computed).round(3)
    passes["output_tokens_per_second"] = (passes["completion_tokens"] / passes["seconds"]).where(computed.notna()).round(1)
    passes["corpus_items"] = [n_corpus, n_corpus, n_corpus_answered]
    passes["estimated_corpus_hours"] = (passes["seconds_per_item"] * passes["corpus_items"] / 3600).round(1)
    columns = ["step", "items", "seconds", "calls", "cache_hits", "retries", "failures", "prompt_tokens",
               "completion_tokens", "seconds_per_item", "output_tokens_per_second", "corpus_items",
               "estimated_corpus_hours"]
    return passes[columns].astype(object).where(passes[columns].notna(), None)


def summary_table(run: dict[str, Any]) -> pd.DataFrame:
    critiques, responses, audit = run["critiques"], run["responses"], run["audit"]
    units = int(audit["n_units"].sum())
    types = critique_response_types(responses) if len(responses) else pd.Series(dtype=object)
    values = {
        "reviews": len(audit),
        "reviews_with_critiques": int((audit["n_critiques"] > 0).sum()),
        "critiques": len(critiques),
        "critiques_per_review_mean": round(float(audit["n_critiques"].mean()), 2),
        "critiques_per_review_median": float(audit["n_critiques"].median()),
        "critiques_per_review_max": int(audit["n_critiques"].max()),
        "share_units_in_critiques": checks.share(int(audit["n_units_in_critiques"].sum()), units),
        "share_units_ignored": checks.share(int(audit["n_units_ignored"].sum()), units),
        "share_units_post_rebuttal": checks.share(int(audit["n_post_rebuttal_units"].sum()), units),
        "reviews_with_post_rebuttal_units": int((audit["n_post_rebuttal_units"] > 0).sum()),
        "reviews_truncated": int(audit["review_truncated"].sum()),
        "replies_truncated": int(audit["reply_truncated"].sum()),
        "segment_failed": int(audit["segment_failed"].sum()),
        "type_failed": int(audit["type_failed"].sum()),
        "align_failed": int(audit["align_failed"].sum()),
        "reviews_with_author_reply": int((audit["n_reply_units"] > 0).sum()),
        "critiques_typed": int(critiques["aspect"].notna().sum()),
        "critiques_aligned": len(types),
        "critiques_with_a_response": int((types != NO_RESPONSE).sum()),
    }
    return pd.DataFrame(list(values.items()), columns=["metric", "value"], dtype=object)


def sanity_checks(run: dict[str, Any]) -> pd.DataFrame:
    """Automatic checks (src/llm/checks.py): they flag problems, they do not measure accuracy."""
    critiques, responses = run["critiques"], run["responses"]
    rows: dict[str, Any] = {"critiques": len(critiques), **checks.junk_counts(critiques)}
    critique_units = {rid: [list(units) for units in group.sort_values("critique_index")["units"]]
                      for rid, group in critiques.groupby("review_id")}
    set_aside = {row.review_id: list(row.post_rebuttal_units) for row in run["audit"].itertuples()}
    rows.update(checks.unit_fate(critique_units, set_aside, run["review_units"]))
    rows.update(checks.line_structure(critique_units, run["review_units"]))

    answered = responses[responses["response_type"] != NO_RESPONSE] if len(responses) else responses
    positive = set(critiques.loc[critiques["polarity"] == "positive", "critique_id"])
    negative = set(critiques.loc[critiques["polarity"] == "negative", "critique_id"])
    aligned = set(responses["critique_id"]) if len(responses) else set()
    with_response = set(answered["critique_id"]) if len(answered) else set()
    rows.update({
        "critiques_with_a_response": len(with_response),
        "responses_to_positive_critiques": len(with_response & positive),
        "share_aligned_negative_critiques_with_a_response": checks.share(
            len(with_response & negative), len(aligned & negative)),
    })
    if len(answered):
        rows.update(checks.span_quote_consistency(critiques, answered))
        texts = {rid: dict(zip(group["critique_id"], group["text"])) for rid, group in critiques.groupby("review_id")}
        spans = {rid: list(zip(group["critique_id"], group["response_start"].astype(int), group["response_end"].astype(int)))
                 for rid, group in answered.groupby("review_id")}
        aligned_reviews = set(responses["review_id"])
        reply_units = {rid: units for rid, units in run["reply_units"].items() if rid in aligned_reviews}
        rows.update(checks.zone_consistency(texts, reply_units, spans))
    return pd.DataFrame(list(rows.items()), columns=["check", "value"], dtype=object)


def failures_table(failures: list[dict[str, Any]]) -> pd.DataFrame:
    """Logged failures by step and kind of error (`checks.failure_kind`)."""
    kinds = pd.DataFrame({"step": [f["step"] for f in failures],
                          "error": [checks.failure_kind(f["error"]) for f in failures]})
    table = kinds.value_counts().rename("failures").reset_index()
    order = {step: index for index, step in enumerate(STEPS)}
    return table.sort_values(["step", "failures"], ascending=[True, False],
                             key=lambda column: column.map(order) if column.name == "step" else column,
                             kind="stable").reset_index(drop=True)


def run_tables(run: dict[str, Any], n_corpus: int, n_corpus_answered: int) -> dict[str, pd.DataFrame]:
    critiques, responses = run["critiques"], run["responses"]
    tables = {
        "passes": passes_table(run["stats"], n_corpus, n_corpus_answered),
        "summary": summary_table(run),
        "sanity_checks": sanity_checks(run),
    }
    if run["failures"]:
        tables["failures"] = failures_table(run["failures"])
    for label in LABELS:
        tables[label] = distribution(critiques[label], label)
    if len(responses):
        types = critique_response_types(responses)
        tables["response_type"] = distribution(types, "response_type")
        negative = critiques.loc[critiques["polarity"] == "negative", "critique_id"]
        tables["response_type_negative_critiques"] = distribution(types[types.index.isin(negative)], "response_type")
    return tables


def headline(run: dict[str, Any], tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Main figures of a run, for the comparison of runs."""
    stats = run["stats"]
    summary = tables["summary"].set_index("metric")["value"]
    sanity = tables["sanity_checks"].set_index("check")["value"]
    passes = tables["passes"].set_index("step")
    figures: dict[str, Any] = {
        "sample": stats.get("sample", "dev"),  # the first pilot ran on what is now the dev sample
        "prompts": ", ".join(stats["prompts"].values()),
    }
    for name in ("reviews", "critiques", "critiques_per_review_mean", "critiques_per_review_median",
                 "share_units_ignored", "share_units_post_rebuttal"):
        figures[name] = summary[name]
    for name in ("critiques_like_bibliography_entry", "critiques_like_heading", "critiques_like_pointer_or_thanks",
                 "critiques_like_junk", "junk_like_units", "share_junk_like_units_kept_in_a_critique",
                 "ignored_units", "long_ignored_units_not_junk_like",
                 "share_one_line_neighbours_split", "share_two_line_neighbours_merged"):
        figures[name] = sanity[name]
    figures["reviews_with_author_reply"] = summary["reviews_with_author_reply"]
    for name in ("critiques_with_a_response", "responses_to_positive_critiques",
                 "share_aligned_negative_critiques_with_a_response",
                 "response_spans_quoting_a_critique", "share_quoting_spans_assigned_to_the_quoted_critique",
                 "quote_zones", "share_quote_zones_given_to_the_quoted_critique",
                 "quotations_followed_by_a_span", "share_first_span_after_a_quotation_naming_it"):
        figures[name] = sanity.get(name)
    for step in STEPS:
        figures[f"{step}_retries"] = passes.loc[step, "retries"]
        figures[f"{step}_failures"] = passes.loc[step, "failures"]
    for step in STEPS:
        figures[f"{step}_estimated_corpus_hours"] = passes.loc[step, "estimated_corpus_hours"]
    hours = [figures[f"{step}_estimated_corpus_hours"] for step in STEPS]
    figures["estimated_corpus_hours"] = round(sum(hours), 1) if all(h is not None for h in hours) else None
    return figures


# --------------------------------------------------------------------------- examples
def examples_markdown(run: dict[str, Any], n: int, seed: int) -> str:
    """Readable dump of `n` random reviews: critiques, labels, aligned author reply."""
    critiques, responses, audit = run["critiques"], run["responses"], run["audit"]
    chosen = audit.sort_values("review_id").sample(n=min(n, len(audit)), random_state=seed)
    answers = dict(tuple(responses.groupby("critique_id"))) if len(responses) else {}
    lines = [f"# {len(chosen)} random reviews of run `{run['tag']}` (seed {seed})", "",
             "Review text is public content from OpenReview. `[ignored]` units are in no critique.", ""]
    for number, row in enumerate(chosen.itertuples(index=False), start=1):
        units = run["review_units"][row.review_id]
        mine = critiques[critiques["review_id"] == row.review_id].sort_values("critique_index")
        used = {n for unit_ids in mine["units"] for n in unit_ids}
        post = set(row.post_rebuttal_units)
        lines += [f"## Example {number} — review `{row.review_id}` (ICLR {row.year})", "",
                  f"{row.n_units} units, {row.n_critiques} critiques, {row.n_units_ignored} ignored, "
                  f"{row.n_post_rebuttal_units} set aside as post-rebuttal.", ""]
        if row.segment_failed:
            lines += ["**Segmentation failed for this review.**", ""]
        if row.align_failed:
            lines += ["**Alignment failed for this review.**", ""]
        for c in mine.itertuples(index=False):
            lines += [f"**Critique {c.critique_index}** — aspect `{c.aspect}`, severity `{c.severity}`, "
                      f"polarity `{c.polarity}`, target `{c.target}`, actionable `{c.actionable}`", "",
                      f"> {c.text}", ""]
            for answer in answers[c.critique_id].itertuples() if c.critique_id in answers else ():
                if answer.response_type == NO_RESPONSE:
                    lines += ["Author response: none.", ""]
                    continue
                excerpt = answer.response_text
                excerpt = excerpt if len(excerpt) <= 600 else excerpt[:600] + " […]"
                lines += [f"Author response — `{answer.response_type}` "
                          f"(units {int(answer.response_start)}–{int(answer.response_end)}):",
                          "", f"> {excerpt}", ""]
        ignored = [u.text for u in units if u.id not in used and u.id not in post]
        if ignored:
            lines += ["`[ignored]` " + " ⏐ ".join(ignored), ""]
        if post:
            lines += ["`[post-rebuttal, set aside]` " + " ⏐ ".join(u.text for u in units if u.id in post), ""]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- outputs
def write_report(cfg: dict[str, Any], run: dict[str, Any], tables: dict[str, pd.DataFrame]) -> str:
    stats, tag = run["stats"], run["tag"]
    tables_dir = cfg["paths"]["tables"]
    tables_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(tables_dir / f"llm_{tag}_{name}.csv", index=False)

    passes = tables["passes"]
    n_corpus, n_corpus_answered = passes["corpus_items"].iloc[0], passes["corpus_items"].iloc[2]
    hours = list(passes["estimated_corpus_hours"])
    text = [
        f"# Critique extraction report ({tag})", "",
        f"Sample `{stats.get('sample', 'dev')}`, model `{stats['model']}` (revision `{stats['revision']}`), prompts "
        + ", ".join(f"`{v}`" for v in stats["prompts"].values())
        + f", {stats['concurrency']} simultaneous requests, temperature 0.", "",
        "## Passes and throughput", "", report.to_markdown(passes), "",
    ]
    if all(h is not None for h in hours):
        text += [f"Estimated time for the full corpus ({n_corpus} reviews, {n_corpus_answered} with author "
                 f"replies): **{round(sum(hours), 1)} hours**, extrapolated from the time per item sent to the "
                 f"model at this concurrency. It does not include the loading of the model."]
        if int(passes["cache_hits"].sum()):
            text += ["Some items were served from the cache: the time per item only counts the others."]
        text += [""]
    else:
        text += ["At least one pass was entirely served from the cache: no time estimate for this run.", ""]
    text += ["## Summary", "", report.to_markdown(tables["summary"]), ""]
    text += ["## Automatic sanity checks", "",
             "No human label is involved: these checks flag problems, they do not measure accuracy "
             "(definitions in `src/llm/checks.py`).",
             "- `critiques_like_*`: critiques that look like something the prompt says to leave out.",
             "- `junk_like_units`: sentences of the reviews that look like a bibliography entry, a pointer, "
             "thanks or a bare heading, and the share of them kept inside a critique.",
             f"- `long_ignored_units_not_junk_like`: ignored sentences of at least {checks.LONG_UNIT_WORDS} "
             "content words that do not look like junk: possibly a point that was lost.",
             "- `share_one_line_neighbours_split`: neighbouring sentences of one line of the review "
             "(a paragraph or a bullet point) put in two critiques.",
             f"- `response_spans_quoting_a_critique`: spans containing at least "
             f"{int(checks.SPAN_QUOTE_SHARE * 100)} % of the words of a critique; that critique should be the "
             "one the span is assigned to (indicator of the first pilot).",
             "- `quote_zones`: a sentence of the reply that quotes a critique opens a zone running until the "
             "quotation of another critique. The quoted critique should be given a span touching its zone, "
             "and the first span that starts in the zone should name the quoted critique.", "",
             report.to_markdown(tables["sanity_checks"]), ""]
    if "failures" in tables:
        text += ["## Logged failures", "",
                 "Failures of the run by step and kind of error (numbers and lists of the messages replaced "
                 "by `N` and `[...]`). An item that failed has no answer for this step: no critique "
                 "(segment), no label (type), no aligned author response (align).", "",
                 report.to_markdown(tables["failures"]), ""]
    for name in (*LABELS, "response_type", "response_type_negative_critiques"):
        if name in tables:
            text += [f"## {name}", "", report.to_markdown(tables[name]), ""]
    (tables_dir / f"llm_{tag}_report.md").write_text("\n".join(text), encoding="utf-8")

    examples = cfg["llm"]["examples"]
    (tables_dir / f"llm_{tag}_examples.md").write_text(
        examples_markdown(run, examples["n"], examples["seed"]), encoding="utf-8")
    return "\n".join(text)


def write_comparison(cfg: dict[str, Any], figures: dict[str, dict[str, Any]]) -> str:
    table = pd.DataFrame(figures, dtype=object)
    table = table.where(table.notna(), None).rename_axis("figure").reset_index()
    tables_dir = cfg["paths"]["tables"]
    table.to_csv(tables_dir / "llm_pilot_comparison.csv", index=False)
    text = "\n".join([
        "# Comparison of critique-extraction runs", "",
        "One column per run (`data/interim/llm/<run>/`). The checks flag problems, they do not measure "
        "accuracy; see `src/llm/checks.py` and the report of each run. A time estimate is missing when a "
        "pass was entirely served from the cache.", "",
        report.to_markdown(table), "",
    ])
    (tables_dir / "llm_pilot_comparison.md").write_text(text, encoding="utf-8")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--tag", help="run to report (directory name under data/interim/llm)")
    mode.add_argument("--compare", nargs="+", metavar="TAG", help="runs to compare")
    args = parser.parse_args()

    cfg = load_config()
    name = f"03b_llm_report_{args.tag}" if args.tag else "03b_llm_report_comparison"
    log = setup_run_logging(name, cfg["paths"]["logs"])
    n_corpus, n_corpus_answered = corpus_size(cfg)

    figures = {}
    for tag in [args.tag] if args.tag else args.compare:
        run = load_run(cfg, tag)
        tables = run_tables(run, n_corpus, n_corpus_answered)
        if args.tag:
            print(write_report(cfg, run, tables))
            log.info("report written for run %s", tag)
        figures[tag] = headline(run, tables)
    if args.compare:
        print(write_comparison(cfg, figures))
        log.info("comparison written for runs %s", args.compare)
    return 0


if __name__ == "__main__":
    sys.exit(main())
