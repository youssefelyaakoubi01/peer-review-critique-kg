"""Anti-leakage tests (CLAUDE.md, rule 2).

Coverage:
  - the forbidden-field list in the config covers every category of rule 2, and the
    guard rejects inputs that contain a forbidden field;
  - the model-input views, the cleaned tables and the built graphs hold no forbidden
    field, no final score and no column equal to the label;
  - flipping the labels of the test papers changes no prediction, and changing the
    features of the test-year articles, reviews and critiques changes no prediction made
    for a training or validation paper.
The structure of the graph of the study is NOT free of the test year: its concept
vocabulary and its shares_concept edges are counted on the training and test years
together (src/kg/tables.py), so the graph a model is trained on depends on the keywords
of the test year, without any label. results/tables/kg_concept_scope.csv measures it
(scripts/07e_sensitivity.py) and the article reports it. The last test of this file
shows this dependence and checks that the graph of the protocol checks
(scripts/05f_inductive_graph.py: training years first, later years appended with the
vocabulary frozen) does not have it.
Not covered: what the pretrained models (text encoders, LLM) may have read.
"""

import pytest

from src.utils.config import load_config
from src.utils.leakage import assert_no_forbidden_fields, find_forbidden_fields

# One representative field per category listed in rule 2.
REQUIRED_FORBIDDEN = {
    "decision",
    "meta_review",
    "area_chair_comment",
    "final_rating",
    "venue",
    "venueid",
    "camera_ready",
    "invitations",
    "pdf",
    "citations_received",
    "authors",
    "authorids",
    "author_affiliation",
}


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def forbidden(cfg):
    return cfg["leakage"]["forbidden_fields"]


def test_forbidden_list_covers_rule_2(forbidden):
    missing = REQUIRED_FORBIDDEN - {f.lower() for f in forbidden}
    assert not missing, f"forbidden_fields is missing: {sorted(missing)}"


@pytest.mark.parametrize("field", sorted(REQUIRED_FORBIDDEN))
def test_guard_rejects_forbidden_field(field, forbidden):
    with pytest.raises(ValueError, match="leakage"):
        assert_no_forbidden_fields(["title", "abstract", field], forbidden)


def test_guard_is_case_insensitive(forbidden):
    assert find_forbidden_fields(["Decision", "VenueID", "title"], forbidden) == [
        "Decision",
        "VenueID",
    ]


def test_guard_accepts_clean_inputs(forbidden):
    assert_no_forbidden_fields(["title", "abstract", "initial_rating", "review_text"], forbidden)


# ----------------------------------------------------------------- model-input entry point
def synthetic_tables():
    import pandas as pd

    from src.clean.normalize import PHASE_AFTER, PHASE_BEFORE

    return {
        "papers": pd.DataFrame({"forum_id": ["F1", "F2"], "year": [2024, 2024], "title": ["camera-ready a", "b"]}),
        "papers_initial": pd.DataFrame({"forum_id": ["F1", "F2"], "year": [2024, 2024], "title": ["a", "b"]}),
        "reviews": pd.DataFrame({
            "review_id": ["R1", "R2", "R3"],
            "forum_id": ["F1", "F1", "F2"],
            "phase": [PHASE_BEFORE, PHASE_AFTER, PHASE_BEFORE],
            "rating_initial": [5, 6, 3],
            "weaknesses": ["x", "y", "z"],
        }),
        "reviews_final": pd.DataFrame({"review_id": ["R1"], "rating_final": [8]}),
        "outcomes": pd.DataFrame({
            "forum_id": ["F1", "F2"], "year": [2024, 2024], "split": ["train", "val"],
            "label": pd.array([1, None], dtype="Int64"),
            "label_withdrawn_as_reject": pd.array([1, 0], dtype="Int64"),
            "eligible": [True, False], "eligible_withdrawn_as_reject": [True, True],
        }),
    }


def test_setting_a_inputs_exclude_outcomes_final_scores_and_second_phase(cfg):
    from src.clean import views

    inputs = views.model_inputs(synthetic_tables(), cfg, setting="A")
    assert set(inputs) == {"papers_initial", "reviews"}
    assert list(inputs["papers_initial"]["title"]) == ["a", "b"]  # never the current, camera-ready text
    assert list(inputs["reviews"]["review_id"]) == ["R1", "R3"]  # R2 came after the author response
    assert "phase" not in inputs["reviews"].columns


