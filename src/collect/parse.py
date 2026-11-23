"""Version-agnostic reading of raw OpenReview documents (API v1 and v2).

Only used to describe the raw data (collection report). The normalised tables
of the cleaning phase are built later, in src/clean/.
"""

import re
from typing import Any

STATUSES = ("accepted", "rejected", "withdrawn", "desk_rejected", "undecided")


def content_value(note: dict[str, Any], key: str) -> Any:
    """Content field of a note: plain value in API v1, {"value": ...} in API v2."""
    value = (note.get("content") or {}).get(key)
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def invitations(note: dict[str, Any]) -> list[str]:
    """Invitation ids of a note: `invitations` (v2) or `invitation` (v1)."""
    if note.get("invitations"):
        return list(note["invitations"])
    return [note["invitation"]] if note.get("invitation") else []


def reply_kind(reply: dict[str, Any], info: dict[str, Any]) -> str:
    """Classify a reply from the name of its invitation."""
    names = [inv.split("/-/")[-1] for inv in invitations(reply)]
    if info["review_name"] in names:
        return "review"
    if info["meta_review_name"] in names:
        return "meta_review"
    if info["decision_name"] in names:
        return "decision"
    for name in names:
        if "Desk_Reject" in name:
            return "desk_rejection"
        if "Withdraw" in name:
            return "withdrawal"
        if "Rebuttal" in name:
            return "rebuttal"
        if name == "Official_Comment":
            return "official_comment"
        if name == "Public_Comment":
            return "public_comment"
    return "other"


def signed_by_authors(note: dict[str, Any]) -> bool:
    return any(s.endswith("/Authors") for s in note.get("signatures") or [])


