"""
revision_supplement.py
----------------------
Supplementary analyses for the November 2026 paper revision, computed from the
saved outputs of the corrected run (outputs/run_v2, read only) and the H1
experiment (outputs/revision_h1_cgrid, from src/h1_c_grid.py). No model is
refitted here except the event-grouped linear regressions in (4).

  1. Event-ID check: at each budget, FF, FK and KK conditions score identical
     events; cohort sizes and class counts.
  2. RQ2 baselines: single-view model vs full-graph model with the same features
     (all features; N_K alone), paired on the same events, using Study 2's own
     single-view estimand and paired bootstrap (study2_observation.paired).
  3. N_K vs structure within view-trained models (single-view BA).
  4. Overlap of N_K and structure: event-grouped cross-validated R^2 of
     log N_K predicted linearly from the six structural features, per budget.
  5. Degree-preserving null: how often each arrangement feature changes.
  6. Repeated-split sign counts for the primary contrasts.
  7. H1 summary (count-model regularisation grid).
  8. Repeated campaign hashtags and their fold placement.

Output: output.revision_supplement in the config (default config:
outputs/revision_supplement/supplement.json), read by src/export_latex_results.py
and src/export_frontend_data.py together with paper_results.json. Run
src/h1_c_grid.py first; it writes output.revision_h1_dir.

Usage: python src/revision_supplement.py [--config configs/v2_coreness_fix.yaml]
"""

import re
import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from study2_observation import paired  # noqa: E402
from splits import make_event_folds  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

STRUCT6 = ["indegree_gini", "outdegree_gini", "reciprocity", "largest_wcc_fraction", "coreness_median", "coreness_max"]
ARRANGE = ["reciprocity", "largest_wcc_fraction", "coreness_median", "coreness_max"]
BUDGETS = (250, 500, 1000)


def ci(d):
    return {"delta": d["delta"], "ci": d["ci"]}


