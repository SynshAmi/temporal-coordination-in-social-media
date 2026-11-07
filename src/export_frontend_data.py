"""
export_frontend_data.py
-----------------------
Exports the website payload, frontend/public/data/research_data.json, from the
corrected run selected by the config (default: configs/v2_coreness_fix.yaml ->
outputs/run_v2).

All result values come from <run_dir>/paper_results.json, the revision
supplement (output.revision_supplement) and the audit results
(output.audit_results), the same files the paper is built from, so the
website and the paper cannot disagree. Run src/export_paper_results.py,
src/revision_supplement.py and src/export_audit_results.py first.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import balanced_accuracy_score

sys.stdout.reconfigure(encoding="utf-8")

LEVEL_TEXT = {
    "M0": "Counts: log node and edge count",
    "M0q": "Counts with squared/interaction terms (nonlinear count control)",
    "M1": "M0q + in/out-degree Gini",
    "M2": "M1 + reciprocity, largest WCC, coreness (arrangement)",
    "M3": "M0q + content (duplicates, text concentration, length dispersion)",
    "M4": "M2 + content (all features)",
    "M4d": "M4 + density (diagnostic; density is fixed by the counts)",
}
FS_TEXT = {
    "NK": "Sampled endpoint count N_K only",
    "struct7": "Structure incl. density (7)",
    "struct6": "Structure without density (6)",
    "NK_struct6": "N_K + structure (6)",
    "content": "Content (3)",
    "combined": "N_K + structure + content",
}
COND_TEXT = {"FF": "Full graph -> full graph", "FK": "Full graph -> single view (frozen)", "KK": "Single view -> single view (retrained)"}


PAPER_PDF = Path(__file__).resolve().parents[1] / "paper" / "Finding_Signal_in_Network_Simplicity.pdf"


def paper_pages():
    """Page count of the built paper, for the website's download label (None if the PDF is missing)."""
    if not PAPER_PDF.exists():
        return None
    from pypdf import PdfReader
    return len(PdfReader(PAPER_PDF).pages)


