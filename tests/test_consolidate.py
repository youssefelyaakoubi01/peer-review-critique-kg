"""Consolidation of the results (phase 10): sourced values, LaTeX tables, summary, reproduction script."""

import os
import re
import subprocess

import pandas as pd
import pytest

from src.eval import latex, paper, summary
from src.eval.sources import Sources, excludes_zero, verdict
from src.utils.config import REPO_ROOT, load_config

SCRIPT = REPO_ROOT / "scripts" / "reproduce_all.sh"


@pytest.fixture
def sources(tmp_path):
    tables = tmp_path / "results" / "tables"
    tables.mkdir(parents=True)
    pd.DataFrame({"model": ["a", "a", "b"], "subset": ["all", "borderline", "all"], "auc": [0.8, 0.7, 0.6],
                  "aspect": ["novelty", None, None]}).to_csv(tables / "t.csv", index=False)
    return Sources(tables, tmp_path)


def test_a_value_is_the_cell_of_exactly_one_row(sources):
    assert sources.value("t.csv", "auc", model="a", subset="borderline") == 0.7
    assert sources.value("t.csv", "auc", model="a", aspect=None) == 0.7          # None: the missing value
    with pytest.raises(LookupError, match="2 rows"):
        sources.value("t.csv", "auc", model="a")
    with pytest.raises(LookupError, match="0 rows"):
        sources.value("t.csv", "auc", model="c")
    with pytest.raises(KeyError):
        sources.value("t.csv", "f1", model="b")
    with pytest.raises(KeyError):
        sources.rows("t.csv", seed=0)
    with pytest.raises(FileNotFoundError):
        sources.table("absent.csv")


def test_the_files_read_are_remembered_with_their_path(sources):
    sources.value("t.csv", "auc", model="b")
    assert sources.path("t.csv") == "results/tables/t.csv"
    assert sources.take_used() == ["results/tables/t.csv"]
    assert sources.take_used() == []


def test_verdict_follows_the_confidence_interval():
    assert verdict(-0.03, -0.01) == "significant" and verdict(0.01, 0.03) == "significant"
    assert verdict(-0.01, 0.01) == "not significant" and verdict(0.0, 0.02) == "not significant"
    assert not excludes_zero(-0.003, 0.0005)
    # a test that does not reject although the interval excludes zero is said so
    assert verdict(-0.004, -0.001, p_value=0.39) == "interval excludes zero, test does not reject"
    assert verdict(-0.004, -0.001, p_value=0.001) == "significant" and verdict(-0.004, 0.001, p_value=0.001) == "not significant"


def test_a_sentence_that_the_tables_do_not_support_stops_the_summary():
    summary.expect(True, "holds")
    with pytest.raises(AssertionError, match="no longer support"):
        summary.expect(False, "every GNN is below the baseline")


def test_latex_cells():
    assert latex.escape("hgt+scores_50% & co") == r"hgt+scores\_50\% \& co"
    assert latex.number(0.87331) == "$0.873$" and latex.signed(0.0123, 4) == "$+0.0123$" and latex.signed(-0.02, 2) == "$-0.02$"
    assert latex.count(8655) == r"$8\,655$" and latex.percent(0.2166) == r"$21.7\,\%$"
    assert latex.interval(-0.0033, 0.0005, 4, sign=True) == r"$[-0.0033,\,+0.0005]$"
    assert latex.number(float("nan")) == latex.MISSING and latex.interval(float("nan"), 1.0) == latex.MISSING
    assert latex.bold("$-2.0$") == r"$\mathbf{-2.0}$" and latex.bold("text") == r"\textbf{text}"


def column_count(text: str) -> int:
    """Number of columns of the tabular of a table: l, c, r and p{...} columns, whatever their >{...} prefix."""
    line = next(line for line in text.splitlines() if line.startswith(r"\begin{tabular}"))
    spec = line.removeprefix(r"\begin{tabular}{").removesuffix("}").replace("@{}", "")
    spec = re.sub(r"p\{[^{}]*\}", "P", re.sub(r">\{[^{}]*\}", "", spec))
    assert re.fullmatch(r"[lcrP]+", spec), spec
    return len(spec)


def test_column_count_reads_paragraph_columns():
    assert column_count("\\begin{tabular}{@{}llrr@{}}") == 4 and column_count("\\begin{tabular}{lccc}") == 4
    assert column_count(r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.5\linewidth}rr@{}}") == 3


def well_formed(text: str) -> None:
    for rule in (r"\toprule", r"\bottomrule", r"\begin{tabular}", r"\end{tabular}", r"\caption{", r"\label{tab:"):
        assert text.count(rule) == 1, rule
    assert text.count("{") == text.count("}")
    assert text.count("$") % 2 == 0
    assert not re.search(r"(?<!\\)[_%&#]", re.sub(r"&", "", text.split(r"\begin{tabular}")[0])), "unescaped character in the caption"
    width = column_count(text)
    for line in text.splitlines():
        if line.endswith(r"\\") and r"\multicolumn" not in line:
            assert line.count("&") == width - 1, line


def test_latex_table_structure():
    text = latex.table(["Model", "AUC"], ["Block", ["a\\_b", "$0.8$"], None, ["c", "$0.7$"]], caption="A caption.", label="tab:x")
    well_formed(text)
    assert r"\multicolumn{2}{l}{\emph{Block}}" in text and text.count(r"\midrule") == 2
    assert r"\begin{table}[t]" in text and r"\begin{table*}" in latex.table(["a"], [["b"]], "c", "tab:y", wide=True)
    with pytest.raises(ValueError, match="2 cells for 3 columns"):
        latex.table(["a", "b", "c"], [["1", "2"]], "c", "tab:z")


