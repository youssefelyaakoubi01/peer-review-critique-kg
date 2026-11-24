"""Text of the paper (phase 11): every number comes from a result file through a macro."""

import re

import pytest

from src.eval import numbers
from src.eval.sources import Sources
from src.paper import references, related
from src.utils.config import REPO_ROOT, load_config

PAPER = REPO_ROOT / "paper"
SECTIONS = sorted((PAPER / "sections").glob("*.tex"))
GENERATED = PAPER / "generated" / "numbers.tex"
YEARS = {"2024", "2025", "2026"}   # conference years may be written in full
# The public archive (scripts/12_release.py, recognised by its ARCHIVE.md) does not hold the manuscript.
needs_manuscript = pytest.mark.skipif((REPO_ROOT / "ARCHIVE.md").is_file() and not (PAPER / "main.tex").is_file(),
                                      reason="the manuscript is not part of the public archive")


@pytest.fixture(scope="module")
def macros():
    cfg = load_config()
    return numbers.build(Sources(cfg["paths"]["tables"], REPO_ROOT), cfg)


def prose(text: str) -> str:
    """Text of a section without what is not prose: comments, references, file names and lengths."""
    text = re.sub(r"(?<!\\)%.*", "", text)
    text = re.sub(r"\\(?:label|ref|eqref|input|cite|begin|end)\*?(?:\[[^\]]*\])?\{[^}]*\}", "", text)
    text = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}", "", text)
    return re.sub(r"\d*\.?\d+\s*(?:em|pt|mm|cm|\\linewidth|\\textwidth)\b", "", text)


def test_formats():
    assert numbers.count(8655) == r"8\,655" and numbers.plain(0.85806) == "0.858"
    assert numbers.signed(-0.0152) == r"\ensuremath{-}0.0152" and numbers.signed(0.00001) == "0.0000"
    assert numbers.percent(0.425) == r"42.5\,\%"
    assert numbers.difference(0.0272, 0.0222, 0.0324) == r"\ensuremath{+}0.0272 [\ensuremath{+}0.0222, \ensuremath{+}0.0324]"
    assert numbers.camel("scores_rating_lr", "hgt+scores") == "ScoresRatingLrHgtScores"


def test_a_macro_names_the_file_its_value_is_read_in(tmp_path):
    import pandas as pd
    tables = tmp_path / "results" / "tables"
    tables.mkdir(parents=True)
    pd.DataFrame({"model": ["a"], "auc": [0.8]}).to_csv(tables / "t.csv", index=False)
    pd.DataFrame({"model": ["a"], "auc": [0.7]}).to_csv(tables / "u.csv", index=False)
    n = numbers.Numbers(Sources(tables, tmp_path))
    n.add("First", numbers.plain(n.s.value("t.csv", "auc", model="a")), "t.csv")
    assert n.macros["First"] == ("0.800", ["results/tables/t.csv"])
    with pytest.raises(ValueError, match="does not name"):   # read in u.csv, said to come from t.csv
        n.add("Second", numbers.plain(n.s.value("u.csv", "auc", model="a")), "t.csv")
    with pytest.raises(ValueError, match="twice"):
        n.add("First", "1", "t.csv")
    with pytest.raises(ValueError, match="only holds letters"):
        n.add("Auc2025", "1", "t.csv")
    with pytest.raises(ValueError, match="no source"):
        n.add("Third", "1")


def test_the_macro_file_is_the_one_the_result_tables_give(macros):
    assert GENERATED.read_text(encoding="utf-8") == numbers.render(macros), \
        "paper/generated/numbers.tex is out of date: run scripts/11_paper.py"


def test_every_macro_names_an_existing_source(macros):
    for name, (_, sources) in macros.items():
        assert sources, name
        for source in sources:
            assert (REPO_ROOT / source).is_file(), f"{name}: {source}"


