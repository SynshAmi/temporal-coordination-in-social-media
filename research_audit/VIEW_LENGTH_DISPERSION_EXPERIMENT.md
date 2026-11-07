# Message-Length Dispersion Under Fixed-Budget Observation

Date: 2026-11-05. The final planned experiment of the LEN-Small project. It is a robustness
investigation, not an independent confirmatory test: message-length dispersion was singled out
after the full-graph results were examined (`FINAL_ROBUSTNESS_AND_CONTRIBUTION_ASSESSMENT.md`,
Part II C). Nothing outside `research_audit/` was modified. Existing Study 1 and Study 2 results
are unchanged.

## 1. Research question

In fixed-K edge samples, does message-length dispersion, computed from the sampled edges only, add
predictive value:
- beyond the sampled endpoint count N_K, a size proxy (model B vs model A); and
- beyond N_K plus the evaluated structural features (model D vs model C)?

## 2. Data and cohorts

- **Views.** The existing Study 2 views, `data/processed/sampled_views_v2.parquet`: 10 views per
  eligible event (sampling seeds 100–109), each made of K edges drawn uniformly without replacement.
  No new samples were drawn.
- **Cohorts.** The existing budget-specific cohorts, meaning all events with at least K edges:

  | K | Events | Campaign / comparison | Views |
  |---|---|---|---|
  | 250 | 102 | 51 / 51 | 1,020 |
  | 500 | 98 | 48 / 50 | 980 |
  | 1000 | 73 | 28 / 45 | 730 |

- **Cohort changes with K.** The K = 1000 cohort is a subset of larger events and is imbalanced.
  Differences between budgets therefore mix observation depth with cohort composition.
- **Is the text in the views? Yes, verified** (`v01_view_text_availability.py`).
  - Each view's edges keep their `text` attribute, and the stored view features were computed from
    the sampled edges only (`src/sample_views.py` → `features.compute_features_for_sampled_view`).
  - Re-running the original sampler reproduces all 2,730 views. The regenerated N_K and an
    independently written message-length dispersion both match the stored values exactly (max
    |difference| 0.0, identical missing-value pattern).

## 3. Feature construction and missingness

**Definition.** Unchanged from Study 1: `features.extract_content_features`, the same function used
for full graphs.

| Question | Answer |
|---|---|
| Which messages are used? | The texts of the K sampled edges. Each sampled edge contributes its message once. |
| Repeated messages? | Counted repeatedly. Identical texts on different sampled edges each count. |
| Missing texts? | Null texts are dropped. Texts empty after cleaning are dropped. Cleaning: lower-case, URLs removed, whitespace collapsed, stripped. |
| Calculation | Sample SD (ddof 1) of whitespace token counts of the remaining texts. 0 if one text remains; undefined (NaN) if none. |
| Undefined values in models | Median-imputed by the pipeline, fitted on the training fold only. |

**Text availability is not random** (`v01_view_text.json`, Fig. 1). Share of the K sampled edges
with usable text:

| K | Campaign views: mean (median) | Comparison views: mean (median) | Campaign views with feature undefined | Comparison views with feature undefined | Campaign views with < 25% usable text | Comparison views with < 25% usable text |
|---|---|---|---|---|---|---|
| 250 | 0.57 (0.63) | 0.80 (0.83) | 20 of 510 | 0 of 510 | 142 | 1 |
| 500 | 0.57 (0.63) | 0.80 (0.82) | 20 of 480 | 0 of 500 | 144 | 0 |
| 1000 | 0.54 (0.53) | 0.79 (0.81) | 10 of 280 | 0 of 450 | 92 | 0 |

- **Where undefined values come from:** only the two campaign events with no text in the archive
  (one of them at K = 1000).
- **Very few texts:** a further 10 (K = 250), 9 (K = 500) and 0 (K = 1000) campaign views have
  1–9 usable texts. Every comparison view has at least 10.
- **Consequence:** campaign views estimate the feature from fewer messages. Missingness is itself
  associated with the label. This experiment does not model it, by design (no new features).

**Does sampling preserve the feature?** (`v02_results.json`, `descriptive_lensd`; Fig. 3) Yes.

