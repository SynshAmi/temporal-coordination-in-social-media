"""
claim_evidence_audit.py
-----------------------
Builds reports/audit/claim_evidence.md: every headline claim of the paper and
website, the value(s) behind it, the key in <run_dir>/paper_results.json, the
source artifact, and whether the value appears verbatim in the built paper PDF.

The website reads the same paper_results.json unchanged (enforced by
tests/test_frontend_payload.py), so a claim that resolves here is the value the
website shows.

Usage: python src/claim_evidence_audit.py [--config configs/v2_coreness_fix.yaml]
"""

import sys
import json
import re
import argparse
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")

PDF = Path("reports/LEN_Small_Measurement_Validity_Audit_Research_Paper.pdf")
OUT = Path("reports/audit/claim_evidence.md")


# Formatting identical to reports/paper/paper_content.js
def f3(v): return f"{v:.3f}".replace("-", "−")
def f2(v): return f"{v:.2f}".replace("-", "−")
def pct(v): return f"{100 * v:.1f}"
def sg(v): return "0.000" if abs(v) < 0.0005 else ("+" if v > 0 else "−") + f"{abs(v):.3f}"
def ci(a): return f"[{sg(a[0])}, {sg(a[1])}]"
def ciu(a): return f"[{f3(a[0])}, {f3(a[1])}]"


def get(R, path):
    o = R
    for k in path.split("."):
        o = o[k]
    return o