@pytest.mark.parametrize("column", ["rating_final", "label", "decision_text", "modified_after_release", "authors"])
def test_entry_point_refuses_a_table_with_a_forbidden_column(cfg, column):
    from src.clean import views

    tables = synthetic_tables()
    tables["reviews"][column] = 1
    with pytest.raises(ValueError, match="leakage"):
        views.model_inputs(tables, cfg, setting="A")


def test_labels_follow_the_treatment_of_withdrawn_papers():
    from src.clean import views

    outcomes = synthetic_tables()["outcomes"]
    assert list(views.labels(outcomes, "excluded")["forum_id"]) == ["F1"]
    as_reject = views.labels(outcomes, "as_reject")
    assert list(as_reject["label"]) == [1, 0]


def test_model_input_tables_never_include_outcome_tables(cfg):
    assert set(cfg["clean"]["model_input_tables"]) == {"papers_initial", "reviews"}


def test_entry_point_refuses_the_table_with_the_current_paper_text(cfg):
    import copy

    from src.clean import views

    unsafe = copy.deepcopy(cfg)
    unsafe["clean"]["model_input_tables"] = ["papers", "reviews"]
    with pytest.raises(ValueError, match="post-decision text"):
        views.model_inputs(synthetic_tables(), unsafe, setting="A")


# ----------------------------------------------------------------- real cleaned tables
@pytest.fixture(scope="module")
def interim(cfg):
    import pandas as pd

    directory = cfg["paths"]["interim"]
    names = ("papers", "reviews", "reviews_final", "discussion", "outcomes")
    if not all((directory / f"{n}.parquet").exists() for n in names):
        pytest.skip("interim tables not built yet: run scripts/02_clean.py")
    columns = {"discussion": ["reply_id", "forum_id", "role", "phase", "tcdate", "target_review_id"]}
    return {n: pd.read_parquet(directory / f"{n}.parquet", columns=columns.get(n)) for n in names}


def test_interim_model_inputs_have_no_forbidden_fields(cfg, forbidden, interim):
    from src.clean import views
    from src.clean.normalize import PHASE_BEFORE

    inputs = views.load_model_inputs(cfg, setting="A")
    for name, table in inputs.items():
        assert_no_forbidden_fields(table.columns, forbidden)
        assert not [c for c in table.columns if c.endswith(("_final", "_ext_post"))], name

    # Only reviews posted before the first author response of their forum.
    before = set(interim["reviews"].loc[interim["reviews"]["phase"] == PHASE_BEFORE, "review_id"])
    assert set(inputs["reviews"]["review_id"]) == before
    first_response = interim["outcomes"].set_index("forum_id")["first_author_response_tcdate"]
    limit = inputs["reviews"]["forum_id"].map(first_response)
    assert not (inputs["reviews"]["tcdate"] >= limit).fillna(False).any()


def test_interim_tables_contain_no_desk_rejected_paper(interim):
    assert "desk_rejected" not in set(interim["outcomes"]["status"])
    known = set(interim["outcomes"]["forum_id"])
    for name in ("papers", "reviews", "reviews_final", "discussion"):
        assert set(interim[name]["forum_id"]) <= known, name


def test_interim_labels_are_binary_and_consistent(interim):
    outcomes = interim["outcomes"]
    assert set(outcomes["label"].dropna().unique()) <= {0, 1}
    # The second variant only adds rejections, for papers withdrawn before a decision.
    added = outcomes["label"].isna() & outcomes["label_withdrawn_as_reject"].notna()
    assert (outcomes.loc[added, "label_withdrawn_as_reject"] == 0).all()
    assert outcomes.loc[added, "withdrawn_before_decision"].all()
    same = outcomes["label"].notna()
    assert (outcomes.loc[same, "label"] == outcomes.loc[same, "label_withdrawn_as_reject"]).all()
    # A test-year paper is never in train or validation.
    assert set(outcomes.loc[outcomes["split"] == "test", "year"]).isdisjoint(
        set(outcomes.loc[outcomes["split"] != "test", "year"])
    )


