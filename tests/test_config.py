"""The default config must respect the project rules (temporal split, 5 seeds)."""

import copy

import pytest

from src.utils.config import REPO_ROOT, load_config, validate_config
from src.utils.splits import assign_split, validation_score


@pytest.fixture()
def cfg():
    return load_config()


def test_default_config_loads(cfg):
    assert cfg["project"]["venue"] == "ICLR"
    assert cfg["years"] == sorted(cfg["years"])


def test_split_years_are_disjoint_and_cover_years(cfg):
    splits = cfg["splits"]
    groups = [splits["train"], splits["test"], splits.get("holdout", [])]
    assert sum(map(len, groups)) == len(set().union(*groups))
    assert set().union(*groups) == set(cfg["years"])


def test_test_years_come_after_training_years_and_holdout_years_after_them(cfg):
    splits = cfg["splits"]
    assert max(splits["train"]) < min(splits["test"])
    assert all(year > max(splits["test"]) for year in splits.get("holdout", []))


def test_holdout_years_are_kept_apart(cfg):
    splits = copy.deepcopy(cfg["splits"])
    splits["holdout"] = [2031]
    assert {assign_split(f"forum{i}", 2031, splits) for i in range(200)} == {"holdout"}
    early = copy.deepcopy(cfg)
    early["splits"]["holdout"], early["years"] = [2020], sorted({*early["splits"]["train"], *early["splits"]["test"], 2020})
    with pytest.raises(ValueError, match="holdout"):
        validate_config(early)
    shared = copy.deepcopy(cfg)
    shared["splits"]["holdout"] = list(shared["splits"]["test"])
    with pytest.raises(ValueError, match="several splits"):
        validate_config(shared)


def test_five_distinct_seeds(cfg):
    assert len(cfg["seeds"]) == 5
    assert len(set(cfg["seeds"])) == 5


def test_paths_are_inside_repo(cfg):
    for path in cfg["paths"].values():
        assert path.is_absolute()
        assert REPO_ROOT in path.parents


def test_non_temporal_split_is_rejected(cfg):
    bad = copy.deepcopy(cfg)
    bad["splits"]["train"], bad["splits"]["test"] = bad["splits"]["test"], bad["splits"]["train"]
    with pytest.raises(ValueError):
        validate_config(bad)


def test_overlapping_split_is_rejected(cfg):
    bad = copy.deepcopy(cfg)
    bad["splits"]["test"] = bad["splits"]["test"] + bad["splits"]["train"]
    with pytest.raises(ValueError):
        validate_config(bad)


def test_wrong_number_of_seeds_is_rejected(cfg):
    bad = copy.deepcopy(cfg)
    bad["seeds"] = bad["seeds"][:3]
    with pytest.raises(ValueError):
        validate_config(bad)


def test_split_assignment_is_by_year_and_deterministic(cfg):
    splits = cfg["splits"]
    test_year, train_year = splits["test"][0], splits["train"][0]
    ids = [f"forum{i:05d}" for i in range(4000)]

    # A test-year submission is always in the test set, whatever its id.
    assert {assign_split(i, test_year, splits) for i in ids} == {"test"}
    # Training-year submissions go to train or val, never to test.
    assigned = [assign_split(i, train_year, splits) for i in ids]
    assert set(assigned) == {"train", "val"}
    # Same assignment at every call, close to the configured fraction.
    assert assigned == [assign_split(i, train_year, splits) for i in ids]
    share = assigned.count("val") / len(ids)
    assert abs(share - splits["validation"]["fraction"]) < 0.03
    assert 0 <= validation_score("x", "salt") < 1


def test_unknown_year_is_rejected(cfg):
    with pytest.raises(ValueError):
        assign_split("x", 1999, cfg["splits"])
