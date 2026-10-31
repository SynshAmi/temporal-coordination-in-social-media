# Independent Methodological Audit: LEN-Small Robustness Audit

**Document:** `reports/methodology_audit.md`  
**Date:** October 2026  
**Subject:** Methodological verification, data integrity audit, defect corrections, and statistical boundaries of the LEN-Small campaign classification audit.

---

## 1. Executive Summary & Audit Verdict

This audit independently verified the pipeline, data structures, cross-validation protocol, size matching, edge-budget sampling, and statistical reporting. 

The core research question—*whether campaign-versus-comparison classification on LEN-Small is dominated by graph scale, and whether non-scale signals survive size control and observation restriction*—is scientifically substantiated, but required crucial corrections to defects in the original implementation guide.

### Key Audit Findings

| Dimension | Initial Guide Claim / Assumption | Verified Empirical Reality | Audit Verdict |
|---|---|---|---|
| **Archive Format** | ZIP archive of TSV/CSV edgelists + `metadata.csv` | Single tar archive (`small_encoder_final.tar`) containing 104 NetworkX `node_link_data` JSONs. | **Corrected** |
| **Dataset Size & Labels** | 100 events (51 campaign, 49 comparison) | 104 files $\rightarrow$ **103 unique events** (52 campaign, 51 comparison) after removing 1 byte-identical duplicate. Labels derived from filename. | **Verified & Corrected** |
| **Size Distribution** | Campaign graphs assumed larger than comparison | **Inverted Confounder:** Comparison graphs are **$5\times$ larger** (median nodes: 3,227 vs 506; median edges: 3,769 vs 1,078). | **Corrected & Audited** |
| **Scale Baseline** | Assumed secondary to coordination structure | **Dominant:** Log node count alone achieves **0.8739 Balanced Accuracy** (95% CI: [0.805, 0.932]). | **Verified** |
| **Size Matching** | Caliper matching on log node count | 16 pairs (32 events) retained; \|SMD\| reduced from 2.24 to 0.10 (signed: −2.24 to −0.10). Non-scale features retain 0.750 BA (LogReg). Tree-based HGBT collapses on small $N=32$. | **Verified with Caveat** |
| **Edge Budget ($K=2000$)** | Feasible for all $K \in \{250, 500, 1000, 2000\}$ | **Infeasible for 5-fold CV:** Only 4 campaign graphs have $\ge 2,000$ edges. Evaluating 5-fold CV on 4 events violates stratification and causes empty folds. $K=2000$ excluded and marked unavailable. | **Provisional / Excluded** |
| **Metric Calculation** | Guide used `f1_score(..., pos_label=...)` for recall | Mislabeled code corrected to `recall_score(..., pos_label=...)`. | **Corrected** |
| **Frozen vs Retrained Models** | Guide retrained restricted models and called them "approximations" | Implemented **true frozen-model evaluation (D1)** (full-graph trained model evaluated directly on restricted subgraphs) vs **retrained evaluation (D2)**. | **Corrected & Verified** |

---

## 2. Ingestion, Label Mapping & Data Integrity Audit

### A. Authoritative Label Mapping & Deduplication
- **Authoritative Source:** The archive `small_encoder_final.tar` contains no standalone CSV label file. The ground-truth classification is encoded in the file naming convention (`_campaign_fulldata.json` = 1, `_noncampaign_fulldata.json` = 0).
- **Exact Duplicate Detection:** 
  - Member `./small_encoder_final/#SesimiziDuyanVarMı___2023-03-23_campaign_fulldata.json`
  - Member `./small_encoder_final/#SesimiziDuyanVarMi___2023-03-23_campaign_fulldata.json`
  - Both files have identical byte size (25,726,396 bytes) and identical SHA-256 hash (`57da6c1942138f0549c87a9cf696b8c306d32bc1f7aa7b51de9f49b10a313b88`).
  - The duplication arose solely from Unicode Turkish dotless `ı` (U+0131) versus ASCII `i` (U+0069).
  - **Audit Action:** The ingestion script `src/ingest_len.py` detects duplicate SHA-256 hashes on the fly, logging the duplication in `data/manifests/duplicate_files.json` and retaining exactly one canonical record. This leaves **103 unique event graphs** (52 campaign, 51 comparison).

### B. Prevention of Feature Leakage
- **Embedding Vectors:** The raw JSON files contain 772-dim `node_attr` and 776-dim `edge_attr` continuous embedding arrays. These arrays are pre-trained representation vectors. During ingestion, these heavy arrays are discarded.
- **Identifer Leakage Check:**
  - `event_id`, `file_name`, and `sha256` are maintained exclusively in `manifest.parquet` and as DataFrame indices in feature tables.
  - The feature matrices passed to cross-validation explicitly exclude `event_id`, `label`, and `fold_id`.
  - Feature groups consist strictly of mathematical graph properties (scale, density, reciprocity, components, degree Gini, coreness) and aggregate text metrics (exact duplicate fraction, token count dispersion).
  - No text embeddings, user account IDs, or filenames enter the feature space.

