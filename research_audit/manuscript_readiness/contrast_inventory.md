# Contrast inventory: Study 2 models A–D

This inventory uses existing outputs only. Nothing was computed for it, and a missing cell is marked **NOT COMPUTED**.

**Models.** All are single-view logistic regression in the KK regime (trained and scored on views of the same seed). Each value is the mean over sampling seeds 100–109.

| Model | Features |
|---|---|
| A | log(1 + N_K) |
| B | A + `token_std` |
| C | A + six structural features (reciprocity, largest-WCC fraction, in- and out-degree Gini, median and max coreness) |
| D | C + `token_std` |

**Estimands.**
- Log loss and AUC come from log-loss-tuned fits; BA comes from BA-tuned fits.
- Δ = first model − second model on identical events and folds.
- Negative Δ log loss favours the first model; positive ΔAUC and ΔBA favour it.

**Status.** Every contrast involving B or D (`token_std`) is **Exploratory-post-hoc**. C − A is part of the original exploratory Study 2.

## Sources

| Code | Artifact | Script | Content |
|---|---|---|---|
| S2 | `outputs/run_v2/study2/results.json` | `src/study2_observation.py` | A ("NK") and C ("NK_struct6") on both cohorts. C − A ("structure_beyond_NK"): BA and log loss, 1,000-resample event bootstrap (seed 7), uncorrected p, **no AUC contrast, no Holm** |
| V2 | `research_audit/outputs/v02_performance.csv`, `v02_contrasts.csv`, `v02_results.json` | `research_audit/scripts/v02_view_lensd_experiment.py` | A–D on **budget-specific cohorts only**. B − A and D − C: log loss, AUC and BA, 1,000-resample event bootstrap (seed 7), Holm across the three K per contrast and metric. Primary analysis on partition 42, with a 10-partition sensitivity analysis |
| D2 | `research_audit/final_diagnostics/outputs/d02_*` | `final_diagnostics/scripts/d02_exclude_undefined_events.py` | B − A and D − C with the two no-text events excluded (sensitivity) |

**Validation.** V2's A and C predictions equal S2's stored predictions exactly (max |diff| 0.0, `v02.log`).

## Cohorts

| Cohort | K = 250 | K = 500 | K = 1000 |
|---|---|---|---|
| Budget-specific (events with ≥ K edges) | 102 (51 campaign / 51 comparison) | 98 (48 / 50) | 73 (28 / 45) |
| Common (eligible at every K) | 73 (28 / 45) | 73 (28 / 45) | 73 (28 / 45) |

**The common cohort is identical to the K = 1000 budget-specific cohort.**
- The stored S2 predictions for the two cohorts at K = 1000 are identical (max |diff| 0.0, checked while preparing this file).
- S2's `budget_specific_K1000` and `common_K1000` entries are equal.
- V2 ran B and D on exactly these 73 events, with the same folds, seeds and code path. Its K = 1000 values therefore apply to the common cohort at K = 1000. They are not separately stored under a "common" label.

## Table 1. Model performance, KK, partition 42

**Budget-specific cohorts** (source: V2 `v02_performance.csv`)

| K | Model | Log loss [seed range] | AUC [seed range] | BA [seed range] |
|---|---|---|---|---|
| 250 | A | 0.279 [0.268, 0.295] | 0.961 [0.955, 0.967] | 0.922 [0.882, 0.941] |
| 250 | B | 0.243 [0.223, 0.258] | 0.959 [0.955, 0.962] | 0.950 [0.941, 0.951] |
| 250 | C | 0.273 [0.240, 0.298] | 0.946 [0.937, 0.955] | 0.914 [0.902, 0.931] |
| 250 | D | 0.226 [0.196, 0.263] | 0.957 [0.934, 0.972] | 0.933 [0.912, 0.941] |
| 500 | A | 0.315 [0.308, 0.322] | 0.952 [0.949, 0.958] | 0.880 [0.845, 0.896] |
| 500 | B | 0.246 [0.237, 0.267] | 0.954 [0.951, 0.955] | 0.949 [0.938, 0.958] |
| 500 | C | 0.328 [0.287, 0.378] | 0.944 [0.930, 0.957] | 0.905 [0.887, 0.928] |
| 500 | D | 0.237 [0.215, 0.262] | 0.955 [0.939, 0.965] | 0.942 [0.928, 0.958] |
| 1000 | A | 0.382 [0.377, 0.385] | 0.890 [0.886, 0.894] | 0.851 [0.839, 0.857] |
| 1000 | B | 0.268 [0.251, 0.292] | 0.955 [0.952, 0.956] | 0.942 [0.917, 0.964] |
| 1000 | C | 0.423 [0.401, 0.447] | 0.899 [0.887, 0.909] | 0.885 [0.860, 0.906] |
| 1000 | D | 0.285 [0.272, 0.307] | 0.944 [0.939, 0.949] | 0.917 [0.888, 0.946] |

**Common cohort, 73 events** (source: S2 `common_K*`; seed ranges for log loss and AUC are not stored)

