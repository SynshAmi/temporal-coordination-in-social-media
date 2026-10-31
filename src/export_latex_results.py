"""
export_latex_results.py
-----------------------
Writes the LaTeX macros that carry every number in the paper,
paper/generated/results.tex, from <run_dir>/paper_results.json. The paper
(paper/main.tex) never contains a hand-typed result: inline values are macros
such as \\RCountsBA, and table bodies are macros such as \\RTabLevels.

Formatting matches the website (frontend/src/lib/fmt.js): three decimals, a
true minus sign, signed differences, and "0.000" in place of "-0.000".

Usage: python src/export_latex_results.py [--config CONFIG] [--out PATH]
"""

import sys
import json
import argparse
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")

MINUS = "$-$"


def fixed(v, d):
    """Round like JavaScript's Number.toFixed (exact binary value, halves away from zero),
    so the paper prints the same digits as the website (e.g. 0.8125 -> 0.813)."""
    return str(Decimal(v).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))


def f3(v):
    return fixed(v, 3).replace("-", MINUS)


def f2(v):
    return fixed(v, 2).replace("-", MINUS)


def pct(v):
    return fixed(100 * v, 1)


def sg(v):
    return "0.000" if abs(v) < 0.0005 else ("+" if v > 0 else MINUS) + fixed(abs(v), 3)


def ci(a):
    return f"[{sg(a[0])}, {sg(a[1])}]"


def ciu(a):
    return f"[{f3(a[0])}, {f3(a[1])}]"


def pv(p):
    return "$<$0.001" if p < 0.001 else f3(p)


def intc(v):
    return f"{round(v):,}"


def rows(lines):
    """Table body: cells joined by &, rows ended by \\\\ and a rule."""
    return "\n".join(" & ".join(r) + r" \\ \hline" for r in lines)


