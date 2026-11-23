"""Turn raw OpenReview forums (API v2) into flat records, one table per kind of information.

Tables are split by what a model is allowed to see:

  papers      submission as model input: title, abstract, keywords, area. No author,
              venue, PDF or revision information.
  reviews     reviews as model input in setting A: pre-rebuttal scores (external
              archive, or current state for a year whose reviews were reverted by the
              conference: config `clean.initial_scores`) and review text.
  reviews_final  post-rebuttal scores, modification flags, author replies received.
              Never a model input in setting A.
  discussion  author replies and comments, each aligned on the review it answers.
  outcomes    status, decision, labels, meta-review, split. Labels only.

Two temporal phases, per submission: before / after the first author response
posted in its forum. Setting A only uses what was posted before.

Known limit: the review text is the one currently on OpenReview. For a review
modified after its release it may contain post-rebuttal remarks; the initial text
is not available anywhere. (Not for a year in "current_state": there the current
text is the initial one.)
"""

from typing import Any

from src.collect import external, parse, report
from src.utils.splits import assign_split

REVIEW_TEXT_FIELDS = ("summary", "strengths", "weaknesses", "questions")
SCORE_FIELDS = ("rating", "confidence", "soundness", "presentation", "contribution")
# Text fields of a meta-review: one field until 2025, three in 2026.
META_REVIEW_FIELDS = ("metareview", "summary", "reviewer_concerns", "reviewer_scores")
DISCUSSION_KINDS = ("official_comment", "public_comment", "rebuttal")
AUTHOR_RESPONSE_KINDS = ("official_comment", "rebuttal")
PHASE_BEFORE = "before_author_response"
PHASE_AFTER = "after_author_response"
MAX_THREAD_DEPTH = 100


def role_of(note: dict[str, Any]) -> str:
    """Role of the signer, from the anonymous signature. No identity is kept."""
    for signature in note.get("signatures") or []:
        name = signature.rsplit("/", 1)[-1]
        if name == "Authors":
            return "authors"
        if name.startswith("Reviewer_"):
            return "reviewer"
        if name.startswith("Area_Chair"):
            return "area_chair"
        if name.startswith("Senior_Area_Chair"):
            return "senior_area_chair"
        if name == "Program_Chairs":
            return "program_chairs"
        if name.startswith("~"):
            return "public"
    return "other"


def text(note: dict[str, Any], field: str) -> str | None:
    value = parse.content_value(note, field)
    if value is None:
        return None
    value = str(value).strip()
    return value or None


# --------------------------------------------------------------------------- decisions
def decision_type(decision: str | None) -> str | None:
    """oral / spotlight / poster / accept (no sub-type) / reject, whatever the casing."""
    if decision is None:
        return None
    lowered = decision.lower()
    if "reject" in lowered:
        return "reject"
    if "accept" in lowered:
        for kind in ("oral", "spotlight", "poster"):
            if kind in lowered:
                return kind
        return "accept"
    return None


def label_from_decision(decision: str | None) -> int | None:
    """Binary label: 1 = accept (oral, spotlight or poster), 0 = reject, None = no decision."""
    kind = decision_type(decision)
    if kind is None:
        return None
    return 0 if kind == "reject" else 1


# --------------------------------------------------------------------------- phases and threads
def first_author_response(doc: dict[str, Any], info: dict[str, Any]) -> int | None:
    """Creation time (ms) of the first author reply in the forum, None if there is none."""
    times = [
        reply["tcdate"]
        for reply in doc["replies"]
        if parse.reply_kind(reply, info) in AUTHOR_RESPONSE_KINDS
        and role_of(reply) == "authors"
        and reply.get("tcdate")
    ]
    return min(times) if times else None


def phase_of(tcdate: int | None, author_response: int | None) -> str:
    """A note belongs to the second phase from the first author response onwards."""
    if author_response is not None and tcdate is not None and tcdate >= author_response:
        return PHASE_AFTER
    return PHASE_BEFORE


