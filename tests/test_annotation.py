"""Phase 4: annotation sample, files given to the annotators, agreement and LLM scores.

The annotations used here are built inside the tests and written to temporary
directories only: no reference label is ever produced for the real sample.
"""

import pandas as pd
import pytest

from src.eval import annotation
from src.llm.units import build_units

ASPECTS = annotation.LABEL_VALUES["aspect"]
SEVERITIES = annotation.LABEL_VALUES["severity"]


def fake_critiques(per_stratum: dict[tuple[int, str, str], int]) -> pd.DataFrame:
    rows = []
    for (year, aspect, severity), n in per_stratum.items():
        for i in range(n):
            review = f"r{year}{aspect[:3]}{severity[:3]}{i // 2}"
            rows.append({"critique_id": f"{review}:{i % 2 + 1}", "review_id": review, "forum_id": f"f{review}",
                         "year": year, "critique_index": i % 2 + 1, "units": [i % 2 + 1], "fields": ["weaknesses"],
                         "text": f"Critique {i} about {aspect}.", "aspect": aspect, "severity": severity,
                         "polarity": "negative", "target": "general", "actionable": True})
    return pd.DataFrame(rows)


POOL = fake_critiques({(2024, "soundness", "major"): 400, (2024, "soundness", "minor"): 300,
                       (2025, "clarity", "minor"): 280, (2025, "novelty", "blocking"): 3,
                       (2025, "other", "minor"): 12})


# --------------------------------------------------------------------------- sampling
def test_unlabelled_critiques_and_excluded_reviews_are_not_in_the_population():
    critiques = POOL.copy()
    critiques.loc[0, "aspect"] = None  # typing failed for this critique
    excluded = {critiques.loc[5, "review_id"]}
    pool = annotation.population(critiques, excluded)
    assert critiques.loc[0, "critique_id"] not in set(pool["critique_id"])
    assert not set(pool["review_id"]) & excluded
    assert list(pool["critique_id"]) == sorted(pool["critique_id"])


def test_every_stratum_gets_the_floor_and_the_rest_follows_the_sizes():
    sizes = pd.Series({"big": 400, "medium": 300, "small": 12, "tiny": 3})
    counts = annotation.allocate(sizes, 100, 5)
    assert counts.sum() == 100
    assert counts["tiny"] == 3 and counts["small"] >= 5  # a stratum smaller than the floor is taken whole
    assert counts["big"] > counts["medium"] > counts["small"]
    assert (counts <= sizes).all()
    assert annotation.allocate(sizes, 18, 5).to_dict() == {"big": 5, "medium": 5, "small": 5, "tiny": 3}
    with pytest.raises(ValueError, match="floor"):
        annotation.allocate(sizes, 10, 5)
    with pytest.raises(ValueError, match="population"):
        annotation.allocate(sizes, 1000, 5)


def test_the_sample_is_reproducible_stratified_and_weighted():
    pool = annotation.population(POOL, set())
    ids = annotation.draw_sample(pool, 100, 5, seed=0)
    assert ids == annotation.draw_sample(pool, 100, 5, seed=0)
    assert ids != annotation.draw_sample(pool, 100, 5, seed=1)
    assert len(ids) == len(set(ids)) == 100

    key = annotation.sample_key(pool, ids)
    assert list(key["item_id"][:2]) == ["item_001", "item_002"] and list(key["critique_id"]) == ids
    per_stratum = key.groupby(["year", "llm_aspect", "llm_severity"]).size()
    assert per_stratum[(2025, "novelty", "blocking")] == 3 and per_stratum[(2025, "other", "minor")] >= 5
    # the weights bring the sample back to the population
    assert key["weight"].sum() == pytest.approx(len(pool), rel=1e-3)
    assert set(key["llm_actionable"]) == {"true"}
    # item numbers do not follow the strata
    assert list(key["llm_aspect"]) != sorted(key["llm_aspect"])


def test_a_frozen_sample_is_never_drawn_again(tmp_path):
    path = tmp_path / "sample.txt"
    annotation.write_sample_file(path, ["r1:1", "r2:3"], ["two critiques"])
    assert annotation.read_sample_file(path) == ["r1:1", "r2:3"]
    with pytest.raises(FileExistsError):
        annotation.write_sample_file(path, ["r9:1"], ["another draw"])
    with pytest.raises(ValueError, match="not in the population"):
        annotation.sample_key(annotation.population(POOL, set()), ["unknown:1"])


# --------------------------------------------------------------------------- files to annotate
REVIEW = {"strengths": "The idea is new. It is well motivated.",
          "weaknesses": "No baseline is given. The proofs are unclear.\nFigure 2 is too small.",
          "questions": "Why this dataset?"}


