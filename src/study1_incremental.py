"""
study1_incremental.py
---------------------
Study 1: incremental predictive information beyond graph scale and degree.

Nested feature levels (full cohort, identical event-level outer folds):
  M0   log N, log E
  M0q  M0 + log N^2, log E^2, log N * log E      (nonlinear count control)
  M1   M0q + in/out-degree Gini                   (degree concentration)
  M2   M1 + reciprocity, largest-WCC fraction, coreness median/max (arrangement)
  M3   M0q + content (duplicate fraction, text concentration, length dispersion)
  M4   M2 + content
  M4d  M4 + density   (diagnostic: density = E / (N (N-1)) is determined by N, E)

Confirmatory contrasts (Holm-adjusted): C1 M4 vs M0q, C2 M2 vs M1, C3 M3 vs M0q.
Estimands: paired differences in balanced accuracy (BA) and log loss on
identical events, with an event-level paired bootstrap of the fixed
out-of-fold predictions. Refitting/split variability is reported separately
from re-drawn fold splits (not independent replicates).

Also: degree-preserving rewiring null for the arrangement features (M2), and an
exploratory size-matching sensitivity.

Outputs: <run_dir>/study1/
"""

import sys
import json
import zlib
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import binomtest
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import compute_all_features, edges_to_digraph, extract_structural_features  # noqa: E402
from rewiring import rewire_directed, assert_degree_preserved  # noqa: E402
from splits import make_event_folds  # noqa: E402
from train import run_cv  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

SCALE = ["log_node_count", "log_edge_count"]
QUAD = ["log_n_sq", "log_e_sq", "log_n_x_log_e"]
DEGREE = ["indegree_gini", "outdegree_gini"]
ARRANGE = ["reciprocity", "largest_wcc_fraction", "coreness_median", "coreness_max"]
CONTENT = ["exact_dup_proportion", "text_concentration", "msg_length_dispersion"]
LEVELS = {
    "M0": SCALE,
    "M0q": SCALE + QUAD,
    "M1": SCALE + QUAD + DEGREE,
    "M2": SCALE + QUAD + DEGREE + ARRANGE,
    "M3": SCALE + QUAD + CONTENT,
    "M4": SCALE + QUAD + DEGREE + ARRANGE + CONTENT,
    "M4d": SCALE + QUAD + DEGREE + ARRANGE + CONTENT + ["density"],
}
CONFIRMATORY = {"C1": ("M4", "M0q"), "C2": ("M2", "M1"), "C3": ("M3", "M0q")}
EXPLORATORY = {"E1": ("M1", "M0q"), "E2": ("M4", "M3"), "E3": ("M4", "M2"), "E4": ("M0q", "M0"),
               "E5": ("M4d", "M4")}
EPS = 1e-6


