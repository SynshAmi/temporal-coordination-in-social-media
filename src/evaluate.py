"""
evaluate.py
-----------
Evaluation, bootstrap confidence intervals, visualization figures,
and checkpoint reporting for LEN-Small robustness audit.

Figures generated:
  outputs/run_final/figures/fig1_size_overlap.png
  outputs/run_final/figures/fig2_baseline_comparison.png
  outputs/run_final/figures/fig3_matched_cohort_comparison.png
  outputs/run_final/figures/fig4_edge_budget_robustness.png

Report generated:
  reports/checkpoint_report.md
"""

import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml
from sklearn.metrics import balanced_accuracy_score

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_resamples: int = 1000,
    seed: int = 7,
) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0, 0.0
    point = float(balanced_accuracy_score(y_true, y_pred))
    boot_vals = []
    for _ in range(n_resamples):
        idx = rng.choice(n, size=n, replace=True)
        try:
            boot_vals.append(balanced_accuracy_score(y_true[idx], y_pred[idx]))
        except Exception:
            pass
    if len(boot_vals) == 0:
        return point, point, point
    arr = np.array(boot_vals)
    return point, float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


CAMPAIGN_COLOR = "#d62728"   # Red
COMPARISON_COLOR = "#1f77b4" # Blue


def fig1_size_overlap(manifest: pd.DataFrame, out_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))

    n_camp = int((manifest["label"] == 1).sum())
    n_comp = int((manifest["label"] == 0).sum())

    for ax, (col, label_str) in zip(axes, [("n_nodes", "Node Count"), ("n_edges", "Edge Count")]):
        camp_vals = np.log1p(manifest[manifest["label"] == 1][col].values)
        comp_vals = np.log1p(manifest[manifest["label"] == 0][col].values)

        parts = ax.violinplot(
            [comp_vals, camp_vals],
            positions=[1, 2],
            showmedians=True,
            showextrema=True,
        )
        parts["bodies"][0].set_facecolor(COMPARISON_COLOR)
        parts["bodies"][0].set_alpha(0.6)
        parts["bodies"][1].set_facecolor(CAMPAIGN_COLOR)
        parts["bodies"][1].set_alpha(0.6)

        rng = np.random.default_rng(42)
        for pos, vals, color in [(1, comp_vals, COMPARISON_COLOR), (2, camp_vals, CAMPAIGN_COLOR)]:
            jitter = rng.uniform(-0.06, 0.06, size=len(vals))
            ax.scatter(pos + jitter, vals, alpha=0.6, s=24, color=color, zorder=3)

        ax.set_xticks([1, 2])
        ax.set_xticklabels([f"Comparison\n(n={n_comp})", f"Campaign\n(n={n_camp})"], fontsize=10)
        ax.set_ylabel(f"log(1 + {label_str})", fontsize=10)
        ax.set_title(f"Distribution of log {label_str}", fontsize=11, fontweight="bold")
        ax.grid(axis="y", linestyle=":", alpha=0.6)

    fig.suptitle("Base-grid diagnostic A: event scale distributions by class", fontsize=13, fontweight="bold")
    plt.tight_layout()
    out_path = out_dir / "fig1_size_overlap.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Diagnostic 1 saved -> {out_path}")


def fig2_baseline_comparison(metrics: dict, out_dir: Path) -> None:
    relevant = {
        "Size (log N)": "B0a_log_node_logreg",
        "Size (log N+E)": "B0b_log_node_edge_logreg",
        "Structure": "A_structure_logreg",
        "Content": "A_content_logreg",
        "Combined": "A_combined_logreg",
    }
    labels, values, colors = [], [], []
    for name, key in relevant.items():
        if key in metrics:
            labels.append(name)
            val = metrics[key]["balanced_accuracy"]
            values.append(val)
            colors.append("#ff7f0e" if "Size" in name else "#2ca02c")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(labels, values, color=colors, alpha=0.85, edgecolor="black", linewidth=0.8, width=0.55)

    ax.axhline(0.5, linestyle="--", color="gray", linewidth=1.2, label="Chance Level (0.50)")
    ax.set_ylim(0.4, 1.05)
    ax.set_ylabel("Balanced Accuracy (5-Fold CV)", fontsize=10)
    ax.set_title("Base-grid diagnostic B: feature groups, full cohort (LR)", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.015,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    out_path = out_dir / "fig2_baseline_comparison.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Diagnostic 2 saved -> {out_path}")