def test_the_context_marks_the_critique_inside_the_review():
    units = build_units(REVIEW)
    context = annotation.critique_context(units, [3, 4], window=20)
    assert context == ("[strengths]\nThe idea is new. It is well motivated.\n"
                       "[weaknesses]\n>>> No baseline is given. The proofs are unclear. <<<\nFigure 2 is too small.\n"
                       "[questions]\nWhy this dataset?")
    short = annotation.critique_context(units, [5], window=1)
    assert short == "[...]\n[weaknesses]\nThe proofs are unclear.\n>>> Figure 2 is too small. <<<\n[questions]\nWhy this dataset?"
    with pytest.raises(ValueError):
        annotation.critique_context(units, [99], window=1)


def annotator_table() -> tuple[pd.DataFrame, pd.DataFrame]:
    pool = annotation.population(POOL, set())
    key = annotation.sample_key(pool, annotation.draw_sample(pool, 60, 5, seed=0))
    units = {rid: build_units({"weaknesses": "First point of the review.\nSecond point of the review."})
             for rid in key["review_id"]}
    return key, annotation.annotation_table(key, units, window=3)


def test_the_files_to_annotate_hold_no_label_of_the_llm():
    key, table = annotator_table()
    assert list(table.columns) == list(annotation.ANNOTATOR_COLUMNS)
    assert (table[[*annotation.LABELS, "comment"]] == "").all().all()
    assert not [c for c in table.columns if c.startswith("llm_") or c in ("weight", "year", "forum_id", "review_id")]
    assert list(table["item_id"]) == list(key["item_id"])
    first, second = (annotation.annotator_order(len(table), 0, index) for index in (0, 1))
    assert sorted(first) == sorted(second) == list(range(len(table))) and list(first) != list(second)


def test_a_file_with_annotations_is_never_overwritten(tmp_path):
    _, table = annotator_table()
    path = tmp_path / "to_annotate_A.csv"
    assert annotation.write_annotator_file(path, table) and not annotation.has_annotations(path)
    assert annotation.write_annotator_file(path, table)  # still empty: written again
    filled = annotation.read_csv(path)
    filled.loc[0, "aspect"] = "clarity"
    filled.to_csv(path, index=False, encoding=annotation.ENCODING)
    assert annotation.has_annotations(path) and not annotation.write_annotator_file(path, table)
    assert annotation.read_csv(path).loc[0, "aspect"] == "clarity"


# --------------------------------------------------------------------------- annotations
def fill(table: pd.DataFrame, labels: dict[str, list[str]]) -> pd.DataFrame:
    filled = table.copy()
    for label, values in labels.items():
        filled[label] = values
    return filled


ITEMS = pd.DataFrame({"item_id": ["item_001", "item_002", "item_003", "item_004"],
                      "critique": ["c1", "c2", "c3", "c4"], "context": ["x1", "x2", "x3", "x4"]})
A = {"aspect": ["clarity", "clarity", "novelty", "soundness"], "severity": ["minor", "major", "major", "minor"],
     "polarity": ["negative"] * 4, "target": ["general"] * 4, "actionable": ["TRUE", "true", "False", " true "]}
B = {"aspect": ["clarity", "soundness", "novelty", "soundness"], "severity": ["minor", "major", "major", "minor"],
     "polarity": ["negative"] * 4, "target": ["general"] * 4, "actionable": ["true", "true", "false", "true"]}
KEY = pd.DataFrame({"item_id": ITEMS["item_id"], "llm_aspect": ["clarity", "clarity", "soundness", "soundness"],
                    "llm_severity": ["minor", "major", "major", "major"], "llm_polarity": ["negative"] * 4,
                    "llm_target": ["general"] * 4, "llm_actionable": ["true", "true", "false", "false"],
                    "weight": [1.0, 1.0, 10.0, 1.0]})


def write(tmp_path, name: str, labels: dict[str, list[str]]):
    path = tmp_path / f"to_annotate_{name}.csv"
    fill(ITEMS, labels).to_csv(path, index=False, encoding=annotation.ENCODING)
    return path


def test_annotations_are_read_normalised_and_checked(tmp_path):
    first = annotation.read_annotations(write(tmp_path, "A", A), list(ITEMS["item_id"]))
    assert list(first["actionable"]) == ["true", "true", "false", "true"]  # spreadsheet spellings accepted
    with pytest.raises(ValueError, match="aspect: 1 empty cells.*severity: 1 values outside"):
        annotation.read_annotations(write(tmp_path, "C", {**A, "aspect": ["", "clarity", "novelty", "soundness"],
                                                          "severity": ["minor", "huge", "major", "minor"]}))
    with pytest.raises(ValueError, match="1 items of the sample are missing"):
        annotation.read_annotations(write(tmp_path, "A", A), [*ITEMS["item_id"], "item_005"])


