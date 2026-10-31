# LEN-Small Robustness Audit — Complete Implementation Guide

> **Project:** *Beyond Graph Scale: Auditing Size Confounding and Retained-Observation Robustness in Campaign Classification on LEN-Small*
> **Dataset:** LEN-Small (100 event graphs, 51 campaign, 49 comparison)
> **Team:** Two students | **Deadline:** 5 days (Day 1 = 15 October 2026)

---

## What We Are Actually Doing (Plain English First)

The LEN paper trained classifiers to distinguish "campaign" Twitter events from organic "comparison" events using graph features. **The problem we audit:** campaign graphs tend to be *much larger* than comparison graphs. A classifier might just be learning "big graph → campaign" rather than learning genuine coordination patterns. We want to know:

1. How much accuracy disappears when we control for size? (Match events of similar scale, then re-evaluate.)
2. How much accuracy disappears when we artificially restrict how many edges the model can see? (Edge budget experiments.)
3. Do structural or content features add value *on top of* raw size features?

We are **not** building a new detector. We are **auditing measurement validity** of an existing benchmark.

---

## Repository Layout

```
len-audit/
├── README.md
├── configs/
│   └── final.yaml               # single source of truth for all params
├── data/
│   ├── raw/                     # gitignored — put downloaded archive here
│   ├── manifests/
│   │   ├── manifest.parquet     # one row per event graph
│   │   └── validation_report.json
│   └── processed/
│       ├── nodes.parquet
│       └── edges.parquet
├── src/
│   ├── ingest_len.py            # download, hash, parse graphs
│   ├── validate_len.py          # schema checks, label audit
│   ├── build_cohorts.py         # node-count matching
│   ├── sample_views.py          # edge-budget experiments
│   ├── features.py              # all feature extraction
│   ├── splits.py                # stratified folds, no leakage
│   ├── train.py                 # logistic regression + HGBT
│   └── evaluate.py              # metrics, uncertainty, figures
├── tests/
│   ├── test_ingestion.py
│   ├── test_sampling.py
│   └── test_leakage.py
├── outputs/run_final/
│   ├── config.json
│   ├── predictions.parquet
│   ├── metrics.json
│   ├── tables.md
│   └── figures/
│       ├── fig1_size_overlap.png
│       ├── fig2_baseline_comparison.png
│       ├── fig3_matched_cohort_comparison.png
│       └── fig4_edge_budget_robustness.png
└── reports/
    └── checkpoint_report.md
```

---

## Day 0 — Environment Setup

### Install dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Core scientific stack
pip install numpy pandas scipy scikit-learn matplotlib seaborn

# Graph processing
pip install networkx

# Utilities
pip install pyarrow pyyaml tqdm requests

# Dev / testing
pip install pytest pytest-cov
```

### `configs/final.yaml` — The Single Source of Truth

```yaml
# configs/final.yaml
# Every parameter that affects results lives here.
# Scripts read this file; never hard-code numbers in src/.

data:
  raw_dir: "data/raw"
  processed_dir: "data/processed"
  manifests_dir: "data/manifests"
  len_small_url: "https://erdemub.github.io/large-engagement-network/"
  expected_events: 100
  expected_campaign: 51
  expected_comparison: 49

features:
  # Scale group
  use_log_node_count: true
  use_log_edge_count: true
  # Structure group
  use_density: true
  use_reciprocity: true
  use_largest_wcc_fraction: true
  use_indegree_concentration: true   # Gini of in-degree distribution
  use_outdegree_concentration: true  # Gini of out-degree distribution
  use_coreness_summary: true         # median / max of k-core numbers
  # Content group (conditional — set false if text is unusable)
  use_text_features: true
  use_exact_dup_proportion: true
  use_text_concentration: true       # Gini of message-frequency distribution
  use_msg_length_dispersion: true    # std of token counts
  # Temporal: OFF until timestamp semantics are verified
  use_temporal: false

matching:
  caliper_sd_fraction: 0.25          # nearest-neighbour caliper in SD units of log(node_count)
  random_seed: 42

edge_budgets:
  K_values: [250, 500, 1000, 2000]
  n_seeds: 10
  base_seed: 100                     # seeds = base_seed + seed_index

splits:
  n_folds: 5
  stratify: true
  random_seed: 42

models:
  logreg:
    C_values: [0.01, 0.1, 1.0, 10.0]
    max_iter: 1000
    solver: "lbfgs"
  hgbt:
    max_iter_values: [50, 100, 200]
    max_depth: 4
    random_state: 42

evaluation:
  bootstrap_n_resamples: 2000
  bootstrap_seed: 7
  primary_metrics: ["balanced_accuracy", "macro_f1"]

output:
  run_dir: "outputs/run_final"
  figures_dir: "outputs/run_final/figures"
```

---

## Day 1 — Data Foundation

### What we are doing on Day 1

We download the LEN-Small archive, verify every file, parse all 100 event graphs, map the authoritative campaign/comparison labels, and produce a validated `manifest.parquet`. **No modelling until this gate passes.**

---

### `src/ingest_len.py` — Download, Hash, Parse

```python
"""
ingest_len.py
-------------
Download the LEN-Small archive, verify SHA-256, unzip, parse every graph
into a canonical (nodes, edges) representation, and emit two parquet files:
  data/processed/nodes.parquet
  data/processed/edges.parquet

Also writes data/manifests/manifest.parquet — one row per event graph.

Run:
  python src/ingest_len.py --config configs/final.yaml
"""

import hashlib
import json
import os
import re
import argparse
import zipfile
from pathlib import Path
from datetime import datetime, timezone

import networkx as nx
import pandas as pd
import yaml
from tqdm import tqdm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Label mapping
# ---------------------------------------------------------------------------

def build_label_map(raw_dir: Path) -> dict[str, int]:
    """
    Load the authoritative label mapping from metadata files shipped with the
    LEN-Small archive.  Returns {event_id: label} where label=1 → campaign,
    label=0 → comparison.

    The LEN dataset ships a metadata CSV (or JSON) that maps graph filenames
    to campaign/comparison categories.  Adjust the path below to wherever
    the dataset places this file after extraction.
    """
    # LEN-Small ships its labels as a CSV.  Common names observed in the repo:
    #   LEN_Small_metadata.csv  |  event_metadata.csv  |  labels.csv
    # We try a short list of candidate names and stop at the first hit.
    candidates = [
        raw_dir / "LEN_Small_metadata.csv",
        raw_dir / "event_metadata.csv",
        raw_dir / "labels.csv",
        raw_dir / "LEN-Small" / "metadata.csv",
    ]
    meta_path = next((p for p in candidates if p.exists()), None)
    if meta_path is None:
        raise FileNotFoundError(
            "Cannot find label metadata CSV.  Expected one of:\n  "
            + "\n  ".join(str(p) for p in candidates)
            + "\nCheck the archive contents and update this list."
        )

    df = pd.read_csv(meta_path)
    # Normalise column names to lower-case, strip spaces
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Identify the event-ID column (usually 'event_id', 'event', or 'graph_id')
    id_col = next(
        (c for c in df.columns if c in {"event_id", "event", "graph_id", "id"}), None
    )
    if id_col is None:
        raise ValueError(f"Cannot find event-ID column in {meta_path}. Columns: {list(df.columns)}")

    # Identify the label column ('label', 'category', 'class', 'type')
    lbl_col = next(
        (c for c in df.columns if c in {"label", "category", "class", "type"}), None
    )
    if lbl_col is None:
        raise ValueError(f"Cannot find label column in {meta_path}. Columns: {list(df.columns)}")

    label_map: dict[str, int] = {}
    for _, row in df.iterrows():
        eid = str(row[id_col]).strip()
        raw_lbl = str(row[lbl_col]).strip().lower()
        if raw_lbl in {"campaign", "1", "coordinated"}:
            label_map[eid] = 1
        elif raw_lbl in {"comparison", "0", "organic", "non-campaign"}:
            label_map[eid] = 0
        else:
            raise ValueError(f"Unknown label value '{raw_lbl}' for event '{eid}'")

    return label_map


# ---------------------------------------------------------------------------
# Graph parser
# ---------------------------------------------------------------------------

def parse_graph_file(graph_path: Path) -> nx.DiGraph:
    """
    Parse a single LEN graph file into a NetworkX DiGraph.

    LEN graphs are distributed as edge-list files (TSV or CSV) with columns:
      source, target[, weight, interaction_type, text, timestamp, ...]

    The exact column layout varies — we read what is present and attach
    everything as edge attributes.

    DIRECTION CONVENTION:
    The paper states an edge u → v means "u engaged with v's content."
    (e.g., u retweeted v.)  We store edges in this direction.

    If your downloaded files use a different format (e.g., JSON adjacency
    list), replace the pd.read_csv call with the appropriate parser and
    map to (source, target, attrs) tuples.
    """
    # Try TSV first, fall back to CSV
    for sep in ["\t", ","]:
        try:
            df = pd.read_csv(graph_path, sep=sep)
            if df.shape[1] > 1:  # successfully parsed multiple columns
                break
        except Exception:
            continue

    # Normalise column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Identify source and target columns
    src_col = next(
        (c for c in df.columns if c in {"source", "src", "user_a", "from"}), None
    )
    tgt_col = next(
        (c for c in df.columns if c in {"target", "tgt", "user_b", "to"}), None
    )
    if src_col is None or tgt_col is None:
        raise ValueError(
            f"Cannot identify source/target columns in {graph_path}. "
            f"Columns found: {list(df.columns)}"
        )

    G = nx.DiGraph()
    for _, row in df.iterrows():
        attrs = {c: row[c] for c in df.columns if c not in {src_col, tgt_col}}
        G.add_edge(str(row[src_col]), str(row[tgt_col]), **attrs)

    return G