def test_interim_author_replies_point_to_reviews_of_the_same_forum(interim):
    discussion = interim["discussion"]
    aligned = discussion[discussion["target_review_id"].notna()]
    review_forum = interim["reviews"].set_index("review_id")["forum_id"]
    assert aligned["target_review_id"].isin(review_forum.index).all()
    assert (aligned["target_review_id"].map(review_forum) == aligned["forum_id"]).all()
    # Authors never write before their own first response.
    from src.clean.normalize import PHASE_AFTER

    assert (discussion.loc[discussion["role"] == "authors", "phase"] == PHASE_AFTER).all()


# ----------------------------------------------------------------- processed graphs
ALLOWED_NODE_ATTRIBUTES = {"x", "year"}
ALLOWED_EDGE_ATTRIBUTES = {"edge_index", "edge_weight"}


@pytest.fixture(scope="module")
def graphs(cfg):
    """The two processed graphs with their side files (skipped until phase 5 has run)."""
    import json

    import pandas as pd
    import torch

    processed = cfg["paths"]["processed"]
    paths = {setting: processed / f"graph_{setting}.pt" for setting in ("A", "B")}
    if not any(path.exists() for path in paths.values()):
        pytest.skip("no processed graph yet: leakage check on real model inputs not run")
    return {
        "graphs": {setting: torch.load(path, weights_only=False) for setting, path in paths.items()},
        "layout": json.loads((processed / "graph_features.json").read_text()),
        "nodes": {t: pd.read_parquet(processed / f"nodes_{t}.parquet") for t in ("article", "review", "critique", "response")},
        "targets": pd.read_parquet(processed / "targets.parquet"),
    }


def test_processed_graphs_hold_no_forbidden_attribute(graphs, forbidden, cfg):
    response_fields = set(cfg["leakage"]["setting_b_fields"])
    assert response_fields <= set(forbidden)  # they stay forbidden in setting A
    for setting, graph in graphs["graphs"].items():
        not_allowed = [f for f in forbidden if setting == "A" or f not in response_fields]
        for node_type in graph.node_types:
            names = set(graph[node_type].keys())
            assert names <= ALLOWED_NODE_ATTRIBUTES, f"graph {setting}, {node_type}: {names}"
            assert_no_forbidden_fields(names | {node_type}, not_allowed)
        for edge_type in graph.edge_types:
            names = set(graph[edge_type].keys())
            assert names <= ALLOWED_EDGE_ATTRIBUTES, f"graph {setting}, {edge_type}: {names}"
            assert_no_forbidden_fields(names | set(edge_type), not_allowed)
        for node_type, blocks in graphs["layout"][setting].items():
            assert_no_forbidden_fields([block["name"] for block in blocks], not_allowed)
            assert blocks[-1]["end"] == graph[node_type].x.shape[1]


def test_setting_a_graph_has_nothing_from_the_author_response(graphs):
    graph_a, graph_b = graphs["graphs"]["A"], graphs["graphs"]["B"]
    assert "response" not in graph_a.node_types and "response" in graph_b.node_types
    assert not [edge for edge in graph_a.edge_types if "respon" in edge[1] or "response" in edge]
    assert "response" not in graphs["layout"]["A"]
    assert not [b for blocks in graphs["layout"]["A"].values() for b in blocks if "response" in b["name"]]
    # B is A plus the responses: same nodes, same features, same other edges
    import torch

    for node_type in graph_a.node_types:
        assert torch.equal(graph_a[node_type].x, graph_b[node_type].x), node_type
    for edge_type in graph_a.edge_types:
        assert torch.equal(graph_a[edge_type].edge_index, graph_b[edge_type].edge_index), edge_type
    assert set(graph_b.edge_types) - set(graph_a.edge_types) == {
        ("response", "responds_to", "critique"), ("critique", "rev_responds_to", "response")}


def test_graph_reviews_are_the_initial_reviews_with_initial_scores_only(graphs, cfg):
    from src.clean import views
    from src.kg.tables import REVIEW_SCORES

    before = views.load_model_inputs(cfg, "A")["reviews"]  # reviews posted before the author response
    in_graph = graphs["nodes"]["review"]
    assert set(in_graph["review_id"]) <= set(before["review_id"])
    names = [block["name"] for block in graphs["layout"]["A"]["review"]]
    assert names == [*REVIEW_SCORES, "text"]
    assert all(name.endswith("_initial") for name in names[:-1])
    # the scores stored in the graph are the initial ones
    scores = before.set_index("review_id").loc[in_graph["review_id"], list(REVIEW_SCORES)].to_numpy(dtype="float32")
    assert (graphs["graphs"]["A"]["review"].x[:, :len(REVIEW_SCORES)].numpy() == scores).all()


