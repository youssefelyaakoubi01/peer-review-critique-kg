"""Model features read from a processed graph.

Two views of the same graph:
  - one row per article, for the models that do not use the graph: statistics of the
    initial scores of its reviews, mean embedding of its reviews, its own embedding,
    counts of the critiques of its reviews by label;
  - the graph itself, standardised, and its flattened (homogeneous) form.

Scaling statistics always come from the training articles (and the nodes that belong
to them), never from validation or test papers. Every continuous column is centred and
scaled to unit variance; the columns of an embedding are then divided by the square
root of their number, so that a whole embedding weighs as much as one score. Without
this, the hundreds of text columns drown the few score columns (first run of phase 6).
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from scipy import sparse
from torch_geometric.data import HeteroData
from torch_geometric.utils import subgraph

from src.kg.build import article_masks, member_of
from src.kg.tables import CONTAINS, CRITIQUE_LABELS, HAS_CONCEPT, HAS_REVIEW, REVIEW_SCORES

Layout = dict[str, list[dict]]

# Blocks of 0/1 columns: never rescaled.
BINARY_BLOCKS = {"text_missing", "aspect", "severity", "polarity", "target", "actionable", "identity", "response_type"}
# Text embeddings share the same columns in the flattened graph, whatever the node type.
TEXT_BLOCKS = {"specter2", "text"}
SCORE_STATISTICS = ("mean", "min", "max", "std")
# Blocks of the article table that hold an embedding (its columns; the last column of
# `article_text` is the text-missing flag).
EMBEDDINGS = {"review_text": slice(None), "article_text": slice(None, -1)}


def columns(layout: Layout, node_type: str, name: str) -> slice:
    for block in layout[node_type]:
        if block["name"] == name:
            return slice(block["start"], block["end"])
    raise KeyError(f"no block '{name}' in the features of '{node_type}'")


def fit_scaler(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(mean, standard deviation) of each column; a constant column is left unscaled."""
    mean, std = x.mean(axis=0), x.std(axis=0)
    return mean, np.where(std > 0, std, 1.0)


# --------------------------------------------------------------------------- one row per article
@dataclass
class ArticleTable:
    blocks: dict[str, np.ndarray]      # raw features, one row per article node
    names: dict[str, list[str]]        # column names of each block
    mean_rating: np.ndarray            # mean initial rating (defines the borderline zone)
    text_available: np.ndarray         # False: no text of the article from before the decisions

    def design(self, blocks: list[str], train_rows: np.ndarray) -> np.ndarray:
        """Matrix of the chosen blocks, each column centred and scaled with the training
        rows, embeddings brought to a total variance of one. The embedding of an article
        without text stays at zero, the training mean."""
        parts = []
        for name in blocks:
            x = self.blocks[name]
            mean, std = fit_scaler(x[train_rows])
            scaled = ((x - mean) / std).astype(np.float32)
            if name == "article_text":
                scaled[~self.text_available, :-1] = 0.0  # last column: the text-missing flag
            if name in EMBEDDINGS:
                scaled[:, EMBEDDINGS[name]] /= np.sqrt(scaled[:, EMBEDDINGS[name]].shape[1])
            parts.append(scaled)
        return np.concatenate(parts, axis=1)


