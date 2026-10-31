"""
study2_observation.py
---------------------
Study 2: single-view retained-observation validity at fixed edge budgets K.

For each K and cohort (budget-specific eligible events; common cohort eligible
at every K), all conditions use the SAME events, the SAME outer folds (the
full-cohort event folds restricted to the cohort) and the SAME feature
definitions:

  FF  full-graph-trained model evaluated on full graphs        (reference)
  FK  full-graph-trained model applied to single K-edge views   (frozen transfer)
  KK  model trained on single K-edge views of the same seed     (observation-matched)

Feature sets (recomputed on every view; nothing from the full graph is used as
a view input):
  NK          log(1 + N_K)                       sampled endpoint count
  struct7     density, reciprocity, largest WCC, in/out Gini, coreness median/max
  struct6     struct7 without density (at fixed K, density = K / (N_K (N_K - 1)))
  NK_struct6  NK + struct6
  content     duplicate fraction, text concentration, length dispersion
  combined    NK + struct6 + content

Estimands, reported separately:
  single-view  metric computed per sampling seed (one view per event), then
               summarised over the 10 seeds
  ensemble     probabilities averaged over the 10 views per event, then classified
Repeated views are nested within events: event-level paired bootstrap only.

Mechanism: expected sampled endpoint count under uniform K-edge sampling
without replacement, E[N_K] = sum_v [1 - C(E - d_v, K) / C(E, K)], where d_v is
the number of distinct edges incident to v (a self-loop counts once).

Outputs: <run_dir>/study2/
"""

import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.special import gammaln
from scipy.stats import spearmanr
from sklearn.metrics import balanced_accuracy_score, log_loss, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import compute_all_features  # noqa: E402
from splits import make_event_folds  # noqa: E402
from train import make_logreg_pipeline, tune_logreg_C  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
EPS = 1e-6
STRUCT6 = ["reciprocity", "largest_wcc_fraction", "indegree_gini", "outdegree_gini", "coreness_median", "coreness_max"]
CONTENT = ["exact_dup_proportion", "text_concentration", "msg_length_dispersion"]
FSETS = {
    "NK": ["log_node_count"],
    "struct7": ["density"] + STRUCT6,
    "struct6": STRUCT6,
    "NK_struct6": ["log_node_count"] + STRUCT6,
    "content": CONTENT,
    "combined": ["log_node_count"] + STRUCT6 + CONTENT,
}
CONTRASTS = [  # (name, (condition, featureset, estimand) A, ... B)
    ("retrain_effect_struct6", ("KK", "struct6", "single"), ("FK", "struct6", "single")),
    ("retrain_effect_combined", ("KK", "combined", "single"), ("FK", "combined", "single")),
    ("structure_beyond_NK", ("KK", "NK_struct6", "single"), ("KK", "NK", "single")),
    ("content_beyond_NK_struct", ("KK", "combined", "single"), ("KK", "NK_struct6", "single")),
    ("ensemble_vs_single_combined", ("KK", "combined", "ensemble"), ("KK", "combined", "single")),
    ("transfer_loss_struct6", ("FK", "struct6", "single"), ("FF", "struct6", "single")),
    ("density_effect_frozen", ("FK", "struct7", "single"), ("FK", "struct6", "single")),
]


SCORING = {"ba": "balanced_accuracy", "ll": "neg_log_loss"}


def fit_predict(Xtr, ytr, Xte, config, objective):
    C = tune_logreg_C(Xtr, ytr, config["models"]["logreg"]["C_values"], 3, config, scoring=SCORING[objective])
    pipe = make_logreg_pipeline(config, C=C)
    pipe.fit(Xtr, ytr)
    return pipe.predict_proba(Xte)[:, 1]


def expected_endpoints(ev: pd.DataFrame, K: int) -> float:
    E = len(ev)
    inc = pd.concat([ev.source, ev.target[ev.source != ev.target]]).value_counts().values  # distinct incident edges per node
    logC = lambda n, k: gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)
    miss = np.where(E - inc >= K, np.exp(logC(E - inc, K) - logC(E, K)), 0.0)
    return float(np.sum(1.0 - miss))


