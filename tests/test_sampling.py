"""
test_sampling.py
----------------
Tests for edge sampling correctness and determinism.
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import MANIFESTS_DIR, VIEWS_PATH  # noqa: E402


@pytest.fixture(scope="module")
def views_df():
    path = VIEWS_PATH
    if not path.exists():
        pytest.skip(f"{path.name} not found - run src/sample_views.py first")
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def manifest():
    return pd.read_parquet(MANIFESTS_DIR / "manifest.parquet")


def test_sampled_view_columns(views_df):
    required = {"event_id", "label", "K", "seed", "log_node_count", "log_edge_count"}
    assert required.issubset(set(views_df.columns))


def test_sampled_node_count_le_original(views_df, manifest):
    merged = views_df.merge(manifest[["event_id", "n_nodes"]], on="event_id")
    sampled_nodes = np.expm1(merged["log_node_count"])
    original_nodes = merged["n_nodes"]
    assert (sampled_nodes <= original_nodes + 1e-5).all(), "Sampled view has more nodes than original graph!"


def test_K_seeds_are_unique(views_df):
    n_rows = len(views_df)
    n_unique = views_df.groupby(["event_id", "K", "seed"]).ngroups
    assert n_rows == n_unique, "Duplicate (event_id, K, seed) rows found"


def test_determinism(views_df):
    dupes = views_df.duplicated(subset=["event_id", "K", "seed"], keep=False)
    assert not dupes.any(), "Non-unique (event, K, seed) entries found"