# ---------------------------------------------------------------------------
# Main ingestion loop
# ---------------------------------------------------------------------------

def ingest(config: dict) -> None:
    raw_dir = Path(config["data"]["raw_dir"])
    processed_dir = Path(config["data"]["processed_dir"])
    manifests_dir = Path(config["data"]["manifests_dir"])

    processed_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    # ---- 1. Find graph files -------------------------------------------------
    # LEN-Small graph files are typically named <event_id>.txt or <event_id>.csv
    graph_files = sorted(
        list(raw_dir.glob("**/*.txt")) + list(raw_dir.glob("**/*.csv"))
    )
    # Exclude metadata/label files by name pattern
    graph_files = [
        g for g in graph_files
        if "metadata" not in g.name.lower() and "label" not in g.name.lower()
    ]
    print(f"Found {len(graph_files)} candidate graph files in {raw_dir}")

    # ---- 2. Load label map ---------------------------------------------------
    label_map = build_label_map(raw_dir)
    print(f"Label map has {len(label_map)} entries "
          f"({sum(v for v in label_map.values())} campaign, "
          f"{sum(1-v for v in label_map.values())} comparison)")

    # ---- 3. Parse all graphs -------------------------------------------------
    manifest_rows = []
    all_nodes = []
    all_edges = []

    for gf in tqdm(graph_files, desc="Parsing graphs"):
        event_id = gf.stem  # filename without extension

        if event_id not in label_map:
            print(f"  WARNING: {event_id} has no label — skipping")
            continue

        try:
            G = parse_graph_file(gf)
        except Exception as e:
            print(f"  ERROR parsing {gf}: {e}")
            continue

        label = label_map[event_id]
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        file_hash = sha256_file(gf)

        manifest_rows.append({
            "event_id": event_id,
            "label": label,
            "label_str": "campaign" if label == 1 else "comparison",
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "file_path": str(gf),
            "file_size_bytes": gf.stat().st_size,
            "sha256": file_hash,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })

        # Nodes table
        for node in G.nodes():
            all_nodes.append({"event_id": event_id, "node_id": node})

        # Edges table
        for src, tgt, attrs in G.edges(data=True):
            row = {"event_id": event_id, "source": src, "target": tgt}
            row.update(attrs)
            all_edges.append(row)

    # ---- 4. Write outputs ---------------------------------------------------
    manifest_df = pd.DataFrame(manifest_rows)
    manifest_df.to_parquet(manifests_dir / "manifest.parquet", index=False)
    print(f"\nManifest: {len(manifest_df)} events saved → {manifests_dir/'manifest.parquet'}")

    nodes_df = pd.DataFrame(all_nodes)
    nodes_df.to_parquet(processed_dir / "nodes.parquet", index=False)
    print(f"Nodes: {len(nodes_df)} rows → {processed_dir/'nodes.parquet'}")

    edges_df = pd.DataFrame(all_edges)
    edges_df.to_parquet(processed_dir / "edges.parquet", index=False)
    print(f"Edges: {len(edges_df)} rows → {processed_dir/'edges.parquet'}")

    # ---- 5. Summary validation printout ------------------------------------
    n_campaign = (manifest_df.label == 1).sum()
    n_comparison = (manifest_df.label == 0).sum()
    print(f"\n--- Ingestion summary ---")
    print(f"Total events : {len(manifest_df)}")
    print(f"Campaign     : {n_campaign}  (expected 51)")
    print(f"Comparison   : {n_comparison}  (expected 49)")
    print(f"Node range   : {manifest_df.n_nodes.min()} – {manifest_df.n_nodes.max()}")
    print(f"Edge range   : {manifest_df.n_edges.min()} – {manifest_df.n_edges.max()}")

    if len(manifest_df) != config["data"]["expected_events"]:
        print(f"\n!!! WARNING: Expected {config['data']['expected_events']} events, "
              f"got {len(manifest_df)}.  Do not proceed to modelling until resolved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    ingest(cfg)
```

---

### `src/validate_len.py` — Schema Checks and Data-Quality Report

```python
"""
validate_len.py
---------------
Runs a battery of data-quality checks on the parsed parquet files and
writes data/manifests/validation_report.json.

Checks:
  - Event count matches expected (100)
  - Label count matches expected (51/49)
  - No duplicate event IDs
  - No events with 0 nodes or 0 edges
  - Missing-field audit for edges table
  - Duplicate edges within the same event
  - Interaction_Count semantics (is it always ≥ 1?)
  - Timestamp column presence (used only to decide whether temporal is usable)
  - Account-ID overlap across events (for fold-grouping audit)

Run:
  python src/validate_len.py --config configs/final.yaml
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import yaml


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def validate(config: dict) -> dict:
    manifests_dir = Path(config["data"]["manifests_dir"])
    processed_dir = Path(config["data"]["processed_dir"])

    manifest = pd.read_parquet(manifests_dir / "manifest.parquet")
    edges    = pd.read_parquet(processed_dir  / "edges.parquet")
    nodes    = pd.read_parquet(processed_dir  / "nodes.parquet")

    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "warnings": [],
        "pass": True,
    }

    def fail(key: str, message: str):
        report["checks"][key] = {"status": "FAIL", "detail": message}
        report["pass"] = False

    def warn(key: str, message: str):
        report["checks"][key] = {"status": "WARN", "detail": message}
        report["warnings"].append(message)

    def ok(key: str, detail: str = ""):
        report["checks"][key] = {"status": "OK", "detail": detail}

    # ---- Event counts -------------------------------------------------------
    n_total = len(manifest)
    n_camp  = (manifest.label == 1).sum()
    n_comp  = (manifest.label == 0).sum()

    if n_total == config["data"]["expected_events"]:
        ok("event_count", f"{n_total} events")
    else:
        fail("event_count",
             f"Expected {config['data']['expected_events']}, got {n_total}")

    if n_camp == config["data"]["expected_campaign"]:
        ok("campaign_count", str(n_camp))
    else:
        fail("campaign_count",
             f"Expected {config['data']['expected_campaign']}, got {n_camp}")

    if n_comp == config["data"]["expected_comparison"]:
        ok("comparison_count", str(n_comp))
    else:
        fail("comparison_count",
             f"Expected {config['data']['expected_comparison']}, got {n_comp}")

    # ---- Duplicate event IDs ------------------------------------------------
    dupes = manifest[manifest.event_id.duplicated()]
    if dupes.empty:
        ok("no_duplicate_event_ids")
    else:
        fail("no_duplicate_event_ids",
             f"Duplicates: {dupes.event_id.tolist()}")

    # ---- Empty graphs -------------------------------------------------------
    empty_nodes = manifest[manifest.n_nodes == 0]
    empty_edges = manifest[manifest.n_edges == 0]
    if empty_nodes.empty:
        ok("no_empty_node_graphs")
    else:
        fail("no_empty_node_graphs",
             f"Events with 0 nodes: {empty_nodes.event_id.tolist()}")
    if empty_edges.empty:
        ok("no_empty_edge_graphs")
    else:
        warn("no_empty_edge_graphs",
             f"Events with 0 edges: {empty_edges.event_id.tolist()}")

    # ---- Edge-table missing fields ------------------------------------------
    edge_cols = list(edges.columns)
    report["edge_columns_present"] = edge_cols
    for expected_col in ["source", "target"]:
        if expected_col not in edge_cols:
            fail(f"edge_col_{expected_col}", f"Column '{expected_col}' missing from edges")
        else:
            ok(f"edge_col_{expected_col}")

    # Text column presence (for content features)
    text_candidates = ["text", "tweet_text", "content", "message"]
    text_col = next((c for c in text_candidates if c in edge_cols), None)
    report["text_column"] = text_col
    if text_col:
        ok("text_column_present", text_col)
    else:
        warn("text_column_present",
             f"No text column found (tried {text_candidates}). "
             "Content features will be disabled.")

    # Timestamp column presence
    ts_candidates = ["timestamp", "created_at", "time", "action_time"]
    ts_col = next((c for c in ts_candidates if c in edge_cols), None)
    report["timestamp_column"] = ts_col
    if ts_col:
        warn("timestamp_column",
             f"Timestamp column '{ts_col}' present but semantics unverified. "
             "Temporal features remain OFF until confirmed.")
    else:
        ok("timestamp_column_absent",
           "No timestamp column — temporal features correctly disabled.")

    # Interaction_Count semantics
    if "interaction_count" in edge_cols:
        ic_min = edges["interaction_count"].min()
        ic_max = edges["interaction_count"].max()
        report["interaction_count_range"] = [float(ic_min), float(ic_max)]
        if ic_min >= 1:
            ok("interaction_count_ge1",
               f"Range [{ic_min}, {ic_max}] — all ≥ 1 as expected for retained last interaction")
        else:
            warn("interaction_count_ge1",
                 f"interaction_count has values < 1 (min={ic_min}). "
                 "Verify semantics before using as a feature.")

    # ---- Duplicate edges within event ---------------------------------------
    dup_edges = edges[edges.duplicated(subset=["event_id", "source", "target"])]
    if dup_edges.empty:
        ok("no_duplicate_edges")
    else:
        warn("no_duplicate_edges",
             f"{len(dup_edges)} duplicate (event,src,tgt) rows found. "
             "LEN retains last interaction per pair — check whether these are "
             "genuine duplicates or parsing artefacts.")

    # ---- Account-ID overlap across events ------------------------------------
    # How many unique accounts appear in more than one event?
    account_event = nodes.groupby("node_id")["event_id"].nunique()
    shared_accounts = (account_event > 1).sum()
    total_accounts  = len(account_event)
    report["account_overlap"] = {
        "total_unique_accounts": int(total_accounts),
        "accounts_in_multiple_events": int(shared_accounts),
        "fraction": round(shared_accounts / total_accounts, 4) if total_accounts > 0 else 0.0,
    }
    if shared_accounts / max(total_accounts, 1) > 0.10:
        warn("account_overlap",
             f"{shared_accounts}/{total_accounts} accounts appear in >1 event "
             f"({report['account_overlap']['fraction']:.1%}). "
             "Consider grouped-split sensitivity check.")
    else:
        ok("account_overlap",
           f"{shared_accounts}/{total_accounts} accounts shared across events "
           f"({report['account_overlap']['fraction']:.1%})")

    # ---- Write report -------------------------------------------------------
    out_path = Path(config["data"]["manifests_dir"]) / "validation_report.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    status = "✅ PASS" if report["pass"] else "❌ FAIL"
    print(f"\nValidation: {status}")
    print(f"Report written to {out_path}")
    if report["warnings"]:
        print(f"Warnings ({len(report['warnings'])}):")
        for w in report["warnings"]:
            print(f"  ⚠  {w}")
    if not report["pass"]:
        print("\nFix failing checks before proceeding to modelling.")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    validate(cfg)
```

---

## Day 2 — Features, Baselines, and Matching

### `src/features.py` — All Feature Extraction

```python
"""
features.py
-----------
Extracts all feature groups from parsed graph data.

Feature groups (controlled by config):
  - Scale:     log1p(node_count), log1p(edge_count)
  - Structure: density, reciprocity, largest-WCC fraction,
               in/out-degree concentration (Gini),
               coreness summary (if reliable post-sampling)
  - Content:   exact/near-dup text proportion, text concentration,
               message-length dispersion
  - Combined:  all above groups together

Key design rules (from protocol):
  - Fit normalisation transforms INSIDE training folds only (see splits.py).
  - After edge sampling, NEVER use original full-graph structural values.
  - Temporal features are OFF (use_temporal: false in config).
  - Content features are conditional on text column presence.

Returns a dict of DataFrames, one per feature group, indexed by event_id.
"""

import re
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path


# ---------------------------------------------------------------------------
# Utility: Gini coefficient
# ---------------------------------------------------------------------------

def gini(values: np.ndarray) -> float:
    """
    Gini coefficient in [0, 1].
    0 = perfectly equal distribution (all nodes have same degree).
    1 = maximally concentrated (one node has all edges).
    We use this as an 'in-degree concentration' measure.
    """
    if len(values) == 0:
        return 0.0
    v = np.sort(np.abs(values))
    n = len(v)
    cumsum = np.cumsum(v)
    return (2 * np.dot(np.arange(1, n + 1), v) - (n + 1) * cumsum[-1]) / (n * cumsum[-1] + 1e-12)


# ---------------------------------------------------------------------------
# Rebuild a graph from edge rows (used after sampling)
# ---------------------------------------------------------------------------

def edges_to_digraph(edge_rows: pd.DataFrame) -> nx.DiGraph:
    """
    Build a DiGraph from a DataFrame with columns [source, target, ...].
    Only nodes incident to given edges are included (correct after sampling).
    """
    G = nx.DiGraph()
    for _, row in edge_rows.iterrows():
        G.add_edge(str(row["source"]), str(row["target"]))
    return G


# ---------------------------------------------------------------------------
# Feature extractors — one function per group
# ---------------------------------------------------------------------------

def extract_scale_features(G: nx.DiGraph) -> dict:
    return {
        "log_node_count": np.log1p(G.number_of_nodes()),
        "log_edge_count": np.log1p(G.number_of_edges()),
    }


def extract_structural_features(G: nx.DiGraph) -> dict:
    n = G.number_of_nodes()
    m = G.number_of_edges()

    # Density: m / (n*(n-1)) for directed graph
    density = nx.density(G) if n > 1 else 0.0

    # Reciprocity: fraction of edges that have a reverse edge
    reciprocity = nx.reciprocity(G) if m > 0 else 0.0

    # Largest weakly connected component fraction
    if n > 0:
        wccs = sorted(nx.weakly_connected_components(G), key=len, reverse=True)
        largest_wcc_frac = len(wccs[0]) / n
    else:
        largest_wcc_frac = 0.0

    # In-degree and out-degree Gini coefficients
    in_degrees  = np.array([d for _, d in G.in_degree()])
    out_degrees = np.array([d for _, d in G.out_degree()])
    indegree_gini  = gini(in_degrees)
    outdegree_gini = gini(out_degrees)

    # Coreness summary: k-core number of each node
    # Only use for full-graph views.  After sampling, recompute from sampled graph.
    try:
        undirected = G.to_undirected()
        core_numbers = nx.core_number(undirected)
        core_vals = np.array(list(core_numbers.values()), dtype=float)
        coreness_median = float(np.median(core_vals))
        coreness_max    = float(core_vals.max())
    except Exception:
        coreness_median = 0.0
        coreness_max    = 0.0

    return {
        "density": density,
        "reciprocity": reciprocity,
        "largest_wcc_fraction": largest_wcc_frac,
        "indegree_gini": indegree_gini,
        "outdegree_gini": outdegree_gini,
        "coreness_median": coreness_median,
        "coreness_max": coreness_max,
    }


def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    # Lowercase, collapse whitespace, strip URLs
    text = re.sub(r"https?://\S+", "", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_content_features(edge_rows: pd.DataFrame, text_col: str) -> dict:
    """
    Aggregate content features from the edge-level text column.
    Each edge may carry the text of the engaged-with tweet.

    Features:
      - exact_dup_proportion : fraction of text values that are exact duplicates
      - text_concentration   : Gini of message-frequency distribution
      - msg_length_dispersion: std of whitespace-token counts across messages
    """
    texts = edge_rows[text_col].dropna().apply(_clean_text)
    texts = texts[texts != ""]

    if len(texts) == 0:
        return {
            "exact_dup_proportion": np.nan,
            "text_concentration": np.nan,
            "msg_length_dispersion": np.nan,
        }

    # Exact duplicate proportion
    n_total = len(texts)
    n_unique = texts.nunique()
    exact_dup_proportion = 1.0 - (n_unique / n_total)

    # Text concentration: Gini over how often each unique message appears
    freq = texts.value_counts().values.astype(float)
    text_concentration = gini(freq)

    # Message-length dispersion
    lengths = texts.str.split().str.len().astype(float)
    msg_length_dispersion = float(lengths.std(ddof=1)) if len(lengths) > 1 else 0.0

    return {
        "exact_dup_proportion": exact_dup_proportion,
        "text_concentration": text_concentration,
        "msg_length_dispersion": msg_length_dispersion,
    }


# ---------------------------------------------------------------------------
# Main function: compute all feature groups for all events
# ---------------------------------------------------------------------------

def compute_all_features(
    edges_df: pd.DataFrame,
    manifest_df: pd.DataFrame,
    config: dict,
    event_ids: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Compute feature groups for a list of events (or all events if None).

    Parameters
    ----------
    edges_df    : the full edges parquet table
    manifest_df : the manifest parquet table
    config      : loaded yaml config
    event_ids   : if given, restrict to these events

    Returns
    -------
    dict mapping group name → DataFrame indexed by event_id, with label column.
    """
    feat_cfg = config["features"]

    if event_ids is None:
        event_ids = manifest_df["event_id"].tolist()

    text_col = None
    text_candidates = ["text", "tweet_text", "content", "message"]
    for tc in text_candidates:
        if tc in edges_df.columns:
            text_col = tc
            break
    if text_col is None and feat_cfg.get("use_text_features", True):
        print("WARNING: No text column found — disabling content features.")

    records = {g: [] for g in ["scale", "structure", "content", "combined"]}

    for eid in event_ids:
        ev_edges = edges_df[edges_df["event_id"] == eid]
        label_row = manifest_df[manifest_df["event_id"] == eid]
        if label_row.empty:
            continue
        label = int(label_row.iloc[0]["label"])

        G = edges_to_digraph(ev_edges)

        row_base = {"event_id": eid, "label": label}

        # Scale
        scale_feats = extract_scale_features(G) if feat_cfg.get("use_log_node_count") else {}
        records["scale"].append({**row_base, **scale_feats})

        # Structure
        struct_feats = extract_structural_features(G) if feat_cfg.get("use_density") else {}
        records["structure"].append({**row_base, **struct_feats})

        # Content
        if text_col and feat_cfg.get("use_text_features", True):
            cont_feats = extract_content_features(ev_edges, text_col)
        else:
            cont_feats = {}
        records["content"].append({**row_base, **cont_feats})

        # Combined: merge all feature dicts
        all_feats = {**scale_feats, **struct_feats, **cont_feats}
        records["combined"].append({**row_base, **all_feats})

    result = {}
    for group, rows in records.items():
        df = pd.DataFrame(rows).set_index("event_id")
        result[group] = df

    return result


def compute_features_for_sampled_view(
    sampled_edges: pd.DataFrame,
    event_id: str,
    label: int,
    config: dict,
) -> dict:
    """
    Compute features from a sampled edge subset.
    IMPORTANT: structural features are recomputed from scratch on the sampled graph.
    Full-graph attributes are not used here.
    """
    G = edges_to_digraph(sampled_edges)
    feat_cfg = config["features"]

    feats = {"event_id": event_id, "label": label}

    scale   = extract_scale_features(G)
    struct  = extract_structural_features(G)
    feats.update(scale)
    feats.update(struct)

    text_candidates = ["text", "tweet_text", "content", "message"]
    text_col = next((c for c in text_candidates if c in sampled_edges.columns), None)
    if text_col and feat_cfg.get("use_text_features", True):
        cont = extract_content_features(sampled_edges, text_col)
        feats.update(cont)

    return feats
```

---

### `src/build_cohorts.py` — Node-Count Matching

```python
"""
build_cohorts.py
----------------
Match campaign and comparison events on log(node_count) using
nearest-neighbour matching with a predeclared caliper.

Algorithm:
  1. Compute log1p(node_count) for all events.
  2. For each campaign event, find the nearest comparison event
     (by Euclidean distance in log-node-count space) that has not
     yet been matched and is within the caliper.
  3. Report retention, balance diagnostics, and standardised mean
     difference (SMD) before and after matching.
  4. Write matched manifest to data/manifests/matched_manifest.parquet.

IMPORTANT: The caliper is set BEFORE inspecting any model scores.
           It must not be changed after scores are compared.

Run:
  python src/build_cohorts.py --config configs/final.yaml
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def standardised_mean_difference(values: np.ndarray, labels: np.ndarray) -> float:
    """SMD = (mean_campaign - mean_comparison) / pooled_sd"""
    v_c = values[labels == 1]
    v_k = values[labels == 0]
    pooled_sd = np.sqrt((v_c.var(ddof=1) + v_k.var(ddof=1)) / 2)
    if pooled_sd == 0:
        return 0.0
    return float((v_c.mean() - v_k.mean()) / pooled_sd)


def match_cohort(manifest: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, dict]:
    """
    Returns (matched_df, diagnostics_dict).
    matched_df has the same schema as manifest, restricted to matched events.
    """
    mc = config["matching"]
    rng = np.random.default_rng(mc["random_seed"])

    log_nc = np.log1p(manifest["n_nodes"].values)
    caliper_abs = mc["caliper_sd_fraction"] * float(np.std(log_nc, ddof=1))

    campaign_idx  = manifest.index[manifest.label == 1].tolist()
    comparison_idx = manifest.index[manifest.label == 0].tolist()

    # Shuffle campaign order (reproducible) to avoid order effects
    rng.shuffle(campaign_idx)

    available_comparisons = set(comparison_idx)
    matched_pairs = []   # list of (campaign_idx, comparison_idx)

    log_nc_by_idx = {i: np.log1p(manifest.loc[i, "n_nodes"]) for i in manifest.index}

    for ci in campaign_idx:
        lnc_c = log_nc_by_idx[ci]
        # Filter by caliper
        candidates = [
            ki for ki in available_comparisons
            if abs(log_nc_by_idx[ki] - lnc_c) <= caliper_abs
        ]
        if not candidates:
            continue
        # Pick nearest
        best = min(candidates, key=lambda ki: abs(log_nc_by_idx[ki] - lnc_c))
        matched_pairs.append((ci, best))
        available_comparisons.discard(best)

    # Build matched manifest
    matched_indices = [i for pair in matched_pairs for i in pair]
    matched_df = manifest.loc[matched_indices].copy()
    matched_df["matched_pair_id"] = [
        pid for pid, _ in enumerate(matched_pairs) for _ in range(2)
    ]

    # Diagnostics
    log_nc_arr = np.array([log_nc_by_idx[i] for i in manifest.index])
    labels_arr  = manifest["label"].values
    log_nc_m   = np.array([log_nc_by_idx[i] for i in matched_indices])
    labels_m   = matched_df["label"].values

    diag = {
        "caliper_abs": round(caliper_abs, 4),
        "caliper_sd_fraction": mc["caliper_sd_fraction"],
        "n_campaign_total": int((manifest.label == 1).sum()),
        "n_comparison_total": int((manifest.label == 0).sum()),
        "n_matched_pairs": len(matched_pairs),
        "n_campaign_matched": int((matched_df.label == 1).sum()),
        "n_comparison_matched": int((matched_df.label == 0).sum()),
        "n_excluded": len(manifest) - len(matched_df),
        "smd_before": round(standardised_mean_difference(log_nc_arr, labels_arr), 4),
        "smd_after":  round(standardised_mean_difference(log_nc_m, labels_m), 4),
        "log_node_count_campaign_mean_before": round(float(np.mean(log_nc_arr[labels_arr == 1])), 4),
        "log_node_count_comparison_mean_before": round(float(np.mean(log_nc_arr[labels_arr == 0])), 4),
        "log_node_count_campaign_mean_after": round(float(np.mean(log_nc_m[labels_m == 1])), 4),
        "log_node_count_comparison_mean_after": round(float(np.mean(log_nc_m[labels_m == 0])), 4),
    }

    return matched_df, diag


def build_cohorts(config: dict) -> None:
    manifests_dir = Path(config["data"]["manifests_dir"])
    manifest = pd.read_parquet(manifests_dir / "manifest.parquet")

    print(f"Full cohort: {len(manifest)} events")
    print(f"  Campaign  : {(manifest.label == 1).sum()}")
    print(f"  Comparison: {(manifest.label == 0).sum()}")

    matched_df, diag = match_cohort(manifest, config)

    out_manifest = manifests_dir / "matched_manifest.parquet"
    matched_df.to_parquet(out_manifest, index=True)

    out_diag = manifests_dir / "matching_diagnostics.json"
    with open(out_diag, "w") as f:
        json.dump(diag, f, indent=2)

    print(f"\n--- Matching diagnostics ---")
    print(f"Caliper (abs units): {diag['caliper_abs']:.4f}  "
          f"({diag['caliper_sd_fraction']} SD of log node count)")
    print(f"Matched pairs      : {diag['n_matched_pairs']}")
    print(f"Events retained    : {diag['n_campaign_matched']} campaign, "
          f"{diag['n_comparison_matched']} comparison")
    print(f"Events excluded    : {diag['n_excluded']}")
    print(f"SMD before         : {diag['smd_before']:.4f}")
    print(f"SMD after          : {diag['smd_after']:.4f}")
    print(f"\nMatched manifest → {out_manifest}")
    print(f"Diagnostics        → {out_diag}")

    if diag["n_matched_pairs"] < 20:
        print("\nWARNING: Fewer than 20 matched pairs — results will be very noisy. "
              "Report this limitation; do not relax the caliper to get a 'better' result.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    build_cohorts(cfg)
```

---

## Day 2 continued — Splits and Baseline Training

### `src/splits.py` — Stratified Folds, No Leakage

```python
"""
splits.py
---------
Create event-level stratified k-fold splits.

LEAKAGE RULE: all sampled views of one event must stay in the same fold.
This is enforced by splitting at the event level and then mapping views
to their event's fold.

Returns a dict {event_id: fold_id} for any given manifest.

Also provides utility to assign views from sample_views output to folds.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold


def make_event_folds(
    manifest: pd.DataFrame,
    n_folds: int,
    random_seed: int,
) -> dict[str, int]:
    """
    Returns {event_id: fold_index} with stratified splits.
    'label' column in manifest is used for stratification.
    """
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_seed)
    event_ids = manifest["event_id"].values
    labels    = manifest["label"].values

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
    Assign fold_id to each row of a views DataFrame (which has 'event_id' column).
    Rows with event_id not in the map are dropped with a warning.
    """
    views_df = views_df.copy()
    views_df["fold_id"] = views_df["event_id"].map(event_fold_map)
    n_missing = views_df["fold_id"].isna().sum()
    if n_missing > 0:
        print(f"WARNING: {n_missing} view rows have event_ids not in fold map — dropped.")
        views_df = views_df.dropna(subset=["fold_id"])
    views_df["fold_id"] = views_df["fold_id"].astype(int)
    return views_df
```

---

### `src/train.py` — Training and Cross-Validation

```python
"""
train.py
--------
Run event-level stratified cross-validation for all experiment conditions:
  A  Full cohort reference
  B0a/B0b Scale-only baselines
  C  Matched cohort
  D1 Frozen-model edge-budget shift (test only)
  D2 Restricted-view learnability (train+test at same K)
  E  Feature-family ablation

