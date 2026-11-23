"""Offline tests of the cleaning step, on a synthetic API v2 forum."""

import pytest

from src.clean import normalize
from src.utils.config import load_config
from src.utils.leakage import find_forbidden_fields

VENUE_ID = "ICLR.cc/2024/Conference"
INFO = {
    "api_version": "v2",
    "venue_id": VENUE_ID,
    "review_name": "Official_Review",
    "meta_review_name": "Meta_Review",
    "decision_name": "Decision",
    "rating_field": "rating",
    "confidence_field": "confidence",
    "withdrawn_venue_id": f"{VENUE_ID}/Withdrawn_Submission",
    "desk_rejected_venue_id": f"{VENUE_ID}/Desk_Rejected_Submission",
    "rejected_venue_id": f"{VENUE_ID}/Rejected_Submission",
}
SPLITS = {"train": [2024], "test": [2025], "validation": {"fraction": 0.15, "salt": "s"}}
# The 2024 external file uses the older field names.
FIELD_MAP = {"rating": "rating", "confidence": "confidence", "correctness": "soundness",
             "technical_novelty": "contribution", "presentation": "presentation"}
EXT = {
    "F1": {
        "tracing_score": 0,
        "reviews": {"Kha2": {"rating": (3, 6), "confidence": (4, 4), "correctness": (2, 3), "technical_novelty": (2, 2)}},
    }
}


def reply(reply_id, name, signature, content, created=100, modified=100, replyto="F1"):
    return {
        "id": reply_id,
        "forum": "F1",
        "replyto": replyto,
        "invitations": [f"{VENUE_ID}/Submission7/-/{name}"],
        "signatures": [f"{VENUE_ID}/Submission7/{signature}" if not signature.startswith("~") else signature],
        "tcdate": created,
        "tmdate": modified,
        "content": {k: {"value": v} for k, v in content.items()},
    }


REVIEW = {"summary": "S", "strengths": "+", "weaknesses": "-", "questions": "?", "rating": "6: marginally above",
          "confidence": 4, "soundness": "3 good", "presentation": "2 fair", "contribution": "2 fair"}
DOC = {
    "forum_id": "F1",
    "year": 2024,
    "number": 7,
    "submission": {
        "id": "F1",
        "invitations": [f"{VENUE_ID}/-/Submission", f"{VENUE_ID}/Submission7/-/Camera_Ready_Revision"],
        "signatures": [f"{VENUE_ID}/Submission7/Authors"],
        "content": {k: {"value": v} for k, v in {
            "title": " A title ", "abstract": "An abstract.", "keywords": ["graphs", " "], "primary_area": "area",
            "authors": ["Someone"], "authorids": ["~Someone1"], "venue": "ICLR 2024 poster", "venueid": VENUE_ID,
            "_bibtex": "@inproceedings{...}", "paperhash": "someone|a_title", "pdf": "/pdf/x.pdf",
        }.items()},
    },
    "replies": [
        reply("R1", "Official_Review", "Reviewer_Kha2", REVIEW, created=100, modified=900),
        reply("R2", "Official_Review", "Reviewer_zzzz", {**REVIEW, "rating": 5}),
        # The first author response (t=500) opens the second phase.
        reply("C1", "Official_Comment", "Authors", {"title": "Response", "comment": "We thank the reviewer."},
              created=500, modified=500, replyto="R1"),
        reply("C2", "Official_Comment", "Reviewer_Kha2", {"comment": "Thanks, I raise my score."},
              created=600, modified=600, replyto="C1"),
        reply("C3", "Official_Comment", "Area_Chair_abcd", {"comment": "Please discuss."}, created=600, modified=600),
        reply("C4", "Public_Comment", "~Some_Person1", {"comment": "Interesting."}, created=600, modified=600),
        reply("M1", "Meta_Review", "Area_Chair_abcd", {"metareview": "Accept."}, created=900, modified=900),
        reply("D1", "Decision", "Program_Chairs", {"decision": "Accept (poster)"}, created=950, modified=950),
    ],
}


@pytest.fixture(scope="module")
def forbidden():
    return load_config()["leakage"]["forbidden_fields"]


def test_paper_record_keeps_only_blind_inputs(forbidden):
    paper = normalize.paper_record(DOC)
    assert paper["title"] == "A title"
    assert paper["keywords"] == ["graphs"]
    assert paper["tldr"] is None
    assert find_forbidden_fields(paper.keys(), forbidden) == []
    assert not {"authors", "venue", "pdf", "paperhash"} & set(paper)