def test_agreement_disagreements_and_consensus(tmp_path):
    ids = list(ITEMS["item_id"])
    first = annotation.read_annotations(write(tmp_path, "A", A), ids)
    second = annotation.read_annotations(write(tmp_path, "B", B), ids)

    agreement = annotation.agreement_table(first, second).set_index("label")
    assert agreement.loc["aspect", "agreement"] == 0.75 and agreement.loc["severity", "cohen_kappa"] == 1.0
    assert 0 < agreement.loc["aspect", "cohen_kappa"] < 1

    disagreements = annotation.disagreement_table(first, second, ("A", "B"), ITEMS)
    assert disagreements[["item_id", "label", "annotator_A", "annotator_B", "consensus", "critique"]].values.tolist() \
        == [["item_002", "aspect", "clarity", "soundness", "", "c2"]]

    # nothing is settled by the code: the open disagreement has no consensus
    consensus = annotation.consensus_labels(first, second)
    assert consensus.at["item_002", "aspect"] is None and consensus.at["item_001", "aspect"] == "clarity"

    path = tmp_path / "disagreements.csv"
    disagreements.to_csv(path, index=False, encoding=annotation.ENCODING)
    assert annotation.read_resolutions(path).empty
    disagreements["consensus"] = [" Soundness "]
    disagreements.to_csv(path, index=False, encoding=annotation.ENCODING)
    settled = annotation.consensus_labels(first, second, annotation.read_resolutions(path))
    assert settled.at["item_002", "aspect"] == "soundness" and settled.notna().all().all()

    disagreements["consensus"] = ["wrong"]
    disagreements.to_csv(path, index=False, encoding=annotation.ENCODING)
    with pytest.raises(ValueError, match="outside the allowed"):
        annotation.read_resolutions(path)
    agreed = pd.DataFrame({"item_id": ["item_001"], "label": ["aspect"], "consensus": ["novelty"]})
    with pytest.raises(ValueError, match="nothing to settle"):
        annotation.consensus_labels(first, second, agreed)


def test_llm_scores_against_the_consensus(tmp_path):
    ids = list(ITEMS["item_id"])
    first = annotation.read_annotations(write(tmp_path, "A", A), ids)
    second = annotation.read_annotations(write(tmp_path, "B", B), ids)
    scores = annotation.llm_scores(annotation.consensus_labels(first, second), KEY)

    summary = scores["summary"].set_index("label")
    # aspect: item_002 has no consensus; of the three others the LLM is right on two
    assert summary.loc["aspect", "items"] == 3 and summary.loc["aspect", "items_without_consensus"] == 1
    assert summary.loc["aspect", "accuracy_sample"] == round(2 / 3, 4)
    assert summary.loc["aspect", "accuracy_corpus"] == round(2 / 12, 4)  # the wrong item weighs 10
    assert summary.loc["polarity", "accuracy_sample"] == 1.0 and summary.loc["polarity", "macro_f1_sample"] == 1.0
    assert summary.loc["severity", "accuracy_sample"] == 0.75

    categories = scores["categories"].set_index(["label", "category", "weighting"])
    assert categories.loc[("aspect", "soundness", "sample"), ["precision", "recall", "support"]].tolist() == [0.5, 1.0, 1.0]
    assert categories.loc[("aspect", "novelty", "sample"), "recall"] == 0.0
    assert categories.loc[("actionable", "true", "sample"), "recall"] == round(2 / 3, 4)

    confusion = scores["confusion_aspect"].set_index("consensus \\ llm")
    assert confusion.loc["novelty", "soundness"] == 1 and confusion.loc["clarity", "clarity"] == 1
    assert confusion.to_numpy().sum() == 3


# --------------------------------------------------------------------------- guide
def test_the_guide_defines_every_value_with_the_words_of_the_prompt():
    import yaml

    from src.utils.config import REPO_ROOT

    guide = (REPO_ROOT / "data" / "annotation" / "GUIDE.md").read_text(encoding="utf-8")
    for label, allowed in annotation.LABEL_VALUES.items():
        assert f"`{label}`" in guide
        for value in allowed:
            assert f"| `{value}` |" in guide, f"{label}: {value} is not defined in the guide"
    # the annotators and the LLM are given the same definitions
    prompt = yaml.safe_load((REPO_ROOT / "configs" / "prompts" / "type_v1.yaml").read_text(encoding="utf-8"))["system"]
    for line in prompt.splitlines():
        if line.startswith("- ") and ": " in line:
            value, definition = line[2:].split(": ", 1)
            assert f"| `{value}` | {definition} |" in guide, f"definition of {value} differs from the prompt"
