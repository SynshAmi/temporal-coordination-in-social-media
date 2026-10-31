"""
rewiring.py
-----------
Directed degree-preserving null graphs for the Study 1 topology null.

Null model (documented assumptions):
  * Input: a directed simple graph (no repeated (u, v) pairs) that may contain
    self-loops.
  * Self-loops are held fixed: they are removed before swapping and added back
    unchanged, so each node's self-loop status is preserved.
  * Non-loop edges are rewired by directed double-edge swaps:
        (a, b), (c, d)  ->  (a, d), (c, b)
    accepted only if a != d, c != b (no new self-loops) and neither new edge
    already exists (no multi-edges). This preserves every node's out-degree and
    in-degree among non-loop edges, the node set, |E|, and therefore density and
    the in/out-degree Gini coefficients exactly.
  * It randomises reciprocity, connectivity and core structure subject to the
    degree sequences. Directed double-edge swaps alone do not connect the full
    space of digraphs with given degrees (some configurations need 3-cycle
    reversals), so this is a degree-preserving null, not a uniform sample.
  * Realisations of the same event are nested within that event; they are not
    independent observations.
"""

import networkx as nx
import numpy as np


def rewire_directed(G: nx.DiGraph, swaps_per_edge: float, seed: int, return_stats: bool = False):
    rng = np.random.default_rng(seed)
    loops = [(u, v) for u, v in G.edges() if u == v]
    edges = [(u, v) for u, v in G.edges() if u != v]
    m = len(edges)
    present = set(edges)
    target = int(round(swaps_per_edge * m))
    done = tries = 0
    max_tries = max(10 * target, 1000)
    while done < target and tries < max_tries and m >= 2:
        tries += 1
        i, j = rng.integers(0, m, size=2)
        if i == j:
            continue
        a, b = edges[i]
        c, d = edges[j]
        if a == d or c == b or a == c or b == d:
            continue
        if (a, d) in present or (c, b) in present:
            continue
        present.discard((a, b)); present.discard((c, d))
        present.add((a, d)); present.add((c, b))
        edges[i] = (a, d)
        edges[j] = (c, b)
        done += 1
    R = nx.DiGraph()
    R.add_nodes_from(G.nodes())
    R.add_edges_from(edges)
    R.add_edges_from(loops)
    if return_stats:
        orig = set((u, v) for u, v in G.edges() if u != v)
        stats = {"swaps": done, "tries": tries, "target": target,
                 "frac_edges_unchanged": len(orig & set(edges)) / max(m, 1)}
        return R, stats
    return R


def assert_degree_preserved(G: nx.DiGraph, R: nx.DiGraph) -> None:
    """Invariants of the null model; raises AssertionError on any violation."""
    assert set(G.nodes()) == set(R.nodes())
    assert G.number_of_edges() == R.number_of_edges()
    assert dict(G.in_degree()) == dict(R.in_degree())
    assert dict(G.out_degree()) == dict(R.out_degree())
    assert set(u for u, v in G.edges() if u == v) == set(u for u, v in R.edges() if u == v)