def run_conditions(full, views, cohort, fold_map, config, K):
    """Returns per-(condition, featureset, objective) arrays probs[seed, event], y, event ids.
    Hyperparameters are tuned inside the outer training fold only, separately for
    each objective (BA or log loss)."""
    ev_ids = sorted(cohort)
    y = full.loc[ev_ids, "label"].values.astype(int)
    folds = np.array([fold_map[e] for e in ev_ids])
    seeds = sorted(views.seed.unique())
    vk = views[(views.K == K) & views.event_id.isin(ev_ids)]
    vmat = {s: vk[vk.seed == s].set_index("event_id").loc[ev_ids] for s in seeds}
    out = {}
    for fs, cols in FSETS.items():
        Xfull = full.loc[ev_ids, cols].values
        for obj in SCORING:
            ff = np.zeros(len(ev_ids))
            fk = np.zeros((len(seeds), len(ev_ids)))
            kk = np.zeros((len(seeds), len(ev_ids)))
            for k in np.unique(folds):
                tr, te = folds != k, folds == k
                # full-graph-trained model (trained on the same eligible training events)
                C = tune_logreg_C(Xfull[tr], y[tr], config["models"]["logreg"]["C_values"], 3, config, scoring=SCORING[obj])
                pipe = make_logreg_pipeline(config, C=C).fit(Xfull[tr], y[tr])
                ff[te] = pipe.predict_proba(Xfull[te])[:, 1]
                for si, s_ in enumerate(seeds):
                    Xv = vmat[s_][cols].values
                    fk[si, te] = pipe.predict_proba(Xv[te])[:, 1]
                    kk[si, te] = fit_predict(Xv[tr], y[tr], Xv[te], config, obj)
            out[("FF", fs, obj)] = np.tile(ff, (len(seeds), 1))
            out[("FK", fs, obj)] = fk
            out[("KK", fs, obj)] = kk
    return out, y, ev_ids


def summarise(P, PL, y):
    """BA from BA-tuned probabilities P; log loss and AUC from log-loss-tuned probabilities PL.
    single-view: per-seed metrics summarised over seeds; ensemble: mean prob over seeds."""
    ba = [balanced_accuracy_score(y, (p >= 0.5).astype(int)) for p in P]
    ll = [log_loss(y, np.clip(p, EPS, 1 - EPS), labels=[0, 1]) for p in PL]
    auc = [roc_auc_score(y, p) for p in PL]
    pe, pel = P.mean(axis=0), PL.mean(axis=0)
    return {"single_view_ba_mean": float(np.mean(ba)), "single_view_ba_min": float(np.min(ba)), "single_view_ba_max": float(np.max(ba)),
            "single_view_logloss_mean": float(np.mean(ll)), "single_view_auc_mean": float(np.mean(auc)),
            "ensemble_ba": float(balanced_accuracy_score(y, (pe >= 0.5).astype(int))),
            "ensemble_logloss": float(log_loss(y, np.clip(pel, EPS, 1 - EPS), labels=[0, 1])),
            "ensemble_auc": float(roc_auc_score(y, pel))}


def estimand_ll(P, y, idx, estimand):
    if estimand == "single":
        return float(np.mean([log_loss(y[idx], np.clip(p[idx], EPS, 1 - EPS), labels=[0, 1]) for p in P]))
    pe = P.mean(axis=0)
    return float(log_loss(y[idx], np.clip(pe[idx], EPS, 1 - EPS), labels=[0, 1]))


def estimand_ba(P, y, idx, estimand):
    if estimand == "single":
        return float(np.mean([balanced_accuracy_score(y[idx], (p[idx] >= 0.5).astype(int)) for p in P]))
    pe = P.mean(axis=0)
    return float(balanced_accuracy_score(y[idx], (pe[idx] >= 0.5).astype(int)))


def paired(P_a, P_b, y, ea, eb, n_boot, seed, metric="ba"):
    f = estimand_ba if metric == "ba" else estimand_ll
    rng = np.random.default_rng(seed)
    n = len(y)
    full = np.arange(n)
    point = f(P_a, y, full, ea) - f(P_b, y, full, eb)
    d = []
    for _ in range(n_boot):
        i = rng.integers(0, n, n)
        if len(set(y[i])) < 2:
            continue
        d.append(f(P_a, y, i, ea) - f(P_b, y, i, eb))
    d = np.asarray(d)
    return {"delta": float(point), "ci": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
            "p_bootstrap": float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean())))}