def thread_target(
    reply: dict[str, Any], forum_id: str, parents: dict[str, str | None], kinds: dict[str, str]
) -> tuple[str | None, str]:
    """Review a note answers, found by walking up its thread.

    Returns (review id or None, thread root). The root is "review", "submission"
    (general comment on the paper), "meta_review", "decision", or "unknown" when a
    parent is missing from the forum (deleted or not readable).
    `parents` maps each reply id of the forum to the id it replies to.
    """
    current = reply.get("replyto")
    for _ in range(MAX_THREAD_DEPTH):
        if current is None:
            return None, "unknown"
        if current == forum_id:
            return None, "submission"
        kind = kinds.get(current)
        if kind == "review":
            return current, "review"
        if kind in ("meta_review", "decision"):
            return None, kind
        if current not in parents:
            return None, "unknown"
        current = parents[current]
    return None, "unknown"


# --------------------------------------------------------------------------- records
def paper_record(doc: dict[str, Any]) -> dict[str, Any]:
    """Model-input view of a submission."""
    submission = doc["submission"]
    keywords = parse.content_value(submission, "keywords") or []
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",")]
    return {
        "forum_id": doc["forum_id"],
        "year": doc["year"],
        "number": doc["number"],
        "title": text(submission, "title"),
        "abstract": text(submission, "abstract"),
        "keywords": [str(k).strip() for k in keywords if str(k).strip()],
        "primary_area": text(submission, "primary_area"),
        "tldr": text(submission, "TLDR"),
    }


def score(reply: dict[str, Any], field: str, rating_levels: dict[int, int] | None) -> int | None:
    """Score as an integer (labelled strings in 2024, integers later); the overall rating
    of a year with another scale is brought to the common one, level by level."""
    value = parse.parse_score(parse.content_value(reply, field))
    if field == "rating" and rating_levels and value is not None:
        if value not in rating_levels:
            raise ValueError(f"review {reply['id']}: rating {value} is not a level of the configured scale")
        return rating_levels[value]
    return value