def parse_score(value: Any) -> int | None:
    """Leading integer of a score such as 8 or "8: accept, good paper"."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.match(r"\s*(-?\d+)", value)
        if match:
            return int(match.group(1))
    return None


def first_present(note_or_content: dict[str, Any], fields: str | list[str]) -> Any:
    """Value of the first field that exists (the rating field name varies across years)."""
    for field in [fields] if isinstance(fields, str) else fields:
        value = content_value(note_or_content, field)
        if value is not None:
            return value
    return None


def version_time(version: dict[str, Any]) -> int:
    return version.get("tcdate") or version.get("cdate") or 0


def version_content(version: dict[str, Any], api: str) -> dict[str, Any]:
    """Content carried by one version: a reference (v1) is a note, an edit (v2) wraps one."""
    if api == "v2":
        return (version.get("note") or {}).get("content") or {}
    return version.get("content") or {}


def decision_text(replies: list[dict[str, Any]], info: dict[str, Any]) -> str | None:
    for reply in replies:
        if reply_kind(reply, info) == "decision":
            value = content_value(reply, "decision")
            return str(value) if value is not None else None
    return None


def paper_status(doc: dict[str, Any], info: dict[str, Any]) -> str:
    """accepted / rejected / withdrawn / desk_rejected / undecided, kept strictly apart."""
    submission = doc["submission"]
    decision = decision_text(doc["replies"], info)

    if info["api_version"] == "v2":
        venueid = content_value(submission, "venueid")
        if venueid and venueid == info.get("withdrawn_venue_id"):
            return "withdrawn"
        if venueid and venueid == info.get("desk_rejected_venue_id"):
            return "desk_rejected"
        if venueid and venueid == info.get("rejected_venue_id"):
            return "rejected"
        if venueid and venueid == info["venue_id"]:
            return "accepted"
    else:
        invitation = submission.get("invitation") or ""
        if invitation == info["withdrawn_invitation"]:
            return "withdrawn"
        if invitation == info["desk_rejected_invitation"]:
            return "desk_rejected"

    if decision is not None:
        if "accept" in decision.lower():
            return "accepted"
        if "reject" in decision.lower():
            return "rejected"
    return "undecided"


def review_rows(
    doc: dict[str, Any], history: dict[str, Any] | None, info: dict[str, Any]
) -> list[dict[str, Any]]:
    """One row per review: current (final) scores, timestamps, readable versions.

    `history` is None when the history of the forum has not been collected yet.
    What the pilot showed about versions (2026-11-15):
      - API v1: a review has a single reference, identical to its current content;
      - API v2: the creation edit of a review is not readable; the first readable
        edit is the conference-wide edit that released the reviews, followed by
        the edits made by the reviewer afterwards.
    So the initial content is only known for reviews that were never modified
    after their release; see report.flag_modified_after_release().
    """
    api = info["api_version"]
    review_suffix = "/-/" + info["review_name"]
    rows = []
    for reply in doc["replies"]:
        if reply_kind(reply, info) != "review":
            continue
        versions = None if history is None else history["versions"].get(reply["id"])
        creation_readable = None
        reviewer_edits = None
        if versions is not None and api == "v2":
            with_content = [v for v in versions if version_content(v, api)]
            creation_readable = any(
                abs(version_time(v) - reply["tcdate"]) < 60_000 for v in with_content
            )
            reviewer_edits = sum(
                1 for v in with_content if (v.get("invitation") or "").endswith(review_suffix)
            )
        rows.append(
            {
                "year": doc["year"],
                "api_version": api,
                "forum_id": doc["forum_id"],
                "review_id": reply["id"],
                "content_fields": sorted((reply.get("content") or {}).keys()),
                "rating_final": parse_score(first_present(reply, info["rating_field"])),
                "confidence_final": parse_score(first_present(reply, info["confidence_field"])),
                "tcdate": reply.get("tcdate"),
                "tmdate": reply.get("tmdate"),
                "history_collected": versions is not None,
                "history_forbidden": history is not None and reply["id"] in history["errors"],
                "n_versions_readable": len(versions) if versions is not None else None,
                "creation_edit_readable": creation_readable,
                "n_reviewer_edits_readable": reviewer_edits,
            }
        )
    return rows


def has_meta_review(replies: list[dict[str, Any]], info: dict[str, Any]) -> bool:
    """A meta-review note, or a decision note that embeds the meta-review (ICLR 2023)."""
    for reply in replies:
        kind = reply_kind(reply, info)
        if kind == "meta_review":
            return True
        if kind == "decision" and any(
            key.lower().startswith("metareview") for key in reply.get("content") or {}
        ):
            return True
    return False


def has_camera_ready_revision(submission: dict[str, Any]) -> bool:
    """True if the submission was edited through a camera-ready invitation (API v2).

    The current content of such a note is posterior to the decision.
    """
    return any("Camera_Ready" in inv.split("/-/")[-1] for inv in invitations(submission))


def paper_row(
    doc: dict[str, Any], history: dict[str, Any] | None, info: dict[str, Any]
) -> dict[str, Any]:
    """One row per submission: status, counts of replies, missing fields."""
    submission = doc["submission"]
    replies = doc["replies"]
    kinds = [reply_kind(r, info) for r in replies]
    author_replies = sum(
        1
        for reply, kind in zip(replies, kinds)
        if kind in ("official_comment", "rebuttal") and signed_by_authors(reply)
    )
    author_reply_times = [
        reply["tcdate"]
        for reply, kind in zip(replies, kinds)
        if kind in ("official_comment", "rebuttal") and signed_by_authors(reply) and reply.get("tcdate")
    ]
    versions = None if history is None else history["versions"].get(submission["id"])
    return {
        "year": doc["year"],
        "api_version": info["api_version"],
        "forum_id": doc["forum_id"],
        "number": doc.get("number"),
        "first_author_reply_tcdate": min(author_reply_times) if author_reply_times else None,
        "status": paper_status(doc, info),
        "decision": decision_text(replies, info),
        "n_reviews": kinds.count("review"),
        "n_author_replies": author_replies,
        "n_official_comments": kinds.count("official_comment"),
        "n_public_comments": kinds.count("public_comment"),
        "has_meta_review": has_meta_review(replies, info),
        "has_decision": "decision" in kinds,
        "missing_title": not content_value(submission, "title"),
        "missing_abstract": not content_value(submission, "abstract"),
        "missing_keywords": not content_value(submission, "keywords"),
        "has_pdf": bool(content_value(submission, "pdf")),
        "camera_ready_revision": has_camera_ready_revision(submission),
        "history_collected": history is not None,
        "submission_n_versions": len(versions) if versions is not None else None,
    }
