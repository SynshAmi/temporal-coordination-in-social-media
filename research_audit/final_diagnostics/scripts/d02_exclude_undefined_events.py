"""
d02_exclude_undefined_events.py — Check 2: do the two campaign events with no usable text (token_std undefined,
median-imputed in training) materially affect the v02 comparisons B - A and D - C?

Events (both label 1 = campaign in manifest and full-graph features; full-graph token_std also undefined):
  Tapuma_YapıKayıt___2023-04-19_campaign_fulldata      (1,186 edges: in the K = 250, 500 and 1000 cohorts)
  YapıKayıt_YoksaOyyok___2023-05-01_campaign_fulldata   (546 edges: in the K = 250 and 500 cohorts)

Procedure: identical to research_audit/scripts/v02_view_lensd_experiment.py (whose run() is copied verbatim
below, with one added argument, `exclude`), applied to each budget-specific cohort minus these events:
  same feature sets A-D, budgets, sampling seeds 100-109 (stored views), outer folds
  src/splits.make_event_folds(manifest, 5, part) restricted to the remaining events (each remaining event keeps
  its original fold), src/train.tune_logreg_C / make_logreg_pipeline fitted on the training fold only, BA from
  BA-tuned and log loss/AUC from log-loss-tuned fits, single-view estimand averaged over seeds, event-level
  paired bootstrap (1,000 resamples, seed 7) via s00_engine.contrast, Holm across the three K per contrast,
  metric and analysis. Primary: partition 42; sensitivity: partitions 42, 1-9 (as v02).
Validation: with exclude = () this code reproduces research_audit/outputs/v02_predictions.npz exactly.
Also reported (secondary, no refit): the original v02 predictions scored with the two events removed, which
separates the effect of removing them from evaluation from the effect of removing them from training.
Outputs: research_audit/final_diagnostics/outputs/d02_*.csv/json/npz, d02.log
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from joblib import Parallel, delayed

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "research_audit/scripts"))
from splits import make_event_folds  # noqa: E402
from train import make_logreg_pipeline, tune_logreg_C  # noqa: E402
from s00_engine import contrast, holm  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = ROOT / "research_audit/final_diagnostics/outputs"
OUT.mkdir(parents=True, exist_ok=True)
CFG = yaml.safe_load(open(ROOT / "configs/v2_coreness_fix.yaml", encoding="utf-8"))
NB, BS = CFG["study2"]["n_bootstrap"], CFG["study2"]["bootstrap_seed"]
SCORING = {"ba": "balanced_accuracy", "ll": "neg_log_loss"}
STRUCT6 = ["reciprocity", "largest_wcc_fraction", "indegree_gini", "outdegree_gini", "coreness_median", "coreness_max"]
L = "msg_length_dispersion"
FSETS = {"A": ["log_node_count"], "B": ["log_node_count", L], "C": ["log_node_count"] + STRUCT6, "D": ["log_node_count"] + STRUCT6 + [L]}
KS = (250, 500, 1000)
PARTS = [42, 1, 2, 3, 4, 5, 6, 7, 8, 9]
EXCL = ("Tapuma_YapıKayıt___2023-04-19_campaign_fulldata", "YapıKayıt_YoksaOyyok___2023-05-01_campaign_fulldata")

man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet")
views = pd.read_parquet(ROOT / "data/processed/sampled_views_v2.parquet")
full = pd.read_parquet(ROOT / "outputs/run_v2/study1/full_graph_features.parquet")
SEEDS = sorted(views.seed.unique())

# ---- verification of the two events and of the one-view-per-(K, seed, event) structure
assert views.groupby(["K", "seed", "event_id"]).size().max() == 1
ver = {}
for e in EXCL:
    ver[e] = {"manifest_label": int(man.set_index("event_id").loc[e, "label"]), "manifest_label_str": man.set_index("event_id").loc[e, "label_str"],
              "full_graph_label": int(full.loc[e, "label"]), "full_graph_token_std_is_nan": bool(np.isnan(full.loc[e, L])),
              "n_edges": int(man.set_index("event_id").loc[e, "n_edges"]),
              "views_by_K": {int(K): int(((views.event_id == e) & (views.K == K)).sum()) for K in KS},
              "views_token_std_nan_by_K": {int(K): int(((views.event_id == e) & (views.K == K) & views[L].isna()).sum()) for K in KS}}
nan_other = views[~views.event_id.isin(EXCL)][L].isna().sum()
ver["views_with_undefined_token_std_outside_these_events"] = int(nan_other)
print(json.dumps(ver, indent=1, ensure_ascii=False), flush=True)
assert all(ver[e]["manifest_label"] == 1 == ver[e]["full_graph_label"] for e in EXCL) and nan_other == 0


def run(K, part, fs, obj, exclude=()):
    """Verbatim v02.run (as study2_observation.run_conditions, FF and KK only) plus cohort exclusion."""
    fm = make_event_folds(man, 5, part)
    ev = sorted(e for e in views[views.K == K].event_id.unique() if e not in exclude)
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
# validation: no exclusion, partition 42, must equal stored v02 predictions
orig = np.load(ROOT / "research_audit/outputs/v02_predictions.npz")
val_jobs = [j for j in jobs if j[1] == 42]
val = Parallel(n_jobs=-1)(delayed(run)(*j) for j in val_jobs)
vdiff = max(float(np.abs(orig[f"K{K}|part{p}|{fs}|{o}|{c}"] - r[i]).max())
            for (K, p, fs, o), r in zip(val_jobs, val) for i, c in enumerate(("FF", "KK")))
print(f"validation (no exclusion, partition 42) max |diff| vs v02_predictions.npz: {vdiff}", flush=True)
assert vdiff == 0.0

print(f"{len(jobs)} jobs with exclusion", flush=True)
res = dict(zip(jobs, Parallel(n_jobs=-1)(delayed(run)(*j, EXCL) for j in jobs)))
np.savez_compressed(OUT / "d02_predictions_excluding_two_events.npz",
                    **{f"K{K}|part{p}|{fs}|{o}|{c}": res[(K, p, fs, o)][i] for (K, p, fs, o) in res for i, c in enumerate(("FF", "KK"))})

EVall = {K: sorted(views[views.K == K].event_id.unique()) for K in KS}
EV = {K: [e for e in EVall[K] if e not in EXCL] for K in KS}
Y = {K: full.loc[EV[K], "label"].to_numpy().astype(int) for K in KS}
KEEP = {K: np.array([e not in EXCL for e in EVall[K]]) for K in KS}


def P(K, fs, o, parts, source):
    if source == "refit":
        return np.vstack([res[(K, p, fs, o)][1] for p in parts])
    return np.vstack([orig[f"K{K}|part{p}|{fs}|{o}|KK"][:, KEEP[K]] for p in parts])


rows = []
for source, label in (("refit", "excluded and refitted"), ("orig", "original fits, two events dropped from scoring only")):
    for an, parts in (("primary (partition 42)", (42,)), ("sensitivity (10 partitions)", PARTS)):
        for K in KS:
            for a, b in (("B", "A"), ("D", "C")):
                c = contrast(Y[K], P(K, a, "ll", parts, source), P(K, b, "ll", parts, source),
                             P(K, a, "ba", parts, source), P(K, b, "ba", parts, source), n_boot=NB, seed=BS)
                rows.append({"version": label, "analysis": an, "K": K, "contrast": f"{a} - {b}", "n_events": len(EV[K]),
                             "n_campaign": int(Y[K].sum()), **c})
CT = pd.DataFrame(rows)
for (v, an, con), g in CT.groupby(["version", "analysis", "contrast"]):
    for m in ("LL", "AUC", "BA"):
        h = holm({K: p for K, p in zip(g.K, g[f"p_{m}"])})
        CT.loc[g.index, f"p_{m}_holm_across_K"] = [h[K] for K in g.K]

# side-by-side with the original v02 (KK) contrasts
O = pd.DataFrame(json.loads((ROOT / "research_audit/outputs/v02_results.json").read_text(encoding="utf-8"))["contrasts"])
O = O[O.condition == "KK"]
cmp = []
for _, r in CT[CT.version == "excluded and refitted"].iterrows():
    o = O[(O.analysis == r.analysis) & (O.K == r.K) & (O.contrast == r.contrast)].iloc[0]
    d = {"analysis": r.analysis, "K": r.K, "contrast": r.contrast, "n_events_orig": int(o.n_events), "n_events_excl": int(r.n_events)}
    for m in ("LL", "AUC", "BA"):
        d |= {f"d{m}_orig": o[f"d{m}"], f"d{m}_ci_orig": o[f"d{m}_ci"], f"p_{m}_holm_orig": o[f"p_{m}_holm_across_K"],
              f"d{m}_excl": r[f"d{m}"], f"d{m}_ci_excl": r[f"d{m}_ci"], f"p_{m}_holm_excl": r[f"p_{m}_holm_across_K"],
              f"d{m}_change": r[f"d{m}"] - o[f"d{m}"]}
    d |= {"repeats_favouring_lensd_LL_orig": int(o.repeats_favouring_A_LL), "repeats_favouring_lensd_LL_excl": int(r.repeats_favouring_A_LL),
          "n_repeats": int(r.n_repeats)}
    cmp.append(d)
CMP = pd.DataFrame(cmp)


def fmt(df):
    f = df.copy()
    for c in [c for c in f.columns if c.endswith("_ci") or "_ci_" in c]:
        f[c] = f[c].map(lambda v: f"[{v[0]:+.3f}, {v[1]:+.3f}]")
    return f


fmt(CT).to_csv(OUT / "d02_contrasts.csv", index=False)
fmt(CMP).to_csv(OUT / "d02_comparison_with_original.csv", index=False)
for _, r in CT.iterrows():
    print(f"{r.version[:8]:8s} {r.analysis[:11]:11s} K={r.K:4d} {r.contrast} n={r.n_events} dLL {r.dLL:+.3f} [{r.dLL_ci[0]:+.3f}, {r.dLL_ci[1]:+.3f}] "
          f"holm {r.p_LL_holm_across_K:.3f} | dAUC {r.dAUC:+.3f} [{r.dAUC_ci[0]:+.3f}, {r.dAUC_ci[1]:+.3f}] holm {r.p_AUC_holm_across_K:.3f} | "
          f"dBA {r.dBA:+.3f} [{r.dBA_ci[0]:+.3f}, {r.dBA_ci[1]:+.3f}] holm {r.p_BA_holm_across_K:.3f} | fav LL {r.repeats_favouring_A_LL}/{r.n_repeats}",
          flush=True)
print(fmt(CMP).round(3).to_string(index=False), flush=True)


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, np.ndarray)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    return o


(OUT / "d02_results.json").write_text(json.dumps(clean({"verification": ver, "validation_max_abs_diff_no_exclusion": vdiff,
                                                        "excluded_events": list(EXCL), "contrasts": CT.to_dict("records"),
                                                        "comparison_with_original": CMP.to_dict("records")}),
                                                 indent=2, ensure_ascii=False), encoding="utf-8")
