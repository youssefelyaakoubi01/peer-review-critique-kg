"""Node and edge tables of the knowledge graph, built from the cleaned tables.

Everything here is a model input. Outcomes are never read: the list of usable papers
is given by the caller, and the targets live in a separate file (`targets`).

Nodes: article, review, critique, response, aspect, concept. An edge table is a pair
of integer arrays (source index, target index) into the node tables.
"""

from dataclasses import dataclass, field
from typing import Any, get_args

import numpy as np
import pandas as pd
from scipy import sparse

from src.kg import text as kg_text
from src.llm import steps
from src.llm.schemas import NO_RESPONSE, AnswerType, Aspect, Polarity, Severity, Target

ASPECTS = get_args(Aspect)
CRITIQUE_LABELS = {"aspect": ASPECTS, "severity": get_args(Severity), "polarity": get_args(Polarity),
                   "target": get_args(Target)}
RESPONSE_TYPES = get_args(AnswerType)
REVIEW_SCORES = ("rating_initial", "confidence_initial", "soundness_initial", "contribution_initial")

# (source node type, relation, target node type)
HAS_REVIEW = ("article", "has_review", "review")
CONTAINS = ("review", "contains", "critique")
ABOUT = ("critique", "about", "aspect")
HAS_CONCEPT = ("article", "has_concept", "concept")
SHARES_CONCEPT = ("article", "shares_concept", "article")
RESPONDS_TO = ("response", "responds_to", "critique")
SETTING_B_ONLY = {"nodes": ("response",), "edges": (RESPONDS_TO,)}


@dataclass
class GraphTables:
    nodes: dict[str, pd.DataFrame]
    edges: dict[tuple[str, str, str], tuple[np.ndarray, np.ndarray]]
    edge_weights: dict[tuple[str, str, str], np.ndarray] = field(default_factory=dict)

    def setting(self, name: str) -> "GraphTables":
        """Tables of setting A (no author response) or B (everything)."""
        if name == "B":
            return self
        if name != "A":
            raise ValueError(f"unknown setting {name!r}")
        return GraphTables(
            {t: table for t, table in self.nodes.items() if t not in SETTING_B_ONLY["nodes"]},
            {r: e for r, e in self.edges.items() if r not in SETTING_B_ONLY["edges"]},
            dict(self.edge_weights),
        )


def positions(ids: pd.Series) -> dict[Any, int]:
    return {value: index for index, value in enumerate(ids)}


def link(sources: pd.Series, source_index: dict, targets: pd.Series, target_index: dict) -> tuple[np.ndarray, np.ndarray]:
    return (sources.map(source_index).to_numpy(dtype=np.int64), targets.map(target_index).to_numpy(dtype=np.int64))


# --------------------------------------------------------------------------- nodes
def article_nodes(papers_initial: pd.DataFrame, forum_ids: set[str]) -> pd.DataFrame:
    """Usable papers with their text before the decisions (missing for some)."""
    articles = papers_initial[papers_initial["forum_id"].isin(forum_ids)].sort_values("forum_id")
    if len(articles) != len(forum_ids):
        raise ValueError(f"{len(forum_ids) - len(articles)} usable papers are missing from papers_initial")
    columns = ["forum_id", "year", "title", "abstract", "keywords", "text_available"]
    return articles[columns].reset_index(drop=True)


def review_nodes(reviews: pd.DataFrame, audit: pd.DataFrame, forum_ids: set[str], max_chars: int,
                 chunk_chars: int) -> pd.DataFrame:
    """Initial reviews of the usable papers: initial scores and the chunks of their text.

    The text is made of the fields read by the LLM (strengths, weaknesses, questions)
    without the sentences it set aside as written after the author response. The
    summary of the paper is not used: nothing screened it for later additions.
    """
    reviews = reviews[reviews["forum_id"].isin(forum_ids)].sort_values("review_id").reset_index(drop=True)
    set_aside = {row.review_id: set(row.post_rebuttal_units) for row in audit.itertuples()}
    chunks, markers = [], []
    for review in reviews.to_dict("records"):
        units = kg_text.kept_units(steps.review_units(review, max_chars)[0], set_aside.get(review["review_id"], set()))
        pieces = kg_text.chunks(units, chunk_chars)
        chunks.append(pieces)
        markers.append(any(kg_text.has_post_rebuttal_marker(piece) for piece in pieces))
    nodes = reviews[["review_id", "forum_id", "year", *REVIEW_SCORES]].copy()
    nodes["chunks"] = chunks
    nodes["post_rebuttal_marker_left"] = markers  # for the residual-risk table, not a feature
    return nodes


def critique_nodes(critiques: pd.DataFrame, review_ids: set[str]) -> pd.DataFrame:
    critiques = critiques[critiques["review_id"].isin(review_ids)].sort_values(["review_id", "critique_index"])
    columns = ["critique_id", "review_id", "year", "text", *CRITIQUE_LABELS, "actionable"]
    return critiques[columns].reset_index(drop=True)