def critique_counts(graph: HeteroData, layout: Layout, articles: np.ndarray, reviews: np.ndarray,
                    mean_of_reviews: sparse.csr_matrix) -> tuple[dict[str, np.ndarray], dict[str, list[str]]]:
    """Counts of critiques by label, per article (blocks, column names).

    The critiques of each review are counted in every cell; an article gets the mean of
    its reviews (a review without critique counts zero), and for three cells the count
    of its most extreme review.
      critique_marginals        number of critiques; by aspect, severity, polarity, target; actionable
      critique_aspect_severity  negative critiques by aspect x severity; positive critiques by aspect
      critique_worst_review     most negative blocking / negative major critiques in one review,
                                fewest positive critiques in one review
    """
    owners, critiques = graph[CONTAINS].edge_index.numpy()
    n_reviews, n_critiques = graph["review"].num_nodes, graph["critique"].num_nodes
    if len(np.unique(critiques)) != len(critiques):
        raise ValueError("a critique is attached to several reviews")
    x = graph["critique"].x
    one_hot = {label: x[:, columns(layout, "critique", label)].numpy().astype(np.float64) for label in CRITIQUE_LABELS}
    actionable = x[:, columns(layout, "critique", "actionable")].numpy().astype(np.float64)
    polarity = {name: one_hot["polarity"][:, [i]] for i, name in enumerate(CRITIQUE_LABELS["polarity"])}
    aspects, severities = CRITIQUE_LABELS["aspect"], CRITIQUE_LABELS["severity"]
    negative_cells = (polarity["negative"] * one_hot["aspect"])[:, :, None] * one_hot["severity"][:, None, :]

    per_critique = {
        "critique_marginals": np.concatenate([np.ones((n_critiques, 1)), *one_hot.values(), actionable], axis=1),
        "critique_aspect_severity": np.concatenate([negative_cells.reshape(n_critiques, -1), polarity["positive"] * one_hot["aspect"]], axis=1),
    }
    names = {
        "critique_marginals": ["critiques_per_review", *[f"critique_{label}_{value}" for label, values in CRITIQUE_LABELS.items() for value in values],
                               "critique_actionable"],
        "critique_aspect_severity": [f"critique_negative_{aspect}_{severity}" for aspect in aspects for severity in severities]
        + [f"critique_positive_{aspect}" for aspect in aspects],
        "critique_worst_review": [*[f"critique_negative_{severity}_max" for severity in ("blocking", "major")], "critique_positive_min"],
    }
    sum_of_critiques = sparse.csr_matrix((np.ones(len(critiques)), (owners, critiques)), shape=(n_reviews, n_critiques))
    blocks = {name: np.asarray(mean_of_reviews @ (sum_of_critiques @ values), dtype=np.float32) for name, values in per_critique.items()}

    severity = {name: one_hot["severity"][:, [i]] for i, name in enumerate(severities)}
    extremes = np.concatenate([polarity["negative"] * severity["blocking"], polarity["negative"] * severity["major"], polarity["positive"]], axis=1)
    grouped = pd.DataFrame((sum_of_critiques @ extremes)[reviews]).groupby(articles)
    worst = pd.concat([grouped[[0, 1]].max(), grouped[[2]].min()], axis=1).reindex(range(mean_of_reviews.shape[0]))
    blocks["critique_worst_review"] = worst.to_numpy(dtype=np.float32)
    return blocks, names


def article_table(graph: HeteroData, layout: Layout) -> ArticleTable:
    """Features of each article computed from its own node and its review nodes."""
    articles, reviews = graph[HAS_REVIEW].edge_index.numpy()
    n_articles, n_reviews = graph["article"].num_nodes, graph["review"].num_nodes
    if len(np.unique(reviews)) != len(reviews):
        raise ValueError("a review is attached to several articles")
    review_x = graph["review"].x.numpy()

    scores = pd.DataFrame({score: review_x[reviews, columns(layout, "review", score)].ravel() for score in REVIEW_SCORES})
    grouped = scores.groupby(articles)
    statistics = {"mean": grouped.mean(), "min": grouped.min(), "max": grouped.max(), "std": grouped.std(ddof=0)}
    count = grouped.size().reindex(range(n_articles), fill_value=0)
    if (count == 0).any():
        raise ValueError(f"{int((count == 0).sum())} articles have no review")

    def block(score_names: tuple[str, ...]) -> tuple[np.ndarray, list[str]]:
        names = [f"{score}_{statistic}" for score in score_names for statistic in SCORE_STATISTICS]
        values = [statistics[statistic][score].reindex(range(n_articles)) for score in score_names for statistic in SCORE_STATISTICS]
        return np.stack(values, axis=1).astype(np.float32), names

    rating, rating_names = block(REVIEW_SCORES[:1])
    others, other_names = block(REVIEW_SCORES[1:])
    others = np.concatenate([others, count.to_numpy(dtype=np.float32)[:, None]], axis=1)

    weights = 1.0 / count.to_numpy(dtype=np.float64)[articles]
    mean_of_reviews = sparse.csr_matrix((weights, (articles, reviews)), shape=(n_articles, n_reviews))
    text = columns(layout, "review", "text")
    review_text = np.asarray(mean_of_reviews @ review_x[:, text], dtype=np.float32)

    article_x = graph["article"].x.numpy()
    missing = article_x[:, columns(layout, "article", "text_missing")].ravel() == 1
    width = text.stop - text.start
    critique_blocks, critique_names = critique_counts(graph, layout, articles, reviews, mean_of_reviews)
    return ArticleTable(
        blocks={"rating": rating, "other_scores": others, "review_text": review_text, "article_text": article_x, **critique_blocks},
        names={"rating": rating_names, "other_scores": [*other_names, "n_reviews"],
               "review_text": [f"review_text_{i}" for i in range(width)],
               "article_text": [f"article_text_{i}" for i in range(article_x.shape[1] - 1)] + ["text_missing"], **critique_names},
        mean_rating=rating[:, 0].astype(np.float64), text_available=~missing)


