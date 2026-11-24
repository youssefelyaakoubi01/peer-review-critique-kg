"""Protocol checks: budgeted search, record of the runs, graph models trained on one
graph and validated or applied on another (src/models/search.py, src/models/staged.py).

Everything runs on a small random graph, on CPU.
"""

import numpy as np
import pytest
import torch
from sklearn.metrics import roc_auc_score
from test_baselines import LAYOUT, synthetic_graph

from src.kg.build import article_masks
from src.models import baselines, features, hetero, search, staged
from src.utils.config import load_config

HETERO_TRAINING = {"heads": 2, "weight_decay": 0.0, "max_epochs": 40, "patience": 15}
HETERO_PARAMS = {"layers": 2, "hidden": 16, "dropout": 0.0, "lr": 0.01}
GCN_PARAMS = {"layers": 2, "hidden": 16, "dropout": 0.0, "lr": 0.01, "weight_decay": 0.0}
GCN_TRAINING = {"max_epochs": 40, "patience": 15}


@pytest.fixture(scope="module")
def cfg():
    return load_config()


# --------------------------------------------------------------------------- search
def test_a_budget_draws_distinct_configurations_and_always_the_same():
    space = {"hidden": [32, 64, 128], "dropout": [0.2, 0.5, 0.7], "lr": [0.001, 0.01]}
    drawn = search.sample_configurations(space, 5, seed=0)
    assert len(drawn) == 5 and len({tuple(sorted(c.items())) for c in drawn}) == 5
    assert drawn == search.sample_configurations(space, 5, seed=0) != search.sample_configurations(space, 5, seed=1)
    assert all(c[name] in values for c in drawn for name, values in space.items())
    assert len(search.sample_configurations(space, 100, seed=0)) == 18 == len(search.sample_configurations(space, None, seed=0))


def test_the_best_configurations_leave_out_the_runs_that_failed():
    assert search.best_first([0.7, float("nan"), 0.9, 0.9, 0.8], top=3) == [2, 3, 4]  # tie: the first drawn first
    assert search.best_first([float("nan"), 0.5], top=5) == [1]
    assert search.best_first([float("nan")], top=2) == []


def test_values_at_the_edge_of_a_space_are_named():
    space = {"hidden": [32, 64, 128], "dropout": [0.2, 0.5, 0.7], "heads": [4]}
    assert search.at_edge({"hidden": 32, "dropout": 0.5, "heads": 4}, space) == ["hidden"]
    assert search.at_edge({"hidden": 64, "dropout": 0.7, "heads": 4}, space) == ["dropout"]


def test_recorded_runs_are_found_again_after_an_interruption(tmp_path):
    key = ["stage", "model", "phase", "params", "seed"]
    records = search.Records(tmp_path / "runs.csv", key)
    run = {"stage": "search", "model": "hgt", "phase": "selection", "params": {"lr": 0.01, "hidden": 64}, "seed": 0}
    assert records.find(run) is None
    records.add({**run, "val_auc": 0.8, "seconds": 2.0, "status": "ok"})
    records.add({**run, "seed": 1, "val_auc": float("nan"), "seconds": 1.0, "status": "out_of_memory"})
    again = search.Records(tmp_path / "runs.csv", key)  # a new process reads the file
    assert again.find({**run, "params": {"hidden": 64, "lr": 0.01}})["val_auc"] == 0.8  # the order of the keys does not matter
    assert again.find({**run, "seed": 1}) is None  # a failed run is not a result
    assert again.find({**run, "seed": 1}, failed=True)["status"] == "out_of_memory"  # but it is known, and a search does not try it again
    assert again.find({**run, "phase": "final"}) is None
    again.add({**run, "seed": 1, "val_auc": 0.7, "seconds": 3.0, "status": "ok"})  # tried again: replaces the failure
    assert len(again.rows) == 2 and again.find({**run, "seed": 1})["val_auc"] == 0.7
    assert again.seconds(stage="search") == [2.0, 3.0] and again.seconds(model="gcn") == []


