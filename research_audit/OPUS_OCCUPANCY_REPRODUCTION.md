# Independent Reproduction: Endpoint Occupancy and Degree-Sequence Signal

Date: 2026-11-04. Scope: the analysed 103-graph LEN-Small archive only. **Every result here is
exploratory.** K = 250 was chosen after earlier results had been seen, and the comparisons in §3.4 were
added after the main run. Nothing in this document generalises beyond this archive. No manuscript,
website or earlier audit output was changed. New files: `research_audit/scripts/o01–o04_*.py` and
`research_audit/outputs/o0*_*`.

**Verdict: PARTIALLY REPRODUCED.** The pilot's numbers reproduce almost exactly. Its interpretation —
that E[N_K] carries label information *beyond graph counts* — holds only in a narrow sense:
- it beats a **linear** count model in ranking (AUC);
- it does **not** reliably improve log loss;
- it is **not** detectably better than flexibly modelled counts (QDA or quadratic terms);
- it is largely matched by two simple degree-sequence summaries (Σd² and the degree-1 fraction);
- its advantage fades at larger K.

See §7.

---

## 1. Data provenance and equivalence checks

| Item | Finding | Evidence |
|---|---|---|
| Original archive | `small_encoder_final.tar` at the project root, 5,792,081,920 bytes, SHA-256 `aaa1fdc1…1c75` (earlier audit) | `outputs/a01_archive_summary.json` |
| Pilot scripts | Not at `research_audit/reference/pilot_scripts.zip` as stated. Found at `reference/pilot_scripts.zip` (project root; identical copy in `Downloads`, SHA-256 prefix `bb993dbd5e2b9c9d`). Contains `a1.py`–`a7.py`. **Read as text only; not executed, not extracted, not moved.** | listing via `zipfile` |
| Raw vs exported graphs | All **103/103** exported graphs (`frontend/public/data/len/events/*.json`, the pilot's input) are identical to the raw archive graphs. Identical: node count, node ids 0..N−1, multiset **and order** of directed edges, self-loop counts, interaction counts, incident-edge degrees d_v, labels (file token = export = manifest; 52 campaign / 51 comparison). The one unmatched raw member is the byte-identical duplicate the pipeline drops (`#SesimiziDuyanVarMı…`; the dotted-i copy is kept). | `scripts/o01_export_equivalence.py` → `outputs/o01_export_equivalence.{json,csv}` |
| Name encoding (discrepancy, resolved) | 41 archive file names are stored in decomposed Unicode (NFD); the pipeline normalises names to NFC (`src/ingest_len.py:67`). A first, un-normalised match found only 62/103 graphs. After applying the same NFC normalisation, all 103 match. No graph content differs. | o01 log |
| Graph representation | Directed, simple (no repeated directed pair), self-loops present (4,212 in total, every graph), no isolated nodes. Edges are directed `(source, target)` pairs; interaction counts are not used by any feature here. | a01, o01 |
| Degree definition: this reproduction | d_v = number of distinct directed edges incident to v = out_v + in_v − [self-loop at v]. Computed from the raw tar (`o02`). | `scripts/o02_occupancy_features.py` |
| Degree definition: pilot | Identical: `bincount(s) + bincount(t) − bincount(s[loop])` on the exported edges (`a1.py`, `a2.py`). Because the exported graphs equal the raw graphs, the pilot's d_v equal ours (checked: `all_d_v_equal: true`). | `reference/pilot_scripts.zip/a2.py` |
| Other pilot preprocessing differences | (i) K = min(250, m) for all 103 events (one event, `Gelenekten_Geleceğe___2023-05-13`, has m = 206, so its "E[N_250]" equals its node count 214); (ii) homogeneous approximation n[1 − (1 − K/m)^(2m/n)], which counts self-loops twice in the mean degree; (iii) NaN features filled with the median of the full data before CV (a small leakage, but no feature used in the occupancy comparisons has NaNs); (iv) C tuned on log loss, with BA from the same fit. | `a2.py` |

---

## 2. Methodology and feature definitions

**Population.** Primary analysis (configuration A): the **102 events with m ≥ 250** (51 campaign / 51
comparison), so E[N_250] is defined without clipping. Configuration B reimplements the pilot's
specification on all 103 events, independently of its code. K-sensitivity: K = 500 (98 events) and
K = 1000 (73 events), each on its own eligible events.

**Features** (all computed from the raw archive; `o02`):

| Name | Definition |
|---|---|
| counts | log(1+n), log(1+m); n = node count, m = directed edge count including self-loops |
| counts + nonlinear | counts + log(1+n)², log(1+m)², log(1+n)·log(1+m) (the paper's M0q) |
| E[N_K] | log of Σ_v [1 − C(m − d_v, K) / C(m, K)], computed exactly with log-gamma; K = 250 unless stated |
| degree Gini | Gini of in-degree and of out-degree (paper eq. 1) |
| Σd² + degree-1 fraction | log Σ_v d_v² and the share of nodes with d_v = 1 |
| homogeneous approx. (pilot) | log of n[1 − (1 − K/m)^(2m/n)] |

**Model.** StandardScaler + LogisticRegression(class_weight = "balanced"):
- **Tuning:** C chosen by GridSearchCV over 10^−3…10^3 (A: 7 values; B: 9 values, as in the pilot), with an inner StratifiedKFold(3, shuffle, seed 0) scored on log loss.
- **Fitting:** done inside each outer training fold only.
- **Decisions:** BA uses threshold 0.5 on the same fit.
- **QDA:** "QDA on counts" (StandardScaler + QDA) is included only to compare with the pilot.

**Resampling.** 20 repeats of StratifiedKFold(5, shuffle). Seeds are 1000 + r for A and 100 + r for B
(the pilot's). Splits are identical across all models within a configuration.

**Uncertainty, three levels.** None of these accounts for variation across independent datasets.
1. *Repeat level:* mean and SD over 20 repeats of the pooled out-of-fold metric. Paired differences use Nadeau–Bengio-corrected resampled t intervals (variance factor 1/20 + 1/4).
2. *Event level (primary for inference):* metrics of the out-of-fold probabilities averaged over repeats. Paired differences use an event bootstrap (2,000 resamples, seed 7). This is the only interval that resamples the 102 events, the actual units.
3. *Fold level:* SD of per-fold AUC and log loss over the 100 folds, and the share of folds with a positive paired AUC difference.

The repeat-level NB intervals are much narrower than the event bootstrap: repeated CV re-splits the same 102 events and does not create new ones. Inference below relies on the event bootstrap.

**Multiplicity.** No correction across the eight contrasts in §3.2 (exploratory). Across K, the counts + E[N_K] vs counts AUC contrast is Holm-adjusted (§3.3).

---

## 3. Reproduced numerical results

### 3.1 Performance (configuration A: 102 events, K = 250)

Columns 2–4: mean over 20 repeats (SD across repeats). Columns 5–7: from repeat-averaged probabilities. Last column: SD over 100 folds.

| Model | BA | AUC | Log loss | AUC (avg. prob.) | LL (avg. prob.) | BA (avg. prob.) | Fold AUC SD |
|---|---|---|---|---|---|---|---|
| counts | 0.872 (0.008) | 0.927 (0.007) | 0.340 (0.019) | 0.928 | 0.332 | 0.873 | 0.057 |
| counts + nonlinear | 0.846 (0.022) | 0.939 (0.006) | 0.312 (0.018) | 0.942 | 0.303 | 0.843 | 0.048 |
| E[N_K] alone | 0.928 (0.005) | 0.962 (0.005) | 0.286 (0.042) | 0.963 | 0.275 | 0.931 | 0.041 |
| counts + E[N_K] | 0.899 (0.011) | 0.954 (0.006) | 0.302 (0.047) | 0.957 | 0.286 | 0.892 | 0.043 |
| counts + degree Gini | 0.854 (0.020) | 0.909 (0.013) | 0.418 (0.059) | 0.922 | 0.349 | 0.853 | 0.063 |
| counts + Σd² + degree-1 frac | 0.915 (0.010) | 0.947 (0.004) | 0.318 (0.020) | 0.949 | 0.305 | 0.931 | 0.047 |
| homogeneous approx. (pilot) | 0.847 (0.013) | 0.926 (0.004) | 0.370 (0.013) | 0.925 | 0.365 | 0.863 | 0.056 |
| QDA on counts | 0.863 (0.008) | 0.952 (0.002) | 0.301 (0.007) | 0.951 | 0.297 | 0.873 | 0.042 |

The log-loss SD across repeats is large for every model containing E[N_K] (0.042–0.047, vs 0.019 for counts). A few events receive very confident wrong predictions in some splits.

### 3.2 Paired differences (configuration A; event bootstrap = primary interval)

| Contrast (A − B) | ΔAUC, event bootstrap | ΔLL, event bootstrap | ΔBA, event bootstrap | ΔAUC, NB (repeats) | Folds ΔAUC > 0 | Events with lower LL |
|---|---|---|---|---|---|---|
| counts + E[N_K] − counts | **+0.030 [+0.005, +0.061]** | −0.046 [−0.105, +0.020] | +0.020 [−0.037, +0.082] | +0.027 [+0.019, +0.035] | 83% | 76/102 |
| E[N_K] alone − counts | **+0.036 [+0.006, +0.073]** | −0.057 [−0.136, +0.033] | +0.059 [−0.009, +0.133] | +0.035 [+0.027, +0.043] | 83% | 69/102 |
| counts + E[N_K] − counts + degree Gini | **+0.035 [+0.002, +0.074]** | [−0.132, +0.021] | — | +0.045 [+0.029, +0.060] | 89% | 84/102 |
| counts + E[N_K] − counts + Σd² + deg-1 | +0.008 [+0.000, +0.020] | [−0.047, +0.008] | BA lower (rep. −0.016) | +0.006 [+0.002, +0.010] | 43% | 63/102 |
| counts + Σd² + deg-1 − counts | +0.022 [−0.003, +0.054] | [−0.100, +0.054] | — | +0.021 [+0.012, +0.029] | 74% | 54/102 |
| counts + degree Gini − counts | −0.005 [−0.019, +0.009] | [−0.006, +0.037] | — | −0.018 [−0.032, −0.004] | 14% | 19/102 |
| counts + nonlinear − counts | +0.015 [−0.003, +0.035] | [−0.070, +0.010] | — | +0.012 [+0.003, +0.020] | 59% | 74/102 |
| E[N_K] alone − homogeneous approx. | **+0.039 [+0.010, +0.074]** | [−0.176, +0.019] | — | +0.036 [+0.030, +0.042] | 81% | 77/102 |

Notes:
- "—" means the value is in `outputs/o03_contrasts.csv` / `o03_results.json` but omitted here for space.
- All twenty repeats favour counts + E[N_K] over counts in AUC, and 19/20 in log loss. These repeats reuse the same events and are not independent evidence.

### 3.3 K sensitivity (counts + E[N_K] − counts; Holm across the three K)

| K | Events | ΔAUC, event bootstrap | p (bootstrap) | Holm p | ΔLL, event bootstrap |
|---|---|---|---|---|---|
| 250 | 102 | +0.030 [+0.005, +0.061] | 0.015 | 0.045 | [−0.105, +0.020] |
| 500 | 98 | +0.017 [−0.007, +0.042] | 0.147 | 0.294 | [−0.071, +0.009] |
| 1000 | 73 | +0.002 [−0.016, +0.021] | 0.764 | 0.764 | [−0.028, +0.036] |

The cohorts differ by K, so the decline mixes the effect of K with the change of population.

### 3.4 Post-hoc: flexible count models (`scripts/o04_posthoc_flexible_counts.py`; same 102 events and splits)

Added after §3.1 showed QDA on counts reaching AUC 0.951. Not pre-specified.

| Contrast | ΔAUC | ΔLL | ΔBA |
|---|---|---|---|
| E[N_K] alone − QDA on counts | +0.012 [−0.042, +0.061] | −0.022 [−0.159, +0.136] | +0.059 [+0.005, +0.120] |
| E[N_K] alone − counts + nonlinear | +0.021 [−0.012, +0.059] | −0.027 [−0.098, +0.045] | +0.088 [+0.013, +0.167] |
| counts + nonlinear + E[N_K] − counts + nonlinear | +0.018 [−0.014, +0.053] | −0.024 [−0.081, +0.039] | +0.059 [−0.003, +0.123] |

Against flexibly modelled counts, the ranking and log-loss advantages of E[N_K] are not detectable.
The remaining BA differences concern the 0.5 decision threshold of balanced-weight models, a
threshold-dependent quantity known to be unstable here (see the earlier audit, §D).

---

## 4. Plots

All figures use configuration A (102 events with m ≥ 250; 51 campaign, 51 comparison). Plotting data
is saved next to each figure. Colours: red = campaign, blue = comparison (labels from the dataset file names).

**Figure 1: `outputs/o03_fig1_occupancy_vs_m.png`** (data: `o03_fig1_data.csv`)
- *X:* edge count m of the full graph (directed edges incl. self-loops), raw, log scale.
- *Y:* E[N_250] in nodes, raw (exact formula, not a simulation).
- *Points:* one per event, n = 102. Dotted line: the upper bound 2K = 500.
- *Reading:* the classes overlap in m between about 700 and 2,000 edges. At a given m, campaign events tend to have lower expected occupancy (more edges concentrated on fewer nodes).

**Figure 2: `outputs/o03_fig2_auc_by_model.png`** (data: `o03_fig2_data.csv`)
- *X:* out-of-fold ROC-AUC (cross-validated).
- *Y:* feature set / model.
- *Dots and whiskers:* AUC of the out-of-fold probabilities averaged over 20 repeats, with 95% event-bootstrap intervals of each model's own AUC (2,000 resamples).
- *Orange bar:* range of AUC across the 20 CV repeats.
- *Caution:* the single-model intervals overlap heavily. Paired differences must be read from §3.2 and §3.4, not from overlap in this figure.

**Figure 3: `outputs/o03_fig3_degree_summaries.png`** (data: `o03_fig3_data.csv`)
- *Panels 1–3:*
  - *X:* node count n, raw, log scale.
  - *Y, panel 1:* E[N_250] (log scale).
  - *Y, panel 2:* Σ_v d_v² (log scale).
  - *Y, panel 3:* share of nodes with d_v = 1 (linear).
- *Panel 4:* residual of log E[N_250] after an ordinary-least-squares fit on (log(1+n), log(1+m)) over all 102 events (not cross-validated), by label; bars mark class medians.
- *Reading:*
  - E[N_250] is a tight, saturating function of n (panel 1).
  - After a linear adjustment for log n and log m, the residual medians are nearly equal across classes; campaign events are only more dispersed (panel 4).
  - The extra ranking signal therefore sits largely in the nonlinear shape of size, consistent with QDA / quadratic counts closing most of the gap (§3.4).

---

## 5. Comparison with the pilot

| Pilot reference value | Configuration B (pilot spec, reimplemented) | Configuration A (primary) | Agreement |
|---|---|---|---|
| E[N_250]: BA 0.928, AUC 0.961, LL 0.306 | 0.928, 0.961, 0.305 | 0.928, 0.962, 0.286 | Reproduced (B exact; A differs only in LL, by excluding the clipped event) |
| Counts M0: BA 0.872, AUC 0.927, LL 0.340 | 0.872, 0.926, 0.341 | 0.872, 0.927, 0.340 | Reproduced |
| QDA: BA 0.857, AUC 0.948, LL 0.319 | 0.860, 0.948, 0.317 | 0.863, 0.952, 0.301 | Reproduced within 0.003 (B) |
| E[N_250] − M0: ΔAUC +0.035 [+0.006, +0.072] | +0.036 [+0.006, +0.072] | +0.036 [+0.006, +0.073] | Reproduced |
| E[N_250] − homogeneous: ΔAUC +0.037 [+0.010, +0.072] | +0.037 [+0.009, +0.073] | +0.039 [+0.010, +0.074] | Reproduced |

Explanation of the small discrepancies:
- In B, QDA BA and LL differ by ≤ 0.003; the cause was not traced.
- A's lower log loss for E[N_K] (0.286 vs 0.305) comes from excluding the one event with m < 250, whose clipped value E = n behaves as an outlier.
- None of the pilot's pipeline choices (clipping, binomial approximation, median imputation before CV) changes the numbers materially.

Where the pilot's interpretation goes beyond the evidence:
- "Beyond basic counts" holds against a *linear* count model only.
- The comparison with QDA, which the pilot itself ran, gives no detectable ranking difference (§3.4).
- Most of the gain is recovered by Σd² and the degree-1 fraction (§3.2), so the occupancy formula itself is not uniquely informative.
- No log-loss gain is reliable.

---

## 6. Limitations and unresolved discrepancies

- **Exploratory and post-hoc.** K = 250 was chosen after seeing results, and §3.4 was added after §3.1. The K = 250 ΔAUC has Holm p = 0.045 only under a three-K family that does not capture these earlier choices.
- **Effective sample size.** 102 events (51 / 51). Repeats and folds reuse them. Two campaign hashtags appear twice (dependence).
- **Population.** This archive is not the tabulated LEN-Small release, and the LEN-Small selection rule is contradicted by its own published tables (`AUDIT_REPORT.md` §B). Size–label associations here need not hold in LEN or in other data.
- **Threshold metrics.** BA differences depend on the 0.5 threshold of balanced-weight models; ranking (AUC) and probability (log loss) results should take precedence.
- **Interval methods disagree.** Repeat-level (NB) intervals exclude zero for several contrasts whose event-bootstrap intervals include zero. The event bootstrap is the appropriate one for these units.
- **Unresolved.** Whether degree heterogeneity contributes label information beyond a flexible function of size cannot be decided with 102 events: the post-hoc intervals are wide (±0.05 in AUC). Settling it needs independent graphs and a pre-specified analysis.
- **Not done** (by instruction): pilot scripts not executed; no external data; no GNNs or broad model search; earlier audit outputs, the ledger, the manuscript and the website were not modified.

---

## 7. Verdict

**PARTIALLY REPRODUCED.**

**Reproduced.**
- The pilot's input data equal the raw archive exactly.
- E[N_K] is computed correctly under the archive's conventions.
- Every reference value reproduces to within 0.003: performance of E[N_250], counts and QDA, and both AUC contrasts with their intervals.
- Under my own primary specification, E[N_250] alone and counts + E[N_250] rank events better than a *linear* count model (ΔAUC +0.036 [+0.006, +0.073] and +0.030 [+0.005, +0.061]).

**Not supported in this archive.**
- **Improvement beyond counts in general.** Against QDA or quadratic count models, the ranking advantage is not detectable (ΔAUC +0.012 [−0.042, +0.061]).
- **Improvement in log loss.** All event-bootstrap intervals include zero.
- **Uniqueness of the occupancy formula.** Σd² + degree-1 fraction come within ΔAUC +0.008.
- **Robustness to K.** At K = 500 the gain is not detectable, and at K = 1000 it is near zero.

**Defensible statement.** In this 103-graph archive, the exact expected endpoint occupancy at K = 250 is a strong single predictor of the file-name labels (AUC ≈ 0.96). It ranks events better than a linear function of log node and edge counts. But this sample cannot distinguish it from flexible functions of size or from simple degree-sequence summaries. Whether degree heterogeneity carries label information beyond size remains an open, exploratory question.
