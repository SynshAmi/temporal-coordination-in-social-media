"""
a05_endpoint_rewiring.py — endpoint occupancy and the degree-preserving null.

A. E[N_K] = sum_v [1 - C(m - d_v, K) / C(m, K)], with d_v the number of distinct directed edges
   incident to v (out + in - self-loop) and K edges drawn uniformly without replacement.
   Checked against (i) Monte Carlo draws and (ii) the actual Study 2 views (exported edge indices).
   Also: the exact variance, using P(u, v both missing) = C(m - d_u - d_v + e_uv, K) / C(m, K),
   where e_uv is the number of directed edges joining u and v (0, 1 or 2).
B. Rewiring: with the pipeline's own rewire_directed (10 swaps per edge), check that every d_v is
   unchanged (so E[N_K] is exactly unchanged) and compare the N_K distribution (Monte Carlo)
   between real and rewired graphs.
C. Stored null-model outputs: swaps achieved vs target, unmoved edges, and how often each
   arrangement feature varies across the 5 realisations.

Output: research_audit/outputs/a05_endpoint_rewiring.json
"""
import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.special import gammaln

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from rewiring import rewire_directed, assert_degree_preserved  # noqa: E402

LEN = ROOT / "frontend/public/data/len"
idx = json.loads((LEN / "index.json").read_text(encoding="utf-8"))
ev = pd.DataFrame(idx["events"])
rng = np.random.default_rng(2026)
logC = lambda n, k: gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)


def load(i):
    g = json.loads((LEN / f"events/e{i:03d}.json").read_text(encoding="utf-8"))
    e = np.array(g["edges"]).reshape(-1, 2)
    return g["n"], e[:, 0], e[:, 1]


def incident(n, s, t):
    return np.bincount(s, minlength=n) + np.bincount(t, minlength=n) - np.bincount(s[s == t], minlength=n)


def expected(n, s, t, K):
    m, d = len(s), incident(n, s, t)
    q = np.where(m - d >= K, np.exp(logC(m - d, K) - logC(m, K)), 0.0)
    return float(np.sum(1 - q)), q


def exact_var(n, s, t, K):
    m, d = len(s), incident(n, s, t)
    E, q = expected(n, s, t, K)
    var = float(np.sum(q * (1 - q)))
    # e_uv for joined pairs; unjoined pairs have e = 0
    pairs = pd.Series(1, index=pd.MultiIndex.from_arrays([np.minimum(s, t), np.maximum(s, t)])).groupby(level=[0, 1]).sum()
    pairs = pairs[pairs.index.get_level_values(0) != pairs.index.get_level_values(1)]
    # sum over u != v of [P(both missing) - q_u q_v]; for e = 0 pairs, use the closed form over all pairs
    D = np.arange(d.max() + 1)
    cnt = np.bincount(d)
    tot = 0.0
    for a in D[cnt > 0]:
        for b in D[cnt > 0]:
            num = cnt[a] * (cnt[b] - (a == b))
            if num == 0:
                continue
            p_ab = np.exp(logC(m - a - b, K) - logC(m, K)) if m - a - b >= K else 0.0
            qa = np.exp(logC(m - a, K) - logC(m, K)) if m - a >= K else 0.0
            qb = np.exp(logC(m - b, K) - logC(m, K)) if m - b >= K else 0.0
            tot += num * (p_ab - qa * qb)
    # correct joined pairs: replace e = 0 term by actual e_uv term (ordered pairs: x2)
    u, v = pairs.index.get_level_values(0).to_numpy(), pairs.index.get_level_values(1).to_numpy()
    e = pairs.to_numpy()
    p0 = np.where(m - d[u] - d[v] >= K, np.exp(logC(m - d[u] - d[v], K) - logC(m, K)), 0.0)
    pe = np.where(m - d[u] - d[v] + e >= K, np.exp(logC(m - d[u] - d[v] + e, K) - logC(m, K)), 0.0)
    tot += 2 * np.sum(pe - p0)
    return E, var + tot


def mc(n, s, t, K, reps=3000):
    m = len(s)
    out = np.empty(reps)
    for r in range(reps):
        i = rng.choice(m, K, replace=False)
        out[r] = len(np.unique(np.concatenate([s[i], t[i]])))
    return out


