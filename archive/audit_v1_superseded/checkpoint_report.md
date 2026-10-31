# Checkpoint Report - LEN-Small Robustness Audit

## Executive Summary
- **Dataset:** LEN-Small archive (`small_encoder_final.tar`).
- **Events Analysed:** 103 unique event graphs (52 campaign, 51 comparison).
- **Unit of Analysis:** Entire user-to-user engagement event graph. All predictions and evaluations are strictly event-level.

## 1. Scale Confounding & Baselines (RQ1)

### Empirical Scale Distributions
- **Campaign Graphs:** Median node count = 506.0, mean = 662.2.
- **Comparison Graphs:** Median node count = 3227.0, mean = 3479.2.
- **Key Finding:** Contrary to initial teammate assumptions, **comparison graphs are substantially larger (approx. 5x) than campaign graphs**. Size is an extraordinarily strong confounder.

### Scale Baseline Performance (Out-of-Fold 5-Fold CV)
| Model / Feature Group | Balanced Accuracy | Macro F1 | Campaign Recall | Comparison Recall | ROC-AUC |
|---|---|---|---|---|---|
| B0a: Log Node Count (LogReg) | 0.8739 | 0.8738 | 0.8654 | 0.8824 | 0.934 |
| B0b: Log Node + Log Edge (LogReg) | 0.8837 | 0.8835 | 0.8654 | 0.902 | 0.9306 |
| Scale Baseline (LogReg) | 0.8837 | 0.8835 | 0.8654 | 0.902 | 0.9306 |
| Structure Group (LogReg) | 0.7785 | 0.7697 | 0.5962 | 0.9608 | 0.8458 |
| Content Group (LogReg) | 0.7866 | 0.7864 | 0.7692 | 0.8039 | 0.859 |
| Combined Group (LogReg) | 0.9229 | 0.9221 | 0.8654 | 0.9804 | 0.9857 |

## 2. Size-Matched Cohort Evaluation (RQ1 Controlled)

- **Matching Caliper:** 0.2859 (0.25 SD of log node count).
- **Retained Pairs:** 16 pairs (16 campaign, 16 comparison; 71 excluded).
- **Balance Diagnostics (SMD):** Standardised Mean Difference dropped from **-2.2374** before matching to **-0.0954** after matching.

| Feature Group (LogReg) | Full Cohort BA | Matched Cohort BA | Impact of Size Matching |
|---|---|---|---|
| Scale | 0.8837 | 0.5938 | -0.2899 |
| Structure | 0.7785 | 0.6875 | -0.091 |
| Content | 0.7866 | 0.75 | -0.0366 |
| Combined | 0.9229 | 0.75 | -0.1729 |

## 3. Edge-Budget Robustness (RQ2)

| Edge Budget (K) | Eligible Events (Camp / Comp) | D2 Retrained BA | D1 Frozen Structure BA | Feasibility Note |
|---|---|---|---|---|
| K=250 | 51 / 51 | 0.9412 | 0.598 | Feasible (5-fold CV) |
| K=500 | 48 / 50 | 0.9379 | 0.7246 | Feasible (5-fold CV) |
| K=1000 | 28 / 45 | 0.9063 | 0.7456 | Feasible (5-fold CV) |
| K=2000 | 4 / 32 | N/A | N/A | Infeasible: only 4 campaigns (CV folds empty) |

## 4. Methodological Audit & Defects Resolved
1. **Archive Ingestion:** Resolved lack of CSV/metadata files by streaming JSON node-link graphs directly from `small_encoder_final.tar`.
2. **Deduplication:** Identified and eliminated byte-identical duplicate `#SesimiziDuyanVarM[i/ı]`.
3. **Metric Calculation Correction:** Corrected code in guide that called `f1_score` to compute `campaign_recall` and `comparison_recall` to use true `recall_score`.
4. **Class Inbalance at K=2000:** Discovered that only 4 campaign events meet the K=2000 threshold, precluding 5-fold CV without data leakage.
5. **Memory Management:** Dropped 770+ dimensional float vectors (`node_attr`, `edge_attr`) during ingestion, keeping memory usage minimal.