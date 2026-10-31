"""
test_leakage.py
----------------
Tests that all views of an event remain strictly in the same fold (no view leakage).
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from splits import make_event_folds, assign_view_folds

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import MANIFESTS_DIR, VIEWS_PATH, require  # noqa: E402


@pytest.fixture(scope="module")
def manifest():
    path = MANIFESTS_DIR / "manifest.parquet"
    require(path, "Event manifest")
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def views_df():
    require(VIEWS_PATH, "Sampled edge views")
    return pd.read_parquet(VIEWS_PATH)


def test_views_stay_in_same_fold(manifest, views_df):
    fold_map = make_event_folds(manifest, n_folds=5, random_seed=42)
    views_with_folds = assign_view_folds(views_df.copy(), fold_map)

    event_folds = views_with_folds.groupby("event_id")["fold_id"].nunique()
    leaking = event_folds[event_folds > 1]
    assert leaking.empty, f"Events with views across multiple folds: {leaking.index.tolist()}"


def test_fold_distribution_balanced(manifest):
    fold_map = make_event_folds(manifest, n_folds=5, random_seed=42)
    df = manifest.copy()
    df["fold_id"] = df["event_id"].map(fold_map)

    for fold_idx in range(5):
        fold_df = df[df["fold_id"] == fold_idx]
        n_camp = (fold_df["label"] == 1).sum()
        n_comp = (fold_df["label"] == 0).sum()
        ratio = n_camp / max(len(fold_df), 1)
        assert 0.35 <= ratio <= 0.65, f"Fold {fold_idx} imbalanced: {n_camp} camp, {n_comp} comp"