def fig3_matched_cohort_comparison(metrics: dict, out_dir: Path) -> None:
    groups = ["scale", "structure", "content", "combined"]
    model = "logreg"
    full_vals = [metrics.get(f"A_{g}_{model}", {}).get("balanced_accuracy", np.nan) for g in groups]
    matched_vals = [metrics.get(f"C_matched_{g}_{model}", {}).get("balanced_accuracy", np.nan) for g in groups]

    x = np.arange(len(groups))
    w = 0.35

    fig, ax = plt.subplots(figsize=(9, 4.5))
    rects1 = ax.bar(x - w/2, full_vals, w, label="Full Cohort (N=103)", color="#4a7bb0", edgecolor="black", alpha=0.9)
    rects2 = ax.bar(x + w/2, matched_vals, w, label="Size-Matched Cohort", color="#e07a5f", edgecolor="black", alpha=0.9)

    ax.axhline(0.5, linestyle="--", color="gray", linewidth=1.2, label="Chance (0.50)")
    ax.set_xticks(x)
    ax.set_xticklabels([g.capitalize() for g in groups], fontsize=10)
    ax.set_ylim(0.4, 1.05)
    ax.set_ylabel("Balanced Accuracy (5-Fold CV)", fontsize=10)
    ax.set_title("Base-grid diagnostic C: primary matching ordering only (exploratory)", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    for rect in list(rects1) + list(rects2):
        h = rect.get_height()
        if not np.isnan(h):
            ax.text(rect.get_x() + rect.get_width() / 2, h + 0.012, f"{h:.3f}",
                    ha="center", va="bottom", fontsize=8.5)

    plt.tight_layout()
    out_path = out_dir / "fig3_matched_cohort_comparison.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Diagnostic 3 saved -> {out_path}")


def fig4_edge_budget_robustness(metrics: dict, eligibility: dict, out_dir: Path) -> None:
    K_values = sorted([int(k) for k in eligibility.keys() if int(k) in [250, 500, 1000]])
    d2_vals = [metrics.get(f"D2_K{K}", {}).get("balanced_accuracy", np.nan) for K in K_values]
    d1_vals = [metrics.get(f"D1_K{K}_frozen", {}).get("balanced_accuracy", np.nan) for K in K_values]
    n_eligible = [eligibility[str(K)]["total_eligible"] for K in K_values]

    fig, ax1 = plt.subplots(figsize=(8.5, 4.5))

    ax1.plot(K_values, d2_vals, "o-", color="#d62728", linewidth=2.2, markersize=8, label="D2: retrained on sampled views (all 12 features)")
    if any(not np.isnan(v) for v in d1_vals):
        ax1.plot(K_values, d1_vals, "s--", color="#2ca02c", linewidth=2.0, markersize=7, label="D1: frozen full-graph model (7 structural features)")

    ax1.axhline(0.5, linestyle="--", color="gray", linewidth=1.2, label="Chance Level")
    ax1.set_xlabel("Retained Edge Budget (K)", fontsize=10)
    ax1.set_ylabel("Balanced Accuracy", fontsize=10)
    ax1.set_ylim(0.4, 1.05)
    ax1.set_title("Base-grid diagnostic D: edge budgets (feature sets differ; not a retraining estimate)", fontsize=11, fontweight="bold")
    ax1.legend(loc="lower left")
    ax1.grid(axis="y", linestyle=":", alpha=0.6)

    ax2 = ax1.twinx()
    ax2.bar(K_values, n_eligible, width=60, alpha=0.2, color="steelblue", label="Eligible Events")
    ax2.set_ylabel("Eligible Events (>= K edges)", color="steelblue", fontsize=10)
    ax2.tick_params(axis="y", labelcolor="steelblue")
    ax2.set_ylim(0, 120)
    ax2.legend(loc="upper right")

    for K, ba in zip(K_values, d2_vals):
        if not np.isnan(ba):
            ax1.annotate(f"{ba:.3f}", xy=(K, ba), xytext=(0, 8),
                         textcoords="offset points", ha="center", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    out_path = out_dir / "fig4_edge_budget_robustness.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Diagnostic 4 saved -> {out_path}")


