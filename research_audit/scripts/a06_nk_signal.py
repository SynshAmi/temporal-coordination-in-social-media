"""
a06_nk_signal.py — EXPLORATORY: where does the label signal of the sampled endpoint count come from?

Events: the 102 events with at least 250 edges. Folds: the study's outer split
(StratifiedKFold(5, shuffle, seed 42) over all 103 events, restricted to these 102).
Model: logistic regression (median imputation, standardisation, balanced weights), C tuned by
inner 3-fold CV on the training fold for log loss (AUC and log loss reported) and separately for
balanced accuracy. Paired event-level bootstrap (2,000 resamples, seed 7) for selected contrasts.
These are post-hoc analyses on the same 102 events, without multiplicity correction.

Per event, K = 250:
  log_n, log_m          full-graph node and edge counts
  log_E_hom             expected endpoints if every node had the mean incident-edge count (size only)
  log_E_nk              exact expectation from the degree sequence (eq. 3 of the paper)
  het_resid             log_E_nk - log_E_hom: the part of the expectation due to degree heterogeneity
  gini_in, gini_out     full-graph degree concentration (paper features)
  log_nk_view           realised N_K in the first Study 2 view (seed 100)
  log_src, log_tgt      distinct sources and distinct targets in that view

Output: research_audit/outputs/a06_nk_signal.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import gammaln
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
LEN = ROOT / "frontend/public/data/len"
K = 250
logC = lambda n, k: gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)

idx = json.loads((LEN / "index.json").read_text(encoding="utf-8"))
rows = []
for e in idx["events"]:
    if K not in e["budgets"]:
        continue
    g = json.loads((LEN / e["graph"]).read_text(encoding="utf-8"))
    E = np.array(g["edges"]).reshape(-1, 2)
    s, t, n, m = E[:, 0], E[:, 1], g["n"], len(E)
    d = np.bincount(s, minlength=n) + np.bincount(t, minlength=n) - np.bincount(s[s == t], minlength=n)
    q = np.where(m - d >= K, np.exp(logC(m - d, K) - logC(m, K)), 0.0)
    dbar = d.mean()
    E_hom = n * (1 - np.exp(logC(m - dbar, K) - logC(m, K)))
    S = json.loads((LEN / e["samples"]).read_text(encoding="utf-8"))
    view = np.array(S["budgets"][str(K)]["edges"][0])
    rows.append({"id": e["id"], "label": e["label"], "log_n": np.log(n), "log_m": np.log(m), "log_E_hom": np.log(E_hom),
                 "log_E_nk": np.log((1 - q).sum()), "gini_in": e["features"]["indegree_gini"], "gini_out": e["features"]["outdegree_gini"],
                 "log_nk_view": np.log(len(np.unique(np.concatenate([s[view], t[view]])))),
                 "log_src": np.log(len(np.unique(s[view]))), "log_tgt": np.log(len(np.unique(t[view])))})
D = pd.DataFrame(rows)
D["het_resid"] = D.log_E_nk - D.log_E_hom

man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet")
fold = {}
for k, (_, te) in enumerate(StratifiedKFold(5, shuffle=True, random_state=42).split(man.event_id.values, man.label.values)):
    for i in te:
        fold[man.event_id.values[i]] = k
D["fold"] = D.id.map(fold)
y = D.label.values.astype(int)
Cs = [0.01, 0.1, 1.0, 10.0, 100.0]


def pipe(C):
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=C, max_iter=2000, class_weight="balanced"))


def fit_oof(cols, scoring):
    X, p = D[cols].values, np.zeros(len(D))
    for k in range(5):
        tr, te = D.fold.values != k, D.fold.values == k
        best, bs = Cs[0], -np.inf
        for C in Cs:
            sc = []
            for a, b in StratifiedKFold(3, shuffle=True, random_state=0).split(X[tr], y[tr]):
                pr = pipe(C).fit(X[tr][a], y[tr][a]).predict_proba(X[tr][b])[:, 1]
                sc.append(balanced_accuracy_score(y[tr][b], pr >= .5) if scoring == "ba" else -log_loss(y[tr][b], pr, labels=[0, 1]))
            if np.mean(sc) > bs:
                best, bs = C, np.mean(sc)
        p[te] = pipe(best).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return p


SETS = {
    "counts": ["log_n", "log_m"],
    "E_hom (size only)": ["log_E_hom"],
    "E_nk (degree sequence)": ["log_E_nk"],
    "counts + E_nk": ["log_n", "log_m", "log_E_nk"],
    "counts + het_resid": ["log_n", "log_m", "het_resid"],
    "counts + degree Gini": ["log_n", "log_m", "gini_in", "gini_out"],
    "N_K realised (one view)": ["log_nk_view"],
    "sources + targets (one view)": ["log_src", "log_tgt"],
}
P = {name: (fit_oof(c, "ba"), fit_oof(c, "ll")) for name, c in SETS.items()}
perf = {name: {"BA": balanced_accuracy_score(y, pb >= .5), "AUC": roc_auc_score(y, pl), "LL": log_loss(y, pl)} for name, (pb, pl) in P.items()}


def boot(a, b, n_boot=2000, seed=7):
    rng = np.random.default_rng(seed)
    pa, pb = P[a][1], P[b][1]
    la = -(y * np.log(np.clip(pa, 1e-6, 1)) + (1 - y) * np.log(np.clip(1 - pa, 1e-6, 1)))
    lb = -(y * np.log(np.clip(pb, 1e-6, 1)) + (1 - y) * np.log(np.clip(1 - pb, 1e-6, 1)))
    dll, dauc = [], []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) < 2:
            continue
        dll.append(la[i].mean() - lb[i].mean())
        dauc.append(roc_auc_score(y[i], pa[i]) - roc_auc_score(y[i], pb[i]))
    return {"dLL": float(la.mean() - lb.mean()), "dLL_ci": np.percentile(dll, [2.5, 97.5]).tolist(),
            "dAUC": float(roc_auc_score(y, pa) - roc_auc_score(y, pb)), "dAUC_ci": np.percentile(dauc, [2.5, 97.5]).tolist()}


contrasts = {f"{a} vs {b}": boot(a, b) for a, b in [
    ("E_nk (degree sequence)", "E_hom (size only)"), ("counts + E_nk", "counts"), ("counts + het_resid", "counts"),
    ("counts + degree Gini", "counts"), ("sources + targets (one view)", "N_K realised (one view)"), ("N_K realised (one view)", "counts")]}
corr = D[["log_n", "log_m", "log_E_hom", "log_E_nk", "het_resid", "gini_in", "gini_out", "log_nk_view"]].corr().round(3)
out = {"n_events": len(D), "performance": perf, "contrasts": contrasts, "correlations": corr.to_dict()}
(ROOT / "research_audit/outputs/a06_nk_signal.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
print(pd.DataFrame(perf).T.round(3).to_string())
for k, v in contrasts.items():
    print(f"{k:58s} dLL {v['dLL']:+.3f} [{v['dLL_ci'][0]:+.3f}, {v['dLL_ci'][1]:+.3f}]  dAUC {v['dAUC']:+.3f} [{v['dAUC_ci'][0]:+.3f}, {v['dAUC_ci'][1]:+.3f}]")
print(corr[["het_resid", "log_E_nk"]].to_string())
