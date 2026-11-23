"""Phase 5: build the knowledge graph in settings A and B, and export it.

    uv run python scripts/05a_article_text.py                                   # text before the decisions
    uv run --project envs/specter2 python scripts/05b_embed_articles.py         # SPECTER2 (own environment)
    uv run python scripts/05_build_graph.py --benchmark                         # time estimate only
    uv run python scripts/05_build_graph.py                                     # embeddings, graphs, RDF

Outputs in data/processed/:
    graph_A.pt, graph_B.pt      HeteroData; A has no author response
    graph_features.json         columns of each feature block, per setting and node type
    nodes_<type>.parquet        identifier of each node, in the order of the graph
    targets.parquet             outcome and split of each article (never in the graph)
    peer_review_kg.ttl          RDF export (setting B)
and in results/tables/: kg_statistics.csv, kg_post_rebuttal_markers.csv,
kg_embedding_benchmark.csv.

Embeddings are cached: a second run encodes nothing.
"""

import argparse
import json
import sys
import time

import numpy as np
import pandas as pd
import torch

from src.clean import views
from src.kg import build, embed, rdf, tables as kg_tables
from src.kg.assemble import article_embeddings, load_tables, texts_to_encode
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

ID_COLUMNS = {"article": ["forum_id", "year"], "review": ["review_id", "forum_id"], "critique": ["critique_id", "review_id"],
              "response": ["response_id", "review_id"], "aspect": ["aspect"], "concept": ["concept", "n_articles"]}


def benchmark(texts: dict[str, list[str]], encode: embed.Encoder, n: int) -> pd.DataFrame:
    """Time to encode `n` random texts of each kind, and its extrapolation."""
    rng = np.random.default_rng(0)
    encode(texts["concept"][:64])  # loads the model and warms the GPU up
    rows = []
    for kind, items in texts.items():
        unique = sorted(set(items))
        sample = [unique[i] for i in rng.choice(len(unique), size=min(n, len(unique)), replace=False)]
        start = time.time()
        encode(sample)
        seconds = time.time() - start
        rows.append({"kind": kind, "texts": len(items), "distinct_texts": len(unique), "sample": len(sample),
                     "sample_seconds": round(seconds, 2), "texts_per_second": round(len(sample) / seconds, 1),
                     "estimated_minutes": round(len(unique) * seconds / len(sample) / 60, 1)})
    return pd.DataFrame(rows)