@pytest.mark.parametrize("path", SECTIONS, ids=lambda path: path.name)
def test_no_result_is_typed_by_hand_in_a_section(path):
    """A decimal number, a percentage or an integer of three digits or more in the text of
    a section must be a macro of paper/generated/numbers.tex. Conference years excepted."""
    text = prose(path.read_text(encoding="utf-8"))
    found = [number for number in re.findall(r"(?<![A-Za-z\\])\d+(?:[.,]\d+)*(?:\s*(?:\\,)?\\%)?", text)
             if number not in YEARS and (len(re.sub(r"\D", "", number)) >= 3 or "." in number or "%" in number)]
    assert not found, f"{path.name}: numbers typed by hand: {found}"


@pytest.mark.parametrize("path", SECTIONS, ids=lambda path: path.name)
def test_a_macro_is_not_followed_by_a_space(path, macros):
    """TeX swallows the space after a macro: it must be written \\Name{} before a word."""
    text = re.sub(r"(?<!\\)%.*", "", path.read_text(encoding="utf-8"))
    swallowed = [name for name in re.findall(r"\\([A-Za-z]+)(?=[ \t]+[^\s\\$&])", text) if name in macros]
    assert not swallowed, f"{path.name}: write {{}} after {sorted(set(swallowed))}"


@needs_manuscript
def test_every_file_of_the_paper_exists():
    figures = REPO_ROOT / "results" / "figures"
    for path in [PAPER / "main.tex", *SECTIONS]:
        text = re.sub(r"(?<!\\)%.*", "", path.read_text(encoding="utf-8"))
        for name in re.findall(r"\\input\{([^}]+)\}", text):
            assert (PAPER / name).with_suffix(".tex").is_file(), f"{path.name}: \\input{{{name}}}"
        for name in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text):
            assert (figures / name).with_suffix(".pdf").is_file(), f"{path.name}: figure {name}"


def test_every_citation_is_in_the_reference_file():
    """No reference is typed from memory: a cited key must be an entry of paper/references.bib."""
    cited = set()
    for path in SECTIONS:
        for keys in re.findall(r"\\cite\{([^}]+)\}", re.sub(r"(?<!\\)%.*", "", path.read_text(encoding="utf-8"))):
            cited |= {key.strip() for key in keys.split(",")}
    bib = PAPER / "references.bib"
    known = set(re.findall(r"@\w+\{([^,\s]+),", bib.read_text(encoding="utf-8"))) if bib.is_file() else set()
    assert cited <= known, f"cited but not in paper/references.bib: {sorted(cited - known)}"


# ---------------------------------------------------------------- references (no network in the tests)


def stored_references() -> dict:
    import json
    return json.loads((PAPER / "references.json").read_text(encoding="utf-8"))


def declared_references() -> dict:
    import yaml
    return yaml.safe_load((PAPER / "references.yaml").read_text(encoding="utf-8"))


def body_keys() -> list[str]:
    main = re.sub(r"(?<!\\)%.*", "", (PAPER / "main.tex").read_text(encoding="utf-8"))
    names = re.findall(r"\\input\{(sections/[^}]+)\}", main)
    return references.cited_keys([(PAPER / f"{name}.tex").read_text(encoding="utf-8") for name in names])


def test_every_stored_reference_is_the_declared_record():
    """paper/references.json holds exactly the declared references, each with the identifier
    and the title that were declared: a record fetched for another identifier is refused."""
    declared, stored = declared_references(), stored_references()
    assert set(stored) == set(declared), "run scripts/11c_references.py"
    for key, entry in declared.items():
        references.check(key, entry, stored[key])
        assert stored[key]["source"] in ("crossref", "arxiv") and stored[key]["doi"]


def test_a_record_with_another_title_is_refused():
    record = {"doi": "10.1/x", "title": "Another paper", "authors": [{"family": "A", "given": "B"}], "year": 2020}
    with pytest.raises(ValueError, match="expected a title"):
        references.check("key", {"doi": "10.1/x", "title": "The expected paper"}, record)
    with pytest.raises(ValueError, match="not the one"):
        references.check("key", {"doi": "10.1/y", "title": "Another paper"}, record)