def response_nodes(responses: pd.DataFrame, critique_ids: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(response nodes, response-critique links). A response is one passage (block) of
    the author reply to a review; it can answer several critiques."""
    answered = responses[(responses["response_type"] != NO_RESPONSE) & responses["critique_id"].isin(critique_ids)].copy()
    answered["response_id"] = answered["review_id"] + ":r" + answered["block_index"].astype(int).astype(str)
    nodes = answered.groupby("response_id", sort=True).agg(
        review_id=("review_id", "first"), year=("year", "first"), text=("response_text", "first"),
        response_type=("response_type", "first"), n_texts=("response_text", "nunique"),
        n_types=("response_type", "nunique")).reset_index()
    if (nodes["n_texts"] > 1).any() or (nodes["n_types"] > 1).any():
        raise ValueError("a response block has several texts or several types")
    return nodes.drop(columns=["n_texts", "n_types"]), answered[["response_id", "critique_id"]]


def concept_nodes(articles: pd.DataFrame, min_articles: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(concept nodes, article-concept links): normalised keywords used by at least
    `min_articles` articles."""
    pairs = pd.DataFrame(
        [(forum_id, concept) for forum_id, keywords in zip(articles["forum_id"], articles["keywords"])
         for concept in kg_text.concepts_of(keywords)], columns=["forum_id", "concept"])
    counts = pairs["concept"].value_counts()
    kept = counts[counts >= min_articles]
    nodes = pd.DataFrame({"concept": sorted(kept.index)})
    nodes["n_articles"] = nodes["concept"].map(kept).astype(int)
    return nodes, pairs[pairs["concept"].isin(kept.index)].reset_index(drop=True)


def shared_concepts(article_index: np.ndarray, concept_index: np.ndarray, n_articles: int, concept_sizes: np.ndarray,
                    max_articles: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pairs of articles (i < j) that share at least one concept used by at most
    `max_articles` articles, with the number of such concepts they share."""
    usable = concept_sizes[concept_index] <= max_articles
    incidence = sparse.csr_matrix(
        (np.ones(int(usable.sum()), dtype=np.int32), (article_index[usable], concept_index[usable])),
        shape=(n_articles, len(concept_sizes)))
    common = sparse.triu(incidence @ incidence.T, k=1).tocoo()
    return common.row.astype(np.int64), common.col.astype(np.int64), common.data.astype(np.float32)


# --------------------------------------------------------------------------- whole graph
def build_tables(
    papers_initial: pd.DataFrame, reviews: pd.DataFrame, critiques: pd.DataFrame, responses: pd.DataFrame,
    audit: pd.DataFrame, forum_ids: set[str], settings: dict[str, Any], max_chars: int,
) -> GraphTables:
    """Tables of setting B; `GraphTables.setting("A")` drops the author responses.

    `reviews` must be the model-input view of setting A (reviews posted before the
    author response, initial scores). `settings`: the `kg` section of the config.
    """
    articles = article_nodes(papers_initial, forum_ids)
    review_table = review_nodes(reviews, audit, forum_ids, max_chars, settings["review_chunk_chars"])
    critique_table = critique_nodes(critiques, set(review_table["review_id"]))
    response_table, response_links = response_nodes(responses, set(critique_table["critique_id"]))
    concept_table, concept_links = concept_nodes(articles, settings["concepts"]["min_articles"])
    aspects = pd.DataFrame({"aspect": list(ASPECTS)})

    index = {"article": positions(articles["forum_id"]), "review": positions(review_table["review_id"]),
             "critique": positions(critique_table["critique_id"]), "response": positions(response_table["response_id"]),
             "aspect": positions(aspects["aspect"]), "concept": positions(concept_table["concept"])}
    typed = critique_table[critique_table["aspect"].notna()]
    has_concept = link(concept_links["forum_id"], index["article"], concept_links["concept"], index["concept"])
    first, second, weight = shared_concepts(
        has_concept[0], has_concept[1], len(articles), concept_table["n_articles"].to_numpy(),
        settings["concepts"]["max_articles_for_shared"])
    edges = {
        HAS_REVIEW: link(review_table["forum_id"], index["article"], review_table["review_id"], index["review"]),
        CONTAINS: link(critique_table["review_id"], index["review"], critique_table["critique_id"], index["critique"]),
        ABOUT: link(typed["critique_id"], index["critique"], typed["aspect"], index["aspect"]),
        HAS_CONCEPT: has_concept,
        # symmetric relation: stored in both directions
        SHARES_CONCEPT: (np.concatenate([first, second]), np.concatenate([second, first])),
        RESPONDS_TO: link(response_links["response_id"], index["response"], response_links["critique_id"], index["critique"]),
    }
    nodes = {"article": articles, "review": review_table, "critique": critique_table, "response": response_table,
             "aspect": aspects, "concept": concept_table}
    return GraphTables(nodes, edges, {SHARES_CONCEPT: np.concatenate([weight, weight])})


def targets(articles: pd.DataFrame, labels_excluded: pd.DataFrame, labels_as_reject: pd.DataFrame) -> pd.DataFrame:
    """Outcome and split of each article, in the order of the article nodes. Kept out
    of the graph: a model is given these only as targets.

    `label`: decision with withdrawn papers left out (missing for them);
    `label_withdrawn_as_reject`: withdrawn papers counted as rejections.
    """
    table = articles[["forum_id", "year"]].copy()
    table.insert(0, "article_index", np.arange(len(table)))
    wide = labels_as_reject.set_index("forum_id")
    table["split"] = table["forum_id"].map(wide["split"])
    table["label_withdrawn_as_reject"] = table["forum_id"].map(wide["label"]).astype("Int64")
    table["label"] = table["forum_id"].map(labels_excluded.set_index("forum_id")["label"]).astype("Int64")
    if table["split"].isna().any():
        raise ValueError("an article of the graph has no split")
    return table