def test_initial_and_final_review_rows_are_separate(forbidden):
    initial, final = normalize.review_records(DOC, INFO, EXT, FIELD_MAP)
    first, second = initial
    # Pre-rebuttal scores from the external archive, with the 2024 field names mapped to ours.
    assert (first["rating_initial"], first["confidence_initial"]) == (3, 4)
    assert (first["soundness_initial"], first["contribution_initial"]) == (2, 2)
    assert first["presentation_initial"] is None  # not archived for 2024
    assert first["initial_scores_source"] == "iclr_insights"
    assert first["weaknesses"] == "-"
    # No external record for the second reviewer: no initial score, never the final one.
    assert second["rating_initial"] is None and second["initial_scores_source"] is None

    # `phase` is only used to select the rows; the model-input view drops it.
    assert find_forbidden_fields(first.keys(), forbidden) == ["phase"]
    assert (final[0]["rating_final"], final[0]["soundness_final"]) == (6, 3)
    assert final[0]["rating_ext_post"] == 6
    assert final[0]["any_score_changed"] is True
    assert final[1]["any_score_changed"] is None
    # Final-state columns are all forbidden as model inputs.
    leaked = set(find_forbidden_fields(final[0].keys(), forbidden))
    assert {"rating_final", "confidence_final", "tmdate", "any_score_changed"} <= leaked


def test_discussion_has_roles_but_no_identity_and_no_outcome():
    rows = normalize.discussion_records(DOC, INFO)
    assert [r["reply_id"] for r in rows] == ["C1", "C2", "C3", "C4"]
    assert [r["role"] for r in rows] == ["authors", "reviewer", "area_chair", "public"]
    assert rows[1]["reviewer_key"] == "Kha2" and rows[0]["reviewer_key"] is None
    assert all("signatures" not in r for r in rows)
    assert "Some_Person" not in str(rows)


def test_author_replies_are_aligned_on_the_review_they_answer():
    rows = {r["reply_id"]: r for r in normalize.discussion_records(DOC, INFO)}
    # Direct reply to a review, and a reply nested two levels below it.
    assert (rows["C1"]["target_review_id"], rows["C1"]["thread_root"]) == ("R1", "review")
    assert (rows["C2"]["target_review_id"], rows["C2"]["thread_root"]) == ("R1", "review")
    # General comments on the submission answer no particular review.
    assert (rows["C3"]["target_review_id"], rows["C3"]["thread_root"]) == (None, "submission")

    orphan = reply("C9", "Official_Comment", "Authors", {"comment": "x"}, replyto="deleted-note")
    doc = {**DOC, "replies": DOC["replies"] + [orphan]}
    rows = {r["reply_id"]: r for r in normalize.discussion_records(doc, INFO)}
    assert (rows["C9"]["target_review_id"], rows["C9"]["thread_root"]) == (None, "unknown")


def test_notes_are_split_at_the_first_author_response():
    # Author response at t=500: R1 (t=100) is before, a late review (t=800) is after.
    late_review = reply("R3", "Official_Review", "Reviewer_late", REVIEW, created=800)
    early_comment = reply("C0", "Official_Comment", "Reviewer_Kha2", {"comment": "early"}, created=200)
    doc = {**DOC, "replies": DOC["replies"] + [late_review, early_comment]}

    assert normalize.first_author_response(doc, INFO) == 500
    reviews, _ = normalize.review_records(doc, INFO, EXT, FIELD_MAP)
    assert {r["review_id"]: r["phase"] for r in reviews} == {
        "R1": normalize.PHASE_BEFORE, "R2": normalize.PHASE_BEFORE, "R3": normalize.PHASE_AFTER,
    }
    phases = {r["reply_id"]: r["phase"] for r in normalize.discussion_records(doc, INFO)}
    assert phases["C0"] == normalize.PHASE_BEFORE
    assert phases["C1"] == normalize.PHASE_AFTER  # the author response opens the second phase
    assert phases["C2"] == normalize.PHASE_AFTER

    # A forum without any author response is entirely in the first phase.
    silent = {**DOC, "replies": [r for r in DOC["replies"] if r["id"] != "C1"]}
    assert normalize.first_author_response(silent, INFO) is None
    assert {r["phase"] for r in normalize.discussion_records(silent, INFO)} == {normalize.PHASE_BEFORE}


@pytest.mark.parametrize(
    "decision, kind, label",
    [
        ("Accept (oral)", "oral", 1),
        ("Accept (Spotlight)", "spotlight", 1),
        ("Accept (poster)", "poster", 1),
        ("Accept", "accept", 1),
        ("Reject", "reject", 0),
        (None, None, None),
    ],
)
def test_decision_is_normalised_to_a_binary_label(decision, kind, label):
    assert normalize.decision_type(decision) == kind
    assert normalize.label_from_decision(decision) == label


def with_venueid(doc, venueid, replies=None):
    content = {**doc["submission"]["content"], "venueid": {"value": venueid}}
    return {**doc, "submission": {**doc["submission"], "content": content},
            "replies": doc["replies"] if replies is None else replies}


def outcome(doc):
    initial, _ = normalize.review_records(doc, INFO, EXT, FIELD_MAP)
    return normalize.outcome_record(doc, INFO, SPLITS, initial)