def test_the_spaces_of_the_protocol_contain_the_grids_of_the_study_and_go_beyond(cfg):
    protocol, spaces = cfg["protocol"], cfg["protocol"]["spaces"]
    grids = {"hetero": cfg["gnn"]["grid"][protocol["setting"]], "gcn": cfg["baselines"]["models"]["gcn"]["grid"],
             "mlp": cfg["baselines"]["models"]["text_scores_mlp"]["grid"], "logistic": cfg["baselines"]["models"]["scores_rating_lr"]["grid"],
             "gbt": cfg["baselines"]["models"]["scores_all_gbt"]["grid"]}
    for family, grid in grids.items():
        for name, values in grid.items():
            assert set(values) <= set(spaces[family][name]), (family, name)
        assert len(baselines.grid({"grid": spaces[family]})) > len(baselines.grid({"grid": grid}))
    assert "weight_decay" in spaces["hetero"]  # fixed in phase 7, searched here
    # the same number of configurations for every family trained by epochs
    drawn = {family: len(search.sample_configurations(spaces[family], protocol["budget"], protocol["sample_seed"]))
             for family in ("mlp", "gcn", "hetero")}
    assert set(drawn.values()) == {protocol["budget"]}
    assert all(hidden % protocol["training"]["heads"] == 0 for hidden in spaces["hetero"]["hidden"])


def test_every_stage_follows_the_order_of_the_years(cfg):
    splits, order = cfg["splits"], {"train": 0, "test": 1, "holdout": 2}
    assert max(splits["train"]) < min(splits["test"]) < min(splits["holdout"])
    known = set(cfg["baselines"]["models"]) | set(hetero.KINDS)
    for name, stage in cfg["protocol"]["stages"].items():
        assert set(stage["models"]) <= known and stage["roles"] in staged.ROLES
        assert stage["train_graph"] == ["train"], name  # a model is always trained on the graph of the training years
        last = lambda names: max(order[n] for n in names)  # noqa: E731
        assert last(stage["train_graph"]) <= last(stage["validation_graph"]) <= min(last(names) for names in stage["predict"].values())
        assert stage["predict"]["val"] == stage["validation_graph"]
        # the papers of a role are predicted on a graph that holds their year and no later year
        role_year = {"study": {"val": "train", "test": "test", "holdout": "holdout"},
                     "rolling": {"val": "test", "test": "holdout"}}[stage["roles"]]
        for role, names in stage["predict"].items():
            assert names[-1] == role_year[role], (name, role)
    rolling = cfg["protocol"]["stages"]["rolling"]
    assert rolling["validation_graph"] == ["train", "test"] and set(rolling["predict"]) == {"val", "test"}


def test_roles_of_the_rolling_protocol():
    split = np.array(["train", "val", "test", "holdout"], dtype=object)
    assert staged.roles_of("study", split).tolist() == ["train", "val", "test", "holdout"]
    assert staged.roles_of("rolling", split).tolist() == ["train", "train", "val", "test"]
    with pytest.raises(ValueError, match="unknown scheme"):
        staged.roles_of("random", split)


# --------------------------------------------------------------------------- staged graph models
@pytest.fixture(scope="module")
def task():
    graph, labels, split = synthetic_graph()
    data = baselines.Data(features.article_table(graph, LAYOUT), labels, split)
    return graph, labels, split, data


def study_stages(graph, split, kind, extra=None):
    """Stages of phases 6 and 7: training years for training and validation, whole graph for the test."""
    scaled = staged.scaled_graph(graph, LAYOUT, split == "train")
    known, everyone = split != "test", np.ones(len(split), dtype=bool)
    if kind == "gcn":
        flat = features.flatten(graph, scaled.x_dict, LAYOUT)
        return staged.flat_stage(graph, flat, known), staged.flat_stage(graph, flat, everyone)
    return staged.hetero_stage(scaled, known, extra), staged.hetero_stage(scaled, everyone, extra)


