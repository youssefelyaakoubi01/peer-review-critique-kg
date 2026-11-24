"""Graph of setting A whose vocabulary of concepts is counted on the training years only.

    uv run python scripts/05f_inductive_graph.py

In the graph of the study (scripts/05_build_graph.py) a keyword is a concept if at least
`kg.concepts.min_articles` articles of the training AND test years use it: the graph a
model is trained on depends on the keywords of the test papers (no label). Here the
graph of the training years is built first, alone; the test years and then the holdout
years are appended with the vocabulary and the concepts that carry `shares_concept`
frozen (src/kg/extend.py, as the holdout year was appended to the graph of the study).
Nothing else changes: same papers, same reviews, same critiques, same embeddings.

Checked before anything is written:
  - every concept is used by at least `min_articles` articles of the training years, and
    its number of articles is counted on these years;
  - the features of every article, review and critique are those of the graph of the
    study extended with the holdout year (data/processed/<kg.holdout.dir>), node by node;
  - the relations that do not involve a concept hold the same number of edges.

Outputs in data/processed/<kg.inductive.dir>/:
    graph_A.pt, graph_features.json, nodes_<type>.parquet, targets.parquet, graph.stats.md
and in results/tables/: kg_statistics_inductive.csv, kg_concept_coverage_inductive.csv.

No outcome is read to build the graph; the targets are written apart, as in phase 5.
"""

import json
import sys
import time

import numpy as np
import pandas as pd
import torch

from src.clean import views
from src.kg import build, embed, extend, tables as kg_tables, text as kg_text
from src.kg.assemble import article_embeddings, load_tables, texts_to_encode
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

SETTING = "A"
TRAINING_SPLITS = ("train", "val")
ID_COLUMNS = {"article": ["forum_id", "year"], "review": ["review_id", "forum_id"], "critique": ["critique_id", "review_id"],
              "aspect": ["aspect"], "concept": ["concept", "n_articles"]}
NODE_KEYS = {"article": "forum_id", "review": "review_id", "critique": "critique_id"}
CONCEPT_FREE = (kg_tables.HAS_REVIEW, kg_tables.CONTAINS, kg_tables.ABOUT)