def claims(R):
    """(claim, [(key, printed form)], source artifact, where shown)"""
    S1, LC = "study1.performance.logreg", "study1.confirmatory.logreg"
    S2C = "study2.contrasts.budget_specific_K{}"
    S2R = "study2.results.budget_specific_K{}.conditions"
    g = lambda p: get(R, p)
    ens = max(abs(g(S2C.format(k) + ".ensemble_vs_single_combined.ba.delta")) for k in (250, 500, 1000))
    return [
        ("Archive has 104 JSON files; 1 SHA-256 duplicate removed; 103 canonical events (52 campaign / 51 comparison)",
         [("dataset.archive_json_files", str(g("dataset.archive_json_files"))), ("dataset.n_events", str(g("dataset.n_events"))),
          ("dataset.n_campaign", str(g("dataset.n_campaign"))), ("dataset.n_comparison", str(g("dataset.n_comparison")))],
         "data/manifests/manifest.parquet, duplicate_files.json", "Paper §III, Table I; website Overview, Study Design, Methods §1"),
        ("Official LEN-Small release is 100 graphs (51/49); archive differs and the reason is unknown",
         [("dataset.official_len_small.n_graphs", "100 graphs"), ("dataset.official_len_small.n_campaign", "51 campaign")],
         "LEN paper (ICWSM 2025), Table 3 caption", "Paper abstract, §III; website Overview, navbar, Methods §1"),
        ("Signed SMD of log node count (campaign − comparison) is −2.24",
         [("dataset.smd_log_nodes_full_cohort", f2(g("dataset.smd_log_nodes_full_cohort")))],
         "data/manifests/matching_diagnostics.json", "Paper §III; website Fig. 1"),
        ("Counts-only LR (M0) reaches BA 0.884",
         [(f"{S1}.M0.balanced_accuracy", f3(g(f"{S1}.M0.balanced_accuracy")))],
         "outputs/run_v2/study1/oof_predictions.parquet", "Paper abstract, §V-A, Table II; website Overview, Fig. 2"),
        ("Node count alone reaches BA 0.874",
         [("run_v2_metrics.B0a_log_node_logreg.balanced_accuracy", f3(g("run_v2_metrics.B0a_log_node_logreg.balanced_accuracy")))],
         "outputs/run_v2/metrics.json", "Paper §V-A"),
        ("All features (M4): BA 0.893, log loss 0.216, AUC 0.971 vs count model log loss 0.326, AUC 0.932",
         [(f"{S1}.M4.balanced_accuracy", f3(g(f"{S1}.M4.balanced_accuracy"))), (f"{S1}.M4.log_loss", f3(g(f"{S1}.M4.log_loss"))),
          (f"{S1}.M4.roc_auc_ll_fit", f3(g(f"{S1}.M4.roc_auc_ll_fit"))), (f"{S1}.M0q.log_loss", f3(g(f"{S1}.M0q.log_loss")))],
         "outputs/run_v2/study1/oof_predictions.parquet", "Paper §V-A, Table II; website Overview, results table"),
        ("C1 (M4 vs M0q): no detectable BA gain",
         [(f"{LC}.C1.ba.delta_ba", sg(g(f"{LC}.C1.ba.delta_ba"))), (f"{LC}.C1.ba.delta_ba_ci", ci(g(f"{LC}.C1.ba.delta_ba_ci")))],
         "outputs/run_v2/study1/nested_results.json", "Paper abstract, §V-A, Table III, Fig. 2; website Overview, Fig. 2"),
        ("C1 improves log loss (Holm-adjusted p = 0.009)",
         [(f"{LC}.C1.log_loss.delta_logloss", sg(g(f"{LC}.C1.log_loss.delta_logloss"))),
          (f"{LC}.C1.log_loss.delta_logloss_ci", ci(g(f"{LC}.C1.log_loss.delta_logloss_ci"))),
          (f"{LC}.C1.log_loss.p_holm", f3(g(f"{LC}.C1.log_loss.p_holm")))],
         "outputs/run_v2/study1/nested_results.json", "Paper abstract, §V-A, Table III; website Overview, Fig. 2"),
        ("C1 improves AUC",
         [(f"{LC}.C1.auc_ll_fit.delta_auc", f3(g(f"{LC}.C1.auc_ll_fit.delta_auc"))),
          (f"{LC}.C1.auc_ll_fit.delta_auc_ci", ci(g(f"{LC}.C1.auc_ll_fit.delta_auc_ci")))],
         "outputs/run_v2/study1/nested_results.json", "Paper abstract, §V-A, Table III; website Fig. 2"),
        ("C2 (arrangement beyond degree) and C3 (content beyond counts) show no detectable BA gain",
         [(f"{LC}.C2.ba.delta_ba_ci", ci(g(f"{LC}.C2.ba.delta_ba_ci"))), (f"{LC}.C3.ba.delta_ba_ci", ci(g(f"{LC}.C3.ba.delta_ba_ci")))],
         "outputs/run_v2/study1/nested_results.json", "Paper §V-A, Table III; website Fig. 2"),
        ("Across 10 re-drawn splits, C1 ΔBA ranges +0.010 to +0.049 (stable direction, unstable magnitude)",
         [("study1.repeated_splits_lr.C1.dBA_min", sg(g("study1.repeated_splits_lr.C1.dBA_min"))),
          ("study1.repeated_splits_lr.C1.dBA_max", sg(g("study1.repeated_splits_lr.C1.dBA_max")))],
         "outputs/run_v2/study1/repeated_splits_lr.csv", "Paper §V-A; website Fig. 2 notes, Overview RQ1"),
        ("Tuning is sensitive to row order (C1 ΔBA +0.010 → +0.029 with permuted rows)",
         [("study1.row_order_sensitivity.ba:C1.delta_permuted_order", sg(g("study1.row_order_sensitivity")["ba:C1"]["delta_permuted_order"]))],
         "outputs/run_v2/verification/verification_report.json", "Paper §V-A, Limitations; website Methods §3"),
        ("HGBT is secondary: its count model is weak; vs LR M0q, HGBT M4 ΔBA is inconclusive",
         [("study1.performance.hgbt.M0q.balanced_accuracy", f3(g("study1.performance.hgbt.M0q.balanced_accuracy"))),
          ("study1.hgbt_vs_best_count_baseline.HGBT_M4_vs_LR_M0q_ba.delta_ba_ci", ci(g("study1.hgbt_vs_best_count_baseline.HGBT_M4_vs_LR_M0q_ba.delta_ba_ci")))],
         "outputs/run_v2/study1/oof_predictions.parquet", "Paper §V-A; website results table notes"),
        ("Arrangement features did not outperform degree-preserving rewired counterparts",
         [("null_model.M2_real_ba", f3(g("null_model.M2_real_ba"))), ("null_model.M2_null_ba_mean", f3(g("null_model.M2_null_ba_mean"))),
          ("null_model.real_minus_null_ba.delta_ba_ci", ci(g("null_model.real_minus_null_ba.delta_ba_ci")))],
         "outputs/run_v2/study1/null_results.json", "Paper abstract, §V-B, Table IV; website Overview, Methods §4"),
        ("Rewiring mixes incompletely (median unmoved non-loop edges)",
         [("null_model.frac_edges_unchanged_quantiles[2]", f2(g("null_model.frac_edges_unchanged_quantiles")[2]))],
         "outputs/run_v2/study1/null_results.json; verification_report.json", "Paper §V-B, Table IV, Limitations; website Overview limitations"),
        ("Exploratory matching: 16 pairs, |SMD| 2.24 → 0.10; counts near chance (median 0.531), content above chance (median 0.781)",
         [("matching.primary_pairs", str(g("matching.primary_pairs"))), ("matching.node_only.ba.M0.median", f3(g("matching.node_only.ba.M0.median"))),
          ("matching.node_only.ba.M3.median", f3(g("matching.node_only.ba.M3.median")))],
         "outputs/run_v2/study1/matching_sensitivity.json", "Paper §IV-C, §V-C, Table V; website Fig. 3"),
        ("Single views stay predictive through N_K alone (KK BA at K = 250 / 500 / 1000)",
         [(S2R.format(k) + ".KK|NK.single_view_ba_mean", f3(g(S2R.format(k))["KK|NK"]["single_view_ba_mean"])) for k in (250, 500, 1000)],
         "outputs/run_v2/study2/results.json", "Paper §V-D, Table VI, Fig. 3; website Overview RQ2, Fig. 4"),
        ("Training on views vs frozen transfer, same structural features, K = 250: +0.254 [0.162, 0.348]",
         [(S2C.format(250) + ".retrain_effect_struct6.ba.delta", f3(g(S2C.format(250) + ".retrain_effect_struct6.ba.delta"))),
          (S2C.format(250) + ".retrain_effect_struct6.ba.ci", ciu(g(S2C.format(250) + ".retrain_effect_struct6.ba.ci")))],
         "outputs/run_v2/study2/results.json", "Paper §V-D, Table VII; website Overview, Fig. 4, Methods §4"),
        ("Frozen transfer loses BA at K = 250 relative to full graphs",
         [(S2C.format(250) + ".transfer_loss_struct6.ba.delta", f3(-g(S2C.format(250) + ".transfer_loss_struct6.ba.delta")))],
         "outputs/run_v2/study2/results.json", "Paper §V-D, Table VII"),
        ("Ensembling 10 views changes BA by at most 0.004",
         [("study2.contrasts.*.ensemble_vs_single_combined.ba.delta (max |Δ|)", f3(ens))],
         "outputs/run_v2/study2/results.json", "Paper §V-D; website Overview RQ2, Fig. 4 notes"),
        ("E[N_K] matches observed N_K within 3.5% at K = 250; label AUC 0.965 vs 0.934 for log node count",
         [("study2.mechanism.K250.max_abs_rel_error_expected_vs_observed", pct(g("study2.mechanism.K250.max_abs_rel_error_expected_vs_observed")) + "%"),
          ("study2.mechanism.K250.auc_expectedNK_label", f3(g("study2.mechanism.K250.auc_expectedNK_label")))],
         "outputs/run_v2/study2/results.json", "Paper §V-E; website Explorer scope note"),
        ("Node count and mean degree explain 93.0% of E[N_K] variation at K = 250; Gini adds nothing",
         [("study2.mechanism_r2_K250.log N + log mean degree", pct(g("study2.mechanism_r2_K250")["log N + log mean degree"]) + "%"),
          ("study2.mechanism_r2_K250.size + degree concentration", pct(g("study2.mechanism_r2_K250")["size + degree concentration"]) + "%")],
         "outputs/run_v2/verification/verification_report.json", "Paper §V-E, Fig. 4; website Overview RQ2, Explorer"),
        ("K = 2000 is infeasible: only 4 campaign events have ≥ 2,000 edges",
         [("eligibility.2000.campaign_eligible", str(g("eligibility")["2000"]["campaign_eligible"]) + " campaign events")],
         "data/manifests/edge_budget_eligibility.json", "Paper §IV-E; website Fig. 4, Methods §4"),
        ("Independent verification passes every check",
         [("verification.n_pass / n_checks", f"{g('verification.n_pass')}/{g('verification.n_checks')}")],
         "outputs/run_v2/verification/verification_report.json", "Paper §VIII; website hero, footer, Methods"),
        ("Correction history: combined-model BA 0.923 (superseded run) → 0.894 (corrected run)",
         [("superseded_run_final.A_combined_logreg_ba", f3(g("superseded_run_final.A_combined_logreg_ba"))),
          ("run_v2_metrics.A_combined_logreg.balanced_accuracy", f3(g("run_v2_metrics.A_combined_logreg.balanced_accuracy")))],
         "outputs/run_final/metrics.json (archived); outputs/run_v2/metrics.json", "Paper §VIII; website Methods §5"),
    ]