def test_vancouver_entries():
    journal = {"source": "crossref", "type": "journal-article", "doi": "10.1/j", "title": "A title", "year": 2020, "venue": "A Journal",
               "series": "", "volume": "4", "issue": "2", "pages": "10-20", "publisher": "",
               "authors": [{"family": "Doe", "given": "Jane Mary"}, {"family": "Roe", "given": "Jean-Paul"}]}
    assert references.vancouver(journal).startswith("Doe JM, Roe JP. A title. A Journal. 2020;4(2):10-20. doi: ")
    many = journal | {"authors": [{"family": f"A{letter}", "given": "X"} for letter in "bcdefgh"]}
    assert references.vancouver(many).startswith("Ab X, Ac X, Ad X, Ae X, Af X, Ag X, et al. A title.")
    preprint = journal | {"source": "arxiv", "type": "preprint", "arxiv": "0000.00000", "title": "Is it? 50% & more"}
    assert "Is it? 50\\% \\& more. arXiv:0000.00000 [Preprint]. 2020." in references.vancouver(preprint)
    chapter = journal | {"type": "book-chapter", "venue": "A Book", "series": "A Series"}
    assert "In: A Book. A Series; 2020. p. 10-20." in references.vancouver(chapter)


@needs_manuscript
def test_the_reference_list_is_the_one_the_records_give():
    """Cited keys only, in the order of first citation, every one verified."""
    generated = (PAPER / "generated" / "references.tex").read_text(encoding="utf-8")
    assert generated == references.thebibliography(body_keys(), stored_references()), \
        "paper/generated/references.tex is out of date: run scripts/11_paper.py"
    assert (PAPER / "references.bib").read_text(encoding="utf-8") == references.bibtex(stored_references())
    with pytest.raises(ValueError, match="not verified"):
        references.thebibliography(["unknown"], stored_references())


def test_citation_order():
    assert references.cited_keys(["a \\cite{b,a} % \\cite{z}\n \\cite{c}", "\\cite{a, d}"]) == ["b", "a", "c", "d"]


# ---------------------------------------------------------------- comparison table of the related work


def test_the_comparison_table_is_the_one_the_file_gives():
    """Every cell of a cited study has a supporting passage or reads "not stated"; the table is generated."""
    spec = related.load(PAPER / "related_studies.yaml")
    assert not related.problems(spec)
    generated = (PAPER / "generated" / "related_studies.tex").read_text(encoding="utf-8")
    assert generated == related.render(spec, stored_references()), "run scripts/11_paper.py"


def test_the_supporting_passages_are_in_the_papers():
    """Checked against the extracted full texts, which are not versioned (skipped without them)."""
    fulltext = PAPER / "refs" / "fulltext"
    spec = related.load(PAPER / "related_studies.yaml")
    if not any((fulltext / f"{key}.txt").is_file() for key in spec["studies"]):
        pytest.skip("the full texts of the compared studies are not on this machine")
    missing, checked = related.check_quotes(spec, fulltext)
    assert checked and not missing, missing


def test_a_passage_that_is_not_in_the_paper_is_reported(tmp_path):
    (tmp_path / "a.txt").write_text("=== page 01 ===\nThe data are split\n   at random.\n=== page 02 ===\nNothing else.\n", encoding="utf-8")
    spec = {"studies": {"a": {"split": {"value": "random", "quotes": [{"text": "The data are split at random.", "page": 1}]},
                              "data": {"value": "x", "quotes": [{"text": "split by year", "page": 1}]}}}}
    missing, checked = related.check_quotes(spec, tmp_path)
    assert checked == 2 and len(missing) == 1 and missing[0].startswith("a.data")
    spec["columns"] = {"split": "Split", "target": "Target"}
    assert related.problems(spec) == ["a.target: no value"]
