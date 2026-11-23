"""Phase 5b: SPECTER2 embeddings of the articles (title and abstract before the decisions).

Runs in its own environment, because SPECTER2 needs the `adapters` library:

    uv run --project envs/specter2 python scripts/05b_embed_articles.py
    uv run --project envs/specter2 python scripts/05b_embed_articles.py --holdout   # papers of the holdout years

Reads data/interim/papers_initial.parquet (never the current, camera-ready text) and
writes data/interim/kg/article_specter2.npy (float32, one row per paper with text) and
article_specter2.parquet (forum_id of each row). With --holdout, the papers of the
holdout years go to their own files (`kg.holdout.article_vectors`) and the files of the
study are not touched. This script imports nothing from `src`: the environment only
holds what SPECTER2 needs.
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from adapters import AutoAdapterModel
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--holdout", action="store_true", help="embed the papers of the holdout years, in their own files")
    args = parser.parse_args()
    cfg = yaml.safe_load((ROOT / "configs" / "default.yaml").read_text(encoding="utf-8"))
    settings = cfg["kg"]["article_model"]
    log_dir = ROOT / cfg["paths"]["logs"]
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(log_dir / f"05b_embed_articles_{datetime.now():%Y%m%d_%H%M%S}.log")])
    log = logging.getLogger("05b_embed_articles")

    papers = pd.read_parquet(ROOT / cfg["paths"]["interim"] / "papers_initial.parquet",
                             columns=["forum_id", "year", "title", "abstract", "text_available"])
    # Training and test years only: a holdout year is not part of the graph of the study.
    study_years = [*cfg["splits"]["train"], *cfg["splits"]["test"]]
    years, output = (cfg["splits"]["holdout"], cfg["kg"]["holdout"]["article_vectors"]) if args.holdout else (study_years, "article_specter2")
    papers = papers[papers["text_available"] & papers["year"].isin(years)].sort_values("forum_id").reset_index(drop=True)

    torch.manual_seed(0)
    tokenizer = AutoTokenizer.from_pretrained(settings["base"], revision=settings["base_revision"])
    model = AutoAdapterModel.from_pretrained(settings["base"], revision=settings["base_revision"])
    name = model.load_adapter(settings["adapter"], source="hf", revision=settings["adapter_revision"],
                              load_as="proximity", set_active=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    log.info("papers_with_text=%d base=%s adapter=%s active_adapter=%s device=%s",
             len(papers), settings["base"], settings["adapter"], name, device)

    texts = (papers["title"] + tokenizer.sep_token + papers["abstract"]).tolist()
    order = np.argsort([len(text) for text in texts])  # batches of similar length
    vectors = np.zeros((len(texts), model.config.hidden_size), dtype=np.float32)
    start = time.time()
    with torch.inference_mode():
        for begin in range(0, len(texts), settings["batch_size"]):
            rows = order[begin:begin + settings["batch_size"]]
            batch = tokenizer([texts[i] for i in rows], padding=True, truncation=True,
                              max_length=settings["max_length"], return_tensors="pt",
                              return_token_type_ids=False).to(device)
            vectors[rows] = model(**batch).last_hidden_state[:, 0, :].float().cpu().numpy()  # [CLS]
    out = ROOT / cfg["kg"]["dir"]
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / f"{output}.npy", vectors)
    papers[["forum_id"]].to_parquet(out / f"{output}.parquet", index=False)
    log.info("years=%s vectors=%s seconds=%.1f output=%s", years, vectors.shape, time.time() - start, out / output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
