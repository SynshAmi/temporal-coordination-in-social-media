"""
a04_study2_diagnostics.py — Study 2: is the frozen-transfer (FK) penalty a ranking loss or a
threshold shift? And how do FF, FK and KK differ in calibration, ranking and decisions?

Reads the stored single-view predictions (outputs/run_v2/study2/view_predictions.parquet) and,
per budget-specific cohort, condition and feature set, averages over the ten sampling seeds:
BA at the 0.5 threshold (BA-tuned fits), AUC and log loss (log-loss-tuned fits), recall per class,
share predicted campaign, mean predicted probability per class, and the BA at the best threshold
for each seed (an optimistic, in-sample upper bound used only to separate ranking from threshold).

Output: research_audit/outputs/a04_study2_diagnostics.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, log_loss, roc_auc_score, roc_curve

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
v = pd.read_parquet(ROOT / "outputs/run_v2/study2/view_predictions.parquet")
v = v[v.cohort == "budget_specific"]


def best_threshold_ba(y, p):
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max((tpr + 1 - fpr) / 2))


rows = []
for (K, cond, fs), g in v.groupby(["K", "condition", "featureset"]):
    rec = {"K": K, "condition": cond, "featureset": fs}
    stats = {k: [] for k in ("ba", "auc", "ll", "recall_campaign", "recall_comparison", "share_pred_campaign",
                             "mean_p_campaign", "mean_p_comparison", "best_threshold_ba")}
    for s, gs in g.groupby("seed_index"):
        b = gs[gs.objective == "ba"].sort_values("event_id")
        l = gs[gs.objective == "ll"].sort_values("event_id")
        y, pb, pl = b.label.values.astype(int), b.prob_campaign.values, l.prob_campaign.values
        stats["ba"].append(balanced_accuracy_score(y, pb >= .5))
        stats["recall_campaign"].append(((pb >= .5) & (y == 1)).sum() / (y == 1).sum())
        stats["recall_comparison"].append(((pb < .5) & (y == 0)).sum() / (y == 0).sum())
        stats["share_pred_campaign"].append((pb >= .5).mean())
        stats["auc"].append(roc_auc_score(y, pl))
        stats["ll"].append(log_loss(y, np.clip(pl, 1e-6, 1 - 1e-6)))
        stats["mean_p_campaign"].append(pl[y == 1].mean())
        stats["mean_p_comparison"].append(pl[y == 0].mean())
        stats["best_threshold_ba"].append(best_threshold_ba(y, pb))
    rec.update({k: float(np.mean(x)) for k, x in stats.items()})
    rec["n_events"] = int(g.event_id.nunique())
    rows.append(rec)
d = pd.DataFrame(rows)
d.to_csv(ROOT / "research_audit/outputs/a04_study2_diagnostics.csv", index=False)
show = d[d.featureset.isin(["struct6", "combined", "NK"])].sort_values(["featureset", "K", "condition"])
print(show.round(3).to_string(index=False))