def ba_ci(y, p, n_boot=2000, seed=7):
    rng = np.random.default_rng(seed)
    yhat = (p >= 0.5).astype(int)
    vals = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        vals.append(balanced_accuracy_score(y[i], yhat[i]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def export_data(config_path: str, output_path: Path) -> None:
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    run = Path(cfg["output"]["run_dir"])
    manifest = pd.read_parquet(Path(cfg["data"]["manifests_dir"]) / "manifest.parquet")
    paper_path = run / "paper_results.json"
    if not paper_path.exists():
        raise FileNotFoundError(f"{paper_path} missing; run src/export_paper_results.py first.")
    R = json.loads(paper_path.read_text(encoding="utf-8"))
    sup_path = Path(cfg["output"]["revision_supplement"])
    if not sup_path.exists():
        raise FileNotFoundError(f"{sup_path} missing; run src/revision_supplement.py first.")
    S = json.loads(sup_path.read_text(encoding="utf-8"))
    aud_path = Path(cfg["output"]["audit_results"])
    if not aud_path.exists():
        raise FileNotFoundError(f"{aud_path} missing; run src/export_audit_results.py first.")
    A = json.loads(aud_path.read_text(encoding="utf-8"))
    oof = pd.read_parquet(run / "study1" / "oof_predictions.parquet")

    def summarize(arr):
        return {"count": int(len(arr)), "mean": round(float(np.mean(arr)), 1), "median": round(float(np.median(arr)), 1),
                "p25": round(float(np.percentile(arr, 25)), 1), "p75": round(float(np.percentile(arr, 75)), 1),
                "min": int(np.min(arr)), "max": int(np.max(arr))}

    cohort_stats = {f"{cls}_{col.split('_')[1]}": summarize(manifest.loc[manifest.label == lab, col].values)
                    for cls, lab in (("campaign", 1), ("comparison", 0)) for col in ("n_nodes", "n_edges")}
    event_points = [{"event_id": r.event_id, "label": int(r.label), "label_str": r.label_str,
                     "n_nodes": int(r.n_nodes), "n_edges": int(r.n_edges),
                     "log_nodes": round(float(np.log1p(r.n_nodes)), 3), "log_edges": round(float(np.log1p(r.n_edges)), 3)}
                    for r in manifest.itertuples()]

    # Benchmark-table rows: Study 1 levels and Study 2 conditions
    rows = []
    X = R["study1"]["hgbt_vs_best_count_baseline"]["HGBT_M4_vs_LR_M0q_ba"]
    hgbt_note = (f" HGBT is secondary: its own count model is weak (BA {R['study1']['performance']['hgbt']['M0q']['balanced_accuracy']:.3f}); "
                 f"against the best count model (LR M0q) HGBT M4 changes BA by {X['delta_ba']:+.3f} "
                 f"[{X['delta_ba_ci'][0]:+.3f}, {X['delta_ba_ci'][1]:+.3f}].")
    for model, mlabel in (("logreg", "LogReg"), ("hgbt", "HGBT")):
        perf = R["study1"]["performance"][model]
        for lv, txt in LEVEL_TEXT.items():
            d = oof[(oof.model == model) & (oof.objective == "ba") & (oof.experiment == lv)]
            lo, hi = ba_ci(d.label.values.astype(int), d.prob_campaign.values)
            rows.append({"experiment_id": f"S1_{mlabel}_{lv}", "study": "Study 1", "category": "Study 1: full cohort",
                         "feature_group": txt, "model": mlabel, "balanced_accuracy": perf[lv]["balanced_accuracy"],
                         "ba_ci_lower": lo, "ba_ci_upper": hi, "interval_kind": "95% CI",
                         "log_loss": perf[lv]["log_loss"], "roc_auc": perf[lv]["roc_auc_ll_fit"], "n_events": len(d),
                         "note": "BA from BA-tuned fits; log loss and AUC from log-loss-tuned fits (same outer folds)."
                                 + (hgbt_note if model == "hgbt" else "")})
    for K in cfg["edge_budgets"]["K_values"]:
        res = R["study2"]["results"][f"budget_specific_K{K}"]
        for key, s in res["conditions"].items():
            c, fs = key.split("|")
            full = c == "FF"  # full graphs: no sampling, so no seed range or ensemble
            rows.append({"experiment_id": f"S2_K{K}_{c}_{fs}", "study": "Study 2", "category": f"Study 2: K = {K}",
                         "feature_group": f"{COND_TEXT[c]}; {FS_TEXT[fs]}", "model": "LogReg",
                         "balanced_accuracy": s["single_view_ba_mean"],
                         "ba_ci_lower": None if full else s["single_view_ba_min"],
                         "ba_ci_upper": None if full else s["single_view_ba_max"],
                         "interval_kind": "full graphs, no sampling" if full else "seed range",
                         "ensemble_ba": None if full else s["ensemble_ba"], "log_loss": s["single_view_logloss_mean"],
                         "roc_auc": s["single_view_auc_mean"], "n_events": res["n_events"],
                         "note": ("Trained and evaluated on full graphs of the events eligible at this budget (reference for FK and KK)"
                                  if full else
                                  f"Single-view BA, mean over 10 sampling seeds (10-view ensemble BA {s['ensemble_ba']:.3f})")
                                 + f"; log loss and AUC from log-loss-tuned fits. Budget-specific cohort: "
                                   f"{res['n_campaign']} campaign / {res['n_comparison']} comparison events."})

    # Post-hoc token-count dispersion models B and D (stored audit outputs; A and C equal the pipeline rows)
    for K in cfg["edge_budgets"]["K_values"]:
        for model, fs in (("B", "N_K + token-count dispersion (post hoc)"), ("D", "N_K + structure (6) + token-count dispersion (post hoc)")):
            s = A["edge_limited_token_std"]["performance"][f"K{K}"]["KK"][model]
            rows.append({"experiment_id": f"S2_K{K}_KK_{model}", "study": "Study 2", "category": f"Study 2: K = {K}",
                         "feature_group": f"{COND_TEXT['KK']}; {fs}", "model": "LogReg", "balanced_accuracy": s["ba"],
                         "ba_ci_lower": s["ba_seed_min"], "ba_ci_upper": s["ba_seed_max"], "interval_kind": "seed range",
                         "ensemble_ba": None, "log_loss": s["log_loss"], "roc_auc": s["auc"], "n_events": s["n_events"],
                         "note": "Post hoc: token-count dispersion was singled out after the full-graph results were examined. "
                                 "Single-view means over 10 sampling seeds, partition 42; from the stored audit outputs."})

    payload = {
        "metadata": {
            "project_identity": "Temporal Coordination in Social Media",
            "paper_title": "Finding Signal in Network Simplicity",
            "paper_pdf": PAPER_PDF.name,
            "paper_pages": paper_pages(),
            "source_run": R["source_run"], "config": R["config"],
            "exported_at": datetime.now(timezone.utc).isoformat(),
        },
        "cohort_statistics": cohort_stats,
        "event_points": event_points,
        "paper": R,
        "revision": S,
        "audit": A,
        "experiments": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(f"Exported research data -> {output_path} ({output_path.stat().st_size:,} bytes; {len(rows)} table rows)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    ap.add_argument("--out", default=None, help="default: output.frontend_payload in the config")
    a = ap.parse_args()
    cfg_out = yaml.safe_load(open(a.config, encoding="utf-8"))["output"].get("frontend_payload", "frontend/public/data/research_data.json")
    export_data(a.config, Path(a.out or cfg_out))
