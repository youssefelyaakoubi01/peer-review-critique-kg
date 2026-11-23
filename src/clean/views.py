"""Single entry point for what a model may read. Every model must load its data here.

Setting A (initial reviews): the submission and the reviews posted before the
first author response, with pre-rebuttal scores. No final score, no discussion,
no outcome. The forbidden-field list of the config is checked at every call.

The text of the submission comes from `papers_initial` (title, abstract and keywords
before the decisions). The table `papers` holds the current text, which is the
camera-ready version for accepted papers: it is never a model input.
"""

from typing import Any

import pandas as pd

from src.clean.normalize import PHASE_BEFORE
from src.utils.leakage import assert_no_forbidden_fields

LABEL_COLUMNS = {"excluded": ("label", "eligible"),
                 "as_reject": ("label_withdrawn_as_reject", "eligible_withdrawn_as_reject")}


def model_inputs(
    tables: dict[str, pd.DataFrame], cfg: dict[str, Any], setting: str = "A"
) -> dict[str, pd.DataFrame]:
    """Model-input views built from the cleaned tables."""
    if setting != "A":
        raise ValueError(f"setting {setting!r} is not defined yet")
    allowed = cfg["clean"]["model_input_tables"]
    if "papers" in allowed:
        raise ValueError("leakage: `papers` holds post-decision text, use `papers_initial`")
    views = {name: tables[name] for name in allowed}
    reviews = views["reviews"]
    # Only what existed before the authors answered; the phase is then constant.
    views["reviews"] = reviews[reviews["phase"] == PHASE_BEFORE].drop(columns=["phase"])
    for name, view in views.items():
        assert_no_forbidden_fields(view.columns, cfg["leakage"]["forbidden_fields"])
        if any(c.endswith(("_final", "_ext_post")) for c in view.columns):
            raise ValueError(f"leakage: final-state column in model input table '{name}'")
    return views


def load_model_inputs(cfg: dict[str, Any], setting: str = "A") -> dict[str, pd.DataFrame]:
    """Read the model-input tables from data/interim/."""
    interim = cfg["paths"]["interim"]
    names = cfg["clean"]["model_input_tables"]
    return model_inputs({n: pd.read_parquet(interim / f"{n}.parquet") for n in names}, cfg, setting)


def labels(outcomes: pd.DataFrame, withdrawn: str = "excluded") -> pd.DataFrame:
    """Labels and splits of the papers usable in setting A.

    `withdrawn`: "excluded" (papers withdrawn before a decision are left out) or
    "as_reject" (they count as rejections).
    """
    label, eligible = LABEL_COLUMNS[withdrawn]
    selected = outcomes[outcomes[eligible]]
    return selected[["forum_id", "year", "split"]].assign(label=selected[label].astype(int))


def load_labels(cfg: dict[str, Any], withdrawn: str = "excluded") -> pd.DataFrame:
    return labels(pd.read_parquet(cfg["paths"]["interim"] / "outcomes.parquet"), withdrawn)
