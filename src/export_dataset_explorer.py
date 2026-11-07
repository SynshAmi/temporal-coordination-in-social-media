"""
export_dataset_explorer.py
--------------------------
Exports the static data behind the website's Dataset Explorer to
output.dataset_explorer_dir (default config: frontend/public/data/len/):

  index.json            dataset attribution, archive vs official release, and one
                        row per event: label, counts, descriptive statistics and
                        the paper's full-graph features (run_v2)
  events/eNNN.json      one graph per event: node count, directed edges as a flat
                        integer array [s0, t0, s1, t1, ...] in the order the
                        pipeline sampled from, interaction counts, and each node's
                        core number (the paper's convention)
  samples/eNNN.json     the Study 2 observations of that event: for each budget K
                        and each of the ten sampling seeds, the indices of the K
                        sampled edges, and the stored features of that view

Only graph structure is exported: node indices (per-graph, 0..N-1, not account
identifiers), directed edges and interaction counts. Message texts, timestamps
and embeddings are never written.

The sampled edge sets are not stored by the pipeline, only their features. They
are regenerated here with exactly the pipeline's procedure (src/sample_views.py:
numpy default_rng(base_seed + seed_index) per budget and seed, events in
eligibility order), and every regenerated view is checked against the stored
features in the sampled-views file before anything is written. The full-graph
features are likewise recomputed from the exported edges and checked against
<run_dir>/study1/full_graph_features.parquet. Any mismatch, invalid edge or
missing record stops the export with a report.

Output is deterministic: fixed event order (sorted event IDs), fixed rounding,
compact JSON with sorted keys.

Usage: python src/export_dataset_explorer.py [--config configs/v2_coreness_fix.yaml]
"""

import sys
import json
import shutil
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import compute_features_for_sampled_view, edges_to_digraph, extract_structural_features  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

STRUCT = ["density", "reciprocity", "largest_wcc_fraction", "indegree_gini", "outdegree_gini", "coreness_median", "coreness_max"]
VIEW_COLS = ["log_node_count", "log_edge_count", *STRUCT, "exact_dup_proportion", "text_concentration", "msg_length_dispersion"]
TOL = 1e-9

SOURCE = {
    "dataset": "LEN-Small, a subset of LEN: Large Engagement Networks",
    "authors": "A. A. Gopalakrishnan, J. Hossain, T. Elmas and A. E. Sarıyüce",
    "paper": "Large engagement networks for classifying coordinated campaigns and organic Twitter trends",
    "venue": "Proc. Int. AAAI Conf. Web and Social Media (ICWSM), vol. 19, no. 1, pp. 688–702, 2025",
    "doi": "10.1609/icwsm.v19i1.35839",
    "project_url": "https://erdemub.github.io/large-engagement-network/",
    "licence_statement": "The dataset is released under a CC-BY license, enabling free sharing and adaptation for research or development purpose.",
    "licence_note": "Quoted from the LEN paper, which gives no licence version. Exported here: graph structure only (per-graph node indices, directed edges, interaction counts). No message text, timestamps, embeddings or account identifiers.",
}


def r6(x):
    return float(round(float(x), 6))


