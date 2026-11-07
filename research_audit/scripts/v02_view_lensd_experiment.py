"""
v02_view_lensd_experiment.py — does message-length dispersion add predictive value in fixed-K views?

Framework (unchanged from src/study2_observation.py, budget-specific cohorts K = 250, 500, 1000):
  * views: data/processed/sampled_views_v2.parquet (10 views per event, seeds 100-109); every feature
    of a view is computed from its K sampled edges only (verified by v01);
  * KK regime: for each sampling seed, LR is trained on that seed's views of the training-fold events
    and scores that seed's views of the test-fold events; every view of an event is in its event's
    fold, so no event contributes to both training and evaluation;
  * outer folds: src/splits.make_event_folds(manifest, 5, 42) restricted to the cohort (the paper's);
  * src/train.tune_logreg_C (C in {0.01, 0.1, 1, 10}, inner 3-fold) and make_logreg_pipeline (median
    imputation, standardisation, balanced LR), fitted on the training fold only; BA from BA-tuned fits,
    log loss and AUC from log-loss-tuned fits;
  * single-view estimand: metric per sampling seed, averaged over the 10 seeds;
  * uncertainty: event-level paired bootstrap (1,000 resamples, seed 7, as config study2): events are
    resampled and every seed's views of a resampled event go with it.
Feature sets: A N_K = log(1 + N_K); B A + lensd; C A + six structural features (= Study 2 "NK_struct6");
D C + lensd. lensd = msg_length_dispersion. Central contrasts: B - A and D - C. Holm across the three K,
separately for each contrast and metric.
Reference (same events and folds): FF, the same four models on the full graphs of the cohort events
(N_K replaced by full-graph log node count, lensd by its full-graph value).
Sensitivity (added, documented): the primary analysis uses one outer partition, as the framework does;
the same analysis is repeated over the paper's 10 Study 1 split seeds (42, 1-9).
Outputs: research_audit/outputs/v02_*.csv/json/png, v02.log
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from joblib import Parallel, delayed
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from splits import make_event_folds  # noqa: E402
from train import make_logreg_pipeline, tune_logreg_C  # noqa: E402
from s00_engine import auc_rows, ba_rows, contrast, holm, loss  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = ROOT / "research_audit/outputs"
CFG = yaml.safe_load(open(ROOT / "configs/v2_coreness_fix.yaml", encoding="utf-8"))
NB, BS = CFG["study2"]["n_bootstrap"], CFG["study2"]["bootstrap_seed"]
SCORING = {"ba": "balanced_accuracy", "ll": "neg_log_loss"}
STRUCT6 = ["reciprocity", "largest_wcc_fraction", "indegree_gini", "outdegree_gini", "coreness_median", "coreness_max"]
L = "msg_length_dispersion"
FSETS = {"A": ["log_node_count"], "B": ["log_node_count", L], "C": ["log_node_count"] + STRUCT6, "D": ["log_node_count"] + STRUCT6 + [L]}
NAMES = {"A": "N_K", "B": "N_K + lensd", "C": "N_K + structure", "D": "N_K + structure + lensd"}
KS = (250, 500, 1000)
PARTS = [42, 1, 2, 3, 4, 5, 6, 7, 8, 9]

man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet")
views = pd.read_parquet(ROOT / "data/processed/sampled_views_v2.parquet")
full = pd.read_parquet(ROOT / "outputs/run_v2/study1/full_graph_features.parquet")
SEEDS = sorted(views.seed.unique())


def run(K, part, fs, obj):
    """As study2_observation.run_conditions (FF and KK only) for one feature set and objective."""
    fm = make_event_folds(man, 5, part)
    ev = sorted(views[views.K == K].event_id.unique())
    y = full.loc[ev, "label"].to_numpy().astype(int)
    folds = np.array([fm[e] for e in ev])
    vk = views[views.K == K]
    vmat = {s: vk[vk.seed == s].set_index("event_id").loc[ev] for s in SEEDS}
    cols = FSETS[fs]
    Xf = full.loc[ev, cols].to_numpy()
    ff, kk = np.zeros(len(ev)), np.zeros((len(SEEDS), len(ev)))
    for k in np.unique(folds):
        tr, te = folds != k, folds == k
        C = tune_logreg_C(Xf[tr], y[tr], CFG["models"]["logreg"]["C_values"], 3, CFG, scoring=SCORING[obj])
        ff[te] = make_logreg_pipeline(CFG, C=C).fit(Xf[tr], y[tr]).predict_proba(Xf[te])[:, 1]
        for si, s in enumerate(SEEDS):
            Xv = vmat[s][cols].to_numpy()
            C = tune_logreg_C(Xv[tr], y[tr], CFG["models"]["logreg"]["C_values"], 3, CFG, scoring=SCORING[obj])
            kk[si, te] = make_logreg_pipeline(CFG, C=C).fit(Xv[tr], y[tr]).predict_proba(Xv[te])[:, 1]
    return ff, kk


jobs = [(K, p, fs, o) for K in KS for p in PARTS for fs in FSETS for o in SCORING]
print(f"{len(jobs)} jobs", flush=True)
res = dict(zip(jobs, Parallel(n_jobs=-1)(delayed(run)(*j) for j in jobs)))
EV = {K: sorted(views[views.K == K].event_id.unique()) for K in KS}
Y = {K: full.loc[EV[K], "label"].to_numpy().astype(int) for K in KS}
np.savez_compressed(OUT / "v02_predictions.npz", **{f"K{K}|part{p}|{fs}|{o}|{c}": res[(K, p, fs, o)][i]
                                                     for (K, p, fs, o) in res for i, c in enumerate(("FF", "KK"))})

# ---- validation: A and C under KK and FF (partition 42) must equal the stored Study 2 predictions
vp = pd.read_parquet(ROOT / "outputs/run_v2/study2/view_predictions.parquet")
vp = vp[vp.cohort == "budget_specific"]
chk = {}
for K in KS:
    for fs, name in (("A", "NK"), ("C", "NK_struct6")):
        for o in SCORING:
            for ci, cond in enumerate(("FF", "KK")):
                s = vp[(vp.K == K) & (vp.condition == cond) & (vp.featureset == name) & (vp.objective == o)]
                M = s.pivot(index="seed_index", columns="event_id", values="prob_campaign")[EV[K]].to_numpy()
                mine = res[(K, 42, fs, o)][ci]
                mine = np.tile(mine, (10, 1)) if cond == "FF" else mine
                chk[f"K{K}|{cond}|{name}|{o}"] = float(np.abs(M - mine).max())
print("max |diff| vs stored Study 2 predictions:", max(chk.values()), flush=True)


def P(K, fs, o, cond="KK", parts=(42,)):
    m = [res[(K, p, fs, o)][1] if cond == "KK" else res[(K, p, fs, o)][0][None] for p in parts]
    return np.vstack(m)


# ---- performance and contrasts (primary: partition 42)
perf, rows = [], []
for K in KS:
    y = Y[K]
    for cond in ("KK", "FF"):
        for fs in FSETS:
            pl, pb = P(K, fs, "ll", cond), P(K, fs, "ba", cond)
            ll, au, ba = loss(y, pl).mean(1), auc_rows(y, pl), ba_rows(y, pb)
            perf.append({"K": K, "condition": cond, "model": fs, "features": NAMES[fs], "n_events": len(y), "n_campaign": int(y.sum()),
                         "log_loss": float(ll.mean()), "log_loss_seed_min": float(ll.min()), "log_loss_seed_max": float(ll.max()),
                         "auc": float(au.mean()), "auc_seed_min": float(au.min()), "auc_seed_max": float(au.max()),
                         "ba": float(ba.mean()), "ba_seed_min": float(ba.min()), "ba_seed_max": float(ba.max())})
        for a, b in (("B", "A"), ("D", "C")):
            c = contrast(y, P(K, a, "ll", cond), P(K, b, "ll", cond), P(K, a, "ba", cond), P(K, b, "ba", cond), n_boot=NB, seed=BS)
            rows.append({"analysis": "primary (partition 42)", "K": K, "condition": cond, "contrast": f"{a} - {b}",
                         "description": f"{NAMES[a]} vs {NAMES[b]}", **c})
        # sensitivity: 10 outer partitions (KK only; FF has one view-independent fit per partition)
        if cond == "KK":
            for a, b in (("B", "A"), ("D", "C")):
                c = contrast(y, P(K, a, "ll", cond, PARTS), P(K, b, "ll", cond, PARTS), P(K, a, "ba", cond, PARTS), P(K, b, "ba", cond, PARTS),
                             n_boot=NB, seed=BS)
                per = [float((loss(y, P(K, a, "ll", cond, (p,))) - loss(y, P(K, b, "ll", cond, (p,)))).mean()) for p in PARTS]
                per_auc = [float((auc_rows(y, P(K, a, "ll", cond, (p,))) - auc_rows(y, P(K, b, "ll", cond, (p,)))).mean()) for p in PARTS]
                rows.append({"analysis": "sensitivity (10 partitions)", "K": K, "condition": cond, "contrast": f"{a} - {b}",
                             "description": f"{NAMES[a]} vs {NAMES[b]}", **c,
                             "partition_dLL": per, "partitions_favouring_A_LL": int(sum(d < 0 for d in per)),
                             "partition_dAUC": per_auc, "partitions_favouring_A_AUC": int(sum(d > 0 for d in per_auc))})
PERF = pd.DataFrame(perf)
CT = pd.DataFrame(rows)
for (an, cond, con), g in CT.groupby(["analysis", "condition", "contrast"]):
    for m in ("LL", "AUC", "BA"):
        h = holm({K: p for K, p in zip(g.K, g[f"p_{m}"])})
        CT.loc[g.index, f"p_{m}_holm_across_K"] = [h[K] for K in g.K]
PERF.to_csv(OUT / "v02_performance.csv", index=False)
flat = CT.copy()
for c in ("dLL_ci", "dAUC_ci", "dBA_ci"):
    flat[c] = flat[c].map(lambda v: f"[{v[0]:+.3f}, {v[1]:+.3f}]")
flat.to_csv(OUT / "v02_contrasts.csv", index=False)
print(PERF.round(3).to_string(index=False), flush=True)
for _, r in CT.iterrows():
    print(f"{r.analysis[:11]:11s} K={r.K:4d} {r.condition} {r.contrast} dLL {r.dLL:+.3f} [{r.dLL_ci[0]:+.3f}, {r.dLL_ci[1]:+.3f}] holm {r.p_LL_holm_across_K:.3f} | "
          f"dAUC {r.dAUC:+.3f} [{r.dAUC_ci[0]:+.3f}, {r.dAUC_ci[1]:+.3f}] holm {r.p_AUC_holm_across_K:.3f} | dBA {r.dBA:+.3f} [{r.dBA_ci[0]:+.3f}, {r.dBA_ci[1]:+.3f}] "
          f"holm {r.p_BA_holm_across_K:.3f} | seeds/partitions favouring A (LL) {r.repeats_favouring_A_LL}/{r.n_repeats}", flush=True)

# ---- descriptive: view lensd vs full-graph lensd, and class separation of lensd in views
v01 = pd.read_csv(OUT / "v01_view_text.csv")
desc = {}
for K in KS:
    g = v01[v01.K == K].groupby("event_id").agg(view_lensd=("lensd_stored", "mean"), label=("label", "first"))
    g["full_lensd"] = full.loc[g.index, L]
    ok = g.dropna()
    vk = v01[(v01.K == K) & v01.lensd_stored.notna()]
    seed_auc = [float(auc_rows(1 - s.label.to_numpy(), s.lensd_stored.to_numpy()[None])[0]) for _, s in vk.groupby("seed")]
    desc[str(K)] = {"events_with_defined_lensd": int(len(ok)), "spearman_view_mean_vs_full": float(spearmanr(ok.view_lensd, ok.full_lensd)[0]),
                    "median_abs_view_minus_full": float((ok.view_lensd - ok.full_lensd).abs().median()),
                    "auc_lensd_for_comparison_single_view_mean": float(np.mean(seed_auc)),
                    "auc_lensd_for_comparison_full_graph": float(auc_rows(1 - ok.label.to_numpy(), ok.full_lensd.to_numpy()[None])[0]),
                    "within_event_sd_of_view_lensd_median": float(vk.groupby("event_id").lensd_stored.std().median())}
print("descriptive:", json.dumps(desc, indent=1), flush=True)

# ---- figures (validated default categorical slots: blue = comparison, orange = campaign)
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#222222", "#8a8a85"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUTED})

# Fig 1: text availability per view
fig, ax = plt.subplots(figsize=(7, 3.4))
pos, data, cols = [], [], []
for i, K in enumerate(KS):
    for j, (lab, col) in enumerate(((0, BLUE), (1, ORANGE))):
        pos.append(i * 3 + j)
        data.append(v01[(v01.K == K) & (v01.label == lab)].usable_share.to_numpy())
        cols.append(col)
bp = ax.boxplot(data, positions=pos, widths=0.7, patch_artist=True, showfliers=True, flierprops={"markersize": 2, "markeredgecolor": MUTED},
                medianprops={"color": INK})
for patch, c in zip(bp["boxes"], cols):
    patch.set_facecolor(c)
    patch.set_edgecolor(INK)
ax.set_xticks([0.5, 3.5, 6.5])
ax.set_xticklabels([f"K = {K}\n{len(EV[K])} events\n{int(Y[K].sum())} campaign / {len(EV[K]) - int(Y[K].sum())} comparison" for K in KS], fontsize=8)
ax.set_ylabel("share of the K sampled edges\nwith usable message text")
ax.set_ylim(-0.03, 1.15)
ax.legend([bp["boxes"][0], bp["boxes"][1]], ["comparison views", "campaign views"], frameon=False, fontsize=8, loc="upper center", ncol=2)
ax.set_title("Text availability in Study 2 views (10 views per event)", fontsize=10, loc="left")
fig.tight_layout()
fig.savefig(OUT / "v02_fig1_text_availability.png", dpi=200)
v01[["K", "seed", "event_id", "label", "n_usable_text", "usable_share"]].to_csv(OUT / "v02_fig1_data.csv", index=False)

# Fig 2: paired contrasts by K
fig, ax = plt.subplots(1, 3, figsize=(10, 3.6))
pr = CT[CT.analysis.str.startswith("primary")]
lab_off = {("B - A", "KK"): -0.27, ("D - C", "KK"): -0.09, ("B - A", "FF"): 0.09, ("D - C", "FF"): 0.27}
styles = {("B - A", "KK"): (ORANGE, "o", "lensd beyond N_K (views)"), ("D - C", "KK"): (BLUE, "o", "lensd beyond N_K + structure (views)"),
          ("B - A", "FF"): (ORANGE, "s", "lensd beyond N_K (full graphs, ref.)"),
          ("D - C", "FF"): (BLUE, "s", "lensd beyond N_K + structure (full graphs, ref.)")}
for a, (m, lab) in zip(ax, (("dLL", "Δ log loss (lower favours lensd)"), ("dAUC", "Δ AUC (higher favours lensd)"), ("dBA", "Δ balanced accuracy"))):
    for (con, cond), (col, mk, nm) in styles.items():
        g = pr[(pr.contrast == con) & (pr.condition == cond)].set_index("K").loc[list(KS)]
        x = np.arange(3) + lab_off[(con, cond)]
        a.errorbar(x, g[m], yerr=[g[m] - g[f"{m}_ci"].str[0], g[f"{m}_ci"].str[1] - g[m]], fmt=mk, color=col, ms=5, capsize=2,
                   mfc=col if cond == "KK" else "white", label=nm)
    a.axhline(0, color=MUTED, lw=0.8)
    a.set_xticks(range(3))
    a.set_xticklabels([f"K={K}" for K in KS])
    a.set_ylabel(lab)
h_, l_ = ax[0].get_legend_handles_labels()
fig.legend(h_, l_, fontsize=7.5, frameon=False, loc="lower center", ncol=4)
fig.suptitle("Adding message-length dispersion: paired differences, budget-specific cohorts, 95% event bootstrap", fontsize=10)
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig(OUT / "v02_fig2_contrasts.png", dpi=200)
pr.drop(columns=[c for c in pr.columns if c.startswith("partition")], errors="ignore").to_csv(OUT / "v02_fig2_data.csv", index=False)

# Fig 3: view lensd vs full-graph lensd
fig, ax = plt.subplots(1, 3, figsize=(10, 3.3), sharey=True)
for a, K in zip(ax, KS):
    g = v01[v01.K == K].groupby("event_id").agg(view_lensd=("lensd_stored", "mean"), label=("label", "first"))
    g["full_lensd"] = full.loc[g.index, L]
    for lab, col, nm in ((0, BLUE, "comparison"), (1, ORANGE, "campaign")):
        h = g[g.label == lab]
        a.scatter(h.full_lensd, h.view_lensd, s=14, color=col, edgecolor="white", linewidth=0.5, label=nm)
    lim = [0, 16]
    a.plot(lim, lim, color=MUTED, lw=0.8)
    a.set_xlim(lim)
    a.set_ylim(lim)
    a.set_xlabel("full-graph message-length SD (tokens)")
    a.set_title(f"K = {K} ({len(g)} events)", fontsize=9)
ax[0].set_ylabel("mean over 10 views of\nview message-length SD (tokens)")
ax[0].legend(fontsize=7, frameon=False)
fig.tight_layout()
fig.savefig(OUT / "v02_fig3_view_vs_full.png", dpi=200)


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


(OUT / "v02_results.json").write_text(json.dumps(clean({"validation_max_abs_diff_vs_stored_study2": chk, "performance": PERF.to_dict("records"),
                                                        "contrasts": CT.to_dict("records"), "descriptive_lensd": desc, "feature_sets": FSETS}),
                                                 indent=2), encoding="utf-8")