def add_quadratic(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["log_n_sq"] = df["log_node_count"] ** 2
    df["log_e_sq"] = df["log_edge_count"] ** 2
    df["log_n_x_log_e"] = df["log_node_count"] * df["log_edge_count"]
    return df


SCORING = {"ba": "balanced_accuracy", "ll": "neg_log_loss"}


def tuned_hgbt_cv(feat_df, fold_map, config, label, objective="ba"):
    """HGBT with hyperparameters tuned inside each training fold (inner 3-fold CV) for the given objective."""
    hc = config["study1"]["hgbt_grid"]
    df = feat_df.copy()
    df["fold_id"] = df.index.map(fold_map)
    cols = [c for c in df.columns if c not in {"label", "fold_id"}]
    rows = []
    for k in sorted(df.fold_id.unique()):
        tr, te = df[df.fold_id != k], df[df.fold_id == k]
        gs = GridSearchCV(
            HistGradientBoostingClassifier(class_weight="balanced", random_state=config["models"]["hgbt"]["random_state"]),
            hc, scoring=SCORING[objective],
            cv=StratifiedKFold(3, shuffle=True, random_state=0), n_jobs=1)
        gs.fit(tr[cols].values, tr["label"].values.astype(int))
        p = gs.predict_proba(te[cols].values)[:, 1]
        for eid, prob, y in zip(te.index, p, te["label"].values.astype(int)):
            rows.append({"event_id": eid, "fold_id": int(k), "label": int(y), "prob_campaign": float(prob),
                         "pred_label": int(prob >= 0.5), "experiment": label, "model": "hgbt",
                         "params": json.dumps(gs.best_params_, sort_keys=True)})
    return pd.DataFrame(rows)


def metrics(y, p):
    yhat = (p >= 0.5).astype(int)
    return {"balanced_accuracy": float(balanced_accuracy_score(y, yhat)),
            "log_loss": float(log_loss(y, np.clip(p, EPS, 1 - EPS), labels=[0, 1])),
            "roc_auc": float(roc_auc_score(y, p)) if len(set(y)) == 2 else None,
            "n_events": int(len(y))}


def paired_bootstrap(y, pa, pb, n_boot, seed):
    """Event-level paired bootstrap of (A - B) for BA, log loss and AUC on fixed OOF predictions."""
    rng = np.random.default_rng(seed)
    n = len(y)
    ya, yb = (pa >= 0.5).astype(int), (pb >= 0.5).astype(int)
    la = -(y * np.log(np.clip(pa, EPS, 1)) + (1 - y) * np.log(np.clip(1 - pa, EPS, 1)))
    lb = -(y * np.log(np.clip(pb, EPS, 1)) + (1 - y) * np.log(np.clip(1 - pb, EPS, 1)))
    d_ba, d_ll, d_auc = [], [], []
    for _ in range(n_boot):
        i = rng.integers(0, n, n)
        if len(set(y[i])) < 2:
            continue
        d_ba.append(balanced_accuracy_score(y[i], ya[i]) - balanced_accuracy_score(y[i], yb[i]))
        d_ll.append(la[i].mean() - lb[i].mean())
        d_auc.append(roc_auc_score(y[i], pa[i]) - roc_auc_score(y[i], pb[i]))
    d_ba, d_ll, d_auc = map(np.asarray, (d_ba, d_ll, d_auc))
    point_ba = balanced_accuracy_score(y, ya) - balanced_accuracy_score(y, yb)
    point_ll = la.mean() - lb.mean()

    def p_two_sided(d):
        # bootstrap percentile p-value for H0: difference = 0
        return float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean())))

    disc_a = int(((ya == y) & (yb != y)).sum())
    disc_b = int(((ya != y) & (yb == y)).sum())
    mcn = binomtest(disc_a, disc_a + disc_b, 0.5).pvalue if disc_a + disc_b > 0 else 1.0
    return {
        "delta_ba": float(point_ba), "delta_ba_ci": [float(np.percentile(d_ba, 2.5)), float(np.percentile(d_ba, 97.5))],
        "p_ba_bootstrap": p_two_sided(d_ba),
        "delta_logloss": float(point_ll), "delta_logloss_ci": [float(np.percentile(d_ll, 2.5)), float(np.percentile(d_ll, 97.5))],
        "p_logloss_bootstrap": p_two_sided(d_ll),
        "delta_auc": float(roc_auc_score(y, pa) - roc_auc_score(y, pb)),
        "delta_auc_ci": [float(np.percentile(d_auc, 2.5)), float(np.percentile(d_auc, 97.5))],
        "mcnemar_a_right_b_wrong": disc_a, "mcnemar_b_right_a_wrong": disc_b, "mcnemar_exact_p": float(mcn),
        "n_boot_used": int(len(d_ba)),
    }


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for r, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - r) * p))
        out[k] = running
    return out


def run_level(feat, fold_map, config, level, model, objective="ba"):
    """Out-of-fold predictions; hyperparameters tuned in the training folds only, for `objective`."""
    df = feat[["label"] + LEVELS[level]]
    if model == "logreg":
        preds, _ = run_cv(df, fold_map, config, level, "logreg", scoring=SCORING[objective])
    else:
        preds = tuned_hgbt_cv(df, fold_map, config, level, objective)
    return preds.set_index("event_id").sort_index()


def contrasts(preds, contrast_map, n_boot, seed):
    out = {}
    for name, (a, b) in contrast_map.items():
        pa, pb = preds[a], preds[b]
        assert pa.index.equals(pb.index)
        out[name] = {"a": a, "b": b, **paired_bootstrap(pa.label.values, pa.prob_campaign.values,
                                                          pb.prob_campaign.values, n_boot, seed)}
    return out