def pdf_text(pdf=PDF):
    from pypdf import PdfReader
    return re.sub(r"\s+", " ", " ".join(p.extract_text() for p in PdfReader(pdf).pages))


def check(R, text):
    """[(claim, values, source, shown_in, found_flags)] for every headline claim."""
    # Word may break a line after "[" or ","; compare with whitespace removed as a fallback
    squeezed = text.replace(" ", "")
    return [(claim, vals, src, where, [(v in text) or (v.replace(" ", "") in squeezed) for _, v in vals])
            for claim, vals, src, where in claims(R)]


def main(config_path):
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    R = json.loads((Path(cfg["output"]["run_dir"]) / "paper_results.json").read_text(encoding="utf-8"))

    lines = ["# Claim-to-Evidence Audit", "",
             f"Generated by `src/claim_evidence_audit.py` from `{R['source_run']}/paper_results.json`. "
             "Each value is printed exactly as the paper formats it and searched for in the built PDF "
             f"(`{PDF.as_posix()}`). The website embeds the same results file unchanged "
             "(`tests/test_frontend_payload.py`).", "",
             "| # | Claim | Value(s) as printed | Key in paper_results.json | Source artifact | Shown in | In PDF |",
             "|---|---|---|---|---|---|---|"]
    missing = 0
    for i, (claim, vals, src, where, found) in enumerate(check(R, pdf_text()), 1):
        missing += not all(found)
        lines.append(f"| {i} | {claim} | " + "<br>".join(f"`{v}`" for _, v in vals) + " | "
                     + "<br>".join(f"`{k}`" for k, _ in vals) + f" | {src} | {where} | "
                     + ("yes" if all(found) else "**check**: " + ", ".join(v for (_, v), ok in zip(vals, found) if not ok)) + " |")
    lines += ["", f"{len(lines) - 6} claims; {missing} with a value not found verbatim in the PDF."]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{OUT}: {len(lines) - 8} claims, {missing} not found verbatim")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    main(ap.parse_args().config)