| K | Spearman ρ: event-mean view value vs full-graph value | Median within-event SD across the 10 views (tokens) | Single-view AUC* | Full-graph AUC* (same events) |
|---|---|---|---|---|
| 250 | 0.995 | 0.37 | 0.78 | 0.78 |
| 500 | 0.999 | 0.22 | 0.77 | 0.77 |
| 1000 | 0.999 | 0.14 | 0.81 | 0.81 |

\*Univariate AUC of the feature for the comparison class (higher dispersion indicates comparison).

The SD of message length is an average-type statistic. Unlike size measures such as N_K, it does
not depend systematically on how many edges are seen.

## 4. Evaluation methodology

The existing Study 2 framework is reused unchanged (`src/study2_observation.py`).

**Training and test regime.**
- **Regime (KK):** for each sampling seed separately, logistic regression is trained on that seed's
  views of the training-fold events and scores that seed's views of the test-fold events.
- **Folds:** the full-cohort event folds (`make_event_folds`, seed 42) restricted to the cohort.
- **No leakage across views:** all views of an event sit in that event's fold, so no event
  contributes to both training and evaluation.
- **Same splits everywhere:** models A–D share the same events, folds and views.

**Fitting.**
- **C tuning:** C is tuned by inner 3-fold CV over {0.01, 0.1, 1, 10} (`train.tune_logreg_C`).
- **Pipeline:** median imputation → standardisation → balanced logistic regression
  (`train.make_logreg_pipeline`).
- **No evaluation data in fitting:** all transformations are fitted on the training fold only.

**Estimands and uncertainty.**
- **Estimand:** single-view performance, computed per sampling seed and averaged over the 10 seeds.
- **Metrics:** log loss and AUC from log-loss-tuned fits; balanced accuracy (BA) from BA-tuned fits.
- **Uncertainty:** an event-level paired bootstrap (1,000 resamples, seed 7, as configured for Study 2).
  - Events are resampled, and all 10 views of a resampled event go with it.
  - Views are never treated as independent events.

**Models.**

| Model | Features |
|---|---|
| A | log(1 + N_K) |
| B | A + message-length dispersion |
| C | A + six structural features (Study 2 "NK_struct6": reciprocity, largest WCC fraction, in/out-degree Gini, median/max coreness) |
| D | C + message-length dispersion |

**Multiplicity.** Holm correction is applied across the three budgets, separately for each contrast
(B − A, D − C) and each metric.

**Validation.** Models A and C reproduce the stored Study 2 predictions of "NK" and "NK_struct6"
exactly (max |difference| 0.0), for both objectives and both the KK and FF conditions.

**Reference condition (FF).**
- **What it is:** the same four models fitted to the full graphs of the same cohort, with the same
  folds. N_K is replaced by full-graph log node count, and the view feature by its full-graph value.
- **Why:** it shows whether any gain is weaker in views than with complete observation, on
  identical events.

**Documented framework limitations.**
1. **Single outer partition.** The framework uses one outer partition. Study 1 showed partition
   variability comparable to event uncertainty. As a labelled sensitivity, the analysis was
   repeated over the paper's 10 Study 1 split seeds (100 partition × seed fits per model). No other
   part of the method changed.
2. **Conditional intervals.** Bootstrap intervals are conditional on the fitted out-of-fold
   predictions; they exclude refitting variability.

## 5. Results for each K

Single-view performance under the KK regime: mean over 10 seeds (seed range).
FF = full-graph reference on the same events.