def test_outcome_record():
    result = outcome(DOC)
    assert result["status"] == "accepted" and result["label"] == 1
    assert result["decision_type"] == "poster"
    assert result["meta_review"] == "Accept."
    assert result["camera_ready_revision"] is True
    assert result["has_author_response"] is True
    assert (result["n_reviews"], result["n_reviews_before_with_initial_scores"]) == (2, 1)
    assert result["eligible"] is False  # one review has no initial rating
    assert result["split"] in ("train", "val")

    # Every review posted before the author response has an initial rating: eligible.
    one_review = {**DOC, "replies": [r for r in DOC["replies"] if r["id"] != "R2"]}
    assert outcome(one_review)["eligible"] is True


def test_withdrawn_papers_have_two_label_variants():
    withdrawn_id = f"{VENUE_ID}/Withdrawn_Submission"
    reviews_only = [r for r in DOC["replies"] if r["id"] == "R1"]

    # Withdrawn before any decision: no label, or a rejection in the second variant.
    before = outcome(with_venueid(DOC, withdrawn_id, reviews_only))
    assert before["withdrawn"] and before["withdrawn_before_decision"]
    assert before["label"] is None and before["label_withdrawn_as_reject"] == 0
    assert before["eligible"] is False and before["eligible_withdrawn_as_reject"] is True

    # Withdrawn after the decision: the decision note gives the label in both variants.
    after = outcome(with_venueid(DOC, withdrawn_id, [r for r in DOC["replies"] if r["id"] != "R2"]))
    assert after["withdrawn"] and not after["withdrawn_before_decision"]
    assert after["label"] == 1 and after["label_withdrawn_as_reject"] == 1

    # Withdrawn without any review: unusable in both variants.
    empty = outcome(with_venueid(DOC, withdrawn_id, []))
    assert empty["eligible"] is False and empty["eligible_withdrawn_as_reject"] is False


def test_role_of():
    assert normalize.role_of({"signatures": [f"{VENUE_ID}/Program_Chairs"]}) == "program_chairs"
    assert normalize.role_of({"signatures": [f"{VENUE_ID}/Submission7/Senior_Area_Chair_ab12"]}) == "senior_area_chair"
    assert normalize.role_of({"signatures": []}) == "other"


# --------------------------------------------------------------------------- year reverted by the conference
def test_a_reverted_year_takes_its_initial_scores_from_the_current_state():
    """No external archive: a review last modified by a conference-wide edit, or never
    modified, keeps its current scores as initial ones; a review modified at another
    time has none. The overall rating is brought to the common scale, level by level."""
    from src.collect import report

    hour = 3_600_000
    windows = report.event_windows({"release": [["1970-01-01 10:00", "1970-01-01 12:00"]],
                                    "revert": [["1970-01-02 00:00", "1970-01-02 03:00"]]})
    assert windows["release"] == [(10 * hour, 12 * hour)]
    assert report.last_modification(hour, hour + 30_000, windows) == "never_modified"
    assert report.last_modification(hour, 11 * hour, windows) == "release"
    assert report.last_modification(hour, 25 * hour, windows) == "revert"
    assert report.last_modification(hour, 15 * hour, windows) == "other"

    levels = {0: 1, 2: 3, 4: 5, 6: 6, 8: 8, 10: 10}
    scores = {"confidence": 4, "soundness": 3, "presentation": 2, "contribution": 2}
    doc = {**DOC, "year": 2026, "replies": [
        reply("R1", "Official_Review", "Reviewer_aaaa", {**REVIEW, **scores, "rating": 4}, created=hour, modified=11 * hour),
        reply("R2", "Official_Review", "Reviewer_bbbb", {**REVIEW, **scores, "rating": 0}, created=hour, modified=25 * hour),
        reply("R3", "Official_Review", "Reviewer_cccc", {**REVIEW, **scores, "rating": 8}, created=hour, modified=15 * hour),
        reply("R4", "Official_Review", "Reviewer_dddd", {**REVIEW, **scores, "rating": 10}, created=hour, modified=hour),
    ]}
    initial, final = normalize.review_records(doc, INFO, None, FIELD_MAP, windows, levels)
    assert [row["rating_initial"] for row in initial] == [5, 1, None, 10]
    assert [row["initial_scores_source"] for row in initial] == ["current_state", "current_state", None, "current_state"]
    assert initial[0]["presentation_initial"] == 2 and initial[2]["confidence_initial"] is None
    assert [row["rating_final"] for row in final] == [5, 1, 8, 10]  # the final table uses the common scale too
    assert all(row["any_score_changed"] is None and row["rating_ext_post"] is None for row in final)
    # the paper is not usable in setting A: one of its reviews has no initial rating
    splits = {**SPLITS, "holdout": [2026]}
    outcome = normalize.outcome_record(doc, INFO, splits, initial)
    assert outcome["split"] == "holdout" and outcome["n_reviews_before_with_initial_scores"] == 3 and not outcome["eligible"]
    # a value outside the configured scale is refused
    odd = {**doc, "replies": [reply("R5", "Official_Review", "Reviewer_eeee", {**REVIEW, **scores, "rating": 5}, created=hour, modified=hour)]}
    with pytest.raises(ValueError, match="not a level"):
        normalize.review_records(odd, INFO, None, FIELD_MAP, windows, levels)
