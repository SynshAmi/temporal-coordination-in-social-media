"""
splits.py
---------
Create event-level stratified k-fold splits.

LEAKAGE RULE: all sampled views of one event must stay in the same fold.
Splitting is performed at the event level; views are mapped to their event's fold.
"""

import pandas as pd
from sklearn.model_selection import StratifiedKFold


def make_event_folds(
    manifest: pd.DataFrame,
    n_folds: int = 5,
    random_seed: int = 42,
) -> dict[str, int]:
    """
    Returns {event_id: fold_index} with stratified splits on manifest['label'].
    """
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_seed)
    event_ids = manifest["event_id"].values
    labels = manifest["label"].values

    fold_map: dict[str, int] = {}
    for fold_idx, (_, test_idx) in enumerate(skf.split(event_ids, labels)):
        for i in test_idx:
            fold_map[event_ids[i]] = fold_idx

    return fold_map


def assign_view_folds(
    views_df: pd.DataFrame,
    event_fold_map: dict[str, int],
) -> pd.DataFrame:
    """
    Assign fold_id to each row of a views DataFrame using event_fold_map.
    """
    views_df = views_df.copy()
    views_df["fold_id"] = views_df["event_id"].map(event_fold_map)
    n_missing = views_df["fold_id"].isna().sum()
    if n_missing > 0:
        print(f"WARNING: {n_missing} view rows have event_ids not in fold map - dropped.")
        views_df = views_df.dropna(subset=["fold_id"])
    views_df["fold_id"] = views_df["fold_id"].astype(int)
    return views_df
