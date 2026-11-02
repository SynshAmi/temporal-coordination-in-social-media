"""
h1_c_grid.py
------------
Revision experiment H1: is the logistic-regression count baseline under-tuned?

In the corrected Study 1 run, the count models (M0, M0q) selected C = 10, the
largest value of the grid {0.01, 0.1, 1, 10}, in every log-loss fold. This
script repeats the Study 1 logistic-regression analysis with a wider grid,
using exactly the same folds, features, preprocessing, inner-CV tuning,
objectives and paired bootstrap (functions imported from study1_incremental).

Protocol check: the original grid is re-run first and must reproduce the stored
out-of-fold predictions in outputs/run_v2/study1/oof_predictions.parquet.

Outputs go to output.revision_h1_dir in the config (default config:
outputs/revision_h1_cgrid/); the run_v2 results are only read:
  results.json            performance, primary contrasts, exploratory E2/E3, tuned C
  oof_predictions.parquet main-split predictions with the wide grid
  repeated_splits_lr.csv  the 10 re-drawn splits with the wide grid

Usage: python src/h1_c_grid.py [--config configs/v2_coreness_fix.yaml]
"""

import sys
import copy
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from study1_incremental import (LEVELS, CONFIRMATORY, EXPLORATORY, SCORING, add_quadratic,  # noqa: E402
                                run_level, metrics, contrasts, holm)
from splits import make_event_folds  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

WIDE_GRID = [0.001, 0.01, 0.1, 1, 10, 100, 1000]
EXTENDED_GRID = WIDE_GRID + [1e4, 1e5]   # used only if an optimum sits at 1000


def fit_all(feat, fold_map, cfg):
    return {obj: {lv: run_level(feat, fold_map, cfg, lv, "logreg", obj) for lv in LEVELS} for obj in SCORING}


def tuned_c(preds):
    return {obj: {lv: [float(c) for c in p.groupby("fold_id")["tuned_C"].first().tolist()] for lv, p in d.items()}
            for obj, d in preds.items()}


def summarise(preds, nb, bs):
    perf = {lv: {"balanced_accuracy": metrics(preds["ba"][lv].label.values, preds["ba"][lv].prob_campaign.values)["balanced_accuracy"],
                 "log_loss": metrics(preds["ll"][lv].label.values, preds["ll"][lv].prob_campaign.values)["log_loss"],
                 "roc_auc_ll_fit": metrics(preds["ll"][lv].label.values, preds["ll"][lv].prob_campaign.values)["roc_auc"]}
            for lv in LEVELS}
    cb, cl = contrasts(preds["ba"], CONFIRMATORY, nb, bs), contrasts(preds["ll"], CONFIRMATORY, nb, bs)
    hb = holm({k: v["p_ba_bootstrap"] for k, v in cb.items()})
    hl = holm({k: v["p_logloss_bootstrap"] for k, v in cl.items()})
    primary = {k: {"a": a, "b": b,
                   "delta_ba": cb[k]["delta_ba"], "delta_ba_ci": cb[k]["delta_ba_ci"], "p_ba_holm": hb[k],
                   "delta_logloss": cl[k]["delta_logloss"], "delta_logloss_ci": cl[k]["delta_logloss_ci"], "p_logloss_holm": hl[k],
                   "delta_auc_ll_fit": cl[k]["delta_auc"], "delta_auc_ll_fit_ci": cl[k]["delta_auc_ci"]}
               for k, (a, b) in CONFIRMATORY.items()}
    sub = {k: EXPLORATORY[k] for k in ("E2", "E3")}
    eb, el = contrasts(preds["ba"], sub, nb, bs), contrasts(preds["ll"], sub, nb, bs)
    exploratory = {k: {"a": a, "b": b, "delta_ba": eb[k]["delta_ba"], "delta_ba_ci": eb[k]["delta_ba_ci"],
                       "delta_logloss": el[k]["delta_logloss"], "delta_logloss_ci": el[k]["delta_logloss_ci"]}
                   for k, (a, b) in sub.items()}
    return perf, primary, exploratory