def name_of(event_id):
    base = event_id
    for suffix in ("_noncampaign_fulldata", "_campaign_fulldata"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    return base.replace("___", " · ")


def core_numbers_by_index(n, src, dst):
    """Core number of every node 0..n-1, as in features.core_numbers_undirected."""
    U = nx.Graph()
    U.add_nodes_from(range(n))
    U.add_edges_from((int(u), int(v)) for u, v in zip(src, dst) if u != v)
    core = nx.core_number(U)
    return [int(core[i]) for i in range(n)]


def main(config_path):
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    out = Path(cfg["output"]["dataset_explorer_dir"])
    processed, manifests = Path(cfg["data"]["processed_dir"]), Path(cfg["data"]["manifests_dir"])
    eb = cfg["edge_budgets"]
    budgets, n_seeds, base_seed = eb["K_values"], eb["n_seeds"], eb["base_seed"]

    manifest = pd.read_parquet(manifests / "manifest.parquet")
    edges = pd.read_parquet(processed / "edges.parquet")
    nodes = pd.read_parquet(processed / "nodes.parquet")
    views = pd.read_parquet(processed / eb["views_file"])
    full = pd.read_parquet(Path(cfg["output"]["run_dir"]) / "study1" / "full_graph_features.parquet")
    elig = json.loads((manifests / "edge_budget_eligibility.json").read_text(encoding="utf-8"))

    problems = []
    event_ids = sorted(manifest.event_id)
    index_of = {eid: i + 1 for i, eid in enumerate(event_ids)}
    by_event = {eid: g for eid, g in edges.groupby("event_id", sort=False)}
    nodes_by_event = nodes.groupby("event_id").node_id.apply(lambda s: sorted(int(x) for x in s)).to_dict()

    # ---- 1. Regenerate the Study 2 views exactly as src/sample_views.py drew them, and verify them
    samples = {eid: {} for eid in event_ids}
    vstore = views.set_index(["event_id", "K", "seed"]).sort_index()
    n_checked = 0
    for K in budgets:
        eligible = elig[str(K)]["eligible_event_ids"]
        for s in range(n_seeds):
            seed = base_seed + s
            rng = np.random.default_rng(seed)
            for eid in eligible:
                ev = by_event[eid]
                idx = rng.choice(len(ev), size=K, replace=False)
                lab = int(manifest.loc[manifest.event_id == eid, "label"].iloc[0])
                feats = compute_features_for_sampled_view(ev.iloc[idx].reset_index(drop=True), eid, lab, cfg)
                if (eid, K, seed) not in vstore.index:
                    problems.append(f"missing stored view {eid} K={K} seed={seed}")
                    continue
                stored = vstore.loc[(eid, K, seed)]
                bad = [c for c in VIEW_COLS if not np.isclose(feats[c], stored[c], rtol=0, atol=TOL, equal_nan=True)]
                if bad:
                    problems.append(f"regenerated view differs from stored features: {eid} K={K} seed={seed}: {bad}")
                n_checked += 1
                rec = samples[eid].setdefault(str(K), {"seeds": [], "edges": [], "features": []})
                rec["seeds"].append(seed)
                rec["edges"].append(sorted(int(i) for i in idx))
                rec["features"].append({"n_nodes": int(round(np.expm1(stored["log_node_count"]))),
                                        **{c: r6(stored[c]) for c in STRUCT}})
    expected_views = sum(len(elig[str(K)]["eligible_event_ids"]) for K in budgets) * n_seeds
    if n_checked != expected_views or len(views) != expected_views:
        problems.append(f"view count: regenerated {n_checked}, stored {len(views)}, expected {expected_views}")

    # ---- 2. Full graphs: validate structure and recompute the paper's features
    rows, graphs = [], {}
    full = full.reset_index() if "event_id" not in full.columns else full
    full = full.set_index("event_id")
    for eid in event_ids:
        m = manifest.loc[manifest.event_id == eid].iloc[0]
        ev = by_event.get(eid)
        if ev is None:
            problems.append(f"no edges for {eid}")
            continue
        n = int(m.n_nodes)
        node_ids = nodes_by_event.get(eid, [])
        if node_ids != list(range(n)):
            problems.append(f"{eid}: node ids are not 0..{n - 1}")
        src, dst = ev.source.astype(int).to_numpy(), ev.target.astype(int).to_numpy()
        if len(ev) != int(m.n_edges):
            problems.append(f"{eid}: {len(ev)} edges vs manifest {int(m.n_edges)}")
        if src.min() < 0 or dst.min() < 0 or src.max() >= n or dst.max() >= n:
            problems.append(f"{eid}: edge endpoint outside 0..{n - 1}")
        if pd.Series(list(zip(src, dst))).duplicated().any():
            problems.append(f"{eid}: repeated directed edge")
        feats = extract_structural_features(edges_to_digraph(ev))
        bad = [c for c in STRUCT if not np.isclose(feats[c], full.loc[eid, c], rtol=0, atol=TOL)]
        if bad:
            problems.append(f"{eid}: recomputed full-graph features differ from run_v2: {bad}")

        indeg, outdeg = np.bincount(dst, minlength=n), np.bincount(src, minlength=n)
        loops = src == dst
        incident = np.zeros(n, bool)
        incident[src] = True
        incident[dst] = True
        G = nx.DiGraph()
        G.add_nodes_from(range(n))
        G.add_edges_from(zip(src.tolist(), dst.tolist()))
        wcc = sorted((len(c) for c in nx.weakly_connected_components(G)), reverse=True)
        pairs = set(zip(src[~loops].tolist(), dst[~loops].tolist()))
        recip_pairs = sum(1 for (u, v) in pairs if (v, u) in pairs) // 2
        core = core_numbers_by_index(n, src, dst)
        w = ev.interaction_count.astype(int).tolist()

        i = index_of[eid]
        graphs[i] = {"i": i, "n": n, "edges": np.column_stack([src, dst]).ravel().tolist(),
                     "w": w if any(x != 1 for x in w) else None, "core": core}
        rows.append({
            "i": i, "id": eid, "name": name_of(eid), "label": int(m.label),
            "n_nodes": n, "n_edges": int(len(ev)), "n_self_loops": int(loops.sum()),
            "n_isolated": int((~incident).sum()), "n_reciprocal_pairs": int(recip_pairs),
            "n_wcc": len(wcc), "largest_wcc": wcc[0], "max_in": int(indeg.max()), "max_out": int(outdeg.max()),
            "n_interactions": int(sum(w)),
            "features": {c: r6(full.loc[eid, c]) for c in STRUCT},
            "budgets": [K for K in budgets if eid in elig[str(K)]["eligible_event_ids"]],
            "graph": f"events/e{i:03d}.json",
            "samples": f"samples/e{i:03d}.json" if samples[eid] else None,
        })

    if problems:
        print(f"EXPORT STOPPED: {len(problems)} problem(s):")
        for p in problems[:50]:
            print("  -", p)
        sys.exit(1)

    # ---- 3. Write (deterministic)
    def dump(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False),
                        encoding="utf-8")

    if out.exists():
        shutil.rmtree(out)
    lab = manifest.label
    index = {
        "schema": 1,
        "source": SOURCE,
        "archive": {
            "n_events": len(rows), "n_campaign": int((lab == 1).sum()), "n_comparison": int((lab == 0).sum()),
            "official": {"n_events": 100, "n_campaign": 51, "n_comparison": 49},
            "note": ("These are the 103 graphs of the LEN project archive analysed in the paper. The archive is distinct from the published "
                     "LEN-Small description (100 graphs), so no event is marked as belonging to the published subset."),
        },
        "budgets": budgets, "n_seeds": n_seeds, "seeds": [base_seed + s for s in range(n_seeds)],
        "verification": {"views_regenerated_and_matched": n_checked, "full_graphs_matched": len(rows), "tolerance": TOL},
        "events": rows,
    }
    dump(out / "index.json", index)
    for i, g in graphs.items():
        dump(out / f"events/e{i:03d}.json", g)
    for eid, s in samples.items():
        if s:
            dump(out / f"samples/e{index_of[eid]:03d}.json", {"i": index_of[eid], "budgets": s})
    size = sum(f.stat().st_size for f in out.rglob("*.json"))
    print(f"Dataset explorer data -> {out.as_posix()}: {len(rows)} events, {len(graphs)} graph files, "
          f"{sum(1 for s in samples.values() if s)} sample files, {size / 1e6:.1f} MB")
    print(f"Verified: {n_checked} regenerated views match the stored Study 2 features; "
          f"{len(rows)} full graphs match the run_v2 features (tolerance {TOL}).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    main(ap.parse_args().config)
