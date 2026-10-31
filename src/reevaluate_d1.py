"""
reevaluate_d1.py
----------------
Corrected D1 (frozen full-graph model) evaluation.

The original D1 loop in train.py applied fold model i (trained with the
full-cohort fold map) to the events that the *budget-specific* fold map placed
in fold i. The two maps differ, so some sampled views were scored by a model
that had been trained on the same event's full graph.

This script:
  1. Refits the five A_structure_logreg fold models exactly as train.py does
     and checks that they reproduce the stored out-of-fold predictions.
  2. Reproduces the original (misaligned) D1 numbers as a sanity check.
  3. Scores every sampled view only with the fold model that held its event
     out under the full-cohort fold map (the corrected protocol).
  4. Computes metrics and 95% percentile-bootstrap CIs with the same settings
     as evaluate.py (1,000 resamples, seed from config).

Outputs (outputs/run_final/):
  d1_corrected_metrics.json, d1_corrected_predictions.parquet
  With --apply, the corrected D1 results also replace the D1 entries in
  metrics.json and predictions.parquet (train.py has since been fixed, so a
  full pipeline re-run produces the same fold-aligned values).
"""

import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import balanced_accuracy_score, f1_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from splits import make_event_folds
from features import compute_all_features
from train import run_cv, compute_metrics

sys.stdout.reconfigure(encoding="utf-8")


def bootstrap(pred_df: pd.DataFrame, n_boot: int, seed: int) -> dict:
    y_true = pred_df["label"].values.astype(int)
    y_pred = pred_df["pred_label"].values.astype(int)
    rng = np.random.default_rng(seed)
    b_ba, b_f1 = [], []
    for _ in range(n_boot):
        idx = rng.choice(len(y_true), size=len(y_true), replace=True)
        b_ba.append(balanced_accuracy_score(y_true[idx], y_pred[idx]))
        b_f1.append(f1_score(y_true[idx], y_pred[idx], average="macro", zero_division=0))
    ba_lo, ba_hi = np.percentile(b_ba, [2.5, 97.5])
    f1_lo, f1_hi = np.percentile(b_f1, [2.5, 97.5])
    return {"ba_ci_lower": round(float(ba_lo), 4), "ba_ci_upper": round(float(ba_hi), 4),
            "f1_ci_lower": round(float(f1_lo), 4), "f1_ci_upper": round(float(f1_hi), 4)}


def score_views(k_views, models, test_fold_of) -> pd.DataFrame:
    """Average frozen-model probabilities over seeds; test_fold_of maps event -> fold."""
    rows = []
    for seed_val in sorted(k_views["seed"].unique()):
        seed_views = k_views[k_views["seed"] == seed_val].set_index("event_id")
        for fold_idx, pipe, feat_cols in models:
            ev = seed_views.loc[[e for e in seed_views.index if test_fold_of.get(e) == fold_idx]]
            if ev.empty:
                continue
            probs = pipe.predict_proba(ev[feat_cols].values)[:, 1]
            for eid, prob, lbl in zip(ev.index, probs, ev["label"].values.astype(int)):
                rows.append({"event_id": eid, "seed": seed_val, "label": int(lbl), "prob_campaign": float(prob)})
    df = pd.DataFrame(rows)
    return (df.groupby("event_id")
              .agg(prob_campaign=("prob_campaign", "mean"), label=("label", "first"))
              .assign(pred_label=lambda d: (d.prob_campaign >= 0.5).astype(int))
              .reset_index())


