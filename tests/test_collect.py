"""Offline tests of the collection code: no network, synthetic notes only.

The synthetic notes mirror what the pilot showed about real data (2026-11-15):
  - API v1: a review has one reference, identical to its current content;
  - API v2: the creation edit of a review is not readable; the first readable edit
    is the conference-wide release edit (no content), then the reviewer's edits.
"""

import logging

import pytest

from src.collect import collector, external, parse, report, store
from src.collect.client import (
    OpenReviewError,
    OpenReviewSession,
    RateLimiter,
    RateLimitExceeded,
    api_version,
)
from src.collect.openalex import best_match, match_row, normalise_title
from src.utils.config import load_config

LOG = logging.getLogger("test_collect")
VENUE = "ICLR"
V2_ID = "ICLR.cc/2024/Conference"
V1_ID = "ICLR.cc/2023/Conference"
RELEASE = 1000  # minute at which the synthetic API v2 reviews are released


def minutes(m):
    return m * 60_000


# --------------------------------------------------------------------------- fake API v2
def v2_note(note_id, number, venueid, replies=()):
    return {
        "id": note_id,
        "forum": note_id,
        "number": number,
        "invitations": [f"{V2_ID}/-/Submission"],
        "content": {
            "title": {"value": f"Paper {number}"},
            "abstract": {"value": "An abstract."},
            "keywords": {"value": ["graphs"]},
            "pdf": {"value": f"/pdf/{note_id}.pdf"},
            "venueid": {"value": venueid},
        },
        "details": {"replies": list(replies)},
    }


def v2_reply(reply_id, forum, number, name, content, signature="Reviewer_abc", created=100, modified=None):
    return {
        "id": reply_id,
        "forum": forum,
        "invitations": [f"{V2_ID}/Submission{number}/-/{name}"],
        "signatures": [f"{V2_ID}/Submission{number}/{signature}"],
        "tcdate": minutes(created),
        "tmdate": minutes(created if modified is None else modified),
        "content": {k: {"value": v} for k, v in content.items()},
    }


V2_GROUP = {
    "id": V2_ID,
    "domain": V2_ID,
    "content": {
        "submission_id": {"value": f"{V2_ID}/-/Submission"},
        "review_name": {"value": "Official_Review"},
        "meta_review_name": {"value": "Meta_Review"},
        "decision_name": {"value": "Decision"},
        "review_rating": {"value": "rating"},
        "review_confidence": {"value": "confidence"},
        "submission_venue_id": {"value": f"{V2_ID}/Submission"},
        "withdrawn_venue_id": {"value": f"{V2_ID}/Withdrawn_Submission"},
        "desk_rejected_venue_id": {"value": f"{V2_ID}/Desk_Rejected_Submission"},
        "rejected_venue_id": {"value": f"{V2_ID}/Rejected_Submission"},
    },
}

V2_NOTES = [
    v2_note("W", 3, f"{V2_ID}/Withdrawn_Submission"),
    v2_note("K", 4, f"{V2_ID}/Desk_Rejected_Submission"),
    v2_note(
        "A",
        1,
        V2_ID,
        replies=[
            # R1: modified by the reviewer after the release (rating raised to 8).
            v2_reply("R1", "A", 1, "Official_Review", {"rating": "8: accept", "confidence": 4, "soundness": 3},
                     created=100, modified=2000),
            v2_reply("R2", "A", 1, "Official_Review", {"rating": 5, "confidence": 3, "soundness": 2},
                     created=110, modified=RELEASE),
            v2_reply("C1", "A", 1, "Official_Comment", {"comment": "We thank the reviewer."}, "Authors", 1200),
            v2_reply("M1", "A", 1, "Meta_Review", {"metareview": "Fine."}, "Area_Chair_x", 3000),
            v2_reply("D1", "A", 1, "Decision", {"decision": "Accept (poster)"}, "Program_Chairs", 3100),
        ],
    ),
    v2_note(
        "B",
        2,
        f"{V2_ID}/Rejected_Submission",
        replies=[
            v2_reply("R3", "B", 2, "Official_Review", {"rating": 3, "confidence": 4}, created=120, modified=RELEASE),
            # R4: posted after the release and never modified.
            v2_reply("R4", "B", 2, "Official_Review", {"rating": 5, "confidence": 2}, created=1500),
            v2_reply("D2", "B", 2, "Decision", {"decision": "Reject"}, "Program_Chairs", 3100),
        ],
    ),
]

