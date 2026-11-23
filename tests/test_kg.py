"""Phase 5: node/edge tables, embeddings cache, graph assembly, RDF export.

Everything runs on small synthetic tables and a fake encoder: no model, no GPU.
"""

import numpy as np
import pandas as pd
import pytest
import torch

from src.kg import build, embed, rdf, tables as kg_tables, text as kg_text
from src.llm.units import build_units

SETTINGS = {"review_chunk_chars": 60, "concepts": {"min_articles": 2, "max_articles_for_shared": 2}}


# --------------------------------------------------------------------------- texts
def test_keywords_are_normalised_into_concepts():
    assert kg_text.normalise_keyword("Large Language Models") == "large language model"
    assert kg_text.normalise_keyword("large-language model") == "large language model"
    assert kg_text.normalise_keyword("Graph Neural Networks (GNNs)") == "graph neural networks gnn"
    # words that end with "s" without being plurals keep it
    for keyword in ("bias", "analysis", "robotics", "loss", "consensus"):
        assert kg_text.normalise_keyword(keyword) == keyword
    assert kg_text.normalise_keyword("LLM") == "llm"  # no synonym table
    assert kg_text.normalise_keyword(" -- ") == ""
    assert kg_text.concepts_of(np.array(["GANs", "gan", "Diffusion"], dtype=object)) == ["diffusion", "gan"]
    assert kg_text.concepts_of(None) == []


def test_post_rebuttal_sentences_are_left_out_of_the_review_text():
    units = build_units({"weaknesses": "No baseline.\nAfter rebuttal: I raise my score to 8.", "questions": "Why this dataset?"})
    kept = kg_text.kept_units(units, {2})
    assert [u.text for u in kept] == ["No baseline.", "Why this dataset?"]
    assert kg_text.chunks(kept, max_chars=1000) == ["No baseline. Why this dataset?"]
    assert kg_text.chunks(kept, max_chars=15) == ["No baseline.", "Why this dataset?"]  # whole units only
    assert kg_text.chunks([], 100) == []


@pytest.mark.parametrize("text", [
    "After the rebuttal, my concerns remain.", "I will raise my score.", "Updated score: 6",
    "Thanks for the response, it clarified my doubts.", "Post-rebuttal comments below.",
    "The revision has addressed my main concern.",
])
def test_mentions_of_the_rebuttal_are_found(text):
    assert kg_text.has_post_rebuttal_marker(text)


@pytest.mark.parametrize("text", [
    "The score function is not defined.", "No baseline is given.", "The response time of the system is not measured.",
])
def test_ordinary_sentences_are_not_taken_for_mentions_of_the_rebuttal(text):
    assert not kg_text.has_post_rebuttal_marker(text)


# --------------------------------------------------------------------------- tables
def synthetic_inputs():
    papers = pd.DataFrame({
        "forum_id": ["P1", "P2", "P3", "P4", "PX"], "year": [2024, 2024, 2025, 2025, 2025],
        "title": ["t1", "t2", "t3", None, "tx"], "abstract": ["a1", "a2", "a3", None, "ax"],
        "keywords": [["GANs", "Vision"], ["gan", "vision", "Rare topic"], ["Vision", "Robotics"], None, ["gan"]],
        "text_available": [True, True, True, False, True], "text_source": ["s", "s", "s", None, "s"],
    })
    reviews = pd.DataFrame({
        "review_id": ["R1", "R2", "R3", "R4"], "forum_id": ["P1", "P1", "P2", "P3"], "year": [2024, 2024, 2024, 2025],
        "rating_initial": [6, 3, 8, 5], "confidence_initial": [4, 3, 4, 2], "soundness_initial": [3, 2, 3, 2],
        "contribution_initial": [3, 2, 4, 2], "presentation_initial": [None, None, None, 3],
        "summary": ["The paper does X. I raise my score."] * 4,
        "strengths": ["The idea is new.", None, "Clear writing.", None],
        "weaknesses": ["No baseline.\nAfter rebuttal: I raise my score to 8.", "Weak experiments.", None, "Unclear proofs."],
        "questions": [None, None, None, None],
    })
    critiques = pd.DataFrame({
        "critique_id": ["R1:1", "R1:2", "R2:1", "R3:1", "R4:1"], "review_id": ["R1", "R1", "R2", "R3", "R4"],
        "forum_id": ["P1", "P1", "P1", "P2", "P3"], "year": [2024, 2024, 2024, 2024, 2025], "critique_index": [1, 2, 1, 1, 1],
        "text": ["The idea is new.", "No baseline.", "Weak experiments.", "Clear writing.", "Unclear proofs."],
        "aspect": ["novelty", "experimental_comparison", "experimental_comparison", "clarity", None],
        "severity": ["minor", "major", "major", "minor", None], "polarity": ["positive", "negative", "negative", "positive", None],
        "target": ["general", "experiment", "experiment", "general", None], "actionable": [False, True, True, False, None],
    })
    responses = pd.DataFrame({
        "critique_id": ["R1:1", "R1:2", "R2:1", "R3:1"], "review_id": ["R1", "R1", "R2", "R3"],
        "forum_id": ["P1", "P1", "P1", "P2"], "year": [2024] * 4,
        "block_index": pd.array([None, 1, 1, None], dtype="Int64"),
        "response_text": [None, "We added two baselines.", "We added experiments.", None],
        "response_type": ["none", "new_experiment", "new_experiment", "none"],
    })
    audit = pd.DataFrame({"review_id": ["R1", "R2", "R3", "R4"], "post_rebuttal_units": [[3], [], [], []]})
    return papers, reviews, critiques, responses, audit