def main(config_path: str, apply: bool = False) -> None:
    config = yaml.safe_load(open(config_path, encoding="utf-8"))
    manifests_dir = Path(config["data"]["manifests_dir"])
    processed_dir = Path(config["data"]["processed_dir"])
    run_dir = Path(config["output"]["run_dir"])
    sc = config["splits"]
    n_boot = config["evaluation"]["bootstrap_n_resamples"]
    boot_seed = config["evaluation"]["bootstrap_seed"]

    manifest = pd.read_parquet(manifests_dir / "manifest.parquet")
    edges_df = pd.read_parquet(processed_dir / "edges.parquet")
    views_df = pd.read_parquet(processed_dir / config["edge_budgets"].get("views_file", "sampled_views.parquet"))
    stored_metrics = json.load(open(run_dir / "metrics.json", encoding="utf-8"))
    stored_preds = pd.read_parquet(run_dir / "predictions.parquet")

    fold_map = make_event_folds(manifest, sc["n_folds"], sc["random_seed"])

    print("Recomputing full-graph structural features...")
    struct_df = compute_all_features(edges_df, manifest, config)["structure"]

    print("Refitting A_structure_logreg fold models...")
    preds, models = run_cv(struct_df, fold_map, config, "A_structure_logreg", "logreg")
    ref = stored_preds[stored_preds.experiment == "A_structure_logreg"].set_index("event_id")["prob_campaign"]
    max_diff = float((preds.set_index("event_id")["prob_campaign"] - ref.loc[preds.event_id].values).abs().max())
    refit_ba = compute_metrics(preds)["balanced_accuracy"]
    print(f"  refit BA={refit_ba} (stored {stored_metrics['A_structure_logreg']['balanced_accuracy']}), max |dprob|={max_diff:.2e}")
    if max_diff > 1e-6:
        raise RuntimeError("Refitted models do not reproduce stored predictions; aborting.")

    out = {"protocol": "Frozen A_structure_logreg fold models; each sampled event scored only by the model "
                       "whose full-cohort training fold excluded it; probabilities averaged over 10 seeds.",
           "refit_check": {"max_abs_prob_diff": max_diff, "refit_balanced_accuracy": refit_ba},
           "results": {}}
    all_pred = []
    a_struct = preds.set_index("event_id")
    for K in config["edge_budgets"]["K_values"]:
        k_views = views_df[views_df["K"] == K]
        eligible = k_views["event_id"].unique().tolist()
        elig_manifest = manifest[manifest["event_id"].isin(eligible)].reset_index(drop=True)
        k_fold_map = make_event_folds(elig_manifest, sc["n_folds"], sc["random_seed"])

        # Sanity check: the original misaligned assignment reproduces stored D1.
        leaky = compute_metrics(score_views(k_views, models, k_fold_map))["balanced_accuracy"]
        stored = stored_metrics[f"D1_K{K}_frozen"]["balanced_accuracy"]

        corr_df = score_views(k_views, models, fold_map)
        m = compute_metrics(corr_df)
        m.update(bootstrap(corr_df, n_boot, boot_seed))

        # Same frozen models on the same eligible events, but complete graphs.
        full_sub = a_struct.loc[eligible].reset_index()
        m_full = compute_metrics(full_sub)

        n_misaligned = int(sum(k_fold_map[e] != fold_map[e] for e in eligible))
        out["results"][f"D1_K{K}_frozen_corrected"] = {
            **m,
            # Superseded value of the original misaligned protocol, recomputed here
            # from the refitted models (independent of what metrics.json holds).
            "superseded_misaligned_balanced_accuracy": leaky,
            "n_events_previously_misaligned": n_misaligned,
            "full_graph_same_models_same_events_balanced_accuracy": m_full["balanced_accuracy"],
        }
        if apply:
            stored_metrics[f"D1_K{K}_frozen"] = {
                **m,
                "fold_aligned": True,
                "full_graph_reference_balanced_accuracy": m_full["balanced_accuracy"],
            }
        print(f"  K={K:4d} N={m['n_events']:3d} corrected BA={m['balanced_accuracy']:.4f} "
              f"[{m['ba_ci_lower']}, {m['ba_ci_upper']}] | stored(misaligned)={stored} reproduced={leaky} "
              f"| full-graph same events={m_full['balanced_accuracy']} | misaligned events={n_misaligned}")
        all_pred.append(corr_df.assign(experiment=f"D1_K{K}_frozen_corrected", model="logreg"))

    (run_dir / "d1_corrected_metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    corrected = pd.concat(all_pred, ignore_index=True)
    corrected.to_parquet(run_dir / "d1_corrected_predictions.parquet", index=False)
    print(f"Saved -> {run_dir / 'd1_corrected_metrics.json'}")

    if apply:
        # Promote the fold-aligned D1 results into the authoritative run outputs,
        # under the experiment names that train.py writes.
        with open(run_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(stored_metrics, f, indent=2, ensure_ascii=False)
        kept = stored_preds[~stored_preds["experiment"].str.startswith("D1_")]
        d1_rows = corrected.assign(
            experiment=corrected["experiment"].str.replace("_frozen_corrected", "_frozen_structure", regex=False)
        )
        pd.concat([kept, d1_rows], ignore_index=True).to_parquet(run_dir / "predictions.parquet", index=False)
        print("Applied corrected D1 to metrics.json and predictions.parquet")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/final.yaml")
    ap.add_argument("--apply", action="store_true",
                    help="write the fold-aligned D1 results into metrics.json and predictions.parquet")
    args = ap.parse_args()
    main(args.config, args.apply)