def main() -> int:
    cfg = load_config()
    settings = cfg["kg"]
    log = setup_run_logging("05f_inductive_graph", cfg["paths"]["logs"])
    tables_dir, processed = cfg["paths"]["tables"], cfg["paths"]["processed"]
    out_dir = processed / settings["inductive"]["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    max_chars = cfg["llm"]["max_input_chars"]

    # ---- tables: the training years alone, then each later year with the vocabulary frozen
    start = time.time()
    base = load_tables(cfg, TRAINING_SPLITS).setting(SETTING)
    if not set(base.nodes["article"]["year"]) <= set(cfg["splits"]["train"]):
        raise SystemExit("the base graph holds articles of other years than the training years")
    inputs = views.load_model_inputs(cfg, SETTING)
    labels = views.load_labels(cfg, "as_reject")  # the widest set of usable papers
    tables = base
    for split, run in (("test", settings["run"]), ("holdout", settings["holdout"]["run"])):
        run_dir = cfg["paths"]["llm"] / run
        forum_ids = set(labels.loc[labels["split"] == split, "forum_id"])
        tables = extend.extend_tables(tables, inputs["papers_initial"], inputs["reviews"], pd.read_parquet(run_dir / "critiques.parquet"),
                                      pd.read_parquet(run_dir / "audit.parquet"), forum_ids, settings, max_chars)
        log.info("%s years appended: %s", split, {t: len(table) for t, table in tables.nodes.items()})
    log.info("tables built in %.0f s (graph of the training years: %s)", time.time() - start,
             {t: len(table) for t, table in base.nodes.items()})

    # ---- check: the vocabulary owes nothing to a later year
    articles, concepts = tables.nodes["article"], tables.nodes["concept"]
    training = articles[articles["year"].isin(cfg["splits"]["train"])]
    counts = pd.Series([c for keywords in training["keywords"] for c in kg_text.concepts_of(keywords)]).value_counts()
    expected = counts[counts >= settings["concepts"]["min_articles"]]
    if sorted(expected.index) != concepts["concept"].tolist() or not concepts["n_articles"].equals(
            concepts["concept"].map(expected).astype(int)):
        raise SystemExit("the vocabulary of concepts is not the one counted on the training years")
    log.info("vocabulary: %d concepts, each used by at least %d articles of %s", len(concepts), settings["concepts"]["min_articles"],
             cfg["splits"]["train"])

    # ---- embeddings: every text is already in the cache
    model = settings["text_model"]
    encode = embed.sentence_encoder(model, "cuda" if torch.cuda.is_available() else "cpu")
    directory = cfg["paths"]["interim"] / "kg"
    cache = embed.EmbeddingCache(directory / embed.cache_name(model["name"], model["revision"]))
    embeddings = {"article": article_embeddings(directory, articles, ("article_specter2", settings["holdout"]["article_vectors"]))}
    texts = texts_to_encode(tables)
    for kind in ("concept", "critique", "review"):
        start = time.time()
        vectors, encoded = cache.embed(texts[kind], encode)
        if kind == "review":
            vectors = embed.mean_of_chunks(vectors, [len(chunks) for chunks in tables.nodes["review"]["chunks"]])
        embeddings[kind] = vectors
        log.info("embeddings %s: %d texts, %d sent to the model, %.0f s", kind, len(texts[kind]), encoded, time.time() - start)
    graph, layout = build.build_graph(tables, embeddings)

    # ---- check against the graph of the study extended with the holdout year: only the concepts differ
    reference_dir = processed / settings["holdout"]["dir"]
    reference = torch.load(reference_dir / f"graph_{SETTING}.pt", weights_only=False)
    reference_layout = json.loads((reference_dir / "graph_features.json").read_text(encoding="utf-8"))[SETTING]
    if layout != reference_layout:
        raise SystemExit("the feature layout differs from the one of the graph of the study")
    for node_type, key in NODE_KEYS.items():
        ids = pd.read_parquet(reference_dir / f"nodes_{node_type}.parquet")[key]
        row_of = pd.Series(np.arange(len(ids)), index=ids)
        if len(ids) != len(tables.nodes[node_type]) or set(ids) != set(tables.nodes[node_type][key]):
            raise SystemExit(f"the {node_type} nodes are not those of the graph of the study")
        rows = torch.from_numpy(row_of.loc[tables.nodes[node_type][key]].to_numpy())
        if not torch.equal(graph[node_type].x, reference[node_type].x[rows]):
            raise SystemExit(f"the features of the {node_type} nodes differ from those of the graph of the study")
    for relation in CONCEPT_FREE:
        if graph[relation].edge_index.shape[1] != reference[relation].edge_index.shape[1]:
            raise SystemExit(f"the relation {relation} does not hold the edges of the graph of the study")
    log.info("articles, reviews and critiques: same nodes and same features as in the graph of the study; "
             "concepts: %d here, %d there", graph["concept"].num_nodes, reference["concept"].num_nodes)
    del reference

    # ---- outputs
    targets = kg_tables.targets(articles, views.load_labels(cfg, "excluded"), labels)
    torch.save(graph, out_dir / f"graph_{SETTING}.pt")
    (out_dir / "graph_features.json").write_text(json.dumps({SETTING: layout}, indent=1), encoding="utf-8")
    for node_type, columns in ID_COLUMNS.items():
        tables.nodes[node_type][columns].to_parquet(out_dir / f"nodes_{node_type}.parquet", index=False)
    targets.to_parquet(out_dir / "targets.parquet", index=False)
    log.info("graph: %s", graph)

    statistics = build.statistics(tables, SETTING)
    for column in statistics.columns[statistics.columns.str.startswith("count")]:
        statistics[column] = statistics[column].astype("Int64")
    statistics.to_csv(tables_dir / "kg_statistics_inductive.csv", index=False)
    coverage = extend.concept_coverage(tables, settings["concepts"]["max_articles_for_shared"])
    coverage.to_csv(tables_dir / "kg_concept_coverage_inductive.csv", index=False)
    (out_dir / "graph.stats.md").write_text("\n".join([
        f"# Knowledge graph of setting {SETTING}, vocabulary of concepts of the training years", "",
        f"`graph_{SETTING}.pt`: the graph of {cfg['splits']['train']}, then the articles of {cfg['splits']['test']} and of "
        f"{cfg['splits']['holdout']} appended with the vocabulary frozen. No outcome inside: see `targets.parquet`.", "",
        f"- articles: {len(articles)}, of which {int((~articles['text_available']).sum())} without text before the decisions",
        f"- concepts: {len(concepts)} (counted on {cfg['splits']['train']} only)",
        f"- targets: {targets['split'].value_counts().to_dict()}; with a decision (withdrawn excluded): {int(targets['label'].notna().sum())}",
        "- nodes and edges by type: `results/tables/kg_statistics_inductive.csv`",
        "- keywords covered and neighbours by year: `results/tables/kg_concept_coverage_inductive.csv`", "",
    ]), encoding="utf-8")
    log.info("statistics\n%s", statistics.to_string(index=False))
    log.info("concepts\n%s", coverage.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
