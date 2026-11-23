"""Classification metrics of the study, and their summary over seeds.

Every model outputs the probability that a paper is accepted. The decision threshold
is fixed (0.5) and never tuned.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef, roc_auc_score

METRICS = ("auc", "macro_f1", "mcc", "accuracy", "ece")
THRESHOLD = 0.5
ECE_BINS = 15


def expected_calibration_error(labels: np.ndarray, probabilities: np.ndarray, n_bins: int = ECE_BINS) -> float:
    """Gap between the predicted probability of acceptance and the observed acceptance
    rate, averaged over `n_bins` bins of equal width weighted by their size."""
    labels, probabilities = np.asarray(labels, dtype=float), np.asarray(probabilities, dtype=float)
    bins = np.minimum((probabilities * n_bins).astype(int), n_bins - 1)
    total = 0.0
    for b in np.unique(bins):
        inside = bins == b
        total += inside.sum() * abs(labels[inside].mean() - probabilities[inside].mean())
    return float(total / len(labels))


def classification_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    """The five metrics of the study. AUC is missing (nan) when a single class is present."""
    labels, probabilities = np.asarray(labels).astype(int), np.asarray(probabilities, dtype=float)
    if len(labels) == 0:
        return {name: float("nan") for name in METRICS}
    predicted = (probabilities >= THRESHOLD).astype(int)
    both_classes = len(np.unique(labels)) == 2
    return {
        "auc": float(roc_auc_score(labels, probabilities)) if both_classes else float("nan"),
        "macro_f1": float(f1_score(labels, predicted, average="macro", labels=[0, 1], zero_division=0)),
        "mcc": float(matthews_corrcoef(labels, predicted)),
        "accuracy": float(accuracy_score(labels, predicted)),
        "ece": expected_calibration_error(labels, probabilities),
    }


def summarise(by_seed: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Mean and standard deviation over seeds (sample standard deviation, n - 1) of each
    metric, per group of `keys`. Columns that are constant in a group are kept."""
    constant = [c for c in by_seed.columns if c not in (*keys, "seed", *METRICS)]
    rows = []
    for group, table in by_seed.groupby(keys, sort=False):
        row = dict(zip(keys, group if isinstance(group, tuple) else (group,)))
        for column in constant:
            values = table[column].unique()
            if len(values) != 1:
                raise ValueError(f"column '{column}' varies between seeds")
            row[column] = values[0]
        row["n_seeds"] = table["seed"].nunique()
        for metric in METRICS:
            row[f"{metric}_mean"] = table[metric].mean()
            row[f"{metric}_std"] = table[metric].std(ddof=1) if len(table) > 1 else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def latex_table(summary: pd.DataFrame, row_label: str, labels: dict[str, str], caption: str, label: str,
                group: str | None = None, group_labels: dict[str, str] | None = None, wide: bool = False,
                size: str = "small") -> str:
    """booktabs table of `summary` (output of `summarise`): one row per `row_label`,
    cells "mean ± std" with three decimals, optionally in blocks of `group`. `wide`:
    over the two columns of a two-column paper, in a smaller font (`size`)."""
    header = ["Model", "AUC", "Macro F1", "MCC", "Accuracy", "ECE"]
    environment = "table*" if wide else "table"
    lines = [rf"\begin{{{environment}}}[t]", r"\centering", *([rf"\{size}"] if wide else []), rf"\caption{{{caption}}}", rf"\label{{{label}}}",
             r"\begin{tabular}{l" + "c" * len(METRICS) + "}", r"\toprule", " & ".join(header) + r" \\"]
    blocks = [(None, summary)] if group is None else list(summary.groupby(group, sort=False))
    for name, block in blocks:
        lines.append(r"\midrule")
        if name is not None:
            title = (group_labels or {}).get(name, str(name)).replace("_", r"\_")
            lines.append(rf"\multicolumn{{{len(header)}}}{{l}}{{\emph{{{title}}} ($n = {int(block['n_papers'].iloc[0])}$)}} \\")
        for _, row in block.iterrows():
            cells = [labels.get(row[row_label], str(row[row_label])).replace("_", r"\_")]
            for metric in METRICS:
                mean, std = row[f"{metric}_mean"], row[f"{metric}_std"]
                cells.append("--" if np.isnan(mean) else rf"${mean:.3f} \pm {std:.3f}$")
            lines.append(" & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", rf"\end{{{environment}}}", ""]
    return "\n".join(lines)