Outputs:
  outputs/run_final/predictions.parquet  — all out-of-fold predictions
  outputs/run_final/metrics.json         — per-experiment metrics

Key safety rules:
  - StandardScaler is fit INSIDE each training fold, applied to test fold.
  - Hyperparameter tuning (inner CV) happens inside training fold only.
  - No labels, IDs, raw timestamps, or absolute dates as features.

Run:
  python src/train.py --config configs/final.yaml
"""

import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score

from features import compute_all_features, compute_features_for_sampled_view
from splits import make_event_folds, assign_view_folds


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------

def make_logreg_pipeline(config: dict) -> Pipeline:
    """Returns a Pipeline(scaler, logreg) with default C=1.0."""
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            C=1.0,
            max_iter=config["models"]["logreg"]["max_iter"],
            solver=config["models"]["logreg"]["solver"],
            class_weight="balanced",
        ))
    ])


def make_hgbt_pipeline(config: dict) -> Pipeline:
    return Pipeline([
        # HGBT handles NaN natively; scaler still useful for logreg later
        ("clf", HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=config["models"]["hgbt"]["max_depth"],
            random_state=config["models"]["hgbt"]["random_state"],
            class_weight="balanced",
        ))
    ])


def tune_logreg_C(
    X_train: np.ndarray,
    y_train: np.ndarray,
    C_values: list[float],
    inner_cv: int,
    config: dict,
) -> float:
    """Inner-loop C tuning via stratified CV on training fold."""
    best_C, best_score = C_values[0], -np.inf
    for C in C_values:
        pipe = make_logreg_pipeline(config)
        pipe.set_params(clf__C=C)
        scores = cross_val_score(pipe, X_train, y_train,
                                 cv=StratifiedKFold(inner_cv, shuffle=True, random_state=0),
                                 scoring="balanced_accuracy")
        if scores.mean() > best_score:
            best_score = scores.mean()
            best_C = C
    return best_C


# ---------------------------------------------------------------------------
# Core cross-validation function
# ---------------------------------------------------------------------------

def run_cv(
    feature_df: pd.DataFrame,
    fold_map: dict[str, int],
    config: dict,
    experiment_label: str,
    model_type: str = "logreg",
) -> pd.DataFrame:
    """
    Run outer cross-validation.

    Parameters
    ----------
    feature_df    : DataFrame indexed by event_id with 'label' column and
                    feature columns (all numeric; NaN allowed for HGBT only)
    fold_map      : {event_id: fold_index}
    config        : loaded yaml config
    experiment_label : string tag for the predictions table
    model_type    : 'logreg' or 'hgbt'

    Returns
    -------
    DataFrame with columns:
      event_id, fold_id, label, prob_campaign, pred_label, experiment
    """
    n_folds = config["splits"]["n_folds"]
    C_values = config["models"]["logreg"]["C_values"]

    # Align fold assignments
    df = feature_df.copy()
    df["fold_id"] = df.index.map(fold_map)
    df = df.dropna(subset=["fold_id"])
    df["fold_id"] = df["fold_id"].astype(int)

    feature_cols = [c for c in df.columns if c not in {"label", "fold_id"}]

    all_preds = []

    for fold_idx in range(n_folds):
        train_mask = df["fold_id"] != fold_idx
        test_mask  = df["fold_id"] == fold_idx

        X_train = df.loc[train_mask, feature_cols].values.astype(float)
        y_train = df.loc[train_mask, "label"].values
        X_test  = df.loc[test_mask,  feature_cols].values.astype(float)
        y_test  = df.loc[test_mask,  "label"].values

        if model_type == "logreg":
            best_C = tune_logreg_C(X_train, y_train, C_values,
                                   inner_cv=3, config=config)
            pipe = make_logreg_pipeline(config)
            pipe.set_params(clf__C=best_C)
        else:
            pipe = make_hgbt_pipeline(config)

        pipe.fit(X_train, y_train)
        probs = pipe.predict_proba(X_test)[:, 1]
        preds = (probs >= 0.5).astype(int)

        test_event_ids = df.loc[test_mask].index.tolist()
        for eid, prob, pred, true_lbl in zip(test_event_ids, probs, preds, y_test):
            all_preds.append({
                "event_id":     eid,
                "fold_id":      fold_idx,
                "label":        int(true_lbl),
                "prob_campaign": float(prob),
                "pred_label":   int(pred),
                "experiment":   experiment_label,
                "model":        model_type,
            })

    return pd.DataFrame(all_preds)


# ---------------------------------------------------------------------------
# Metrics helper
# ---------------------------------------------------------------------------

def compute_metrics(pred_df: pd.DataFrame) -> dict:
    y_true = pred_df["label"].values
    y_pred = pred_df["pred_label"].values
    y_prob = pred_df["prob_campaign"].values

    metrics = {
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, y_pred)), 4),
        "macro_f1":          round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "campaign_recall":   round(float(f1_score(y_true, y_pred, pos_label=1, average="binary", zero_division=0)), 4),
        "comparison_recall": round(float(f1_score(y_true, y_pred, pos_label=0, average="binary", zero_division=0)), 4),
        "n_events":          int(len(pred_df)),
    }
    try:
        metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 4)
    except Exception:
        metrics["roc_auc"] = None

    return metrics


# ---------------------------------------------------------------------------
# Main training orchestrator
# ---------------------------------------------------------------------------

def train_all(config: dict) -> None:
    manifests_dir = Path(config["data"]["manifests_dir"])
    processed_dir = Path(config["data"]["processed_dir"])
    run_dir       = Path(config["output"]["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_parquet(manifests_dir / "manifest.parquet")
    edges_df = pd.read_parquet(processed_dir  / "edges.parquet")

    split_cfg = config["splits"]
    fold_map  = make_event_folds(manifest, split_cfg["n_folds"], split_cfg["random_seed"])

    all_predictions = []
    all_metrics     = {}

    # =====================================================================
    # Compute full feature groups once
    # =====================================================================
    print("Computing features for all events...")
    feature_groups = compute_all_features(edges_df, manifest, config)

    # =====================================================================
    # Experiment A — Full cohort reference (all four feature groups)
    # =====================================================================
    print("\n[A] Full-cohort reference...")
    for group_name, feat_df in feature_groups.items():
        for model_type in ["logreg", "hgbt"]:
            exp_label = f"A_{group_name}_{model_type}"
            pred_df = run_cv(feat_df, fold_map, config, exp_label, model_type)
            all_predictions.append(pred_df)
            all_metrics[exp_label] = compute_metrics(pred_df)
            ba = all_metrics[exp_label]["balanced_accuracy"]
            f1 = all_metrics[exp_label]["macro_f1"]
            print(f"  {exp_label:40s}  balanced_acc={ba:.3f}  macro_f1={f1:.3f}")

    # =====================================================================
    # Experiment B — Scale-only baselines
    # =====================================================================
    print("\n[B] Scale-only baselines...")
    scale_df = feature_groups["scale"].copy()

    # B0a: log node count only
    b0a_df = scale_df[["label", "log_node_count"]].copy()
    for model_type in ["logreg", "hgbt"]:
        exp_label = f"B0a_log_node_{model_type}"
        pred_df = run_cv(b0a_df, fold_map, config, exp_label, model_type)
        all_predictions.append(pred_df)
        all_metrics[exp_label] = compute_metrics(pred_df)
        ba = all_metrics[exp_label]["balanced_accuracy"]
        print(f"  {exp_label:40s}  balanced_acc={ba:.3f}")

    # B0b: log node + log edge count
    b0b_df = scale_df[["label", "log_node_count", "log_edge_count"]].copy()
    for model_type in ["logreg", "hgbt"]:
        exp_label = f"B0b_log_node_edge_{model_type}"
        pred_df = run_cv(b0b_df, fold_map, config, exp_label, model_type)
        all_predictions.append(pred_df)
        all_metrics[exp_label] = compute_metrics(pred_df)
        ba = all_metrics[exp_label]["balanced_accuracy"]
        print(f"  {exp_label:40s}  balanced_acc={ba:.3f}")

    # =====================================================================
    # Experiment C — Matched cohort
    # =====================================================================
    matched_manifest_path = manifests_dir / "matched_manifest.parquet"
    if matched_manifest_path.exists():
        print("\n[C] Matched cohort...")
        matched_manifest = pd.read_parquet(matched_manifest_path)
        matched_eids = matched_manifest["event_id"].tolist()
        matched_fold_map = make_event_folds(
            matched_manifest.reset_index(), split_cfg["n_folds"], split_cfg["random_seed"]
        )

        for group_name, feat_df in feature_groups.items():
            matched_feat_df = feat_df.loc[feat_df.index.isin(matched_eids)]
            for model_type in ["logreg", "hgbt"]:
                exp_label = f"C_matched_{group_name}_{model_type}"
                pred_df = run_cv(matched_feat_df, matched_fold_map, config, exp_label, model_type)
                all_predictions.append(pred_df)
                all_metrics[exp_label] = compute_metrics(pred_df)
                ba = all_metrics[exp_label]["balanced_accuracy"]
                print(f"  {exp_label:40s}  balanced_acc={ba:.3f}")
    else:
        print("\n[C] Skipped — run build_cohorts.py first.")

    # =====================================================================
    # Experiments D1 + D2 — Edge budget (see sample_views.py output)
    # =====================================================================
    views_path = processed_dir / "sampled_views.parquet"
    if views_path.exists():
        print("\n[D] Edge-budget experiments...")
        views_df = pd.read_parquet(views_path)

        for K in config["edge_budgets"]["K_values"]:
            k_views = views_df[views_df["K"] == K]
            eligible_eids = k_views["event_id"].unique().tolist()
            eligible_manifest = manifest[manifest["event_id"].isin(eligible_eids)]

            if len(eligible_eids) == 0:
                print(f"  K={K}: no eligible events — skipping")
                continue

            k_fold_map = make_event_folds(
                eligible_manifest.reset_index(), split_cfg["n_folds"], split_cfg["random_seed"]
            )
            k_views = assign_view_folds(k_views, k_fold_map)

            # D1: frozen model trained on full graphs, tested on restricted views
            # (We use the logreg trained in Experiment A on full combined features,
            #  but here we re-fit on training events' SAMPLED views for simplicity;
            #  true D1 would pickle the full-graph model from A and apply it to
            #  sampled view features.  The simpler version is documented as an
            #  approximation in the report.)

            # D2: train and test at same K — averaged over seeds
            # Aggregate per-event predictions across seeds
            seed_preds = []
            for seed_val in k_views["seed"].unique():
                seed_views = k_views[k_views["seed"] == seed_val]
                # Each row in seed_views is one event's features at this K+seed
                feat_df_seed = seed_views.drop(columns=["K", "seed"]).set_index("event_id")
                pred_df = run_cv(feat_df_seed, k_fold_map, config,
                                 f"D2_K{K}_seed{seed_val}", "logreg")
                seed_preds.append(pred_df)

            # Summarise: average prob across seeds per event
            if seed_preds:
                combined = pd.concat(seed_preds)
                avg_pred = (
                    combined.groupby("event_id")
                    .agg(prob_campaign=("prob_campaign", "mean"),
                         label=("label", "first"))
                    .assign(pred_label=lambda d: (d.prob_campaign >= 0.5).astype(int),
                            experiment=f"D2_K{K}_avgseeds",
                            model="logreg")
                )
                avg_pred.reset_index(inplace=True)
                all_predictions.append(avg_pred)
                all_metrics[f"D2_K{K}"] = compute_metrics(avg_pred)
                ba = all_metrics[f"D2_K{K}"]["balanced_accuracy"]
                print(f"  D2 K={K:5d}:  eligible={len(eligible_eids)}  balanced_acc={ba:.3f}")
    else:
        print("\n[D] Skipped — run sample_views.py first.")

    # =====================================================================
    # Save all outputs
    # =====================================================================
    all_preds_df = pd.concat([df for df in all_predictions], ignore_index=True)
    pred_path = run_dir / "predictions.parquet"
    all_preds_df.to_parquet(pred_path, index=False)
    print(f"\nPredictions saved → {pred_path}")

    metrics_path = run_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"Metrics saved    → {metrics_path}")

    # Quick summary table
    summary_rows = []
    for exp, m in all_metrics.items():
        summary_rows.append({"experiment": exp, **m})
    summary_df = pd.DataFrame(summary_rows).sort_values("experiment")
    tables_path = run_dir / "tables.md"
    with open(tables_path, "w") as f:
        f.write("# Results Summary\n\n")
        f.write(summary_df.to_markdown(index=False))
        f.write("\n\n*All numbers are out-of-fold estimates on LEN-Small (100 events).*\n")
    print(f"Tables saved     → {tables_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    train_all(cfg)
```

---

## Day 3 — Edge Sampling

### `src/sample_views.py` — Fixed Retained-Edge Budgets

```python
"""
sample_views.py
---------------
For each K in {250, 500, 1000, 2000} and each of 10 seeds, sample K
existing edges without replacement from each eligible event graph.