# --------------------------------------------------------------------------- the graph
def training_nodes(graph: HeteroData, train_articles: torch.Tensor) -> dict[str, torch.Tensor]:
    """Nodes whose features may be used to fit the scaling: the training articles, what
    belongs to them, the concepts they use, and the aspects."""
    masks = article_masks(graph, train_articles)
    masks["concept"] = member_of(train_articles, graph[HAS_CONCEPT].edge_index, graph["concept"].num_nodes)
    return masks


def standardise(graph: HeteroData, layout: Layout, fit_on: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    """Features of each node type with every continuous column centred and scaled by
    the statistics of the nodes in `fit_on`, embeddings brought to a total variance of
    one. Binary blocks are unchanged. A row of zeros in an embedding block means "no
    text": it is left out of the statistics and stays at zero."""
    out = {}
    for node_type in graph.node_types:
        x = graph[node_type].x.clone()
        for block in layout[node_type]:
            if block["name"] in BINARY_BLOCKS:
                continue
            part = x[:, block["start"]:block["end"]]
            empty = ~part.any(dim=1) if part.shape[1] > 1 else torch.zeros(len(part), dtype=torch.bool)
            reference = part[fit_on[node_type] & ~empty]
            if len(reference) == 0:
                raise ValueError(f"no training node to scale '{block['name']}' of '{node_type}'")
            mean, std = reference.mean(dim=0), reference.std(dim=0, correction=0)
            scaled = (part - mean) / torch.where(std > 0, std, torch.ones_like(std))
            scaled[empty] = 0.0
            if block["name"] in TEXT_BLOCKS:
                scaled = scaled / part.shape[1] ** 0.5
            x[:, block["start"]:block["end"]] = scaled
        out[node_type] = x
    return out


@dataclass
class FlatGraph:
    """Homogeneous form of a graph: one feature space, one kind of edge."""
    x: torch.Tensor
    edge_index: torch.Tensor
    offsets: dict[str, int]            # index of the first node of each type
    sizes: dict[str, int]
    columns: list[dict]                # blocks of the common feature space

    def nodes(self, node_type: str, index: torch.Tensor) -> torch.Tensor:
        return index + self.offsets[node_type]


def flatten(graph: HeteroData, x: dict[str, torch.Tensor], layout: Layout) -> FlatGraph:
    """All nodes in one feature space (text embeddings share their columns, every other
    block has its own, the rest is zero) and all relations merged into one edge set,
    without relation type and without weight."""
    widths: dict[str, int] = {}
    for node_type in graph.node_types:
        for block in layout[node_type]:
            name = "text" if block["name"] in TEXT_BLOCKS else block["name"]
            if widths.setdefault(name, block["end"] - block["start"]) != block["end"] - block["start"]:
                raise ValueError(f"block '{name}' has different widths across node types")
    common, start = {}, 0
    for name in ["text"] + [name for name in widths if name != "text"]:
        common[name] = {"start": start, "end": start + widths[name]}
        start += widths[name]

    offsets, sizes, total = {}, {}, 0
    for node_type in graph.node_types:
        offsets[node_type], sizes[node_type] = total, graph[node_type].num_nodes
        total += sizes[node_type]
    flat = torch.zeros((total, start), dtype=torch.float32)
    for node_type in graph.node_types:
        rows = slice(offsets[node_type], offsets[node_type] + sizes[node_type])
        for block in layout[node_type]:
            target = common["text" if block["name"] in TEXT_BLOCKS else block["name"]]
            flat[rows, target["start"]:target["end"]] = x[node_type][:, block["start"]:block["end"]]
    edges = [graph[edge_type].edge_index + torch.tensor([[offsets[edge_type[0]]], [offsets[edge_type[2]]]])
             for edge_type in graph.edge_types]
    return FlatGraph(flat, torch.cat(edges, dim=1), offsets, sizes,
                     [{"name": name, "start": b["start"], "end": b["end"]} for name, b in common.items()])


def flat_mask(flat: FlatGraph, masks: dict[str, torch.Tensor]) -> torch.Tensor:
    """Mask over the nodes of the flattened graph from one mask per node type."""
    return torch.cat([masks[node_type] for node_type in flat.offsets])


def flat_subgraph(flat: FlatGraph, keep: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """(features, edges, new index of each kept node) of the nodes in `keep`."""
    edge_index, _ = subgraph(keep, flat.edge_index, relabel_nodes=True, num_nodes=len(keep))
    new_index = torch.full((len(keep),), -1, dtype=torch.long)
    new_index[keep] = torch.arange(int(keep.sum()))
    return flat.x[keep], edge_index, new_index
