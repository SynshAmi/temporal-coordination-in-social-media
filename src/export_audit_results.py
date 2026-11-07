"""
export_audit_results.py
-----------------------
Collects the audit-derived values that the paper and the website report into one
file, <output.audit_results> (default outputs/research_audit/audit_results.json).

The values come from the stored outputs of the robustness audit in
research_audit/ (20 outer partitions, the missing-text exclusion, the post-hoc
token-count dispersion analyses, text retention) and from the pipeline's own
Study 2 contrasts. Nothing is refitted or resampled here: every number is read
from an existing artifact, and each block records its source file.

The only arithmetic is presentation-level:
- Holm adjustment of stored bootstrap p-values across the three edge budgets,
  for the pipeline's Study 2 contrasts (the audit used the same family for its
  own contrasts; this script checks that it reproduces those values exactly);
- counts and ranges over stored rows (for example, how many of six stored
  exclusion contrasts changed by at most a given amount).

Usage: python src/export_audit_results.py [--config CONFIG] [--out PATH]
"""

import sys
import json
import math
import argparse
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "research_audit" / "outputs"
DIAG = ROOT / "research_audit" / "final_diagnostics" / "outputs"
READY = ROOT / "research_audit" / "manuscript_readiness"
KS = (250, 500, 1000)


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def holm(ps):
    """Holm step-down adjustment (monotone, capped at 1), in input order."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = running
    return out


def pick(row, keys):
    return {k: row[k] for k in keys if k in row and not (isinstance(row[k], float) and math.isnan(row[k]))}


CONTRAST_KEYS = ["dLL", "dLL_ci", "p_LL", "dAUC", "dAUC_ci", "p_AUC", "dBA", "dBA_ci", "p_BA",
                 "repeats_favouring_A_LL", "repeats_favouring_A_AUC", "repeats_favouring_A_BA", "n_repeats",
                 "repeat_dLL_min", "repeat_dLL_max", "repeat_dLL_sd", "repeat_dBA_min", "repeat_dBA_max",
                 "events_improved_LL", "n_events", "dLL_event_sd", "p_LL_holm"]


def study1(out):
    src = AUD / "s02_results.json"
    s02 = load(src)
    rows = {(r["subset"], r["contrast"]): r for r in s02["contrasts"]}
    want = {
        "C1": ("all", "C1: M4 - M0q"),
        "C2": ("all", "C2: M2 - M1 (arrangement)"),
        "C3": ("all", "C3: M3 - M0q (content beyond counts)"),
        "E1": ("all", "E1: M1 - M0q (degree Gini)"),
        "M2_minus_M0q": ("all", "M2 - M0q (structure beyond counts)"),
        "E2": ("all", "E2: M4 - M3 (structure beyond counts+content)"),
        "E3": ("all", "E3: M4 - M2 (content beyond counts+structure)"),
        "arrangement_given_content_degree": ("all", "M4 - M3+degree (arrangement given content+degree)"),
        "degree_given_content_arrangement": ("all", "M4 - M3+arrangement (degree given content+arrangement)"),
        "M4_minus_spline": ("all", "M4 - S (spline counts)"),
        "M4_minus_cubic": ("all", "M4 - P3 (cubic counts)"),
        "M4_minus_QDA": ("all", "M4 - QDA (counts)"),
        "C1_text101": ("text101", "C1: M4 - M0q"),
        "C3_text101": ("text101", "C3: M3 - M0q"),
        "E3_text101": ("text101", "E3: M4 - M2"),
        "C1_grouped": ("grouped", "C1: M4 - M0q"),
        "tokenstd_beyond_counts": ("all", "M0q+lensd - M0q"),
    }
    missing = [k for k, v in want.items() if v not in rows]
    if missing:
        raise SystemExit(f"s02_results.json lacks contrasts: {missing}")
    C = {k: pick(rows[v], CONTRAST_KEYS) for k, v in want.items()}
    s04 = load(AUD / "s04_posthoc_lensd.json")
    C["M4_minus_counts_tokenstd"] = pick(s04["M4 - M0q+lensd"], CONTRAST_KEYS)
    # the single-feature row must agree between the two audit files
    assert abs(s04["M0q+lensd - M0q"]["dLL"] - C["tokenstd_beyond_counts"]["dLL"]) < 1e-12

    perf = {}
    import csv
    with open(AUD / "s02_performance.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["subset"] == "all" and r["model"] in ("M0", "M0q", "M1", "M2", "M3", "M4", "M0q+lensd"):
                perf[r["model"]] = {k: float(r[k]) for k in ("LL", "AUC", "BA") if r[k] != ""}

    s03 = load(AUD / "s03_results.json")
    conc, loeo = s03["concentration"], s03["refit_loeo"]
    out["study1_20_partitions"] = {
        "_source": [rel(src), rel(AUD / "s04_posthoc_lensd.json"), rel(AUD / "s02_performance.csv"), rel(AUD / "s03_results.json")],
        "_note": "Outer partitions with seeds 42 and 1-19 on the same 103 events; out-of-fold predictions averaged over "
                 "partitions, then an event-level paired bootstrap (2,000 resamples). Seeds 42 and 1-9 reproduce the "
                 "pipeline's stored repeated splits (max |diff| < 1e-14). Unadjusted p unless p_LL_holm is given; "
                 "p_LL_holm is over the audit's 7-contrast family listed in holm_family.",
        "seeds": s02["seeds"],
        "n_partitions": len(s02["seeds"]),
        "reproduction_max_abs_diff_ll": max(v["max_abs_diff_ll"] for v in s02["reproduction_check_vs_stored_repeated_splits"].values()),
        "holm_family": s02["holm_family"],
        "n_events_text101": s02["text101_events"],
        "performance": perf,
        "contrasts": C,
        "concentration": {"share_from_top10_favouring_M4": conc["share_from_top10_favouring_M4"],
                          "events_improved": conc["events_improved"], "events_worse": conc["events_worse"],
                          "refit_leave_one_event_out_dLL_range": loeo["refit_dLL_range"],
                          "refit_leave_one_event_out_n_partitions": 10,
                          "events_whose_removal_makes_dLL_nonnegative": len(loeo["events_whose_removal_makes_dLL_nonnegative"])},
    }


def text_retention(out):
    s01 = load(AUD / "s01_content_verification.json")
    t01 = load(READY / "t01_summary.json")
    share = s01["usable_text_share_by_label"]
    out["text_retention"] = {
        "_source": [rel(AUD / "s01_content_verification.json"), rel(READY / "t01_summary.json")],
        "_note": "Raw-archive recomputation. A text is usable if it is a non-null string that is non-empty after cleaning.",
        "links_total": s01["links_total"], "links_text_null": s01["links_text_null"],
        "null_share": s01["links_text_null"] / s01["links_total"],
        "usable_share_mean_campaign": share["1"]["mean"], "usable_share_mean_comparison": share["0"]["mean"],
        "usable_share_median_campaign": share["1"]["median"], "usable_share_median_comparison": share["0"]["median"],
        "events_without_usable_text": len(s01["events_without_usable_text"]),
        "events_usable_share_below_0_2_campaign": s01["events_usable_share_below_0.2"]["1"],
        "events_usable_share_below_0_2_comparison": s01["events_usable_share_below_0.2"]["0"],
        "content_max_abs_diff_vs_pipeline": max(s01["content_max_abs_diff_vs_pipeline"].values()),
        "token_std_raw_check": t01,
    }


def edge_limited(out, R):
    v02 = load(AUD / "v02_results.json")
    perf = {}
    for r in v02["performance"]:
        perf.setdefault(f"K{r['K']}", {}).setdefault(r["condition"], {})[r["model"]] = pick(
            r, ["n_events", "n_campaign", "log_loss", "log_loss_seed_min", "log_loss_seed_max", "auc", "auc_seed_min",
                "auc_seed_max", "ba", "ba_seed_min", "ba_seed_max"])
    # Models A and C are the pipeline's KK|NK and KK|NK_struct6; check agreement with paper_results.json
    for k in KS:
        c = R["study2"]["results"][f"budget_specific_K{k}"]["conditions"]
        for model, key in (("A", "NK"), ("C", "NK_struct6")):
            for cond in ("KK", "FF"):
                a, b = perf[f"K{k}"][cond][model], c[f"{cond}|{key}"]
                assert abs(a["ba"] - b["single_view_ba_mean"]) < 1e-9, (k, cond, model)
                assert abs(a["log_loss"] - b["single_view_logloss_mean"]) < 1e-9, (k, cond, model)
                assert abs(a["auc"] - b["single_view_auc_mean"]) < 1e-9, (k, cond, model)

    con = {}
    for r in v02["contrasts"]:
        an = "primary" if r["analysis"].startswith("primary") else "partitions10"
        con.setdefault(an, {}).setdefault(r["condition"], {}).setdefault(r["contrast"].replace(" ", ""), {})[f"K{r['K']}"] = pick(
            r, CONTRAST_KEYS + ["p_LL_holm_across_K", "p_AUC_holm_across_K", "p_BA_holm_across_K"])
    # Check our Holm implementation against the audit's stored Holm-across-K values
    for an in con.values():
        for cond in an.values():
            for c in cond.values():
                for m in ("LL", "AUC", "BA"):
                    ps = [c[f"K{k}"][f"p_{m}"] for k in KS]
                    for k, h in zip(KS, holm(ps)):
                        assert abs(h - c[f"K{k}"][f"p_{m}_holm_across_K"]) < 1e-9, ("holm mismatch", m, k)
    # Six-test family: both dispersion contrasts (B - A, D - C) at the three budgets ask one post-hoc
    # question (does dispersion add predictive value?), so the paper adjusts over all six per metric
    # and condition. The audit's three-test values (p_*_holm_across_K) are kept alongside.
    for an in con.values():
        for cond in an.values():
            keys = [(n, f"K{k}") for n in ("B-A", "D-C") for k in KS]
            for m in ("LL", "AUC", "BA"):
                for (n, kk), h in zip(keys, holm([cond[n][kk][f"p_{m}"] for n, kk in keys])):
                    cond[n][kk][f"p_{m}_holm_family6"] = h

    d02 = load(DIAG / "d02_results.json")
    excl = {}
    for r in d02["comparison_with_original"]:
        if r["analysis"].startswith("primary"):
            excl.setdefault(r["contrast"].replace(" ", ""), {})[f"K{r['K']}"] = pick(
                r, ["n_events_orig", "n_events_excl", "dLL_orig", "dLL_excl", "dLL_ci_excl", "dLL_change",
                    "dAUC_excl", "dAUC_ci_excl", "p_LL_holm_excl"])
    changes = [abs(v["dLL_change"]) for c in excl.values() for v in c.values()]
    small = sorted(changes)[-2]   # largest change among all but the largest

    d01 = load(DIAG / "d01_results.json")
    comp = [a for a in d01["associations"] if a["class"] == "comparison"]
    camp = [a for a in d01["associations"] if a["class"] == "campaign"]
    strata = [s for s in d01["stratified_class_separation"] if s["stratum_m_K_over_K"] != "all views"]
    desc = v02["descriptive_lensd"]

    out["edge_limited_token_std"] = {
        "_source": [rel(AUD / "v02_results.json"), rel(DIAG / "d01_results.json"), rel(DIAG / "d02_results.json")],
        "_note": "Post hoc. Models: A = N_K; B = N_K + token-count dispersion; C = N_K + six structural features; "
                 "D = C + token-count dispersion. KK = trained and evaluated on single K-edge views; FF = full graphs "
                 "of the same events. Budget-specific cohorts, outer partition 42, ten sampling seeds, event-level "
                 "paired bootstrap (1,000 resamples), Holm over the six dispersion contrasts (B - A and D - C at three budgets; p_*_holm_family6), with the audit's three-budget values kept as p_*_holm_across_K. A and C equal the pipeline's "
                 "stored Study 2 values (checked).",
        "feature_sets": v02["feature_sets"],
        "performance": perf,
        "contrasts": con,
        "descriptive": desc,
        "spearman_view_vs_full_min": min(d["spearman_view_mean_vs_full"] for d in desc.values()),
        "exclusion_no_text": excl,
        "exclusion_n_contrasts": len(changes),
        "exclusion_n_within_second_largest": sum(c <= small + 1e-12 for c in changes),
        "exclusion_second_largest_abs_change": small,
        "exclusion_largest_abs_change": max(changes),
        "text_availability": {
            "comparison_event_spearman_by_K": {f"K{a['K']}": a["b_event_spearman"] for a in comp},
            "comparison_event_spearman_ci_by_K": {f"K{a['K']}": a["b_event_spearman_ci"] for a in comp},
            "campaign_event_spearman_by_K": {f"K{a['K']}": a["b_event_spearman"] for a in camp},
            "campaign_event_spearman_ci_by_K": {f"K{a['K']}": a["b_event_spearman_ci"] for a in camp},
            "stratified_auc_min": min(s["auc_token_std_comparison_higher_mean_over_seeds"] for s in strata),
            "stratified_auc_max": max(s["auc_token_std_comparison_higher_mean_over_seeds"] for s in strata),
            "descriptives": d01["descriptives"],
        },
    }


def study2_holm(out, R, S):
    """Pipeline Study 2 contrasts with Holm across the three budgets (per contrast and metric)."""
    res = {}
    for name in ("retrain_effect_struct6", "retrain_effect_combined", "transfer_loss_struct6", "structure_beyond_NK",
                 "content_beyond_NK_struct", "ensemble_vs_single_combined"):
        block = {}
        for metric in ("log_loss", "ba"):
            cs = [R["study2"]["contrasts"][f"budget_specific_K{k}"][name][metric] for k in KS]
            hs = holm([c["p_bootstrap"] for c in cs])
            for k, c, h in zip(KS, cs, hs):
                block.setdefault(f"K{k}", {})[metric] = {"delta": c["delta"], "ci": c["ci"], "p": c["p_bootstrap"], "p_holm_across_K": h}
        res[name] = block
    kkff = {}
    for k in KS:
        b = S["rq2_baselines"][f"budget_specific_K{k}"]["KK_minus_FF_combined"]
        kkff[f"K{k}"] = {m: {"delta": b[m]["delta"], "ci": b[m]["ci"]} for m in ("log_loss", "ba")}
    res["KK_minus_FF_combined"] = kkff
    out["study2_contrasts_holm"] = {
        "_source": [f"{R['source_run']}/paper_results.json (study2.contrasts)", "outputs/revision_supplement/supplement.json (rq2_baselines)"],
        "_note": "Estimates, intervals and bootstrap p-values are the pipeline's (1,000 resamples). p_holm_across_K adjusts "
                 "each contrast and metric across K = 250, 500, 1000; it is computed here from the stored p-values. "
                 "KK_minus_FF_combined has no stored p-value, so it has no adjusted value.",
        "contrasts": res,
    }


def main(config_path, out_path):
    cfg = yaml.safe_load(open(ROOT / config_path, encoding="utf-8"))
    R = load(ROOT / cfg["output"]["run_dir"] / "paper_results.json")
    S = load(ROOT / cfg["output"]["revision_supplement"])
    out = {"_note": "Generated by src/export_audit_results.py from stored audit and pipeline outputs. Do not edit by hand."}
    study1(out)
    text_retention(out)
    edge_limited(out, R)
    study2_holm(out, R, S)
    dest = ROOT / (out_path or cfg["output"].get("audit_results", "outputs/research_audit/audit_results.json"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"Audit results -> {rel(dest)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    main(a.config, a.out)