def build(R):
    D, S1, S2, NM, MT, EL = R["dataset"], R["study1"], R["study2"], R["null_model"], R["matching"], R["eligibility"]
    lr, hg, LC = S1["performance"]["logreg"], S1["performance"]["hgbt"], S1["confirmatory"]["logreg"]
    rep, ro, X = S1["repeated_splits_lr"], S1["row_order_sensitivity"], S1["hgbt_vs_best_count_baseline"]["HGBT_M4_vs_LR_M0q_ba"]
    cond = lambda k, key: S2["results"][f"budget_specific_K{k}"]["conditions"][key]
    con = lambda k, n: S2["contrasts"][f"budget_specific_K{k}"][n]
    r2, mech = S2["mechanism_r2_K250"], S2["mechanism"]["K250"]
    z = NM["observed_vs_null_median_z"]
    m = {}

    # cohort
    m.update(NEvents=str(D["n_events"]), NCampaign=str(D["n_campaign"]), NComparison=str(D["n_comparison"]),
             ArchiveFiles=str(D["archive_json_files"]), DupRemoved=str(D["duplicates_removed"]),
             ExtraEvents=str(D["n_events"] - D["official_len_small"]["n_graphs"]),
             ExtraEventsWord=["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][D["n_events"] - D["official_len_small"]["n_graphs"]],
             OfficialN=str(D["official_len_small"]["n_graphs"]), OfficialCamp=str(D["official_len_small"]["n_campaign"]),
             OfficialNon=str(D["official_len_small"]["n_noncampaign"]),
             EdgesTotal=intc(D["n_edges_total"]), SelfLoops=intc(D["n_self_loops"]), SMDNodes=f2(D["smd_log_nodes_full_cohort"]))

    # Study 1
    baMaxHi = max(LC[k]["ba"]["delta_ba_ci"][1] for k in ("C1", "C2", "C3"))
    m.update(CountsBA=f3(lr["M0"]["balanced_accuracy"]), NodeOnlyBA=f3(R["run_v2_metrics"]["B0a_log_node_logreg"]["balanced_accuracy"]),
             AllBA=f3(lr["M4"]["balanced_accuracy"]), AllLL=f3(lr["M4"]["log_loss"]), AllAUC=f3(lr["M4"]["roc_auc_ll_fit"]),
             CountsQLL=f3(lr["M0q"]["log_loss"]), CountsQAUC=f3(lr["M0q"]["roc_auc_ll_fit"]),
             COneBA=sg(LC["C1"]["ba"]["delta_ba"]), COneBACI=ci(LC["C1"]["ba"]["delta_ba_ci"]),
             COneBALo=sg(LC["C1"]["ba"]["delta_ba_ci"][0]), COneBAHi=sg(LC["C1"]["ba"]["delta_ba_ci"][1]),
             COneLLGain=f3(-LC["C1"]["log_loss"]["delta_logloss"]), COneLLCI=ci(LC["C1"]["log_loss"]["delta_logloss_ci"]),
             COneLLHolm=pv(LC["C1"]["log_loss"]["p_holm"]), COneAUC=f3(LC["C1"]["auc_ll_fit"]["delta_auc"]),
             COneAUCCI=ci(LC["C1"]["auc_ll_fit"]["delta_auc_ci"]),
             COneOnlyAll=str(LC["C1"]["ba"]["mcnemar_a_right_b_wrong"]), COneOnlyCounts=str(LC["C1"]["ba"]["mcnemar_b_right_a_wrong"]),
             BAMaxHi=f2(baMaxHi), NBoot=intc(S1["n_bootstrap"]), NSplits=str(S1["n_split_seeds"]),
             SplitBAMin=sg(rep["C1"]["dBA_min"]), SplitBAMax=sg(rep["C1"]["dBA_max"]),
             SplitLLMin=sg(rep["C1"]["dLL_min"]), SplitLLMax=sg(rep["C1"]["dLL_max"]),
             SplitAUCMin=sg(rep["C1"]["dAUC_min"]), SplitAUCMax=sg(rep["C1"]["dAUC_max"]),
             RowOneStudy=sg(ro["ba:C1"]["delta_study_order"]), RowOnePerm=sg(ro["ba:C1"]["delta_permuted_order"]),
             RowThreeStudy=sg(ro["ba:C3"]["delta_study_order"]), RowThreePerm=sg(ro["ba:C3"]["delta_permuted_order"]),
             RowOneLL=sg(ro["ll:C1"]["delta_study_order"]),
             HGBTCountsBA=f3(hg["M0q"]["balanced_accuracy"]), HGBTvsLRBA=sg(X["delta_ba"]), HGBTvsLRBACI=ci(X["delta_ba_ci"]),
             HGBTvsLRAUC=sg(X["delta_auc"]), HGBTvsLRAUCCI=ci(X["delta_auc_ci"]), HGBTAllLL=f3(hg["M4"]["log_loss"]))

    # degree-preserving null
    m.update(Swaps=str(NM["swaps_per_edge"]), Realizations=str(NM["realizations"]),
             ZRecipCamp=f2(z["reciprocity"]["median_z_campaign"]), ZRecipComp=f2(z["reciprocity"]["median_z_comparison"]),
             ZWCCCamp=f2(z["largest_wcc_fraction"]["median_z_campaign"]),
             NullRealBA=f3(NM["M2_real_ba"]), NullMeanBA=f3(NM["M2_null_ba_mean"]),
             NullMinBA=f3(NM["M2_null_ba_range"][0]), NullMaxBA=f3(NM["M2_null_ba_range"][1]),
             NullDBA=sg(NM["real_minus_null_ba"]["delta_ba"]), NullDBACI=ci(NM["real_minus_null_ba"]["delta_ba_ci"]),
             NullDLL=sg(NM["real_minus_null_logloss"]["delta_logloss"]), NullDLLCI=ci(NM["real_minus_null_logloss"]["delta_logloss_ci"]),
             UnmovedPct=str(round(100 * NM["frac_edges_unchanged_quantiles"][2])),
             CoreZeroVarPct=str(round(100 * NM["share_events_zero_null_variance"]["coreness_median"])))

    # matching
    no = MT["node_only"]
    m.update(Caliper=str(MT["caliper_sd_fraction"]), Pairs=str(MT["primary_pairs"]), MatchedEvents=str(2 * MT["primary_pairs"]),
             SMDBefore=f3(MT["smd_before"]), SMDAfter=f3(MT["smd_after"]),
             AbsSMDBefore=f2(abs(MT["smd_before"])), AbsSMDAfter=f2(abs(MT["smd_after"])),
             Orders=str(no["n_order_seeds"]), PairsMin=str(no["n_pairs_range"][0]), PairsMax=str(no["n_pairs_range"][1]),
             EdgeSMDMin=f2(no["smd_log_edges_range"][0]), EdgeSMDMax=f2(no["smd_log_edges_range"][1]),
             MatchCountsBA=f3(no["ba"]["M0"]["median"]), MatchContentBA=f3(no["ba"]["M3"]["median"]),
             MatchContentMin=f3(no["ba"]["M3"]["min"]), MatchContentMax=f3(no["ba"]["M3"]["max"]))

    # Study 2
    for k, name in ((250, "TwoFifty"), (500, "FiveHundred"), (1000, "Thousand")):
        e = EL[str(k)]
        m[f"Elig{name}"] = str(e["total_eligible"])
        m[f"Elig{name}Camp"] = str(e["campaign_eligible"])
        m[f"Elig{name}Comp"] = str(e["comparison_eligible"])
        m[f"KKNK{name}"] = f3(cond(k, "KK|NK")["single_view_ba_mean"])
        m[f"KKAll{name}"] = f3(cond(k, "KK|combined")["single_view_ba_mean"])
        m[f"Retrain{name}"] = f3(con(k, "retrain_effect_struct6")["ba"]["delta"])
    m.update(TwoThousandCamp=str(EL["2000"]["campaign_eligible"]),
             NViewEvents=str(S2["results"]["budget_specific_K250"]["n_events"]),
             RetrainTwoFiftyCI=ciu(con(250, "retrain_effect_struct6")["ba"]["ci"]),
             TransferLossTwoFifty=f3(-con(250, "transfer_loss_struct6")["ba"]["delta"]),
             EnsembleMax=f3(max(abs(con(k, "ensemble_vs_single_combined")["ba"]["delta"]) for k in (250, 500, 1000))),
             CommonRetrainTwoFifty=f3(S2["contrasts"]["common_K250"]["retrain_effect_struct6"]["ba"]["delta"]),
             MechRelErr=pct(mech["max_abs_rel_error_expected_vs_observed"]), MechAUC=f3(mech["auc_expectedNK_label"]),
             MechAUCNodes=f3(mech["auc_log_N_full_label"]), RTwoSizeDegree=pct(r2["log N + log mean degree"]),
             RTwoNodes=pct(r2["log N only"]), RTwoWithGini=pct(r2["size + degree concentration"]))

    m.update(ChecksPassed=str(R["verification"]["n_pass"]), ChecksTotal=str(R["verification"]["n_checks"]))

    # ---- table bodies
    nd, ed = D["nodes"], D["edges"]
    T = {}
    T["TabCohort"] = rows([
        ["Archive JSON files", f"{D['archive_json_files']} ({D['duplicates_removed']} SHA-256 duplicate removed)"],
        ["Canonical events", f"{D['n_events']} ({D['n_campaign']} campaign / {D['n_comparison']} comparison)"],
        ["Official LEN-Small", f"{D['official_len_small']['n_graphs']} ({D['official_len_small']['n_campaign']} / {D['official_len_small']['n_noncampaign']}); smallest 100 of 314 by node count"],
        ["Nodes, median [IQR]", f"campaign {intc(nd['campaign']['median'])} [{intc(nd['campaign']['q25'])}--{intc(nd['campaign']['q75'])}]; comparison {intc(nd['comparison']['median'])} [{intc(nd['comparison']['q25'])}--{intc(nd['comparison']['q75'])}]"],
        ["Edges, median [IQR]", f"campaign {intc(ed['campaign']['median'])} [{intc(ed['campaign']['q25'])}--{intc(ed['campaign']['q75'])}]; comparison {intc(ed['comparison']['median'])} [{intc(ed['comparison']['q25'])}--{intc(ed['comparison']['q75'])}]"],
        ["Edges / self-loops", f"{intc(D['n_edges_total'])} / {intc(D['n_self_loops'])} (all {D['events_with_self_loops']} events)"],
        ["Account identifiers", "none (per-graph node indices)"],
    ])
    T["TabLevels"] = rows([[("M4 + density" if lv == "M4d" else lv),
                            f3(lr[lv]["balanced_accuracy"]), f3(lr[lv]["log_loss"]), f3(lr[lv]["roc_auc_ll_fit"]),
                            f3(hg[lv]["balanced_accuracy"]), f3(hg[lv]["log_loss"]), f3(hg[lv]["roc_auc_ll_fit"])]
                           for lv in ("M0", "M0q", "M1", "M2", "M3", "M4", "M4d")])
    # each cell: estimate / 95% interval / (Holm p), stacked so the table fits one column
    T["TabContrasts"] = rows([[rf"\shortstack[l]{{{k}:\\{LC[k]['a']} vs {LC[k]['b']}}}",
                               rf"\shortstack{{{sg(LC[k]['ba']['delta_ba'])}\\{ci(LC[k]['ba']['delta_ba_ci'])}\\({pv(LC[k]['ba']['p_holm'])})}}",
                               rf"\shortstack{{{sg(LC[k]['log_loss']['delta_logloss'])}\\{ci(LC[k]['log_loss']['delta_logloss_ci'])}\\({pv(LC[k]['log_loss']['p_holm'])})}}",
                               rf"\shortstack{{{sg(LC[k]['auc_ll_fit']['delta_auc'])}\\{ci(LC[k]['auc_ll_fit']['delta_auc_ci'])}}}"]
                              for k in ("C1", "C2", "C3")])
    q = NM["frac_edges_unchanged_quantiles"]
    T["TabNull"] = rows([
        ["M1 (counts + degree), BA", f3(NM["M1_ba"])],
        ["M2 real arrangement, BA", f3(NM["M2_real_ba"])],
        [f"M2 rewired arrangement, BA (mean of {NM['realizations']})", f"{f3(NM['M2_null_ba_mean'])} [{f3(NM['M2_null_ba_range'][0])}--{f3(NM['M2_null_ba_range'][1])}]"],
        [r"Real $-$ rewired, $\Delta$BA [95\% CI]", f"{sg(NM['real_minus_null_ba']['delta_ba'])} {ci(NM['real_minus_null_ba']['delta_ba_ci'])}"],
        [r"Real $-$ rewired, $\Delta$log loss [95\% CI]", f"{sg(NM['real_minus_null_logloss']['delta_logloss'])} {ci(NM['real_minus_null_logloss']['delta_logloss_ci'])}"],
        ["Unmoved non-loop edges, median [IQR]", f"{f2(q[2])} [{f2(q[1])}--{f2(q[3])}]"],
    ])
    T["TabMatching"] = rows([[("Log node count" if k == "node_only" else "Log node + edge count"),
                              f"{MT[k]['n_pairs_range'][0]}--{MT[k]['n_pairs_range'][1]}",
                              *[rf"\shortstack{{{f3(MT[k]['ba'][lv]['median'])}\\[{f3(MT[k]['ba'][lv]['min'])}--{f3(MT[k]['ba'][lv]['max'])}]}}" for lv in ("M0", "M3", "M4")]]
                             for k in ("node_only", "node_edge")])
    s2 = [("FF|struct6", r"FF: full $\to$ full, structure"), ("FK|struct6", r"FK: full $\to$ view, structure"),
          ("KK|struct6", r"KK: view $\to$ view, structure"), ("KK|NK", r"KK: $N_K$ only"),
          ("KK|NK_struct6", r"KK: $N_K$ + structure"), ("KK|combined", r"KK: $N_K$ + structure + content")]
    T["TabSingleView"] = rows([[label, *[f3(cond(k, key)["single_view_ba_mean"]) for k in (250, 500, 1000)]] for key, label in s2]
                              + [["KK: all, 10-view ensemble", *[f3(cond(k, "KK|combined")["ensemble_ba"]) for k in (250, 500, 1000)]]])
    s2c = [("retrain_effect_struct6", r"Retraining (KK $-$ FK), structure"), ("transfer_loss_struct6", r"Transfer (FK $-$ FF), structure"),
           ("structure_beyond_NK", r"Structure beyond $N_K$ (KK)"), ("content_beyond_NK_struct", r"Content beyond $N_K$ + structure"),
           ("ensemble_vs_single_combined", r"Ensemble $-$ single view (KK, all)")]
    T["TabSTwoContrasts"] = rows([[label, *[rf"\shortstack{{{sg(con(k, n)['ba']['delta'])}\\{ci(con(k, n)['ba']['ci'])}}}" for k in (250, 500, 1000)]]
                                  for n, label in s2c])

    out = ["% Generated by src/export_latex_results.py from paper_results.json. Do not edit by hand.",
           f"% Source run: {R['source_run']}", ""]
    out += [rf"\newcommand{{\R{k}}}{{{v}}}" for k, v in m.items()]
    # A line break followed by "[" would be read as \\[<length>]; an empty group prevents that.
    out += [""] + [rf"\newcommand{{\R{k}}}{{%" + "\n" + v.replace("\\\\[", "\\\\{}[") + "}" for k, v in T.items()]
    return "\n".join(out) + "\n", len(m), len(T)


def main(config_path, out_path):
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    R = json.loads((Path(cfg["output"]["run_dir"]) / "paper_results.json").read_text(encoding="utf-8"))
    out = Path(out_path or cfg["output"].get("paper_results_tex", "paper/generated/results.tex"))
    text, n_inline, n_tables = build(R)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"LaTeX results -> {out} ({n_inline} inline values, {n_tables} tables)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    main(a.config, a.out)