def test_graph_article_text_comes_from_before_the_decisions(graphs, cfg):
    import numpy as np
    import pandas as pd

    assert "papers" not in cfg["clean"]["model_input_tables"]
    initial = pd.read_parquet(cfg["paths"]["interim"] / "papers_initial.parquet").set_index("forum_id")
    articles = graphs["nodes"]["article"]
    x = graphs["graphs"]["A"]["article"].x.numpy()
    available = initial.loc[articles["forum_id"], "text_available"].to_numpy()
    assert (x[:, -1] == (~available).astype("float32")).all()  # last column: text missing
    assert not x[~available, :-1].any()  # no text, no embedding
    # the embeddings are those computed from papers_initial by scripts/05b_embed_articles.py
    directory = cfg["paths"]["interim"] / "kg"
    rows = pd.read_parquet(directory / "article_specter2.parquet")["forum_id"]
    vectors = pd.DataFrame(np.load(directory / "article_specter2.npy"), index=rows)
    with_text = articles.loc[available, "forum_id"]
    assert np.array_equal(x[available, :-1], vectors.loc[with_text].to_numpy())
    script = (cfg["paths"]["logs"].parent / "scripts" / "05b_embed_articles.py").read_text()
    assert '"papers_initial.parquet"' in script and '"papers.parquet"' not in script


def test_outcomes_are_kept_out_of_the_graphs(graphs):
    targets = graphs["targets"]
    articles = graphs["nodes"]["article"]
    assert list(targets["forum_id"]) == list(articles["forum_id"])  # aligned on the article nodes
    labels = targets["label_withdrawn_as_reject"].to_numpy(dtype="float32")
    for setting, graph in graphs["graphs"].items():
        x = graph["article"].x.numpy()
        assert not (x == labels[:, None]).all(axis=0).any(), f"graph {setting}: a feature column equals the outcome"
        assert graph["article"].num_nodes == len(targets)
    # a test-year paper is never a training or validation target
    assert set(targets.loc[targets["split"] == "test", "year"]).isdisjoint(set(targets.loc[targets["split"] != "test", "year"]))


# ----------------------------------------------------------------- baselines (phase 6)
def test_baselines_read_the_graph_of_setting_a_and_the_targets_only(cfg, forbidden):
    import re

    script = (cfg["paths"]["logs"].parent / "scripts" / "06_baselines.py").read_text()
    assert cfg["baselines"]["setting"] == "A"
    assert set(re.findall(r'processed / f?"([^"]+)"', script)) == {"graph_{setting}.pt", "graph_features.json", "targets.parquet"}
    assert script.count("read_parquet(") == 1 and "interim" not in script and '"raw"' not in script
    assert "label_withdrawn_as_reject" not in script
    for spec in cfg["baselines"]["models"].values():
        assert set(spec.get("features", [])) <= {"rating", "other_scores", "review_text", "article_text", "critique_marginals",
                                                 "critique_aspect_severity", "critique_worst_review"}


def test_baseline_feature_names_are_not_forbidden(forbidden):
    from test_baselines import LAYOUT, synthetic_graph

    from src.models import features

    table = features.article_table(synthetic_graph()[0], LAYOUT)
    for names in table.names.values():
        assert_no_forbidden_fields(names, forbidden)
    assert all("_initial_" in name for name in table.names["rating"])


@pytest.mark.parametrize("name", ["majority", "logistic", "gbt", "mlp", "gcn"])
def test_baseline_predictions_do_not_depend_on_the_test_labels(name):
    import numpy as np
    from test_baselines import SETTINGS, SPECS, make_data, synthetic_graph

    from src.models import baselines

    graph, labels, split = synthetic_graph()
    flipped = labels.copy()
    flipped[split == "test"] = 1 - flipped[split == "test"]
    spec, params = SPECS[name]
    first, _ = baselines.run(spec, params, make_data(graph, labels, split), 0, SETTINGS)
    second, _ = baselines.run(spec, params, make_data(graph, flipped, split), 0, SETTINGS)
    assert np.array_equal(first, second)