| K | Model | Log loss | AUC | BA | FF log loss | FF AUC | FF BA |
|---|---|---|---|---|---|---|---|
| 250 | A: N_K | 0.279 (0.268–0.295) | 0.961 | 0.922 | 0.331 | 0.931 | 0.873 |
| 250 | B: N_K + lensd | 0.243 (0.223–0.258) | 0.959 | 0.950 | 0.271 | 0.957 | 0.902 |
| 250 | C: N_K + structure | 0.273 (0.240–0.298) | 0.946 | 0.914 | 0.363 | 0.930 | 0.863 |
| 250 | D: N_K + structure + lensd | 0.226 (0.196–0.263) | 0.957 | 0.933 | 0.263 | 0.956 | 0.922 |
| 500 | A | 0.315 (0.308–0.322) | 0.952 | 0.880 | 0.337 | 0.930 | 0.888 |
| 500 | B | 0.246 (0.237–0.267) | 0.954 | 0.949 | 0.273 | 0.957 | 0.908 |
| 500 | C | 0.328 (0.287–0.378) | 0.944 | 0.905 | 0.395 | 0.927 | 0.878 |
| 500 | D | 0.237 (0.215–0.262) | 0.955 | 0.942 | 0.224 | 0.965 | 0.907 |
| 1000 | A | 0.382 (0.377–0.385) | 0.890 | 0.851 | 0.262 | 0.952 | 0.855 |
| 1000 | B | 0.268 (0.251–0.292) | 0.955 | 0.942 | 0.227 | 0.967 | 0.938 |
| 1000 | C | 0.423 (0.401–0.447) | 0.899 | 0.885 | 0.437 | 0.925 | 0.869 |
| 1000 | D | 0.285 (0.272–0.307) | 0.944 | 0.917 | 0.340 | 0.949 | 0.895 |

Full table with seed ranges for every metric: `outputs/v02_performance.csv`.

## 6. Paired comparisons and uncertainty

**Primary analysis** (partition 42; 95% event bootstrap; Holm p across K in parentheses; "p < 0.003"
means no bootstrap resample crossed zero):

| K | Contrast | Δ log loss | ΔAUC | ΔBA | Seeds favouring lensd (log loss / AUC / BA) | Events with lower loss |
|---|---|---|---|---|---|---|
| 250 | B − A | −0.036 [−0.112, +0.038] (0.35) | −0.002 [−0.034, +0.025] (1.0) | +0.028 [−0.007, +0.066] (0.15) | 10 / 3 / 10 of 10 | 50 / 102 |
| 250 | D − C | −0.047 [−0.134, +0.037] (0.27) | +0.011 [−0.020, +0.046] (1.0) | +0.020 [−0.008, +0.047] (0.30) | 10 / 8 / 8 | 59 / 102 |
| 500 | B − A | −0.068 [−0.163, +0.018] (0.27) | +0.002 [−0.037, +0.038] (1.0) | **+0.070 [+0.020, +0.127] (< 0.003)** | 10 / 8 / 10 | 54 / 98 |
| 500 | D − C | −0.091 [−0.184, −0.001] (0.096) | +0.011 [−0.026, +0.050] (1.0) | +0.037 [+0.003, +0.075] (0.12) | 10 / 9 / 10 | 60 / 98 |
| 1000 | B − A | −0.114 [−0.218, −0.011] (0.084) | +0.065 [+0.010, +0.144] (0.072) | +0.091 [+0.010, +0.176] (0.056) | 10 / 10 / 10 | 47 / 73 |
| 1000 | D − C | **−0.138 [−0.208, −0.076] (< 0.003)** | +0.045 [+0.002, +0.111] (0.066) | +0.031 [−0.010, +0.086] (0.30) | 10 / 10 / 10 | 56 / 73 |

**Sensitivity: 10 outer partitions** (all views from all 10 partitions; event bootstrap):

| K | Contrast | Δ log loss | ΔAUC | ΔBA | Partitions favouring lensd (log loss / AUC) |
|---|---|---|---|---|---|
| 250 | B − A | −0.041 [−0.114, +0.031] | −0.000 [−0.031, +0.026] | +0.026 [−0.009, +0.063] | 10 / 4 of 10 |
| 250 | D − C | −0.060 [−0.131, +0.009] | +0.017 [−0.008, +0.049] | +0.018 [−0.009, +0.043] | 10 / 10 |
| 500 | B − A | −0.065 [−0.155, +0.019] | +0.001 [−0.038, +0.036] | +0.064 [+0.016, +0.112] | 10 / 5 |
| 500 | D − C | −0.062 [−0.134, +0.006] | +0.012 [−0.019, +0.046] | +0.035 [−0.001, +0.073] | 9 / 9 |
| 1000 | B − A | −0.102 [−0.204, +0.004] | +0.063 [+0.007, +0.138] | +0.085 [+0.015, +0.164] | 10 / 10 |
| 1000 | D − C | −0.129 [−0.204, −0.050] (Holm 0.006) | +0.040 [−0.007, +0.106] | +0.039 [−0.001, +0.090] | 10 / 10 |