def main(config_path):
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    run = Path(cfg["output"]["run_dir"])
    s2 = cfg["study2"]
    nb, bs = s2["n_bootstrap"], s2["bootstrap_seed"]
    vp = pd.read_parquet(run / "study2" / "view_predictions.parquet")
    out = {"_source": f"{run.as_posix()}/study2, study1; {cfg['output']['revision_h1_dir']}; "
                      f"{Path(cfg['data']['processed_dir']).as_posix()}/{cfg['edge_budgets']['views_file']}",
           "study2_n_bootstrap": nb}

    def mat(cohort, K, cond, fs, obj):
        d = vp[(vp.cohort == cohort) & (vp.K == K) & (vp.condition == cond) & (vp.featureset == fs) & (vp.objective == obj)]
        w = d.pivot(index="seed_index", columns="event_id", values="prob_campaign").sort_index(axis=1)
        y = d.drop_duplicates("event_id").set_index("event_id").loc[w.columns, "label"].values.astype(int)
        return w.values, y, list(w.columns)

    # 1 + 2. Cohorts and RQ2 baselines (same events by construction; verified here)
    rq2 = {}
    for cohort in ("budget_specific", "common"):
        for K in BUDGETS:
            ids = {c: mat(cohort, K, c, "combined", "ba")[2] for c in ("FF", "FK", "KK")}
            assert ids["FF"] == ids["FK"] == ids["KK"], f"conditions score different events: {cohort} K={K}"
            y = mat(cohort, K, "FF", "combined", "ba")[1]
            row = {"n_events": len(y), "n_campaign": int(y.sum()), "n_comparison": int(len(y) - y.sum())}
            for fs in ("combined", "NK"):
                ff_ba, _, _ = mat(cohort, K, "FF", fs, "ba")
                kk_ba, _, _ = mat(cohort, K, "KK", fs, "ba")
                ff_ll, _, _ = mat(cohort, K, "FF", fs, "ll")
                kk_ll, _, _ = mat(cohort, K, "KK", fs, "ll")
                row[f"KK_minus_FF_{fs}"] = {
                    "ba": ci(paired(kk_ba, ff_ba, y, "single", "single", nb, bs, "ba")),
                    "log_loss": ci(paired(kk_ll, ff_ll, y, "single", "single", nb, bs, "ll"))}
            rq2[f"{cohort}_K{K}"] = row
    out["rq2_baselines"] = rq2

    # 3. N_K vs structure within view-trained models (budget-specific cohorts)
    nk = {}
    for K in BUDGETS:
        a, y, _ = mat("budget_specific", K, "KK", "NK", "ba")
        s, _, _ = mat("budget_specific", K, "KK", "struct6", "ba")
        b, _, _ = mat("budget_specific", K, "KK", "NK_struct6", "ba")
        nk[f"K{K}"] = {"NK_minus_structure": ci(paired(a, s, y, "single", "single", nb, bs, "ba")),
                       "NK_added_to_structure": ci(paired(b, s, y, "single", "single", nb, bs, "ba"))}
    out["nk_vs_structure"] = nk

    # 4. How much of log N_K the structural features encode (event-grouped CV)
    views = pd.read_parquet(Path(cfg["data"]["processed_dir"]) / cfg["edge_budgets"]["views_file"])
    r2 = {}
    for K in BUDGETS:
        d = views[views.K == K].dropna(subset=STRUCT6 + ["log_node_count"])
        pred = cross_val_predict(LinearRegression(), d[STRUCT6].values, d["log_node_count"].values,
                                 cv=GroupKFold(5), groups=d["event_id"].values)
        r2[f"K{K}"] = {"r2_event_grouped_cv": float(r2_score(d["log_node_count"].values, pred)),
                       "n_views": int(len(d)), "n_events": int(d.event_id.nunique())}
    out["structure_predicts_log_NK"] = r2

    # 5. Degree-preserving null: how often each arrangement feature changes
    nf = pd.read_parquet(run / "study1" / "null_features.parquet")
    ob = pd.read_parquet(run / "study1" / "full_graph_features.parquet")
    ob = ob.reset_index() if "event_id" not in ob.columns else ob
    ob = ob.set_index("event_id")
    change = {}
    for c in ARRANGE:
        j = nf.join(ob[[c]], on="event_id", rsuffix="_obs")
        diff = (j[c] != j[c + "_obs"]).groupby(j.event_id)
        change[c] = {"share_events_changed_in_some_realization": float(diff.any().mean()),
                     "share_events_unchanged_in_all_realizations": float(1 - diff.any().mean())}
    out["null_feature_change"] = change

    # 6. Repeated-split sign counts (primary contrasts, original grid)
    rep = pd.read_csv(run / "study1" / "repeated_splits_lr.csv")
    out["repeated_splits_signs"] = {
        "n_splits": int(len(rep)),
        "C1": {"n_dBA_positive": int((rep.dBA_C1 > 0).sum()), "n_dLL_negative": int((rep.dLL_C1 < 0).sum()),
               "dBA_mean": float(rep.dBA_C1.mean()), "dLL_median": float(rep.dLL_C1.median())},
        "C2": {"n_dBA_positive": int((rep.dBA_C2 > 0).sum()), "n_dBA_negative": int((rep.dBA_C2 < 0).sum())},
        "C3": {"n_dBA_positive": int((rep.dBA_C3 > 0).sum()), "n_dBA_negative": int((rep.dBA_C3 < 0).sum())},
        "E2_M4_minus_M3_n_dLL_negative": int(((rep.ll_M4 - rep.ll_M3) < 0).sum()),
        "E3_M4_minus_M2_n_dLL_negative": int(((rep.ll_M4 - rep.ll_M2) < 0).sum())}

    # 7. H1 summary
    h1 = json.loads((Path(cfg["output"]["revision_h1_dir"]) / "results.json").read_text(encoding="utf-8"))
    out["h1"] = {"grid": h1["grid"], "original_grid": h1["original_grid"],
                 "tuned_C_ll_M0q": h1["tuned_C"]["ll"]["M0q"], "tuned_C_ll_M4": h1["tuned_C"]["ll"]["M4"],
                 "M0q": h1["performance"]["M0q"], "M4": h1["performance"]["M4"], "C1": h1["primary"]["C1"],
                 "repeated_splits_C1": h1["repeated_splits"]["C1"],
                 "levels_with_optimum_at_upper_bound": h1["levels_with_optimum_at_upper_bound"]}

    # 8. Repeated campaign hashtags (same hashtag, different dates) and fold placement
    man = pd.read_parquet(Path(cfg["data"]["manifests_dir"]) / "manifest.parquet")
    fm = make_event_folds(man, cfg["splits"]["n_folds"], cfg["splits"]["random_seed"])
    tag = man.event_id.map(lambda e: re.sub(r"_(non)?campaign_fulldata$", "", e).split("___")[0].lower().replace("ı", "i"))
    groups = [g.event_id.tolist() for _, g in man.assign(tag=tag).groupby("tag") if len(g) > 1]
    out["repeated_hashtags"] = [{"events": g, "folds": [int(fm[e]) for e in g]} for g in groups]
    out["n_repeated_hashtag_pairs"] = len(groups)
    out["n_repeated_hashtag_pairs_split_across_folds"] = sum(len({fm[e] for e in g}) > 1 for g in groups)

    path = Path(cfg["output"]["revision_supplement"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Supplement -> {path}")
    for k, v in rq2.items():
        print(f"  {k}: n={v['n_events']} ({v['n_campaign']}/{v['n_comparison']}) | KK-FF all: {v['KK_minus_FF_combined']['ba']['delta']:+.3f} "
              f"{np.round(v['KK_minus_FF_combined']['ba']['ci'], 3)} | KK-FF N_K: {v['KK_minus_FF_NK']['ba']['delta']:+.3f} "
              f"{np.round(v['KK_minus_FF_NK']['ba']['ci'], 3)} | LL all {v['KK_minus_FF_combined']['log_loss']['delta']:+.3f} "
              f"{np.round(v['KK_minus_FF_combined']['log_loss']['ci'], 3)}")
    print("  R2:", {k: round(v["r2_event_grouped_cv"], 3) for k, v in r2.items()})
    print("  null change:", {k: round(v["share_events_changed_in_some_realization"], 2) for k, v in change.items()})
    print("  splits:", json.dumps(out["repeated_splits_signs"]))
    print("  hashtags:", out["repeated_hashtags"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    main(ap.parse_args().config)