def main(config_path):
    base = yaml.safe_load(open(config_path, encoding="utf-8"))
    s1 = base["study1"]
    run = Path(base["output"]["run_dir"])
    out = Path(base["output"]["revision_h1_dir"])
    out.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_parquet(Path(base["data"]["manifests_dir"]) / "manifest.parquet")
    feat = add_quadratic(pd.read_parquet(run / "study1" / "full_graph_features.parquet"))
    fold_map = make_event_folds(manifest, base["splits"]["n_folds"], base["splits"]["random_seed"])

    # 1. Protocol check: the original grid must reproduce the stored predictions.
    stored = pd.read_parquet(run / "study1" / "oof_predictions.parquet")
    stored = stored[stored.model == "logreg"]
    for obj in SCORING:
        for lv in ("M0q", "M4"):
            p = run_level(feat, fold_map, base, lv, "logreg", obj)
            s = stored[(stored.objective == obj) & (stored.experiment == lv)].set_index("event_id").sort_index()
            assert np.allclose(p.prob_campaign.values, s.prob_campaign.values, atol=1e-10), f"protocol mismatch {obj} {lv}"
    print("Protocol check passed: original grid reproduces the stored Study 1 predictions.")

    # 2. Wide grid on the main split
    def cfg_with(grid):
        c = copy.deepcopy(base)
        c["models"]["logreg"]["C_values"] = grid
        return c
    grid = WIDE_GRID
    preds = fit_all(feat, fold_map, cfg_with(grid))
    tc = tuned_c(preds)
    at_upper = sorted({f"{obj}:{lv}" for obj, d in tc.items() for lv, cs in d.items() if max(grid) in cs})
    if at_upper:
        print(f"Optimum at C = {max(grid)} for {at_upper}; extending the grid to {EXTENDED_GRID}.")
        grid = EXTENDED_GRID
        preds = fit_all(feat, fold_map, cfg_with(grid))
        tc = tuned_c(preds)
    at_upper = sorted({f"{obj}:{lv}" for obj, d in tc.items() for lv, cs in d.items() if max(grid) in cs})
    at_lower = sorted({f"{obj}:{lv}" for obj, d in tc.items() for lv, cs in d.items() if min(grid) in cs})
    perf, primary, exploratory = summarise(preds, s1["n_bootstrap"], s1["bootstrap_seed"])
    pd.concat([p.reset_index().assign(objective=obj) for obj, d in preds.items() for p in d.values()]).to_parquet(
        out / "oof_predictions.parquet", index=False)

    # 3. Re-drawn splits with the same grid
    rows = []
    for sseed in s1["split_seeds"]:
        fm = make_event_folds(manifest, base["splits"]["n_folds"], sseed)
        pr = fit_all(feat, fm, cfg_with(grid))
        ba = {lv: metrics(p.label.values, p.prob_campaign.values)["balanced_accuracy"] for lv, p in pr["ba"].items()}
        ll = {lv: metrics(p.label.values, p.prob_campaign.values)["log_loss"] for lv, p in pr["ll"].items()}
        au = {lv: metrics(p.label.values, p.prob_campaign.values)["roc_auc"] for lv, p in pr["ll"].items()}
        rows.append({"split_seed": sseed, **{f"ba_{k}": v for k, v in ba.items()}, **{f"ll_{k}": v for k, v in ll.items()},
                     **{f"dBA_{c}": ba[a] - ba[b] for c, (a, b) in CONFIRMATORY.items()},
                     **{f"dLL_{c}": ll[a] - ll[b] for c, (a, b) in CONFIRMATORY.items()},
                     **{f"dAUC_{c}": au[a] - au[b] for c, (a, b) in CONFIRMATORY.items()},
                     "C_ll_M0q": json.dumps(tuned_c(pr)["ll"]["M0q"])})
    rep = pd.DataFrame(rows)
    rep.to_csv(out / "repeated_splits_lr.csv", index=False)

    res = {"grid": grid, "original_grid": base["models"]["logreg"]["C_values"],
           "protocol_check": "original grid reproduces stored run_v2 LR predictions (M0q, M4; both objectives)",
           "tuned_C": tc, "levels_with_optimum_at_upper_bound": at_upper, "levels_with_optimum_at_lower_bound": at_lower,
           "performance": perf, "primary": primary, "exploratory": exploratory,
           "repeated_splits": {c: {f"{m}_{st}": float(getattr(rep[f"{m}_{c}"], st)()) for m in ("dBA", "dLL", "dAUC")
                                   for st in ("mean", "min", "max")} | {"n_dLL_negative": int((rep[f"dLL_{c}"] < 0).sum()),
                                                                        "n_dBA_positive": int((rep[f"dBA_{c}"] > 0).sum())}
                               for c in CONFIRMATORY},
           "n_split_seeds": len(s1["split_seeds"])}
    (out / "results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print("grid:", grid, "| optimum at upper bound:", at_upper or "none", "| at lower bound:", at_lower or "none")
    print("LL-tuned C, M0q:", tc["ll"]["M0q"], "M0:", tc["ll"]["M0"], "M4:", tc["ll"]["M4"])
    for lv in ("M0", "M0q", "M2", "M3", "M4"):
        print(f"  {lv}: BA {perf[lv]['balanced_accuracy']:.3f}  LL {perf[lv]['log_loss']:.3f}  AUC {perf[lv]['roc_auc_ll_fit']:.3f}")
    for k, v in primary.items():
        print(f"  {k}: dBA {v['delta_ba']:+.3f} {np.round(v['delta_ba_ci'], 3)} | dLL {v['delta_logloss']:+.3f} "
              f"{np.round(v['delta_logloss_ci'], 3)} holm {v['p_logloss_holm']:.3f} | dAUC {v['delta_auc_ll_fit']:+.3f}")
    print("repeated splits:", json.dumps(res["repeated_splits"]["C1"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    main(ap.parse_args().config)
