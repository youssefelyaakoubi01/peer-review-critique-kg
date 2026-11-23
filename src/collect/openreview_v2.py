"""Collection for API v2 venues (ICLR 2024 and later)."""

from typing import Any

from src.collect.client import OpenReviewError, OpenReviewSession

API = "v2"


def venue_info(venue_id: str, group: dict[str, Any]) -> dict[str, Any]:
    """Invitation names and venue ids published in the venue group content."""
    content = group.get("content") or {}

    def value(key: str, default: Any = None) -> Any:
        return (content.get(key) or {}).get("value", default)

    return {
        "api_version": API,
        "venue_id": venue_id,
        "submission_invitation": value("submission_id", f"{venue_id}/-/Submission"),
        "review_name": value("review_name", "Official_Review"),
        "meta_review_name": value("meta_review_name", "Meta_Review"),
        "decision_name": value("decision_name", "Decision"),
        "rating_field": value("review_rating", "rating"),
        "confidence_field": value("review_confidence", "confidence"),
        "submission_venue_id": value("submission_venue_id"),
        "withdrawn_venue_id": value("withdrawn_venue_id"),
        "desk_rejected_venue_id": value("desk_rejected_venue_id"),
        "rejected_venue_id": value("rejected_venue_id"),
    }


def list_submissions(
    session: OpenReviewSession,
    info: dict[str, Any],
    max_items: int | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Submissions with all their replies. `status`: None (any), "withdrawn", "desk_rejected"."""
    params: dict[str, Any] = {"invitation": info["submission_invitation"], "details": "replies"}
    if status is not None:
        venueid = info[f"{status}_venue_id"]
        if not venueid:
            return []
        params["content.venueid"] = venueid
    if max_items is not None:
        params["sort"] = "number:asc"
    return session.get_all(API, "/notes", "notes", params, max_items=max_items)


def fetch_forum(
    session: OpenReviewSession, info: dict[str, Any], note: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Split a listed note into (submission, replies); replies came with the listing."""
    submission = {k: v for k, v in note.items() if k != "details"}
    replies = (note.get("details") or {}).get("replies") or []
    return submission, replies


def fetch_versions(session: OpenReviewSession, note_id: str) -> list[dict[str, Any]]:
    """Edit history of one note (raw edits)."""
    return session.get(API, "/notes/edits", {"note.id": note_id})["edits"]


def is_review(reply: dict[str, Any], info: dict[str, Any]) -> bool:
    suffix = "/-/" + info["review_name"]
    return any(inv.endswith(suffix) for inv in reply.get("invitations") or [])


def fetch_history(
    session: OpenReviewSession,
    info: dict[str, Any],
    submission: dict[str, Any],
    replies: list[dict[str, Any]],
) -> dict[str, Any]:
    """All versions of the submission and of each review."""
    targets = [submission["id"]] + [r["id"] for r in replies if is_review(r, info)]
    versions: dict[str, list[dict[str, Any]]] = {}
    errors: dict[str, dict[str, Any]] = {}
    for note_id in targets:
        try:
            versions[note_id] = fetch_versions(session, note_id)
        except OpenReviewError as exc:
            # A history we are not allowed to read is a finding, not a crash.
            if exc.status == 403 and exc.name != "ChallengeRequiredError":
                errors[note_id] = exc.as_dict()
            else:
                raise
    return {"versions": versions, "errors": errors}