RELEASE_EDIT = {"tcdate": minutes(RELEASE), "invitation": f"{V2_ID}/-/Edit", "note": {"readers": ["everyone"]}}
V2_EDITS = {
    "A": [],
    "B": [],
    "W": [],
    "K": [],
    "R1": [
        {**RELEASE_EDIT, "id": "e1"},
        {
            "id": "e2",
            "tcdate": minutes(2000),
            "invitation": f"{V2_ID}/Submission1/-/Official_Review",
            "note": {"content": {"rating": {"value": "8: accept"}, "confidence": {"value": 4}}},
        },
    ],
    "R3": [{**RELEASE_EDIT, "id": "e3"}],
    "R4": [],
}


# As on OpenReview: the accepted paper was edited through a camera-ready invitation.
next(n for n in V2_NOTES if n["id"] == "A")["invitations"].append(
    f"{V2_ID}/Submission1/-/Camera_Ready_Revision"
)


# --------------------------------------------------------------------------- fake API v1
def v1_note(note_id, number, invitation_name, forum=None, replyto=None, content=None,
            signature="Authors", created=10, modified=None):
    return {
        "id": note_id,
        "forum": forum or note_id,
        "replyto": replyto,
        "number": number,
        "invitation": f"{V1_ID}/{invitation_name}",
        "signatures": [f"{V1_ID}/Paper{number}/{signature}"],
        "tcdate": minutes(created),
        "tmdate": minutes(created if modified is None else modified),
        "content": content
        or {"title": f"Paper {number}", "abstract": "An abstract.", "keywords": [], "pdf": "/pdf/x.pdf"},
    }


V1_LISTINGS = {
    f"{V1_ID}/-/Blind_Submission": [v1_note("P1", 1, "-/Blind_Submission")],
    f"{V1_ID}/-/Withdrawn_Submission": [v1_note("P2", 2, "-/Withdrawn_Submission")],
    f"{V1_ID}/-/Desk_Rejected_Submission": [v1_note("P3", 3, "-/Desk_Rejected_Submission")],
}
V1_REVIEW = {"recommendation": "5: marginally below", "confidence": "4: confident", "correctness": "3"}
V1_FORUMS = {
    "P1": [
        V1_LISTINGS[f"{V1_ID}/-/Blind_Submission"][0],
        # V1: modified after the first author reply (minute 500).
        v1_note("V1", 1, "Paper1/-/Official_Review", "P1", "P1", V1_REVIEW, "AnonReviewer1", 100, 900),
        # V4: modified, but before the discussion started.
        v1_note("V4", 1, "Paper1/-/Official_Review", "P1", "P1", V1_REVIEW, "AnonReviewer2", 120, 130),
        # Nested reply: answers the review, not the submission.
        v1_note("V2", 1, "Paper1/-/Official_Comment", "P1", "V1", {"comment": "Response."}, "Authors", 500),
        # ICLR 2023 embeds the meta-review in the decision note.
        v1_note("V3", 1, "Paper1/-/Decision", "P1", "P1",
                {"decision": "Reject", "metareview:_summary,_strengths_and_weaknesses": "…"}, "Program_Chairs", 3000),
    ],
    "P2": [V1_LISTINGS[f"{V1_ID}/-/Withdrawn_Submission"][0]],
    "P3": [V1_LISTINGS[f"{V1_ID}/-/Desk_Rejected_Submission"][0]],
}
V1_REFERENCES = {
    "P1": [{"id": "r0", "tcdate": minutes(5), "content": {"title": "Paper 1 (first version)"}},
           {"id": "r1", "tcdate": minutes(10), "content": {"title": "Paper 1"}}],
    # A single reference, identical to the current content.
    "V1": [{"id": "r2", "tcdate": minutes(100), "tmdate": minutes(900), "content": V1_REVIEW}],
    "V4": [{"id": "r3", "tcdate": minutes(120), "tmdate": minutes(130), "content": V1_REVIEW}],
}