| K | Model | Log loss | AUC | BA [seed range] |
|---|---|---|---|---|
| 250 | A | 0.292 | 0.952 | 0.932 [0.913, 0.946] |
| 250 | B | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED |
| 250 | C | 0.341 | 0.934 | 0.913 [0.900, 0.929] |
| 250 | D | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED |
| 500 | A | 0.338 | 0.939 | 0.868 [0.857, 0.882] |
| 500 | B | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED |
| 500 | C | 0.345 | 0.930 | 0.902 [0.884, 0.917] |
| 500 | D | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED |
| 1000 | A–D | = budget-specific K = 1000 rows above (identical cohort) | | |

FF references for A–D on full graphs of the same events exist in `v02_performance.csv` for the budget-specific cohorts. They are not repeated here.

## Table 2. Paired contrasts, KK, partition 42

Each cell gives Δ [95% event-bootstrap interval], then p. The p is Holm-adjusted across K wherever a "Holm" value exists. Otherwise it is the uncorrected bootstrap p, marked "unc.".

### Budget-specific cohorts

| K | Contrast | Δ log loss | ΔAUC | ΔBA | Source |
|---|---|---|---|---|---|
| 250 | B − A | −0.036 [−0.112, +0.038]; Holm 0.35 | −0.002 [−0.034, +0.025]; Holm 1.00 | +0.028 [−0.007, +0.066]; Holm 0.15 | V2 |
| 250 | D − C | −0.047 [−0.134, +0.037]; Holm 0.27 | +0.011 [−0.020, +0.046]; Holm 1.00 | +0.020 [−0.008, +0.047]; Holm 0.30 | V2 |
| 250 | C − A | −0.006 [−0.079, +0.062]; unc. 0.91 | NOT COMPUTED | −0.008 [−0.033, +0.019]; unc. 0.52 | S2 |
| 250 | D − B | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED | — |
| 500 | B − A | −0.068 [−0.163, +0.018]; Holm 0.27 | +0.002 [−0.037, +0.038]; Holm 1.00 | +0.070 [+0.020, +0.127]; Holm < 0.003 | V2 |
| 500 | D − C | −0.091 [−0.184, −0.001]; Holm 0.096 | +0.011 [−0.026, +0.050]; Holm 1.00 | +0.037 [+0.003, +0.075]; Holm 0.12 | V2 |
| 500 | C − A | +0.013 [−0.049, +0.088]; unc. 0.77 | NOT COMPUTED | +0.026 [−0.013, +0.076]; unc. 0.26 | S2 |
| 500 | D − B | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED | — |
| 1000 | B − A | −0.114 [−0.218, −0.011]; Holm 0.084 | +0.065 [+0.010, +0.144]; Holm 0.072 | +0.091 [+0.010, +0.176]; Holm 0.056 | V2 |
| 1000 | D − C | −0.138 [−0.208, −0.076]; Holm < 0.003 | +0.045 [+0.002, +0.111]; Holm 0.066 | +0.031 [−0.010, +0.086]; Holm 0.30 | V2 |
| 1000 | C − A | +0.041 [−0.033, +0.129]; unc. 0.29 | NOT COMPUTED | +0.034 [−0.046, +0.113]; unc. 0.40 | S2 |
| 1000 | D − B | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED | — |

How to read the Holm values:
- "Holm < 0.003" means a bootstrap p of 0 out of 1,000 resamples, multiplied by 3. `v02_contrasts.csv` prints it as 0.000.
- Holm adjusts only across the three K within each contrast and metric. It does not adjust for the post-hoc selection of `token_std`.

### Common cohort

| K | Contrast | Δ log loss | ΔAUC | ΔBA | Source |
|---|---|---|---|---|---|
| 250 | B − A | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED | — |
| 250 | D − C | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED | — |
| 250 | C − A | +0.049 [−0.015, +0.137]; unc. 0.22 | NOT COMPUTED | −0.019 [−0.060, +0.007]; unc. 0.25 | S2 |
| 250 | D − B | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED | — |
| 500 | B − A | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED | — |
| 500 | D − C | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED | — |
| 500 | C − A | +0.007 [−0.047, +0.064]; unc. 0.80 | NOT COMPUTED | +0.034 [−0.044, +0.111]; unc. 0.42 | S2 |
| 500 | D − B | NOT COMPUTED | NOT COMPUTED | NOT COMPUTED | — |
| 1000 | all | = budget-specific K = 1000 rows (identical cohort, folds and seeds) | | | V2 / S2 |

### Related existing contrast (not D − C)

The manuscript's "content beyond N_K + structure" is "combined" − "NK_struct6": C plus **three** content features (duplicate fraction, frequency Gini and `token_std`) minus C. Source: S2, uncorrected.

| K | Budget-specific Δ log loss | Budget-specific ΔBA | Common Δ log loss | Common ΔBA |
|---|---|---|---|---|
| 250 | −0.067 [−0.145, +0.005]; unc. 0.058 | +0.020 [−0.010, +0.049] | −0.072 [−0.159, +0.002]; unc. 0.056 | +0.023 [−0.006, +0.064] |
| 500 | −0.127 [−0.226, −0.036]; unc. < 0.001 | +0.029 [−0.003, +0.062] | −0.098 [−0.163, −0.040]; unc. < 0.001 | +0.039 [+0.006, +0.086] |
| 1000 | −0.173 [−0.247, −0.105]; unc. < 0.001 | +0.030 [−0.013, +0.084] | (= budget-specific) | (= budget-specific) |

