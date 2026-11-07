# Author decisions: five reporting points

This file is based only on existing artifacts; nothing was run, refitted or changed. Claim IDs refer to `claim_ledger.md`.

**Conventions.**
- Δ = first model − second model on identical events. Negative Δ log loss favours the first model.
- **FPB** = event-level paired bootstrap of fixed out-of-fold predictions.
- Log loss and AUC come from log-loss-tuned fits; BA comes from BA-tuned fits.
- Study 1: 103 events (52 campaign / 51 comparison), logistic regression.

---

## 1. C1 uncertainty: −0.110 (primary split) vs −0.094 (20-split average)

### Artifacts and exact results

| Quantity | Value | Artifact |
|---|---|---|
| C1 = M4 − M0q, primary partition (seed 42) | Δ log loss −0.110 [−0.181, −0.039]; Holm p 0.009 over the 3 pre-specified log-loss tests; FPB with 2,000 resamples | `outputs/run_v2/paper_results.json` → `paper/generated/results.tex` (`\RCOneLLGain`, `\RCOneLLCI`, `\RCOneLLHolm`) |
| Same predictions, re-bootstrapped by the audit engine | −0.110 [−0.184, −0.039]; 80/103 events improved | `research_audit/outputs/s02_results.json` (`primary_split_C1`) |
| C1 averaged over 20 partitions (seeds 42 and 1–19) | −0.094 [−0.172, −0.013]; p 0.024; Holm p 0.120 over a 7-contrast family assembled in the robustness phase; 82/103 events improved | `research_audit/outputs/s02_contrasts.csv`, row "C1: M4 - M0q", subset "all" |
| Per-partition spread (20) | −0.122 to +0.028; 19/20 favour M4; partition SD 0.035 against an event-bootstrap SD of 0.040 | `s02_contrasts.csv`; `FINAL_ROBUSTNESS_AND_CONTRIBUTION_ASSESSMENT.md` Part II B |
| Rank of the primary partition | 8th of 20; median per-partition C1 −0.103 | same report, Part II |
| The paper's 10 partitions | −0.122 to +0.028, median −0.103, 9/10 negative | `outputs/revision_supplement/supplement.json`; `outputs/run_v2/study1/repeated_splits_lr.csv` |
| Bootstrap intervals for the same predictions | Upper limit −0.039 in both; lower limit −0.181 vs −0.184 | Two bootstrap implementations (paper vs audit). Do not mix them in the paper; use the paper's value for the primary result |

**How the two numbers relate.** They are different estimands of the same contrast:
- **−0.110** is the pre-specified analysis on one partition. Its interval covers event resampling only.
- **−0.094** is the mean over 20 partitions of the same events. Its interval covers event resampling of repeat-averaged predictions.

Partition variability (SD 0.035) is about as large as the event uncertainty, so the single-partition interval omits a source of variation of comparable size. The primary partition is typical (8th of 20), not cherry-picked. The 20-partition mean is lower mainly because of two partitions (seeds 3 and 7).

### Decision

- **Principal result: −0.110 [−0.181, −0.039], Holm p 0.009.** It was specified before the corrected run, with a stated three-test family. Replacing it with a quantity chosen afterwards would weaken the pre-specification.
- **Report −0.094 [−0.172, −0.013] next to it, in the same paragraph, as a sensitivity analysis.** Name its adjustment: unadjusted p 0.024. The Holm p of 0.12 belongs to a family built after the fact; give it only with that family named, or leave it out of the main text.

**We can claim:**
- M4 had lower out-of-fold log loss than the count model on the pre-specified partition.
- The direction was the same in 19 of 20 partitions of the same events.
- The magnitude averaged over partitions was −0.094.

**We must avoid:**
- Presenting either number alone.
- Calling the 20 partitions replications.
- Reporting −0.094 with "Holm p 0.12" and no family named.
- Using the audit bootstrap's [−0.184, −0.039] in the paper.

**Wording.**
> "On the pre-specified partition, adding degree, arrangement and content features to the count model changed log loss by −0.110 [−0.181, −0.039] (Holm-adjusted p = 0.009 across the three primary log-loss contrasts). Because this interval does not include partition variability, we repeated the analysis over 20 outer partitions of the same events: the repeat-averaged difference was −0.094 [−0.172, −0.013] (unadjusted), and the direction was the same in 19 of the 20 partitions. The partitions reuse the same events and are not independent replications."

---

## 2. Structural contribution: beyond counts vs beyond counts and content

### Artifacts and exact results

