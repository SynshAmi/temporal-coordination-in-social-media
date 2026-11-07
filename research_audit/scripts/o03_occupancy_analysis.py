"""
o03_occupancy_analysis.py — EXPLORATORY reproduction: does expected endpoint occupancy E[N_K] carry
label information beyond graph counts in the analysed 103-graph archive?

K = 250 was chosen after earlier results were seen, so this is not a confirmatory test. All contrasts
below were fixed in this script before it was run; no multiplicity correction except where stated.

Input: research_audit/outputs/o02_features.csv (computed from the raw archive).

Configurations
  A (primary)      102 events with m >= 250 (E[N_250] defined without clipping).
                   Logistic regression: StandardScaler + LogisticRegression(class_weight="balanced"),
                   C tuned by GridSearchCV over 10^{-3..3} (7 values) with inner StratifiedKFold(3, shuffle,
                   seed 0) on neg log loss, inside each outer training fold. BA at threshold 0.5 from the same
                   fit. 20 repeats of StratifiedKFold(5, shuffle, seed 1000 + r); identical splits for all models.
  B (pilot spec)   the external pilot's specification, reimplemented here: all 103 events with
                   K = min(250, m); C over 10^{-3..3} (9 values); outer seeds 100 + r. Same model otherwise.
  K-sensitivity    counts vs counts + log E[N_K] for K = 500 (98 events) and K = 1000 (73 events),
                   each on its own eligible events; Holm correction across the three K for that contrast.

Uncertainty
  - Repeat-level: mean over 20 repeats of the pooled out-of-fold metric; SD across repeats; for paired
    differences the Nadeau–Bengio corrected resampled t interval (variance factor 1/20 + 1/4).
  - Event-level: AUC / log loss / BA of the repeat-averaged out-of-fold probabilities, with an event
    bootstrap (2,000 resamples, seed 7) for paired differences.
  - Fold-level: SD of per-fold AUC and log loss over the 100 folds; share of folds with a positive paired
    AUC difference.
  Neither interval accounts for variation across independent datasets: the 102 events are the only units.

Outputs: research_audit/outputs/o03_*.csv / .json and figures o03_fig*.png (+ plotting data CSVs).
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research_audit/outputs"
F0 = pd.read_csv(OUT / "o02_features.csv")
EPS = 1e-6
R = 20


def design(F, Ecol):
    X = pd.DataFrame(index=F.index)
    X["log_n"], X["log_m"] = np.log1p(F.n), np.log1p(F.m)
    X["log_n_sq"], X["log_m_sq"], X["log_n_x_m"] = X.log_n ** 2, X.log_m ** 2, X.log_n * X.log_m
    X["log_E"] = np.log(F[Ecol])
    X["log_hom_binom"] = np.log(F.hom_binom)
    if F.hom_hyper.notna().all():
        X["log_hom_hyper"] = np.log(F.hom_hyper)
    X["gini_in"], X["gini_out"] = F.gini_in, F.gini_out
    X["log_sum_d2"], X["deg1_frac"] = np.log(F.sum_d2), F.deg1_frac
    return X


COUNTS = ["log_n", "log_m"]
MODELS = {
    "counts": COUNTS,
    "counts + nonlinear": COUNTS + ["log_n_sq", "log_m_sq", "log_n_x_m"],
    "E[N_K] alone": ["log_E"],
    "counts + E[N_K]": COUNTS + ["log_E"],
    "counts + degree Gini": COUNTS + ["gini_in", "gini_out"],
    "counts + Σd² + degree-1 frac": COUNTS + ["log_sum_d2", "deg1_frac"],
    "homogeneous approx. (pilot)": ["log_hom_binom"],
    "QDA on counts": COUNTS,  # comparison with the pilot only
}
CONTRASTS = [("counts + E[N_K]", "counts"), ("E[N_K] alone", "counts"), ("counts + E[N_K]", "counts + degree Gini"),
             ("counts + E[N_K]", "counts + Σd² + degree-1 frac"), ("counts + Σd² + degree-1 frac", "counts"),
             ("counts + degree Gini", "counts"), ("counts + nonlinear", "counts"), ("E[N_K] alone", "homogeneous approx. (pilot)")]


def make(name, Cs):
    if name.startswith("QDA"):
        return make_pipeline(StandardScaler(), QuadraticDiscriminantAnalysis(reg_param=0.0))
    lr = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=5000))
    return GridSearchCV(lr, {"logisticregression__C": Cs}, cv=StratifiedKFold(3, shuffle=True, random_state=0), scoring="neg_log_loss")


def run(X, y, models, seeds, Cs):
    P = {k: np.zeros((len(seeds), len(y))) for k in models}
    fold = {k: [] for k in models}  # per-fold (repeat, auc, ll)
    for r, sd in enumerate(seeds):
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=sd).split(X, y):
            for k, cols in models.items():
                mdl = make(k, Cs).fit(X[cols].values[tr], y[tr])
                p = np.clip(mdl.predict_proba(X[cols].values[te])[:, 1], EPS, 1 - EPS)
                P[k][r, te] = p
                fold[k].append((r, roc_auc_score(y[te], p) if len(set(y[te])) > 1 else np.nan, log_loss(y[te], p, labels=[0, 1])))
    return P, fold


def per_repeat(P, y):
    return {k: np.array([[balanced_accuracy_score(y, p >= .5), roc_auc_score(y, p), log_loss(y, p)] for p in v]) for k, v in P.items()}


def nb_interval(d, J):
    se = np.sqrt((1 / J + 0.25) * d.var(ddof=1))
    t = stats.t.ppf(0.975, J - 1)
    return [float(d.mean() - t * se), float(d.mean() + t * se)]


def event_boot(y, pa, pb, B=2000, seed=7):
    rng = np.random.default_rng(seed)
    la = -(y * np.log(pa) + (1 - y) * np.log(1 - pa))
    lb = -(y * np.log(pb) + (1 - y) * np.log(1 - pb))
    da, dl, dbal = [], [], []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) < 2:
            continue
        da.append(roc_auc_score(y[i], pa[i]) - roc_auc_score(y[i], pb[i]))
        dl.append(la[i].mean() - lb[i].mean())
        dbal.append(balanced_accuracy_score(y[i], pa[i] >= .5) - balanced_accuracy_score(y[i], pb[i] >= .5))
    da, dl, dbal = map(np.array, (da, dl, dbal))
    p_auc = float(min(1, 2 * min((da <= 0).mean(), (da >= 0).mean())))
    return {"dAUC": float(roc_auc_score(y, pa) - roc_auc_score(y, pb)), "dAUC_ci": np.percentile(da, [2.5, 97.5]).tolist(), "p_dAUC": p_auc,
            "dLL": float(la.mean() - lb.mean()), "dLL_ci": np.percentile(dl, [2.5, 97.5]).tolist(),
            "dBA": float(balanced_accuracy_score(y, pa >= .5) - balanced_accuracy_score(y, pb >= .5)), "dBA_ci": np.percentile(dbal, [2.5, 97.5]).tolist(),
            "per_event_dLL": (la - lb).tolist()}


def summarise(tag, F, X, y, P, fold, contrasts):
    M = per_repeat(P, y)
    perf = {}
    for k in P:
        pa = P[k].mean(0)
        f = np.array([(a, l) for _, a, l in fold[k]], float)
        perf[k] = {"BA_mean": M[k][:, 0].mean(), "BA_sd": M[k][:, 0].std(ddof=1), "AUC_mean": M[k][:, 1].mean(), "AUC_sd": M[k][:, 1].std(ddof=1),
                   "LL_mean": M[k][:, 2].mean(), "LL_sd": M[k][:, 2].std(ddof=1),
                   "AUC_avgprob": roc_auc_score(y, pa), "LL_avgprob": log_loss(y, pa), "BA_avgprob": balanced_accuracy_score(y, pa >= .5),
                   "fold_AUC_sd": float(np.nanstd(f[:, 0], ddof=1)), "fold_LL_sd": float(np.std(f[:, 1], ddof=1))}
    con = {}
    for a, b in contrasts:
        d = M[a] - M[b]
        eb = event_boot(y, P[a].mean(0), P[b].mean(0))
        fa = np.array([x[1] for x in fold[a]]); fb = np.array([x[1] for x in fold[b]])
        con[f"{a} − {b}"] = {"repeat_mean": {"dBA": d[:, 0].mean(), "dAUC": d[:, 1].mean(), "dLL": d[:, 2].mean()},
                             "NB_ci": {"dBA": nb_interval(d[:, 0], len(d)), "dAUC": nb_interval(d[:, 1], len(d)), "dLL": nb_interval(d[:, 2], len(d))},
                             "repeats_dAUC_positive": int((d[:, 1] > 0).sum()), "repeats_dLL_negative": int((d[:, 2] < 0).sum()),
                             "folds_dAUC_positive_share": float(np.nanmean(fa - fb > 0)),
                             "event_bootstrap": {k: v for k, v in eb.items() if k != "per_event_dLL"},
                             "events_improved_LL": int((np.array(eb["per_event_dLL"]) < 0).sum()), "n_events": len(y)}
        con[f"{a} − {b}"]["_per_event_dLL"] = eb["per_event_dLL"]
    return {"config": tag, "n_events": int(len(y)), "n_campaign": int(y.sum()), "performance": perf, "contrasts": con}


results = {}
# ---------------- Configuration A (primary)
FA = F0[F0.m >= 250].reset_index(drop=True)
XA, yA = design(FA, "E250"), FA.label.values.astype(int)
CsA = list(np.logspace(-3, 3, 7))
PA, foldA = run(XA, yA, MODELS, [1000 + r for r in range(R)], CsA)
results["A"] = summarise("A: 102 events, m >= 250", FA, XA, yA, PA, foldA, CONTRASTS)
print("A done", flush=True)

# ---------------- Configuration B (pilot specification, reimplemented)
XB, yB = design(F0, "E250_clip"), F0.label.values.astype(int)
models_B = {k: v for k, v in MODELS.items()}
PB, foldB = run(XB, yB, models_B, [100 + r for r in range(R)], list(np.logspace(-3, 3, 9)))
results["B"] = summarise("B: pilot spec, 103 events, K = min(250, m)", F0, XB, yB, PB, foldB,
                         [("E[N_K] alone", "counts"), ("E[N_K] alone", "homogeneous approx. (pilot)"), ("counts + E[N_K]", "counts")])
print("B done", flush=True)

# ---------------- K sensitivity (Holm across K for counts + E vs counts, event-bootstrap p for dAUC)
ksens = {}
for K in (250, 500, 1000):
    FK = F0[F0.m >= K].reset_index(drop=True)
    XK, yK = design(FK, f"E{K}"), FK.label.values.astype(int)
    sub = {"counts": COUNTS, "counts + E[N_K]": COUNTS + ["log_E"], "E[N_K] alone": ["log_E"]}
    PK, foldK = run(XK, yK, sub, [1000 + r for r in range(R)], CsA) if K != 250 else ({k: PA[k] for k in sub}, {k: foldA[k] for k in sub})
    s = summarise(f"K={K}", FK, XK, yK, PK, foldK, [("counts + E[N_K]", "counts"), ("E[N_K] alone", "counts")])
    ksens[K] = s
ps = sorted(((ksens[K]["contrasts"]["counts + E[N_K] − counts"]["event_bootstrap"]["p_dAUC"], K) for K in ksens))
holm, running = {}, 0.0
for rank, (p, K) in enumerate(ps):
    running = max(running, min(1.0, (len(ps) - rank) * p))
    holm[K] = running
for K in ksens:
    ksens[K]["holm_p_dAUC_countsE_vs_counts"] = holm[K]
results["K_sensitivity"] = ksens


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, list):
        return [clean(v) for v in o]
    return o


(OUT / "o03_results.json").write_text(json.dumps(clean(results), indent=2, ensure_ascii=False), encoding="utf-8")
rows = []
for cfg in ("A", "B"):
    for k, v in results[cfg]["performance"].items():
        rows.append({"config": cfg, "model": k, **v})
pd.DataFrame(rows).to_csv(OUT / "o03_performance.csv", index=False, encoding="utf-8")
crow = []
for cfg in ("A", "B"):
    for k, v in results[cfg]["contrasts"].items():
        eb, nb = v["event_bootstrap"], v["NB_ci"]
        crow.append({"config": cfg, "contrast": k, "dAUC_repeat_mean": v["repeat_mean"]["dAUC"], "dAUC_NB_lo": nb["dAUC"][0], "dAUC_NB_hi": nb["dAUC"][1],
                     "dAUC_avgprob": eb["dAUC"], "dAUC_boot_lo": eb["dAUC_ci"][0], "dAUC_boot_hi": eb["dAUC_ci"][1],
                     "dLL_repeat_mean": v["repeat_mean"]["dLL"], "dLL_NB_lo": nb["dLL"][0], "dLL_NB_hi": nb["dLL"][1],
                     "dLL_boot_lo": eb["dLL_ci"][0], "dLL_boot_hi": eb["dLL_ci"][1],
                     "dBA_repeat_mean": v["repeat_mean"]["dBA"], "dBA_NB_lo": nb["dBA"][0], "dBA_NB_hi": nb["dBA"][1],
                     "repeats_dAUC_pos": v["repeats_dAUC_positive"], "folds_dAUC_pos_share": v["folds_dAUC_positive_share"],
                     "events_improved_LL": v["events_improved_LL"], "n_events": v["n_events"]})
pd.DataFrame(crow).to_csv(OUT / "o03_contrasts.csv", index=False, encoding="utf-8")

# ---------------- Figures (configuration A data)
CAMP, COMP = "#8f2626", "#23527c"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

# Fig 1: E[N_250] vs m
d1 = FA[["event_id", "label", "n", "m", "E250"]].copy()
d1.to_csv(OUT / "o03_fig1_data.csv", index=False, encoding="utf-8")
fig, ax = plt.subplots(figsize=(6, 4.2))
for lab, c, nm in ((1, CAMP, "campaign"), (0, COMP, "comparison")):
    s = d1[d1.label == lab]
    ax.scatter(s.m, s.E250, s=18, c=c, alpha=.8, label=f"{nm} (n={len(s)})", edgecolors="none")
mm = np.logspace(np.log10(250), np.log10(d1.m.max()), 100)
ax.plot(mm, np.full_like(mm, 250 * 2), color="#999", lw=.8, ls=":", label="upper bound 2K = 500")
ax.set_xscale("log"); ax.set_xlabel("Edge count m of the full graph (log scale)")
ax.set_ylabel("Expected distinct endpoints E[N_250] (nodes)")
ax.set_title("Expected endpoint occupancy vs graph size (K = 250, 102 events)", fontsize=9)
ax.legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(OUT / "o03_fig1_occupancy_vs_m.png", dpi=160); plt.close(fig)

# Fig 2: AUC by model with intervals (A)
order = ["counts", "counts + nonlinear", "counts + degree Gini", "counts + Σd² + degree-1 frac", "homogeneous approx. (pilot)", "E[N_K] alone", "counts + E[N_K]", "QDA on counts"]
rng = np.random.default_rng(7)
rows2 = []
for k in order:
    pa = PA[k].mean(0)
    bs = []
    for _ in range(2000):
        i = rng.integers(0, len(yA), len(yA))
        if len(set(yA[i])) > 1:
            bs.append(roc_auc_score(yA[i], pa[i]))
    rep = per_repeat({k: PA[k]}, yA)[k][:, 1]
    rows2.append({"model": k, "AUC_avgprob": roc_auc_score(yA, pa), "boot_lo": np.percentile(bs, 2.5), "boot_hi": np.percentile(bs, 97.5),
                  "AUC_repeat_mean": rep.mean(), "repeat_min": rep.min(), "repeat_max": rep.max()})
d2 = pd.DataFrame(rows2); d2.to_csv(OUT / "o03_fig2_data.csv", index=False, encoding="utf-8")
fig, ax = plt.subplots(figsize=(6.4, 4.2))
yy = np.arange(len(d2))[::-1]
ax.errorbar(d2.AUC_avgprob, yy, xerr=[d2.AUC_avgprob - d2.boot_lo, d2.boot_hi - d2.AUC_avgprob], fmt="o", color="#15263a", ms=4, capsize=2, lw=1, label="AUC of repeat-averaged OOF probabilities, 95% event bootstrap")
ax.hlines(yy - .18, d2.repeat_min, d2.repeat_max, color="#c27d38", lw=2.5, label="range over 20 CV repeats")
ax.set_yticks(yy); ax.set_yticklabels(d2.model, fontsize=8)
ax.set_xlabel("Out-of-fold ROC-AUC (campaign vs comparison)")
ax.set_title("Predictive ranking by feature set (102 events, K = 250; exploratory)", fontsize=9)
ax.legend(frameon=False, fontsize=7, loc="lower left")
fig.tight_layout(); fig.savefig(OUT / "o03_fig2_auc_by_model.png", dpi=160); plt.close(fig)

# Fig 3: degree-sequence alternatives vs size and label
res_E = XA.log_E - np.polyval(np.polyfit(XA.log_n, XA.log_E, 1), XA.log_n)  # placeholder, replaced below
Z = np.column_stack([np.ones(len(XA)), XA.log_n, XA.log_m])
beta, *_ = np.linalg.lstsq(Z, XA.log_E, rcond=None)
res_E = XA.log_E - Z @ beta
d3 = FA[["event_id", "label", "n", "m", "E250", "sum_d2", "deg1_frac"]].copy()
d3["log_E_resid_on_log_n_log_m"] = res_E.values
d3.to_csv(OUT / "o03_fig3_data.csv", index=False, encoding="utf-8")
fig, axs = plt.subplots(2, 2, figsize=(8.2, 6.4))
panels = [("E250", "E[N_250] (nodes, log scale)", True), ("sum_d2", "Σ d_v² (log scale)", True), ("deg1_frac", "Share of nodes with d_v = 1", False)]
for ax, (col, lab, logy) in zip(axs.flat[:3], panels):
    for l, c, nm in ((1, CAMP, "campaign"), (0, COMP, "comparison")):
        s = d3[d3.label == l]
        ax.scatter(s.n, s[col], s=12, c=c, alpha=.8, edgecolors="none", label=nm)
    ax.set_xscale("log"); ax.set_xlabel("Node count n (log scale)"); ax.set_ylabel(lab, fontsize=8)
    if logy:
        ax.set_yscale("log")
axs.flat[0].legend(frameon=False, fontsize=7)
ax = axs.flat[3]
for l, c, x0 in ((1, CAMP, 1), (0, COMP, 0)):
    v = d3.loc[d3.label == l, "log_E_resid_on_log_n_log_m"]
    ax.scatter(np.full(len(v), x0) + np.random.default_rng(l).uniform(-.12, .12, len(v)), v, s=12, c=c, alpha=.8, edgecolors="none")
    ax.hlines(v.median(), x0 - .25, x0 + .25, color=c, lw=2)
ax.set_xticks([0, 1]); ax.set_xticklabels(["comparison", "campaign"])
ax.set_ylabel("Residual of log E[N_250] on log n, log m", fontsize=8)
ax.axhline(0, color="#999", lw=.6, ls=":")
fig.suptitle("Degree-sequence summaries vs graph size and label (102 events, raw values; residual from OLS on all events)", fontsize=8.5)
fig.tight_layout(); fig.savefig(OUT / "o03_fig3_degree_summaries.png", dpi=160); plt.close(fig)

# console summary
for cfg in ("A", "B"):
    print(f"\n=== {results[cfg]['config']} ===")
    print(pd.DataFrame(results[cfg]["performance"]).T[["BA_mean", "BA_sd", "AUC_mean", "AUC_sd", "LL_mean", "LL_sd", "AUC_avgprob", "fold_AUC_sd"]].round(3).to_string())
    for k, v in results[cfg]["contrasts"].items():
        eb = v["event_bootstrap"]
        print(f"{k:58s} dAUC rep {v['repeat_mean']['dAUC']:+.3f} NB [{v['NB_ci']['dAUC'][0]:+.3f},{v['NB_ci']['dAUC'][1]:+.3f}] | boot {eb['dAUC']:+.3f} [{eb['dAUC_ci'][0]:+.3f},{eb['dAUC_ci'][1]:+.3f}]"
              f" | dLL rep {v['repeat_mean']['dLL']:+.3f} NB [{v['NB_ci']['dLL'][0]:+.3f},{v['NB_ci']['dLL'][1]:+.3f}] boot [{eb['dLL_ci'][0]:+.3f},{eb['dLL_ci'][1]:+.3f}]"
              f" | dBA rep {v['repeat_mean']['dBA']:+.3f} NB [{v['NB_ci']['dBA'][0]:+.3f},{v['NB_ci']['dBA'][1]:+.3f}] | folds+ {v['folds_dAUC_positive_share']:.2f} | LL-improved events {v['events_improved_LL']}/{v['n_events']}")
print("\n=== K sensitivity (counts + E[N_K] − counts) ===")
for K, s in ksens.items():
    v = s["contrasts"]["counts + E[N_K] − counts"]
    eb = v["event_bootstrap"]
    print(f"K={K} n={s['n_events']}: dAUC boot {eb['dAUC']:+.3f} [{eb['dAUC_ci'][0]:+.3f},{eb['dAUC_ci'][1]:+.3f}] p={eb['p_dAUC']:.3f} Holm={s['holm_p_dAUC_countsE_vs_counts']:.3f}; NB {v['NB_ci']['dAUC']} | dLL boot [{eb['dLL_ci'][0]:+.3f},{eb['dLL_ci'][1]:+.3f}]")