def test_the_gcn_is_trained_without_any_node_of_the_test_year():
    import numpy as np
    import torch
    from test_baselines import SETTINGS, SPECS, make_data, synthetic_graph

    from src.kg.build import article_masks
    from src.models import baselines

    graph, labels, split = synthetic_graph()
    changed = graph.clone()
    masks = article_masks(graph, torch.from_numpy(split == "test"))
    for node_type in ("article", "review", "critique"):
        changed[node_type].x[masks[node_type]] += 7.0  # everything that belongs to a test article
    spec, params = SPECS["gcn"]
    first, _ = baselines.run(spec, params, make_data(graph, labels, split), 0, SETTINGS)
    second, _ = baselines.run(spec, params, make_data(changed, labels, split), 0, SETTINGS)
    known = split != "test"
    assert np.array_equal(first[known], second[known])  # same training, same predictions for the training years
    assert not np.allclose(first[~known], second[~known])  # the test articles are read at prediction time only


# ----------------------------------------------------------------- heterogeneous GNNs (phase 7)
HETERO_SETTINGS = {"heads": 2, "weight_decay": 0.0, "max_epochs": 30, "patience": 10}
HETERO_PARAMS = {"layers": 2, "hidden": 16, "dropout": 0.0, "lr": 0.01}


def hetero_predictions(kind, graph, labels, split):
    from test_baselines import LAYOUT

    from src.models import baselines, features, hetero

    data = baselines.Data(features.article_table(graph, LAYOUT), labels, split)
    return hetero.run(kind, HETERO_PARAMS, data, hetero.hetero_views(graph, LAYOUT, split, "cpu"), 0, HETERO_SETTINGS)[0]


@pytest.mark.parametrize("kind", ["rgcn", "han", "hgt"])
def test_hetero_gnn_never_reads_the_test_year_before_prediction(kind):
    import numpy as np
    import torch
    from test_baselines import synthetic_graph

    from src.kg.build import article_masks

    graph, labels, split = synthetic_graph()
    first = hetero_predictions(kind, graph, labels, split)
    flipped = labels.copy()
    flipped[split == "test"] = 1 - flipped[split == "test"]
    assert np.array_equal(first, hetero_predictions(kind, graph, flipped, split))  # test labels are never read
    changed = graph.clone()
    masks = article_masks(graph, torch.from_numpy(split == "test"))
    for node_type in ("article", "review", "critique"):
        changed[node_type].x[masks[node_type]] += 7.0
    second = hetero_predictions(kind, changed, labels, split)
    known = split != "test"
    assert np.array_equal(first[known], second[known])  # same training without the nodes of the test year
    assert not np.allclose(first[~known], second[~known])


def test_gnn_script_reads_the_graphs_the_targets_and_the_baseline_tables_only(cfg):
    import re

    script = (cfg["paths"]["logs"].parent / "scripts" / "07_hetero_gnn.py").read_text()
    assert set(re.findall(r'processed / f?"([^"]+)"', script)) == {"graph_{setting}.pt", "graph_features.json", "targets.parquet", "models"}
    assert "interim" not in script and '"raw"' not in script
    assert set(cfg["gnn"]["settings"]) == {"A", "B"}
    assert set(cfg["gnn"]["score_variant"]["features"]) <= {"rating", "other_scores"}


def test_setting_a_models_get_no_author_response(graphs):
    from src.models import hetero

    import numpy as np

    split = graphs["targets"]["split"].to_numpy(dtype=object)
    graph = graphs["graphs"]["A"]
    assert "response" not in graph.node_types
    assert not [e for e in graph.edge_types if "response" in e or "respon" in e[1]]
    assert int((split != "test").sum()) + int((split == "test").sum()) == graph["article"].num_nodes
    assert np.isin(split, ["train", "val", "test"]).all() and hetero.KINDS == ("rgcn", "han", "hgt")