---

## 3. Cross-Validation & Preprocessing Integrity

### A. Event-Level Partitioning & Leakage Prevention
- **Outer Fold Consistency:** 5-fold cross-validation is instantiated using `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` partitioned at the *event level*.
- **Sub-observation Rule:** In edge-budget experiments where multiple sampled subgraphs (10 seeds per event) are generated, all 10 views of an event are mapped strictly to the event's outer fold via `assign_view_folds()`. No sampled view of a test event is used for training. For the frozen-model condition (D1), each event is scored only by the full-cohort fold model whose training fold excluded it (see Section 5).
- **Automated Verification:** Verified by `tests/test_leakage.py` (`test_views_stay_in_same_fold` PASSED).

### B. Preprocessing & Hyperparameter Tuning
- **Leakage-Free Pipelines:** Missing value imputation (`SimpleImputer(strategy='median')`) and feature standardization (`StandardScaler()`) are embedded inside an `sklearn.pipeline.Pipeline`.
- Imputer medians and scaler means/variances are fitted **strictly on training fold data** and applied out-of-fold to test samples.
- **Regularization Tuning:** In `tune_logreg_C()`, hyperparameter search over $C \in \{0.01, 0.1, 1.0, 10.0\}$ is performed using an *inner 3-fold stratified cross-validation* loop on the training fold only. Test fold data is never seen during hyperparameter selection.

### C. Metric Calculations
- **Recall Correction:** The initial teammate implementation guide erroneously computed recall via `f1_score(y_true, y_pred, pos_label=...)`. This was corrected to `recall_score(y_true, y_pred, pos_label=...)`.
- **Primary Metrics:** Balanced Accuracy and Macro-F1 are reported as primary metrics due to balanced class weighting. ROC-AUC is computed from continuous out-of-fold decision probabilities (`pipe.predict_proba(X_test)[:, 1]`).

---

## 4. Size Matching Audit

### A. Protocol & Balance Diagnostics
- **Method:** 1:1 nearest-neighbor matching without replacement on $\log(1 + \text{n\_nodes})$.
- **Caliper:** Predeclared at $0.25 \times \text{SD}$ of $\log(1 + \text{n\_nodes})$ (caliper = $0.2859$).
- **Balance Verification:**
  - Before matching: Campaign mean $\log(1+N) = 6.2142$, Comparison mean $\log(1+N) = 7.9184$. Standardised Mean Difference = **$-2.2374$** ($|\text{SMD}| = 2.24$, reflecting that comparison graphs are substantially larger).
  - After matching: Campaign mean = $6.9842$, Comparison mean = $7.0328$. Standardised Mean Difference = **$-0.0954$** ($|\text{SMD}| = 0.10$, satisfying the standard balance criterion $|\text{SMD}| \le 0.10$).
  - Retained: 16 matched pairs (**32 events** in total: 16 campaign, 16 comparison). Excluded: 71 events.

### B. Findings on the Matched Cohort
- **Scale Baseline Collapses:** On the full cohort, scale alone achieves $0.8837$ BA. On the size-matched cohort, scale performance drops to **$0.5938$ BA** (95% CI: [0.417, 0.753]), statistically indistinguishable from chance (0.50).
- **Survival of Rich Features:** Structural features achieve **$0.6875$ BA** (95% CI: [0.524, 0.857]), and content/combined features achieve **$0.7500$ BA** (95% CI: [0.592, 0.906]).
- **Methodological Caveat on Tree Models:** HistGradientBoosting (HGBT) on the 32-event matched cohort predicted constant majority labels ($0.5000$ BA, recall 1.0/0.0) due to tree-split requirements with small sample counts. Linear models with balanced regularization behave stably.
- **Scientific Limitation:** With $N=32$, 95% confidence intervals are wide ($\pm 0.15$). Matching serves as a strong directional sensitivity audit, not definitive proof of causal coordination mechanisms.

---

## 5. Edge-Budget Observation Robustness Audit

### A. Distinguishing Experiment D1 and D2
1. **D2 — Restricted-View Retraining:**
   - Both training and evaluation occur under the restricted observation budget ($K$ edges).
   - Reconstructed graphs simulate an environment where the classifier is trained specifically on incomplete data.
   - Features: all 12 features (scale, structural and content), recomputed on every sampled view.
   - Result: $K=250 \rightarrow 0.9412$ BA; $K=500 \rightarrow 0.9379$ BA; $K=1000 \rightarrow 0.9063$ BA.