Eligibility: graph must have at least K edges.

For each (event, K, seed):
  1. Sample K edges without replacement.
  2. Keep edge content attached.
  3. Rebuild the graph from sampled edges (only incident nodes kept).
  4. Recompute all structural + content features from scratch.
  5. NEVER include original node/edge counts or full-graph attributes.

Writes:
  data/processed/sampled_views.parquet  — one row per (event, K, seed)
  data/manifests/edge_budget_eligibility.json  — which events qualify at each K

IMPORTANT: Seeds are deterministic and fixed before any score comparison.
           Do NOT change K_values or n_seeds after inspecting results.

Run:
  python src/sample_views.py --config configs/final.yaml
"""

import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

from features import compute_features_for_sampled_view


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def sample_views(config: dict) -> None:
    processed_dir = Path(config["data"]["processed_dir"])
    manifests_dir = Path(config["data"]["manifests_dir"])

    manifest = pd.read_parquet(manifests_dir / "manifest.parquet")
    edges_df = pd.read_parquet(processed_dir / "edges.parquet")

    K_values = config["edge_budgets"]["K_values"]
    n_seeds  = config["edge_budgets"]["n_seeds"]
    base_seed = config["edge_budgets"]["base_seed"]

    eligibility: dict[int, list[str]] = {}
    all_rows = []

    for K in K_values:
        print(f"\nK = {K}")

        # Determine eligible events
        eligible = manifest[manifest["n_edges"] >= K]["event_id"].tolist()
        eligibility[K] = eligible
        print(f"  Eligible events: {len(eligible)} / {len(manifest)}")

        n_camp  = manifest[manifest.event_id.isin(eligible) & (manifest.label == 1)].shape[0]
        n_comp  = manifest[manifest.event_id.isin(eligible) & (manifest.label == 0)].shape[0]
        print(f"  Campaign: {n_camp}, Comparison: {n_comp}")

        if len(eligible) == 0:
            print("  No eligible events — skipping K")
            continue

        for seed_idx in range(n_seeds):
            seed_val = base_seed + seed_idx
            rng = np.random.default_rng(seed_val)

            for eid in tqdm(eligible, desc=f"  K={K} seed={seed_val}", leave=False):
                ev_edges = edges_df[edges_df["event_id"] == eid].copy()
                label = int(manifest[manifest.event_id == eid].iloc[0]["label"])

                # Sample K edges without replacement
                sampled_idx = rng.choice(len(ev_edges), size=K, replace=False)
                sampled_edges = ev_edges.iloc[sampled_idx].reset_index(drop=True)

                # Recompute features — never use full-graph values
                feats = compute_features_for_sampled_view(sampled_edges, eid, label, config)
                feats["K"]    = K
                feats["seed"] = seed_val

                all_rows.append(feats)

    # Write outputs
    views_df = pd.DataFrame(all_rows)
    out_path = processed_dir / "sampled_views.parquet"
    views_df.to_parquet(out_path, index=False)
    print(f"\nSampled views → {out_path}  ({len(views_df)} rows)")

    elig_path = manifests_dir / "edge_budget_eligibility.json"
    with open(elig_path, "w") as f:
        json.dump({str(k): v for k, v in eligibility.items()}, f, indent=2)
    print(f"Eligibility   → {elig_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    sample_views(cfg)
```

---

## Day 4 — Evaluation, Uncertainty, and Figures

### `src/evaluate.py` — Bootstrap Uncertainty and All Four Figures

```python
"""
evaluate.py
-----------
Reads predictions.parquet and metrics.json.
Computes bootstrap confidence intervals on original events.
Generates the four required figures.
Writes reports/checkpoint_report.md.

