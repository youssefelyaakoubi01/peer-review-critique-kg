"""Inputs of the graph construction, shared by scripts/05_build_graph.py (training and
test years) and scripts/05c_extend_graph.py (a holdout year added afterwards)."""

from pathlib import Path

import numpy as np
import pandas as pd

from src.clean import views
from src.kg import tables as kg_tables


def load_tables(cfg, splits: tuple[str, ...] = ("train", "val", "test")) -> kg_tables.GraphTables:
    """Tables of the graph of the study: training and test years, settings A and B.

    `splits`: the papers of the graph. The default is the graph of the study (a holdout
    year is not part of it); ("train", "val") gives the graph of the training years alone,
    whose vocabulary of concepts owes nothing to a later year."""
    settings = cfg["kg"]
    inputs = views.load_model_inputs(cfg, "A")
    run_dir = cfg["paths"]["llm"] / settings["run"]
    labels = views.load_labels(cfg, "as_reject")  # the widest set of usable papers
    forum_ids = set(labels.loc[labels["split"].isin(splits), "forum_id"])
    return kg_tables.build_tables(
        inputs["papers_initial"], inputs["reviews"],
        pd.read_parquet(run_dir / "critiques.parquet"), pd.read_parquet(run_dir / "critique_responses.parquet"),
        pd.read_parquet(run_dir / "audit.parquet"), forum_ids, settings, cfg["llm"]["max_input_chars"])


def texts_to_encode(tables: kg_tables.GraphTables) -> dict[str, list[str]]:
    """Texts of each kind of node, in the order of the nodes (no author response in setting A)."""
    nodes = tables.nodes
    texts = {
        "critique": nodes["critique"]["text"].tolist(),
        "response": nodes["response"]["text"].tolist() if "response" in nodes else None,
        "concept": nodes["concept"]["concept"].tolist(),
        "review": [chunk for chunks in nodes["review"]["chunks"] for chunk in chunks],  # one text per chunk
    }
    return {kind: items for kind, items in texts.items() if items is not None}


def article_embeddings(directory: Path, articles: pd.DataFrame, names: tuple[str, ...] = ("article_specter2",)) -> np.ndarray:
    """SPECTER2 vectors in the order of the article nodes; zeros where the text is
    missing. `names`: the files written by scripts/05b_embed_articles.py to read."""
    vectors = np.concatenate([np.load(directory / f"{name}.npy") for name in names])
    forum_ids = pd.concat([pd.read_parquet(directory / f"{name}.parquet")["forum_id"] for name in names], ignore_index=True)
    if forum_ids.duplicated().any():
        raise ValueError("an article has several SPECTER2 vectors")
    row_of = {forum_id: i for i, forum_id in enumerate(forum_ids)}
    out = np.zeros((len(articles), vectors.shape[1]), dtype=np.float32)
    for index, (forum_id, available) in enumerate(zip(articles["forum_id"], articles["text_available"])):
        if available:
            out[index] = vectors[row_of[forum_id]]  # KeyError if scripts/05b was not run on this text
    return out