@pytest.mark.parametrize("kind", hetero.KINDS)
def test_with_the_stages_of_the_study_a_heterogeneous_gnn_gives_the_predictions_of_phase_7(task, kind):
    graph, labels, split, data = task
    expected, fitted, _ = hetero.run(kind, HETERO_PARAMS, data, hetero.hetero_views(graph, LAYOUT, split, "cpu"), 0, HETERO_TRAINING)
    training, whole = study_stages(graph, split, kind)
    val, test = data.rows("val"), data.rows("test")
    got, again, _ = staged.run(kind, HETERO_PARAMS, HETERO_TRAINING, 0, labels, training, data.rows("train"), training, val,
                               [(training, val), (whole, test)], "cpu")
    assert (again.best_epoch, again.epochs) == (fitted.best_epoch, fitted.epochs)
    for rows in (val, test):
        assert np.array_equal(got[rows].astype(np.float32), expected[rows])
    assert np.isnan(got[data.rows("train")]).all()  # only the papers of the plan are predicted


def test_score_statistics_added_to_the_articles_give_the_predictions_of_phase_7(task):
    graph, labels, split, data = task
    extra = data.table.design(["rating", "other_scores"], data.rows("train"))
    views = hetero.with_article_columns(hetero.hetero_views(graph, LAYOUT, split, "cpu"), extra, "cpu")
    expected, _, _ = hetero.run("hgt", HETERO_PARAMS, data, views, 0, HETERO_TRAINING)
    plain = study_stages(graph, split, "hgt")
    training, whole = (staged.with_article_columns(stage, extra) for stage in plain)
    test = data.rows("test")
    got, _, _ = staged.run("hgt", HETERO_PARAMS, HETERO_TRAINING, 0, labels, training, data.rows("train"), training, data.rows("val"),
                           [(whole, test)], "cpu")
    assert np.array_equal(got[test].astype(np.float32), expected[test])
    built_at_once = study_stages(graph, split, "hgt", extra)[1]
    assert torch.equal(built_at_once.inputs[0]["article"], whole.inputs[0]["article"])
    assert plain[1].inputs[0]["article"].shape[1] == whole.inputs[0]["article"].shape[1] - extra.shape[1]  # the plain stage is untouched


def test_with_the_stages_of_the_study_the_gcn_gives_the_predictions_of_phase_6(task):
    graph, labels, split, _ = task
    data = baselines.Data(features.article_table(graph, LAYOUT), labels, split, graph=baselines.graph_views(graph, LAYOUT, split, "cpu"))
    expected, fitted = baselines.run_gcn(data, GCN_PARAMS, 0, GCN_TRAINING)
    training, whole = study_stages(graph, split, "gcn")
    val, test = data.rows("val"), data.rows("test")
    got, again, _ = staged.run("gcn", GCN_PARAMS, {**GCN_TRAINING, "weight_decay": GCN_PARAMS["weight_decay"]}, 0, labels, training,
                               data.rows("train"), training, val, [(training, val), (whole, test)], "cpu")
    assert again.best_epoch == fitted.best_epoch
    for rows in (val, test):
        assert np.array_equal(got[rows].astype(np.float32), expected[rows])


def rolling_run(kind, graph, labels, roles):
    """Trained on the training papers, validated on the following year predicted on the
    graph that holds it, applied to the whole graph."""
    scaled = staged.scaled_graph(graph, LAYOUT, roles == "train")
    masks = {"train": roles == "train", "val": roles != "test", "test": np.ones(len(roles), dtype=bool)}
    if kind == "gcn":
        flat = features.flatten(graph, scaled.x_dict, LAYOUT)
        stages = {name: staged.flat_stage(graph, flat, mask) for name, mask in masks.items()}
        params, training = GCN_PARAMS, {**GCN_TRAINING, "weight_decay": 0.0}
    else:
        stages = {name: staged.hetero_stage(scaled, mask) for name, mask in masks.items()}
        params, training = HETERO_PARAMS, HETERO_TRAINING
    rows = {role: np.flatnonzero((roles == role) & ~np.isnan(labels)) for role in masks}
    probabilities, fitted, _ = staged.run(kind, params, training, 0, labels, stages["train"], rows["train"], stages["val"], rows["val"],
                                          [(stages["val"], rows["val"]), (stages["test"], rows["test"])], "cpu")
    return probabilities, fitted, stages, rows


