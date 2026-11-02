"""
test_dataset_explorer.py
------------------------
The Dataset Explorer's static files (src/export_dataset_explorer.py) must describe
the archive exactly, contain graph structure only, and index valid sampled edges.
These checks run on the committed files, so they also run on a fresh clone.
"""

import sys
import json
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import CFG, MANIFESTS_DIR, ROOT  # noqa: E402

DIR = ROOT / CFG["output"]["dataset_explorer_dir"]
INDEX = DIR / "index.json"
pytestmark = pytest.mark.skipif(not INDEX.exists(), reason="run src/export_dataset_explorer.py first")


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_index_matches_manifest():
    import pandas as pd
    idx = load(INDEX)
    man = pd.read_parquet(MANIFESTS_DIR / "manifest.parquet").set_index("event_id")
    assert [e["i"] for e in idx["events"]] == list(range(1, len(man) + 1))
    assert sorted(e["id"] for e in idx["events"]) == sorted(man.index)
    for e in idx["events"]:
        row = man.loc[e["id"]]
        assert (e["label"], e["n_nodes"], e["n_edges"]) == (int(row.label), int(row.n_nodes), int(row.n_edges))
    a = idx["archive"]
    assert (a["n_events"], a["n_campaign"], a["n_comparison"]) == (len(man), int((man.label == 1).sum()), int((man.label == 0).sum()))
    assert a["official"] == {"n_events": 100, "n_campaign": 51, "n_comparison": 49}


def test_graph_files_hold_structure_only_and_valid_edges():
    for e in load(INDEX)["events"]:
        g = load(DIR / e["graph"])
        assert set(g) == {"i", "n", "edges", "w", "core"}, "graph files must contain structure only"
        n, edges = g["n"], g["edges"]
        assert n == e["n_nodes"] and len(edges) == 2 * e["n_edges"] and len(g["core"]) == n
        assert min(edges) >= 0 and max(edges) < n
        pairs = list(zip(edges[::2], edges[1::2]))
        assert len(set(pairs)) == len(pairs)
        assert sum(s == t for s, t in pairs) == e["n_self_loops"]
        assert g["w"] is None or (len(g["w"]) == e["n_edges"] and min(g["w"]) >= 1)


def test_samples_index_valid_edge_sets():
    idx = load(INDEX)
    for e in idx["events"]:
        if not e["budgets"]:
            assert e["samples"] is None and e["n_edges"] < min(idx["budgets"])
            continue
        s = load(DIR / e["samples"])
        assert sorted(int(k) for k in s["budgets"]) == e["budgets"]
        for k, rec in s["budgets"].items():
            assert rec["seeds"] == idx["seeds"]
            for edges, f in zip(rec["edges"], rec["features"]):
                assert len(edges) == len(set(edges)) == int(k)
                assert 0 <= min(edges) and max(edges) < e["n_edges"]
                assert 0 < f["n_nodes"] <= min(2 * int(k), e["n_nodes"])


def test_no_message_text_or_timestamps_exported():
    for f in DIR.rglob("*.json"):
        text = f.read_text(encoding="utf-8")
        for key in ('"text"', '"timestamp"', '"embedding"', '"user'):
            assert key not in text, f"{f.name} contains {key}"