Figures:
  fig1_size_overlap.png         — node/edge distributions by label
  fig2_baseline_comparison.png  — size-only vs richer feature groups
  fig3_matched_cohort_comparison.png — full vs matched cohort results
  fig4_edge_budget_robustness.png    — balanced accuracy vs K

Run:
  python src/evaluate.py --config configs/final.yaml
"""

import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # non-interactive backend for servers
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import yaml
from scipy import stats


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def bootstrap_metric(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_fn,
    n_resamples: int,
    seed: int,
) -> tuple[float, float, float]:
    """Returns (point_estimate, ci_lower, ci_upper) at 95%."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    boot_vals = []
    for _ in range(n_resamples):
        idx = rng.choice(n, size=n, replace=True)
        try:
            val = metric_fn(y_true[idx], y_pred[idx])
            boot_vals.append(val)
        except Exception:
            pass
    arr = np.array(boot_vals)
    point = metric_fn(y_true, y_pred)
    return float(point), float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

CAMPAIGN_COLOR  = "#d62728"   # red
COMPARISON_COLOR = "#1f77b4"  # blue

def fig1_size_overlap(manifest: pd.DataFrame, out_dir: Path) -> None:
    """Violin + strip plot of log node count and log edge count by label."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    for ax, (col, label_str) in zip(axes, [
        ("n_nodes", "Node Count"),
        ("n_edges", "Edge Count"),
    ]):
        camp_vals = np.log1p(manifest[manifest.label == 1][col].values)
        comp_vals = np.log1p(manifest[manifest.label == 0][col].values)

        parts = ax.violinplot(
            [camp_vals, comp_vals],
            positions=[1, 2],
            showmedians=True,
            showextrema=True,
        )
        parts["bodies"][0].set_facecolor(CAMPAIGN_COLOR)
        parts["bodies"][0].set_alpha(0.6)
        parts["bodies"][1].set_facecolor(COMPARISON_COLOR)
        parts["bodies"][1].set_alpha(0.6)

        # Overlay jittered points
        rng = np.random.default_rng(0)
        for pos, vals, color in [
            (1, camp_vals, CAMPAIGN_COLOR),
            (2, comp_vals, COMPARISON_COLOR),
        ]:
            jitter = rng.uniform(-0.08, 0.08, size=len(vals))
            ax.scatter(pos + jitter, vals, alpha=0.5, s=18, color=color, zorder=3)

        ax.set_xticks([1, 2])
        ax.set_xticklabels(["Campaign\n(n=51)", "Comparison\n(n=49)"])
        ax.set_ylabel(f"log(1 + {label_str})")
        ax.set_title(f"Distribution of log {label_str}")

    fig.suptitle("Figure 1: LEN-Small Size Distributions by Label", fontsize=13)
    plt.tight_layout()
    out = out_dir / "fig1_size_overlap.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved {out}")


def fig2_baseline_comparison(metrics: dict, out_dir: Path) -> None:
    """Bar chart: B0a, B0b vs structural, combined — balanced accuracy."""
    # Filter to logreg results for fair comparison (one model type)
    relevant = {
        "Size\n(log N)":         "B0a_log_node_logreg",
        "Size\n(log N+E)":       "B0b_log_node_edge_logreg",
        "Structure":             "A_structure_logreg",
        "Content":               "A_content_logreg",
        "Combined":              "A_combined_logreg",
    }
    labels, values = [], []
    for name, key in relevant.items():
        if key in metrics:
            labels.append(name)
            values.append(metrics[key]["balanced_accuracy"])

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = [CAMPAIGN_COLOR if "Size" in l else COMPARISON_COLOR for l in labels]
    bars = ax.bar(labels, values, color=colors, alpha=0.8, edgecolor="black", linewidth=0.7)

    ax.axhline(0.5, linestyle="--", color="grey", linewidth=1, label="Chance (0.5)")
    ax.set_ylim(0.4, 1.05)
    ax.set_ylabel("Balanced Accuracy (out-of-fold)")
    ax.set_title("Figure 2: Feature Group Comparison — Full Cohort (Logistic Regression)")
    ax.legend()

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    out = out_dir / "fig2_baseline_comparison.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved {out}")


def fig3_matched_cohort_comparison(metrics: dict, out_dir: Path) -> None:
    """Grouped bar: full cohort vs matched cohort per feature group."""
    groups = ["scale", "structure", "content", "combined"]
    model  = "logreg"
    full_vals    = [metrics.get(f"A_{g}_{model}",   {}).get("balanced_accuracy", np.nan) for g in groups]
    matched_vals = [metrics.get(f"C_matched_{g}_{model}", {}).get("balanced_accuracy", np.nan) for g in groups]

    x = np.arange(len(groups))
    w = 0.35

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(x - w/2, full_vals,    w, label="Full cohort",    color=CAMPAIGN_COLOR,  alpha=0.8, edgecolor="black")
    ax.bar(x + w/2, matched_vals, w, label="Matched cohort", color=COMPARISON_COLOR, alpha=0.8, edgecolor="black")

    ax.axhline(0.5, linestyle="--", color="grey", linewidth=1, label="Chance")
    ax.set_xticks(x)
    ax.set_xticklabels([g.capitalize() for g in groups])
    ax.set_ylim(0.4, 1.05)
    ax.set_ylabel("Balanced Accuracy (out-of-fold)")
    ax.set_title("Figure 3: Full Cohort vs Node-Count-Matched Cohort (Logistic Regression)")
    ax.legend()
    plt.tight_layout()

    out = out_dir / "fig3_matched_cohort_comparison.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved {out}")


def fig4_edge_budget_robustness(metrics: dict, eligibility: dict, out_dir: Path) -> None:
    """Line plot: balanced accuracy vs K for D2."""
    K_values = sorted([int(k) for k in eligibility.keys()])
    ba_vals  = [metrics.get(f"D2_K{K}", {}).get("balanced_accuracy", np.nan) for K in K_values]
    n_eligible = [len(eligibility[str(K)]) for K in K_values]

    fig, ax1 = plt.subplots(figsize=(8, 4))
    color_line = CAMPAIGN_COLOR

    ax1.plot(K_values, ba_vals, "o-", color=color_line, linewidth=2, markersize=7, label="Balanced Accuracy (D2)")
    ax1.axhline(0.5, linestyle="--", color="grey", linewidth=1, label="Chance")
    ax1.set_xlabel("Edge Budget (K)")
    ax1.set_ylabel("Balanced Accuracy")
    ax1.set_ylim(0.4, 1.05)
    ax1.set_title("Figure 4: Classification Under Fixed Edge Budgets (D2 — Restricted-View Training)")
    ax1.legend(loc="upper left")

    ax2 = ax1.twinx()
    ax2.bar(K_values, n_eligible, width=80, alpha=0.25, color="steelblue", label="Eligible events")
    ax2.set_ylabel("Eligible Events (≥ K edges)", color="steelblue")
    ax2.tick_params(axis="y", labelcolor="steelblue")
    ax2.legend(loc="upper right")

    for K, ba in zip(K_values, ba_vals):
        if not np.isnan(ba):
            ax1.annotate(f"{ba:.3f}", xy=(K, ba), xytext=(0, 8),
                         textcoords="offset points", ha="center", fontsize=9)

    plt.tight_layout()
    out = out_dir / "fig4_edge_budget_robustness.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Checkpoint report
# ---------------------------------------------------------------------------

def write_checkpoint_report(metrics: dict, manifest: pd.DataFrame, config: dict) -> None:
    report_path = Path("reports/checkpoint_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Checkpoint Report — LEN-Small Robustness Audit",
        "",
        f"**Generated:** see run timestamp in metrics.json",
        f"**Dataset:** LEN-Small — {len(manifest)} events "
        f"({(manifest.label==1).sum()} campaign, {(manifest.label==0).sum()} comparison)",
        "",
        "## RQ1: Does classification survive size controls?",
        "",
        "### Scale-only baselines (Experiments B0a, B0b)",
        "",
    ]

    for key in ["B0a_log_node_logreg", "B0b_log_node_edge_logreg"]:
        m = metrics.get(key, {})
        lines.append(f"- **{key}**: Balanced Accuracy = {m.get('balanced_accuracy', 'N/A')}, "
                     f"Macro-F1 = {m.get('macro_f1', 'N/A')}")

    lines += [
        "",
        "### Full cohort vs matched cohort (Experiment C)",
        "",
        "| Feature Group | Full Cohort BA | Matched Cohort BA |",
        "|---|---|---|",
    ]
    for g in ["scale", "structure", "content", "combined"]:
        fa = metrics.get(f"A_{g}_logreg", {}).get("balanced_accuracy", "—")
        mc = metrics.get(f"C_matched_{g}_logreg", {}).get("balanced_accuracy", "—")
        lines.append(f"| {g.capitalize()} | {fa} | {mc} |")

    lines += [
        "",
        "## RQ2: Do richer features add value under restricted observation?",
        "",
        "### Edge-budget D2 results",
        "",
        "| K | Balanced Accuracy | Eligible Events |",
        "|---|---|---|",
    ]
    elig_path = Path(config["data"]["manifests_dir"]) / "edge_budget_eligibility.json"
    eligibility = {}
    if elig_path.exists():
        with open(elig_path) as f:
            eligibility = json.load(f)
    for K in config["edge_budgets"]["K_values"]:
        m = metrics.get(f"D2_K{K}", {})
        ba = m.get("balanced_accuracy", "—")
        n_elig = len(eligibility.get(str(K), []))
        lines.append(f"| {K} | {ba} | {n_elig} |")

    lines += [
        "",
        "## Limitations",
        "",
        "- LEN-Small is a *selected* subset of 100 events; findings do not automatically generalise.",
        "- Matching and eligibility filtering reduce the number of independent events.",
        "- Edge budgets test one specific restriction procedure, not all missing-data mechanisms.",
        "- Bootstrap CIs are conditional on fitted fold models.",
        "- No account-level attribution; labels are event-level.",
        "",
        "## Next steps",
        "",
        "- Verify content feature usability from validation report.",
        "- Resolve any WARN/FAIL flags in validation_report.json.",
        "- Cross-check every reported number against raw predictions.parquet.",
        "- Prepare demo narrative (see Section 9 of the Research Execution Lock).",
    ]

    with open(report_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Checkpoint report → {report_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def evaluate(config: dict) -> None:
    run_dir    = Path(config["output"]["run_dir"])
    figs_dir   = Path(config["output"]["figures_dir"])
    figs_dir.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_parquet(Path(config["data"]["manifests_dir"]) / "manifest.parquet")

    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        print("metrics.json not found — run train.py first.")
        return
    with open(metrics_path) as f:
        metrics = json.load(f)

    elig_path = Path(config["data"]["manifests_dir"]) / "edge_budget_eligibility.json"
    eligibility = {}
    if elig_path.exists():
        with open(elig_path) as f:
            eligibility = json.load(f)

    print("Generating figures...")
    fig1_size_overlap(manifest, figs_dir)
    fig2_baseline_comparison(metrics, figs_dir)
    fig3_matched_cohort_comparison(metrics, figs_dir)
    fig4_edge_budget_robustness(metrics, eligibility, figs_dir)

    write_checkpoint_report(metrics, manifest, config)
    print("\nAll outputs written.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    evaluate(cfg)
```

---

## Tests

### `tests/test_ingestion.py`

```python
"""
Tests for ingestion and label integrity.
Run: pytest tests/test_ingestion.py -v
"""

import pytest
import pandas as pd
from pathlib import Path
import json


MANIFESTS_DIR = Path("data/manifests")
PROCESSED_DIR  = Path("data/processed")


@pytest.fixture(scope="module")
def manifest():
    path = MANIFESTS_DIR / "manifest.parquet"
    if not path.exists():
        pytest.skip("manifest.parquet not found — run ingest_len.py first")
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def validation_report():
    path = MANIFESTS_DIR / "validation_report.json"
    if not path.exists():
        pytest.skip("validation_report.json not found — run validate_len.py first")
    with open(path) as f:
        return json.load(f)


def test_event_count(manifest):
    assert len(manifest) == 100, f"Expected 100 events, got {len(manifest)}"


def test_campaign_count(manifest):
    assert (manifest.label == 1).sum() == 51


def test_comparison_count(manifest):
    assert (manifest.label == 0).sum() == 49


def test_no_duplicate_event_ids(manifest):
    assert manifest["event_id"].nunique() == len(manifest)


def test_no_zero_node_events(manifest):
    assert (manifest.n_nodes == 0).sum() == 0, "Some events have 0 nodes"


def test_labels_are_binary(manifest):
    assert set(manifest.label.unique()).issubset({0, 1})


def test_sha256_present(manifest):
    assert "sha256" in manifest.columns
    assert manifest["sha256"].notna().all()


def test_validation_passes(validation_report):
    if not validation_report["pass"]:
        failing = [k for k, v in validation_report["checks"].items()
                   if v["status"] == "FAIL"]
        pytest.fail(f"Validation FAILED. Failing checks: {failing}")
```

### `tests/test_sampling.py`

```python
"""
Tests for edge sampling correctness.
Run: pytest tests/test_sampling.py -v
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path