def write_checkpoint_report(metrics: dict, manifest: pd.DataFrame, config: dict) -> None:
    report_path = Path(config["output"].get("report_path", "reports/checkpoint_report.md"))
    report_path.parent.mkdir(parents=True, exist_ok=True)

    manifests_dir = Path(config["data"]["manifests_dir"])
    diag_path = manifests_dir / "matching_diagnostics.json"
    diag = {}
    if diag_path.exists():
        with open(diag_path, "r", encoding="utf-8") as f:
            diag = json.load(f)

    elig_path = manifests_dir / "edge_budget_eligibility.json"
    elig = {}
    if elig_path.exists():
        with open(elig_path, "r", encoding="utf-8") as f:
            elig = json.load(f)

    n_total = len(manifest)
    n_camp = (manifest["label"] == 1).sum()
    n_comp = (manifest["label"] == 0).sum()

    lines = [
        "# Checkpoint Report: Base Experiment Grid (diagnostic)",
        "",
        "> **Read this first.** This is an automatically generated summary of the pipeline's base experiment grid "
        "(stages 5-7). It is a diagnostic, not the paper's analysis. The paper's results come from Study 1 and "
        "Study 2 and are collected in `paper_results.json` in the same run directory. In particular, the edge-budget "
        "table below compares a frozen model on 7 structural features with a retrained model on all 12 features, "
        "so their difference is **not** an estimate of the effect of retraining; Study 2 makes that comparison with "
        "matched feature sets. The single-ordering size-matching table is likewise superseded by the paper's "
        "20-ordering exploratory analysis.",
        "",
        "## Cohort",
        f"- **Dataset:** analysed LEN-Small archive (`small_encoder_final.tar`); {n_total} canonical event graphs ({n_camp} campaign, {n_comp} comparison).",
        "- **Unit of analysis:** the event engagement graph; all predictions and evaluations are event-level.",
        f"- **Campaign graphs:** median node count {float(manifest[manifest['label']==1]['n_nodes'].median()):.1f}, mean {float(manifest[manifest['label']==1]['n_nodes'].mean()):.1f}.",
        f"- **Comparison graphs:** median node count {float(manifest[manifest['label']==0]['n_nodes'].median()):.1f}, mean {float(manifest[manifest['label']==0]['n_nodes'].mean()):.1f}.",
        "",
        "## 1. Full-Cohort Feature Groups (Out-of-Fold, 5-Fold CV)",
        "| Model / Feature Group | Balanced Accuracy | Macro F1 | Campaign Recall | Comparison Recall | ROC-AUC |",
        "|---|---|---|---|---|---|",
    ]

    for key, name in [
        ("B0a_log_node_logreg", "B0a: Log Node Count (LogReg)"),
        ("B0b_log_node_edge_logreg", "B0b: Log Node + Log Edge (LogReg)"),
        ("A_scale_logreg", "Scale Baseline (LogReg)"),
        ("A_structure_logreg", "Structure Group (LogReg)"),
        ("A_content_logreg", "Content Group (LogReg)"),
        ("A_combined_logreg", "Combined Group (LogReg)"),
    ]:
        m = metrics.get(key, {})
        lines.append(f"| {name} | {m.get('balanced_accuracy', 'N/A')} | {m.get('macro_f1', 'N/A')} | {m.get('campaign_recall', 'N/A')} | {m.get('comparison_recall', 'N/A')} | {m.get('roc_auc', 'N/A')} |")

    lines.extend([
        "",
        "## 2. Size Matching, Primary Ordering Only (exploratory; see the paper for the 20-ordering analysis)",
        "",
        f"- **Matching Caliper:** {diag.get('caliper_abs', 'N/A')} ({diag.get('caliper_sd_fraction', 'N/A')} SD of log node count).",
        f"- **Retained Pairs:** {diag.get('n_matched_pairs', 'N/A')} pairs ({diag.get('n_campaign_matched', 'N/A')} campaign, {diag.get('n_comparison_matched', 'N/A')} comparison; {diag.get('n_excluded', 'N/A')} excluded).",
        f"- **Balance Diagnostics (SMD):** Standardised Mean Difference dropped from **{diag.get('smd_before', 'N/A')}** before matching to **{diag.get('smd_after', 'N/A')}** after matching.",
        "",
        "| Feature Group (LogReg) | Full Cohort BA | Matched Cohort BA | Difference |",
        "|---|---|---|---|",
    ])

    for g in ["scale", "structure", "content", "combined"]:
        fa = metrics.get(f"A_{g}_logreg", {}).get("balanced_accuracy", "N/A")
        mc = metrics.get(f"C_matched_{g}_logreg", {}).get("balanced_accuracy", "N/A")
        diff = round(mc - fa, 4) if isinstance(fa, float) and isinstance(mc, float) else "N/A"
        lines.append(f"| {g.capitalize()} | {fa} | {mc} | {diff} |")

    lines.extend([
        "",
        "## 3. Edge Budgets (feature sets differ between columns; not a retraining estimate)",
        "",
        "| Edge Budget (K) | Eligible Events (Camp / Comp) | D2: retrained, 12 features | D1: frozen, 7 structural features | Feasibility Note |",
        "|---|---|---|---|---|",
    ])

    for K in [250, 500, 1000, 2000]:
        k_str = str(K)
        e_info = elig.get(k_str, {})
        n_camp = e_info.get("campaign_eligible", "N/A")
        n_comp = e_info.get("comparison_eligible", "N/A")
        d2_m = metrics.get(f"D2_K{K}", {}).get("balanced_accuracy", "N/A")
        d1_m = metrics.get(f"D1_K{K}_frozen", {}).get("balanced_accuracy", "N/A")
        feas = "Feasible (5-fold CV)" if e_info.get("feasible_for_5fold_cv") else f"Infeasible: only {n_camp} campaign events (CV folds empty)"
        lines.append(f"| K={K} | {n_camp} / {n_comp} | {d2_m} | {d1_m} | {feas} |")

    lines.extend([
        "",
        "## 4. Processing Notes",
        "1. **Ingestion:** node-link JSON graphs are streamed directly from `small_encoder_final.tar`; labels come from file-name tokens.",
        "2. **Deduplication:** one byte-identical duplicate (`#SesimiziDuyanVarM[i/ı]`, file names differing only in a dotless ı) is removed by SHA-256.",
        "3. **Embeddings:** the pretrained node and edge embedding vectors (`node_attr`, `edge_attr`) are not used.",
        "4. **Coreness convention:** core numbers are computed on the simple undirected projection with self-loops removed (an earlier version silently set coreness to zero; see the paper's correction history).",
        "5. **Frozen-model scoring:** each sampled event is scored only by the full-cohort fold model that held it out (an earlier version used a budget-specific split; see the paper's correction history).",
        "6. **K = 2000:** too few campaign events for five-fold stratified evaluation.",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Checkpoint report written -> {report_path}")


def evaluate(config: dict) -> None:
    run_dir = Path(config["output"]["run_dir"])
    figs_dir = Path(config["output"]["figures_dir"])
    figs_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = Path(config["data"]["manifests_dir"]) / "manifest.parquet"
    manifest = pd.read_parquet(manifest_path)

    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing {metrics_path}. Run train.py first.")
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    elig_path = Path(config["data"]["manifests_dir"]) / "edge_budget_eligibility.json"
    eligibility = {}
    if elig_path.exists():
        with open(elig_path, "r", encoding="utf-8") as f:
            eligibility = json.load(f)

    # Compute bootstrap confidence intervals for all experiments from predictions.parquet
    pred_path = run_dir / "predictions.parquet"
    if pred_path.exists():
        preds_df = pd.read_parquet(pred_path)
        rng_seed = config.get("evaluation", {}).get("bootstrap_seed", 7)
        n_boot = config.get("evaluation", {}).get("bootstrap_n_resamples", 1000)
        from sklearn.metrics import f1_score

        for exp_name, group in preds_df.groupby("experiment"):
            # Map experiment name to metrics key
            key_candidates = [
                exp_name,
                exp_name.replace("_retrained", ""),
                exp_name.replace("_frozen_structure", "_frozen")
            ]
            metric_key = next((k for k in key_candidates if k in metrics), None)
            if not metric_key:
                continue

            y_true = group["label"].values.astype(int)
            y_pred = group["pred_label"].values.astype(int)
            n_events = len(y_true)

            rng = np.random.default_rng(rng_seed)
            boot_ba = []
            boot_f1 = []
            for _ in range(n_boot):
                idx = rng.choice(n_events, size=n_events, replace=True)
                try:
                    boot_ba.append(balanced_accuracy_score(y_true[idx], y_pred[idx]))
                    boot_f1.append(f1_score(y_true[idx], y_pred[idx], average="macro", zero_division=0))
                except Exception:
                    pass

            if boot_ba:
                ba_lo, ba_hi = np.percentile(boot_ba, [2.5, 97.5])
                metrics[metric_key]["ba_ci_lower"] = round(float(ba_lo), 4)
                metrics[metric_key]["ba_ci_upper"] = round(float(ba_hi), 4)
            if boot_f1:
                f1_lo, f1_hi = np.percentile(boot_f1, [2.5, 97.5])
                metrics[metric_key]["f1_ci_lower"] = round(float(f1_lo), 4)
                metrics[metric_key]["f1_ci_upper"] = round(float(f1_hi), 4)

        # Write updated metrics.json with CIs
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"Updated metrics with 95% bootstrap CIs -> {metrics_path}")

        # Update tables.md with CIs
        summary_rows = []
        for exp, m in metrics.items():
            summary_rows.append({
                "experiment": exp,
                "balanced_accuracy": m.get("balanced_accuracy"),
                "ba_95ci": f"[{m.get('ba_ci_lower', '—')}, {m.get('ba_ci_upper', '—')}]",
                "macro_f1": m.get("macro_f1"),
                "f1_95ci": f"[{m.get('f1_ci_lower', '—')}, {m.get('f1_ci_upper', '—')}]",
                "campaign_recall": m.get("campaign_recall"),
                "comparison_recall": m.get("comparison_recall"),
                "roc_auc": m.get("roc_auc"),
                "n_events": m.get("n_events"),
            })
        summary_df = pd.DataFrame(summary_rows).sort_values("experiment")
        tables_path = run_dir / "tables.md"

        def df_to_markdown(df: pd.DataFrame) -> str:
            headers = [str(c) for c in df.columns]
            lines = ["| " + " | ".join(headers) + " |"]
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for _, row in df.iterrows():
                row_vals = [str(row[c]) if pd.notna(row[c]) else "" for c in df.columns]
                lines.append("| " + " | ".join(row_vals) + " |")
            return "\n".join(lines)

        with open(tables_path, "w", encoding="utf-8") as f:
            f.write("# Base Experiment Grid: Results Summary (diagnostic; the paper's results are in paper_results.json)\n\n")
            f.write(df_to_markdown(summary_df))
            f.write("\n\n*All numbers are out-of-fold estimates evaluated via stratified 5-fold cross-validation with 95% bootstrap confidence intervals (1,000 resamples).*\n")
        print(f"Updated summary table with CIs -> {tables_path}")

    print("Generating figures...")
    fig1_size_overlap(manifest, figs_dir)
    fig2_baseline_comparison(metrics, figs_dir)
    fig3_matched_cohort_comparison(metrics, figs_dir)
    fig4_edge_budget_robustness(metrics, eligibility, figs_dir)

    write_checkpoint_report(metrics, manifest, config)
    print("\nEvaluation and reporting complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate outputs and generate figures")
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    evaluate(cfg)
