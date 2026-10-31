"""
train.py
--------
Training and cross-validation orchestrator for LEN-Small robustness audit.

Experiments:
  [A] Full-cohort reference (scale, structure, content, combined) x (logreg, hgbt)
  [B] Scale-only baselines (B0a: log_node, B0b: log_node + log_edge) x (logreg, hgbt)
  [C] Size-matched cohort (scale, structure, content, combined) x (logreg, hgbt)
  [D2] Edge-budget retraining at fixed K (K=250, 500, 1000) averaged across 10 seeds
  [D1] True frozen-model evaluation (full-graph trained model applied to restricted views)

Outputs:
  outputs/run_final/predictions.parquet
  outputs/run_final/metrics.json
  outputs/run_final/tables.md
"""

import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score,
    recall_score,
    roc_auc_score,
)

from splits import make_event_folds, assign_view_folds
from features import compute_all_features

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_logreg_pipeline(config: dict, C: float = 1.0) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            C=C,
            max_iter=config["models"]["logreg"]["max_iter"],
            solver=config["models"]["logreg"]["solver"],
            class_weight="balanced",
            random_state=config["splits"]["random_seed"],
        ))
    ])


def make_hgbt_pipeline(config: dict) -> Pipeline:
    # HGBT handles NaN natively
    return Pipeline([
        ("clf", HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=config["models"]["hgbt"]["max_depth"],
            random_state=config["models"]["hgbt"]["random_state"],
            class_weight="balanced",
        ))
    ])


def tune_logreg_C(
    X_train: np.ndarray,
    y_train: np.ndarray,
    C_values: list[float],
    inner_cv: int,
    config: dict,
    scoring: str = "balanced_accuracy",
) -> float:
    """Select C by inner stratified CV on the training fold only.

    scoring is the inner-CV objective: "balanced_accuracy" for BA estimands,
    "neg_log_loss" for log-loss estimands (higher is better for both).
    """
    best_C, best_score = C_values[0], -np.inf
    # Ensure inner CV has at least 2 samples per class
    min_class = np.min(np.bincount(y_train))
    cv_splits = max(2, min(inner_cv, min_class))
    
    for C in C_values:
        pipe = make_logreg_pipeline(config, C=C)
        scores = cross_val_score(
            pipe, X_train, y_train,
            cv=StratifiedKFold(cv_splits, shuffle=True, random_state=0),
            scoring=scoring
        )
        if scores.mean() > best_score:
            best_score = scores.mean()
            best_C = C
    return best_C


def run_cv(
    feature_df: pd.DataFrame,
    fold_map: dict[str, int],
    config: dict,
    experiment_label: str,
    model_type: str = "logreg",
    scoring: str = "balanced_accuracy",
) -> tuple[pd.DataFrame, list]:
    n_folds = config["splits"]["n_folds"]
    C_values = config["models"]["logreg"]["C_values"]

    df = feature_df.copy()
    df["fold_id"] = df.index.map(fold_map)
    df = df.dropna(subset=["fold_id"])
    df["fold_id"] = df["fold_id"].astype(int)

    feature_cols = [c for c in df.columns if c not in {"label", "fold_id"}]

    all_preds = []
    fitted_models = []

    for fold_idx in range(n_folds):
        train_mask = df["fold_id"] != fold_idx
        test_mask = df["fold_id"] == fold_idx

        X_train = df.loc[train_mask, feature_cols].values
        y_train = df.loc[train_mask, "label"].values.astype(int)
        X_test = df.loc[test_mask, feature_cols].values
        y_test = df.loc[test_mask, "label"].values.astype(int)

        if len(X_test) == 0:
            continue

        best_C = None
        if model_type == "logreg":
            best_C = tune_logreg_C(X_train, y_train, C_values, inner_cv=3, config=config, scoring=scoring)
            pipe = make_logreg_pipeline(config, C=best_C)
        else:
            pipe = make_hgbt_pipeline(config)

        pipe.fit(X_train, y_train)
        fitted_models.append((fold_idx, pipe, feature_cols))

        probs = pipe.predict_proba(X_test)[:, 1]
        preds = (probs >= 0.5).astype(int)

        test_eids = df.loc[test_mask].index.tolist()
        for eid, prob, pred, true_lbl in zip(test_eids, probs, preds, y_test):
            all_preds.append({
                "event_id": eid,
                "fold_id": fold_idx,
                "label": int(true_lbl),
                "prob_campaign": float(prob),
                "pred_label": int(pred),
                "experiment": experiment_label,
                "model": model_type,
                "tuned_C": best_C,
            })

    return pd.DataFrame(all_preds), fitted_models


