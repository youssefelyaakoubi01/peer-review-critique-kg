"""Human validation of the critique labels given by the LLM (phase 4).

Two parts:
- before the annotation: a stratified sample of critiques and the files given to the
  annotators, which never contain a label of the LLM;
- after it: agreement between the annotators, consensus labels, and the labels of the
  LLM scored against the consensus.

Nothing here writes a reference label: the annotators fill their files, and they
settle their disagreements themselves in the file written by `disagreement_table`.
"""

import warnings
from pathlib import Path
from typing import Any, get_args

import numpy as np
import pandas as pd
from sklearn.exceptions import UndefinedMetricWarning
from sklearn.metrics import cohen_kappa_score, confusion_matrix, precision_recall_fscore_support

from src.llm.schemas import Aspect, Polarity, Severity, Target
from src.llm.units import Unit

# Labels and their allowed values, as the annotators write them.
LABEL_VALUES: dict[str, tuple[str, ...]] = {
    "aspect": get_args(Aspect),
    "severity": get_args(Severity),
    "polarity": get_args(Polarity),
    "target": get_args(Target),
    "actionable": ("true", "false"),
}
LABELS = tuple(LABEL_VALUES)
STRATA = ("year", "aspect", "severity")
ANNOTATOR_COLUMNS = ("item_id", "critique", "context", *LABELS, "comment")
MARK_START, MARK_END = ">>>", "<<<"
CUT = "[...]"
ENCODING = "utf-8-sig"  # opens correctly in spreadsheet software


# --------------------------------------------------------------------------- sampling
def population(critiques: pd.DataFrame, excluded_reviews: set[str]) -> pd.DataFrame:
    """Critiques that can be drawn: labelled by the LLM, outside the excluded reviews."""
    kept = critiques[critiques["aspect"].notna() & ~critiques["review_id"].isin(excluded_reviews)]
    return kept.sort_values("critique_id").reset_index(drop=True)


def allocate(sizes: pd.Series, n: int, floor: int) -> pd.Series:
    """Number of critiques drawn in each stratum.

    Every stratum gets `floor` critiques (all of them if it has fewer), so that rare
    categories can be scored; what is left of `n` is shared in proportion to what
    remains in each stratum (largest remainders first).
    """
    base = sizes.clip(upper=floor)
    rest = n - int(base.sum())
    room = sizes - base
    if rest < 0:
        raise ValueError(f"{len(sizes)} strata with a floor of {floor} need more than {n} critiques")
    if rest > int(room.sum()):
        raise ValueError(f"cannot draw {n} critiques from a population of {int(sizes.sum())}")
    if rest == 0:
        return base
    quota = room / room.sum() * rest
    extra = np.floor(quota).astype(int)
    largest = (quota - extra).sort_values(ascending=False, kind="stable").index[: rest - int(extra.sum())]
    extra[largest] += 1
    return base + extra


def strata_table(pool: pd.DataFrame, sampled: pd.Series) -> pd.DataFrame:
    """Population, sample size and sampling weight of each stratum (`sampled`: per stratum)."""
    table = pool.groupby(list(STRATA)).size().rename("population").to_frame()
    table["sampled"] = sampled.reindex(table.index).fillna(0).astype(int)
    table["weight"] = (table["population"] / table["sampled"].where(table["sampled"] > 0)).round(4)
    return table.reset_index()


def draw_sample(pool: pd.DataFrame, n: int, floor: int, seed: int) -> list[str]:
    """Critique ids of a new stratified sample, in the order of the items.

    Strata: year x aspect x severity given by the LLM. The order of the items is
    random, so that an item number says nothing about its stratum.
    """
    sizes = pool.groupby(list(STRATA)).size()
    counts = allocate(sizes, n, floor)
    rng = np.random.default_rng(seed)
    drawn: list[str] = []
    for stratum, group in pool.groupby(list(STRATA)):  # sorted strata, sorted critique ids
        drawn += list(rng.choice(group["critique_id"].to_numpy(), size=int(counts[stratum]), replace=False))
    return [drawn[i] for i in rng.permutation(len(drawn))]


def read_sample_file(path: Path) -> list[str]:
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def write_sample_file(path: Path, ids: list[str], header: list[str]) -> None:
    if path.exists():
        raise FileExistsError(f"{path} exists: a frozen sample is never drawn again")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {line}" for line in header] + ids) + "\n", encoding="utf-8")


def sample_key(pool: pd.DataFrame, ids: list[str]) -> pd.DataFrame:
    """Key of the sample: one row per item, with the critique, the labels of the LLM
    and the sampling weight. Not for the annotators."""
    if len(set(ids)) != len(ids):
        raise ValueError("the sample contains a critique twice")
    rows = pool.set_index("critique_id").reindex(ids)
    if rows["review_id"].isna().any():
        missing = list(rows.index[rows["review_id"].isna()][:5])
        raise ValueError(f"critiques of the sample are not in the population, e.g. {missing}")
    key = rows.reset_index()
    key.insert(0, "item_id", [f"item_{i:03d}" for i in range(1, len(key) + 1)])
    sampled = key.groupby(list(STRATA)).size()
    weights = strata_table(pool, sampled).set_index(list(STRATA))["weight"]
    key["weight"] = [weights[stratum] for stratum in key[list(STRATA)].itertuples(index=False, name=None)]
    key["actionable"] = key["actionable"].map(lambda value: str(bool(value)).lower())
    key = key.rename(columns={label: f"llm_{label}" for label in LABELS})
    columns = ["item_id", "critique_id", "review_id", "forum_id", "year", "units", "text",
               *(f"llm_{label}" for label in LABELS), "weight"]
    return key[columns]


