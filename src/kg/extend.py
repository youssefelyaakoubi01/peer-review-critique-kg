"""A graph of setting A extended with the articles of a later year.

The nodes and edges of the base graph are kept as they are, in the same order; the new
articles, their reviews and their critiques are appended after them. The vocabulary of
concepts is frozen: a new article is linked to the concepts that already exist, and no
concept is added. The part of the extended graph that belongs to the base years is
therefore the base graph itself, apart from the edges that reach the new articles.
"""

from typing import Any

import numpy as np
import pandas as pd
from scipy import sparse

from src.kg import text as kg_text
from src.kg.tables import (ABOUT, CONTAINS, HAS_CONCEPT, HAS_REVIEW, SHARES_CONCEPT, GraphTables, article_nodes, critique_nodes,
                           link, positions, review_nodes)


def shared_concepts_with_new(article_index: np.ndarray, concept_index: np.ndarray, n_base: int, n_articles: int,
                             eligible: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pairs of articles (i < j, j a new article) that share at least one eligible
    concept, with the number of eligible concepts they share. `eligible`: one flag per
    concept, decided on the base graph."""
    usable = eligible[concept_index]
    incidence = sparse.csr_matrix(
        (np.ones(int(usable.sum()), dtype=np.int32), (article_index[usable], concept_index[usable])),
        shape=(n_articles, len(eligible)))
    common = sparse.triu(incidence @ incidence[n_base:].T, k=1 - n_base).tocoo()  # columns: new articles; i < j
    return common.row.astype(np.int64), common.col.astype(np.int64) + n_base, common.data.astype(np.float32)


def extend_tables(base: GraphTables, papers_initial: pd.DataFrame, reviews: pd.DataFrame, critiques: pd.DataFrame,
                  audit: pd.DataFrame, forum_ids: set[str], settings: dict[str, Any], max_chars: int) -> GraphTables:
    """Tables of setting A with the usable papers `forum_ids` of a later year appended.

    `base`: tables of setting A (no author response). `reviews`: the model-input view of
    setting A; `critiques`, `audit`: extraction run of the new year. `settings`: the
    `kg` section of the config.
    """
    if "response" in base.nodes:
        raise ValueError("only a graph of setting A can be extended")
    old = base.nodes
    if forum_ids & set(old["article"]["forum_id"]):
        raise ValueError("a paper to add is already in the graph")
    articles = article_nodes(papers_initial, forum_ids)
    review_table = review_nodes(reviews, audit, forum_ids, max_chars, settings["review_chunk_chars"])
    critique_table = critique_nodes(critiques, set(review_table["review_id"]))
    nodes = {**old, "article": pd.concat([old["article"], articles], ignore_index=True),
             "review": pd.concat([old["review"], review_table], ignore_index=True),
             "critique": pd.concat([old["critique"], critique_table], ignore_index=True)}
    for node_type, key in (("article", "forum_id"), ("review", "review_id"), ("critique", "critique_id")):
        if nodes[node_type][key].duplicated().any():
            raise ValueError(f"a {node_type} appears twice in the extended graph")

    index = {"article": positions(nodes["article"]["forum_id"]), "review": positions(nodes["review"]["review_id"]),
             "critique": positions(nodes["critique"]["critique_id"]), "aspect": positions(old["aspect"]["aspect"]),
             "concept": positions(old["concept"]["concept"])}
    # concepts of the new articles: the existing ones only
    pairs = pd.DataFrame(
        [(forum_id, concept) for forum_id, keywords in zip(articles["forum_id"], articles["keywords"])
         for concept in kg_text.concepts_of(keywords) if concept in index["concept"]], columns=["forum_id", "concept"])
    typed = critique_table[critique_table["aspect"].notna()]
    added = {
        HAS_REVIEW: link(review_table["forum_id"], index["article"], review_table["review_id"], index["review"]),
        CONTAINS: link(critique_table["review_id"], index["review"], critique_table["critique_id"], index["critique"]),
        ABOUT: link(typed["critique_id"], index["critique"], typed["aspect"], index["aspect"]),
        HAS_CONCEPT: link(pairs["forum_id"], index["article"], pairs["concept"], index["concept"]),
    }
    edges = {relation: tuple(np.concatenate([base.edges[relation][side], added[relation][side]]) for side in (0, 1))
             for relation in added}

    # shares_concept: through the concepts that carry this relation in the base graph
    # (their number of articles there is at most `max_articles_for_shared`)
    eligible = old["concept"]["n_articles"].to_numpy() <= settings["concepts"]["max_articles_for_shared"]
    first, second, weight = shared_concepts_with_new(*edges[HAS_CONCEPT], len(old["article"]), len(nodes["article"]), eligible)
    sources, targets = base.edges[SHARES_CONCEPT]
    edges[SHARES_CONCEPT] = (np.concatenate([sources, first, second]), np.concatenate([targets, second, first]))  # both directions
    weights = {SHARES_CONCEPT: np.concatenate([base.edge_weights[SHARES_CONCEPT], weight, weight])}
    return GraphTables(nodes, edges, weights)


def concept_coverage(tables: GraphTables, eligible_max: int) -> pd.DataFrame:
    """Per year: articles, their keywords and how many of them are concepts of the
    graph, articles linked to a concept, articles with a shares_concept neighbour."""
    articles, vocabulary = tables.nodes["article"], set(tables.nodes["concept"]["concept"])
    keywords = articles["keywords"].map(kg_text.concepts_of)
    sources, _ = tables.edges[HAS_CONCEPT]
    linked = np.bincount(sources, minlength=len(articles))
    neighbours = np.bincount(tables.edges[SHARES_CONCEPT][0], minlength=len(articles))
    frame = pd.DataFrame({"year": articles["year"], "keywords": keywords.map(len),
                          "keywords_in_vocabulary": keywords.map(lambda found: sum(k in vocabulary for k in found)),
                          "concepts": linked, "neighbours": neighbours})
    grouped = frame.groupby("year")
    out = grouped.agg(articles=("year", "size"), keywords=("keywords", "sum"), keywords_in_vocabulary=("keywords_in_vocabulary", "sum"),
                      mean_concepts=("concepts", "mean"), mean_shares_concept_neighbours=("neighbours", "mean"),
                      median_shares_concept_neighbours=("neighbours", "median")).reset_index()
    out["share_keywords_in_vocabulary"] = out["keywords_in_vocabulary"] / out["keywords"]
    out["share_articles_with_a_concept"] = grouped["concepts"].apply(lambda column: (column > 0).mean()).to_numpy()
    out["share_articles_with_a_neighbour"] = grouped["neighbours"].apply(lambda column: (column > 0).mean()).to_numpy()
    out["concepts_carrying_shares_concept"] = int((tables.nodes["concept"]["n_articles"] <= eligible_max).sum())
    return out.round(4)