**20-partition, repeat-averaged** (`research_audit/outputs/s02_contrasts.csv`; exploratory, unadjusted unless stated)

| Contrast | Δ log loss [95% FPB] | p | Partitions favouring the larger model (log loss) | ΔAUC [95%] |
|---|---|---|---|---|
| Structure beyond counts: M2 − M0q | +0.002 [−0.048, +0.053] | 0.97 | 9 / 20 | +0.002 [−0.021, +0.025] |
| Degree Gini beyond counts: M1 − M0q (E1) | +0.040 [+0.027, +0.053] (worse) | < 0.001 | 0 / 20 | −0.015 [−0.025, −0.007] |
| Arrangement beyond counts and degree Gini: M2 − M1 (C2) | −0.038 [−0.089, +0.016] | 0.15 | 20 / 20 | +0.017 [−0.008, +0.044] |
| Structure beyond counts and content: M4 − M3 (E2) | −0.059 [−0.110, −0.011] | 0.012 | 19 / 20 | +0.013 [−0.000, +0.027] |
| Arrangement beyond counts, content and degree Gini: M4 − (M3 + degree) | −0.009 [−0.070, +0.057] | 0.74 | 15 / 20 | — |
| Degree Gini beyond counts, content and arrangement: M4 − (M3 + arrangement) | −0.029 [−0.080, +0.006] | 0.13 | 18 / 20 | — |

**Primary partition** (`paper_results.json`)

| Contrast | Δ log loss | Adjustment |
|---|---|---|
| C2 (M2 − M1) | −0.008 [−0.079, +0.081] | Holm 1.000 |
| E2 (M4 − M3) | −0.091 [−0.182, −0.018] | uncorrected, exploratory |

M2 − M0q was not reported as a contrast on the primary partition. The table shows log loss 0.352 for M2 and 0.326 for M0q, with no interval.

**Where the statements conflict.**
- The robustness report says "graph topology contributes little or nothing detectable" and "structure as a whole adds nothing over counts". That is true of M2 − M0q.
- The same report and the manuscript also report E2, whose interval excludes zero.

Both statements are accurate for their own conditioning set. The conflict is a wording conflict: one phrase is applied to two different comparisons.

### What the evidence shows, by conditioning set

- **Given counts only:** adding the structural features gives no detectable change.
  - Degree Gini on its own worsens log loss in every partition.
  - Arrangement then roughly offsets that.
- **Given counts and content:** adding the structural features improves log loss.
  - Interval −0.110 to −0.011; 19 of 20 partitions.
  - Exploratory and unadjusted.
  - Neither degree Gini nor arrangement alone accounts for it: both single-family intervals include zero.

### Decision

**We can claim:**
- No detectable log-loss change from structure beyond counts.
- A log-loss improvement from structure beyond counts and content (exploratory).
- Degree Gini worsens log loss when added to counts.

**We must avoid:**
- "Topology contributes nothing", "contains no information" or "structure is uninformative".
- Treating "no detectable change beyond counts" as absence of information.
- Explaining E2 mechanistically ("interaction", "complementary information"). LR is additive, and the source of E2 is not isolated.
- Attributing E2 to one structural family.

**Wording.**
> "Added to the count model alone, the six structural features produced no detectable change in log loss (M2 − M0q: +0.002 [−0.048, +0.053]); degree concentration on its own worsened log loss in every partition (+0.040 [+0.027, +0.053]). Added to a model that already contained counts and content, the same features changed log loss by −0.059 [−0.110, −0.011] (exploratory, unadjusted; 19 of 20 partitions), an effect not attributable to either degree concentration or arrangement alone. These are predictive comparisons and do not show that graph structure is uninformative or informative about the labels in any causal sense."

If only primary-partition values are used in the main text, cite E2 as −0.091 [−0.182, −0.018] and note that M2 − M0q was not tested on that partition.

---

## 3. Excluding the two events without usable text

### Artifacts and exact results

`research_audit/outputs/s02_contrasts.csv`, subset `text101`: 101 events, 20 partitions, FPB, unadjusted.

| Contrast | All 103 events | Without the 2 events (101) | Partitions favouring M4 (log loss) |
|---|---|---|---|
| C1 (M4 − M0q), Δ log loss | −0.094 [−0.172, −0.013] | **−0.083 [−0.171, +0.008]**, p 0.076 | 19 → 18 of 20 |
| C1, ΔAUC | +0.034 [+0.006, +0.070] | +0.033 [+0.004, +0.069], p 0.023 | AUC: 20 → 20 |
| E3 (M4 − M2), Δ log loss | −0.096 [−0.165, −0.032] | −0.087 [−0.158, −0.015], p 0.021 | 19 → 19 |