# --------------------------------------------------------------------------- files to annotate
def critique_context(units: list[Unit], critique_units: list[int], window: int) -> str:
    """Text of the review around a critique, with the sentences of the critique between
    `>>>` and `<<<`. Each paragraph or bullet point of the review is one line, under the
    name of its field; `window` sentences are kept before and after the critique."""
    inside = set(critique_units)
    positions = [index for index, unit in enumerate(units) if unit.id in inside]
    if not positions:
        raise ValueError("the critique has no unit in this review")
    first, last = max(0, positions[0] - window), min(len(units), positions[-1] + window + 1)
    lines: list[str] = [CUT] if first > 0 else []
    field = line = None
    for unit in units[first:last]:
        text = f"{MARK_START} {unit.text} {MARK_END}" if unit.id in inside else unit.text
        if unit.field != field:
            lines.append(f"[{unit.field}]")
            lines.append(text)
        elif unit.line != line:
            lines.append(text)
        else:
            lines[-1] += " " + text
        field, line = unit.field, unit.line
    if last < len(units):
        lines.append(CUT)
    # neighbouring sentences of the critique read as one marked passage
    return "\n".join(lines).replace(f" {MARK_END} {MARK_START} ", " ")


def annotation_table(key: pd.DataFrame, review_units: dict[str, list[Unit]], window: int) -> pd.DataFrame:
    """Table given to an annotator: the critique, its context, empty label columns.
    It holds no label of the LLM and nothing about the paper, its scores or its decision."""
    table = pd.DataFrame({
        "item_id": key["item_id"],
        "critique": key["text"],
        "context": [critique_context(review_units[row.review_id], list(row.units), window)
                    for row in key.itertuples()],
    })
    for column in (*LABELS, "comment"):
        table[column] = ""
    return table[list(ANNOTATOR_COLUMNS)]


def annotator_order(n_items: int, seed: int, annotator_index: int) -> np.ndarray:
    """Order of the items in the file of one annotator (a different one for each)."""
    return np.random.default_rng([seed, annotator_index]).permutation(n_items)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding=ENCODING)


def has_annotations(path: Path) -> bool:
    """True if a file to annotate already holds at least one label or comment."""
    if not path.exists():
        return False
    table = read_csv(path)
    filled = [c for c in (*LABELS, "comment") if c in table.columns]
    return bool(table[filled].apply(lambda column: column.str.strip() != "").any().any())


def write_annotator_file(path: Path, table: pd.DataFrame) -> bool:
    """Write a file to annotate; False (and nothing written) if it already holds annotations."""
    if has_annotations(path):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False, encoding=ENCODING)
    return True


# --------------------------------------------------------------------------- annotations
def read_annotations(path: Path, item_ids: list[str] | None = None) -> pd.DataFrame:
    """Labels of one annotator, indexed by item. Raises ValueError with the list of
    problems: missing items, empty cells, values outside the allowed ones."""
    table = read_csv(path)
    missing = [c for c in ("item_id", *LABELS) if c not in table.columns]
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    if table["item_id"].duplicated().any():
        raise ValueError(f"{path.name}: an item appears twice")
    labels = table.set_index("item_id")[list(LABELS)].apply(lambda column: column.str.strip().str.lower())
    problems: list[str] = []
    if item_ids is not None and set(labels.index) != set(item_ids):
        problems.append(f"{len(set(item_ids) - set(labels.index))} items of the sample are missing, "
                        f"{len(set(labels.index) - set(item_ids))} items are not in the sample")
    for label, allowed in LABEL_VALUES.items():
        empty = labels.index[labels[label] == ""]
        wrong = labels.index[(labels[label] != "") & ~labels[label].isin(allowed)]
        if len(empty):
            problems.append(f"{label}: {len(empty)} empty cells, e.g. {list(empty[:3])}")
        if len(wrong):
            values = sorted(set(labels.loc[wrong, label]))[:5]
            problems.append(f"{label}: {len(wrong)} values outside {list(allowed)}, e.g. {values}")
    if problems:
        raise ValueError(f"{path.name}: " + "; ".join(problems))
    return labels if item_ids is None else labels.loc[item_ids]