def review_records(
    doc: dict[str, Any],
    info: dict[str, Any],
    ext: dict[str, dict[str, Any]] | None,
    field_map: dict[str, str],
    windows: dict[str, list[tuple[int, int]]] | None = None,
    rating_levels: dict[int, int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(model-input rows, final-state rows), one of each per review.

    `ext`: external pre-rebuttal scores of the year. None when the year is in
    "current_state": the initial scores of a review are then its current ones, unless it
    was last modified outside the conference-wide edits (`windows`, see
    report.last_modification) — such a review has no initial score.
    """
    initial_rows, final_rows = [], []
    paper_scores = None if ext is None else ext.get(doc["forum_id"])
    author_response = first_author_response(doc, info)
    for reply in doc["replies"]:
        if parse.reply_kind(reply, info) != "review":
            continue
        key = external.reviewer_key(reply)
        pairs = None if paper_scores is None else paper_scores["reviews"].get(key or "")
        # Rename the external fields to ours (the 2024 file uses older names).
        pairs = {field_map[f]: pair for f, pair in (pairs or {}).items() if f in field_map} or None

        ids = {"review_id": reply["id"], "forum_id": doc["forum_id"], "year": doc["year"]}
        initial = {
            **ids,
            "reviewer_key": key,
            "tcdate": reply.get("tcdate"),
            "phase": phase_of(reply.get("tcdate"), author_response),
        }
        current = {field: score(reply, field, rating_levels) for field in SCORE_FIELDS}
        if ext is None:
            unchanged = report.last_modification(reply["tcdate"], reply["tmdate"], windows or {}) != "other"
            for field in SCORE_FIELDS:
                initial[f"{field}_initial"] = current[field] if unchanged else None
            initial["initial_scores_source"] = "current_state" if unchanged else None
        else:
            for field in SCORE_FIELDS:
                initial[f"{field}_initial"] = pairs[field][0] if pairs and field in pairs else None
            initial["initial_scores_source"] = "iclr_insights" if pairs else None
        for field in REVIEW_TEXT_FIELDS:
            initial[field] = text(reply, field)
        initial_rows.append(initial)

        final = dict(ids)
        for field in SCORE_FIELDS:
            final[f"{field}_final"] = current[field]
        final["tcdate"] = reply.get("tcdate")
        final["tmdate"] = reply.get("tmdate")
        final["any_score_changed"] = (
            any(a != b for a, b in pairs.values()) if pairs else None
        )
        for field in SCORE_FIELDS:  # external post-rebuttal value, to validate the join
            final[f"{field}_ext_post"] = pairs[field][1] if pairs and field in pairs else None
        final["tracing_score"] = None if paper_scores is None else paper_scores["tracing_score"]
        final_rows.append(final)
    return initial_rows, final_rows


def discussion_records(doc: dict[str, Any], info: dict[str, Any]) -> list[dict[str, Any]]:
    """Comments and author replies (not reviews, meta-reviews or decisions)."""
    kinds = {reply["id"]: parse.reply_kind(reply, info) for reply in doc["replies"]}
    parents = {reply["id"]: reply.get("replyto") for reply in doc["replies"]}
    author_response = first_author_response(doc, info)
    rows = []
    for reply in doc["replies"]:
        kind = kinds[reply["id"]]
        if kind not in DISCUSSION_KINDS:
            continue
        role = role_of(reply)
        target, root = thread_target(reply, doc["forum_id"], parents, kinds)
        rows.append(
            {
                "reply_id": reply["id"],
                "forum_id": doc["forum_id"],
                "year": doc["year"],
                "replyto": reply.get("replyto"),
                "target_review_id": target,
                "thread_root": root,
                "kind": kind,
                "role": role,
                "reviewer_key": external.reviewer_key(reply) if role == "reviewer" else None,
                "tcdate": reply.get("tcdate"),
                "phase": phase_of(reply.get("tcdate"), author_response),
                "title": text(reply, "title"),
                "text": text(reply, "comment"),
            }
        )
    return rows


def outcome_record(
    doc: dict[str, Any],
    info: dict[str, Any],
    splits: dict[str, Any],
    review_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Labels and everything that depends on the outcome. Never a model input.

    The label comes from the decision note whenever there is one, even if the
    paper was withdrawn afterwards. Papers withdrawn before any decision have no
    label in the main variant and count as rejections in the second one.
    """
    status = parse.paper_status(doc, info)
    decision = parse.decision_text(doc["replies"], info)
    label = label_from_decision(decision)
    withdrawn = status == "withdrawn"
    withdrawn_before_decision = withdrawn and label is None
    label_as_reject = 0 if withdrawn_before_decision else label

    meta = next((r for r in doc["replies"] if parse.reply_kind(r, info) == "meta_review"), None)
    before = [r for r in review_rows if r["phase"] == PHASE_BEFORE]
    n_before_initial = sum(1 for r in before if r["rating_initial"] is not None)
    # Setting A needs the initial rating of every review posted before the author response.
    usable = len(before) > 0 and n_before_initial == len(before)
    author_response = first_author_response(doc, info)
    return {
        "forum_id": doc["forum_id"],
        "year": doc["year"],
        "number": doc["number"],
        "status": status,
        "withdrawn": withdrawn,
        "withdrawn_before_decision": withdrawn_before_decision,
        "decision_text": decision,
        "decision_type": decision_type(decision),
        "label": label,
        "label_withdrawn_as_reject": label_as_reject,
        "meta_review": "\n\n".join(t for t in (text(meta, f) for f in META_REVIEW_FIELDS) if t) or None if meta else None,
        "camera_ready_revision": parse.has_camera_ready_revision(doc["submission"]),
        "has_author_response": author_response is not None,
        "first_author_response_tcdate": author_response,
        "n_reviews": len(review_rows),
        "n_reviews_before_author_response": len(before),
        "n_reviews_before_with_initial_scores": n_before_initial,
        "eligible": label is not None and usable,
        "eligible_withdrawn_as_reject": label_as_reject is not None and usable,
        "split": assign_split(doc["forum_id"], doc["year"], splits),
    }