res = {"A_formula": [], "A_study2_views": {}, "B_rewiring": [], "C_null_outputs": {}}
# A: a spread of events by edge count, every eligible budget
sel = ev[ev.budgets.map(len) > 0].sort_values("n_edges")
picks = [sel.iloc[0].i, sel.iloc[len(sel) // 4].i, sel.iloc[len(sel) // 2].i, sel.iloc[3 * len(sel) // 4].i, sel.iloc[-1].i]
for i in picks:
    n, s, t = load(int(i))
    for K in ev.loc[ev.i == i, "budgets"].iloc[0]:
        E, V = exact_var(n, s, t, K)
        x = mc(n, s, t, K)
        res["A_formula"].append({"event": int(i), "m": len(s), "K": K, "E_formula": E, "SD_formula": float(np.sqrt(V)),
                                 "MC_mean": float(x.mean()), "MC_sd": float(x.std(ddof=1)), "MC_se_mean": float(x.std(ddof=1) / np.sqrt(len(x))),
                                 "z": float((x.mean() - E) / (x.std(ddof=1) / np.sqrt(len(x))))})
        print(res["A_formula"][-1], flush=True)

# A(ii): actual Study 2 views — mean realised N_K over 10 seeds vs formula, all events and budgets
zs, rel = [], []
for _, e in ev[ev.samples.notna()].iterrows():
    n, s, t = load(int(e.i))
    S = json.loads((LEN / e.samples).read_text(encoding="utf-8"))
    for K, rec in S["budgets"].items():
        E, _ = expected(n, s, t, int(K))
        realised = [f["n_nodes"] for f in rec["features"]]
        rel.append(abs(np.mean(realised) - E) / E)
res["A_study2_views"] = {"n_event_budgets": len(rel), "max_rel_err_mean_of_10_seeds": float(np.max(rel)), "median_rel_err": float(np.median(rel))}
print(res["A_study2_views"], flush=True)

# B: rewiring invariance on three events of different size
for i in (picks[0], picks[2], picks[4]):
    n, s, t = load(int(i))
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    G.add_edges_from(zip(s.tolist(), t.tolist()))
    K = 250
    E0, V0 = exact_var(n, s, t, K)
    x0 = mc(n, s, t, K, 2000)
    rows = []
    for r in range(5):
        R, st = rewire_directed(G, 10, seed=1000 + r, return_stats=True)
        assert_degree_preserved(G, R)
        e = np.array(list(R.edges()))
        rs, rt = e[:, 0], e[:, 1]
        same_d = bool(np.array_equal(incident(n, s, t), incident(n, rs, rt)))
        E1, V1 = exact_var(n, rs, rt, K)
        x1 = mc(n, rs, rt, K, 2000)
        rows.append({"realisation": r, "d_v_identical": same_d, "E_real": E0, "E_rewired": E1, "SD_real": float(np.sqrt(V0)),
                     "SD_rewired": float(np.sqrt(V1)), "MC_mean_real": float(x0.mean()), "MC_mean_rewired": float(x1.mean()),
                     "swaps_done": st["swaps"], "swaps_target": st["target"], "frac_unchanged": st["frac_edges_unchanged"]})
    res["B_rewiring"].append({"event": int(i), "n": n, "m": len(s), "K": K, "realisations": rows})
    print(res["B_rewiring"][-1], flush=True)

# C: stored null-model outputs
pilot = pd.read_csv(ROOT / "outputs/run_v2/study1/null_pilot.csv")
pilot["achieved"] = pilot.swaps / pilot.target
nf = pd.read_parquet(ROOT / "outputs/run_v2/study1/null_features.parquet")
nr = json.loads((ROOT / "outputs/run_v2/study1/null_results.json").read_text(encoding="utf-8"))
var0 = {c: float((nf.groupby("event_id")[c].std(ddof=0) == 0).mean()) for c in ["reciprocity", "largest_wcc_fraction", "coreness_median", "coreness_max"]}
res["C_null_outputs"] = {
    "pilot_swaps_achieved_fraction_min": float(pilot.achieved.min()),
    "pilot_frac_unchanged_by_swaps_per_edge": pilot.groupby("swaps_per_edge").frac_edges_unchanged.median().to_dict(),
    "share_events_zero_variance_across_5_realisations": var0,
    "null_results_keys": list(nr.keys()),
}
for k in ("frac_edges_unchanged_quantiles", "z_scores", "n_realizations", "swaps_per_edge"):
    if k in nr:
        res["C_null_outputs"][k] = nr[k]
print(json.dumps(res["C_null_outputs"], indent=1, default=str)[:2500])
(ROOT / "research_audit/outputs/a05_endpoint_rewiring.json").write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