@pytest.mark.parametrize("kind", ["gcn", *hetero.KINDS])
def test_the_rolling_protocol_validates_on_the_following_year_and_never_reads_the_test_year(task, kind):
    graph, labels, split, _ = task
    roles = staged.roles_of("study", split)  # in this graph: train, then the validation year, then the test year
    probabilities, fitted, stages, rows = rolling_run(kind, graph, labels, roles)
    # the training graph holds the training papers only; the validation graph adds the validation year
    assert stages["train"].articles.tolist() == np.flatnonzero(roles == "train").tolist()
    assert stages["val"].articles.tolist() == np.flatnonzero(roles != "test").tolist()
    assert fitted.best_val_auc == pytest.approx(roc_auc_score(labels[rows["val"]], probabilities[rows["val"]]))
    assert roc_auc_score(labels[rows["test"]], probabilities[rows["test"]]) > 0.7  # ratings carry the outcome in this graph

    # the labels and the features of the test year change neither the training nor the validation
    flipped = labels.copy()
    flipped[roles == "test"] = 1 - flipped[roles == "test"]
    changed = graph.clone()
    owned = article_masks(graph, torch.from_numpy(roles == "test"))
    for node_type in ("article", "review", "critique"):
        changed[node_type].x[owned[node_type]] += 7.0
    second, again, _, _ = rolling_run(kind, changed, flipped, roles)
    assert (again.best_epoch, again.best_val_auc) == (fitted.best_epoch, fitted.best_val_auc)
    assert np.array_equal(probabilities[rows["val"]], second[rows["val"]])
    assert not np.allclose(probabilities[rows["test"]], second[rows["test"]])  # the test year is read at prediction time only

    # the labels of the validation year are read to stop the training, never in the loss:
    # with other validation labels the model of a given epoch is the same
    one_epoch = {**(GCN_TRAINING if kind == "gcn" else HETERO_TRAINING), "weight_decay": 0.0, "max_epochs": 1}
    scaled = staged.scaled_graph(graph, LAYOUT, roles == "train")
    outputs = []
    for these in (labels, np.where(roles == "val", 1 - labels, labels)):
        if kind == "gcn":
            flat = features.flatten(graph, scaled.x_dict, LAYOUT)
            train_stage, val_stage = staged.flat_stage(graph, flat, roles == "train"), staged.flat_stage(graph, flat, roles != "test")
            params = GCN_PARAMS
        else:
            train_stage, val_stage = staged.hetero_stage(scaled, roles == "train"), staged.hetero_stage(scaled, roles != "test")
            params = HETERO_PARAMS
        outputs.append(staged.run(kind, params, one_epoch, 0, these, train_stage, rows["train"], val_stage, rows["val"],
                                  [(val_stage, rows["val"])], "cpu")[0][rows["val"]])
    assert np.array_equal(*outputs)


def test_an_article_outside_the_graph_of_a_stage_cannot_be_read(task):
    graph, labels, split, _ = task
    stage = staged.hetero_stage(staged.scaled_graph(graph, LAYOUT, split == "train"), split == "train")
    with pytest.raises(ValueError, match="not in the graph"):
        stage.position(np.flatnonzero(split == "test")[:3], len(split))
    with pytest.raises(ValueError, match="unknown kind"):
        staged.build_model("gat", HETERO_PARAMS, stage, 2)


# --------------------------------------------------------------------------- reading rule
def test_a_conclusion_is_confirmed_contradicted_or_not_separated():
    from src.eval.protocol import reading

    # (a) no model above the reference: every difference expected below zero
    assert reading([-0.03, -0.02], [-0.01, -0.005], -1) == "confirmed"
    assert reading([-0.03, -0.01], [-0.01, 0.002], -1) == "not separated"   # one interval contains zero
    assert reading([-0.03, 0.001], [-0.01, 0.02], -1) == "contradicted"     # one model significantly above
    # (b) both models above the GCN: every difference expected above zero
    assert reading([0.01, 0.02], [0.03, 0.04], +1) == "confirmed"
    assert reading([-0.001, 0.02], [0.03, 0.04], +1) == "not separated"
    assert reading([-0.03, 0.02], [-0.01, 0.04], +1) == "contradicted"
    with pytest.raises(ValueError):
        reading([], [], -1)