class FakeSession(OpenReviewSession):
    """Answers from the synthetic data above and records every request."""

    def __init__(self, edit_quota=None):
        self.n_requests = 0
        self.calls = []
        self.challenge = False
        self.edit_quota = edit_quota  # None = unlimited

    def get(self, api, endpoint, params):
        self.n_requests += 1
        self.calls.append((api, endpoint, dict(params)))
        if self.challenge:
            raise OpenReviewError(403, "ChallengeRequiredError", "Challenge verification required")
        if endpoint == "/groups":
            group = V2_GROUP if params["id"] == V2_ID else {"id": params["id"]}
            return {"groups": [group]}
        if api == "v2" and endpoint == "/notes":
            notes = V2_NOTES
            if "content.venueid" in params:
                notes = [n for n in notes if n["content"]["venueid"]["value"] == params["content.venueid"]]
            return {"notes": notes[: params.get("limit", 1000)]}
        if api == "v2" and endpoint == "/notes/edits":
            if self.edit_quota is not None:
                if self.edit_quota == 0:
                    raise RateLimitExceeded("v2 /notes/edits", 2400, "18;w=3600")
                self.edit_quota -= 1
            note_id = params["note.id"]
            if note_id == "R2":
                raise OpenReviewError(403, "ForbiddenError", "no permission to read edits")
            return {"edits": V2_EDITS[note_id]}
        if api == "v1" and endpoint == "/notes":
            if "forum" in params:
                return {"notes": V1_FORUMS[params["forum"]]}
            return {"notes": V1_LISTINGS[params["invitation"]][: params.get("limit", 1000)]}
        if api == "v1" and endpoint == "/references":
            return {"references": V1_REFERENCES.get(params["referent"], [])}
        raise AssertionError(f"unexpected request: {api} {endpoint} {params}")


@pytest.fixture()
def session():
    return FakeSession()


def collect(session, tmp_path, venue_id, year, history=True, **kwargs):
    """Notes pass, then (optionally) history pass, for one year."""
    force = kwargs.get("force", False)
    run = collector.collect_notes(session, tmp_path, VENUE, venue_id, year, LOG, **kwargs)
    summary = None
    if history:
        summary = collector.collect_histories(session, tmp_path, VENUE, {str(year): run}, LOG, force=force)
    return run, summary


def load(tmp_path, year, forum_id):
    info = store.read_json(store.year_dir(tmp_path, VENUE, year) / "venue.json")["info"]
    doc = store.read_json(store.notes_path(tmp_path, VENUE, year, forum_id))
    path = store.history_path(tmp_path, VENUE, year, forum_id)
    return doc, (store.read_json(path) if path.exists() else None), info


def status(tmp_path, year, forum_id):
    doc, _, info = load(tmp_path, year, forum_id)
    return parse.paper_status(doc, info)


def tables(tmp_path, runs):
    papers, reviews, openalex = report.load_rows(tmp_path, VENUE, {"years": runs}, 0.95)
    return report.by_year_table(papers, reviews).set_index("year"), papers, reviews, openalex


# --------------------------------------------------------------------------- client
def test_api_version_follows_group_domain(session):
    assert api_version(session, V2_ID)[0] == "v2"
    assert api_version(session, V1_ID)[0] == "v1"


def test_rate_limiter_enforces_minimum_interval():
    now = [0.0]
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    limiter = RateLimiter(30, clock=lambda: now[0], sleep=sleep)  # one request every 2 s
    limiter.wait()
    limiter.wait()
    now[0] += 5.0  # idle longer than the interval: no sleep needed
    limiter.wait()
    assert sleeps == [2.0]


def test_pilot_allocation_sums_to_size():
    assert collector.pilot_allocation([2023, 2024, 2025], 50) == {2023: 17, 2024: 17, 2025: 16}


# --------------------------------------------------------------------------- API v2
def test_v2_collects_all_statuses_separately(session, tmp_path):
    run, _ = collect(session, tmp_path, V2_ID, 2024)
    assert run["api_version"] == "v2"
    assert sorted(run["forums"]) == ["A", "B", "K", "W"]
    statuses = {f: status(tmp_path, 2024, f) for f in run["forums"]}
    assert statuses == {"A": "accepted", "B": "rejected", "W": "withdrawn", "K": "desk_rejected"}


