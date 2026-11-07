"""
a03_study1_reproduce.py — independent reproduction of the Study 1 primary results.

1. Recomputes scale and structural features from data/processed/edges.parquet with code written
   for this audit (numpy/scipy; NetworkX only for core numbers), and compares them with the
   pipeline's outputs/run_v2/study1/full_graph_features.parquet. Content features need message
   text processing and are taken from the pipeline (not independently recomputed).
2. Checks that density = m / (n (n-1)) and mean degree = m / n are exact functions of the counts.
3. Refits the logistic-regression levels M0, M0q and M4 with an audit-written CV loop
   (StratifiedKFold(5, shuffle, seed 42) outer; StratifiedKFold(3, shuffle, seed 0) inner; C grid
   {0.01, 0.1, 1, 10}; median imputation, standardisation and balanced weights fitted on the
   training fold only), and recomputes C1 (M4 - M0q) with an audit-written paired bootstrap
   (2,000 resamples, seed 7).
4. Reads the tuned C values of the stored run and of the H1 wider-grid run.

Output: research_audit/outputs/a03_study1.json
"""
import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research_audit" / "outputs"


def gini(x):
    x = np.sort(np.asarray(x, float))
    n, s = len(x), x.sum()
    return 0.0 if n == 0 or s == 0 else float((2 * np.arange(1, n + 1) @ x - (n + 1) * s) / (n * s))


def structural(src, dst):
    nodes, inv = np.unique(np.concatenate([src, dst]), return_inverse=True)
    n, m = len(nodes), len(src)
    s, t = inv[:m], inv[m:]
    pairs = set(zip(s.tolist(), t.tolist()))
    recip_edges = sum(1 for a, b in pairs if a != b and (b, a) in pairs)
    A = coo_matrix((np.ones(m), (s, t)), shape=(n, n))
    _, comp = connected_components(A, directed=True, connection="weak")
    U = nx.Graph()
    U.add_nodes_from(range(n))
    U.add_edges_from((a, b) for a, b in pairs if a != b)
    core = np.array(list(nx.core_number(U).values()), float)
    return {"n": n, "m": m, "log_node_count": np.log1p(n), "log_edge_count": np.log1p(m),
            "density": m / (n * (n - 1)), "reciprocity": recip_edges / m,
            "largest_wcc_fraction": np.bincount(comp).max() / n,
            "indegree_gini": gini(np.bincount(t, minlength=n)), "outdegree_gini": gini(np.bincount(s, minlength=n)),
            "coreness_median": float(np.median(core)), "coreness_max": float(core.max())}


def tune_C(X, y, Cs, scoring):
    best, best_s = Cs[0], -np.inf
    for C in Cs:
        sc = []
        for tr, va in StratifiedKFold(3, shuffle=True, random_state=0).split(X, y):
            p = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                              LogisticRegression(C=C, max_iter=1000, class_weight="balanced", random_state=42)).fit(X[tr], y[tr])
            pr = p.predict_proba(X[va])[:, 1]
            sc.append(balanced_accuracy_score(y[va], pr >= 0.5) if scoring == "ba" else -log_loss(y[va], pr, labels=[0, 1]))
        if np.mean(sc) > best_s:
            best, best_s = C, np.mean(sc)
    return best


def oof(X, y, folds, Cs, scoring):
    p, cs = np.zeros(len(y)), []
    for k in range(5):
        tr, te = folds != k, folds == k
        C = tune_C(X[tr], y[tr], Cs, scoring)
        cs.append(C)
        p[te] = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                              LogisticRegression(C=C, max_iter=1000, class_weight="balanced", random_state=42)).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return p, cs


def paired(y, pa, pb, n_boot=2000, seed=7):
    rng = np.random.default_rng(seed)
    la = -(y * np.log(np.clip(pa, 1e-6, 1)) + (1 - y) * np.log(np.clip(1 - pa, 1e-6, 1)))
    lb = -(y * np.log(np.clip(pb, 1e-6, 1)) + (1 - y) * np.log(np.clip(1 - pb, 1e-6, 1)))
    dba, dll = [], []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) < 2:
            continue
        dba.append(balanced_accuracy_score(y[i], pa[i] >= .5) - balanced_accuracy_score(y[i], pb[i] >= .5))
        dll.append(la[i].mean() - lb[i].mean())
    return {"dBA": balanced_accuracy_score(y, pa >= .5) - balanced_accuracy_score(y, pb >= .5),
            "dBA_ci": np.percentile(dba, [2.5, 97.5]).tolist(), "dLL": la.mean() - lb.mean(), "dLL_ci": np.percentile(dll, [2.5, 97.5]).tolist()}


man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet")
edges = pd.read_parquet(ROOT / "data/processed/edges.parquet", columns=["event_id", "source", "target"])
stored = pd.read_parquet(ROOT / "outputs/run_v2/study1/full_graph_features.parquet")
stored = stored.reset_index().set_index("event_id") if "event_id" in stored.reset_index().columns else stored

mine = {eid: structural(g.source.astype(int).to_numpy(), g.target.astype(int).to_numpy()) for eid, g in edges.groupby("event_id")}
mine = pd.DataFrame(mine).T.loc[stored.index]
cols = ["log_node_count", "log_edge_count", "density", "reciprocity", "largest_wcc_fraction", "indegree_gini", "outdegree_gini", "coreness_median", "coreness_max"]
feat_diff = {c: float(np.max(np.abs(mine[c].astype(float) - stored[c].astype(float)))) for c in cols}
n_match_manifest = bool((mine["n"].astype(int).values == man.set_index("event_id").loc[stored.index, "n_nodes"].values).all())
dens_identity = float(np.max(np.abs(mine.density - mine.m / (mine.n * (mine.n - 1)))))
# density as a function of the two log counts only
n_from_log, m_from_log = np.expm1(stored.log_node_count.astype(float)), np.expm1(stored.log_edge_count.astype(float))
dens_from_counts = float(np.max(np.abs(stored.density - m_from_log / (n_from_log * (n_from_log - 1))) / stored.density))