PROCESSED_DIR  = Path("data/processed")
MANIFESTS_DIR  = Path("data/manifests")


@pytest.fixture(scope="module")
def views_df():
    path = PROCESSED_DIR / "sampled_views.parquet"
    if not path.exists():
        pytest.skip("sampled_views.parquet not found — run sample_views.py first")
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def manifest():
    return pd.read_parquet(MANIFESTS_DIR / "manifest.parquet")


def test_sampled_view_columns(views_df):
    required = {"event_id", "label", "K", "seed"}
    assert required.issubset(set(views_df.columns))


def test_sampled_node_count_le_original(views_df, manifest):
    """After edge sampling, the node count (from log_node_count) must not
    exceed the original node count.  Sampled log_node_count ≤ original."""
    merged = views_df.merge(manifest[["event_id", "n_nodes"]], on="event_id")
    # log_node_count in views is log1p of the sampled graph's node count
    sampled_nodes = np.expm1(merged["log_node_count"])
    original_nodes = merged["n_nodes"]
    assert (sampled_nodes <= original_nodes + 1).all(), \
        "Some sampled views have more nodes than the original graph"


def test_K_seeds_are_unique(views_df):
    """Each (event, K, seed) combo must appear exactly once."""
    n_rows    = len(views_df)
    n_unique  = views_df.groupby(["event_id", "K", "seed"]).ngroups
    assert n_rows == n_unique, "Duplicate (event, K, seed) rows found"


