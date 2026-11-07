// Accessors that assemble the paper's results from the payload (research_data.json).
// Every value comes from paper_results.json (data.paper), the revision supplement (data.revision)
// or the audit results (data.audit); nothing here computes a new statistic.

export const KS = [250, 500, 1000];

export function pdfHref(data) {
  return `/${data.metadata.paper_pdf}`;
}

// Full observation (Study 1): paired contrasts, by metric and partitioning (paper Table IV)
export function fullContrastRows(data, metric, partitioning) {
  const LC = data.paper.study1.confirmatory.logreg, EX = data.paper.study1.exploratory.logreg;
  const C = data.audit.study1_20_partitions.contrasts;
  const prim = {
    C1: { ll: [LC.C1.log_loss.delta_logloss, ...LC.C1.log_loss.delta_logloss_ci], auc: [LC.C1.auc_ll_fit.delta_auc, ...LC.C1.auc_ll_fit.delta_auc_ci], ba: [LC.C1.ba.delta_ba, ...LC.C1.ba.delta_ba_ci], holm: { ll: LC.C1.log_loss.p_holm, ba: LC.C1.ba.p_holm } },
    C2: { ll: [LC.C2.log_loss.delta_logloss, ...LC.C2.log_loss.delta_logloss_ci], auc: [LC.C2.auc_ll_fit.delta_auc, ...LC.C2.auc_ll_fit.delta_auc_ci], ba: [LC.C2.ba.delta_ba, ...LC.C2.ba.delta_ba_ci], holm: { ll: LC.C2.log_loss.p_holm, ba: LC.C2.ba.p_holm } },
    C3: { ll: [LC.C3.log_loss.delta_logloss, ...LC.C3.log_loss.delta_logloss_ci], auc: [LC.C3.auc_ll_fit.delta_auc, ...LC.C3.auc_ll_fit.delta_auc_ci], ba: [LC.C3.ba.delta_ba, ...LC.C3.ba.delta_ba_ci], holm: { ll: LC.C3.log_loss.p_holm, ba: LC.C3.ba.p_holm } },
    E1: { ll: [EX.E1.delta_logloss, ...EX.E1.delta_logloss_ci], auc: [EX.E1.delta_auc_ll_fit, ...EX.E1.delta_auc_ll_fit_ci], ba: [EX.E1.delta_ba, ...EX.E1.delta_ba_ci] },
    E2: { ll: [EX.E2.delta_logloss, ...EX.E2.delta_logloss_ci], auc: [EX.E2.delta_auc_ll_fit, ...EX.E2.delta_auc_ll_fit_ci], ba: [EX.E2.delta_ba, ...EX.E2.delta_ba_ci] },
    E3: { ll: [EX.E3.delta_logloss, ...EX.E3.delta_logloss_ci], auc: [EX.E3.delta_auc_ll_fit, ...EX.E3.delta_auc_ll_fit_ci], ba: [EX.E3.delta_ba, ...EX.E3.delta_ba_ci] },
  };
  const tw = (k) => ({ ll: [C[k].dLL, ...C[k].dLL_ci], auc: [C[k].dAUC, ...C[k].dAUC_ci], ba: C[k].dBA_ci ? [C[k].dBA, ...C[k].dBA_ci] : null, fav: `${C[k].repeats_favouring_A_LL}/${C[k].n_repeats}` });
  const spec = [
    ["C1", "C1", "C1: M4 − M0q", "all features beyond counts", "primary"],
    ["C2", "C2", "C2: M2 − M1", "arrangement beyond counts + degree", "primary"],
    ["C3", "C3", "C3: M3 − M0q", "content beyond counts", "primary"],
    ["E1", "E1", "M1 − M0q", "degree concentration beyond counts", "exploratory"],
    [null, "M2_minus_M0q", "M2 − M0q", "structure beyond counts", "exploratory"],
    ["E2", "E2", "M4 − M3", "structure beyond counts + content", "exploratory"],
    ["E3", "E3", "M4 − M2", "content beyond counts + structure", "exploratory"],
    [null, "C1_text101", "C1 without the two no-text graphs", "101 events", "sensitivity"],
    [null, "C1_grouped", "C1, repeated hashtags in one fold", "grouped folds", "sensitivity"],
    [null, "tokenstd_beyond_counts", "M0q + dispersion − M0q", "token-count dispersion beyond counts", "posthoc"],
    [null, "M4_minus_counts_tokenstd", "M4 − (M0q + dispersion)", "all features beyond counts + dispersion", "posthoc"],
  ];
  const m = { log_loss: "ll", auc: "auc", ba: "ba" }[metric];
  return spec.map(([pk, tk, label, sub, status]) => {
    const src = partitioning === "primary" ? (pk ? prim[pk] : null) : tw(tk);
    const v = src && src[m];
    let note = "";
    if (partitioning === "primary" && src?.holm && m !== "auc") note = fmtP(src.holm[m]);
    if (partitioning === "twenty" && v) note = `${src.fav}`;
    return { key: tk, label, sub, status, est: v ? v[0] : null, lo: v ? v[1] : null, hi: v ? v[2] : null, extra: v ? note : "" };
  });
}

