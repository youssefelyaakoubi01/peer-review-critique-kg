"""Reviews sent to the extraction (full corpus or a frozen sample) and their author replies.

Samples are lists of review ids stored in `configs/llm_samples/<name>.txt`. They are
drawn once from the training split and then frozen: changing a prompt example must
not change the reviews a prompt is evaluated on.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.clean import views


def usable_reviews(cfg: dict[str, Any]) -> pd.DataFrame:
    """Reviews of setting A (before the author response) of the usable papers, with their split."""
    reviews = views.load_model_inputs(cfg, "A")["reviews"]
    labels = views.load_labels(cfg, "as_reject")  # the widest set of usable papers
    return reviews.merge(labels[["forum_id", "split"]], on="forum_id")


def prompt_example_ids(prompts_dir: Path) -> set[str]:
    """Reviews used as few-shot examples in any prompt file."""
    ids: set[str] = set()
    for path in sorted(prompts_dir.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            ids |= {example["review_id"] for example in yaml.safe_load(f)["examples"]}
    return ids


def sample_path(cfg: dict[str, Any], name: str) -> Path:
    return cfg["paths"]["llm_samples"] / f"{name}.txt"


def read_sample(path: Path) -> list[str]:
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def draw_sample(cfg: dict[str, Any], name: str, reviews: pd.DataFrame) -> list[str]:
    """Draw and freeze a new sample: reviews of the sample split that are neither a
    prompt example nor in a sample that already exists."""
    settings = cfg["llm"]["samples"]
    path = sample_path(cfg, name)
    if path.exists():
        raise FileExistsError(f"{path} exists: a frozen sample is never drawn again")
    taken = prompt_example_ids(cfg["paths"]["prompts"])
    others = sorted(p for p in path.parent.glob("*.txt"))
    for other in others:
        taken |= set(read_sample(other))
    pool = reviews.loc[(reviews["split"] == settings["split"]) & ~reviews["review_id"].isin(taken), "review_id"]
    seed = settings["seeds"][name]
    ids = sorted(pool.sort_values().sample(n=settings["size"], random_state=seed))
    header = [
        f"# Sample '{name}': {len(ids)} review ids of the {settings['split']} split, drawn with seed {seed}",
        "# among the reviews that are neither a prompt example nor in: "
        + (", ".join(p.name for p in others) or "(no other sample)") + ".",
        "# Frozen: never drawn again.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(header + ids) + "\n", encoding="utf-8")
    return ids


def select_reviews(cfg: dict[str, Any], sample: str | None, years: list[int] | None = None) -> pd.DataFrame:
    """Reviews of a frozen sample (drawn if its file does not exist yet), or all of them
    (those of `years` only, when given)."""
    reviews = usable_reviews(cfg)
    if years is not None:
        reviews = reviews[reviews["year"].isin(years)]
    if sample is not None:
        path = sample_path(cfg, sample)
        ids = read_sample(path) if path.exists() else draw_sample(cfg, sample, reviews)
        selected = reviews[reviews["review_id"].isin(ids)]
        if len(selected) != len(ids):
            raise ValueError(f"sample {sample}: {len(ids) - len(selected)} review ids are not usable reviews")
        allowed = cfg["llm"]["samples"]["split"]
        if set(selected["split"]) != {allowed}:
            raise ValueError(f"sample {sample} contains reviews outside the {allowed} split")
        reviews = selected
    return reviews.sort_values("review_id").reset_index(drop=True)


def author_replies(cfg: dict[str, Any], review_ids: set[str]) -> dict[str, list[str]]:
    """Author replies aligned on each review, in posting order."""
    discussion = pd.read_parquet(
        cfg["paths"]["interim"] / "discussion.parquet",
        columns=["target_review_id", "role", "tcdate", "text"],
    )
    replies = discussion[(discussion["role"] == "authors") & discussion["target_review_id"].isin(review_ids)]
    replies = replies.sort_values("tcdate")
    return {rid: [t for t in group["text"] if t] for rid, group in replies.groupby("target_review_id")}