def frozen_model_test_events(full_fold_map: dict, eligible_eids: list, fold_idx: int) -> list:
    """
    Events a frozen full-cohort fold model may score: those whose full-cohort
    fold is fold_idx, i.e. events excluded from that model's training data.
    Budget-specific fold maps must not be used here (they differ from the
    full-cohort assignment and caused the earlier D1 leakage).
    """
    return [eid for eid in eligible_eids if full_fold_map[eid] == fold_idx]


def compute_metrics(pred_df: pd.DataFrame) -> dict:
    y_true = pred_df["label"].values
    y_pred = pred_df["pred_label"].values
    y_prob = pred_df["prob_campaign"].values

    metrics = {
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        # FIXED: recall_score used for recall instead of erroneous f1_score from the guide
        "campaign_recall": round(float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)), 4),
        "comparison_recall": round(float(recall_score(y_true, y_pred, pos_label=0, zero_division=0)), 4),
        "n_events": int(len(pred_df)),
    }
    try:
        metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 4)
    except Exception:
        metrics["roc_auc"] = None

    return metrics


def train_all(config: dict) -> None:
    manifests_dir = Path(config["data"]["manifests_dir"])
    processed_dir = Path(config["data"]["processed_dir"])
    run_dir = Path(config["output"]["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_parquet(manifests_dir / "manifest.parquet")
    edges_df = pd.read_parquet(processed_dir / "edges.parquet")

    split_cfg = config["splits"]
    fold_map = make_event_folds(manifest, split_cfg["n_folds"], split_cfg["random_seed"])

    all_predictions = []
    all_metrics = {}

    print("Computing full feature groups for all events...")
    feature_groups = compute_all_features(edges_df, manifest, config)

    # Cache fitted models from full cohort for frozen-model evaluation (D1)
    full_fitted_models = {}

    # =========================================================================
    # Experiment A: Full cohort reference
    # =========================================================================
    print("\n[A] Full-cohort reference experiments...")
    for group_name, feat_df in feature_groups.items():
        for model_type in ["logreg", "hgbt"]:
            exp_label = f"A_{group_name}_{model_type}"
            pred_df, models = run_cv(feat_df, fold_map, config, exp_label, model_type)
            all_predictions.append(pred_df)
            m = compute_metrics(pred_df)
            all_metrics[exp_label] = m
            if group_name in {"combined", "structure"} and model_type == "logreg":
                full_fitted_models[group_name] = models
            print(f"  {exp_label:32s} | BA={m['balanced_accuracy']:.4f} | F1={m['macro_f1']:.4f} | AUC={m['roc_auc']}")

    # =========================================================================
    # Experiment B: Scale-only baselines
    # =========================================================================
    print("\n[B] Scale-only baselines...")
    scale_df = feature_groups["scale"].copy()

    # B0a: log node count only
    b0a_df = scale_df[["label", "log_node_count"]].copy()
    for model_type in ["logreg", "hgbt"]:
        exp_label = f"B0a_log_node_{model_type}"
        pred_df, _ = run_cv(b0a_df, fold_map, config, exp_label, model_type)
        all_predictions.append(pred_df)
        m = compute_metrics(pred_df)
        all_metrics[exp_label] = m
        print(f"  {exp_label:32s} | BA={m['balanced_accuracy']:.4f} | F1={m['macro_f1']:.4f} | AUC={m['roc_auc']}")

    # B0b: log node count + log edge count
    b0b_df = scale_df[["label", "log_node_count", "log_edge_count"]].copy()
    for model_type in ["logreg", "hgbt"]:
        exp_label = f"B0b_log_node_edge_{model_type}"
        pred_df, _ = run_cv(b0b_df, fold_map, config, exp_label, model_type)
        all_predictions.append(pred_df)
        m = compute_metrics(pred_df)
        all_metrics[exp_label] = m
        print(f"  {exp_label:32s} | BA={m['balanced_accuracy']:.4f} | F1={m['macro_f1']:.4f} | AUC={m['roc_auc']}")

    # =========================================================================
    # Experiment C: Size-matched cohort
    # =========================================================================
    matched_manifest_path = manifests_dir / "matched_manifest.parquet"
    if matched_manifest_path.exists():
        print("\n[C] Size-matched cohort experiments...")
        matched_manifest = pd.read_parquet(matched_manifest_path)
        matched_eids = matched_manifest["event_id"].tolist()
        matched_fold_map = make_event_folds(
            matched_manifest.reset_index(drop=True), split_cfg["n_folds"], split_cfg["random_seed"]
        )

        for group_name, feat_df in feature_groups.items():
            matched_feat_df = feat_df.loc[feat_df.index.isin(matched_eids)]
            for model_type in ["logreg", "hgbt"]:
                exp_label = f"C_matched_{group_name}_{model_type}"
                pred_df, _ = run_cv(matched_feat_df, matched_fold_map, config, exp_label, model_type)
                all_predictions.append(pred_df)
                m = compute_metrics(pred_df)
                all_metrics[exp_label] = m
                print(f"  {exp_label:32s} | BA={m['balanced_accuracy']:.4f} | F1={m['macro_f1']:.4f} | Retained={m['n_events']}")
    else:
        print("\n[C] Matched cohort skipped - run build_cohorts.py first.")

    # =========================================================================
    # Experiments D1 & D2: Edge budgets
    # =========================================================================
    views_path = processed_dir / config["edge_budgets"].get("views_file", "sampled_views.parquet")
    if views_path.exists():
        print("\n[D] Edge-budget experiments...")
        views_df = pd.read_parquet(views_path)

        for K in config["edge_budgets"]["K_values"]:
            k_views = views_df[views_df["K"] == K]
            eligible_eids = k_views["event_id"].unique().tolist()
            eligible_manifest = manifest[manifest["event_id"].isin(eligible_eids)].reset_index(drop=True)

            if len(eligible_eids) < split_cfg["n_folds"] * 2:
                print(f"  K={K}: insufficient eligible events ({len(eligible_eids)}) - skipping.")
                continue

            k_fold_map = make_event_folds(eligible_manifest, split_cfg["n_folds"], split_cfg["random_seed"])

            # -----------------------------------------------------------------
            # D2: Restricted-view retraining (train and test on sampled views)
            # -----------------------------------------------------------------
            seed_preds_d2 = []
            for seed_val in sorted(k_views["seed"].unique()):
                seed_views = k_views[k_views["seed"] == seed_val]
                feat_df_seed = seed_views.drop(columns=["K", "seed"]).set_index("event_id")
                pred_df, _ = run_cv(feat_df_seed, k_fold_map, config, f"D2_K{K}_seed{seed_val}", "logreg")
                seed_preds_d2.append(pred_df)

            if seed_preds_d2:
                combined_d2 = pd.concat(seed_preds_d2)
                avg_pred_d2 = (
                    combined_d2.groupby("event_id")
                    .agg(prob_campaign=("prob_campaign", "mean"), label=("label", "first"))
                    .assign(
                        pred_label=lambda d: (d.prob_campaign >= 0.5).astype(int),
                        experiment=f"D2_K{K}_retrained",
                        model="logreg"
                    )
                    .reset_index()
                )
                all_predictions.append(avg_pred_d2)
                m_d2 = compute_metrics(avg_pred_d2)
                all_metrics[f"D2_K{K}"] = m_d2
                print(f"  D2 (Retrained) K={K:4d} | N={len(eligible_eids):2d} | BA={m_d2['balanced_accuracy']:.4f} | F1={m_d2['macro_f1']:.4f}")

            # -----------------------------------------------------------------
            # D1: True frozen model (trained on full graphs from Exp A, tested on sampled views)
            # -----------------------------------------------------------------
            if "structure" in full_fitted_models:
                struct_models = full_fitted_models["structure"]  # list of (fold_idx, pipe, feature_cols)
                d1_preds_seeds = []
                for seed_val in sorted(k_views["seed"].unique()):
                    seed_views = k_views[k_views["seed"] == seed_val].set_index("event_id")
                    for fold_idx, pipe, feat_cols in struct_models:
                        test_eids_in_fold = frozen_model_test_events(fold_map, eligible_eids, fold_idx)
                        test_views_fold = seed_views.loc[seed_views.index.isin(test_eids_in_fold)]
                        if test_views_fold.empty:
                            continue
                        X_test = test_views_fold[feat_cols].values
                        y_test = test_views_fold["label"].values.astype(int)
                        probs = pipe.predict_proba(X_test)[:, 1]
                        for eid, prob, lbl in zip(test_views_fold.index, probs, y_test):
                            d1_preds_seeds.append({
                                "event_id": eid,
                                "seed": seed_val,
                                "label": int(lbl),
                                "prob_campaign": float(prob),
                            })
                if d1_preds_seeds:
                    d1_df = pd.DataFrame(d1_preds_seeds)
                    avg_pred_d1 = (
                        d1_df.groupby("event_id")
                        .agg(prob_campaign=("prob_campaign", "mean"), label=("label", "first"))
                        .assign(
                            pred_label=lambda d: (d.prob_campaign >= 0.5).astype(int),
                            experiment=f"D1_K{K}_frozen_structure",
                            model="logreg"
                        )
                        .reset_index()
                    )
                    all_predictions.append(avg_pred_d1)
                    m_d1 = compute_metrics(avg_pred_d1)
                    all_metrics[f"D1_K{K}_frozen"] = m_d1
                    print(f"  D1 (Frozen)    K={K:4d} | N={len(eligible_eids):2d} | BA={m_d1['balanced_accuracy']:.4f} | F1={m_d1['macro_f1']:.4f}")

    # =========================================================================
    # Save outputs
    # =========================================================================
    all_preds_df = pd.concat(all_predictions, ignore_index=True)
    pred_path = run_dir / "predictions.parquet"
    all_preds_df.to_parquet(pred_path, index=False)
    print(f"\nPredictions saved: {len(all_preds_df)} rows -> {pred_path}")

    metrics_path = run_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False)
    print(f"Metrics saved     -> {metrics_path}")

    def df_to_markdown(df: pd.DataFrame) -> str:
        headers = [str(c) for c in df.columns]
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for _, row in df.iterrows():
            row_vals = [str(row[c]) if pd.notna(row[c]) else "" for c in df.columns]
            lines.append("| " + " | ".join(row_vals) + " |")
        return "\n".join(lines)

    summary_rows = []
    for exp, m in all_metrics.items():
        summary_rows.append({"experiment": exp, **m})
    summary_df = pd.DataFrame(summary_rows).sort_values("experiment")
    tables_path = run_dir / "tables.md"
    with open(tables_path, "w", encoding="utf-8") as f:
        f.write("# LEN-Small Robustness Audit - Results Summary\n\n")
        f.write(df_to_markdown(summary_df))
        f.write("\n\n*All numbers are out-of-fold estimates evaluated via stratified 5-fold cross-validation.*\n")
    print(f"Summary table     -> {tables_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and evaluate all models")
    parser.add_argument("--config", default="configs/final.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    train_all(cfg)