def marker_table(cfg, reviews: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    """Reviews whose kept text still holds a mention of the rebuttal, by year and by
    whether the review was modified after its release. Reviews that were never modified
    cannot hold later additions: their rate is the false-alarm rate of the search.
    (`modified_after_release` is read here for this report only; it is not a model input.)"""
    final = pd.read_parquet(cfg["paths"]["interim"] / "reviews_final.parquet", columns=["review_id", "modified_after_release"])
    table = reviews[["review_id", "year", "post_rebuttal_marker_left"]].merge(final, on="review_id", how="left")
    table = table.merge(audit[["review_id", "n_post_rebuttal_units"]], on="review_id", how="left")
    table["sentences_set_aside"] = table["n_post_rebuttal_units"].fillna(0) > 0
    grouped = table.groupby(["year", "modified_after_release"])
    out = grouped.agg(reviews=("review_id", "size"), reviews_with_sentences_set_aside=("sentences_set_aside", "sum"),
                      reviews_with_a_marker_left=("post_rebuttal_marker_left", "sum")).reset_index()
    out["share_with_a_marker_left"] = (out["reviews_with_a_marker_left"] / out["reviews"]).round(4)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--benchmark", action="store_true", help="only estimate the time of the embeddings")
    parser.add_argument("--skip-rdf", action="store_true", help="do not write the RDF export")
    args = parser.parse_args()
    cfg = load_config()
    settings = cfg["kg"]
    log = setup_run_logging("05_build_graph", cfg["paths"]["logs"])
    tables_dir, processed = cfg["paths"]["tables"], cfg["paths"]["processed"]
    tables_dir.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    start = time.time()
    tables = load_tables(cfg)
    log.info("tables built in %.0f s: %s", time.time() - start, {t: len(table) for t, table in tables.nodes.items()})
    texts = texts_to_encode(tables)
    model = settings["text_model"]
    encode = embed.sentence_encoder(model, "cuda" if torch.cuda.is_available() else "cpu")

    if args.benchmark:
        table = benchmark(texts, encode, settings["benchmark_texts"])
        table.to_csv(tables_dir / "kg_embedding_benchmark.csv", index=False)
        log.info("estimated time for all embeddings: %.1f minutes\n%s", table["estimated_minutes"].sum(), table.to_string(index=False))
        return 0

    # ---- embeddings
    cache = embed.EmbeddingCache(cfg["paths"]["interim"] / "kg" / embed.cache_name(model["name"], model["revision"]))
    embeddings = {"article": article_embeddings(cfg["paths"]["interim"] / "kg", tables.nodes["article"])}
    for kind in ("concept", "critique", "response", "review"):
        start = time.time()
        vectors, encoded = cache.embed(texts[kind], encode)
        if kind == "review":
            vectors = embed.mean_of_chunks(vectors, [len(chunks) for chunks in tables.nodes["review"]["chunks"]])
        embeddings[kind] = vectors
        log.info("embeddings %s: %d texts, %d sent to the model, %.0f s", kind, len(texts[kind]), encoded, time.time() - start)

    # ---- graphs
    layouts, statistics = {}, []
    for setting in ("A", "B"):
        view = tables.setting(setting)
        graph, layouts[setting] = build.build_graph(view, embeddings)
        torch.save(graph, processed / f"graph_{setting}.pt")
        statistics.append(build.statistics(view, setting))
        log.info("graph %s: %s", setting, graph)
    (processed / "graph_features.json").write_text(json.dumps(layouts, indent=1), encoding="utf-8")
    for node_type, columns in ID_COLUMNS.items():
        tables.nodes[node_type][columns].to_parquet(processed / f"nodes_{node_type}.parquet", index=False)
    targets = kg_tables.targets(tables.nodes["article"], views.load_labels(cfg, "excluded"), views.load_labels(cfg, "as_reject"))
    if (targets["split"] == "holdout").any():
        raise ValueError("an article of a holdout year is in the graph")
    targets.to_parquet(processed / "targets.parquet", index=False)

    # ---- tables
    statistics = pd.concat(statistics, ignore_index=True)
    for column in statistics.columns[statistics.columns.str.startswith("count")]:
        statistics[column] = statistics[column].astype("Int64")
    statistics.to_csv(tables_dir / "kg_statistics.csv", index=False)
    audit = pd.read_parquet(cfg["paths"]["llm"] / settings["run"] / "audit.parquet", columns=["review_id", "n_post_rebuttal_units"])
    markers = marker_table(cfg, tables.nodes["review"], audit)
    markers.to_csv(tables_dir / "kg_post_rebuttal_markers.csv", index=False)
    articles = tables.nodes["article"]
    (processed / "graph.stats.md").write_text("\n".join([
        "# Knowledge graph (data/processed)", "",
        f"Critiques and author responses of run `{settings['run']}`. `graph_A.pt`: before the author response; "
        "`graph_B.pt`: with the author responses. Neither holds an outcome: see `targets.parquet`.", "",
        f"- articles: {len(articles)}, of which {int((~articles['text_available']).sum())} without text before the decisions",
        f"- targets: {targets['split'].value_counts().to_dict()}; with a decision (withdrawn excluded): {int(targets['label'].notna().sum())}",
        "- nodes and edges by type: `results/tables/kg_statistics.csv`",
        "- feature columns: `graph_features.json`", "",
    ]), encoding="utf-8")
    log.info("statistics\n%s", statistics.to_string(index=False))
    log.info("post-rebuttal markers left\n%s", markers.to_string(index=False))

    # ---- RDF
    if not args.skip_rdf:
        start = time.time()
        triples = rdf.export(tables.setting("B"), processed / "peer_review_kg.ttl", settings["rdf"]["base_iri"],
                             settings["rdf"]["articles_per_chunk"])
        log.info("RDF: %d triples written in %.0f s", triples, time.time() - start)
    return 0


if __name__ == "__main__":
    sys.exit(main())
