"""
build_cohorts.py
----------------
Match campaign and comparison events on log(node_count) using
nearest-neighbour matching with a fixed caliper.

Computes:
1. Retained pairs and exclusions.
2. Standardised Mean Difference (SMD) before and after matching.
3. Outputs matched_manifest.parquet and matching_diagnostics.json.
"""

import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def standardised_mean_difference(values: np.ndarray, labels: np.ndarray) -> float:
    v_c = values[labels == 1]
    v_k = values[labels == 0]
    if len(v_c) < 2 or len(v_k) < 2:
        return 0.0
    pooled_sd = np.sqrt((v_c.var(ddof=1) + v_k.var(ddof=1)) / 2.0)
    if pooled_sd == 0:
        return 0.0
    return float((v_c.mean() - v_k.mean()) / pooled_sd)


def match_cohort(manifest: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, dict]:
    mc = config["matching"]
    rng = np.random.default_rng(mc["random_seed"])

    log_nc = np.log1p(manifest["n_nodes"].values)
    caliper_abs = mc["caliper_sd_fraction"] * float(np.std(log_nc, ddof=1))

    campaign_idx = manifest.index[manifest["label"] == 1].tolist()
    comparison_idx = manifest.index[manifest["label"] == 0].tolist()

    # Reproducible shuffle of campaign events to eliminate arbitrary order bias
    rng.shuffle(campaign_idx)

    available_comparisons = set(comparison_idx)
    matched_pairs = []

    log_nc_by_idx = {i: np.log1p(manifest.loc[i, "n_nodes"]) for i in manifest.index}

    for ci in campaign_idx:
        lnc_c = log_nc_by_idx[ci]
        candidates = [
            ki for ki in available_comparisons
            if abs(log_nc_by_idx[ki] - lnc_c) <= caliper_abs
        ]
        if not candidates:
            continue
        best = min(candidates, key=lambda ki: abs(log_nc_by_idx[ki] - lnc_c))
        matched_pairs.append((ci, best))
        available_comparisons.discard(best)

    matched_indices = [idx for pair in matched_pairs for idx in pair]
    matched_df = manifest.loc[matched_indices].copy()
    matched_df["matched_pair_id"] = [
        pid for pid, _ in enumerate(matched_pairs) for _ in range(2)
    ]

    log_nc_arr = np.array([log_nc_by_idx[i] for i in manifest.index])
    labels_arr = manifest["label"].values
    log_nc_m = np.array([log_nc_by_idx[i] for i in matched_indices])
    labels_m = matched_df["label"].values

    diag = {
        "caliper_abs": round(float(caliper_abs), 4),
        "caliper_sd_fraction": float(mc["caliper_sd_fraction"]),
        "n_campaign_total": int((manifest["label"] == 1).sum()),
        "n_comparison_total": int((manifest["label"] == 0).sum()),
        "n_matched_pairs": int(len(matched_pairs)),
        "n_campaign_matched": int((matched_df["label"] == 1).sum()),
        "n_comparison_matched": int((matched_df["label"] == 0).sum()),
        "n_excluded": int(len(manifest) - len(matched_df)),
        "smd_before": round(standardised_mean_difference(log_nc_arr, labels_arr), 4),
        "smd_after": round(standardised_mean_difference(log_nc_m, labels_m), 4) if len(matched_pairs) > 0 else None,
        "log_node_count_campaign_mean_before": round(float(np.mean(log_nc_arr[labels_arr == 1])), 4),
        "log_node_count_comparison_mean_before": round(float(np.mean(log_nc_arr[labels_arr == 0])), 4),
        "log_node_count_campaign_mean_after": round(float(np.mean(log_nc_m[labels_m == 1])), 4) if len(matched_pairs) > 0 else None,
        "log_node_count_comparison_mean_after": round(float(np.mean(log_nc_m[labels_m == 0])), 4) if len(matched_pairs) > 0 else None,
    }

    return matched_df, diag


def build_cohorts(config: dict) -> None:
    manifests_dir = Path(config["data"]["manifests_dir"])
    manifest = pd.read_parquet(manifests_dir / "manifest.parquet")

    print(f"Full cohort: {len(manifest)} events")
    print(f"  Campaign   : {(manifest['label'] == 1).sum()}")
    print(f"  Comparison : {(manifest['label'] == 0).sum()}")

    matched_df, diag = match_cohort(manifest, config)

    out_manifest = manifests_dir / "matched_manifest.parquet"
    matched_df.to_parquet(out_manifest, index=False)

    out_diag = manifests_dir / "matching_diagnostics.json"
    with open(out_diag, "w", encoding="utf-8") as f:
        json.dump(diag, f, indent=2, ensure_ascii=False)

    print("\n--- Matching Diagnostics ---")
    print(f"Caliper (abs units) : {diag['caliper_abs']} ({diag['caliper_sd_fraction']} SD)")
    print(f"Matched pairs       : {diag['n_matched_pairs']}")
    print(f"Retained events     : {diag['n_campaign_matched']} campaign, {diag['n_comparison_matched']} comparison")
    print(f"Excluded events     : {diag['n_excluded']}")
    print(f"SMD before matching : {diag['smd_before']}")
    print(f"SMD after matching  : {diag['smd_after']}")
    print(f"\nSaved matched manifest -> {out_manifest}")
    print(f"Saved diagnostics      -> {out_diag}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build size-matched cohort")
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    build_cohorts(cfg)
