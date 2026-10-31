"""
validate_len.py
---------------
Performs schema, integrity, and data-quality checks on ingested tables
and outputs data/manifests/validation_report.json.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import yaml

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(config: dict) -> dict:
    manifests_dir = Path(config["data"]["manifests_dir"])
    processed_dir = Path(config["data"]["processed_dir"])

    manifest_path = manifests_dir / "manifest.parquet"
    edges_path = processed_dir / "edges.parquet"
    nodes_path = processed_dir / "nodes.parquet"

    if not manifest_path.exists() or not edges_path.exists() or not nodes_path.exists():
        raise FileNotFoundError("Ingested tables missing. Run src/ingest_len.py first.")

    manifest = pd.read_parquet(manifest_path)
    edges = pd.read_parquet(edges_path)
    nodes = pd.read_parquet(nodes_path)

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

    # 1. Event counts
    n_total = len(manifest)
    n_camp = int((manifest["label"] == 1).sum())
    n_comp = int((manifest["label"] == 0).sum())

    expected_total = config["data"]["expected_events"]
    expected_camp = config["data"]["expected_campaign"]
    expected_comp = config["data"]["expected_comparison"]

    if n_total == expected_total:
        ok("event_count", f"{n_total} events matches expected {expected_total}")
    else:
        fail("event_count", f"Expected {expected_total}, got {n_total}")

    if n_camp == expected_camp:
        ok("campaign_count", f"{n_camp} campaign events")
    else:
        fail("campaign_count", f"Expected {expected_camp}, got {n_camp}")

    if n_comp == expected_comp:
        ok("comparison_count", f"{n_comp} comparison events")
    else:
        fail("comparison_count", f"Expected {expected_comp}, got {n_comp}")

    # 2. Duplicate event IDs
    dupes = manifest[manifest["event_id"].duplicated()]
    if dupes.empty:
        ok("no_duplicate_event_ids")
    else:
        fail("no_duplicate_event_ids", f"Duplicate event IDs: {dupes['event_id'].tolist()}")

    # 3. Empty graphs
    empty_nodes = manifest[manifest["n_nodes"] == 0]
    empty_edges = manifest[manifest["n_edges"] == 0]
    if empty_nodes.empty:
        ok("no_empty_node_graphs")
    else:
        fail("no_empty_node_graphs", f"Events with 0 nodes: {empty_nodes['event_id'].tolist()}")

    if empty_edges.empty:
        ok("no_empty_edge_graphs")
    else:
        warn("no_empty_edge_graphs", f"Events with 0 edges: {empty_edges['event_id'].tolist()}")

    # 4. Edge columns
    edge_cols = list(edges.columns)
    report["edge_columns_present"] = edge_cols
    for col in ["source", "target", "event_id"]:
        if col not in edge_cols:
            fail(f"edge_col_{col}", f"Column '{col}' missing from edges")
        else:
            ok(f"edge_col_{col}")

    # 5. Text column audit
    if "text" in edge_cols:
        text_nonempty_per_event = edges.groupby("event_id")["text"].apply(lambda s: (s.str.strip() != "").any())
        events_with_text = int(text_nonempty_per_event.sum())
        total_events_in_edges = int(len(text_nonempty_per_event))
        ok("text_column_present", f"{events_with_text}/{total_events_in_edges} events have non-empty text")
        if events_with_text < total_events_in_edges:
            warn("text_coverage", f"{total_events_in_edges - events_with_text} events have missing/empty text")
    else:
        warn("text_column_present", "No text column in edges table")

    # 6. Timestamp column audit
    if "timestamp" in edge_cols:
        ts_valid = edges["timestamp"].notna().sum()
        ok("timestamp_column_present", f"Timestamp present ({ts_valid}/{len(edges)} non-null). Temporal features remain OFF per config.")
    else:
        ok("timestamp_absent", "Timestamp column not present")

    # 7. Interaction count semantics
    if "interaction_count" in edge_cols:
        ic_min = edges["interaction_count"].min()
        ic_max = edges["interaction_count"].max()
        report["interaction_count_range"] = [float(ic_min), float(ic_max)]
        if ic_min >= 1:
            ok("interaction_count_ge1", f"Range [{ic_min}, {ic_max}], all >= 1")
        else:
            warn("interaction_count_ge1", f"interaction_count has values < 1: min={ic_min}")

    # 8. Duplicate edges within an event
    dup_edges = edges[edges.duplicated(subset=["event_id", "source", "target"])]
    report["duplicate_edges_count"] = int(len(dup_edges))
    if dup_edges.empty:
        ok("no_duplicate_edges")
    else:
        warn("no_duplicate_edges", f"{len(dup_edges)} multigraph duplicate edges found; will be collapsed in simple DiGraph views")

    # 9. Node identifier scheme. If every graph numbers its nodes 0..N-1, node IDs are
    # per-graph indices, not account identifiers, and cross-event account overlap
    # cannot be measured (equal IDs in two graphs need not be the same account).
    ids = pd.to_numeric(nodes["node_id"], errors="coerce")
    per_event = nodes.assign(_id=ids).groupby("event_id")["_id"].agg(["min", "max", "nunique", "size"])
    per_graph_index = bool(ids.notna().all() and (per_event["min"] == 0).all()
                           and (per_event["max"] == per_event["size"] - 1).all()
                           and (per_event["nunique"] == per_event["size"]).all())
    report["node_id_scheme"] = {
        "per_graph_indices_0_to_n_minus_1": per_graph_index,
        "cross_event_account_overlap": "not measurable: node IDs are per-graph indices" if per_graph_index
                                       else "node IDs are not per-graph indices; overlap not computed here",
    }
    if per_graph_index:
        ok("node_id_scheme", "node IDs are per-graph indices 0..N-1 in every event; the release has no account identifiers")
    else:
        warn("node_id_scheme", "node IDs are not uniformly per-graph indices; inspect before any account-level analysis")

    # Write report
    out_path = manifests_dir / "validation_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    status = "PASS" if report["pass"] else "FAIL"
    print(f"\nValidation Result: {status}")
    print(f"Report written to {out_path}")
    if report["warnings"]:
        print(f"Warnings ({len(report['warnings'])}):")
        for w in report["warnings"]:
            print(f"  - {w}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate ingested LEN-Small tables")
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    validate(cfg)