2. **D1 — True Frozen Full-Graph Evaluation:**
   - The five structural-group logistic regressions from Exp A (7 structural features) are applied without retraining to the sampled views. Each event is scored only by the fold model whose full-cohort training fold excluded it.
   - Result (fold-aligned): $K=250 \rightarrow 0.5980$ BA [0.505, 0.685]; $K=500 \rightarrow 0.7246$ BA [0.639, 0.807]; $K=1000 \rightarrow 0.7456$ BA [0.650, 0.842].
   - Reference: the same frozen models on the complete graphs of the same eligible events score 0.7843, 0.7821 and 0.7567.
   - **Interpretation:** full-graph structural models lose accuracy on sparse views, clearly at $K=250$; at $K=500$ and $K=1000$ the interval includes the complete-graph value.
   - **Comparability:** D1 uses 7 structural features and D2 all 12 features, so the D1-D2 gap is not a controlled estimate of the effect of retraining.
   - **Correction note:** an earlier evaluation assigned frozen models using the budget-specific fold split, so 26, 64 and 49 events (K=250/500/1000) were scored by a model trained on that event's complete graph. The superseded values were 0.7558 (K=500) and 0.8282 (K=1000). Corrected by `src/reevaluate_d1.py`; `src/train.py` now uses the full-cohort fold assignment.

### B. Prevention of Pseudoreplication
- For each budget $K$, 10 random seeds sample $K$ edges per event.
- If each seed observation were treated as an independent test sample, effective sample size would be artificially inflated ten-fold ($102 \times 10 = 1,020$), producing falsely narrow confidence intervals.
- **Audit Verification:** The pipeline groups predictions by `event_id`, averaging predicted probabilities across seeds before calculating metrics. The reported sample size remains strictly the number of unique eligible events ($N=102, 98, 73$).

### C. Infeasibility of $K=2000$
- At $K=2000$, only **4 campaign events** and 32 comparison events qualify.
- In 5-fold stratified cross-validation, 4 positive samples cannot be partitioned across 5 folds without at least one fold having 0 positive test events and empty training strata.
- Attempting 5-fold CV at $K=2000$ produces undefined metrics or severe fold corruption.
- **Verdict:** $K=2000$ is correctly reported as methodologically infeasible and excluded from main benchmarking.

---

## 6. Summary of Verified vs. Provisional Findings

| Finding / Metric | Status | Substantiation |
|---|---|---|
| **Archive Ingestion (103 unique events)** | **Verified** | SHA-256 deduplication logged in `duplicate_files.json`; 17/17 automated tests pass. Note: the LEN project describes LEN-Small as 100 graphs (51/49); this archive contained 104 files. Cause unresolved. |
| **Inverted Scale Confounder** | **Verified** | Comparison graphs are $5\times$ larger than campaign graphs (median 3,227 vs 506 nodes). |
| **Log Node Baseline ($0.8739$ BA)** | **Verified** | 5-fold out-of-fold CV (`B0a_log_node_logreg`). 95% CI: [0.805, 0.932]. |
| **Combined Full-Cohort Model ($0.9229$ BA)** | **Verified** | 95% CI: [0.867, 0.971]. Overlaps with scale baseline confidence interval. |
| **Size Matching SMD Reduction** | **Verified** | Signed SMD $-2.2374 \to -0.0954$; \|SMD\| $2.24 \to 0.10$ (campaign minus comparison, pooled SD); 16 pairs (32 events) retained. |
| **Matched Scale Drop ($0.5938$ BA)** | **Verified** | Scale model (log N + log E; 0.8837 on the full cohort) falls to chance-level under size control; 95% CI [0.417, 0.753]. |
| **Matched Non-Scale Signal (content $0.7500$, structure $0.6875$ BA)** | **Exploratory** | Above chance on 32 matched events, with wide, overlapping intervals. |
| **D2 Retrained Robustness ($\ge 0.90$ BA)** | **Verified** | Models retrained on sampled views with all 12 features stay accurate. |
| **D1 Frozen Structural Models (0.5980 / 0.7246 / 0.7456 BA)** | **Verified (corrected)** | Fold-aligned; complete-graph reference 0.7843 / 0.7821 / 0.7567. Not like-for-like with D2. |
| **$K=2000$ Budget Evaluation** | **Infeasible** | Only 4 campaign graphs eligible; 5-fold CV statistically invalid. |

---

## 7. Audit Conclusion

The research pipeline is sound, reproducible, and methodologically validated. The scientific conclusions are defensible when presented with their exact sample sizes and confidence intervals. Size confounding is the dominant factor in unconstrained LEN-Small classification, while structural and content signals provide genuine, measurable value when size is controlled.