# ---------------------------------------------------------------------------
# Matching sensitivity (exploratory)
# ---------------------------------------------------------------------------
def greedy_match(manifest, cols, caliper_sd, order_seed):
    X = np.column_stack([np.log1p(manifest[c].values) for c in cols])
    sd = X.std(axis=0, ddof=1)
    camp = list(np.where(manifest.label.values == 1)[0])
    comp = set(np.where(manifest.label.values == 0)[0])
    np.random.default_rng(order_seed).shuffle(camp)
    pairs = []
    for i in camp:
        cands = [j for j in comp if np.all(np.abs(X[j] - X[i]) <= caliper_sd * sd)]
        if not cands:
            continue
        j = min(cands, key=lambda j: float(np.sum(((X[j] - X[i]) / sd) ** 2)))
        pairs.append((i, j))
        comp.discard(j)
    return pairs


def smd(v, lab):
    c, k = v[lab == 1], v[lab == 0]
    return float((c.mean() - k.mean()) / np.sqrt((c.var(ddof=1) + k.var(ddof=1)) / 2))


def matched_eval(feat, manifest, pairs, config, levels, n_folds):
    ids = [manifest.event_id.iloc[i] for p in pairs for i in p]
    pair_of = {manifest.event_id.iloc[i]: k for k, p in enumerate(pairs) for i in p}
    # pairs are kept together: fold assigned per pair
    rng = np.random.default_rng(config["splits"]["random_seed"])
    pf = rng.permutation(len(pairs)) % n_folds
    fold_map = {e: int(pf[pair_of[e]]) for e in ids}
    sub = feat.loc[ids]
    res = {}
    for lv in levels:
        p = run_level(sub, fold_map, config, lv, "logreg")
        res[lv] = metrics(p.label.values, p.prob_campaign.values)["balanced_accuracy"]
    lab = manifest.set_index("event_id").loc[ids, "label"].values
    return res, {"n_pairs": len(pairs),
                 "smd_log_nodes": smd(np.log1p(manifest.set_index("event_id").loc[ids, "n_nodes"].values), lab),
                 "smd_log_edges": smd(np.log1p(manifest.set_index("event_id").loc[ids, "n_edges"].values), lab)}