# ----------------------------------------------------------------- structure of the graph (protocol checks)
def test_the_inductive_graph_owes_nothing_to_the_keywords_of_a_later_year():
    import numpy as np

    from src.kg import extend, tables as kg_tables
    from tests.test_kg import SETTINGS, synthetic_inputs

    papers, reviews, critiques, responses, audit = synthetic_inputs()
    training, later = {"P1", "P2"}, {"P3", "P4"}  # 2024, then 2025

    def graphs(table):
        study = kg_tables.build_tables(table, reviews, critiques, responses, audit, training | later, SETTINGS, 36000).setting("A")
        base = kg_tables.build_tables(table, reviews, critiques, responses, audit, training, SETTINGS, 36000).setting("A")
        return study, extend.extend_tables(base, table, reviews, critiques, audit, later, SETTINGS, 36000)

    def among_training(tables, relation):
        """Edges of a relation whose article ends are all training articles."""
        is_training = tables.nodes["article"]["forum_id"].isin(training).to_numpy()
        sources, targets = tables.edges[relation]
        keep = is_training[sources] & (is_training[targets] if relation == kg_tables.SHARES_CONCEPT else True)
        names = tables.nodes["article"]["forum_id"].to_numpy()
        ends = names[targets] if relation == kg_tables.SHARES_CONCEPT else tables.nodes["concept"]["concept"].to_numpy()[targets]
        return sorted(zip(names[sources][keep], np.asarray(ends)[keep]))

    changed = papers.copy()
    changed["keywords"] = [["Rare topic", "Robotics", "GAN", "Vision"] if year == 2025 else keywords
                           for year, keywords in zip(papers["year"], papers["keywords"])]
    study, inductive = graphs(papers)
    study_changed, inductive_changed = graphs(changed)

    # the graph of the study: other keywords in the later year give another vocabulary, and
    # other edges between the training articles themselves ("rare topic" becomes a concept of
    # P2; "gan" and "vision" now have four articles and no longer carry shares_concept)
    assert study.nodes["concept"]["concept"].tolist() == ["gan", "vision"]
    assert study_changed.nodes["concept"]["concept"].tolist() == ["gan", "rare topic", "robotics", "vision"]
    assert among_training(study, kg_tables.HAS_CONCEPT) != among_training(study_changed, kg_tables.HAS_CONCEPT)
    assert among_training(study, kg_tables.SHARES_CONCEPT) == [("P1", "P2"), ("P2", "P1")]
    assert among_training(study_changed, kg_tables.SHARES_CONCEPT) == []

    # the inductive graph: same concepts, same edges among the training articles
    assert inductive.nodes["concept"].equals(inductive_changed.nodes["concept"])
    assert inductive.nodes["concept"]["concept"].tolist() == ["gan", "vision"]
    assert inductive.nodes["concept"]["n_articles"].tolist() == [2, 2]  # counted on the training years
    for relation in (kg_tables.HAS_CONCEPT, kg_tables.SHARES_CONCEPT):
        assert among_training(inductive, relation) == among_training(inductive_changed, relation)
    # the later articles are linked to the existing concepts only
    assert inductive_changed.nodes["article"]["forum_id"].tolist() == ["P1", "P2", "P3", "P4"]
    linked = dict.fromkeys(["P3", "P4"], ())
    sources, targets = inductive_changed.edges[kg_tables.HAS_CONCEPT]
    for article, concept in zip(sources, targets):
        name = inductive_changed.nodes["article"]["forum_id"][article]
        if name in linked:
            linked[name] += (inductive_changed.nodes["concept"]["concept"][concept],)
    assert linked == {"P3": ("gan", "vision"), "P4": ("gan", "vision")}  # "rare topic" and "robotics" are not concepts


def test_the_protocol_scripts_read_graphs_targets_and_stored_tables_only(cfg):
    scripts = cfg["paths"]["logs"].parent / "scripts"
    checks = (scripts / "07f_protocol_checks.py").read_text()
    import re

    assert "interim" not in checks and '"raw"' not in checks and "outcomes" not in checks and "views" not in checks
    read = set(re.findall(r'(?:directory|processed|tables_dir) / f?"([^"]+)"', checks))
    assert read <= {"graph_{setting}.pt", "graph_features.json", "targets.parquet", "models", "gnn_selection.csv",
                    "baselines_selection.csv", "protocol_{stage}_selection.csv", "protocol_{stage}_chosen.csv"}, read
    assert set(cfg["protocol"]["stages"]) == {"vocabulary", "search", "rolling"} and cfg["protocol"]["setting"] == "A"
    graph = (scripts / "05f_inductive_graph.py").read_text()
    # the graph is built without any outcome: the labels give the list of the usable papers
    # and the targets, written apart; no table of outcomes or of final reviews is opened
    code = graph.split('"""', 2)[2]
    assert "outcomes" not in code and "reviews_final" not in code and "read_parquet(cfg[\"paths\"][\"interim\"]" not in code
    assert set(re.findall(r"views\.(\w+)\(", code)) == {"load_model_inputs", "load_labels"}
