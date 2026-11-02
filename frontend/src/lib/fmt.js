// Number formatting shared by every page; mirrors the paper's LaTeX macros (src/export_latex_results.py)
// so the website and the paper print identical values.
const minus = (t) => t.replace(/^-/, "−");

export const f3 = (v) => (v == null ? "—" : minus(Number(v).toFixed(3)));
export const f2 = (v) => (v == null ? "—" : minus(Number(v).toFixed(2)));
export const pct = (v) => (100 * v).toFixed(1);
export const pct0 = (v) => Math.round(100 * v);
export const sg = (v) => (Math.abs(v) < 0.0005 ? "0.000" : (v > 0 ? "+" : "−") + Math.abs(v).toFixed(3));
export const ci = (a) => `[${sg(a[0])}, ${sg(a[1])}]`;
export const ciu = (a) => `[${f3(a[0])}, ${f3(a[1])}]`;
export const pv = (p) => (p < 0.001 ? "<0.001" : f3(p));
export const int = (v) => Math.round(v).toLocaleString("en-US");

// Largest upper BA interval bound among the primary contrasts ("gains of up to about ...")
export const baMaxHi = (P) => Math.max(...["C1", "C2", "C3"].map((k) => P.study1.confirmatory.logreg[k].ba.delta_ba_ci[1]));

// Study 2 accessors
export const cond = (P, k, key, cohort = "budget_specific") => P.study2.results[`${cohort}_K${k}`].conditions[key];
export const con = (P, k, name, cohort = "budget_specific") => P.study2.contrasts[`${cohort}_K${k}`][name];

// Revision supplement accessors: single view minus full graph (same events, same features), and N_K vs structure
export const vmf = (V, k, fs = "combined", cohort = "budget_specific") => V.rq2_baselines[`${cohort}_K${k}`][`KK_minus_FF_${fs}`];
export const nkVsStruct = (V, k) => V.nk_vs_structure[`K${k}`];
export const proxyR2 = (V, k) => V.structure_predicts_log_NK[`K${k}`].r2_event_grouped_cv;
