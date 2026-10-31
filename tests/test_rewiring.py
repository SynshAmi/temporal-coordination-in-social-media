"""Invariant tests for the directed degree-preserving null model."""

import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rewiring import rewire_directed, assert_degree_preserved  # noqa: E402
from features import extract_structural_features  # noqa: E402


def _graph():
    G = nx.gnp_random_graph(60, 0.08, seed=3, directed=True)
    G.add_edges_from([(0, 0), (5, 5), (17, 17)])
    return G


def test_invariants_hold():
    G = _graph()
    R, stats = rewire_directed(G, swaps_per_edge=10, seed=1, return_stats=True)
    assert_degree_preserved(G, R)
    assert stats["swaps"] > 0
    assert stats["frac_edges_unchanged"] < 0.5


def test_no_new_self_loops_or_multiedges():
    G = _graph()
    R = rewire_directed(G, swaps_per_edge=10, seed=2)
    assert {u for u, v in R.edges() if u == v} == {0, 5, 17}
    assert isinstance(R, nx.DiGraph) and not R.is_multigraph()


def test_degree_features_preserved_exactly():
    G = _graph()
    R = rewire_directed(G, swaps_per_edge=10, seed=4)
    fg, fr = extract_structural_features(G), extract_structural_features(R)
    for k in ("density", "indegree_gini", "outdegree_gini"):
        assert fg[k] == fr[k]


def test_deterministic_given_seed():
    G = _graph()
    assert set(rewire_directed(G, 5, seed=9).edges()) == set(rewire_directed(G, 5, seed=9).edges())
