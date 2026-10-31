"""
sample_views.py
---------------
For each edge budget K in config (e.g. 250, 500, 1000) and each seed (10 seeds),
samples K existing edges without replacement from each eligible event graph.

Eligibility: event must have at least K edges.

For each (event, K, seed):
  1. Sample K edges without replacement.
  2. Keep edge attributes attached (text, interaction_count).
  3. Rebuild the graph from sampled edges (incident nodes only).
  4. Recompute all features from scratch.
  5. Never use full-graph attributes or original node/edge counts.

Outputs:
  data/processed/sampled_views.parquet
  data/manifests/edge_budget_eligibility.json
"""

import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

from features import compute_features_for_sampled_view

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def sample_views(config: dict) -> None:
    processed_dir = Path(config["data"]["processed_dir"])
    manifests_dir = Path(config["data"]["manifests_dir"])

    manifest = pd.read_parquet(manifests_dir / "manifest.parquet")
    edges_df = pd.read_parquet(processed_dir / "edges.parquet")

    K_values = config["edge_budgets"]["K_values"]
    n_seeds = config["edge_budgets"]["n_seeds"]
    base_seed = config["edge_budgets"]["base_seed"]

    eligibility: dict[str, dict] = {}
    all_rows = []

    # Also log K=2000 eligibility for documentation
    for check_k in sorted(list(set(K_values + [2000]))):
        sub_eids = manifest[manifest["n_edges"] >= check_k]["event_id"].tolist()
        n_camp = int(manifest[manifest["event_id"].isin(sub_eids) & (manifest["label"] == 1)].shape[0])
        n_comp = int(manifest[manifest["event_id"].isin(sub_eids) & (manifest["label"] == 0)].shape[0])
        eligibility[str(check_k)] = {
            "eligible_event_ids": sub_eids,
            "total_eligible": len(sub_eids),
            "campaign_eligible": n_camp,
            "comparison_eligible": n_comp,
            "feasible_for_5fold_cv": bool(n_camp >= 5 and n_comp >= 5)
        }

    for K in K_values:
        print(f"\nProcessing Edge Budget K = {K}")
        eligible = eligibility[str(K)]["eligible_event_ids"]
        n_camp = eligibility[str(K)]["campaign_eligible"]
        n_comp = eligibility[str(K)]["comparison_eligible"]
        print(f"  Eligible events: {len(eligible)} / {len(manifest)} (Campaign: {n_camp}, Comparison: {n_comp})")

        if len(eligible) == 0:
            print("  No eligible events - skipping K")
            continue

        for seed_idx in range(n_seeds):
            seed_val = base_seed + seed_idx
            rng = np.random.default_rng(seed_val)

            for eid in tqdm(eligible, desc=f"  K={K} seed={seed_val}", leave=False):
                ev_edges = edges_df[edges_df["event_id"] == eid]
                label_val = int(manifest[manifest["event_id"] == eid].iloc[0]["label"])

                # Sample K edges without replacement
                sampled_indices = rng.choice(len(ev_edges), size=K, replace=False)
                sampled_edges = ev_edges.iloc[sampled_indices].reset_index(drop=True)

                # Recompute features from scratch on restricted view
                feats = compute_features_for_sampled_view(sampled_edges, eid, label_val, config)
                feats["K"] = K
                feats["seed"] = seed_val
                all_rows.append(feats)

    # Save sampled views
    views_df = pd.DataFrame(all_rows)
    out_views = processed_dir / config["edge_budgets"].get("views_file", "sampled_views.parquet")
    views_df.to_parquet(out_views, index=False)
    print(f"\nSampled views saved: {len(views_df)} rows -> {out_views}")

    elig_path = manifests_dir / "edge_budget_eligibility.json"
    with open(elig_path, "w", encoding="utf-8") as f:
        json.dump(eligibility, f, indent=2, ensure_ascii=False)
    print(f"Eligibility report saved -> {elig_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sample fixed edge-budget views")
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    sample_views(cfg)