def main(config_path: str) -> None:
    config = yaml.safe_load(open(config_path, encoding="utf-8"))
    s2 = config["study2"]
    run_dir = Path(config["output"]["run_dir"])
    out_dir = run_dir / "study2"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_parquet(Path(config["data"]["manifests_dir"]) / "manifest.parquet")
    edges = pd.read_parquet(Path(config["data"]["processed_dir"]) / "edges.parquet")
    views = pd.read_parquet(Path(config["data"]["processed_dir"]) / config["edge_budgets"]["views_file"])
    feat_path = run_dir / "study1" / "full_graph_features.parquet"
    full = pd.read_parquet(feat_path) if feat_path.exists() else compute_all_features(edges, manifest, config)["combined"]
    for c in STRUCT6:
        assert views[c].nunique() > 1, f"view feature {c} constant"
    fold_map = make_event_folds(manifest, config["splits"]["n_folds"], config["splits"]["random_seed"])
    Ks = config["edge_budgets"]["K_values"]
    elig = {K: set(views[views.K == K].event_id) for K in Ks}
    common = set.intersection(*elig.values())

    results, contrasts, long_rows = {}, {}, []
    for cohort_name in ("budget_specific", "common"):
        for K in Ks:
            cohort = elig[K] if cohort_name == "budget_specific" else common
            res, y, ev_ids = run_conditions(full, views, cohort, fold_map, config, K)
            key = f"{cohort_name}_K{K}"
            n_camp = int(y.sum())
            results[key] = {"n_events": len(y), "n_campaign": n_camp, "n_comparison": int(len(y) - n_camp),
                            "estimand_rule": "BA from objective=ba fits; log loss and AUC from objective=ll fits",
                            "conditions": {f"{c}|{fs}": summarise(res[(c, fs, "ba")], res[(c, fs, "ll")], y)
                                           for (c, fs, o) in res if o == "ba"}}
            contrasts[key] = {name: {"ba": paired(res[(a[0], a[1], "ba")], res[(b[0], b[1], "ba")], y, a[2], b[2], s2["n_bootstrap"], s2["bootstrap_seed"], "ba"),
                                     "log_loss": paired(res[(a[0], a[1], "ll")], res[(b[0], b[1], "ll")], y, a[2], b[2], s2["n_bootstrap"], s2["bootstrap_seed"], "ll")}
                              for name, a, b in CONTRASTS}
            for (c, fs, o), P in res.items():
                for si in range(P.shape[0]):
                    long_rows += [{"cohort": cohort_name, "K": K, "condition": c, "featureset": fs, "objective": o, "seed_index": si,
                                   "event_id": e, "label": int(lbl), "prob_campaign": float(p)} for e, lbl, p in zip(ev_ids, y, P[si])]
            r = results[key]["conditions"]
            print(f"[{key}] n={len(y)} ({n_camp}/{len(y) - n_camp}) | " + " | ".join(
                f"{c}|{fs}: sv={r[f'{c}|{fs}']['single_view_ba_mean']:.3f} ens={r[f'{c}|{fs}']['ensemble_ba']:.3f}"
                for c, fs in [("FF", "struct6"), ("FK", "struct6"), ("KK", "struct6"), ("KK", "NK"), ("KK", "NK_struct6"), ("KK", "combined"), ("FK", "combined")]))
    pd.DataFrame(long_rows).to_parquet(out_dir / "view_predictions.parquet", index=False)

    # Mechanism: expected vs observed sampled endpoint count, and its label information
    mech = {}
    for K in Ks:
        rows = []
        for eid in sorted(elig[K]):
            ev = edges[edges.event_id == eid]
            obs = np.expm1(views[(views.K == K) & (views.event_id == eid)].log_node_count).mean()
            rows.append({"event_id": eid, "expected_NK": expected_endpoints(ev, K), "observed_NK_mean": float(obs),
                         "log_N_full": float(full.loc[eid, "log_node_count"]), "label": int(full.loc[eid, "label"])})
        df = pd.DataFrame(rows)
        rel = (df.observed_NK_mean - df.expected_NK) / df.expected_NK
        mech[f"K{K}"] = {"n": len(df), "max_abs_rel_error_expected_vs_observed": float(rel.abs().max()),
                         "spearman_expectedNK_vs_logN_full": float(spearmanr(df.expected_NK, df.log_N_full)[0]),
                         "auc_expectedNK_label": float(roc_auc_score(df.label, -df.expected_NK)),
                         "auc_log_N_full_label": float(roc_auc_score(df.label, -df.log_N_full)),
                         "median_expectedNK_campaign": float(df[df.label == 1].expected_NK.median()),
                         "median_expectedNK_comparison": float(df[df.label == 0].expected_NK.median())}
        print(f"[mechanism K={K}] " + json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in mech[f'K{K}'].items()}))

    (out_dir / "results.json").write_text(json.dumps({"results": results, "contrasts": contrasts, "mechanism": mech,
                                                       "feature_sets": FSETS}, indent=2), encoding="utf-8")
    for key, cs in contrasts.items():
        print(key, " | ".join(f"{n}: BA {v['ba']['delta']:+.3f} [{v['ba']['ci'][0]:+.3f},{v['ba']['ci'][1]:+.3f}] "
                                f"LL {v['log_loss']['delta']:+.3f} [{v['log_loss']['ci'][0]:+.3f},{v['log_loss']['ci'][1]:+.3f}]"
                                for n, v in cs.items()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    main(ap.parse_args().config)