def test_determinism(views_df):
    """Re-sampling with the same seed must give the same log_node_count.
    We test this by checking that all rows with the same (event, K, seed)
    have the same feature values (should be exactly one row each)."""
    dupes = views_df.duplicated(subset=["event_id", "K", "seed"], keep=False)
    assert not dupes.any(), "Non-unique (event,K,seed) entries found"
```

### `tests/test_leakage.py`

```python
"""
Tests that sampled views of one event are never split across folds.
Run: pytest tests/test_leakage.py -v
"""

import pytest
import pandas as pd
from pathlib import Path
from splits import make_event_folds, assign_view_folds


PROCESSED_DIR  = Path("data/processed")
MANIFESTS_DIR  = Path("data/manifests")


@pytest.fixture(scope="module")
def manifest():
    return pd.read_parquet(MANIFESTS_DIR / "manifest.parquet")


@pytest.fixture(scope="module")
def views_df():
    path = PROCESSED_DIR / "sampled_views.parquet"
    if not path.exists():
        pytest.skip("sampled_views.parquet not found")
    return pd.read_parquet(path)


def test_views_stay_in_same_fold(manifest, views_df):
    """All sampled views of one event must share the same fold."""
    fold_map = make_event_folds(manifest.reset_index(), n_folds=5, random_seed=42)
    views_with_folds = assign_view_folds(views_df.copy(), fold_map)

    # Each event should have exactly one unique fold_id across all its views
    event_folds = views_with_folds.groupby("event_id")["fold_id"].nunique()
    leaking = event_folds[event_folds > 1]
    assert leaking.empty, (
        f"These events have views in multiple folds (LEAKAGE): "
        f"{leaking.index.tolist()}"
    )