def test_v2_final_state_and_versions_are_stored_apart(session, tmp_path):
    collect(session, tmp_path, V2_ID, 2024)
    doc, history, info = load(tmp_path, 2024, "A")
    rows = {r["review_id"]: r for r in parse.review_rows(doc, history, info)}

    # Final state in notes/, every readable version in history/.
    assert doc["replies"][0]["content"]["rating"]["value"] == "8: accept"
    assert len(history["versions"]["R1"]) == 2
    assert rows["R1"]["rating_final"] == 8
    assert rows["R1"]["n_reviewer_edits_readable"] == 1
    # The creation edit is not among the readable ones: the initial content is unknown.
    assert rows["R1"]["creation_edit_readable"] is False


def test_v2_unreadable_history_is_recorded_not_fatal(session, tmp_path):
    collect(session, tmp_path, V2_ID, 2024)
    doc, history, info = load(tmp_path, 2024, "A")
    rows = {r["review_id"]: r for r in parse.review_rows(doc, history, info)}
    assert history["errors"]["R2"]["name"] == "ForbiddenError"
    assert rows["R2"]["history_forbidden"]
    assert not rows["R2"]["history_collected"]


def test_v2_paper_row_counts_replies(session, tmp_path):
    collect(session, tmp_path, V2_ID, 2024)
    row = parse.paper_row(*load(tmp_path, 2024, "A"))
    assert row["n_reviews"] == 2
    assert row["n_author_replies"] == 1
    assert row["has_meta_review"] and row["has_decision"]
    assert row["decision"] == "Accept (poster)"
    assert not row["missing_abstract"]


def test_v2_reviews_modified_after_release_are_flagged(session, tmp_path):
    run, _ = collect(session, tmp_path, V2_ID, 2024)
    _, papers, reviews, _ = tables(tmp_path, {"2024": run})
    releases = report.release_times(papers, reviews)
    assert releases[2024] == minutes(RELEASE)  # most frequent modification minute

    flagged = report.flag_modified_after_release(reviews, releases).set_index("review_id")
    assert flagged.loc["R1", "modified_after_release"] is True
    assert flagged.loc["R2", "modified_after_release"] is False
    assert flagged.loc["R3", "modified_after_release"] is False
    assert flagged.loc["R4", "modified_after_release"] is False  # posted late, never modified


def test_release_burst_spans_several_minutes():
    import pandas as pd

    # 100 reviews stamped per minute during minutes 1000-1020, then scattered reviewer edits.
    burst = [minutes(m) + 1000 * i for m in range(1000, 1021) for i in range(50)]
    scattered = [minutes(m) for m in (1023, 1027, 1031, 1500, 2000)]
    assert report.release_burst_end(pd.Series(burst + scattered)) == minutes(1020)
    assert report.release_burst_end(pd.Series([], dtype="float64")) is None


def test_pilot_sample_respects_size(session, tmp_path):
    run, _ = collect(session, tmp_path, V2_ID, 2024, sample={"total": 3, "withdrawn": 1, "desk_rejected": 1})
    assert run["forums"] == ["W", "K", "A"]


# --------------------------------------------------------------------------- API v1
def test_v1_collects_all_statuses_and_nested_replies(session, tmp_path):
    run, _ = collect(session, tmp_path, V1_ID, 2023)
    assert run["api_version"] == "v1"
    assert sorted(run["forums"]) == ["P1", "P2", "P3"]

    row = parse.paper_row(*load(tmp_path, 2023, "P1"))
    assert row["status"] == "rejected"
    assert row["n_reviews"] == 2
    assert row["n_author_replies"] == 1  # nested under the review
    assert row["has_meta_review"]  # embedded in the decision note
    assert row["submission_n_versions"] == 2
    assert status(tmp_path, 2023, "P2") == "withdrawn"
    assert status(tmp_path, 2023, "P3") == "desk_rejected"


def test_v1_modification_is_measured_against_the_first_author_reply(session, tmp_path):
    run, _ = collect(session, tmp_path, V1_ID, 2023)
    by_year, papers, reviews, _ = tables(tmp_path, {"2023": run})
    releases = report.release_times(papers, reviews)
    assert releases[2023] == minutes(500)

    flagged = report.flag_modified_after_release(reviews, releases).set_index("review_id")
    assert flagged.loc["V1", "modified_after_release"] is True
    assert flagged.loc["V4", "modified_after_release"] is False  # modified before the discussion
    assert flagged.loc["V1", "rating_final"] == 5
    assert "correctness" in flagged.loc["V1", "content_fields"]
    assert by_year.loc[2023, "reviews_modified_after_release"] == 1
    assert by_year.loc[2023, "reviewed_papers_all_initial_known"] == 0