def test_a_cell_on_too_few_papers_is_not_marked():
    cfg = {"consolidate": {"min_articles": 20}}
    row = {"importance_per_critique": -0.02, "ci_excludes_zero": True, "n_articles_with_such_a_critique": 174}
    assert paper.importance_cell(row, cfg) == r"$\mathbf{-2.0}$"
    assert paper.importance_cell({**row, "ci_excludes_zero": False}, cfg) == "$-2.0$"
    assert paper.importance_cell({**row, "n_articles_with_such_a_critique": 4}, cfg) == "($-2.0$)"


# ---- on the result tables of the repository

@pytest.fixture(scope="module")
def results():
    cfg = load_config()
    if not (cfg["paths"]["tables"] / "explainability.csv").is_file():
        pytest.skip("result tables not present")
    return Sources(cfg["paths"]["tables"], REPO_ROOT), cfg


@pytest.mark.parametrize("name", list(paper.TABLES))
def test_every_paper_table_is_well_formed(results, name):
    s, cfg = results
    text = paper.TABLES[name][0](s, cfg)
    well_formed(text)
    assert all(path.startswith("results/tables/") and path.endswith(".csv") for path in s.take_used())


def test_every_file_named_in_the_summary_exists(results):
    s, cfg = results
    text = summary.build(s, cfg, [])
    paths = set(re.findall(r"`((?:results|scripts|src)/[^`*]+)`", text))
    assert len(paths) > 10
    generated = {"results/tables/paper/explain_aspect_severity.tex"}  # written by the same script as the summary
    assert not [path for path in paths - generated if not (REPO_ROOT / path).exists()]
    for heading in ("## RQ1", "## RQ2", "## RQ3", "## RQ4", "## Negative and unexpected results", "## Limitations"):
        assert heading in text


def test_the_summary_refuses_a_result_file_it_does_not_cover(results, tmp_path):
    s, cfg = results
    copy = tmp_path / "results" / "tables"
    copy.mkdir(parents=True)
    for name in ("annotation_sample_strata.csv",):
        (copy / name).write_bytes((s.tables_dir / name).read_bytes())
    assert not summary.has_holdout(Sources(copy, tmp_path), cfg) and summary.holdout(Sources(copy, tmp_path), cfg) == []
    (copy / "annotation_report.md").write_text("# report\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="annotation_report.md"):
        summary.status(Sources(copy, tmp_path), cfg)


# ---- reproduction script

def test_reproduce_all_lists_its_stages_and_runs_nothing_by_default():
    assert subprocess.run(["bash", "-n", str(SCRIPT)]).returncode == 0
    done = subprocess.run([str(SCRIPT)], capture_output=True, text=True)
    assert done.returncode == 0 and "+ " not in done.stdout
    stages = re.search(r"^STAGES=\((.*)\)$", SCRIPT.read_text(), re.MULTILINE).group(1).split()
    assert all(re.search(rf"^{stage}\s+\|", done.stdout, re.MULTILINE) for stage in stages)
    assert subprocess.run([str(SCRIPT), "only", "nothing"], capture_output=True).returncode != 0
    assert subprocess.run([str(SCRIPT), "everything"], capture_output=True).returncode != 0


def test_reproduce_all_names_existing_scripts_in_the_order_of_the_phases():
    done = subprocess.run([str(SCRIPT), "all"], capture_output=True, text=True, env={**os.environ, "DRY_RUN": "1"})
    assert done.returncode == 0, done.stderr
    scripts = re.findall(r"scripts/[\w.]+", "\n".join(line for line in done.stdout.splitlines() if line.startswith("+ ")))
    assert all((REPO_ROOT / script).is_file() for script in scripts)
    # the comparisons of the protocol checks only run where their predictions exist (they have their own chain)
    protocol = "scripts/07g_protocol_results.py"
    assert scripts.count(protocol) <= 1 and (protocol not in scripts or scripts[scripts.index(protocol) + 1] == "scripts/10_consolidate.py")
    scripts = [script for script in scripts if script != protocol]
    phases = [int(re.match(r"scripts/(\d+)", script).group(1)) for script in scripts if re.match(r"scripts/\d", script)]
    # the result scripts of phases 7 to 9 run again at the end, then the consolidation and the paper; the
    # sensitivity analyses (07e) come after the results of the ablations (08b), whose table they read
    expected = sorted(phases[:-6]) + [7, 8, 7, 9, 10, 11]
    assert phases == expected and set(range(12)) <= set(phases)
    assert "03b_llm_report" not in done.stdout       # its failure log of the full run no longer exists


def test_the_consolidation_reads_result_tables_only():
    """No data file, no prediction, no model: the numbers come from the CSV files of results/tables/."""
    for path in ("scripts/10_consolidate.py", "src/eval/paper.py", "src/eval/summary.py", "src/eval/sources.py", "src/eval/latex.py",
                 "scripts/11_paper.py", "src/eval/numbers.py"):
        code = (REPO_ROOT / path).read_text(encoding="utf-8")
        for forbidden in ("read_parquet", "import torch", "torch.load", '["processed"]', '["interim"]', '["raw"]', "sklearn"):
            assert forbidden not in code, f"{path} uses {forbidden}"