**Full-graph reference** (FF, the same events and folds, partition 42):

| K cohort | Contrast | Δ log loss | ΔAUC | ΔBA |
|---|---|---|---|---|
| 250 | B − A | −0.060 [−0.125, +0.015] | +0.025 [−0.005, +0.058] | +0.029 [−0.033, +0.098] |
| 250 | D − C | −0.100 [−0.194, −0.010] | +0.025 [−0.012, +0.069] | +0.059 [−0.012, +0.135] |
| 500 | B − A | −0.063 [−0.150, +0.024] | +0.027 [−0.008, +0.067] | +0.021 [−0.044, +0.091] |
| 500 | D − C | −0.171 [−0.320, −0.053] | +0.038 [+0.001, +0.085] | +0.029 [−0.036, +0.098] |
| 1000 | B − A | −0.035 [−0.127, +0.065] | +0.015 [−0.026, +0.063] | +0.083 [+0.017, +0.165] |
| 1000 | D − C | −0.097 [−0.179, −0.021] | +0.024 [−0.006, +0.070] | +0.027 [−0.072, +0.116] |

**Reading the results.**

1. **Consistent direction, uncertain size.**
   - In log loss, adding the feature helps at every budget, for both contrasts, in every one of the
     10 sampling seeds, and in ≥ 94 of 100 partition × seed fits.
   - The 95% interval excludes zero only at K = 1000 for both contrasts, and at K = 500 for D − C
     (barely).
   - After Holm correction across budgets, only D − C at K = 1000 remains clearly below 0.05.
   - At K = 250 no contrast is distinguishable from zero in any metric.
2. **No ranking gain except at K = 1000.**
   - At K = 250 and 500, N_K alone already ranks views at AUC 0.95–0.96. Adding the feature leaves
     AUC unchanged (ΔAUC between −0.002 and +0.011).
   - At K = 1000, where N_K ranks worse (AUC 0.89), the feature adds +0.065 (B − A) and +0.045 (D − C).
3. **BA gains are threshold-dependent.**
   - The largest Holm-surviving BA effect (B − A, K = 500, +0.070) comes with no AUC change, so it
     reflects decision placement, not better ranking.
4. **The gain is narrow across events.** Only about half the events have lower loss with the
   feature (50 of 102 at K = 250 for B − A). The mean gain is concentrated, as it was in full graphs.
5. **No sign that sampling erodes the signal.**
   - On identical events, the full-graph reference gains are of similar size and similar
     uncertainty: at K = 250, FF B − A is −0.060 [−0.125, +0.015].
   - So the inconclusive result at the smaller budgets reflects how uncertain the feature's
     contribution is in this archive, not a loss caused by sampling.
6. **Budget is confounded with cohort.** The budgets cannot be read as a trend in observation
   depth. The K = 1000 cohort holds larger events, with fewer campaigns, where the N_K baseline is
   weaker. That is a different population and a different baseline, not only more observed edges.

## 7. Limitations

- **Post hoc selection.** The feature was chosen after inspecting full-graph results on the same
  events. Views are subsamples of those events, so this is not independent evidence.
- **One archive.** 103 events from one archive whose relation to the published LEN-Small is
  undefined. There is no generalisation beyond it.
- **Unequal text availability.**
  - Campaign views have about 23 percentage points less usable text; two campaign events have none,
    and their undefined values are median-imputed.
  - Missingness is associated with the label and is not modelled here. Study 1 found that text
    availability added nothing beyond counts and did not explain the full-graph content effect.
    That check was not repeated for views.
- **Budget–cohort confounding.** The three budgets use nested but different cohorts; K = 1000 is
  small and imbalanced (28 / 45).
- **Interval scope.** Intervals are conditional on fitted out-of-fold predictions. The primary
  analysis uses one outer partition; the 10-partition sensitivity gives similar conclusions.
