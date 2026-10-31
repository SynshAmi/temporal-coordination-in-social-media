"""
verify_studies.py
-----------------
Independent verification of Study 1 and Study 2 outputs.

Independence: metrics, bootstrap, Holm correction and the logistic-regression
cross-validation are re-implemented here from scikit-learn primitives; this
module does not import the study scripts' metric or bootstrap code. The study
code is imported only for the tuning-leakage tests, which exercise it directly.

Writes <run_dir>/verification/verification_report.json and prints a summary.
"""

import sys
import json
import zlib
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.special import gammaln
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import balanced_accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout.reconfigure(encoding="utf-8")
SRC = Path(__file__).resolve().parent
EPS = 1e-6
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append({"check": name, "pass": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))


# ----------------------------------------------------------------------------- metrics
def ba(y, p):
    return balanced_accuracy_score(y, (np.asarray(p) >= 0.5).astype(int))


def ll(y, p):
    return log_loss(y, np.clip(p, EPS, 1 - EPS), labels=[0, 1])


def boot_diff(y, fa, fb, stat, n_boot, seed):
    """Independent event-level paired bootstrap: returns point, 95% CI, two-sided p."""
    rng = np.random.default_rng(seed)
    n = len(y)
    point = stat(y, fa, np.arange(n)) - stat(y, fb, np.arange(n))
    d = []
    for _ in range(n_boot):
        i = rng.integers(0, n, n)
        if y[i].min() == y[i].max():
            continue
        d.append(stat(y, fa, i) - stat(y, fb, i))
    d = np.array(d)
    return point, (np.percentile(d, 2.5), np.percentile(d, 97.5)), min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))


def holm(p):
    keys = sorted(p, key=p.get)
    out, run = {}, 0.0
    for r, k in enumerate(keys):
        run = max(run, min(1.0, (len(keys) - r) * p[k]))
        out[k] = run
    return out


# ----------------------------------------------------------------------------- independent LR CV
def lr_pipe(C, seed):
    return Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()),
                     ("clf", LogisticRegression(C=C, max_iter=1000, solver="lbfgs", class_weight="balanced", random_state=seed))])


def lr_oof(X, y, folds, C_grid, scoring, seed):
    p = np.zeros(len(y))
    for k in np.unique(folds):
        tr, te = folds != k, folds == k
        nmin = int(np.bincount(y[tr]).min())
        cv = StratifiedKFold(max(2, min(3, nmin)), shuffle=True, random_state=0)
        scores = [cross_val_score(lr_pipe(C, seed), X[tr], y[tr], cv=cv, scoring=scoring).mean() for C in C_grid]
        best = C_grid[int(np.argmax(scores))]  # first maximum, as in the study code
        p[te] = lr_pipe(best, seed).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return p


def folds_for(event_ids, labels, n_folds, seed):
    f = {}
    for k, (_, te) in enumerate(StratifiedKFold(n_folds, shuffle=True, random_state=seed).split(event_ids, labels)):
        for i in te:
            f[event_ids[i]] = k
    return f