@pytest.fixture(scope="module")
def graph_tables():
    papers, reviews, critiques, responses, audit = synthetic_inputs()
    return kg_tables.build_tables(papers, reviews, critiques, responses, audit, {"P1", "P2", "P3", "P4"}, SETTINGS, 36000)


def test_nodes_follow_the_usable_papers(graph_tables):
    nodes = graph_tables.nodes
    assert list(nodes["article"]["forum_id"]) == ["P1", "P2", "P3", "P4"]  # PX is not a usable paper
    assert list(nodes["review"]["review_id"]) == ["R1", "R2", "R3", "R4"]
    assert len(nodes["critique"]) == 5 and len(nodes["aspect"]) == 8
    with pytest.raises(ValueError, match="missing from papers_initial"):
        kg_tables.article_nodes(nodes["article"], {"P1", "P9"})


def test_the_review_text_has_no_summary_and_no_post_rebuttal_sentence(graph_tables):
    reviews = graph_tables.nodes["review"].set_index("review_id")
    assert reviews.at["R1", "chunks"] == ["The idea is new. No baseline."]
    assert not reviews["post_rebuttal_marker_left"].any()
    assert "presentation_initial" not in reviews.columns  # missing for the training year
    assert not any("The paper does X" in chunk for chunks in reviews["chunks"] for chunk in chunks)


def test_concepts_and_links_between_articles(graph_tables):
    concepts = graph_tables.nodes["concept"].set_index("concept")["n_articles"].to_dict()
    # "rare topic" and "robotic" are used by one article; the unusable paper PX does not count
    assert concepts == {"gan": 2, "vision": 3}
    sources, targets = graph_tables.edges[kg_tables.HAS_CONCEPT]
    assert len(sources) == 5 and set(sources) == {0, 1, 2}  # P4 has no text, hence no concept
    # shares_concept only goes through concepts used by at most 2 articles: "gan" (P1, P2), not "vision"
    first, second = graph_tables.edges[kg_tables.SHARES_CONCEPT]
    assert sorted(zip(first.tolist(), second.tolist())) == [(0, 1), (1, 0)]
    assert graph_tables.edge_weights[kg_tables.SHARES_CONCEPT].tolist() == [1.0, 1.0]


def test_a_response_is_one_passage_and_may_answer_several_critiques():
    papers, reviews, critiques, responses, audit = synthetic_inputs()
    responses.loc[len(responses)] = ["R1:1", "R1", "P1", 2024, 1, "We added two baselines.", "new_experiment"]
    tables = kg_tables.build_tables(papers, reviews, critiques, responses, audit, {"P1", "P2", "P3", "P4"}, SETTINGS, 36000)
    assert list(tables.nodes["response"]["response_id"]) == ["R1:r1", "R2:r1"]
    sources, targets = tables.edges[kg_tables.RESPONDS_TO]
    answered = tables.nodes["critique"]["critique_id"].to_numpy()[targets]
    assert sorted(zip(sources.tolist(), answered.tolist())) == [(0, "R1:1"), (0, "R1:2"), (1, "R2:1")]

    responses.loc[len(responses)] = ["R2:1", "R2", "P1", 2024, 1, "Another text for the same block.", "new_experiment"]
    with pytest.raises(ValueError, match="several texts"):
        kg_tables.build_tables(papers, reviews, critiques, responses, audit, {"P1", "P2", "P3", "P4"}, SETTINGS, 36000)


def test_setting_a_drops_the_author_responses(graph_tables):
    a = graph_tables.setting("A")
    assert "response" not in a.nodes and kg_tables.RESPONDS_TO not in a.edges
    assert set(a.nodes) == {"article", "review", "critique", "aspect", "concept"}
    assert graph_tables.setting("B") is graph_tables
    with pytest.raises(ValueError):
        graph_tables.setting("C")


