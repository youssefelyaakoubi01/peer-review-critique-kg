"""Version-agnostic orchestration: sampling, per-forum collection, resumability.

Two passes, because the two kinds of requests have very different quotas:
  1. notes   (submission + replies, current state): cheap, done for every forum;
  2. history (versions of the submission and of each review): the edit endpoint
     allows very few requests per hour, so this pass stops cleanly when the quota
     is exhausted and continues at the next run.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.collect import openreview_v1, openreview_v2, parse, store
from src.collect.client import OpenReviewSession, RateLimitExceeded, api_version

MODULES = {"v1": openreview_v1, "v2": openreview_v2}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pilot_allocation(years: list[int], size: int) -> dict[int, int]:
    """Split the pilot size evenly across years; the remainder goes to the first years."""
    base, extra = divmod(size, len(years))
    return {year: base + (1 if i < extra else 0) for i, year in enumerate(years)}


def unique_by_id(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for note in notes:
        unique.setdefault(note["id"], note)
    return list(unique.values())


def sample_submissions(
    session: OpenReviewSession,
    module: Any,
    info: dict[str, Any],
    n_total: int,
    n_withdrawn: int,
    n_desk_rejected: int,
) -> list[dict[str, Any]]:
    """Pilot sample: a few withdrawn and desk-rejected papers, then the lowest numbers."""
    notes: list[dict[str, Any]] = []
    if n_withdrawn > 0:
        notes += module.list_submissions(session, info, max_items=n_withdrawn, status="withdrawn")
    if n_desk_rejected > 0:
        notes += module.list_submissions(
            session, info, max_items=n_desk_rejected, status="desk_rejected"
        )
    notes += module.list_submissions(session, info, max_items=n_total)
    return unique_by_id(notes)[:n_total]


def all_submissions(
    session: OpenReviewSession, module: Any, info: dict[str, Any]
) -> list[dict[str, Any]]:
    """Every submission of a venue, whatever its status."""
    notes = module.list_submissions(session, info)
    if info["api_version"] == "v1":
        # In API v1, withdrawn and desk-rejected papers live under their own invitations.
        notes += module.list_submissions(session, info, status="withdrawn")
        notes += module.list_submissions(session, info, status="desk_rejected")
    return unique_by_id(notes)


def collect_notes(
    session: OpenReviewSession,
    raw_dir: Path,
    venue: str,
    venue_id: str,
    year: int,
    log: logging.Logger,
    sample: dict[str, int] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Pass 1 for one year: submissions and replies in their current state."""
    version, group = api_version(session, venue_id)
    module = MODULES[version]
    info = module.venue_info(venue_id, group)
    store.write_json(
        store.year_dir(raw_dir, venue, year) / "venue.json",
        {"info": info, "group": group, "collected_at": utc_now()},
    )
    log.info("year=%d venue=%s api=%s", year, venue_id, version)

    if sample is not None:
        notes = sample_submissions(
            session, module, info, sample["total"], sample["withdrawn"], sample["desk_rejected"]
        )
    else:
        notes = all_submissions(session, module, info)
    log.info("year=%d submissions_to_collect=%d", year, len(notes))

    counts = {"collected": 0, "skipped": 0}
    for i, note in enumerate(notes, start=1):
        path = store.notes_path(raw_dir, venue, year, note["id"])
        if path.exists() and not force:
            counts["skipped"] += 1
        else:
            submission, replies = module.fetch_forum(session, info, note)
            store.write_json(
                path,
                {
                    "api_version": version,
                    "venue_id": venue_id,
                    "year": year,
                    "forum_id": note["id"],
                    "number": submission.get("number"),
                    "collected_at": utc_now(),
                    "submission": submission,
                    "replies": replies,
                },
            )
            counts["collected"] += 1
        if i % (10 if len(notes) <= 200 else 1000) == 0 or i == len(notes):
            log.info(
                "year=%d notes progress=%d/%d collected=%d skipped=%d requests=%d",
                year, i, len(notes), counts["collected"], counts["skipped"], session.n_requests,
            )

    return {
        "api_version": version,
        "venue_id": venue_id,
        "forums": [n["id"] for n in notes],
        "n_collected": counts["collected"],
        "n_skipped": counts["skipped"],
    }


def pending_histories(
    raw_dir: Path, venue: str, runs: dict[str, dict[str, Any]], force: bool
) -> tuple[list[tuple[int, str, dict[str, Any], dict[str, Any]]], int]:
    """Forums without history, decided papers first and years interleaved.

    The order matters when the quota only allows a few forums per run: decided
    papers of every year are the most informative.
    """
    ranked = []
    n_done = 0
    for year_str, run in runs.items():
        year = int(year_str)
        info = store.read_json(store.year_dir(raw_dir, venue, year) / "venue.json")["info"]
        todo = []
        for forum_id in run["forums"]:
            if store.history_path(raw_dir, venue, year, forum_id).exists() and not force:
                n_done += 1
                continue
            doc = store.read_json(store.notes_path(raw_dir, venue, year, forum_id))
            decided = parse.decision_text(doc["replies"], info) is not None
            todo.append((0 if decided else 1, doc))
        todo.sort(key=lambda item: item[0])  # stable: keeps the listing order otherwise
        ranked += [(rank, year, doc, info) for rank, (_, doc) in enumerate(todo)]
    ranked.sort(key=lambda item: (item[0], -item[1]))
    return [(year, doc["forum_id"], doc, info) for _, year, doc, info in ranked], n_done


def collect_histories(
    session: OpenReviewSession,
    raw_dir: Path,
    venue: str,
    runs: dict[str, dict[str, Any]],
    log: logging.Logger,
    force: bool = False,
) -> dict[str, Any]:
    """Pass 2: versions of each submission and review, until done or out of quota."""
    pending, n_done = pending_histories(raw_dir, venue, runs, force)
    log.info("history: already_on_disk=%d to_collect=%d", n_done, len(pending))
    summary: dict[str, Any] = {"n_collected": 0, "n_skipped": n_done, "stopped_by": None}

    for year, forum_id, doc, info in pending:
        module = MODULES[info["api_version"]]
        try:
            history = module.fetch_history(session, info, doc["submission"], doc["replies"])
        except RateLimitExceeded as exc:
            summary["stopped_by"] = exc.as_dict()
            log.warning("history stopped: %s", exc)
            break
        store.write_json(
            store.history_path(raw_dir, venue, year, forum_id),
            {
                "api_version": info["api_version"],
                "year": year,
                "forum_id": forum_id,
                "collected_at": utc_now(),
                **history,
            },
        )
        summary["n_collected"] += 1
        log.info(
            "history year=%d forum=%s done (%d/%d) requests=%d",
            year, forum_id, summary["n_collected"], len(pending), session.n_requests,
        )

    summary["n_pending"] = len(pending) - summary["n_collected"]
    return summary