def main(config_path):
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    run = Path(cfg["output"]["run_dir"])
    out_dir = run / "verification"
    out_dir.mkdir(parents=True, exist_ok=True)
    man = pd.read_parquet(Path(cfg["data"]["manifests_dir"]) / "manifest.parquet")
    C_grid, rs = cfg["models"]["logreg"]["C_values"], cfg["splits"]["random_seed"]
    report = {}

    # ========================================================================= STUDY 1
    print("\n=== Study 1 ===")
    s1 = json.load(open(run / "study1" / "nested_results.json", encoding="utf-8"))
    oof = pd.read_parquet(run / "study1" / "oof_predictions.parquet")
    feat = pd.read_parquet(run / "study1" / "full_graph_features.parquet")
    levels = s1["levels"]
    feat = feat.assign(log_n_sq=feat.log_node_count ** 2, log_e_sq=feat.log_edge_count ** 2,
                       log_n_x_log_e=feat.log_node_count * feat.log_edge_count)
    fmap = folds_for(man.event_id.values, man.label.values, cfg["splits"]["n_folds"], rs)

    # identical events and folds across all levels/models/objectives
    g = oof.groupby(["model", "objective", "experiment"])
    same_events = all(sorted(d.event_id) == sorted(man.event_id) for _, d in g)
    fold_ok = all(all(int(f) == fmap[e] for e, f in zip(d.event_id, d.fold_id)) for _, d in g)
    check("S1 every model uses all 103 events once", same_events)
    check("S1 outer folds identical to an independent StratifiedKFold(seed=42)", fold_ok)

    get = lambda m, o, lv: oof[(oof.model == m) & (oof.objective == o) & (oof.experiment == lv)].set_index("event_id").sort_index()
    y = get("logreg", "ba", "M0").label.values

    # recompute reported performance (BA from ba fits, LL from ll fits)
    mism = []
    for m in ("logreg", "hgbt"):
        for lv in levels:
            pb, pl = get(m, "ba", lv).prob_campaign.values, get(m, "ll", lv).prob_campaign.values
            rep = s1["models"][m]["performance"][lv]
            if abs(ba(y, pb) - rep["balanced_accuracy"]) > 1e-9 or abs(ll(y, pl) - rep["log_loss"]) > 1e-9 \
                    or abs(roc_auc_score(y, pl) - rep["roc_auc_ll_fit"]) > 1e-9:
                mism.append((m, lv))
    check("S1 reported BA/LL/AUC recomputed exactly from saved OOF predictions", not mism, f"mismatches={mism}")

    # independent LR re-implementation reproduces the saved OOF probabilities
    # Row order matters: the inner-CV shuffle depends on it, so replicate in the study's
    # row order (feature-table order) and align by event afterwards.
    feat_s = feat
    fold_arr = np.array([fmap[e] for e in feat_s.index])
    y_study = feat_s.label.values.astype(int)
    maxdiff = 0.0
    for obj, scoring in (("ba", "balanced_accuracy"), ("ll", "neg_log_loss")):
        for lv in levels:
            p_ind = pd.Series(lr_oof(feat_s[levels[lv]].values, y_study, fold_arr, C_grid, scoring, rs), index=feat_s.index).sort_index()
            maxdiff = max(maxdiff, float(np.abs(p_ind.values - get("logreg", obj, lv).prob_campaign.values).max()))
    check("S1 independent LR CV reproduces all saved LR OOF probabilities (both objectives)", maxdiff < 1e-8, f"max |dp|={maxdiff:.2e}")

    # Sensitivity of the tuned fits to row order (a protocol property: reported, not pass/fail)
    order_sens = {}
    perm = np.random.default_rng(3).permutation(len(feat_s))
    fs_p = feat_s.iloc[perm]
    fold_p = np.array([fmap[e] for e in fs_p.index])
    for obj, scoring in (("ba", "balanced_accuracy"), ("ll", "neg_log_loss")):
        for lv in ("M0q", "M1", "M2", "M3", "M4"):
            pp = pd.Series(lr_oof(fs_p[levels[lv]].values, fs_p.label.values.astype(int), fold_p, C_grid, scoring, rs),
                           index=fs_p.index).sort_index()
            metric = ba if obj == "ba" else ll
            order_sens[f"{obj}:{lv}"] = {"study_order": metric(y, get("logreg", obj, lv).prob_campaign.values),
                                         "permuted_order": metric(y, pp.values), "probs": pp.values}
    for c, (a, b) in {"C1": ("M4", "M0q"), "C2": ("M2", "M1"), "C3": ("M3", "M0q")}.items():
        for obj in ("ba", "ll"):
            o = order_sens
            order_sens[f"{obj}:{c}"] = {"delta_study_order": o[f"{obj}:{a}"]["study_order"] - o[f"{obj}:{b}"]["study_order"],
                                       "delta_permuted_order": o[f"{obj}:{a}"]["permuted_order"] - o[f"{obj}:{b}"]["permuted_order"]}
    report["s1_row_order_sensitivity"] = {k: {kk: vv for kk, vv in v.items() if kk != "probs"} for k, v in order_sens.items()}
    print("row-order sensitivity (contrast deltas, study vs permuted order):",
          {k: (round(v["delta_study_order"], 3), round(v["delta_permuted_order"], 3)) for k, v in order_sens.items() if "delta_study_order" in v})

    # BA and LL objectives genuinely differ (no reuse of BA probabilities for LL)
    reuse = [lv for lv in levels if np.allclose(get("logreg", "ba", lv).prob_campaign, get("logreg", "ll", lv).prob_campaign)]
    cdiff = {lv: (get("logreg", "ba", lv).tuned_C.tolist(), get("logreg", "ll", lv).tuned_C.unique().tolist()) for lv in ("M0q", "M4")}
    check("S1 log-loss estimands use separately tuned fits", len(reuse) < len(levels),
          f"levels where both objectives chose identical C everywhere: {reuse}")
    report["s1_tuned_C_examples"] = {lv: {"ba": sorted(set(v[0])), "ll": v[1]} for lv, v in cdiff.items()}

    # confirmatory contrasts: point estimates exact, CIs approx (independent bootstrap, other seed)
    stat_ba = lambda yy, p, i: ba(yy[i], p[i])
    stat_ll = lambda yy, p, i: ll(yy[i], p[i])
    stat_auc = lambda yy, p, i: roc_auc_score(yy[i], p[i])
    conf_rows = []
    for m in ("logreg", "hgbt"):
        pv_ba, pv_ll = {}, {}
        for c, v in s1["models"][m]["confirmatory"].items():
            a, b = v["a"], v["b"]
            pa_b, pb_b = get(m, "ba", a).prob_campaign.values, get(m, "ba", b).prob_campaign.values
            pa_l, pb_l = get(m, "ll", a).prob_campaign.values, get(m, "ll", b).prob_campaign.values
            d1, ci1, p1 = boot_diff(y, pa_b, pb_b, stat_ba, 4000, 99)
            d2, ci2, p2 = boot_diff(y, pa_l, pb_l, stat_ll, 4000, 99)
            d3, ci3, _ = boot_diff(y, pa_l, pb_l, stat_auc, 4000, 99)
            pv_ba[c], pv_ll[c] = v["ba"]["p_bootstrap" if "p_bootstrap" in v["ba"] else "p_ba_bootstrap"], v["log_loss"]["p_logloss_bootstrap"]
            conf_rows.append({"model": m, "contrast": c, "a": a, "b": b,
                              "dBA_reported": v["ba"]["delta_ba"], "dBA_recomputed": d1, "dBA_ci_reported": v["ba"]["delta_ba_ci"], "dBA_ci_independent": list(ci1),
                              "dLL_reported": v["log_loss"]["delta_logloss"], "dLL_recomputed": d2, "dLL_ci_reported": v["log_loss"]["delta_logloss_ci"], "dLL_ci_independent": list(ci2),
                              "dAUC_reported": v["auc_ll_fit"]["delta_auc"], "dAUC_recomputed": d3, "dAUC_ci_independent": list(ci3),
                              "p_holm_ba_reported": v["ba"]["p_holm"], "p_holm_ll_reported": v["log_loss"]["p_holm"],
                              "p_ba_independent": p1, "p_ll_independent": p2})
        # Holm recomputed from the reported raw p-values
        hb, hl = holm(pv_ba), holm(pv_ll)
        okh = all(abs(hb[c] - s1["models"][m]["confirmatory"][c]["ba"]["p_holm"]) < 1e-12 and
                  abs(hl[c] - s1["models"][m]["confirmatory"][c]["log_loss"]["p_holm"]) < 1e-12 for c in hb)
        check(f"S1 [{m}] Holm adjustments recomputed exactly (BA and LL families separately)", okh)
    cr = pd.DataFrame(conf_rows)
    gba = float(np.abs(cr.dBA_reported - cr.dBA_recomputed).max())
    gll = float(np.abs(cr.dLL_reported - cr.dLL_recomputed).max())
    gau = float(np.abs(cr.dAUC_reported - cr.dAUC_recomputed).max())
    check("S1 confirmatory point differences recomputed (BA, AUC exact; LL within clipping-convention tolerance 1e-5)",
          gba < 1e-12 and gau < 1e-12 and gll < 1e-5, f"max gaps BA={gba:.1e} LL={gll:.1e} AUC={gau:.1e}")
    ci_gap = max(max(abs(np.array(r.dBA_ci_reported) - np.array(r.dBA_ci_independent))) for r in cr.itertuples())
    ci_gap_ll = max(max(abs(np.array(r.dLL_ci_reported) - np.array(r.dLL_ci_independent))) for r in cr.itertuples())
    check("S1 paired CIs agree with an independent bootstrap (4000 resamples, other seed) within 0.02",
          ci_gap < 0.02 and ci_gap_ll < 0.02, f"max endpoint gap BA={ci_gap:.3f}, LL={ci_gap_ll:.3f}")
    report["s1_confirmatory"] = conf_rows

    # tuning-leakage test: permuting held-out-fold labels must not change that fold's C or predictions
    sys.path.insert(0, str(SRC))
    from train import run_cv  # noqa: E402
    import study1_incremental as s1mod  # noqa: E402
    df = feat_s[["label"] + levels["M4"]].copy()
    leak_ok = True
    for scoring in ("balanced_accuracy", "neg_log_loss"):
        base, _ = run_cv(df, fmap, cfg, "leak", "logreg", scoring=scoring)
        for k in range(cfg["splits"]["n_folds"]):
            d2 = df.copy()
            idx = [e for e in d2.index if fmap[e] == k]
            d2.loc[idx, "label"] = np.random.default_rng(k).permutation(d2.loc[idx, "label"].values)
            pert, _ = run_cv(d2, fmap, cfg, "leak", "logreg", scoring=scoring)
            b = base[base.fold_id == k].set_index("event_id").sort_index()
            q = pert[pert.fold_id == k].set_index("event_id").sort_index()
            leak_ok &= bool(np.allclose(b.prob_campaign, q.prob_campaign, atol=1e-12) and (b.tuned_C.values == q.tuned_C.values).all())
    check("S1 LR tuning uses no held-out-fold labels (label permutation in each outer fold leaves its C and predictions unchanged)", leak_ok)
    base = s1mod.tuned_hgbt_cv(df, fmap, cfg, "leak", "ba").set_index("event_id").sort_index()
    d2 = df.copy()
    idx = [e for e in d2.index if fmap[e] == 0]
    d2.loc[idx, "label"] = np.random.default_rng(5).permutation(d2.loc[idx, "label"].values)
    q = s1mod.tuned_hgbt_cv(d2, fmap, cfg, "leak", "ba").set_index("event_id").sort_index()
    k0 = [e for e in base.index if fmap[e] == 0]
    check("S1 HGBT tuning uses no held-out-fold labels (fold 0 permutation)",
          np.allclose(base.loc[k0, "prob_campaign"], q.loc[k0, "prob_campaign"]) and (base.loc[k0, "params"] == q.loc[k0, "params"]).all())

    # ----------------------------------------------------------------------- null model audit
    print("\n=== Rewiring null audit ===")
    nr = json.load(open(run / "study1" / "null_results.json", encoding="utf-8"))
    nf = pd.read_parquet(run / "study1" / "null_features.parquet")
    pilot = pd.read_csv(run / "study1" / "null_pilot.csv")
    base_feat = feat.loc[nf.event_id.unique()]
    j = nf.groupby("event_id")[["indegree_gini", "outdegree_gini", "density"]].agg(["min", "max"])
    inv = all(np.allclose(j[(c, "min")], base_feat[c]) and np.allclose(j[(c, "max")], base_feat[c]) for c in ("indegree_gini", "outdegree_gini", "density"))
    check("Null: degree Gini and density identical to observed in every realization", inv)
    # independent M1 / M2 / M2-null BA via the independent LR CV
    arr = ["reciprocity", "largest_wcc_fraction", "coreness_median", "coreness_max"]
    yb = y_study
    p_m1 = lr_oof(feat_s[levels["M1"]].values, yb, fold_arr, C_grid, "balanced_accuracy", rs)
    p_m2 = lr_oof(feat_s[levels["M2"]].values, yb, fold_arr, C_grid, "balanced_accuracy", rs)
    nulls = []
    for r in sorted(nf.realization.unique()):
        fn = feat_s.copy()
        rr = nf[nf.realization == r].set_index("event_id").loc[fn.index]
        fn[arr] = rr[arr].values
        nulls.append(lr_oof(fn[levels["M2"]].values, yb, fold_arr, C_grid, "balanced_accuracy", rs))
    ok = abs(ba(yb, p_m2) - nr["M2_real"]["balanced_accuracy"]) < 1e-9 and \
        abs(np.mean([ba(yb, p) for p in nulls]) - nr["M2_null_ba_mean"]) < 1e-9
    check("Null: M2 real and M2-null BA reproduced by independent LR CV", ok,
          f"M1={ba(yb, p_m1):.3f} M2={ba(yb, p_m2):.3f} M2null mean={np.mean([ba(yb, p) for p in nulls]):.3f}")
    d, ci, _ = boot_diff(yb, p_m2, np.mean(nulls, axis=0), stat_ba, 4000, 99)
    report["null_real_minus_null_ba_independent"] = {"delta": d, "ci": list(ci)}
    # mixing diagnostics
    q_tab = pilot.groupby("swaps_per_edge")[["frac_edges_unchanged"] + arr].mean()
    frac = nf.groupby("event_id").frac_edges_unchanged.mean()
    hub = base_feat.loc[frac.index, ["indegree_gini", "outdegree_gini"]].max(axis=1)
    rho = float(pd.Series(frac.values).corr(pd.Series(hub.values), method="spearman"))
    sd0 = nf.groupby("event_id")[arr].std(ddof=1).eq(0).mean().to_dict()
    report["null_mixing"] = {"pilot_mean_by_swaps_per_edge": q_tab.round(4).reset_index().to_dict(orient="records"),
                             "frac_edges_unchanged_quantiles": frac.quantile([0, .25, .5, .75, 1]).round(3).tolist(),
                             "spearman_unchanged_vs_max_degree_gini": rho,
                             "share_events_zero_null_variance": {k: round(v, 3) for k, v in sd0.items()}}
    check("Null: mixing plateau (unchanged-edge fraction stable from 5 to 20 swaps/edge, within 0.02)",
          abs(q_tab.loc[5, "frac_edges_unchanged"] - q_tab.loc[20, "frac_edges_unchanged"]) < 0.02,
          f"unchanged={q_tab.frac_edges_unchanged.round(3).tolist()}, rho(unchanged, degree Gini)={rho:.2f}")

    # ========================================================================= STUDY 2
    print("\n=== Study 2 ===")
    s2 = json.load(open(run / "study2" / "results.json", encoding="utf-8"))
    vp = pd.read_parquet(run / "study2" / "view_predictions.parquet")
    mism, cons = [], []
    for key, r in s2["results"].items():
        cohort, K = key.rsplit("_K", 1)
        sub = vp[(vp.cohort == cohort) & (vp.K == int(K))]
        for cf, rep in r["conditions"].items():
            c, fs = cf.split("|")
            P = {o: sub[(sub.condition == c) & (sub.featureset == fs) & (sub.objective == o)].pivot(index="seed_index", columns="event_id", values="prob_campaign") for o in ("ba", "ll")}
            yy = sub.drop_duplicates("event_id").set_index("event_id").loc[P["ba"].columns, "label"].values
            sv = np.mean([ba(yy, P["ba"].loc[s].values) for s in P["ba"].index])
            ens = ba(yy, P["ba"].mean().values)
            svll = np.mean([ll(yy, P["ll"].loc[s].values) for s in P["ll"].index])
            if abs(sv - rep["single_view_ba_mean"]) > 1e-9 or abs(ens - rep["ensemble_ba"]) > 1e-9 or abs(svll - rep["single_view_logloss_mean"]) > 1e-9:
                mism.append((key, cf))
    check("S2 single-view and ensemble BA / log loss recomputed exactly from saved view predictions", not mism, f"mismatches={mism[:3]}")
    # views of an event never span folds: FK/KK predictions exist per event per seed only
    cnt = vp.groupby(["cohort", "K", "condition", "featureset", "objective", "event_id"]).seed_index.nunique()
    check("S2 each event has exactly 10 single-view predictions per condition", (cnt == 10).all())
    # contrasts recomputed (point exact, CI approx)
    gaps = []
    for key, cs in s2["contrasts"].items():
        cohort, K = key.rsplit("_K", 1)
        sub = vp[(vp.cohort == cohort) & (vp.K == int(K))]
        for name, v in cs.items():
            a, b = next((a, b) for n, a, b in __import__("study2_observation").CONTRASTS if n == name)
            for metric, obj, stat in (("ba", "ba", ba), ("log_loss", "ll", ll)):
                Pa = sub[(sub.condition == a[0]) & (sub.featureset == a[1]) & (sub.objective == obj)].pivot(index="seed_index", columns="event_id", values="prob_campaign")
                Pb = sub[(sub.condition == b[0]) & (sub.featureset == b[1]) & (sub.objective == obj)].pivot(index="seed_index", columns="event_id", values="prob_campaign")
                yy = sub.drop_duplicates("event_id").set_index("event_id").loc[Pa.columns, "label"].values
                f = lambda P, est, i: (np.mean([stat(yy[i], P.values[s][i]) for s in range(P.shape[0])]) if est == "single"
                                       else stat(yy[i], P.values.mean(axis=0)[i]))
                pt = f(Pa, a[2], np.arange(len(yy))) - f(Pb, b[2], np.arange(len(yy)))
                gaps.append(abs(pt - v[metric]["delta"]))
    check("S2 all contrast point estimates recomputed exactly (BA and log loss)", max(gaps) < 1e-9, f"max gap={max(gaps):.1e}")
    # budget-specific vs common: K=1000 cohorts are the same events
    b1000, c1000 = s2["results"]["budget_specific_K1000"], s2["results"]["common_K1000"]
    check("S2 common and budget-specific cohorts coincide at K=1000 and give identical results",
          b1000["n_events"] == c1000["n_events"] and b1000["conditions"] == c1000["conditions"])
    signs = {}
    for name in s2["contrasts"]["budget_specific_K250"]:
        sb = [np.sign(s2["contrasts"][f"budget_specific_K{K}"][name]["ba"]["delta"]) for K in (250, 500)]
        sc = [np.sign(s2["contrasts"][f"common_K{K}"][name]["ba"]["delta"]) for K in (250, 500)]
        signs[name] = sb == sc
    report["s2_sign_agreement_budget_vs_common"] = signs
    primary = [k for k in signs if k != "density_effect_frozen"]
    check("S2 primary contrast directions agree between budget-specific and common cohorts (K=250, 500)",
          all(signs[k] for k in primary), f"exploratory diagnostic disagreeing: {[k for k, v in signs.items() if not v]}")

    # ----------------------------------------------------------------------- endpoint mechanism
    print("\n=== Endpoint-count mechanism ===")
    edges = pd.read_parquet(Path(cfg["data"]["processed_dir"]) / "edges.parquet")
    views = pd.read_parquet(Path(cfg["data"]["processed_dir"]) / cfg["edge_budgets"]["views_file"])
    rng = np.random.default_rng(11)
    mc = []
    for eid in man.sort_values("n_edges").event_id.iloc[[10, 50, 90]]:
        ev = edges[edges.event_id == eid]
        E = len(ev)
        inc = pd.concat([ev.source, ev.target[ev.source != ev.target]]).value_counts().values
        lc = lambda n, k: gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)
        expN = float(np.sum(1 - np.where(E - inc >= 250, np.exp(lc(E - inc, 250) - lc(E, 250)), 0.0)))
        src, tgt = ev.source.values, ev.target.values
        sims = [len(set(src[i]) | set(tgt[i])) for i in (rng.choice(E, 250, replace=False) for _ in range(400))]
        mc.append({"event_id_crc": zlib.crc32(eid.encode()), "E": E, "formula": expN, "monte_carlo_mean": float(np.mean(sims)),
                   "mc_se": float(np.std(sims, ddof=1) / np.sqrt(len(sims)))})
    okmc = all(abs(r["formula"] - r["monte_carlo_mean"]) < 4 * r["mc_se"] + 0.5 for r in mc)
    check("Mechanism: closed-form E[N_K] matches Monte Carlo (400 draws, 3 events, K=250)", okmc,
          "; ".join(f"{r['formula']:.1f} vs {r['monte_carlo_mean']:.1f}±{r['mc_se']:.1f}" for r in mc))
    # what does E[N_K] reflect? variance explained by size, degree concentration, and both
    rows = []
    for eid in sorted(set(views[views.K == 250].event_id)):
        ev = edges[edges.event_id == eid]
        E = len(ev)
        inc = pd.concat([ev.source, ev.target[ev.source != ev.target]]).value_counts().values
        lc = lambda n, k: gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)
        rows.append({"event_id": eid, "logENK": np.log(np.sum(1 - np.where(E - inc >= 250, np.exp(lc(E - inc, 250) - lc(E, 250)), 0.0)))})
    md = pd.DataFrame(rows).set_index("event_id").join(feat)
    r2 = {}
    md["log_mean_degree"] = md.log_edge_count - md.log_node_count
    for name, cols in {"log N only": ["log_node_count"], "log E only": ["log_edge_count"],
                       "log N + log mean degree": ["log_node_count", "log_mean_degree"],
                       "size (log N, log E)": ["log_node_count", "log_edge_count"],
                       "degree concentration (in/out Gini)": ["indegree_gini", "outdegree_gini"],
                       "size + degree concentration": ["log_node_count", "log_edge_count", "indegree_gini", "outdegree_gini"]}.items():
        r2[name] = float(LinearRegression().fit(md[cols], md.logENK).score(md[cols], md.logENK))
    report["mechanism"] = {"monte_carlo": mc, "r2_log_expected_NK_K250": r2}
    print("Mechanism R2 for log E[N_K] at K=250:", "; ".join(f"{k}: {v:.3f}" for k, v in r2.items()))
    check("Mechanism: variance decomposition computed (interpretation reported separately)", len(r2) == 6)

    report["checks"] = CHECKS
    report["n_pass"] = sum(c["pass"] for c in CHECKS)
    report["n_checks"] = len(CHECKS)
    (out_dir / "verification_report.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
    print(f"\n{report['n_pass']}/{report['n_checks']} checks passed -> {out_dir / 'verification_report.json'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    main(ap.parse_args().config)