- **Bootstrap resolution.** With 1,000 bootstrap resamples, p-values below about 0.002 cannot be
  resolved.
- **One sampling model.** Uniform edge sampling is one observation model among many.
- **Not a test of information.** These are classifier comparisons, not information-theoretic
  measurements. A null contrast does not show that a feature carries no information, and the
  structural result concerns only the six structural features evaluated.

## 8. Conclusion — what this changes in the paper

**Outcome: mixed, leaning inconclusive at small budgets.**
- **The measurement survives restricted observation.** Message-length dispersion computed from a
  single K-edge view almost exactly tracks its full-graph value and keeps the same univariate class
  separation.
- **Its incremental predictive value is consistent in direction but not established throughout.**
  It lowers log loss at every budget, beyond N_K and beyond N_K plus structure. But the improvement
  is distinguishable from zero only at the largest budget, in a smaller cohort of larger events,
  and not at K = 250.
- **It adds no ranking improvement** where the endpoint-count proxy is already strong.
- **This is not evidence that sampling erodes the signal:** the full-graph reference on the same
  events is similarly uncertain.

**What this changes.**
1. The paper may say the content *measurement* is robust to fixed-budget observation.
2. It may not say that content generally adds predictive value under partial observation.
3. Its Study 2 statement that content "added at most a few points of BA, with intervals that
   include zero" should be refined:
   - the single length-dispersion feature improves view log loss in direction at all budgets;
   - it is distinguishable from zero only at K = 1000;
   - its BA gains are threshold-dependent.
4. None of the existing Study 1 or Study 2 claims is overturned.

**Recommended wording.**

> *Results:* "In fixed-budget views, the message-length dispersion of the sampled messages closely
> tracked its full-graph value (Spearman ρ ≥ 0.995 at every budget) and retained its univariate
> class separation. Adding it to the sampled endpoint count, or to the endpoint count and the six
> structural features, lowered single-view log loss at every budget and in every sampling seed, but
> the improvement was distinguishable from zero only at K = 1000 (73 events; endpoint count and
> structure: −0.138 [−0.208, −0.076], Holm-adjusted across budgets), not at K = 250 (−0.047
> [−0.134, +0.037]). It did not improve ranking where the endpoint count already ranked views well
> (ΔAUC ≤ 0.011 at K = 250 and 500). On the same events, full-graph versions of these comparisons
> were similarly uncertain, so we find no evidence that sampling removes this signal, and no
> conclusive evidence that it adds to prediction at small budgets."

> *Limitations:* "Message-length dispersion was identified after inspecting the full-graph results on
> the same events, so its evaluation under sampling is a robustness check, not a confirmation.
> Campaign views contained less usable text than comparison views, and budgets differ in their
> cohorts as well as in the number of observed edges."

---

### Files and reproduction

**Created:**

| Type | Files |
|---|---|
| Scripts | `research_audit/scripts/v01_view_text_availability.py`, `research_audit/scripts/v02_view_lensd_experiment.py` (uses `s00_engine.py` for metric and bootstrap helpers, and `src/train.py`, `src/splits.py` unchanged) |
| Outputs: text availability | `research_audit/outputs/v01_view_text.csv`, `v01_view_text.json`, `v01.log` |
| Outputs: experiment | `research_audit/outputs/v02_performance.csv`, `v02_contrasts.csv`, `v02_results.json`, `v02_predictions.npz`, `v02.log` |
| Figures | `v02_fig1_text_availability.png` (+ `v02_fig1_data.csv`), `v02_fig2_contrasts.png` (+ `v02_fig2_data.csv`), `v02_fig3_view_vs_full.png` |
| This report | `research_audit/VIEW_LENGTH_DISPERSION_EXPERIMENT.md` |

**Commands** (from the project root; Python 3.12 environment of the project; v02 reads v01's output):

```
python research_audit/scripts/v01_view_text_availability.py
python research_audit/scripts/v02_view_lensd_experiment.py
```

Runtime is about 1 minute for v01 and about 2.5 minutes for v02, the latter parallel on 16 cores.