def agreement_table(first: pd.DataFrame, second: pd.DataFrame) -> pd.DataFrame:
    """Raw agreement and Cohen's kappa between two annotators, per label."""
    rows = []
    for label, allowed in LABEL_VALUES.items():
        with warnings.catch_warnings():  # kappa is undefined (NaN) when both annotators use one category only
            warnings.simplefilter("ignore", UndefinedMetricWarning)
            kappa = cohen_kappa_score(first[label], second[label], labels=list(allowed))
        rows.append({
            "label": label,
            "items": len(first),
            "agreement": round(float((first[label] == second[label]).mean()), 4),
            "cohen_kappa": round(float(kappa), 4),
        })
    return pd.DataFrame(rows)


def disagreement_table(first: pd.DataFrame, second: pd.DataFrame, names: tuple[str, str],
                       items: pd.DataFrame) -> pd.DataFrame:
    """One row per (item, label) on which the annotators differ, with an empty
    `consensus` column that they fill together. `items`: critique and context per item."""
    texts = items.set_index("item_id")
    rows = []
    for label in LABELS:
        for item_id in first.index[first[label] != second[label]]:
            rows.append({"item_id": item_id, "label": label,
                         f"annotator_{names[0]}": first.at[item_id, label],
                         f"annotator_{names[1]}": second.at[item_id, label],
                         "consensus": "",
                         "critique": texts.at[item_id, "critique"], "context": texts.at[item_id, "context"]})
    columns = ["item_id", "label", f"annotator_{names[0]}", f"annotator_{names[1]}", "consensus",
               "critique", "context"]
    return pd.DataFrame(rows, columns=columns)


def read_resolutions(path: Path) -> pd.DataFrame:
    """Disagreements settled by the annotators: rows of the disagreement file whose
    `consensus` cell is filled. Raises ValueError on a value outside the allowed ones."""
    table = read_csv(path)
    table["consensus"] = table["consensus"].str.strip().str.lower()
    filled = table[table["consensus"] != ""]
    wrong = [f"{row.item_id}/{row.label}: {row.consensus}" for row in filled.itertuples()
             if row.consensus not in LABEL_VALUES[row.label]]
    if wrong:
        raise ValueError(f"{path.name}: consensus values outside the allowed ones, e.g. {wrong[:5]}")
    return filled[["item_id", "label", "consensus"]]


def consensus_labels(first: pd.DataFrame, second: pd.DataFrame,
                     resolutions: pd.DataFrame | None = None) -> pd.DataFrame:
    """Reference labels: the common label where the annotators agree, the label they
    settled on where they did not, missing (None) where a disagreement is still open."""
    consensus = first.where(first == second).astype(object)
    consensus = consensus.where(consensus.notna(), None)
    for row in (resolutions.itertuples() if resolutions is not None else ()):
        if row.item_id not in consensus.index:
            raise ValueError(f"the disagreement file names an unknown item: {row.item_id}")
        if consensus.at[row.item_id, row.label] is not None:
            raise ValueError(f"{row.item_id}/{row.label}: the annotators agree, nothing to settle")
        consensus.at[row.item_id, row.label] = row.consensus
    return consensus


# --------------------------------------------------------------------------- LLM against consensus
def llm_scores(consensus: pd.DataFrame, key: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Labels of the LLM scored against the consensus.

    Returns `categories` (precision, recall, F1, support per category), `summary`
    (accuracy and macro F1 per label) and one confusion matrix per label
    (`confusion_<label>`: rows = consensus, columns = LLM). Each figure is given
    unweighted (on the sample) and weighted by the sampling weights (estimate for the
    corpus). Items whose disagreement is still open are left out of that label.
    """
    key = key.set_index("item_id").loc[consensus.index]
    categories, summary = [], []
    tables: dict[str, pd.DataFrame] = {}
    for label, allowed in LABEL_VALUES.items():
        known = consensus[label].notna()
        truth, predicted = consensus.loc[known, label], key.loc[known, f"llm_{label}"]
        row: dict[str, Any] = {"label": label, "items": int(known.sum()),
                               "items_without_consensus": int((~known).sum())}
        for weighting, weights in (("sample", None), ("corpus", key.loc[known, "weight"])):
            precision, recall, f1, support = precision_recall_fscore_support(
                truth, predicted, labels=list(allowed), sample_weight=weights, zero_division=0)
            for index, category in enumerate(allowed):
                categories.append({"label": label, "category": category, "weighting": weighting,
                                   "precision": round(float(precision[index]), 4),
                                   "recall": round(float(recall[index]), 4),
                                   "f1": round(float(f1[index]), 4),
                                   "support": round(float(support[index]), 1)})
            correct = (truth == predicted).to_numpy(dtype=float)
            row[f"accuracy_{weighting}"] = round(float(np.average(correct, weights=weights)), 4) if len(truth) else None
            present = [i for i, s in enumerate(support) if s > 0]  # macro F1 over the categories met
            row[f"macro_f1_{weighting}"] = round(float(np.mean(f1[present])), 4) if present else None
        summary.append(row)
        matrix = confusion_matrix(truth, predicted, labels=list(allowed))
        tables[f"confusion_{label}"] = pd.DataFrame(
            matrix, index=pd.Index(allowed, name="consensus \\ llm"), columns=list(allowed)).reset_index()
    tables["categories"] = pd.DataFrame(categories)
    tables["summary"] = pd.DataFrame(summary)
    return tables
