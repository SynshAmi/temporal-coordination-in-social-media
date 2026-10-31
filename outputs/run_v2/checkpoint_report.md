# Checkpoint Report: Base Experiment Grid (diagnostic)

> **Read this first.** This is an automatically generated summary of the pipeline's base experiment grid (stages 5-7). It is a diagnostic, not the paper's analysis. The paper's results come from Study 1 and Study 2 and are collected in `paper_results.json` in the same run directory. In particular, the edge-budget table below compares a frozen model on 7 structural features with a retrained model on all 12 features, so their difference is **not** an estimate of the effect of retraining; Study 2 makes that comparison with matched feature sets. The single-ordering size-matching table is likewise superseded by the paper's 20-ordering exploratory analysis.

## Cohort
- **Dataset:** analysed LEN-Small archive (`small_encoder_final.tar`); 103 canonical event graphs (52 campaign, 51 comparison).
- **Unit of analysis:** the event engagement graph; all predictions and evaluations are event-level.
- **Campaign graphs:** median node count 506.0, mean 662.2.
- **Comparison graphs:** median node count 3227.0, mean 3479.2.

## 1. Full-Cohort Feature Groups (Out-of-Fold, 5-Fold CV)
| Model / Feature Group | Balanced Accuracy | Macro F1 | Campaign Recall | Comparison Recall | ROC-AUC |
|---|---|---|---|---|---|
| B0a: Log Node Count (LogReg) | 0.8739 | 0.8738 | 0.8654 | 0.8824 | 0.934 |
| B0b: Log Node + Log Edge (LogReg) | 0.8837 | 0.8835 | 0.8654 | 0.902 | 0.9306 |
| Scale Baseline (LogReg) | 0.8837 | 0.8835 | 0.8654 | 0.902 | 0.9306 |
| Structure Group (LogReg) | 0.7687 | 0.7605 | 0.5962 | 0.9412 | 0.8654 |
| Content Group (LogReg) | 0.7866 | 0.7864 | 0.7692 | 0.8039 | 0.859 |
| Combined Group (LogReg) | 0.8937 | 0.893 | 0.8462 | 0.9412 | 0.9793 |

## 2. Size Matching, Primary Ordering Only (exploratory; see the paper for the 20-ordering analysis)

- **Matching Caliper:** 0.2859 (0.25 SD of log node count).
- **Retained Pairs:** 16 pairs (16 campaign, 16 comparison; 71 excluded).
- **Balance Diagnostics (SMD):** Standardised Mean Difference dropped from **-2.2374** before matching to **-0.0954** after matching.

| Feature Group (LogReg) | Full Cohort BA | Matched Cohort BA | Difference |
|---|---|---|---|
| Scale | 0.8837 | 0.5938 | -0.2899 |
| Structure | 0.7687 | 0.6875 | -0.0812 |
| Content | 0.7866 | 0.75 | -0.0366 |
| Combined | 0.8937 | 0.6562 | -0.2375 |

## 3. Edge Budgets (feature sets differ between columns; not a retraining estimate)

| Edge Budget (K) | Eligible Events (Camp / Comp) | D2: retrained, 12 features | D1: frozen, 7 structural features | Feasibility Note |
|---|---|---|---|---|
| K=250 | 51 / 51 | 0.9412 | 0.5882 | Feasible (5-fold CV) |
| K=500 | 48 / 50 | 0.9279 | 0.7358 | Feasible (5-fold CV) |
| K=1000 | 28 / 45 | 0.9063 | 0.7992 | Feasible (5-fold CV) |
| K=2000 | 4 / 32 | N/A | N/A | Infeasible: only 4 campaign events (CV folds empty) |

## 4. Processing Notes
1. **Ingestion:** node-link JSON graphs are streamed directly from `small_encoder_final.tar`; labels come from file-name tokens.
2. **Deduplication:** one byte-identical duplicate (`#SesimiziDuyanVarM[i/ı]`, file names differing only in a dotless ı) is removed by SHA-256.
3. **Embeddings:** the pretrained node and edge embedding vectors (`node_attr`, `edge_attr`) are not used.
4. **Coreness convention:** core numbers are computed on the simple undirected projection with self-loops removed (an earlier version silently set coreness to zero; see the paper's correction history).
5. **Frozen-model scoring:** each sampled event is scored only by the full-cohort fold model that held it out (an earlier version used a budget-specific split; see the paper's correction history).
6. **K = 2000:** too few campaign events for five-fold stratified evaluation.