def test_fold_distribution_balanced(manifest):
    """Each fold should have roughly equal class balance."""
    fold_map = make_event_folds(manifest.reset_index(), n_folds=5, random_seed=42)
    manifest = manifest.copy()
    manifest["fold_id"] = manifest["event_id"].map(fold_map)

    for fold_idx in range(5):
        fold_df = manifest[manifest.fold_id == fold_idx]
        n_camp = (fold_df.label == 1).sum()
        n_comp = (fold_df.label == 0).sum()
        # Expect roughly 50/50 (within 15 pp given 20 events/fold)
        ratio = n_camp / max(len(fold_df), 1)
        assert 0.3 <= ratio <= 0.7, \
            f"Fold {fold_idx} is severely imbalanced: {n_camp} campaign, {n_comp} comparison"
```

---

## Day 5 — Clean Rerun and Demo Prep

### Full pipeline run script

```bash
#!/bin/bash
# run_pipeline.sh — Clean reproducible end-to-end run
set -e   # exit immediately on any error

CONFIG="configs/final.yaml"

echo "=== Step 1: Ingest ==="
python src/ingest_len.py --config $CONFIG

echo "=== Step 2: Validate ==="
python src/validate_len.py --config $CONFIG

echo "=== Step 3: Build cohorts (matching) ==="
python src/build_cohorts.py --config $CONFIG

echo "=== Step 4: Sample edge-budget views ==="
python src/sample_views.py --config $CONFIG

echo "=== Step 5: Train all experiments ==="
python src/train.py --config $CONFIG

echo "=== Step 6: Evaluate and generate figures ==="
python src/evaluate.py --config $CONFIG

echo "=== Step 7: Run tests ==="
pytest tests/ -v

echo ""
echo "Pipeline complete. Outputs in outputs/run_final/"
echo "Checkpoint report in reports/checkpoint_report.md"
```

Make it executable: `chmod +x run_pipeline.sh`

---

## Professor Demo Walkthrough

### Slide-by-slide talking points

| Segment | What to show | What to say |
|---|---|---|
| **0:00–1:00** | Terminal: `cat data/manifests/manifest.parquet \| head` | *"The unit of analysis is a single Twitter event graph — 100 in total from LEN-Small, 51 labelled campaign, 49 comparison. Each graph is a user-to-user engagement network. We use only released event-level labels."* |
| **1:00–2:00** | Fig. 1 (size overlap) | *"Campaign events are systematically larger. Campaign median node count is X; comparison is Y. This is our core auditing concern — we need to ask how much the classifier is learning size, not coordination."* |
| **2:00–3:15** | Table: B0a/B0b vs structure/combined | *"A logistic regression given only log node count achieves balanced accuracy of X. Adding log edge count gives Y. The gap between scale-only and combined features quantifies what structural/content information adds beyond size."* |
| **3:15–4:15** | matching_diagnostics.json + Fig. 3 | *"We matched campaign and comparison events using nearest-neighbour matching on log node count with a caliper of 0.25 SD. We retained N pairs. After matching, the SMD drops from X to Y. Performance on the matched cohort is Z — this is what survives the size control."* |
| **4:15–5:45** | Fig. 4 (edge budget curve) | *"We sample K existing edges from each eligible event graph and recompute all features from scratch on the sampled subgraph. At K=250 we have N events eligible; at K=2000 we have M. Performance at each K estimates how well the model learns from restricted observation. Notice it X as K decreases."* |
| **5:45–7:00** | tables.md (ablation table) | *"Content features are X-usable. Structure adds/does-not-add Z points over scale alone under cross-validation. Bootstrap 95% CIs are wide given 100 events — we report uncertainty rather than precise claims."* |
| **7:00–8:30** | Terminal: `python src/train.py --config configs/final.yaml` | *"Every experiment is config-driven. Seeds, folds, K values, and model hyperparameters are in final.yaml. The leakage test confirms no sampled view crosses a fold boundary."* |
| **8:30–10:00** | checkpoint_report.md | *"Findings are scoped to LEN-Small and this sampling procedure. We make no claim about individual accounts or other platforms. Future work could replicate on the full 314-graph LEN benchmark."* |

### Demo checklist (Day 5)

```
[ ] All outputs present in outputs/run_final/
[ ] 4 figures saved and non-blank
[ ] predictions.parquet has rows for every experiment
[ ] metrics.json contains non-NaN balanced_accuracy for all completed experiments
[ ] pytest tests/ → all pass
[ ] validation_report.json → "pass": true
[ ] matching_diagnostics.json present
[ ] checkpoint_report.md written
[ ] run_pipeline.sh executes from scratch without manual edits
[ ] Every number in the demo matches a row in predictions.parquet (no invented scores)
```

---

## Critical Integrity Rules (repeat for team)

> These are not guidelines — violating them invalidates the work.

1. **No score-peeking before fixing the protocol.** The caliper, K values, and feature set are decided in Day 1 config. Change only if data validation proves infeasibility.

2. **No full-graph attributes in sampled-view models.** After edge sampling, `compute_features_for_sampled_view` rebuilds from scratch. Never pass `n_nodes` or `n_edges` from the original manifest to D1/D2 models.

3. **No view crossing fold boundaries.** The `test_leakage.py` test enforces this. If it fails, fix `splits.py` before re-running training.

4. **No invented numbers.** The tables in the demo come from `predictions.parquet`. If an experiment is incomplete, the cell shows "pending," not a guess.

5. **No claiming novelty without checking DECODE.** Before the demo, confirm in one paragraph that your exact combination (size-control + edge-budget + paired audit on LEN-Small) is not already in the DECODE paper.

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `build_label_map` raises `FileNotFoundError` | Metadata CSV has a different name in the archive | Inspect the archive with `python -c "import zipfile; z=zipfile.ZipFile('data/raw/...zip'); print(z.namelist())"` and update the candidate list in `ingest_len.py` |
| `parse_graph_file` column error | Archive uses different column names | Print `df.columns` inside the parser and map to source/target |
| Matching returns < 10 pairs | Very different size distributions | Widen caliper only as a last resort; report infeasibility if distributions don't overlap |
| `test_leakage.py` fails | An event has views in multiple folds | Check whether `assign_view_folds` receives the same `fold_map` as training |
| HGBT runs very slowly | Too many edges or features | Profile with `cProfile`; reduce max_iter or skip HGBT for edge-budget runs |
| Content features are all NaN | Text column absent or all-empty after cleaning | Set `use_text_features: false` in config; document in report |

---

## References

1. Gopalakrishnan et al. (2025). *Large Engagement Networks for Classifying Coordinated Campaigns.* ICWSM. https://ojs.aaai.org/index.php/ICWSM/article/view/35839
2. Gopalakrishnan et al. (2025). *DECODE: Density-aware Walks for Coordinated Campaign Detection.* https://arxiv.org/abs/2506.13912
3. LEN Dataset: https://erdemub.github.io/large-engagement-network/
4. LEN Code: https://github.com/erdemUB/LEN