def test_untyped_critiques_have_no_aspect_link(graph_tables):
    sources, targets = graph_tables.edges[kg_tables.ABOUT]
    assert len(sources) == 4  # R4:1 has no label
    aspects = graph_tables.nodes["aspect"]["aspect"].to_numpy()[targets]
    assert aspects.tolist() == ["novelty", "experimental_comparison", "experimental_comparison", "clarity"]


def test_targets_are_aligned_on_the_articles_and_keep_both_label_variants(graph_tables):
    as_reject = pd.DataFrame({"forum_id": ["P1", "P2", "P3", "P4"], "year": [2024, 2024, 2025, 2025],
                              "split": ["train", "val", "test", "test"], "label": [1, 0, 0, 1]})
    excluded = as_reject[as_reject["forum_id"] != "P2"]  # P2 was withdrawn
    targets = kg_tables.targets(graph_tables.nodes["article"], excluded, as_reject)
    assert list(targets["article_index"]) == [0, 1, 2, 3] and list(targets["split"]) == ["train", "val", "test", "test"]
    assert targets["label"].isna().tolist() == [False, True, False, False]
    assert targets["label_withdrawn_as_reject"].tolist() == [1, 0, 0, 1]
    with pytest.raises(ValueError, match="no split"):
        kg_tables.targets(graph_tables.nodes["article"], excluded, as_reject[as_reject["forum_id"] != "P4"])


# --------------------------------------------------------------------------- embeddings
def fake_encoder(calls: list[int]):
    def encode(texts):
        calls.append(len(texts))
        return np.array([[len(t), sum(map(ord, t)) % 97, 1.0] for t in texts], dtype=np.float32)
    return encode


def test_a_text_is_encoded_once_whatever_the_run(tmp_path):
    calls: list[int] = []
    cache = embed.EmbeddingCache(tmp_path / "model")
    vectors, sent = cache.embed(["bb", "a", "bb", "ccc"], fake_encoder(calls))
    assert sent == 3 and calls == [3]  # the repeated text is sent once
    assert vectors[:, 0].tolist() == [2.0, 1.0, 2.0, 3.0] and vectors.dtype == np.float32

    again = embed.EmbeddingCache(tmp_path / "model")  # another run reads the files
    vectors, sent = again.embed(["ccc", "dddd", "a"], fake_encoder(calls))
    assert sent == 1 and calls == [3, 1] and vectors[:, 0].tolist() == [3.0, 4.0, 1.0]
    _, sent = again.embed(["a", "bb"], fake_encoder(calls))
    assert sent == 0 and calls == [3, 1]

    calls.clear()
    embed.EmbeddingCache(tmp_path / "other").embed([str(i) for i in range(5)], fake_encoder(calls), save_every=2)
    assert calls == [2, 2, 1]  # saved little by little


def test_a_review_embedding_is_the_mean_of_its_chunks():
    chunks = np.array([[1.0, 0.0], [3.0, 2.0], [5.0, 5.0]], dtype=np.float32)
    assert embed.mean_of_chunks(chunks, [2, 0, 1]).tolist() == [[2.0, 1.0], [0.0, 0.0], [5.0, 5.0]]


# --------------------------------------------------------------------------- graph
def fake_embeddings(tables, dim=4):
    rng = np.random.default_rng(0)
    return {t: rng.normal(size=(len(table), dim)).astype(np.float32) for t, table in tables.nodes.items()}


def test_graph_assembly_and_feature_layout(graph_tables):
    embeddings = fake_embeddings(graph_tables)
    graph, layout = build.build_graph(graph_tables, embeddings)
    assert graph["article"].x.shape == (4, 5) and graph["article"].x[:, 4].tolist() == [0.0, 0.0, 0.0, 1.0]
    assert graph["review"].x.shape == (4, 8) and graph["review"].x[:, 0].tolist() == [6.0, 3.0, 8.0, 5.0]
    # critique: text (4) + aspect (8) + severity (3) + polarity (3) + target (5) + actionable (1)
    assert graph["critique"].x.shape == (5, 24)
    assert [(b["name"], b["start"], b["end"]) for b in layout["critique"]] == [
        ("text", 0, 4), ("aspect", 4, 12), ("severity", 12, 15), ("polarity", 15, 18), ("target", 18, 23), ("actionable", 23, 24)]
    assert graph["critique"].x[4, 4:].sum() == 0  # the critique without label has empty label columns
    assert graph["critique"].x[1, 23] == 1 and graph["critique"].x[0, 23] == 0
    assert graph["response"].x.shape == (2, 9) and graph["aspect"].x.shape == (8, 8)
    assert graph["article"].year.tolist() == [2024, 2024, 2025, 2025]

    # every relation has its inverse; the symmetric one holds both directions
    assert graph["article", "has_review", "review"].edge_index.tolist() == [[0, 0, 1, 2], [0, 1, 2, 3]]
    assert graph["review", "rev_has_review", "article"].edge_index.tolist() == [[0, 1, 2, 3], [0, 0, 1, 2]]
    assert ("critique", "rev_responds_to", "response") in graph.edge_types
    assert ("article", "rev_shares_concept", "article") not in graph.edge_types
    assert graph["article", "shares_concept", "article"].edge_weight.tolist() == [1.0, 1.0]

    with pytest.raises(ValueError, match="misaligned"):
        build.build_graph(graph_tables, {**embeddings, "review": embeddings["review"][:2]})


