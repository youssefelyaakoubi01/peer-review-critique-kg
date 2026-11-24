"""Phase 5e: date of the weights of the pretrained models against the dates of each year.

    uv run python scripts/05e_model_dates.py            # needs the network (Hugging Face Hub)

Three pretrained models produce model inputs: the encoder of the articles (SPECTER2, base
model and adapter), the encoder of the other texts, and the LLM that segments and types
the critiques. Their training data are not documented to the day, but weights cannot have
been trained on a text written after they were published. For the revision of each model
pinned in the config, the script reads on the Hub the date of the last commit that changed
each weight file, and compares it with the day the first review of each year was created
and the day of its first decision note (results/tables/input_dates.csv).

When a model has its weights in two formats committed at different dates
(pytorch_model.bin and model.safetensors), both files are downloaded and compared tensor
by tensor: if they hold the same values, the weights are dated by the older file.

Nothing of the project is sent: the requests name public repositories and revisions.
The model compared with the LLM on a sample (llm comparison, a hosted model) produces no
model input and is not listed.

Output: results/tables/pretrained_model_dates.csv, one row per model and year.
"""

import sys
from datetime import datetime, timezone

import pandas as pd
import torch
from huggingface_hub import HfApi, hf_hub_download
from safetensors.torch import load_file

from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

WEIGHT_NAMES = ("pytorch_model.bin", "model.safetensors", "pytorch_adapter.bin")  # and the shards model-0000x-of-0000y.safetensors
PAIR = ("pytorch_model.bin", "model.safetensors")


def is_weight_file(path: str) -> bool:
    return path in WEIGHT_NAMES or (path.startswith("model-") and path.endswith(".safetensors"))


def same_tensors(repository: str, revision: str) -> dict:
    """Whether the two weight files of a revision hold the same values, tensor by tensor."""
    old = torch.load(hf_hub_download(repository, PAIR[0], revision=revision), map_location="cpu", weights_only=True)
    new = load_file(hf_hub_download(repository, PAIR[1], revision=revision))
    shared = sorted(set(old) & set(new))
    equal = sum(bool(torch.equal(old[name], new[name])) for name in shared)
    return {"tensors_compared": len(shared), "tensors_equal": equal, "tensors_in_one_file_only": len(set(old) ^ set(new)),
            "formats_identical": equal == len(shared) and len(shared) > 0}


def main() -> int:
    cfg = load_config()
    log = setup_run_logging("05e_model_dates", cfg["paths"]["logs"])
    tables_dir, kg, api = cfg["paths"]["tables"], cfg["kg"], HfApi()
    models = [
        ("article encoder, base model", kg["article_model"]["base"], kg["article_model"]["base_revision"]),
        ("article encoder, adapter", kg["article_model"]["adapter"], kg["article_model"]["adapter_revision"]),
        ("text encoder", kg["text_model"]["name"], kg["text_model"]["revision"]),
        ("LLM typing the critiques", cfg["llm"]["model"], cfg["llm"]["revision"]),
    ]

    # ---- dates of each year: first review created, first decision note
    reviews = pd.read_parquet(cfg["paths"]["interim"] / "reviews.parquet", columns=["year", "tcdate"])
    first_review = reviews.groupby("year")["tcdate"].min().map(lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).date())
    first_decision = pd.read_csv(tables_dir / "input_dates.csv").set_index("year")["first_decision_note"].map(
        lambda text: datetime.fromisoformat(text).date())

    rows = []
    for role, repository, revision in models:
        commits = {commit.commit_id: commit.created_at for commit in api.list_repo_commits(repository)}
        if revision not in commits:
            raise SystemExit(f"revision {revision} of {repository} is not on its main branch")
        files = [f for f in api.list_repo_tree(repository, revision=revision, recursive=True, expand=True)
                 if hasattr(f, "size") and is_weight_file(f.path)]
        if not files or any(f.last_commit is None for f in files):
            raise SystemExit(f"no dated weight file found in {repository}@{revision}")
        dates = {f.path: f.last_commit.date.date() for f in files}
        check = {"tensors_compared": None, "tensors_equal": None, "tensors_in_one_file_only": None, "formats_identical": None}
        if set(PAIR) <= set(dates) and dates[PAIR[0]] != dates[PAIR[1]]:
            check = same_tensors(repository, revision)
        # the weights are dated by their older file only if the newer one holds the same values
        dated = min(dates.values()) if check["formats_identical"] or len(set(dates.values())) == 1 else max(dates.values())
        log.info("%s (%s@%s): weight files %s, compared %s, weights dated %s", role, repository, revision[:12], dates, check, dated)
        for year in cfg["years"]:
            rows.append({
                "role": role, "repository": repository, "revision": revision, "revision_committed": commits[revision].date().isoformat(),
                "weight_files": " ".join(f"{path}:{day.isoformat()}" for path, day in sorted(dates.items())), **check,
                "weights_dated": dated.isoformat(), "year": year, "first_review_created": first_review[year].isoformat(),
                "first_decision_note": first_decision[year].isoformat(),
                "weights_before_first_review": dated < first_review[year], "weights_before_first_decision": dated < first_decision[year],
                "days_from_weights_to_first_review": (first_review[year] - dated).days})
    table = pd.DataFrame(rows)
    table.to_csv(tables_dir / "pretrained_model_dates.csv", index=False)
    shown = ["role", "weights_dated", "year", "first_review_created", "first_decision_note", "weights_before_first_review",
             "weights_before_first_decision"]
    log.info("weights of the pretrained models against the dates of each year\n%s", table[shown].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