### Sensitivity results that exist for B − A and D − C (budget-specific only)

- **10 outer partitions** (`v02_contrasts.csv`, "sensitivity"). Δ log loss:

  | K | B − A | D − C |
  |---|---|---|
  | 250 | −0.041 [−0.114, +0.031] | −0.060 [−0.131, +0.009] |
  | 500 | −0.065 [−0.155, +0.019] | −0.062 [−0.134, +0.006] |
  | 1000 | −0.102 [−0.204, +0.004] | −0.129 [−0.204, −0.050], Holm 0.006 |

  The partitions reuse the same events, so they are not replications.
- **Two no-text events excluded** (D2, partition 42). Δ log loss:

  | K | B − A | D − C |
  |---|---|---|
  | 250 | −0.039 | −0.053 |
  | 500 | −0.070 | −0.063 |
  | 1000 | −0.108 [−0.215, +0.004] | −0.124 [−0.215, −0.037], Holm 0.018 |

## Answers from existing data

### (a) Is the K = 1000 D − C gain larger than B − A, and is C's own log loss unusually poor?

- **Point estimates.** D − C (−0.138) is 0.024 larger in magnitude than B − A (−0.114), and the intervals overlap almost entirely.
- **Not tested.** No contrast between the two gains, and no D − B, was computed. The data cannot say that adding `token_std` helps more on top of structure.
- **C is poor in log loss at K = 1000.** It has the worst mean log loss of the four models: 0.423, against 0.382 for A, 0.268 for B and 0.285 for D. Its seed range (0.401–0.447) lies entirely above A's (0.377–0.385). Yet C ranks slightly better than A (AUC 0.899 vs 0.890), so adding the six structural features to N_K worsens calibration at this budget. C − A is +0.041 [−0.033, +0.129], uncorrected, with an interval that includes zero.
- **The same pattern on full graphs.** In FF, C has log loss 0.437 against 0.262 for A (`v02_performance.csv`).
- **Consequence.** D − C is measured against a baseline with inflated log loss.
  - D's mean log loss (0.285) is *higher* than B's (0.268). This compares two existing point estimates; it is not a computed contrast.
  - The larger D − C therefore cannot be read as `token_std` being more useful alongside structure.
  - The single Holm-surviving log-loss result (D − C at K = 1000) partly reflects a weak comparator.

### (b) Is there a budget pattern on the common cohort, or could the cohort change explain it?

- **For B − A and D − C: undetermined.**
  - They exist only on budget-specific cohorts, whose composition changes with K: 102 events (51/51), then 98 (48/50), then 73 (28/45).
  - On the common cohort they exist only at K = 1000, where it coincides with the budget-specific cohort. They are NOT COMPUTED at K = 250 and 500.
  - The budget-specific growth in magnitude (B − A: −0.036, −0.068, −0.114) therefore cannot be separated from the change of cohort.
- **What the common cohort does show, for the models that exist there.**
  - On the same 73 events, A gets worse as K grows: log loss 0.292, 0.338, 0.382; AUC 0.952, 0.939, 0.890; BA 0.932, 0.868, 0.851.
  - C's log loss also rises (0.341, 0.345, 0.423).
  - The related three-feature content contrast grows in magnitude on fixed events (−0.072, −0.098, −0.173, uncorrected, with overlapping intervals).
- **Interpretation.**
  - A budget pattern exists on fixed events for the related contrast. But it coincides with the count-only baseline weakening as K grows.
  - `token_std`'s own class separation is roughly constant across K: univariate view AUC 0.78, 0.77 and 0.81 on the budget-specific cohorts (`v02_results.json`). This is consistent with, but does not demonstrate, a shrinking baseline rather than a growing `token_std` contribution.
  - No trend test exists. With three budgets, none would be informative.

### (c) Which claims about budget dependence cannot be supported?

1. "The added value of `token_std` increases with the budget, or with observation depth." There are no common-cohort B and D values below K = 1000, K is confounded with cohort, the intervals overlap and no trend was tested.
2. "`token_std` adds nothing at K = 250 (or 500)." Non-significance is not evidence of no effect, and the log-loss direction favours B and D in 10 of 10 seeds at every K.
3. "Adding `token_std` helps more beyond structure than beyond N_K." The difference was not tested, D − B was not computed and the comparator C has poor log loss.
4. "Sampling erodes, or does not erode, the `token_std` signal." The FF contrasts on the same events are similarly uncertain (`v02_contrasts.csv`, FF rows), and no view-versus-full contrast for B or D was computed.
5. Any reading of "significant at K = 1000, not at K = 250" as a budget effect. A difference in significance is not a significant difference.
6. Any budget-dependence claim for Study 2 contrasts generally that rests on budget-specific cohorts only. Where common-cohort values exist (A, C and the S2 contrasts), they should be cited instead, and B and D marked as unavailable there.