Events improved in log loss: 80 of 101 (C1).

The conflicting statement is in `FINAL_ROBUSTNESS_AND_CONTRIBUTION_ASSESSMENT.md`: Part I says the improvement "survives … excluding the two events without text", while Part II C.3 gives the interval above, which includes zero.

The Study 2 exclusion (`final_diagnostics/outputs/d02_*`) is a separate analysis of B − A and D − C. Keep its numbers separate.

### Direction vs evidence

- **Consistency of direction:** the point estimate stays negative (−0.083), and 18 of 20 partitions favour M4.
- **Statistical evidence:** the log-loss interval now includes zero, so the log-loss improvement is not statistically supported in the 101-event analysis. The AUC improvement and E3 remain supported (both unadjusted).

The two events are a small share of the cohort, but they visibly affect the C1 log-loss interval. Why M4 handles these two events better was not isolated.

### Decision

**We can claim:**
- Without the two events, the C1 log-loss difference kept its direction (−0.083), with an interval that includes zero.
- The AUC difference and the content-beyond-structure contrast (E3) retained intervals excluding zero.

**We must avoid:**
- "Survives", "robust to" or "unchanged by" exclusion, for C1 log loss.
- Reading the wider interval as evidence that the gain depends on these events or disappears without them. Non-significance is not absence.

**Wording.**
> "Two campaign graphs contain no usable message text, so their content features were imputed with the training-fold median. Excluding them (101 events, 20 partitions), the C1 log-loss difference was −0.083 [−0.171, +0.008]: the same direction, but with an interval that includes zero. The AUC difference (+0.033 [+0.004, +0.069]) and the contrast for content beyond counts and structure (−0.087 [−0.158, −0.015]) retained intervals excluding zero (unadjusted)."

---

## 4. Study 2 at K = 1000: D − C vs B − A

### Artifacts and exact results

`research_audit/outputs/v02_performance.csv` and `v02_contrasts.csv`.
- **Cohort:** K = 1000, 73 events (28 campaign / 45 comparison). It is identical to the common cohort.
- **Setting:** KK, partition 42. FPB with 1,000 resamples; Holm across the three K.
- **Status:** all `token_std` results are exploratory and post hoc.

| Item | Value |
|---|---|
| B − A, Δ log loss | −0.114 [−0.218, −0.011]; Holm 0.084 |
| D − C, Δ log loss | −0.138 [−0.208, −0.076]; Holm < 0.003 |
| B − A, ΔAUC / ΔBA | +0.065 [+0.010, +0.144] / +0.091 [+0.010, +0.176] |
| D − C, ΔAUC / ΔBA | +0.045 [+0.002, +0.111] / +0.031 [−0.010, +0.086] |
| Model log loss (mean over 10 seeds) | A 0.382, B 0.268, C 0.423, D 0.285 |
| C − A, Δ log loss | +0.041 [−0.033, +0.129], uncorrected (`outputs/run_v2/study2/results.json`) |
| (D − C) − (B − A), and D − B | **Not computed** |
| 10-partition sensitivity | B − A −0.102 [−0.204, +0.004]; D − C −0.129 [−0.204, −0.050] |
| Without the two no-text events | B − A −0.108 [−0.215, +0.004]; D − C −0.124 [−0.215, −0.037] (`final_diagnostics/outputs/d02_comparison_with_original.csv`) |

### What can be said