def test_setting_a_graph_has_no_response_and_the_same_features_as_b(graph_tables):
    embeddings = fake_embeddings(graph_tables)
    graph_b, _ = build.build_graph(graph_tables, embeddings)
    graph_a, layout_a = build.build_graph(graph_tables.setting("A"), embeddings)
    assert "response" not in graph_a.node_types and "response" not in layout_a
    assert not [e for e in graph_a.edge_types if "respon" in e[1]]
    for node_type in graph_a.node_types:
        assert torch.equal(graph_a[node_type].x, graph_b[node_type].x)


def test_the_subgraph_of_some_articles_keeps_only_what_belongs_to_them(graph_tables):
    graph, _ = build.build_graph(graph_tables, fake_embeddings(graph_tables))
    train = build.article_subgraph(graph, graph["article"].year == 2024)
    assert train["article"].num_nodes == 2 and train["review"].num_nodes == 3
    assert train["critique"].num_nodes == 4 and train["response"].num_nodes == 2
    assert train["aspect"].num_nodes == 8 and train["concept"].num_nodes == 2
    assert train["review"].year.tolist() == [2024, 2024, 2024]
    assert train["article", "has_review", "review"].edge_index.tolist() == [[0, 0, 1], [0, 1, 2]]
    test = build.article_subgraph(graph, graph["article"].year == 2025)
    assert test["review"].num_nodes == 1 and test["response"].num_nodes == 0
    assert test["article", "shares_concept", "article"].edge_index.shape[1] == 0


def test_statistics_count_each_edge_once(graph_tables):
    table = build.statistics(graph_tables, "B").set_index("type")
    assert table.loc["article", "count"] == 4 and table.loc["article", "count_2024"] == 2
    assert table.loc["article -shares_concept-> article", "count"] == 1
    assert table.loc["response -responds_to-> critique", "count"] == 2
    assert "response" not in set(build.statistics(graph_tables.setting("A"), "A")["type"])


# --------------------------------------------------------------------------- RDF
def test_rdf_export_holds_the_structure_and_no_outcome(graph_tables, tmp_path):
    from rdflib import Graph, Literal, URIRef
    from rdflib.namespace import RDF

    path = tmp_path / "kg.ttl"
    triples = rdf.export(graph_tables, path, "https://example.org/kg/", articles_per_chunk=3)
    graph = Graph().parse(path, format="turtle")  # the chunks read as one document
    assert len(graph) == triples
    ns = rdf.Vocabulary("https://example.org/kg/").ns
    count = lambda kind: len(set(graph.subjects(RDF.type, ns[kind])))  # noqa: E731
    assert [count(k) for k in rdf.CLASSES] == [4, 4, 5, 2, 8, 2]

    article, review = URIRef("https://example.org/kg/article/P1"), URIRef("https://example.org/kg/review/R1")
    critique, response = URIRef("https://example.org/kg/critique/R1-2"), URIRef("https://example.org/kg/response/R1-r1")
    assert (article, ns.hasReview, review) in graph and (review, ns.contains, critique) in graph
    assert (response, ns.respondsTo, critique) in graph
    assert (critique, ns.about, URIRef("https://example.org/kg/aspect/experimental_comparison")) in graph
    assert (critique, ns.severity, Literal("major")) in graph and (critique, ns.actionable, Literal(True)) in graph
    assert (review, ns.initialRating, Literal(6)) in graph
    assert (article, ns.sharesConcept, URIRef("https://example.org/kg/article/P2")) in graph
    assert (article, ns.hasConcept, URIRef("https://example.org/kg/concept/gan")) in graph
    # the article without text has no title; nothing about decisions or authors anywhere
    assert not list(graph.objects(URIRef("https://example.org/kg/article/P4"), None, unique=True))[2:]
    text = path.read_text(encoding="utf-8").lower()
    for word in ("decision", "accept", "reject", "author", "reviewer_", "meta"):
        assert word not in text, word
