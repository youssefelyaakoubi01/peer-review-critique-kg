"""Graph of setting A extended with the holdout year (ICLR 2026).

    uv run --project envs/specter2 python scripts/05b_embed_articles.py --holdout   # SPECTER2 of the new articles
    uv run python scripts/05c_extend_graph.py

The graph of the study (data/processed/graph_A.pt, training and test years) is read and
never written. The articles of the holdout years, their reviews and their critiques
(extraction run `kg.holdout.run`) are appended after its nodes; the concepts are those
of the graph of the study. Before anything is written, the script checks that the part
of the new graph that belongs to the study is the graph of the study itself: same
features, same edges, in the same order.

Outputs in data/processed/<kg.holdout.dir>/:
    graph_A.pt, graph_features.json, nodes_<type>.parquet, targets.parquet (split
    `holdout` for the new articles)
and in results/tables/: kg_statistics_holdout.csv, kg_concept_coverage_holdout.csv,
kg_post_rebuttal_markers_holdout.csv.

No outcome is read to build the graph; the targets are written apart, as in phase 5.
"""

import json
import sys
import time

import pandas as pd
import torch

from src.clean import views
from src.kg import build, embed, extend, tables as kg_tables
from src.kg.assemble import article_embeddings, load_tables, texts_to_encode
from src.utils.config import load_config
from src.utils.runlog import setup_run_logging

SETTING = "A"
ID_COLUMNS = {"article": ["forum_id", "year"], "review": ["review_id", "forum_id"], "critique": ["critique_id", "review_id"],
              "aspect": ["aspect"], "concept": ["concept", "n_articles"]}


def same_prefix(graph, reference) -> list[str]:
    """Differences between `reference` and the part of `graph` that holds its nodes and edges."""
    problems = []
    if set(graph.node_types) != set(reference.node_types) or set(graph.edge_types) != set(reference.edge_types):
        return ["node or edge types differ"]
    for node_type in reference.node_types:
        n = reference[node_type].num_nodes
        if not torch.equal(graph[node_type].x[:n], reference[node_type].x):
            problems.append(f"features of '{node_type}'")
    for node_type in ("article", "review"):
        if not torch.equal(graph[node_type].year[:reference[node_type].num_nodes], reference[node_type].year):
            problems.append(f"years of '{node_type}'")
    for edge_type in reference.edge_types:
        n = reference[edge_type].edge_index.shape[1]
        if not torch.equal(graph[edge_type].edge_index[:, :n], reference[edge_type].edge_index):
            problems.append(f"edges {edge_type}")
        if "edge_weight" in reference[edge_type] and not torch.equal(graph[edge_type].edge_weight[:n], reference[edge_type].edge_weight):
            problems.append(f"weights of {edge_type}")
    return problems