# --------------------------------------------------------------------------- resumability and quotas
def test_second_run_downloads_nothing(session, tmp_path):
    first, first_history = collect(session, tmp_path, V2_ID, 2024)
    assert first["n_collected"] == 4 and first_history["n_collected"] == 4

    session.calls.clear()
    second, second_history = collect(session, tmp_path, V2_ID, 2024)
    assert second["n_collected"] == 0 and second["n_skipped"] == 4
    assert second_history["n_collected"] == 0 and second_history["n_skipped"] == 4
    assert not [c for c in session.calls if c[1] == "/notes/edits"]


def test_history_pass_stops_cleanly_on_quota_and_resumes(tmp_path):
    session = FakeSession(edit_quota=4)
    run, summary = collect(session, tmp_path, V2_ID, 2024)
    # Decided papers first: A needs 3 requests (submission + 2 reviews), B is cut short.
    assert run["n_collected"] == 4  # the notes of every forum are on disk
    assert summary["n_collected"] == 1
    assert summary["n_pending"] == 3
    assert summary["stopped_by"]["policy"] == "18;w=3600"
    assert load(tmp_path, 2024, "A")[1] is not None
    assert load(tmp_path, 2024, "B")[1] is None

    session.edit_quota = None  # next hour
    _, summary = collect(session, tmp_path, V2_ID, 2024)
    assert summary == {"n_collected": 3, "n_skipped": 1, "stopped_by": None, "n_pending": 0}


def test_report_works_without_history(session, tmp_path):
    run, _ = collect(session, tmp_path, V2_ID, 2024, history=False)
    by_year, _, reviews, _ = tables(tmp_path, {"2024": run})
    assert by_year.loc[2024, "papers_history_collected"] == 0
    assert by_year.loc[2024, "reviews_history_collected"] == 0
    # Timestamps come with the notes: the flag does not need the edit endpoint.
    assert by_year.loc[2024, "reviews_modified_after_release"] == 1
    assert reviews["creation_edit_readable"].isna().all()


def test_force_fetches_again(session, tmp_path):
    collect(session, tmp_path, V2_ID, 2024)
    run, summary = collect(session, tmp_path, V2_ID, 2024, force=True)
    assert run["n_collected"] == 4 and summary["n_collected"] == 4


def test_challenge_error_stops_the_collection(session, tmp_path):
    session.challenge = True
    with pytest.raises(OpenReviewError, match="ChallengeRequiredError"):
        collect(session, tmp_path, V2_ID, 2024)


def test_atomic_write_leaves_no_temporary_file(tmp_path):
    path = tmp_path / "a" / "x.json.gz"
    store.write_json(path, {"k": "é"})
    assert store.read_json(path) == {"k": "é"}
    assert [p.name for p in path.parent.iterdir()] == ["x.json.gz"]


# --------------------------------------------------------------------------- parsing and report
@pytest.mark.parametrize(
    "value, expected",
    [(8, 8), ("8: accept, good paper", 8), (" 3", 3), ("N/A", None), (None, None), (True, None)],
)
def test_parse_score(value, expected):
    assert parse.parse_score(value) == expected


def test_report_tables(session, tmp_path):
    runs = {
        "2024": collect(session, tmp_path, V2_ID, 2024)[0],
        "2023": collect(session, tmp_path, V1_ID, 2023)[0],
    }
    by_year, papers, reviews, openalex = tables(tmp_path, runs)

    assert by_year.loc[2024, "n_papers"] == 4
    assert by_year.loc[2024, "n_accepted"] == 1
    assert by_year.loc[2024, "n_withdrawn"] == 1
    assert by_year.loc[2024, "n_desk_rejected"] == 1
    assert by_year.loc[2024, "acceptance_rate"] == 0.5  # withdrawn / desk-rejected excluded
    assert by_year.loc[2024, "n_reviews"] == 4
    assert by_year.loc[2024, "reviews_modified_after_release"] == 1
    assert by_year.loc[2024, "reviews_not_modified_after_release"] == 3
    assert by_year.loc[2024, "share_reviews_initial_known"] == 0.75
    assert by_year.loc[2024, "reviewed_papers_all_initial_known"] == 1  # paper B only
    assert by_year.loc[2024, "reviews_history_forbidden"] == 1
    assert by_year.loc[2024, "reviews_creation_edit_readable"] == 0
    assert by_year.loc[2024, "reviews_with_readable_reviewer_edits"] == 1
    assert by_year.loc[2024, "accepted_with_camera_ready_revision"] == 1
    assert by_year.loc[2024, "not_accepted_with_camera_ready_revision"] == 0
    assert by_year.loc[2023, "n_rejected"] == 1
    assert by_year.loc[2023, "missing_keywords"] == 3
    assert by_year.loc[2023, "decided_without_meta_review"] == 0

    fields = report.review_fields_table(reviews)
    soundness = fields[(fields["year"] == 2024) & (fields["field"] == "soundness")]
    assert soundness["n_reviews"].item() == 2
    assert len(openalex) == 0
    assert "| year |" in report.to_markdown(report.by_year_table(papers, reviews))