function fmtP(p) {
  return p < 0.001 ? "<0.001" : Number(p).toFixed(3);
}

// Edge-limited observation (Study 2): performance by condition and feature set (paper Table V)
export function edgeSeries(data, metric) {
  const P = data.paper, E = data.audit.edge_limited_token_std.performance;
  const pipeKey = { log_loss: "single_view_logloss_mean", auc: "single_view_auc_mean", ba: "single_view_ba_mean" }[metric];
  const audKey = { log_loss: "log_loss", auc: "auc", ba: "ba" }[metric];
  const pipe = (cond) => Object.fromEntries(KS.map((k) => [k, P.study2.results[`budget_specific_K${k}`].conditions[cond][pipeKey]]));
  const aud = (model) => Object.fromEntries(KS.map((k) => [k, E[`K${k}`].KK[model][audKey]]));
  return [
    { key: "FF", label: "Full graphs (FF), all features", color: "#9a948a", dash: "5 4", values: pipe("FF|combined") },
    { key: "A", label: "Views (KK), Nₖ alone (A)", color: "#15263a", values: pipe("KK|NK") },
    { key: "C", label: "Views (KK), Nₖ + structure (C)", color: "#23527c", values: pipe("KK|NK_struct6") },
    { key: "all", label: "Views (KK), Nₖ + structure + content", color: "#5e5a52", values: pipe("KK|combined") },
    { key: "B", label: "Views (KK), Nₖ + dispersion (B)", color: "#8f2626", dash: "2 3", values: aud("B"), posthoc: true },
    { key: "FKs", label: "Full-graph model applied to views (FK), structure", color: "#c27d38", dash: "6 3", values: pipe("FK|struct6") },
  ];
}

export function cohorts(data) {
  const EL = data.paper.eligibility;
  return Object.fromEntries(KS.map((k) => [k, { n: EL[String(k)].total_eligible, camp: EL[String(k)].campaign_eligible, comp: EL[String(k)].comparison_eligible }]));
}

// Edge-limited contrasts (paper Table VI) as interval rows for one budget
export function edgeContrastRows(data, k, metric) {
  const H = data.audit.study2_contrasts_holm.contrasts;
  const V = data.audit.edge_limited_token_std.contrasts.primary.KK;
  const pm = metric === "log_loss" ? "log_loss" : "ba";
  const pipe = (name, label, sub) => {
    const x = H[name][`K${k}`][pm];
    const h = x.p_holm_across_K;
    return { key: name, label, sub, status: "exploratory", est: x.delta, lo: x.ci[0], hi: x.ci[1], extra: h == null ? "" : fmtHolm(h, data) };
  };
  const tok = (name, label) => {
    const x = V[name][`K${k}`];
    const key = metric === "log_loss" ? "dLL" : "dBA";
    const h = metric === "log_loss" ? x.p_LL_holm_family6 : x.p_BA_holm_family6;
    return { key: name, label, sub: "token-count dispersion", status: "posthoc", est: x[key], lo: x[`${key}_ci`][0], hi: x[`${key}_ci`][1], extra: fmtHolm(h, data, 6) };
  };
  return [
    pipe("KK_minus_FF_combined", "View − full graph (KK − FF)", "all features"),
    pipe("retrain_effect_struct6", "Retraining (KK − FK)", "six structural features"),
    pipe("transfer_loss_struct6", "Transfer (FK − FF)", "six structural features"),
    pipe("structure_beyond_NK", "Structure beyond Nₖ (C − A)", "within views"),
    pipe("content_beyond_NK_struct", "Content beyond Nₖ + structure", "within views"),
    pipe("ensemble_vs_single_combined", "10-view ensemble − single view", "all features"),
    tok("B-A", "Dispersion beyond Nₖ (B − A)"),
    tok("D-C", "Dispersion beyond Nₖ + structure (D − C)"),
  ];
}

// Token-count dispersion contrasts across budgets (paper Fig. 3), KK or FF
export function dispersionRows(data, metric, condition) {
  const V = data.audit.edge_limited_token_std.contrasts.primary[condition];
  const key = metric === "log_loss" ? "dLL" : "dAUC";
  const rows = [];
  for (const name of ["B-A", "D-C"]) {
    for (const k of KS) {
      const x = V[name][`K${k}`];
      const h = metric === "log_loss" ? x.p_LL_holm_family6 : x.p_AUC_holm_family6;
      rows.push({ key: `${name}-${k}`, label: `${name === "B-A" ? "Added to Nₖ (B − A)" : "Added to Nₖ + structure (D − C)"}`, sub: `K = ${k}, n = ${x.n_events}`, status: "posthoc", est: x[key], lo: x[`${key}_ci`][0], hi: x[`${key}_ci`][1], extra: fmtHolm(h, data, 6) });
    }
  }
  return rows;
}

// Holm-adjusted p over a family of m tests (3 budgets, or 6 for the two dispersion contrasts);
// a stored bootstrap p of 0 means p < 1/n_boot, so the adjusted bound is m/n_boot
function fmtHolm(h, data, m = 3) {
  return h === 0 ? `<${(m / data.revision.study2_n_bootstrap).toFixed(3)}` : fmtP(h);
}
