"""
ingest_len.py
-------------
Ingests the LEN project archive from small_encoder_final.tar without extracting
uncompressed JSON files to disk.

Key operations:
1. Streams members from small_encoder_final.tar.
2. Identifies graph files and computes SHA-256 hashes.
3. Detects identical duplicate graphs (e.g. Turkish character variant).
4. Drops 772-dimensional embedding vectors (node_attr, edge_attr) to keep
   processed tables lightweight and fast.
5. Emits canonical Parquet tables:
   - data/manifests/manifest.parquet
   - data/processed/nodes.parquet
   - data/processed/edges.parquet
"""

import sys
import os
import json
import hashlib
import argparse
import unicodedata
from pathlib import Path
from datetime import datetime, timezone
import tarfile

import pandas as pd
import yaml
from tqdm import tqdm

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ingest(config: dict) -> None:
    archive_path = Path(config["data"].get("archive_path", "small_encoder_final.tar"))
    processed_dir = Path(config["data"]["processed_dir"])
    manifests_dir = Path(config["data"]["manifests_dir"])

    processed_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    print(f"Reading archive: {archive_path}")
    with tarfile.open(archive_path, "r:*") as tf:
        members = [m for m in tf.getmembers() if m.isfile() and m.name.endswith(".json")]
        print(f"Found {len(members)} JSON graph members in archive.")

        # Pass 1: Deduplication by SHA-256
        seen_hashes = {}
        unique_members = []
        duplicate_records = []

        for m in members:
            f = tf.extractfile(m)
            content = f.read()
            h = hashlib.sha256(content).hexdigest()
            norm_name = unicodedata.normalize("NFC", m.name.split("/")[-1])
            if h in seen_hashes:
                duplicate_records.append({
                    "duplicate_file": m.name,
                    "canonical_file": seen_hashes[h],
                    "sha256": h
                })
                print(f"  [Deduplication] Dropping exact duplicate: {norm_name} (matches {seen_hashes[h]})")
            else:
                seen_hashes[h] = norm_name
                unique_members.append((m, norm_name, h, content))

        print(f"\nUnique event graphs retained: {len(unique_members)}")
        if duplicate_records:
            dup_path = manifests_dir / "duplicate_files.json"
            with open(dup_path, "w", encoding="utf-8") as f:
                json.dump(duplicate_records, f, indent=2, ensure_ascii=False)
            print(f"  Saved duplicate audit log -> {dup_path}")

        # Pass 2: Parsing graphs into structured tables
        manifest_rows = []
        all_nodes = []
        all_edges = []

        for m, norm_name, file_hash, content in tqdm(unique_members, desc="Parsing graphs"):
            data = json.loads(content.decode("utf-8"))
            event_id = norm_name.replace(".json", "")
            
            # Authoritative label from dataset file nomenclature
            if "_campaign_" in norm_name:
                label = 1
                label_str = "campaign"
            elif "_noncampaign_" in norm_name:
                label = 0
                label_str = "comparison"
            else:
                raise ValueError(f"Unrecognized class label in filename: {norm_name}")

            raw_nodes = data.get("nodes", [])
            raw_links = data.get("links", [])
            n_nodes = len(raw_nodes)
            n_edges = len(raw_links)

            manifest_rows.append({
                "event_id": event_id,
                "label": label,
                "label_str": label_str,
                "n_nodes": n_nodes,
                "n_edges": n_edges,
                "file_name": norm_name,
                "file_size_bytes": m.size,
                "sha256": file_hash,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            })

            # Extract node IDs
            for node in raw_nodes:
                all_nodes.append({
                    "event_id": event_id,
                    "node_id": str(node.get("id", ""))
                })

            # Extract link topology and lightweight attributes (discarding 776-dim edge_attr)
            for link in raw_links:
                all_edges.append({
                    "event_id": event_id,
                    "source": str(link.get("source", "")),
                    "target": str(link.get("target", "")),
                    "text": link.get("text", ""),
                    "timestamp": link.get("timestamp"),
                    "interaction_count": link.get("Interaction_Count", 1),
                })

    # Save Parquet outputs
    manifest_df = pd.DataFrame(manifest_rows)
    manifest_out = manifests_dir / "manifest.parquet"
    manifest_df.to_parquet(manifest_out, index=False)
    print(f"\nManifest saved: {len(manifest_df)} events -> {manifest_out}")

    nodes_df = pd.DataFrame(all_nodes)
    nodes_out = processed_dir / "nodes.parquet"
    nodes_df.to_parquet(nodes_out, index=False)
    print(f"Nodes table saved: {len(nodes_df)} rows -> {nodes_out}")

    edges_df = pd.DataFrame(all_edges)
    edges_out = processed_dir / "edges.parquet"
    edges_df.to_parquet(edges_out, index=False)
    print(f"Edges table saved: {len(edges_df)} rows -> {edges_out}")

    # Summary
    n_camp = (manifest_df["label"] == 1).sum()
    n_comp = (manifest_df["label"] == 0).sum()
    print("\n--- Ingestion Summary ---")
    print(f"Total events : {len(manifest_df)}")
    print(f"Campaign     : {n_camp}")
    print(f"Comparison   : {n_comp}")
    print(f"Node range   : {manifest_df['n_nodes'].min()} - {manifest_df['n_nodes'].max()}")
    print(f"Edge range   : {manifest_df['n_edges'].min()} - {manifest_df['n_edges'].max()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest the LEN project archive")
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    ingest(cfg)
