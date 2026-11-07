# Final two diagnostics: text availability and the two events without text

**Scope.** This document reports two bounded checks on the view-level message-length dispersion experiment (`research_audit/VIEW_LENGTH_DISPERSION_EXPERIMENT.md`, "v02"):

1. Is `token_std` (stored as `msg_length_dispersion`, called *lensd* in earlier reports) associated with text availability?
2. Do the two campaign events with undefined `token_std` drive the predictive comparisons?

Nothing outside `research_audit/final_diagnostics/` was created or changed. In particular, the manuscript, website, earlier reports, earlier outputs and the investigation ledger are all untouched.

---

## 1. Files and functions inspected

| File | What was inspected |
|---|---|
| `research_audit/scripts/v02_view_lensd_experiment.py` | `run()` (the outer and inner CV, KK/FF regimes, feature sets A–D), how the contrasts are computed, the Holm loop, the partition sensitivity analysis |
| `research_audit/scripts/v01_view_text_availability.py` | the view regeneration, `lensd()` (cleaning, dropping null/empty texts, `ddof = 1`), the definition of `n_usable_text` |
| `research_audit/scripts/s00_engine.py` | `contrast()` (event-level paired bootstrap; all seeds' predictions for a resampled event move together), `holm()`, `loss()`, `auc_rows()`, `ba_rows()`, `pct_p()` |
| `src/train.py` | `tune_logreg_C()` (`StratifiedKFold(min(3, min class count), shuffle, random_state 0)` over the rows it is given; the first C with the maximum mean score wins), `make_logreg_pipeline()` (median imputer, StandardScaler, balanced LR) |
| `src/study2_observation.py` | `run_conditions()`, `fit_predict()` (the Study 2 procedure that v02 mirrors) |
| `src/splits.py` | `make_event_folds()` (event-level StratifiedKFold over the whole manifest; views inherit their event's fold) |
| Data (read only) | `data/processed/sampled_views_v2.parquet`, `data/manifests/manifest.parquet`, `outputs/run_v2/study1/full_graph_features.parquet`, `research_audit/outputs/v01_view_text.csv`, `v02_predictions.npz`, `v02_results.json` |
| Reports | `VIEW_LENGTH_DISPERSION_EXPERIMENT.md` and `FINAL_ROBUSTNESS_AND_CONTRIBUTION_ASSESSMENT.md` (the source of the v02 numbers and the contribution statement). `AUDIT_REPORT.md` and `INVESTIGATION_LEDGER.md` were reviewed in earlier phases; nothing in these checks depends on them beyond the provenance of the corrected run. |

### Event grouping in inner cross-validation and tuning (checked in the code, not taken from the report)

- **Outer folds.** `make_event_folds` assigns each event to one fold. Every view of an event inherits that fold, so no event is ever in both the training and the test set.
- **KK regime.** For each sampling seed `s`, `run()` builds `vmat[s]`, which holds one row per cohort event (a `(K, seed, event)` triple is unique; I asserted this in both new scripts). `tune_logreg_C` and the pipeline are then fitted on `Xv[tr]`, which contains **exactly one view per training event**. Views from different seeds are never pooled in one fit. The inner `StratifiedKFold` therefore splits *events*, and two views of the same event cannot fall on opposite sides of an inner split.
- **FF regime.** One full-graph row per event, so the same holds.
- **Bootstrap.** `contrast()` resamples event indices and takes all 10 seeds' predictions for each resampled event, so events are the unit of uncertainty.

**Conclusion: event grouping is preserved wherever multiple views exist.** No leakage was found, and no correction was needed.

---

## 2. Methodology

### Check 1: text availability vs `token_std` (`scripts/d01_text_availability_association.py`)

- **The variable `m_K`.** `m_K` = `n_usable_text` in `v01_view_text.csv`. It is the number of the K sampled edges whose text is non-null and non-empty after cleaning (lower-casing, URL removal, whitespace collapsing, stripping). These are exactly the texts `token_std` is computed from, as `v01.lensd()` shows. v01 had already verified the regenerated views against the stored ones (max |Δ| = 0.0).
- **Using `m_K/K`.** `m_K/K` = `usable_share`. Within one K it is a constant rescaling of `m_K`, so its correlations are identical to those of `m_K`. It is used only where views are compared across availability levels (the strata and the figure).
- **Views excluded.** Views with undefined `token_std` (`m_K` = 0) are excluded from the correlations. There are 20, 20 and 10 such views, all from the two events in Check 2.
- **Levels of analysis.** Three levels are reported, by K and by class, because an event's 10 views are not independent:
  - **(a) Per-seed view level.** One view per event per seed. Spearman and Pearson are computed within each seed, then averaged over the 10 seeds.
  - **(b) Between-event level.** For each event, the means of `m_K` and `token_std` over its 10 views. Spearman and Pearson are reported, with event-bootstrap 95% CIs (2,000 resamples, seed 7). The campaign − comparison difference in Spearman also gets a CI, with each class resampled separately.
  - **(c) Within-event level.** Spearman between `m_K` and `token_std` across one event's 10 views, which differ only by sampling. This is summarised over events.
- **Class separation within availability strata (descriptive).** Views are split into thirds of `m_K/K`. Within each third, I compute the AUC with which `token_std` ranks comparison views above campaign views, averaged over seeds. For reference, the same AUC is computed for `m_K/K` itself.
- **No models.** No model is fitted in Check 1.

### Check 2: excluding the two events (`scripts/d02_exclude_undefined_events.py`)

- **Procedure.** `run()` is copied verbatim from v02, with one added argument, `exclude`, which removes events from the cohort. Everything else is unchanged:
  - feature sets A–D;
  - K = 250/500/1000;
  - stored views, seeds 100–109;
  - outer folds `make_event_folds(manifest, 5, part)`; each remaining event keeps its original fold;
  - `tune_logreg_C`, using C ∈ {0.01, 0.1, 1, 10} and inner 3-fold CV;
  - `make_logreg_pipeline`, fitted on the training fold only;
  - BA from BA-tuned fits, and log loss and AUC from log-loss-tuned fits;
  - the single-view estimand, averaged over seeds;
  - `contrast()` with 1,000 resamples and seed 7;
  - Holm across the three K, separately for each contrast, metric and analysis.
- **Analyses.** The primary analysis uses partition 42. The sensitivity analysis uses partitions 42 and 1–9, as v02 did.
- **Validation.** With `exclude = ()`, the copied code reproduces every partition-42 prediction in `v02_predictions.npz` exactly (max |Δ| = 0.0).
- **Secondary scoring.** I also re-scored the original v02 fits with the two events dropped from scoring only, without refitting. This separates two effects: the events' own test losses, and their presence in training.

---

## 3. Results

### Check 1a: text availability and `token_std` by class

Views are pooled over 10 seeds. `token_std` is in tokens and is computed over defined views only.

| K | Class | Events | Undefined views | m_K median [IQR] | m_K/K mean | token_std median [IQR] |
|---|---|---|---|---|---|---|
| 250 | campaign | 51 | 20 | 158 [54, 222] | 0.57 | 8.04 [6.58, 9.35] |
| 250 | comparison | 51 | 0 | 207 [183, 223] | 0.80 | 9.86 [8.77, 10.69] |
| 500 | campaign | 48 | 20 | 312.5 [107, 447] | 0.57 | 8.28 [6.55, 9.43] |
| 500 | comparison | 50 | 0 | 408 [364, 441] | 0.80 | 9.92 [8.75, 10.72] |
| 1000 | campaign | 28 | 10 | 530 [197, 897] | 0.54 | 8.06 [6.22, 9.21] |
| 1000 | comparison | 45 | 0 | 811 [733, 874] | 0.79 | 9.87 [8.63, 10.73] |

Campaign views have less usable text and much more spread in how much they have. They also have lower `token_std`.

### Check 1b: association between `m_K` and `token_std`

These are Spearman correlations. For `m_K/K` within a K they are identical.

| K | Class | (a) per-seed view ρ, mean [seed range] | (b) between-event ρ [95% CI] (Pearson) | (c) within-event ρ, median [IQR]; share > 0 |
|---|---|---|---|---|
| 250 | campaign (n = 49) | −0.18 [−0.27, −0.13] | −0.18 [−0.48, +0.14] (−0.15) | +0.05 [−0.17, +0.30]; 57% |
| 250 | comparison (n = 51) | −0.37 [−0.44, −0.33] | −0.37 [−0.59, −0.10] (−0.41) | −0.06 [−0.31, +0.21]; 43% |
| 250 | pooled (n = 100) | −0.11 | −0.11 [−0.31, +0.09] (+0.02) | — |
| 500 | campaign (n = 46) | −0.18 [−0.25, −0.12] | −0.18 [−0.47, +0.14] (−0.15) | −0.06 [−0.31, +0.18]; 46% |
| 500 | comparison (n = 50) | −0.36 [−0.40, −0.32] | −0.36 [−0.59, −0.07] (−0.40) | +0.06 [−0.10, +0.32]; 60% |
| 500 | pooled (n = 96) | −0.14 | −0.15 [−0.35, +0.08] (+0.01) | — |
| 1000 | campaign (n = 27) | −0.15 [−0.18, −0.11] | −0.16 [−0.56, +0.26] (−0.18) | +0.07 [−0.24, +0.38]; 59% |
| 1000 | comparison (n = 45) | −0.50 [−0.54, −0.47] | −0.50 [−0.70, −0.25] (−0.50) | +0.10 [−0.32, +0.32]; 58% |
| 1000 | pooled (n = 72) | −0.18 | −0.18 [−0.43, +0.07] (+0.04) | — |

Here n counts events with `token_std` defined in all 10 views.

The campaign − comparison difference in between-event ρ is:

| K | Difference [95% CI] | Bootstrap p |
|---|---|---|
| 250 | +0.19 [−0.18, +0.59] | 0.33 |
| 500 | +0.17 [−0.23, +0.55] | 0.43 |
| 1000 | +0.34 [−0.15, +0.84] | 0.18 |

### Check 1c: class separation by `token_std` within thirds of text availability

The AUC is the probability that a comparison view has higher `token_std` than a campaign view, averaged over the 10 seeds.

| K | Lowest third of m_K/K | Middle third | Highest third | All views | AUC of m_K/K itself |
|---|---|---|---|---|---|
| 250 | 0.81 (248 / 82) | 0.93 (83 / 249) | 0.77 (159 / 179) | 0.78 | 0.63 |
| 500 | 0.81 (230 / 89) | 0.93 (75 / 245) | 0.77 (155 / 166) | 0.77 | 0.61 |
| 1000 | 0.88 (150 / 90) | 0.92 (23 / 216) | 0.79 (97 / 144) | 0.81 | 0.63 |

Counts in parentheses are campaign / comparison views, summed over the 10 seeds. The strata pool views, so the 10 views of an event fall in the same or nearby strata. The 23 campaign views in the K = 1000 middle third come from only a few events.

Figure: `outputs/d01_fig_mK_vs_tokenstd.png` (data in `outputs/d01_fig_data.csv`).

### Check 2a: the two events

| Event ID | Manifest label | Full-graph label | Edges | Views per K (250 / 500 / 1000) | Undefined `token_std` |
|---|---|---|---|---|---|
| `Tapuma_YapıKayıt___2023-04-19_campaign_fulldata` | 1 (campaign) | 1 | 1,186 | 10 / 10 / 10 | all views; full graph also undefined |
| `YapıKayıt_YoksaOyyok___2023-05-01_campaign_fulldata` | 1 (campaign) | 1 | 546 | 10 / 10 / not eligible | all views; full graph also undefined |

No other view has undefined `token_std`. After exclusion the cohorts are:

| K | Events | Campaign | Comparison |
|---|---|---|---|
| 250 | 100 | 49 | 51 |
| 500 | 96 | 46 | 50 |
| 1000 | 72 | 27 | 45 |

### Check 2b: primary analysis (partition 42), original vs both events excluded and refitted

Each cell gives Δ [95% event-bootstrap CI], then the Holm-adjusted p across K. A negative Δ log loss favours adding `token_std`.

The bootstrap has 1,000 resamples, so an unadjusted p cannot be resolved below 0.001. The smallest adjusted p, three times that, is therefore 0.003, and values reported as 0.000 in the CSVs are shown here as < 0.003.

**B − A: `token_std` beyond N_K**

| K | Δ log loss (original) | Δ log loss (excluded) | Δ AUC (original) | Δ AUC (excluded) | Δ BA (original) | Δ BA (excluded) |
|---|---|---|---|---|---|---|
| 250 | −0.036 [−0.112, +0.038]; 0.35 | −0.039 [−0.117, +0.030]; 0.29 | −0.002 [−0.034, +0.025]; 1.00 | −0.001 [−0.032, +0.027]; 1.00 | +0.028 [−0.007, +0.066]; 0.15 | +0.033 [−0.004, +0.077]; 0.08 |
| 500 | −0.068 [−0.163, +0.018]; 0.27 | −0.070 [−0.163, +0.017]; 0.20 | +0.002 [−0.037, +0.038]; 1.00 | +0.002 [−0.036, +0.042]; 1.00 | +0.070 [+0.020, +0.127]; < 0.003 | +0.064 [+0.015, +0.121]; 0.018 |
| 1000 | −0.114 [−0.218, −0.011]; 0.084 | −0.108 [−0.215, +0.004]; 0.17 | +0.065 [+0.010, +0.144]; 0.072 | +0.066 [+0.005, +0.143]; 0.10 | +0.091 [+0.010, +0.176]; 0.056 | +0.087 [+0.013, +0.167]; 0.020 |

**D − C: `token_std` beyond N_K + structure**

| K | Δ log loss (original) | Δ log loss (excluded) | Δ AUC (original) | Δ AUC (excluded) | Δ BA (original) | Δ BA (excluded) |
|---|---|---|---|---|---|---|
| 250 | −0.047 [−0.134, +0.037]; 0.27 | −0.053 [−0.118, +0.008]; 0.10 | +0.011 [−0.020, +0.046]; 1.00 | +0.014 [−0.011, +0.043]; 0.52 | +0.020 [−0.008, +0.047]; 0.30 | +0.022 [−0.013, +0.057]; 0.34 |
| 500 | −0.091 [−0.184, −0.001]; 0.096 | −0.063 [−0.128, −0.000]; 0.10 | +0.011 [−0.026, +0.050]; 1.00 | +0.010 [−0.022, +0.045]; 0.52 | +0.037 [+0.003, +0.075]; 0.12 | +0.040 [+0.009, +0.079]; 0.054 |
| 1000 | −0.138 [−0.208, −0.076]; < 0.003 | −0.124 [−0.215, −0.037]; 0.018 | +0.045 [+0.002, +0.111]; 0.066 | +0.044 [−0.006, +0.121]; 0.45 | +0.031 [−0.010, +0.086]; 0.30 | +0.017 [−0.037, +0.079]; 0.56 |

In every cell, the log-loss direction favours adding `token_std` in **10 of 10** sampling seeds, both before and after exclusion.

### Check 2c: 10-partition sensitivity, Δ log loss, original vs excluded

The last column counts the partition × seed repeats (out of 100) in which log loss favours adding `token_std`.

| K | Contrast | Original | Excluded | Repeats favouring `token_std` (orig. → excl.) |
|---|---|---|---|---|
| 250 | B − A | −0.041 [−0.114, +0.031]; 0.29 | −0.038 [−0.115, +0.032]; 0.29 | 99 → 95 |
| 250 | D − C | −0.060 [−0.131, +0.009]; 0.14 | −0.057 [−0.136, +0.014]; 0.14 | 99 → 98 |
| 500 | B − A | −0.065 [−0.155, +0.019]; 0.29 | −0.068 [−0.160, +0.015]; 0.29 | 99 → 100 |
| 500 | D − C | −0.062 [−0.134, +0.006]; 0.14 | −0.059 [−0.130, +0.006]; 0.14 | 94 → 89 |
| 1000 | B − A | −0.102 [−0.204, +0.004]; 0.18 | −0.098 [−0.199, +0.019]; 0.29 | 100 → 100 |
| 1000 | D − C | −0.129 [−0.204, −0.050]; 0.006 | −0.129 [−0.206, −0.053]; 0.018 | 99 → 98 |

Δ AUC and Δ BA under the sensitivity analysis move by ≤ 0.009 in every cell. Full values are in `outputs/d02_comparison_with_original.csv`.

---

## 4. Comparison with the original experiment

### Check 1

v02 reported that campaign views have less usable text (0.54–0.57 vs 0.79–0.80). These checks add four findings:

- **Within each class, the association is negative.** Events or views with more usable text tend to have *lower* `token_std`.
  - **Comparison events:** moderate, ρ ≈ −0.36 to −0.50, with CIs excluding 0 at every K.
  - **Campaign events:** weak, ρ ≈ −0.16 to −0.18, with CIs including 0 at every K.
  - **Class difference:** not distinguishable from zero at any K. The bootstrap CIs all include 0, and this is not evidence that the associations are equal.
- **The pooled correlation is misleading.** The pooled between-event ρ is weakly negative (−0.11 to −0.18), and the pooled Pearson is ≈ 0. This happens because, *between* the classes, availability and `token_std` move together: campaign events have less text *and* lower `token_std`. *Within* each class they move the other way. A single pooled correlation would understate the within-class association and hide that the between-class difference has the opposite sign.
- **Within an event there is no association.** When only sampling varies, the median within-event ρ is close to 0 (−0.06 to +0.10), with about half the events positive. The random number of usable texts drawn in a view therefore shows no consistent relation to that view's `token_std`. The within-event range of `m_K` is narrow, however, so this level has limited sensitivity.
- **`token_std` separates the classes within every availability third** (AUC 0.77–0.93), and at least as well as across all views (0.77–0.81). Availability itself separates the classes much less (0.61–0.63).

### Check 2

- **Log loss.** Excluding the two events changes the primary estimates by 0.002–0.014 in all cells except D − C at K = 500, where the estimate moves from −0.091 to −0.063.
  - That change comes from refitting, not from the two events' own test losses. With the original fits and the two events dropped from scoring only, the estimate is −0.093 [−0.202, −0.003] (`outputs/d02_contrasts.csv`).
  - Removing two training events changes fold composition and the C selected by the inner CV, and partition 42 is sensitive to that.
  - In the 10-partition sensitivity analysis the same contrast moves only from −0.062 to −0.059.
- **Direction.** The direction is unchanged in every cell: 10/10 seeds favour adding `token_std` everywhere in the primary analysis, and 89–100 of 100 repeats in the sensitivity analysis.
- **Holm-adjusted results after exclusion:**
  - D − C at K = 1000 remains the strongest result. Log loss −0.124 [−0.215, −0.037], Holm p = 0.018 in the primary analysis; −0.129 [−0.206, −0.053], Holm p = 0.018 in the sensitivity analysis.
  - B − A at K = 1000 had a log-loss CI just excluding 0 (Holm p = 0.084). It now just includes 0: [−0.215, +0.004], Holm p = 0.17. It was not Holm-significant before either.
  - The BA gains for B − A at K = 500 and K = 1000 remain Holm-significant (0.018 and 0.020). AUC is still ≈ 0 at K = 250 and 500.
- **Overall.** The conclusions, the pattern across K and the threshold-dependence of the BA gains are unchanged.

---

## 5. Implementation concerns

- **No implementation error was found.** Event grouping holds in the outer folds, the inner tuning CV and the bootstrap (§1). The copied procedure reproduces v02 exactly.
- **The p-value floor (a reporting point, not a bug).** With 1,000 bootstrap resamples, a bootstrap p-value of "0" means "< 0.001 before adjustment". After Holm across three K it means at most 0.003. v02 already reported these values as "< 0.003", and this report does the same.
- **Folds are inherited, not re-stratified (a design property).** Outer folds are made on the full manifest and then restricted to each cohort, as in Study 2. Cohort folds are therefore not exactly class-balanced, and removing events slightly unbalances them further. I kept this design, as instructed, rather than re-stratifying.
- **Tuning makes single-partition estimates sensitive to small cohort changes.** The D − C log-loss estimate at K = 500 moves by 0.028 when two training events are removed. This is the C selection responding to a small change in fold composition, not an error. It is why v02's 10-partition sensitivity analysis is the more stable summary.

---

## 6. Conclusion

**Is `token_std` substantially associated with text availability?**

- **Moderately within comparison events, weakly within campaign events.** Comparison events with more usable text have lower `token_std` (event-level ρ −0.36 to −0.50). Among campaign events the association is weaker (−0.16 to −0.18) and not distinguishable from zero. The difference between the classes is not statistically resolved.
- **Availability does not appear to account for the class separation.** The association has the opposite sign to the class difference, and `token_std` still separates the classes within narrow availability strata (AUC 0.77–0.93), much better than availability alone (0.61–0.63).
- **Two qualifications remain:**
  - `token_std` is not independent of availability.
  - These descriptive results cannot rule out other dependencies between availability and message content.

  The paper should therefore describe `token_std` as measured on the text that is present. It should report the class difference in text availability alongside it, and should not present it as independent of availability.

**Do the two undefined events materially influence the predictive results?**

- **No.** Excluding them and refitting changes the log-loss differences by ≤ 0.014 in 5 of the 6 primary contrasts. Directions and seed-level consistency are unchanged, and the strongest result (D − C at K = 1000) remains Holm-significant.
- **One single-partition estimate moved by 0.028** (D − C at K = 500). This is attributable to tuning sensitivity, and the 10-partition analysis is stable.
- **One borderline interval crossed zero.** B − A at K = 1000 moved from just excluding 0 to just including it. It was not Holm-significant before either, so this should not be read as evidence of no effect.

**Does either diagnostic change the strongest defensible contribution of the paper?**

- **No.** The contribution remains as stated in the earlier assessment:
  - Retained-engagement graphs carry class information beyond observed scale.
  - Most of the content contribution is concentrated in message-length dispersion.
  - That measurement survives fixed-budget sampling.
  - Its added predictive value under partial observation is consistent in direction and supported with multiplicity control only at K = 1000 beyond N_K + structure.
- **Wording to add.** The two checks support adding two sentences:
  - one noting that campaign events have less usable text and that the dispersion feature is computed on the usable texts only, and moderately associated with their number within comparison events;
  - one noting that excluding the two campaign events without text does not change the comparisons.

---

## 7. Recommendation

**Freeze the experimental work and begin manuscript development.** Both questions are resolved with the original procedure intact. Neither check exposes an implementation error or a change to the conclusions, and nothing further needs to be run.

---

## Files and reproduction

All files are under `research_audit/final_diagnostics/`.

- **Report:** `FINAL_TWO_DIAGNOSTICS.md` (this file).
- **Check 1 script:** `scripts/d01_text_availability_association.py`.
- **Check 1 outputs** (in `outputs/`):
  - `d01_descriptives.csv`
  - `d01_associations.csv`
  - `d01_stratified_class_separation.csv`
  - `d01_results.json`
  - `d01_fig_mK_vs_tokenstd.png`
  - `d01_fig_data.csv`
  - `d01.log`
- **Check 2 script:** `scripts/d02_exclude_undefined_events.py`.
- **Check 2 outputs** (in `outputs/`):
  - `d02_contrasts.csv` (both the excluded-and-refitted and the scored-only versions, primary and sensitivity)
  - `d02_comparison_with_original.csv`
  - `d02_results.json`
  - `d02_predictions_excluding_two_events.npz`
  - `d02.log`

From the project root:

```
python research_audit/final_diagnostics/scripts/d01_text_availability_association.py
python research_audit/final_diagnostics/scripts/d02_exclude_undefined_events.py
```

- **d01** reads `research_audit/outputs/v01_view_text.csv` and runs in seconds.
- **d02** first validates its copied procedure against `v02_predictions.npz`, then refits 240 jobs. It takes about 3 minutes.
