"""Articles to explain: the same number in each group, chosen by a hash of their id."""

import hashlib

import numpy as np
import pandas as pd

GROUPS = ("accepted_borderline", "accepted_other", "rejected_borderline", "rejected_other")


def hash_order(forum_id: str, salt: str) -> int:
    return int(hashlib.sha256(f"{salt}:{forum_id}".encode()).hexdigest()[:16], 16)


def explained_articles(forum_ids: np.ndarray, labels: np.ndarray, borderline: np.ndarray, candidates: np.ndarray,
                       per_group: int, salt: str) -> pd.DataFrame:
    """`per_group` articles of each group (accepted or rejected, borderline or not)
    among `candidates` (article indices with a decision), in the order of a hash of
    their id: independent of every seed, and a smaller sample is a prefix of a larger
    one. Columns: article_index, forum_id, label, borderline, group, rank (in its
    group), population (size of the group among the candidates)."""
    table = pd.DataFrame({"article_index": candidates, "forum_id": forum_ids[candidates],
                          "label": labels[candidates].astype(int), "borderline": borderline[candidates]})
    table["group"] = np.where(table["label"] == 1, "accepted", "rejected") + np.where(table["borderline"], "_borderline", "_other")
    table["order"] = [hash_order(forum_id, salt) for forum_id in table["forum_id"]]
    table = table.sort_values(["group", "order"], kind="stable")
    table["rank"] = table.groupby("group").cumcount()
    table["population"] = table.groupby("group")["forum_id"].transform("size")
    return table[table["rank"] < per_group].drop(columns="order").reset_index(drop=True)