def main() -> int:
    cfg = load_config()
    settings, holdout = cfg["kg"], cfg["kg"]["holdout"]
    log = setup_run_logging("05c_extend_graph", cfg["paths"]["logs"])
    tables_dir, processed = cfg["paths"]["tables"], cfg["paths"]["processed"]
    out_dir = processed / holdout["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- tables: the graph of the study, then the holdout years appended
    start = time.time()
    base = load_tables(cfg).setting(SETTING)
    inputs = views.load_model_inputs(cfg, SETTING)
    labels = views.load_labels(cfg, "as_reject")  # the widest set of usable papers
    forum_ids = set(labels.loc[labels["split"] == "holdout", "forum_id"])
    run_dir = cfg["paths"]["llm"] / holdout["run"]
    audit = pd.read_parquet(run_dir / "audit.parquet")
    critiques = pd.read_parquet(run_dir / "critiques.parquet")
    if not set(critiques["year"]) <= set(cfg["splits"]["holdout"]):
        raise ValueError(f"run {holdout['run']} holds critiques of other years than the holdout years")
    tables = extend.extend_tables(base, inputs["papers_initial"], inputs["reviews"], critiques, audit, forum_ids, settings,
                                  cfg["llm"]["max_input_chars"])
    log.info("tables built in %.0f s: %s (graph of the study: %s)", time.time() - start,
             {t: len(table) for t, table in tables.nodes.items()}, {t: len(table) for t, table in base.nodes.items()})

    # ---- embeddings: the texts of the study come from the cache
    model = settings["text_model"]
    encode = embed.sentence_encoder(model, "cuda" if torch.cuda.is_available() else "cpu")
    directory = cfg["paths"]["interim"] / "kg"
    cache = embed.EmbeddingCache(directory / embed.cache_name(model["name"], model["revision"]))
    embeddings = {"article": article_embeddings(directory, tables.nodes["article"], ("article_specter2", holdout["article_vectors"]))}
    texts = texts_to_encode(tables)
    for kind in ("concept", "critique", "review"):
        start = time.time()
        vectors, encoded = cache.embed(texts[kind], encode)
        if kind == "review":
            vectors = embed.mean_of_chunks(vectors, [len(chunks) for chunks in tables.nodes["review"]["chunks"]])
        embeddings[kind] = vectors
        log.info("embeddings %s: %d texts, %d sent to the model, %.0f s", kind, len(texts[kind]), encoded, time.time() - start)

    # ---- graph, checked against the graph of the study before it is written
    graph, layout = build.build_graph(tables, embeddings)
    reference = torch.load(processed / f"graph_{SETTING}.pt", weights_only=False)
    reference_layout = json.loads((processed / "graph_features.json").read_text(encoding="utf-8"))[SETTING]
    problems = same_prefix(graph, reference) + ([] if layout == reference_layout else ["feature layout"])
    if problems:
        raise SystemExit(f"the extended graph does not hold the graph of the study unchanged: {problems}")
    log.info("the part of the extended graph that belongs to the study is identical to graph_%s.pt", SETTING)
    targets = kg_tables.targets(tables.nodes["article"], views.load_labels(cfg, "excluded"), labels)
    old_targets = pd.read_parquet(processed / "targets.parquet")
    if not targets.iloc[:len(old_targets)].equals(old_targets):
        raise SystemExit("the targets of the articles of the study changed")
    if set(targets["split"].iloc[len(old_targets):]) != {"holdout"}:
        raise SystemExit("an added article is not in the holdout split")
    torch.save(graph, out_dir / f"graph_{SETTING}.pt")
    (out_dir / "graph_features.json").write_text(json.dumps({SETTING: layout}, indent=1), encoding="utf-8")
    for node_type, columns in ID_COLUMNS.items():
        tables.nodes[node_type][columns].to_parquet(out_dir / f"nodes_{node_type}.parquet", index=False)
    targets.to_parquet(out_dir / "targets.parquet", index=False)
    log.info("graph: %s", graph)

    # ---- tables
    statistics = build.statistics(tables, SETTING)
    n_base, (sources, targets_) = len(base.nodes["article"]), tables.edges[kg_tables.SHARES_CONCEPT]
    new_source, new_target = sources >= n_base, targets_ >= n_base
    pairs = {"both of the study": int((~new_source & ~new_target).sum()) // 2, "one of the study, one added": int((new_source & ~new_target).sum()),
             "both added": int((new_source & new_target).sum()) // 2}
    statistics = pd.concat([statistics, pd.DataFrame([{"setting": SETTING, "kind": "shares_concept pairs", "type": name, "count": count}
                                                      for name, count in pairs.items()])], ignore_index=True)
    for column in statistics.columns[statistics.columns.str.startswith("count")]:
        statistics[column] = statistics[column].astype("Int64")
    statistics.to_csv(tables_dir / "kg_statistics_holdout.csv", index=False)
    coverage = extend.concept_coverage(tables, settings["concepts"]["max_articles_for_shared"])
    coverage.to_csv(tables_dir / "kg_concept_coverage_holdout.csv", index=False)
    # reviews whose kept text still mentions the rebuttal (`modified_after_release` is read for this report only)
    final = pd.read_parquet(cfg["paths"]["interim"] / "reviews_final.parquet", columns=["review_id", "modified_after_release"])
    reviews = tables.nodes["review"][["review_id", "year", "post_rebuttal_marker_left"]].merge(final, on="review_id", how="left")
    markers = reviews.groupby(["year", "modified_after_release"]).agg(
        reviews=("review_id", "size"), reviews_with_a_marker_left=("post_rebuttal_marker_left", "sum")).reset_index()
    markers["share_with_a_marker_left"] = (markers["reviews_with_a_marker_left"] / markers["reviews"]).round(4)
    markers.to_csv(tables_dir / "kg_post_rebuttal_markers_holdout.csv", index=False)
    articles = tables.nodes["article"]
    (out_dir / "graph.stats.md").write_text("\n".join([
        f"# Knowledge graph of setting {SETTING} with the holdout years", "",
        f"`graph_{SETTING}.pt`: the graph of the study with the articles of {cfg['splits']['holdout']} appended (critiques of run "
        f"`{holdout['run']}`). No outcome inside: see `targets.parquet`.", "",
        f"- articles: {len(articles)}, of which {int((~articles['text_available']).sum())} without text before the decisions",
        f"- targets: {targets['split'].value_counts().to_dict()}; with a decision (withdrawn excluded): {int(targets['label'].notna().sum())}",
        "- nodes and edges by type: `results/tables/kg_statistics_holdout.csv`", "",
    ]), encoding="utf-8")
    log.info("statistics\n%s", statistics.to_string(index=False))
    log.info("concepts\n%s", coverage.to_string(index=False))
    log.info("post-rebuttal markers left\n%s", markers.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
