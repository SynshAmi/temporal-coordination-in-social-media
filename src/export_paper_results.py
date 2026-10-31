"""
export_paper_results.py
-----------------------
Collects every number reported in the paper and on the website into one
machine-readable file, <run_dir>/paper_results.json, built only from the
corrected run (configs/v2_coreness_fix.yaml -> outputs/run_v2) and its verified
study outputs. The paper builder, paper figures, website export and the
claim-to-evidence audit all read this file; nothing is typed in by hand.

Each value is stored with its source artifact so claims stay traceable.
"""

import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from study1_incremental import paired_bootstrap  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main(config_path: str) -> None:
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    run = Path(cfg["output"]["run_dir"])
    man_dir = Path(cfg["data"]["manifests_dir"])
    manifest = pd.read_parquet(man_dir / "manifest.parquet")
    edges = pd.read_parquet(Path(cfg["data"]["processed_dir"]) / "edges.parquet")
    dup = load(man_dir / "duplicate_files.json")
    diag = load(man_dir / "matching_diagnostics.json")
    elig = load(man_dir / "edge_budget_eligibility.json")
    metrics = load(run / "metrics.json")
    s1 = load(run / "study1" / "nested_results.json")
    s1_null = load(run / "study1" / "null_results.json")
    s1_match = load(run / "study1" / "matching_sensitivity.json")
    s2 = load(run / "study2" / "results.json")
    ver = load(run / "verification" / "verification_report.json")
    assert ver["n_pass"] == ver["n_checks"], "independent verification has failing checks"

    def size_stats(col, lab):
        v = manifest.loc[manifest.label == lab, col]
        return {"median": float(v.median()), "q25": float(v.quantile(.25)), "q75": float(v.quantile(.75)), "mean": float(v.mean())}

    R_ = run.as_posix()
    out = {"source_run": R_, "config": Path(config_path).as_posix()}
    out["dataset"] = {
        "_source": f"{man_dir.as_posix()}/{{manifest.parquet,duplicate_files.json}}, {Path(cfg['data']['processed_dir']).as_posix()}/edges.parquet",
        "archive_json_files": int(len(manifest) + len(dup)),
        "duplicates_removed": len(dup),
        "duplicate_sha256": dup[0]["sha256"] if dup else None,
        "n_events": int(len(manifest)),
        "n_campaign": int((manifest.label == 1).sum()),
        "n_comparison": int((manifest.label == 0).sum()),
        "n_edges_total": int(len(edges)),
        "n_self_loops": int((edges.source == edges.target).sum()),
        "events_with_self_loops": int(edges[edges.source == edges.target].event_id.nunique()),
        "nodes": {"campaign": size_stats("n_nodes", 1), "comparison": size_stats("n_nodes", 0)},
        "edges": {"campaign": size_stats("n_edges", 1), "comparison": size_stats("n_edges", 0)},
        "official_len_small": {"n_graphs": 100, "n_campaign": 51, "n_noncampaign": 49,
                               "selection_rule": "smallest 100 of 314 LEN graphs by node count",
                               "_source": "Gopalakrishnan et al., ICWSM 2025 (arXiv:2503.00599), Table 3 caption"},
        "full_len": {"n_graphs": 314, "n_campaign": 179, "n_noncampaign": 135},
        "smd_log_nodes_full_cohort": diag["smd_before"],
    }
    out["eligibility"] = {k: {kk: v[kk] for kk in ("total_eligible", "campaign_eligible", "comparison_eligible", "feasible_for_5fold_cv")}
                          for k, v in elig.items()}

    # ---------------- Study 1
    lr, hg = s1["models"]["logreg"], s1["models"]["hgbt"]
    oof = pd.read_parquet(run / "study1" / "oof_predictions.parquet")
    get = lambda m, o, lv: oof[(oof.model == m) & (oof.objective == o) & (oof.experiment == lv)].set_index("event_id").sort_index()
    y = get("logreg", "ba", "M0q").label.values
    cross = {}
    for lv in ("M3", "M4"):
        for obj in ("ba", "ll"):
            r = paired_bootstrap(y, get("hgbt", obj, lv).prob_campaign.values, get("logreg", obj, "M0q").prob_campaign.values,
                                 cfg["study1"]["n_bootstrap"], cfg["study1"]["bootstrap_seed"])
            cross[f"HGBT_{lv}_vs_LR_M0q_{obj}"] = r
    rs = ver["s1_row_order_sensitivity"]
    out["study1"] = {
        "_source": f"{R_}/study1/{{nested_results.json, oof_predictions.parquet}}",
        "levels": s1["levels"], "estimand_rule": s1["estimand_rule"],
        "performance": {"logreg": lr["performance"], "hgbt": hg["performance"]},
        "confirmatory": {"logreg": lr["confirmatory"], "hgbt": hg["confirmatory"]},
        "exploratory": {"logreg": lr["exploratory"], "hgbt": hg["exploratory"]},
        "repeated_splits_lr": s1["repeated_splits_lr_summary"],
        "n_split_seeds": len(cfg["study1"]["split_seeds"]),
        "hgbt_vs_best_count_baseline": {k: {kk: v[kk] for kk in ("delta_ba", "delta_ba_ci", "delta_logloss", "delta_logloss_ci", "delta_auc", "delta_auc_ci")}
                                        for k, v in cross.items()},
        "row_order_sensitivity": {k: v for k, v in rs.items() if "delta_study_order" in v},
        "_row_order_source": f"{R_}/verification/verification_report.json",
        "n_bootstrap": cfg["study1"]["n_bootstrap"],
    }
    mix = ver["null_mixing"]
    out["null_model"] = {
        "_source": f"{R_}/study1/{{null_results.json, null_pilot.csv, null_features.parquet}}; verification_report.json",
        "swaps_per_edge": s1_null["swaps_per_edge"], "realizations": s1_null["realizations"],
        "M1_ba": s1_null["M1"]["balanced_accuracy"], "M2_real_ba": s1_null["M2_real"]["balanced_accuracy"],
        "M2_null_ba_mean": s1_null["M2_null_ba_mean"],
        "M2_null_ba_range": [min(r["balanced_accuracy"] for r in s1_null["M2_null_per_realization"]),
                             max(r["balanced_accuracy"] for r in s1_null["M2_null_per_realization"])],
        "real_minus_null_ba": {k: s1_null["M2_real_vs_null_avg"][k] for k in ("delta_ba", "delta_ba_ci")},
        "real_minus_null_logloss": {k: s1_null["log_loss_estimand"]["M2_real_vs_null_avg_ll_fit"][k] for k in ("delta_logloss", "delta_logloss_ci")},
        "M2_real_logloss": s1_null["log_loss_estimand"]["M2_real_ll_fit"]["log_loss"],
        "mean_frac_edges_unchanged": s1_null["mean_frac_edges_unchanged"],
        "frac_edges_unchanged_quantiles": mix["frac_edges_unchanged_quantiles"],
        "pilot": mix["pilot_mean_by_swaps_per_edge"],
        "share_events_zero_null_variance": mix["share_events_zero_null_variance"],
        "observed_vs_null_median_z": s1_null["observed_vs_null_z"],
    }

    def msum(rows):
        df = pd.DataFrame([r for r in rows if not r.get("skipped")])
        return {"n_order_seeds": int(len(df)), "n_pairs_range": [int(df.n_pairs.min()), int(df.n_pairs.max())],
                "smd_log_nodes_median": float(df.smd_log_nodes.median()), "smd_log_edges_median": float(df.smd_log_edges.median()),
                "smd_log_edges_range": [float(df.smd_log_edges.min()), float(df.smd_log_edges.max())],
                "ba": {lv: {"median": float(df[f"ba_{lv}"].median()), "min": float(df[f"ba_{lv}"].min()), "max": float(df[f"ba_{lv}"].max())}
                       for lv in ("M0", "M1", "M2", "M3", "M4")}}
    out["matching"] = {"_source": f"{R_}/study1/matching_sensitivity.json; {man_dir.as_posix()}/matching_diagnostics.json",
                       "caliper_sd_fraction": cfg["matching"]["caliper_sd_fraction"], "caliper_abs": diag["caliper_abs"],
                       "primary_pairs": diag["n_matched_pairs"], "n_excluded": diag["n_excluded"],
                       "smd_before": diag["smd_before"], "smd_after": diag["smd_after"],
                       "node_only": msum(s1_match["node_only"]), "node_edge": msum(s1_match["node_edge"])}

    # ---------------- Study 2
    out["study2"] = {"_source": f"{R_}/study2/{{results.json, view_predictions.parquet}}",
                     "feature_sets": s2["feature_sets"], "results": s2["results"], "contrasts": s2["contrasts"],
                     "mechanism": s2["mechanism"], "mechanism_r2_K250": ver["mechanism"]["r2_log_expected_NK_K250"],
                     "mechanism_monte_carlo": ver["mechanism"]["monte_carlo"]}

    # ---------------- Legacy experiment grid of the corrected run (for the website benchmark table)
    out["run_v2_metrics"] = {"_source": f"{R_}/metrics.json", **metrics}
    out["verification"] = {"_source": f"{R_}/verification/verification_report.json",
                           "n_pass": ver["n_pass"], "n_checks": ver["n_checks"], "checks": [c["check"] for c in ver["checks"]]}

    # Archived original run: used only for the correction-history sentence, never as a current result.
    old = load(Path("outputs/run_final/metrics.json"))
    out["superseded_run_final"] = {"_note": "SUPERSEDED: pre-correction run, kept for the correction history only; not a current result",
                                   "_source": "outputs/run_final/metrics.json",
                                   "A_combined_logreg_ba": old["A_combined_logreg"]["balanced_accuracy"]}

    def clean(o):
        # Undefined statistics (e.g. a z-score whose null variance is zero) become null;
        # strict JSON is then enforced with allow_nan=False.
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (float, np.floating)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, np.integer):
            return int(o)
        return o

    path = run / "paper_results.json"
    path.write_text(json.dumps(clean(out), indent=2, allow_nan=False), encoding="utf-8")
    print(f"Paper results -> {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    main(ap.parse_args().config)
