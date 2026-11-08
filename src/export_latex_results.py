"""
export_latex_results.py
-----------------------
Writes the LaTeX macros that carry every number in the paper,
paper/generated/results.tex, from <run_dir>/paper_results.json, the
revision supplement (output.revision_supplement in the config, written by
src/revision_supplement.py) and the audit results (output.audit_results,
written by src/export_audit_results.py from the stored research_audit outputs).
The paper
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
    # \ensuremath keeps the bound valid in text and lets main.tex write $p\R...$ with math spacing
    return r"\ensuremath{<0.001}" if p < 0.001 else f3(p)


def pvh(p, m=3, nboot=1000):
    """Holm-adjusted p over m tests from a bootstrap with nboot resamples: a raw p of 0 means
    p < 1/nboot, so the adjusted bound is m/nboot, not 0."""
    return rf"\ensuremath{{<{fixed(m / nboot, 3)}}}" if p == 0 else pv(p)


def intc(v):
    return f"{round(v):,}"


NUMWORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


def rows(lines):
    """Table body: cells joined by &, rows ended by \\\\ and a rule."""
    return "\n".join(" & ".join(r) + r" \\ \hline" for r in lines)


def stack(*lines):
    return r"\shortstack{" + r"\\".join(lines) + "}"


def mark(ci_pair, p_holm=None):
    """Significance markers: dagger if the nominal 95% interval excludes zero,
    asterisk if the Holm-adjusted p-value is below 0.05."""
    s = ""
    if ci_pair[0] > 0 or ci_pair[1] < 0:
        s += r"$^{\dagger}$"
    if p_holm is not None and p_holm < 0.05:
        s += r"$^{*}$"
    return s


def audit_macros(m, T, R, A):
    """Macros and tables for the results added in the final revision: the 20-partition
    sensitivity analysis, the conditional structure contrasts, the missing-text exclusion,
    text retention, token-count dispersion and the edge-limited log-loss/AUC tables."""
    P = A["study1_20_partitions"]
    C = P["contrasts"]
    LC, EX = R["study1"]["confirmatory"]["logreg"], R["study1"]["exploratory"]["logreg"]
    lr = R["study1"]["performance"]["logreg"]
    pf = P["performance"]
    X = A["text_retention"]
    E = A["edge_limited_token_std"]
    H = A["study2_contrasts_holm"]["contrasts"]
    V = E["contrasts"]["primary"]["KK"]
    KS = (250, 500, 1000)
    cond = lambda k, key: R["study2"]["results"][f"budget_specific_K{k}"]["conditions"][key]
    dash = "---"

    # ---- 20-partition sensitivity, conditional contrasts, exclusion, post-hoc rows (inline)
    def tw(key, name):
        c = C[key]
        return {f"{name}LL": sg(c["dLL"]), f"{name}LLCI": ci(c["dLL_ci"]), f"{name}AUC": sg(c["dAUC"]),
                f"{name}AUCCI": ci(c["dAUC_ci"]), f"{name}Fav": str(c["repeats_favouring_A_LL"]), f"{name}P": pv(c["p_LL"])}

    for key, name in (("C1", "TwCOne"), ("C2", "TwCTwo"), ("C3", "TwCThree"), ("E1", "TwEOne"), ("M2_minus_M0q", "TwStruct"),
                      ("E2", "TwETwo"), ("E3", "TwEThree"), ("arrangement_given_content_degree", "TwArrGiven"),
                      ("degree_given_content_arrangement", "TwDegGiven"), ("M4_minus_spline", "FlexSpline"),
                      ("M4_minus_cubic", "FlexCubic"), ("M4_minus_QDA", "FlexQDA"), ("C1_text101", "NoTextCOne"),
                      ("C3_text101", "NoTextCThree"), ("E3_text101", "NoTextEThree"), ("C1_grouped", "GroupedCOne"),
                      ("tokenstd_beyond_counts", "TokCounts"), ("M4_minus_counts_tokenstd", "TokMFour")):
        m.update(tw(key, name))
    m.update(NPartitions=str(P["n_partitions"]),
             TwPartSD=fixed(C["C1"]["repeat_dLL_sd"], 3), TwEventSD=fixed(C["C1"]["dLL_event_sd"], 3),
             TwCOneMin=sg(C["C1"]["repeat_dLL_min"]), TwCOneMax=sg(C["C1"]["repeat_dLL_max"]),
             TwCOneBAMin=sg(C["C1"]["repeat_dBA_min"]), TwCOneBAMax=sg(C["C1"]["repeat_dBA_max"]),
             TwCOneBAPos=str(int(C["C1"]["repeats_favouring_A_BA"])),
             TwCTwoBAMin=sg(C["C2"]["repeat_dBA_min"]), TwCTwoBAMax=sg(C["C2"]["repeat_dBA_max"]),
             TwCThreeBAMin=sg(C["C3"]["repeat_dBA_min"]), TwCThreeBAMax=sg(C["C3"]["repeat_dBA_max"]),
             TwHolmN=NUMWORDS[len(P["holm_family"])], NoTextN=str(P["n_events_text101"]),
             FlexSplineHolm=pv(C["M4_minus_spline"]["p_LL_holm"]), FlexCubicHolm=pv(C["M4_minus_cubic"]["p_LL_holm"]),
             FlexQDAHolm=pv(C["M4_minus_QDA"]["p_LL_holm"]),
             TopTenShare=str(round(100 * P["concentration"]["share_from_top10_favouring_M4"])),
             TwEventsImproved=str(P["concentration"]["events_improved"]),
             LoeoMin=sg(P["concentration"]["refit_leave_one_event_out_dLL_range"][0]),
             LoeoMax=sg(P["concentration"]["refit_leave_one_event_out_dLL_range"][1]),
             TwCountsLL=f3(pf["M0q"]["LL"]), TwAllLL=f3(pf["M4"]["LL"]), TwCountsBA=f3(pf["M0"]["BA"]),
             COneLLRaw=sg(LC["C1"]["log_loss"]["delta_logloss"]),
             EOneLL=sg(EX["E1"]["delta_logloss"]), EOneLLCI=ci(EX["E1"]["delta_logloss_ci"]),
             ETwoAUC=sg(EX["E2"]["delta_auc_ll_fit"]), ETwoAUCCI=ci(EX["E2"]["delta_auc_ll_fit_ci"]),
             CTwoLL=sg(LC["C2"]["log_loss"]["delta_logloss"]), CTwoLLCI=ci(LC["C2"]["log_loss"]["delta_logloss_ci"]),
             CThreeLL=sg(LC["C3"]["log_loss"]["delta_logloss"]), CThreeLLCI=ci(LC["C3"]["log_loss"]["delta_logloss_ci"]),
             CountsLL=f3(lr["M0"]["log_loss"]), CountsAUC=f3(lr["M0"]["roc_auc_ll_fit"]),
             COneBAHolm=pv(LC["C1"]["ba"]["p_holm"]), CTwoLLHolm=pv(LC["C2"]["log_loss"]["p_holm"]),
             CThreeLLHolm=pv(LC["C3"]["log_loss"]["p_holm"]))

    nd = R["dataset"]["nodes"]
    m.update(NodesMedCamp=intc(nd["campaign"]["median"]), NodesMedComp=intc(nd["comparison"]["median"]))

    # ---- text retention (Table I rows and inline)
    m.update(TextLinks=intc(X["links_total"]), TextNullPct=pct(X["null_share"]),
             UsableCamp=f2(X["usable_share_mean_campaign"]), UsableComp=f2(X["usable_share_mean_comparison"]),
             NoTextEvents=NUMWORDS[X["events_without_usable_text"]], LowTextCamp=str(X["events_usable_share_below_0_2_campaign"]),
             LowTextComp=NUMWORDS[X["events_usable_share_below_0_2_comparison"]])
    old = r"Account identifiers & none (per-graph node indices) \\ \hline"
    assert old in T["TabCohort"]
    T["TabCohort"] = T["TabCohort"].replace(old, rows([
        ["Edge texts", f"{intc(X['links_total'])}; {pct(X['null_share'])}\\% null"],
        ["Usable-text share, mean", f"campaign {f2(X['usable_share_mean_campaign'])}; comparison {f2(X['usable_share_mean_comparison'])}; "
                                    f"{X['events_without_usable_text']} campaign graphs have none"],
        ["Edge-limited cohorts", "; ".join(f"$K={k}$: {R['eligibility'][str(k)]['total_eligible']} "
                                           f"({R['eligibility'][str(k)]['campaign_eligible']}/{R['eligibility'][str(k)]['comparison_eligible']})"
                                           for k in KS)],
        ["Account identifiers", "none (per-graph node indices)"]]))

    # ---- full observation: performance by level (primary partition and 20-partition mean)
    T["TabLevels"] = rows([[lab, f3(lr[lv]["log_loss"]), f3(lr[lv]["roc_auc_ll_fit"]), f3(lr[lv]["balanced_accuracy"]),
                            f3(pf[lv]["LL"]), f3(pf[lv]["AUC"]), f3(pf[lv]["BA"])]
                           for lv, lab in (("M0", "M0"), ("M0q", "M0q"), ("M1", "M1"), ("M2", "M2"), ("M3", "M3"), ("M4", "M4"))]
                          + [[r"M0q + disp.$^{\mathrm{p}}$", dash, dash, dash, f3(pf["M0q+lensd"]["LL"]), f3(pf["M0q+lensd"]["AUC"]), dash]])

    # ---- full observation: contrasts (primary partition and 20 partitions)
    def cell(est, interval, holm=None):
        lines = [sg(est) + mark(interval, holm), ci(interval)]
        return stack(*(lines + [f"(Holm {pv(holm)})"] if holm is not None else lines))

    def group(title, ncol):
        return [rf"\multicolumn{{{ncol}}}{{|l|}}{{\textit{{{title}}}}}"]

    def lc(k):
        L = LC[k]
        return [cell(L["log_loss"]["delta_logloss"], L["log_loss"]["delta_logloss_ci"], L["log_loss"]["p_holm"]),
                cell(L["auc_ll_fit"]["delta_auc"], L["auc_ll_fit"]["delta_auc_ci"]),
                cell(L["ba"]["delta_ba"], L["ba"]["delta_ba_ci"], L["ba"]["p_holm"])]

    def ex(k):
        e = EX[k]
        return [cell(e["delta_logloss"], e["delta_logloss_ci"]), cell(e["delta_auc_ll_fit"], e["delta_auc_ll_fit_ci"]),
                cell(e["delta_ba"], e["delta_ba_ci"])]

    def twenty(key):
        c = C[key]
        return [cell(c["dLL"], c["dLL_ci"]), cell(c["dAUC"], c["dAUC_ci"]), f"{c['repeats_favouring_A_LL']}/{c['n_repeats']}"]

    nt = NUMWORDS[X["events_without_usable_text"]]
    lab = lambda a, b: rf"\shortstack[l]{{{a}\\{b}}}"
    T["TabFullContrasts"] = rows([
        group("Primary: prespecified, Holm over the three tests for each metric", 7),
        [lab(r"C1: M4 $-$ M0q", "all features beyond counts"), *lc("C1"), *twenty("C1")],
        [lab(r"C2: M2 $-$ M1", "arrangement beyond counts + degree"), *lc("C2"), *twenty("C2")],
        [lab(r"C3: M3 $-$ M0q", "content beyond counts"), *lc("C3"), *twenty("C3")],
        group("Exploratory: conditional contributions, unadjusted", 7),
        [lab(r"M1 $-$ M0q", "degree concentration beyond counts"), *ex("E1"), *twenty("E1")],
        [lab(r"M2 $-$ M0q", "structure beyond counts"), dash, dash, dash, *twenty("M2_minus_M0q")],
        [lab(r"M4 $-$ M3", "structure beyond counts + content"), *ex("E2"), *twenty("E2")],
        [lab(r"M4 $-$ M2", "content beyond counts + structure"), *ex("E3"), *twenty("E3")],
        group("Sensitivity: C1 on altered event sets or folds, unadjusted", 7),
        [lab("C1", rf"without the {nt} no-text graphs ($n={P['n_events_text101']}$)"), dash, dash, dash, *twenty("C1_text101")],
        [lab("C1", "repeated hashtags in one fold"), dash, dash, dash, *twenty("C1_grouped")],
        group("Post hoc: token-count dispersion, unadjusted", 7),
        [lab(r"M0q + disp. $-$ M0q", "dispersion beyond counts"), dash, dash, dash, *twenty("tokenstd_beyond_counts")],
        [lab(r"M4 $-$ (M0q + disp.)", "all features beyond counts + disp."), dash, dash, dash, *twenty("M4_minus_counts_tokenstd")],
    ])

    # ---- edge-limited: performance by condition (pipeline), dispersion models B and D (audit)
    body = []
    for key, label in (("FF|combined", "FF, all features"), ("FF|NK", "FF, node count"), ("FF|struct6", "FF, structure"),
                       ("FK|NK", "FK, node count"), ("FK|struct6", "FK, structure"), ("KK|struct6", "KK, structure"),
                       ("KK|NK", r"KK, $N_K$ (A)"), ("KK|NK_struct6", r"KK, $N_K$ + structure (C)"),
                       ("KK|combined", r"KK, $N_K$ + structure + content")):
        body.append([label, *[f3(cond(k, key)[f]) for k in KS
                              for f in ("single_view_logloss_mean", "single_view_auc_mean", "single_view_ba_mean")]])
    for model, label in (("B", r"KK, $N_K$ + dispersion (B)$^{\mathrm{p}}$"), ("D", r"KK, $N_K$ + structure + disp. (D)$^{\mathrm{p}}$")):
        body.append([label, *[f3(E["performance"][f"K{k}"]["KK"][model][f]) for k in KS for f in ("log_loss", "auc", "ba")]])
    body.append(["KK, all features, 10-view ensemble",
                 *[f3(cond(k, "KK|combined")[f]) for k in KS for f in ("ensemble_logloss", "ensemble_auc", "ensemble_ba")]])
    T["TabEdgePerf"] = rows(body)

    # ---- edge-limited: contrasts (log loss leads, BA beside it)
    def pc(name, k):
        b = H[name][f"K{k}"]
        return [cell(b[mt]["delta"], b[mt]["ci"]) if b[mt].get("p_holm_across_K") is None else
                stack(sg(b[mt]["delta"]) + mark(b[mt]["ci"], b[mt]["p_holm_across_K"]), ci(b[mt]["ci"]))
                for mt in ("log_loss", "ba")]

    def vc(name, k):
        x = V[name][f"K{k}"]
        return [stack(sg(x["dLL"]) + mark(x["dLL_ci"], x["p_LL_holm_family6"]), ci(x["dLL_ci"])),
                stack(sg(x["dBA"]) + mark(x["dBA_ci"], x["p_BA_holm_family6"]), ci(x["dBA_ci"]))]

    T["TabEdgeContrasts"] = rows(
        [group("Observation regime (exploratory)", 7)]
        + [[lab_, *[c for k in KS for c in pc(n, k)]] for n, lab_ in (
            ("KK_minus_FF_combined", r"View $-$ full graph (KK $-$ FF), all features"),
            ("retrain_effect_struct6", r"Retraining (KK $-$ FK), structure"),
            ("retrain_effect_combined", r"Retraining (KK $-$ FK), all features"),
            ("transfer_loss_struct6", r"Transfer (FK $-$ FF), structure"),
            ("ensemble_vs_single_combined", r"10-view ensemble $-$ single view, all"))]
        + [group("Features within views, KK (exploratory)", 7)]
        + [[lab_, *[c for k in KS for c in pc(n, k)]] for n, lab_ in (
            ("structure_beyond_NK", r"Structure beyond $N_K$ (C $-$ A)"),
            ("content_beyond_NK_struct", r"Content beyond $N_K$ + structure"))]
        + [group("Token-count dispersion within views, KK (post hoc)", 7)]
        + [[lab_, *[c for k in KS for c in vc(n, k)]] for n, lab_ in (
            ("B-A", r"Dispersion beyond $N_K$ (B $-$ A)"),
            ("D-C", r"Dispersion beyond $N_K$ + structure (D $-$ C)"))])

    # ---- edge-limited inline values
    for k, name in ((250, "TwoFifty"), (500, "FiveHundred"), (1000, "Thousand")):
        pk = E["performance"][f"K{k}"]["KK"]
        m[f"NKAUC{name}"] = f3(pk["A"]["auc"])
        m[f"NKLL{name}"] = f3(pk["A"]["log_loss"])
        m[f"BLL{name}"] = f3(pk["B"]["log_loss"])
        m[f"CLL{name}"] = f3(pk["C"]["log_loss"])
        m[f"DLL{name}"] = f3(pk["D"]["log_loss"])
        for cn, tag in (("B-A", "BA"), ("D-C", "DC")):
            x = V[cn][f"K{k}"]
            m[f"Tok{tag}LL{name}"] = sg(x["dLL"])
            m[f"Tok{tag}LLCI{name}"] = ci(x["dLL_ci"])
            m[f"Tok{tag}AUC{name}"] = sg(x["dAUC"])
            m[f"Tok{tag}AUCCI{name}"] = ci(x["dAUC_ci"])
            m[f"Tok{tag}Holm{name}"] = pvh(x["p_LL_holm_family6"], m=6)
            m[f"Tok{tag}Seeds{name}"] = str(x["repeats_favouring_A_LL"])
        d = E["descriptive"][str(k)]
        m[f"TokUniAUC{name}"] = f2(d["auc_lensd_for_comparison_single_view_mean"])
        m[f"TokUniAUCFull{name}"] = f2(d["auc_lensd_for_comparison_full_graph"])
        for nm, key in (("Content", "content_beyond_NK_struct"), ("Ensemble", "ensemble_vs_single_combined"),
                        ("StructNK", "structure_beyond_NK"), ("RetrainS", "retrain_effect_struct6"),
                        ("RetrainAllS", "retrain_effect_combined"), ("TransferS", "transfer_loss_struct6")):
            x = H[key][f"K{k}"]["log_loss"]
            m[f"{nm}LL{name}"] = sg(x["delta"])
            m[f"{nm}LLCI{name}"] = ci(x["ci"])
            m[f"{nm}LLHolm{name}"] = pvh(x["p_holm_across_K"])
        x = H["KK_minus_FF_combined"][f"K{k}"]["log_loss"]
        m[f"ViewFullLL{name}"] = sg(x["delta"])
        m[f"ViewFullLLCI{name}"] = ci(x["ci"])
        m[f"FKNKBA{name}"] = f3(cond(k, "FK|NK")["single_view_ba_mean"])
        m[f"FKNKAUC{name}"] = f3(cond(k, "FK|NK")["single_view_auc_mean"])
        m[f"FKStructAUC{name}"] = f3(cond(k, "FK|struct6")["single_view_auc_mean"])
        m[f"KKStructAUC{name}"] = f3(cond(k, "KK|struct6")["single_view_auc_mean"])
        m[f"KKAllAUC{name}"] = f3(cond(k, "KK|combined")["single_view_auc_mean"])
        m[f"FFAllAUC{name}"] = f3(cond(k, "FF|combined")["single_view_auc_mean"])
    # Structure beyond N_K at K = 250 on the common cohort (its direction differs from the budget-specific cohort)
    cs = R["study2"]["contrasts"]["common_K250"]["structure_beyond_NK"]["log_loss"]
    m.update(CommonStructLL=sg(cs["delta"]), CommonStructLLCI=ci(cs["ci"]))
    # The nonlinear count control itself: M0q - M0 (exploratory E4)
    m.update(EFourLL=sg(EX["E4"]["delta_logloss"]), EFourLLCI=ci(EX["E4"]["delta_logloss_ci"]))
    seeds = [V[cn][f"K{k}"]["repeats_favouring_A_LL"] for cn in ("B-A", "D-C") for k in KS]
    nrep = {V[cn][f"K{k}"]["n_repeats"] for cn in ("B-A", "D-C") for k in KS}
    assert len(nrep) == 1
    m.update(TokSeedsMin=str(min(seeds)), TokSeedsN=str(nrep.pop()))
    rhos = list(E["text_availability"]["comparison_event_spearman_by_K"].values())
    m.update(TokSpearmanMin=f3(E["spearman_view_vs_full_min"]),
             TokTextRhoMin=sg(max(rhos)), TokTextRhoMax=sg(min(rhos)),
             TokStratMin=f2(E["text_availability"]["stratified_auc_min"]), TokStratMax=f2(E["text_availability"]["stratified_auc_max"]),
             ExclN=NUMWORDS[E["exclusion_n_contrasts"]], ExclWithin=NUMWORDS[E["exclusion_n_within_second_largest"]],
             ExclSecond=f3(E["exclusion_second_largest_abs_change"]), ExclMax=f3(E["exclusion_largest_abs_change"]),
             EnsembleLLMax=f3(max(abs(H["ensemble_vs_single_combined"][f"K{k}"]["log_loss"]["delta"]) for k in KS)))


def build(R, S, A):
    D, S1, S2, NM, MT, EL = R["dataset"], R["study1"], R["study2"], R["null_model"], R["matching"], R["eligibility"]
    lr, hg, LC = S1["performance"]["logreg"], S1["performance"]["hgbt"], S1["confirmatory"]["logreg"]
    rep, ro, X = S1["repeated_splits_lr"], S1["row_order_sensitivity"], S1["hgbt_vs_best_count_baseline"]["HGBT_M4_vs_LR_M0q_ba"]
    # AUC follows the paper's estimand rule: log-loss-tuned fits (BA stays with BA-tuned fits)
    XL = S1["hgbt_vs_best_count_baseline"]["HGBT_M4_vs_LR_M0q_ll"]
    EX = S1["exploratory"]["logreg"]
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
             HGBTvsLRAUC=sg(XL["delta_auc"]), HGBTvsLRAUCCI=ci(XL["delta_auc_ci"]), HGBTAllLL=f3(hg["M4"]["log_loss"]),
             ETwoLL=sg(EX["E2"]["delta_logloss"]), ETwoLLCI=ci(EX["E2"]["delta_logloss_ci"]),
             EThreeLL=sg(EX["E3"]["delta_logloss"]), EThreeLLCI=ci(EX["E3"]["delta_logloss_ci"]))

    # repeated splits: sign counts (supplement)
    sp = S["repeated_splits_signs"]
    m.update(SplitLLNeg=NUMWORDS[sp["C1"]["n_dLL_negative"]], SplitBAPos=NUMWORDS[sp["C1"]["n_dBA_positive"]],
             SplitNWord=NUMWORDS[sp["n_splits"]], SplitBAMean=sg(sp["C1"]["dBA_mean"]), SplitLLMedian=sg(sp["C1"]["dLL_median"]),
             SplitETwoNeg=NUMWORDS[sp["E2_M4_minus_M3_n_dLL_negative"]], SplitEThreeNeg=NUMWORDS[sp["E3_M4_minus_M2_n_dLL_negative"]])

    # H1: wider regularisation grid for logistic regression (supplement)
    h = S["h1"]
    gfmt = lambda v: f"{v:g}" if v < 1000 else f"10^{{{len(str(int(v))) - 1}}}"
    m.update(HOrigGrid=", ".join(gfmt(v) for v in h["original_grid"]),
             HGridMin=gfmt(min(h["grid"])), HGridMax=gfmt(max(h["grid"])),
             HCountsLL=f3(h["M0q"]["log_loss"]), HAllLL=f3(h["M4"]["log_loss"]),
             HCOneLL=sg(h["C1"]["delta_logloss"]), HCOneLLCI=ci(h["C1"]["delta_logloss_ci"]),
             HCOneBA=sg(h["C1"]["delta_ba"]), HCOneBACI=ci(h["C1"]["delta_ba_ci"]),
             HSplitLLNeg=NUMWORDS[h["repeated_splits_C1"]["n_dLL_negative"]])

    # degree-preserving null
    m.update(Swaps=str(NM["swaps_per_edge"]), Realizations=str(NM["realizations"]),
             ZRecipCamp=f2(z["reciprocity"]["median_z_campaign"]), ZRecipComp=f2(z["reciprocity"]["median_z_comparison"]),
             ZWCCCamp=f2(z["largest_wcc_fraction"]["median_z_campaign"]),
             NullRealBA=f3(NM["M2_real_ba"]), NullMeanBA=f3(NM["M2_null_ba_mean"]),
             NullMinBA=f3(NM["M2_null_ba_range"][0]), NullMaxBA=f3(NM["M2_null_ba_range"][1]),
             NullDBA=sg(NM["real_minus_null_ba"]["delta_ba"]), NullDBACI=ci(NM["real_minus_null_ba"]["delta_ba_ci"]),
             NullDLL=sg(NM["real_minus_null_logloss"]["delta_logloss"]), NullDLLCI=ci(NM["real_minus_null_logloss"]["delta_logloss_ci"]),
             UnmovedPct=str(round(100 * NM["frac_edges_unchanged_quantiles"][2])),
             CoreZeroVarPct=str(round(100 * NM["share_events_zero_null_variance"]["coreness_median"])),
             ZUndefRecipPct=str(round(100 * z["reciprocity"]["share_undefined_sd0"])),
             NullMeanMinusReal=sg(NM["M2_real_ba"] - NM["M2_null_ba_mean"]))
    ch = S["null_feature_change"]
    m.update(ChRecipPct=str(round(100 * ch["reciprocity"]["share_events_changed_in_some_realization"])),
             ChWCCPct=str(round(100 * ch["largest_wcc_fraction"]["share_events_changed_in_some_realization"])),
             ChCoreMedPct=str(round(100 * ch["coreness_median"]["share_events_changed_in_some_realization"])),
             ChCoreMaxPct=str(round(100 * ch["coreness_max"]["share_events_changed_in_some_realization"])))

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
        rq = S["rq2_baselines"][f"budget_specific_K{k}"]
        m[f"FFAll{name}"] = f3(cond(k, "FF|combined")["single_view_ba_mean"])
        m[f"ViewMinusFull{name}"] = sg(rq["KK_minus_FF_combined"]["ba"]["delta"])
        m[f"ViewMinusFull{name}CI"] = ci(rq["KK_minus_FF_combined"]["ba"]["ci"])
        m[f"ViewMinusFullLL{name}"] = sg(rq["KK_minus_FF_combined"]["log_loss"]["delta"])
        m[f"ViewMinusFullLL{name}CI"] = ci(rq["KK_minus_FF_combined"]["log_loss"]["ci"])
        nk = S["nk_vs_structure"][f"K{k}"]
        m[f"NKMinusStruct{name}"] = sg(nk["NK_minus_structure"]["delta"])
        m[f"NKMinusStruct{name}CI"] = ci(nk["NK_minus_structure"]["ci"])
        m[f"NKAdded{name}"] = sg(nk["NK_added_to_structure"]["delta"])
        m[f"NKAdded{name}CI"] = ci(nk["NK_added_to_structure"]["ci"])
        m[f"ProxyRTwo{name}"] = f3(S["structure_predicts_log_NK"][f"K{k}"]["r2_event_grouped_cv"])
        m[f"RetrainAll{name}"] = sg(con(k, "retrain_effect_combined")["ba"]["delta"])
        m[f"RetrainAll{name}CI"] = ci(con(k, "retrain_effect_combined")["ba"]["ci"])
    m.update(TwoThousandCamp=str(EL["2000"]["campaign_eligible"]),
             NViewEvents=str(S2["results"]["budget_specific_K250"]["n_events"]),
             RetrainTwoFiftyCI=ciu(con(250, "retrain_effect_struct6")["ba"]["ci"]),
             TransferLossTwoFifty=f3(-con(250, "transfer_loss_struct6")["ba"]["delta"]),
             EnsembleMax=f3(max(abs(con(k, "ensemble_vs_single_combined")["ba"]["delta"]) for k in (250, 500, 1000))),
             CommonRetrainTwoFifty=f3(S2["contrasts"]["common_K250"]["retrain_effect_struct6"]["ba"]["delta"]),
             STwoNBoot=intc(S["study2_n_bootstrap"]),
             CommonN=str(S["rq2_baselines"]["common_K250"]["n_events"]),
             CommonCamp=str(S["rq2_baselines"]["common_K250"]["n_campaign"]),
             CommonComp=str(S["rq2_baselines"]["common_K250"]["n_comparison"]),
             HashtagPairs=NUMWORDS[S["n_repeated_hashtag_pairs"]],
             HashtagPairsCap=NUMWORDS[S["n_repeated_hashtag_pairs"]].capitalize(),
             HashtagPairsSplit=NUMWORDS[S["n_repeated_hashtag_pairs_split_across_folds"]],
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
        ["LEN-Small (LEN paper)", f"{D['official_len_small']['n_graphs']} graphs ({D['official_len_small']['n_campaign']} / {D['official_len_small']['n_noncampaign']}); a distinct dataset description (Section III)"],
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
        [f"M2 rewired, BA: mean [range] of the {NM['realizations']} per-realization fits$^{{\\mathrm{{a}}}}$", f"{f3(NM['M2_null_ba_mean'])} [{f3(NM['M2_null_ba_range'][0])}--{f3(NM['M2_null_ba_range'][1])}]"],
        [r"Real $-$ rewired ensemble$^{\mathrm{b}}$, $\Delta$BA [95\% CI]", f"{sg(NM['real_minus_null_ba']['delta_ba'])} {ci(NM['real_minus_null_ba']['delta_ba_ci'])}"],
        [r"Real $-$ rewired ensemble$^{\mathrm{b}}$, $\Delta$log loss [95\% CI]", f"{sg(NM['real_minus_null_logloss']['delta_logloss'])} {ci(NM['real_minus_null_logloss']['delta_logloss_ci'])}"],
        ["Unmoved non-loop edges, median [IQR]", f"{f2(q[2])} [{f2(q[1])}--{f2(q[3])}]"],
    ])
    T["TabMatching"] = rows([[("Log node count" if k == "node_only" else "Log node + edge count"),
                              f"{MT[k]['n_pairs_range'][0]}--{MT[k]['n_pairs_range'][1]}",
                              *[rf"\shortstack{{{f3(MT[k]['ba'][lv]['median'])}\\[{f3(MT[k]['ba'][lv]['min'])}--{f3(MT[k]['ba'][lv]['max'])}]}}" for lv in ("M0", "M3", "M4")]]
                             for k in ("node_only", "node_edge")])
    s2 = [("FF|combined", r"FF: full $\to$ full, all features"), ("FF|NK", r"FF: full $\to$ full, node count"),
          ("FF|struct6", r"FF: full $\to$ full, structure"), ("FK|struct6", r"FK: full $\to$ view, structure"),
          ("KK|struct6", r"KK: view $\to$ view, structure"), ("KK|NK", r"KK: $N_K$ only"),
          ("KK|NK_struct6", r"KK: $N_K$ + structure"), ("KK|combined", r"KK: $N_K$ + structure + content")]
    T["TabSingleView"] = rows([[label, *[f3(cond(k, key)["single_view_ba_mean"]) for k in (250, 500, 1000)]] for key, label in s2]
                              + [["KK: all, 10-view ensemble", *[f3(cond(k, "KK|combined")["ensemble_ba"]) for k in (250, 500, 1000)]]])
    s2c = [("retrain_effect_struct6", r"Retraining (KK $-$ FK), structure"), ("transfer_loss_struct6", r"Transfer (FK $-$ FF), structure"),
           ("structure_beyond_NK", r"Structure beyond $N_K$ (KK)"), ("content_beyond_NK_struct", r"Content beyond $N_K$ + structure"),
           ("ensemble_vs_single_combined", r"Ensemble $-$ single view (KK, all)")]
    rq2 = lambda k: S["rq2_baselines"][f"budget_specific_K{k}"]["KK_minus_FF_combined"]["ba"]
    T["TabSTwoContrasts"] = rows([[r"Single view $-$ full graph (KK $-$ FF), all", *[rf"\shortstack{{{sg(rq2(k)['delta'])}\\{ci(rq2(k)['ci'])}}}" for k in (250, 500, 1000)]]]
                                 + [[label, *[rf"\shortstack{{{sg(con(k, n)['ba']['delta'])}\\{ci(con(k, n)['ba']['ci'])}}}" for k in (250, 500, 1000)]]
                                    for n, label in s2c])

    audit_macros(m, T, R, A)

    out = ["% Generated by src/export_latex_results.py from paper_results.json, the revision supplement and audit_results.json. Do not edit by hand.",
           f"% Source run: {R['source_run']}", ""]
    out += [rf"\newcommand{{\R{k}}}{{{v}}}" for k, v in m.items()]
    # A line break followed by "[" would be read as \\[<length>]; an empty group prevents that.
    out += [""] + [rf"\newcommand{{\R{k}}}{{%" + "\n" + v.replace("\\\\[", "\\\\{}[") + "}" for k, v in T.items()]
    return "\n".join(out) + "\n", len(m), len(T)


def main(config_path, out_path):
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    R = json.loads((Path(cfg["output"]["run_dir"]) / "paper_results.json").read_text(encoding="utf-8"))
    S = json.loads(Path(cfg["output"]["revision_supplement"]).read_text(encoding="utf-8"))
    A = json.loads(Path(cfg["output"]["audit_results"]).read_text(encoding="utf-8"))
    out = Path(out_path or cfg["output"].get("paper_results_tex", "paper/generated/results.tex"))
    text, n_inline, n_tables = build(R, S, A)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"LaTeX results -> {out} ({n_inline} inline values, {n_tables} tables)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    main(a.config, a.out)
