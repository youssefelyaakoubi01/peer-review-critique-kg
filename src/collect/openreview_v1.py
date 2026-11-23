"""Collection for API v1 venues (ICLR 2023 and earlier)."""

from typing import Any

from src.collect.client import OpenReviewError, OpenReviewSession

API = "v1"


def venue_info(venue_id: str, group: dict[str, Any]) -> dict[str, Any]:
    """Invitation names for a double-blind API v1 venue (conventions, not published in the group)."""
    return {
        "api_version": API,
        "venue_id": venue_id,
        "submission_invitation": f"{venue_id}/-/Blind_Submission",
        "withdrawn_invitation": f"{venue_id}/-/Withdrawn_Submission",
        "desk_rejected_invitation": f"{venue_id}/-/Desk_Rejected_Submission",
        "review_name": "Official_Review",
        "meta_review_name": "Meta_Review",
        "decision_name": "Decision",
        # ICLR used "rating" until 2022 and "recommendation" in 2023.
        "rating_field": ["rating", "recommendation"],
        "confidence_field": "confidence",
    }


def list_submissions(
    session: OpenReviewSession,
    info: dict[str, Any],
    max_items: int | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Submission notes. `status`: None (active blind submissions), "withdrawn", "desk_rejected"."""
    invitation = info["submission_invitation"] if status is None else info[f"{status}_invitation"]
    params: dict[str, Any] = {"invitation": invitation}
    if max_items is not None:
        params["sort"] = "number:asc"
    return session.get_all(API, "/notes", "notes", params, max_items=max_items)


def fetch_forum(
    session: OpenReviewSession, info: dict[str, Any], note: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """All notes of the forum: nested replies (author responses) are not direct replies."""
    forum_id = note["forum"]
    notes = session.get_all(API, "/notes", "notes", {"forum": forum_id})
    replies = [n for n in notes if n["id"] != forum_id]
    return note, replies


def fetch_versions(
    session: OpenReviewSession, note_id: str, original: bool = False
) -> list[dict[str, Any]]:
    """Revision history of one note (raw references)."""
    params: dict[str, Any] = {"referent": note_id}
    if original:
        params["original"] = True
    return session.get(API, "/references", params)["references"]


def is_review(reply: dict[str, Any], info: dict[str, Any]) -> bool:
    return (reply.get("invitation") or "").endswith("/-/" + info["review_name"])


def fetch_history(
    session: OpenReviewSession,
    info: dict[str, Any],
    submission: dict[str, Any],
    replies: list[dict[str, Any]],
) -> dict[str, Any]:
    """All versions of the submission and of each review."""
    targets = [(submission["id"], True)] + [(r["id"], False) for r in replies if is_review(r, info)]
    versions: dict[str, list[dict[str, Any]]] = {}
    errors: dict[str, dict[str, Any]] = {}
    for note_id, original in targets:
        try:
            versions[note_id] = fetch_versions(session, note_id, original=original)
        except OpenReviewError as exc:
            # A history we are not allowed to read is a finding, not a crash.
            if exc.status == 403 and exc.name != "ChallengeRequiredError":
                errors[note_id] = exc.as_dict()
            else:
                raise
    return {"versions": versions, "errors": errors}