# --------------------------------------------------------------------------- OpenAlex
def test_openalex_title_matching():
    candidates = [
        {"id": "https://openalex.org/W1", "title": "A Completely Different Paper", "referenced_works": ["x"]},
        {"id": "https://openalex.org/W2", "title": "Graph Networks: for Peer-Review!", "referenced_works": ["a", "b"]},
    ]
    work, score = best_match("Graph networks for peer review", candidates)
    assert work["id"].endswith("W2") and score == 1.0
    assert normalise_title("Graph Networks: for Peer-Review!") == "graph networks for peer review"

    result = {"query_title": "Graph networks for peer review", "candidates": candidates}
    assert match_row(result, 0.95) == {
        "matched": True, "match_score": 1.0, "openalex_id": "W2", "n_references": 2,
    }
    unmatched = match_row({"query_title": "Something else entirely", "candidates": candidates}, 0.95)
    assert not unmatched["matched"] and unmatched["n_references"] == 0


def test_openalex_never_requests_leaking_fields():
    select = set(load_config()["openalex"]["select"])
    assert select == {"id", "title", "publication_year", "referenced_works"}


# --------------------------------------------------------------------------- external initial scores
def test_external_scores_are_joined_by_forum_and_reviewer_key(tmp_path):
    path = tmp_path / "scores.json"
    # The real files contain the non-standard token Infinity.
    path.write_text(
        '[{"id": "A", "title": "t", "tracing_score": 0, "review": '
        '{"Kha2": {"rating": "3;5", "confidence": "4;4"}}},'
        ' {"id": "Z", "title": "t", "tracing_score": Infinity, "review": {}}]'
    )
    ext = external.load_iclr_insights(path)
    assert ext["A"]["reviews"]["Kha2"]["rating"] == (3, 5)
    assert ext["Z"]["reviews"] == {}

    review = {"signatures": ["ICLR.cc/2024/Conference/Submission1/Reviewer_Kha2"]}
    row = external.join_review(ext, "A", review)
    assert row["matched"] and row["ext_rating_initial"] == 3 and row["ext_rating_post"] == 5
    assert row["ext_any_score_changed"] is True

    other = {"signatures": ["ICLR.cc/2024/Conference/Submission1/Reviewer_zzzz"]}
    assert not external.join_review(ext, "A", other)["matched"]
    assert not external.join_review(ext, "missing", review)["paper_in_external"]
    assert external.parse_pair("n/a") == (None, None)


def test_latest_manifest_can_be_restricted_to_the_runs_that_cover_given_years(tmp_path):
    directory = store.manifest_dir(tmp_path)
    store.write_json(directory / "full_20261115_172210.json", {"years": {"2024": {}, "2025": {}}})
    store.write_json(directory / "full_20261118_230000.json", {"years": {"2026": {}}})
    assert store.latest_manifest(tmp_path, "full").name == "full_20261118_230000.json"
    assert store.latest_manifest(tmp_path, "full", [2024]).name == "full_20261115_172210.json"
    assert store.latest_manifest(tmp_path, "full", [2024, 2025]).name == "full_20261115_172210.json"
    assert store.latest_manifest(tmp_path, "full", [2026]).name == "full_20261118_230000.json"
    with pytest.raises(FileNotFoundError, match="covering"):
        store.latest_manifest(tmp_path, "full", [2025, 2026])