# Independent LR refit
F = stored.copy()
F["log_n_sq"], F["log_e_sq"], F["log_n_x_log_e"] = F.log_node_count ** 2, F.log_edge_count ** 2, F.log_node_count * F.log_edge_count
L = {"M0": ["log_node_count", "log_edge_count"]}
L["M0q"] = L["M0"] + ["log_n_sq", "log_e_sq", "log_n_x_log_e"]
L["M4"] = L["M0q"] + ["indegree_gini", "outdegree_gini", "reciprocity", "largest_wcc_fraction", "coreness_median", "coreness_max",
                      "exact_dup_proportion", "text_concentration", "msg_length_dispersion"]
ev = man.event_id.values
folds_by_event = {}
for k, (_, te) in enumerate(StratifiedKFold(5, shuffle=True, random_state=42).split(ev, man.label.values)):
    for i in te:
        folds_by_event[ev[i]] = k
F = F.sort_index()
y = F.label.astype(int).values
folds = np.array([folds_by_event[e] for e in F.index])
Cs = [0.01, 0.1, 1.0, 10.0]
res = {}
P = {}
for lv in ("M0", "M0q", "M4"):
    X = F[L[lv]].astype(float).values
    pb, cb = oof(X, y, folds, Cs, "ba")
    pl, cl = oof(X, y, folds, Cs, "ll")
    P[lv] = (pb, pl)
    res[lv] = {"BA": balanced_accuracy_score(y, pb >= .5), "LL": log_loss(y, pl), "AUC": roc_auc_score(y, pl), "C_ba": cb, "C_ll": cl}
c1 = {"ba": paired(y, P["M4"][0], P["M0q"][0]), "ll": paired(y, P["M4"][1], P["M0q"][1])}
c1 = {"dBA": c1["ba"]["dBA"], "dBA_ci": c1["ba"]["dBA_ci"], "dLL": c1["ll"]["dLL"], "dLL_ci": c1["ll"]["dLL_ci"]}

# Stored outputs: tuned C per fold, LR vs HGBT
R = json.loads((ROOT / "outputs/run_v2/paper_results.json").read_text(encoding="utf-8"))
oofp = pd.read_parquet(ROOT / "outputs/run_v2/study1/oof_predictions.parquet")
tc = {}
if "tuned_C" in oofp.columns:
    for (obj, lv), g in oofp[oofp.model == "logreg"].groupby(["objective", "experiment"]):
        tc[f"{obj}:{lv}"] = g.groupby("fold_id").tuned_C.first().tolist()
h1 = json.loads((ROOT / "outputs/revision_h1_cgrid/results.json").read_text(encoding="utf-8"))
perf = R["study1"]["performance"]
out = {
    "feature_max_abs_diff_vs_pipeline": feat_diff,
    "node_count_from_edges_equals_manifest": n_match_manifest,
    "density_identity_max_abs_err": dens_identity,
    "density_from_log_counts_max_rel_err": dens_from_counts,
    "independent_refit": res, "independent_C1": c1,
    "paper_values": {"M0_BA": perf["logreg"]["M0"]["balanced_accuracy"], "M0q_LL": perf["logreg"]["M0q"]["log_loss"],
                     "M4_BA": perf["logreg"]["M4"]["balanced_accuracy"], "M4_LL": perf["logreg"]["M4"]["log_loss"],
                     "M4_AUC": perf["logreg"]["M4"]["roc_auc_ll_fit"],
                     "C1_BA": R["study1"]["confirmatory"]["logreg"]["C1"]["ba"]["delta_ba"],
                     "C1_BA_ci": R["study1"]["confirmatory"]["logreg"]["C1"]["ba"]["delta_ba_ci"],
                     "C1_LL": R["study1"]["confirmatory"]["logreg"]["C1"]["log_loss"]["delta_logloss"],
                     "C1_LL_ci": R["study1"]["confirmatory"]["logreg"]["C1"]["log_loss"]["delta_logloss_ci"]},
    "stored_tuned_C": tc, "h1_tuned_C": h1["tuned_C"], "h1_grid": h1["grid"],
    "h1_upper_bound_hits": h1["levels_with_optimum_at_upper_bound"],
    "lr_vs_hgbt": {lv: {"LR_BA": perf["logreg"][lv]["balanced_accuracy"], "HGBT_BA": perf["hgbt"][lv]["balanced_accuracy"],
                        "LR_AUC": perf["logreg"][lv]["roc_auc_ll_fit"], "HGBT_AUC": perf["hgbt"][lv]["roc_auc_ll_fit"],
                        "LR_LL": perf["logreg"][lv]["log_loss"], "HGBT_LL": perf["hgbt"][lv]["log_loss"]} for lv in perf["logreg"]},
    "hgbt_vs_best_count": R["study1"]["hgbt_vs_best_count_baseline"],
}
(OUT / "a03_study1.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
print(json.dumps({k: out[k] for k in ("feature_max_abs_diff_vs_pipeline", "node_count_from_edges_equals_manifest", "density_identity_max_abs_err",
                                      "density_from_log_counts_max_rel_err", "independent_refit", "independent_C1", "paper_values", "stored_tuned_C")}, indent=1, default=float))
