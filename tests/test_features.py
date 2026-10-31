"""
Regression tests for structural features (coreness convention, self-loops)
and for frozen-model (D1) fold alignment.
"""

import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from features import core_numbers_undirected, edges_to_digraph, extract_structural_features  # noqa: E402
from train import frozen_model_test_events  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import PROCESSED_DIR as PROCESSED, require  # noqa: E402


def test_coreness_ignores_self_loops():
    # Triangle 0-1-2 (one reciprocal pair) plus a pendant node 3 and self-loops.
    G = nx.DiGraph([(0, 1), (1, 0), (1, 2), (2, 0), (2, 3), (0, 0), (3, 3)])
    cores = dict(zip(G.nodes(), core_numbers_undirected(G)))
    assert cores == {0: 2.0, 1: 2.0, 2: 2.0, 3: 1.0}


def test_self_loop_only_node_has_core_zero():
    G = nx.DiGraph([(0, 1), (5, 5)])
    cores = dict(zip(G.nodes(), core_numbers_undirected(G)))
    assert cores[5] == 0.0 and cores[0] == 1.0


def test_structural_features_nonzero_coreness_with_self_loops():
    G = nx.DiGraph([(0, 1), (1, 2), (2, 0), (0, 0)])
    f = extract_structural_features(G)
    assert f["coreness_max"] == 2.0 and f["coreness_median"] == 2.0


def test_core_number_errors_are_not_swallowed(monkeypatch):
    def boom(_):
        raise RuntimeError("unexpected")
    monkeypatch.setattr(nx, "core_number", boom)
    with pytest.raises(RuntimeError):
        extract_structural_features(nx.DiGraph([(0, 1)]))


def test_real_graphs_have_varying_coreness():
    require(PROCESSED / "edges.parquet", "Processed edge table")
    edges = pd.read_parquet(PROCESSED / "edges.parquet")
    sample = edges["event_id"].drop_duplicates().sort_values().head(8)
    vals = []
    for eid in sample:
        ev = edges[edges["event_id"] == eid]
        assert (ev.source == ev.target).any(), "fixture expects self-loops in real graphs"
        vals.append(extract_structural_features(edges_to_digraph(ev))["coreness_max"])
    assert min(vals) >= 1.0
    assert len(set(vals)) > 1, "coreness_max must not be constant across events"


def test_frozen_models_only_score_held_out_events():
    full = {"a": 0, "b": 1, "c": 0, "d": 2, "e": 1}
    eligible = ["a", "b", "c", "d"]
    assert frozen_model_test_events(full, eligible, 0) == ["a", "c"]
    assert frozen_model_test_events(full, eligible, 1) == ["b"]
    # every eligible event is scored by exactly one model, its own held-out fold
    scored = [e for k in range(3) for e in frozen_model_test_events(full, eligible, k)]
    assert sorted(scored) == sorted(eligible)