- **Both contrasts have the same direction,** and their intervals overlap almost entirely. The 0.024 difference between the point estimates was not tested.
- **D − C is measured against a weak comparator.** C has the highest log loss of the four models (its seed range 0.401–0.447 lies above A's 0.377–0.385). Its larger magnitude therefore partly reflects C's poor log loss, not more value from `token_std`.
- **D does not have a lower mean log loss than B** (0.285 vs 0.268). This compares two point estimates; no contrast was computed.
- **The Holm results differ** (< 0.003 vs 0.084), but a difference in significance is not a significant difference.

### Decision

**We can claim:**
- At K = 1000, adding `token_std` was associated with lower log loss whether it was added to N_K (−0.114) or to N_K plus structure (−0.138), in both cases post hoc.
- The two estimates were not compared statistically.

**We must avoid:**
- "Larger", "stronger" or "more useful beyond structure".
- "D − C is significant but B − A is not, so …".
- "D is the best model".
- Any statement ranking B against D.

**Wording.**
> "On the K = 1000 cohort (73 events), adding message-length dispersion lowered single-view log loss when added to N_K (B − A: −0.114 [−0.218, −0.011]) and when added to N_K plus the structural features (D − C: −0.138 [−0.208, −0.076]); both are post-hoc, exploratory contrasts. We did not test whether the two differ, and their intervals overlap almost entirely. The model with N_K and structure but without dispersion (C) had the highest log loss of the four (0.423, against 0.382 for N_K alone), so the D − C contrast is measured against a comparatively poorly calibrated baseline."

---

## 5. Figures and tables: main text vs supplement

**Main text: 3 tables and 2 figures.** All exist or are assembled from existing values without new computation.

| # | Item | Purpose | Source | Status |
|---|---|---|---|---|
| Table 1 | Archive and cohort | Data, provenance, class size difference (medians) and usable-text share | `results.tex` `\RTabCohort` + `s01_content_verification.json` (usable share 0.58 / 0.80) | Exists; add one row and change the "Official LEN-Small" wording |
| Table 2 | Study 1 contrasts | One table for RQ1. Columns: primary partition, 20-partition. Rows: C1 (§1), M2 − M0q and E2 (§2), C3, E3, the 101-event C1 (§3), and counts + `token_std` vs M4 (post hoc, marked) | `paper_results.json`; `s02_contrasts.csv`; `s04_posthoc_lensd.json` | Values exist; assemble |
| Figure 1 | Endpoint occupancy: E[N_250] vs node count, with R² inset | The collision-dependent mechanism, which carries the "why" of the working question | `paper/figures/fig4_endpoint_mechanism.pdf` | Exists |
| Table 3 | Study 2 models A–D by K (log loss, AUC, BA), with B − A, D − C and C − A beneath | The RQ2 core. Footnote: post hoc; common-cohort B and D not computed; C's log loss at K = 1000 | `v02_performance.csv`; `v02_contrasts.csv`; `outputs/run_v2/study2/results.json` | Values exist; assemble |
| Figure 2 | `token_std` contrasts by K (views, with full-graph reference) | Shows direction and uncertainty together; makes the overlapping intervals visible (§4) | `research_audit/outputs/v02_fig2_contrasts.png` (data `v02_fig2_data.csv`) | Exists. A re-plot from the CSV for print quality is formatting only. Caption: post hoc; BA secondary |

**Supplement** (all exist):

| Item | Source |
|---|---|
| S1 Size distributions | `paper/figures/fig1_size_distributions.pdf` |
| S2 Study 1 performance by level, LR and HGBT (incl. 20-partition means) | `\RTabLevels`; `s02_performance.csv` |
| S3 Study 1 contrast graphic | `paper/figures/fig2_study1_contrasts.pdf` |
| S4 Degree-preserving null | `\RTabNull`; give two key numbers in the main text |
| S5 Partition stability of C1 | `s02_fig1_split_stability.png` |
| S6 Per-event contributions to C1 (caption without "influence") | `s03_fig_event_influence.png` |
| S7 Flexible count baselines | `s02_contrasts.csv` |
| S8 Single-view BA, common cohort | `paper/figures/fig3_study2_single_view.pdf` |
| S9 Retraining and transfer, with AUC | `outputs/run_v2/study2/results.json`; `a04_study2_diagnostics.csv` |
| S10 View vs full `token_std` (a measurement check) | `v02_fig3_view_vs_full.png` |
| S11 Text availability by class and K; `m_K` vs `token_std` | `v02_fig1_text_availability.png`; `final_diagnostics/outputs/d01_fig_mK_vs_tokenstd.png` |
| S12 Study 2 exclusion of the no-text events | `final_diagnostics/outputs/d02_comparison_with_original.csv` |
| S13 Exploratory matching | `\RTabMatching` |

**Why this split.**
- Each main-text item answers one part of the working question:
  - Table 1: what the data are;
  - Table 2: how much predictability counts recover, and what adds to them;
  - Figure 1: why views remain predictive;
  - Table 3 and Figure 2: what retains incremental value under edge limits.
- Graphics that duplicate a table (S3, S8), checks (S5, S6, S10, S12) and secondary models or designs (S2, S4, S7, S9, S13) go to the supplement.

**Avoid.**
- BA-only figures in the main text.
- Putting the `token_std` view-vs-full scatter in the main text, where it would read as a finding.
- Any figure or table that needs values marked NOT COMPUTED in `contrast_inventory.md`.