def main(config_path: str, parts: list[str]) -> None:
    config = yaml.safe_load(open(config_path, encoding="utf-8"))
    s1 = config["study1"]
    out_dir = Path(config["output"]["run_dir"]) / "study1"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_parquet(Path(config["data"]["manifests_dir"]) / "manifest.parquet")
    edges = pd.read_parquet(Path(config["data"]["processed_dir"]) / "edges.parquet")
    feat_path = out_dir / "full_graph_features.parquet"
    if feat_path.exists():
        feat = pd.read_parquet(feat_path)
    else:
        print("Computing full-graph features...")
        feat = compute_all_features(edges, manifest, config)["combined"]
        feat.to_parquet(feat_path)
    feat = add_quadratic(feat)
    for c in ARRANGE + DEGREE + CONTENT + SCALE:
        assert feat[c].nunique() > 1, f"feature {c} is constant across the cohort"
    fold_map = make_event_folds(manifest, config["splits"]["n_folds"], config["splits"]["random_seed"])

    if "nested" in parts:
        # BA estimands use BA-tuned fits; log-loss estimands use log-loss-tuned fits.
        # AUC (secondary) is reported for both procedures. Same outer folds throughout.
        results = {"levels": LEVELS, "models": {}, "estimand_rule": "BA from objective=ba fits; log loss from objective=ll fits"}
        all_preds = []
        nb, bs = s1["n_bootstrap"], s1["bootstrap_seed"]
        for model in ("logreg", "hgbt"):
            preds = {obj: {} for obj in SCORING}
            for obj in SCORING:
                for lv in LEVELS:
                    p = run_level(feat, fold_map, config, lv, model, obj)
                    preds[obj][lv] = p
                    all_preds.append(p.reset_index().assign(model=model, objective=obj))
            perf = {lv: {"balanced_accuracy": metrics(preds["ba"][lv].label.values, preds["ba"][lv].prob_campaign.values)["balanced_accuracy"],
                         "log_loss": metrics(preds["ll"][lv].label.values, preds["ll"][lv].prob_campaign.values)["log_loss"],
                         "roc_auc_ba_fit": metrics(preds["ba"][lv].label.values, preds["ba"][lv].prob_campaign.values)["roc_auc"],
                         "roc_auc_ll_fit": metrics(preds["ll"][lv].label.values, preds["ll"][lv].prob_campaign.values)["roc_auc"]}
                    for lv in LEVELS}
            conf_ba = contrasts(preds["ba"], CONFIRMATORY, nb, bs)
            conf_ll = contrasts(preds["ll"], CONFIRMATORY, nb, bs)
            h_ba = holm({k: v["p_ba_bootstrap"] for k, v in conf_ba.items()})
            h_ll = holm({k: v["p_logloss_bootstrap"] for k, v in conf_ll.items()})
            confirm = {}
            for k in CONFIRMATORY:
                a, b = CONFIRMATORY[k]
                confirm[k] = {"a": a, "b": b,
                              "ba": {kk: conf_ba[k][kk] for kk in ("delta_ba", "delta_ba_ci", "p_ba_bootstrap",
                                                                   "mcnemar_a_right_b_wrong", "mcnemar_b_right_a_wrong", "mcnemar_exact_p")}
                                    | {"p_holm": h_ba[k]},
                              "log_loss": {kk: conf_ll[k][kk] for kk in ("delta_logloss", "delta_logloss_ci", "p_logloss_bootstrap")}
                                          | {"p_holm": h_ll[k]},
                              "auc_ba_fit": {"delta_auc": conf_ba[k]["delta_auc"], "delta_auc_ci": conf_ba[k]["delta_auc_ci"]},
                              "auc_ll_fit": {"delta_auc": conf_ll[k]["delta_auc"], "delta_auc_ci": conf_ll[k]["delta_auc_ci"]}}
            expl_ba, expl_ll = contrasts(preds["ba"], EXPLORATORY, nb, bs), contrasts(preds["ll"], EXPLORATORY, nb, bs)
            results["models"][model] = {
                "performance": perf, "confirmatory": confirm,
                "exploratory": {k: {"a": expl_ba[k]["a"], "b": expl_ba[k]["b"],
                                    "delta_ba": expl_ba[k]["delta_ba"], "delta_ba_ci": expl_ba[k]["delta_ba_ci"],
                                    "delta_logloss": expl_ll[k]["delta_logloss"], "delta_logloss_ci": expl_ll[k]["delta_logloss_ci"],
                                    "delta_auc_ll_fit": expl_ll[k]["delta_auc"], "delta_auc_ll_fit_ci": expl_ll[k]["delta_auc_ci"]}
                                for k in EXPLORATORY}}
            print(f"[{model}] " + " | ".join(f"{lv} BA={v['balanced_accuracy']:.3f} LL={v['log_loss']:.3f} AUC={v['roc_auc_ll_fit']:.3f}"
                                            for lv, v in perf.items()))
            for k, v in confirm.items():
                print(f"  {k} {v['a']}-{v['b']}: dBA={v['ba']['delta_ba']:+.3f} {np.round(v['ba']['delta_ba_ci'], 3)} holm={v['ba']['p_holm']:.3f} | "
                      f"dLL={v['log_loss']['delta_logloss']:+.3f} {np.round(v['log_loss']['delta_logloss_ci'], 3)} holm={v['log_loss']['p_holm']:.3f} | "
                      f"dAUC(ll)={v['auc_ll_fit']['delta_auc']:+.3f} {np.round(v['auc_ll_fit']['delta_auc_ci'], 3)}")
        pd.concat(all_preds).to_parquet(out_dir / "oof_predictions.parquet", index=False)

        # Refitting / split variability (LR): re-drawn outer splits. Not independent replicates.
        rows = []
        for sseed in s1["split_seeds"]:
            fm = make_event_folds(manifest, config["splits"]["n_folds"], sseed)
            pb = {lv: run_level(feat, fm, config, lv, "logreg", "ba") for lv in LEVELS}
            pl = {lv: run_level(feat, fm, config, lv, "logreg", "ll") for lv in LEVELS}
            ba = {lv: metrics(p.label.values, p.prob_campaign.values)["balanced_accuracy"] for lv, p in pb.items()}
            ll = {lv: metrics(p.label.values, p.prob_campaign.values)["log_loss"] for lv, p in pl.items()}
            au = {lv: metrics(p.label.values, p.prob_campaign.values)["roc_auc"] for lv, p in pl.items()}
            rows.append({"split_seed": sseed, **{f"ba_{k}": v for k, v in ba.items()}, **{f"ll_{k}": v for k, v in ll.items()},
                         **{f"dBA_{c}": ba[a] - ba[b] for c, (a, b) in CONFIRMATORY.items()},
                         **{f"dLL_{c}": ll[a] - ll[b] for c, (a, b) in CONFIRMATORY.items()},
                         **{f"dAUC_{c}": au[a] - au[b] for c, (a, b) in CONFIRMATORY.items()}})
        rep_df = pd.DataFrame(rows)
        rep_df.to_csv(out_dir / "repeated_splits_lr.csv", index=False)
        results["repeated_splits_lr_summary"] = {
            c: {f"{m}_{st}": float(getattr(rep_df[f"{m}_{c}"], st)()) for m in ("dBA", "dLL", "dAUC") for st in ("mean", "min", "max")}
            for c in CONFIRMATORY}
        print("repeated splits (LR):", json.dumps(results["repeated_splits_lr_summary"], indent=1))
        (out_dir / "nested_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    if "null" in parts:
        nc = s1["null_model"]
        # Pilot: mixing of arrangement features vs swaps per edge on a few events
        pilot_ids = manifest.sort_values("n_edges").event_id.iloc[np.linspace(0, len(manifest) - 1, nc["pilot_events"]).astype(int)]
        pilot = []
        for eid in pilot_ids:
            G = edges_to_digraph(edges[edges.event_id == eid])
            for q in nc["pilot_swaps_per_edge"]:
                R, st = rewire_directed(G, q, seed=nc["seed"], return_stats=True)
                assert_degree_preserved(G, R)
                f = extract_structural_features(R)
                pilot.append({"event_id": eid, "swaps_per_edge": q, **st, **{k: f[k] for k in ARRANGE}})
        pilot = pd.DataFrame(pilot)
        pilot.to_csv(out_dir / "null_pilot.csv", index=False)
        print(pilot.groupby("swaps_per_edge")[["frac_edges_unchanged"] + ARRANGE].mean().round(4))

        q = nc["swaps_per_edge"]
        null_rows = []
        for r in range(nc["realizations"]):
            for eid, ev in edges.groupby("event_id"):
                G = edges_to_digraph(ev)
                R, st = rewire_directed(G, q, seed=nc["seed"] + 1000 * r + zlib.crc32(eid.encode("utf-8")) % 997, return_stats=True)
                assert_degree_preserved(G, R)
                f = extract_structural_features(R)
                null_rows.append({"event_id": eid, "realization": r, "frac_edges_unchanged": st["frac_edges_unchanged"],
                                  **{k: f[k] for k in ARRANGE + DEGREE + ["density"]}})
        null = pd.DataFrame(null_rows)
        null.to_parquet(out_dir / "null_features.parquet", index=False)
        # degree features must be identical in null graphs
        chk = null.groupby("event_id")[DEGREE + ["density"]].first().join(feat[DEGREE + ["density"]], rsuffix="_obs")
        for c in DEGREE + ["density"]:
            assert np.allclose(chk[c], chk[c + "_obs"]), f"null changed {c}"

        res = {"swaps_per_edge": q, "realizations": nc["realizations"],
               "mean_frac_edges_unchanged": float(null.frac_edges_unchanged.mean())}
        real = {lv: run_level(feat, fold_map, config, lv, "logreg", "ba") for lv in ("M1", "M2")}
        real_ll = {lv: run_level(feat, fold_map, config, lv, "logreg", "ll") for lv in ("M1", "M2")}
        y = real["M2"].label.values
        ba_real = metrics(y, real["M2"].prob_campaign.values)["balanced_accuracy"]
        null_probs, null_probs_ll, per_r = [], [], []
        for r in range(nc["realizations"]):
            nf = feat.copy()
            nr = null[null.realization == r].set_index("event_id")
            nf.loc[nr.index, ARRANGE] = nr[ARRANGE].values
            p = run_level(nf, fold_map, config, "M2", "logreg", "ba")
            pll = run_level(nf, fold_map, config, "M2", "logreg", "ll")
            assert p.index.equals(real["M2"].index) and pll.index.equals(real["M2"].index)
            null_probs.append(p.prob_campaign.values)
            null_probs_ll.append(pll.prob_campaign.values)
            per_r.append(metrics(y, p.prob_campaign.values))
        pn = np.mean(null_probs, axis=0)
        res["M2_real"] = metrics(y, real["M2"].prob_campaign.values)
        res["M1"] = metrics(y, real["M1"].prob_campaign.values)
        res["M2_null_per_realization"] = per_r
        res["M2_null_ba_mean"] = float(np.mean([m["balanced_accuracy"] for m in per_r]))
        res["M2_real_vs_null_avg"] = paired_bootstrap(y, real["M2"].prob_campaign.values, pn, s1["n_bootstrap"], s1["bootstrap_seed"])
        res["M2_null_avg_vs_M1"] = paired_bootstrap(y, pn, real["M1"].prob_campaign.values, s1["n_bootstrap"], s1["bootstrap_seed"])
        pn_ll = np.mean(null_probs_ll, axis=0)
        res["log_loss_estimand"] = {
            "M2_real_ll_fit": metrics(y, real_ll["M2"].prob_campaign.values),
            "M1_ll_fit": metrics(y, real_ll["M1"].prob_campaign.values),
            "M2_real_vs_null_avg_ll_fit": paired_bootstrap(y, real_ll["M2"].prob_campaign.values, pn_ll, s1["n_bootstrap"], s1["bootstrap_seed"])}
        res["note"] = "BA fields use objective=ba fits; log_loss_estimand uses objective=ll fits."
        # observed-vs-null standardised differences per feature (descriptive)
        z = {}
        g = null.groupby("event_id")[ARRANGE]
        mu, sdv = g.mean(), g.std(ddof=1).replace(0, np.nan)
        for c in ARRANGE:
            zc = (feat.loc[mu.index, c] - mu[c]) / sdv[c]
            lab = feat.loc[mu.index, "label"]
            z[c] = {"median_z_campaign": float(zc[lab == 1].median()), "median_z_comparison": float(zc[lab == 0].median()),
                    "share_undefined_sd0": float(sdv[c].isna().mean())}
        res["observed_vs_null_z"] = z
        print(f"M2 real BA={ba_real:.3f}; M2 null BA mean={res['M2_null_ba_mean']:.3f}; real-null dBA={res['M2_real_vs_null_avg']['delta_ba']:+.3f} "
              f"{np.round(res['M2_real_vs_null_avg']['delta_ba_ci'], 3)}")
        (out_dir / "null_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")

    if "matching" in parts:
        mc = s1["matching"]
        lv = ["M0", "M1", "M2", "M3", "M4"]
        out = {"note": "Exploratory. Pairs kept in the same outer fold. Order seeds are not independent datasets.",
               "node_only": [], "node_edge": []}
        for key, cols in (("node_only", ["n_nodes"]), ("node_edge", ["n_nodes", "n_edges"])):
            for oseed in mc["order_seeds"]:
                pairs = greedy_match(manifest, cols, config["matching"]["caliper_sd_fraction"], oseed)
                if len(pairs) < config["splits"]["n_folds"] * 2:
                    out[key].append({"order_seed": oseed, "n_pairs": len(pairs), "skipped": True})
                    continue
                ba, bal = matched_eval(feat, manifest, pairs, config, lv, config["splits"]["n_folds"])
                out[key].append({"order_seed": oseed, **bal, **{f"ba_{k}": v for k, v in ba.items()}})
            df = pd.DataFrame([r for r in out[key] if not r.get("skipped")])
            if len(df):
                print(f"[matching {key}] pairs {df.n_pairs.min()}-{df.n_pairs.max()} | " +
                      " ".join(f"{k}: {df[f'ba_{k}'].median():.3f} [{df[f'ba_{k}'].min():.3f},{df[f'ba_{k}'].max():.3f}]" for k in lv))
        (out_dir / "matching_sensitivity.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    ap.add_argument("--parts", default="nested,null,matching")
    a = ap.parse_args()
    main(a.config, a.parts.split(","))
