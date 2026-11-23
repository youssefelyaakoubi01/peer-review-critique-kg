"""RDF export of the knowledge graph (Turtle, written with rdflib).

The export describes setting B (setting A is the same graph without the Response
resources). It holds the structure, the initial scores, the labels of the critiques and
public texts. It holds no decision, no author and no reviewer identifier.

The file is written chunk by chunk (a group of articles with everything attached to
them), so that the whole graph is never held in memory as triples. Each chunk is a
complete Turtle document; their concatenation is one too.

Inverse relations are declared once in the vocabulary (owl:inverseOf) instead of being
written for every edge.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import IO

import pandas as pd
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from src.kg.tables import (ABOUT, CONTAINS, HAS_CONCEPT, HAS_REVIEW, RESPONDS_TO, REVIEW_SCORES, SHARES_CONCEPT,
                           GraphTables)

CLASSES = ("Article", "Review", "Critique", "Response", "Aspect", "Concept")
RELATIONS = {"hasReview": ("reviewOf", "Article", "Review"), "contains": ("partOf", "Review", "Critique"),
             "respondsTo": ("answeredBy", "Response", "Critique"), "about": ("aspectOf", "Critique", "Aspect"),
             "hasConcept": ("conceptOf", "Article", "Concept")}
SCORE_PROPERTIES = {"rating_initial": "initialRating", "confidence_initial": "initialConfidence",
                    "soundness_initial": "initialSoundness", "contribution_initial": "initialContribution"}


class Vocabulary:
    def __init__(self, base_iri: str):
        self.ns = Namespace(base_iri + "vocab#")
        self.base = base_iri

    def resource(self, kind: str, identifier: str) -> URIRef:
        return URIRef(f"{self.base}{kind}/{identifier.replace(' ', '_').replace(':', '-')}")

    def new_graph(self) -> Graph:
        graph = Graph()
        graph.bind("prkg", self.ns)
        graph.bind("dcterms", DCTERMS)
        return graph

    def header(self) -> Graph:
        """Classes and properties of the vocabulary."""
        graph = self.new_graph()
        graph.bind("owl", OWL)
        for name in CLASSES:
            graph.add((self.ns[name], RDF.type, OWL.Class))
        for name, (inverse, domain, range_) in RELATIONS.items():
            graph.add((self.ns[name], RDF.type, OWL.ObjectProperty))
            graph.add((self.ns[name], RDFS.domain, self.ns[domain]))
            graph.add((self.ns[name], RDFS.range, self.ns[range_]))
            graph.add((self.ns[inverse], RDF.type, OWL.ObjectProperty))
            graph.add((self.ns[inverse], OWL.inverseOf, self.ns[name]))
        graph.add((self.ns.sharesConcept, RDF.type, OWL.SymmetricProperty))
        graph.add((self.ns.sharesConcept, RDFS.domain, self.ns.Article))
        graph.add((self.ns.sharesConcept, RDFS.range, self.ns.Article))
        return graph


def grouped(edges: tuple, n_sources: int) -> list[list[int]]:
    """Targets of each source node."""
    out: list[list[int]] = [[] for _ in range(n_sources)]
    for source, target in zip(*edges):
        out[source].append(int(target))
    return out


def fixed_resources(tables: GraphTables, vocabulary: Vocabulary) -> Graph:
    """Aspects and concepts (they belong to no article in particular)."""
    graph, ns = vocabulary.new_graph(), vocabulary.ns
    for aspect in tables.nodes["aspect"]["aspect"]:
        node = vocabulary.resource("aspect", aspect)
        graph.add((node, RDF.type, ns.Aspect))
        graph.add((node, RDFS.label, Literal(aspect)))
    for concept in tables.nodes["concept"]["concept"]:
        node = vocabulary.resource("concept", concept)
        graph.add((node, RDF.type, ns.Concept))
        graph.add((node, RDFS.label, Literal(concept)))
    return graph


def article_chunks(tables: GraphTables, vocabulary: Vocabulary, articles_per_chunk: int) -> Iterator[Graph]:
    """One graph per group of articles: the articles, their reviews, critiques, author
    responses and their links."""
    nodes, edges, ns = tables.nodes, tables.edges, vocabulary.ns
    articles, reviews, critiques = nodes["article"], nodes["review"], nodes["critique"]
    responses = nodes.get("response")
    reviews_of = grouped(edges[HAS_REVIEW], len(articles))
    critiques_of = grouped(edges[CONTAINS], len(reviews))
    concepts_of = grouped(edges[HAS_CONCEPT], len(articles))
    sharing = edges[SHARES_CONCEPT]
    neighbours = grouped((sharing[0][sharing[0] < sharing[1]], sharing[1][sharing[0] < sharing[1]]), len(articles))
    responses_to = grouped((edges[RESPONDS_TO][1], edges[RESPONDS_TO][0]), len(critiques)) if responses is not None else None
    aspect_of = dict(zip(*edges[ABOUT]))
    aspect_names, concept_names = list(nodes["aspect"]["aspect"]), list(nodes["concept"]["concept"])
    article_ids = list(articles["forum_id"])

    for start in range(0, len(articles), articles_per_chunk):
        graph = vocabulary.new_graph()
        for a, article in articles.iloc[start:start + articles_per_chunk].iterrows():
            a_node = vocabulary.resource("article", article["forum_id"])
            graph.add((a_node, RDF.type, ns.Article))
            graph.add((a_node, ns.year, Literal(int(article["year"]), datatype=XSD.gYear)))
            if article["text_available"]:
                graph.add((a_node, DCTERMS.title, Literal(article["title"])))
                graph.add((a_node, DCTERMS.abstract, Literal(article["abstract"])))
            for c in concepts_of[a]:
                graph.add((a_node, ns.hasConcept, vocabulary.resource("concept", concept_names[c])))
            for other in neighbours[a]:
                graph.add((a_node, ns.sharesConcept, vocabulary.resource("article", article_ids[other])))
            for r in reviews_of[a]:
                review = reviews.iloc[r]
                r_node = vocabulary.resource("review", review["review_id"])
                graph.add((a_node, ns.hasReview, r_node))
                graph.add((r_node, RDF.type, ns.Review))
                for column in REVIEW_SCORES:
                    if pd.notna(review[column]):
                        graph.add((r_node, ns[SCORE_PROPERTIES[column]], Literal(int(review[column]))))
                for c in critiques_of[r]:
                    critique = critiques.iloc[c]
                    c_node = vocabulary.resource("critique", critique["critique_id"])
                    graph.add((r_node, ns.contains, c_node))
                    graph.add((c_node, RDF.type, ns.Critique))
                    graph.add((c_node, ns.text, Literal(critique["text"])))
                    if c in aspect_of:
                        graph.add((c_node, ns.about, vocabulary.resource("aspect", aspect_names[aspect_of[c]])))
                        for label in ("severity", "polarity", "target"):
                            graph.add((c_node, ns[label], Literal(critique[label])))
                        graph.add((c_node, ns.actionable, Literal(bool(critique["actionable"]))))
                    for p in (responses_to[c] if responses_to is not None else ()):
                        response = responses.iloc[p]
                        p_node = vocabulary.resource("response", response["response_id"])
                        graph.add((p_node, ns.respondsTo, c_node))
                        graph.add((p_node, RDF.type, ns.Response))
                        graph.add((p_node, ns.responseType, Literal(response["response_type"])))
                        graph.add((p_node, ns.text, Literal(response["text"])))
        yield graph


def write_turtle(graph: Graph, out: IO[str]) -> int:
    out.write(graph.serialize(format="turtle"))
    out.write("\n")
    return len(graph)


def export(tables: GraphTables, path: Path, base_iri: str, articles_per_chunk: int) -> int:
    """Write the graph to `path`; returns the number of triples written."""
    vocabulary = Vocabulary(base_iri)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as out:
        triples = write_turtle(vocabulary.header(), out) + write_turtle(fixed_resources(tables, vocabulary), out)
        for chunk in article_chunks(tables, vocabulary, articles_per_chunk):
            triples += write_turtle(chunk, out)
    return triples
