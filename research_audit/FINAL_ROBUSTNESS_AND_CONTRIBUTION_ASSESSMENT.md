# LEN-Small — Study 1 Robustness, Contribution Assessment and Research Direction

Date: 2026-11-05. Scope: the 103-graph archive analysed in `paper/main.tex`. Builds on
`AUDIT_REPORT.md` (2026-11-04), `INVESTIGATION_LEDGER.md` and `OPUS_OCCUPANCY_REPRODUCTION.md`,
which are cited, not repeated. Nothing outside `research_audit/` was modified; no earlier audit
output was overwritten.

**New work in this phase**

| Script | Purpose | Main outputs (`research_audit/outputs/`) |
|---|---|---|
| `s00_engine.py` | Exact re-implementation of the paper's Study 1 LR procedure (shared code) | — |
| `s01_content_verification.py` | Content features and text availability recomputed from the raw tar | `s01_content_verification.{csv,json,log}` |
| `s02_study1_robustness.py` | 20-split stability, flexible count baselines, content dissection, missing-text and grouped-fold sensitivity | `s02_results.json`, `s02_contrasts.csv`, `s02_performance.csv`, `s02_per_repeat.csv`, `s02_content_correlations.csv`, `s02_oof.npz`, `s02_fig1–3*.png` (+ `_data.csv`), `s02.log` |
| `s03_event_influence.py` | Per-event decomposition, jackknife, refit leave-one-event-out, diagnostic exclusions | `s03_event_influence.csv`, `s03_exclusions.csv`, `s03_results.json`, `s03_fig_event_influence.png` (+ data), `s03.log` |
| `s04_posthoc_lensd.py` | Post-hoc: counts + message-length dispersion vs the full model (no refitting) | `s04_posthoc_lensd.json`, `s04.log` |

**Validation of the engine (VERIFIED).** On the primary split, the re-implementation reproduces
every stored out-of-fold probability of M0–M4, under both tuning objectives, to ≤ 3 × 10⁻¹⁴. On
the paper's 10 split seeds it reproduces every stored log loss and balanced accuracy (BA) in
`repeated_splits_lr.csv` to ≤ 6 × 10⁻¹⁵. This is stronger than the earlier audit's refit (a03),
which matched BA only up to tie-breaks. The difference is that row order and fold construction now
follow the pipeline exactly.

**Conventions.**
- **Contrast notation:** Δ = A − B on identical events. Negative Δ log loss favours A; positive
  ΔAUC and ΔBA favour A.
- **Repeats:** "20 splits" means 20 outer stratified 5-fold partitions (seeds 42 and 1–19; the first
  10 are the paper's).
- **Primary uncertainty:** an event bootstrap (2,000 resamples, seed 7). Per-event log loss is
  averaged over splits; AUC and BA are averaged over splits, with the same resampled events in
  every split.
- **Estimands:** BA comes from BA-tuned fits; log loss and AUC from log-loss-tuned fits, as in the
  paper.
- **Status:** everything in this phase is a post-hoc robustness analysis of the paper's
  pre-specified contrast C1. Holm correction covers the seven contrasts marked "Holm family" (log
  loss). All other contrasts are exploratory and unadjusted.

---

## Part I — Executive assessment

**Current strength.** The core empirical result holds up. The full feature set M4 improves
probabilistic prediction and ranking over the paper's count baseline. The improvement survives:
- removing any single event;
- every one of 20 re-partitions for AUC, and 19 of 20 for log loss;
- controlling for text availability;
- excluding the two events without text.

It is, however, smaller and less certain than the primary-split figure suggests:

| | Primary split (paper) | Mean over 20 splits |
|---|---|---|
| C1 Δ log loss | −0.110 [−0.181, −0.039] | −0.094 [−0.172, −0.013] |
| Unadjusted p | — | 0.024 |
| Holm p (phase family) | — | 0.12 |

The result also changes when it is decomposed. The gain beyond size is almost entirely one
interpretable content dimension, the dispersion of message length; graph topology contributes
little or nothing detectable.

**Strongest defensible contribution.** A benchmark-validity analysis of LEN-Small that finds:
1. The labels are mostly predictable from graph size, and how much depends on how flexibly size
   is modelled.
2. The residual signal beyond size is modest, probabilistic rather than decisional, and lives in
   message-length homogeneity rather than in graph arrangement.
3. Under fixed-budget edge sampling, the label signal in a view is again mostly size, transmitted
   through endpoint occupancy. Occupancy is a degree-sequence functional that degree-preserving
   nulls cannot see by construction.
4. The evaluation choices that decide these conclusions (count-baseline form, metric, single
   versus repeated splits) are documented with evidence.

This is coherent and useful. It is not a detection method, and it should not be framed as one.

**Most important remaining uncertainty.** External validity. Every result comes from one
103-graph archive whose relation to the published LEN-Small is undefined (AUDIT_REPORT B.2–B.4).
The specific "beyond size" feature (message-length dispersion) was identified post hoc on the same
events. No analysis on this archive can remove either issue.

**Readiness.** Ready for paper development, after the reporting changes in Parts IV and VI. No
further analysis is required to answer the four robustness questions.

---

## Part II — Study 1 robustness

### Reference performance (mean over 20 splits; split-to-split SD in parentheses)

| Model | Features | Log loss | AUC | BA |
|---|---|---|---|---|
| M0 | log counts | 0.328 (0.007) | 0.932 | 0.864 |
| M0q | counts + squares + product (paper baseline) | 0.325 (0.007) | 0.933 | 0.867 |
| P3 | cubic polynomial in log counts, tuned C | 0.321 (0.008) | 0.935 | 0.865 |
| S | additive cubic splines on log counts, tuned C | 0.349 (0.058) | 0.927 | 0.836 |
| QDA | quadratic discriminant on log counts | 0.315 (0.014) | 0.950 | 0.856 |
| M1 | M0q + degree Gini | 0.364 (0.027) | 0.918 | 0.860 |
| M2 | M1 + arrangement | 0.326 (0.017) | 0.935 | 0.873 |
| M3 | M0q + content (3) | 0.290 (0.032) | 0.954 | 0.892 |
| **M4** | all (paper's full model) | **0.231 (0.035)** | **0.967** | **0.902** |
| M4S | spline counts + all non-count features | 0.276 (0.056) | 0.956 | 0.894 |
| M0q + lensd | counts + message-length SD only | 0.245 (0.013) | 0.963 | — |

The primary split (seed 42) is typical for log loss. Its C1 of −0.110 ranks 8th of 20, and the
median per-split C1 is −0.103. The 20-split mean of −0.094 is pulled down mainly by two splits
(seeds 3 and 7; see B). For BA the primary split is the least favourable: ΔBA +0.010, tied smallest
of the 20. The paper already notes the BA side.

### A. Event influence (`s03`)

**Decomposition.** C1's log-loss gain is the mean of per-event differences d_i (Fig.
`s03_fig_event_influence.png`, left).
- **Breadth:** 82 of 103 events improve, but the median d_i is only −0.020, against a mean of
  −0.094.
- **Heavy tails in both directions:**
  - the 10 events most favourable to M4 contribute 94% of the net gain;
  - the 5 most favourable contribute 58%;
  - the 5 most unfavourable offset 54%.
- **What M4 does:** it corrects a handful of confidently wrong count predictions and introduces a
  few new confident errors. In between, it slightly improves most events.

**Özür_Dilerim** (campaign; 2,517 nodes, 1,748 edges; largest component 6.5% of nodes; 46% usable
text):
- It is the most influential event, but it works **against** M4.
- Both models call it a comparison event: mean P(campaign) is 0.034 for M0q and 0.008 for M4.
- Its d_i of +2.10 is the largest in the archive. In magnitude it equals 22% of the net gain summed
  over all events.
- It alone produces the only split where C1 reverses (seed 3, ΔLL +0.028; without it, −0.055).
- Removing it and refitting strengthens C1 to −0.103 [−0.189, −0.025].
- Why it fails: it is large, which looks like a comparison event, and its messages have varied
  lengths (SD 10.3, typical of comparison events). Both signals point the wrong way. It is a
  genuine hard case, not a data error.
- **It must not be removed.**

The events that most favour M4 are, in decreasing order:
- `Milliyol_Partisi` (comparison, small, varied messages);
- `İletişim_Başkanlığı` (campaign, large, length SD 1.5, 99% duplicates);
- `#ChampionsLeague`;
- `#Mazi`;
- `Yarısı_Bizden`.

Each is a size-atypical event that content corrects.

**Jackknife (no refit, 20 splits).** Deleting any one event leaves:

| Metric | Range of C1 after deleting one event |
|---|---|
| Δ log loss | −0.115 to −0.079 |
| ΔAUC | +0.028 to +0.037 |
| ΔBA | +0.025 to +0.045 |

**Refit leave-one-event-out (10 splits, both objectives, 4,120 fits).** Removing each event in
turn and refitting gives:

| Metric | Range of C1 after removal and refit |
|---|---|
| Δ log loss | −0.106 to −0.070 |
| ΔAUC | +0.026 to +0.036 |
| ΔBA | +0.012 to +0.047 |

No single removal changes the sign of any metric. Training-set effects, meaning changes in other
events' predictions, are small: at most about 0.01. The largest come from `#MetaAirdrop`,
`Yakup_Türkal` and `#RealMadridManCity`.

**Diagnostic exclusion sets** (refit, 20 splits; sets chosen from the same data, so these are
stress tests, not corrected estimates):

| Removed | n | Δ log loss | ΔAUC | ΔBA |
|---|---|---|---|---|
| none | 103 | −0.094 [−0.172, −0.013] | +0.034 [+0.006, +0.070] | +0.035 [−0.020, +0.095] |
| Özür_Dilerim | 102 | −0.103 [−0.189, −0.025] | +0.033 [+0.005, +0.072] | +0.039 [−0.013, +0.095] |
| top 1 favouring M4 | 102 | −0.081 [−0.154, −0.007] | +0.029 [+0.005, +0.059] | +0.038 [−0.010, +0.091] |
| top 3 favouring M4 | 100 | −0.057 [−0.128, +0.016] | +0.020 [−0.002, +0.048] | +0.021 [−0.023, +0.070] |
| top 5 favouring M4 | 98 | −0.050 [−0.100, +0.000] | +0.015 [−0.002, +0.036] | −0.004 [−0.044, +0.034] |
| top 10 favouring M4 | 93 | −0.002 [−0.049, +0.043] | +0.001 [−0.009, +0.013] | +0.005 [−0.024, +0.036] |
| top 5 favouring M0q | 98 | −0.230 [−0.325, −0.146] | +0.052 [+0.018, +0.096] | +0.093 [+0.040, +0.151] |
| symmetric trim (5 + 5) | 93 | −0.123 [−0.191, −0.062] | +0.024 [+0.005, +0.050] | +0.041 [+0.002, +0.085] |
| 5 highest M4 losses | 98 | −0.194 [−0.292, −0.095] | +0.043 [+0.013, +0.082] | +0.090 [+0.035, +0.151] |
| 5 highest M0q losses | 98 | −0.059 [−0.151, +0.031] | +0.014 [−0.005, +0.040] | +0.044 [−0.003, +0.097] |
| 11 campaigns with < 20% usable text | 92 | −0.112 [−0.199, −0.020] | +0.044 [+0.008, +0.088] | +0.031 [−0.025, +0.083] |

**Interpretation.**
- The gain does not rest on one event.
- One-sided deletion of the most favourable events removes it: after three events, the intervals
  include zero.
- Symmetric trimming strengthens it. The trimmed mean (5% each side) is −0.100.
- So the effect is real but tail-borne: the mean is driven by events where size misleads, and
  content corrects some of them and worsens a few others.

**Answer to A.**
- A small number of events dominates the magnitude, not the existence, of the gain.
- No single event is decisive; Özür_Dilerim weakens rather than inflates the result.
- **Label: STRONGLY SUPPORTED** for log loss and AUC; BA is not interpretable at this size.

### B. Split stability (`s02`, Fig. `s02_fig1_split_stability.png`)

C1 across 20 partitions:

| Metric | Splits favouring M4 | Range across splits | Notes |
|---|---|---|---|
| Δ log loss | 19 / 20 | −0.122 to +0.028 | SD 0.035; 91 of 100 individual folds favour M4 |
| ΔAUC | 20 / 20 | +0.014 to +0.042 | |
| ΔBA | 20 / 20 (no ties) | +0.010 to +0.059 | Event interval [−0.020, +0.095] |

**Partition variability versus event uncertainty.**
- The split-to-split SD of Δ log loss (0.035) is about as large as the event-bootstrap SD of the
  repeat-averaged estimate (0.040).
- The primary-split interval resamples events for one fixed partition, so it omits a source of
  variation of the same size as the one it includes.
- The repeat-averaged interval [−0.172, −0.013] is the better single summary.
- The 20 splits reuse the same 103 events. Consistent signs across them show insensitivity to
  partitioning, **not replication**. The ≥ 19/20 counts must not be read as 19 independent
  confirmations.

**Do the same feature families help consistently?** Per-split contrasts, 20 splits:

| Family contrast | Mean Δ log loss | Splits better (LL / AUC / BA) | Event-bootstrap interval |
|---|---|---|---|
| degree Gini given counts (M1 − M0q) | +0.040 (harms) | 0 / 0 / 5 | [+0.027, +0.053] |
| arrangement given counts + degree (M2 − M1) | −0.038 | 20 / 20 / 15 | [−0.089, +0.016] |
| structure given counts (M2 − M0q) | +0.002 | 9 / 13 / 14 | [−0.048, +0.053] |
| content given counts (M3 − M0q, = C3) | −0.035 | 17 / 20 / 15 | [−0.120, +0.069] |
| content given counts + structure (M4 − M2, = E3) | −0.096 | 19 / 20 / 20 | [−0.165, −0.032] |
| structure given counts + content (M4 − M3, = E2) | −0.059 | 19 / 20 / 14 | [−0.110, −0.011] |
| all given spline counts (M4S − S) | −0.073 | 18 / 20 / 20 | [−0.163, +0.023] |

**Consistent patterns.**
- Degree Gini consistently *worsens* calibration when added to counts.
- Arrangement then recovers about what Gini lost, so structure as a whole adds nothing over counts.
- Content helps in most splits.

**Grouped folds.** Keeping the two repeated campaign hashtags (Tapuma_YapıKayıt,
ŞartsızTayin_Şart) in one fold attenuates C1 slightly: −0.082 [−0.164, +0.005]; ΔAUC +0.030
[+0.002, +0.065]. Event dependence through repeated hashtags is therefore a small but
non-negligible optimism.

**Answer to B.**
- The direction of C1 is stable across partitions.
- Its magnitude is not: it ranges from −0.12 to +0.03 in log loss.
- Partition variability is as large as event uncertainty.
- **Label: VERIFIED** (stability of direction); magnitude STRONGLY SUPPORTED at about −0.09.

### C. Content-feature contribution (`s01`, `s02`, `s04`)

**C.1 Feature calculations (VERIFIED).** Recomputed from the raw JSON with independently written
code, all three content features match the stored values exactly (max |diff| = 0). The NaN pattern
is identical.

**C.2 Text availability — a property of the release, not of our pipeline (VERIFIED).**
- **Scale:** 79,271 of 288,540 links (27.5%) have `text: null` in the raw archive. The key is
  always present; no text is empty before cleaning.
- **By class:**

  | Class | Mean usable-text share | Range |
  |---|---|---|
  | Comparison | 0.80 | 0.31–0.99 |
  | Campaign | 0.58 | 0.00–0.98 |

- **Low-text events:** 11 campaign events and no comparison event have less than 20% usable text.
- **No text at all:** two campaign events, `Tapuma_YapıKayıt___2023-04-19` and
  `YapıKayıt_YoksaOyyok___2023-05-01`; their related hashtag `Tapuma_YapıKayıt___2023-04-22` has
  1.4%.
- **Signal in missingness:** the missing share alone separates the classes weakly (AUC 0.64).
  Null text plausibly reflects tweets unavailable at collection time (for example deleted or
  suspended), which would be a retention artefact correlated with the label. That mechanism is an
  inference, not verified.
- **Effect on content features:** they are computed only over retained text, so they could in
  principle encode retention rather than content. The checks below test this.

**C.3 Missing-value handling (VERIFIED).**
- Median imputation is a pipeline step fitted on each training fold (`src/train.make_logreg_pipeline`).
- There is no leakage, but the two no-text campaign events receive the training-fold median.
- Sensitivities:
  - **Excluding both (101 events):** C1 −0.083 [−0.171, +0.008]; ΔAUC +0.033 [+0.004, +0.069];
    content beyond structure (E3) −0.087 [−0.158, −0.015].
  - **Missing-text indicator added to M4:** no change (Δ < 0.001).
- Without those two events, C1's log-loss interval widens to include zero; the point estimate moves
  from −0.094 to −0.083. Why M4 handles them better was not isolated. The content-beyond-structure
  result does not depend on them.

**C.4 Does content add value?**

| Contrast | Δ log loss [95%] | ΔAUC [95%] |
|---|---|---|
| C3: content given counts (M3 − M0q) | −0.035 [−0.120, +0.069] | +0.022 [−0.007, +0.056] |
| E3: content given counts + structure (M4 − M2) | −0.096 [−0.165, −0.032]; Holm p 0.021 | +0.032 [+0.008, +0.064] |
| E3 controlling for usable-text share | −0.088 [−0.157, −0.019] | +0.029 [+0.006, +0.059] |
| C3 controlling for usable-text share | −0.046 [−0.132, +0.064] | +0.023 [−0.013, +0.062] |
| Text share added to M0q | +0.006 (no help) | −0.004 |
| Text share added to M4 | −0.000 | −0.000 |

Text availability neither predicts the labels beyond counts nor explains the content effect.

**C.5 Which content feature? Single-feature additions and drop-one (exploratory):**

| Contrast | Δ log loss [95%] | ΔAUC [95%] |
|---|---|---|
| counts + **length dispersion** − counts | −0.080 [−0.160, +0.004] | **+0.031 [+0.003, +0.068]** (20/20 splits) |
| counts + duplicate fraction − counts | −0.002 [−0.053, +0.064] | +0.008 [−0.013, +0.029] |
| counts + frequency Gini − counts | −0.016 [−0.068, +0.045] | +0.011 [−0.008, +0.033] |
| M2 + length dispersion − M2 | −0.089 [−0.167, −0.019] | +0.031 [+0.006, +0.063] |
| M4 − (M4 without length dispersion) | −0.060 [−0.138, +0.008] | +0.018 [−0.003, +0.048] |
| M4 − (M4 without duplicate fraction) | +0.001 | −0.001 |
| M4 − (M4 without frequency Gini) | −0.002 | +0.001 |
| *Post hoc (s04):* M4 − (counts + length dispersion) | **−0.014 [−0.055, +0.024]** | +0.004 [−0.009, +0.016] |
| *Post hoc (s04):* M4 − (M2 + length dispersion) | −0.007 [−0.030, +0.018] | +0.002 [−0.006, +0.008] |

**What this shows.**
- Message-length dispersion carries essentially all of the content signal.
- Counts plus that single feature (the five M0q count terms plus one) are statistically
  indistinguishable from the 14-feature M4 (log loss 0.245 vs 0.231).
- The duplicate fraction and frequency Gini add nothing given the rest. In M3 they actively dilute
  the model: M3 has log loss 0.290, against 0.245 for counts plus length dispersion alone.
- That dilution explains why C3, which adds all three content features, looked null.
- It also explains why the paper's E2/E3 pattern ("complementary information in the combined
  feature set") appeared. Structure partly compensates for two noisy content features. The
  evidence does not show a genuine content–structure interaction.

**C.6 Are the duplicate-text and concentration features distinct?** (`s02_content_correlations.csv`,
Spearman, 101 events)
- **Duplicate fraction and frequency Gini:** ρ = 0.59, and 0.66 after partialling out the M0q count
  terms. They largely measure the same thing, how dominated the message pool is by repeated text.
- **Frequency Gini and size:** Gini is strongly size-related (ρ with log nodes 0.63), so it is
  partly a size proxy.
- **Length dispersion:** nearly independent of both (ρ −0.32 and −0.06; partial −0.44 and −0.31)
  and only weakly related to size (0.31) and to text availability (−0.11).
- **Direction:** campaign events have *lower* length dispersion (mean token-count SD 7.9 vs 9.9;
  univariate AUC for comparison 0.79), consistent with templated or copy-pasted campaign messages.
- **Caveat:** "templated messaging" is an interpretation, not something this analysis tested.

**Answer to C.**
- Content adds predictive value beyond counts plus structure (robust: E3 survives Holm,
  text-share control and removal of the no-text events).
- Content beyond counts alone is not detectable with the three-feature set, but is detectable in
  AUC for the single length-dispersion feature.
- The result does not depend on the two no-text events, except that C1's log-loss interval widens.
- Missing-value handling is correct.
- Duplicate fraction and frequency Gini are largely redundant with each other and add nothing.
- **Labels:** content beyond counts + structure STRONGLY SUPPORTED. "The signal is message-length
  dispersion" is EXPLORATORY (post hoc, same events).

### D. Flexible count baselines (`s02`, Fig. `s02_fig2_contrasts.png`)

Applying the lesson of the occupancy reproduction. The count-baseline alternatives were chosen in
advance as a small set: cubic polynomial (P3), additive splines (S) and QDA, with QDA kept because
it was the decisive baseline in that reproduction.

| Holm-family contrast (log loss) | Δ log loss [95%] | p (Holm) | ΔAUC [95%] | ΔBA [95%] |
|---|---|---|---|---|
| C1: M4 − M0q | −0.094 [−0.172, −0.013] | 0.024 (0.120) | +0.034 [+0.006, +0.070] | +0.035 [−0.020, +0.095] |
| M4 − P3 | −0.090 [−0.165, −0.015] | 0.017 (0.102) | +0.032 [+0.004, +0.068] | +0.038 [−0.017, +0.096] |
| M4 − S | −0.118 [−0.227, −0.011] | 0.033 (0.132) | +0.040 [+0.004, +0.082] | +0.067 [+0.012, +0.126] |
| M4 − QDA | −0.084 [−0.232, +0.081] | 0.264 (0.528) | +0.017 [−0.026, +0.057] | +0.047 [−0.007, +0.100] |
| M4S − S | −0.073 [−0.163, +0.023] | 0.128 (0.384) | +0.029 [−0.004, +0.067] | +0.058 [+0.008, +0.111] |
| C3: M3 − M0q | −0.035 [−0.120, +0.069] | 0.442 (0.528) | +0.022 [−0.007, +0.056] | +0.025 [−0.030, +0.083] |
| E3: M4 − M2 | −0.096 [−0.165, −0.032] | 0.003 (**0.021**) | +0.032 [+0.008, +0.064] | +0.029 [−0.014, +0.075] |

**What this shows.**
- **Polynomial and spline baselines:** neither improves on M0q (P3 − M0q −0.004; S − M0q +0.024,
  with unstable spline fits, split SD 0.058). M4 beats both by about as much as it beats M0q.
- **QDA on counts:** the strongest count-only ranker, with AUC 0.950 against 0.933 for M0q.
  - Against QDA, M4's advantage has the same direction (19/20 splits in log loss) and a similar log-loss point estimate.
  - But the interval is wide and includes zero, because QDA makes a few catastrophic probability
    errors.
  - The AUC advantage shrinks to +0.017.
- **Feature value given flexible counts** (all non-count features added to spline counts, M4S − S):
  same direction, log-loss interval includes zero, BA interval excludes zero.
- **The straight-line lesson carries over partly.**
  - Part of M4's AUC advantage over M0q (about half: +0.034 against +0.017) is matched by a
    flexible count model.
  - The log-loss advantage is not matched by any count model's point estimate. The best count log
    loss is 0.315, against 0.231 for M4.
  - So here the gap is not purely nonlinear size, unlike E[N_K] in the occupancy study. But it is
    not established against every reasonable count baseline either.
- **Multiplicity:** after Holm across these seven contrasts, only E3 remains below 0.05. C1's
  unadjusted repeat-averaged interval excludes zero; its Holm-adjusted p is 0.12. This family
  deliberately pairs C1 with highly correlated alternatives, so Holm is conservative here. The
  paper's original three-contrast Holm result (primary split, p = 0.009) stands as reported. It
  should be accompanied by the repeat-averaged estimate.

**Answer to D.**
- The full model's log-loss and AUC gains survive polynomial and spline count baselines.
- Against QDA on counts, and when the features are added to spline counts, the gain keeps its
  direction and size in log loss, but it is not statistically established.
- The AUC gain over a flexible count ranker is small (+0.017).
- **Label: STRONGLY SUPPORTED** against the paper's and other LR count baselines; UNRESOLVED
  against the most flexible count baseline.

---

## Part III — Integration of existing findings

| Finding (evidence) | Status | Where it belongs |
|---|---|---|
| **Study 1–Study 2 relationship.** Both studies find that most label signal is size. Study 1: counts reach AUC 0.93–0.95. Study 2: a view's N_K, a size-like occupancy quantity, carries the view's signal, and in fixed-K views structural features become size proxies (AUDIT a04: struct6 AUC 0.767 full vs 0.947 view-trained). New: Study 1's residual beyond size is message-length homogeneity, which Study 2 has not tested on its own. | VERIFIED (size); open (content under sampling) | **Main results** (narrative spine); the content-under-sampling question is Part V, experiment 1 |
| **Endpoint occupancy** (OPUS_OCCUPANCY_REPRODUCTION). E[N_K] is a correct degree-sequence functional. Alone it gives AUC 0.96, beating *linear* counts (+0.030 [+0.005, +0.061]), but not QDA (+0.012 [−0.042, +0.061]), not log loss, and not counts + Σd² + degree-1 fraction (+0.008); the edge fades with K. | VERIFIED (formula, invariance); EXPLORATORY (signal) | **Results** (Study 2 mechanism: what a view measures) + **Methods** (equation). Present it as explaining *why views are size-informative*, not as a new predictor |
| **Rewiring limitations.** The null preserves every d_v, hence E[N_K] exactly; it changes only reciprocity, connectivity and max core in practice (46% zero reciprocity variance, 99% median core). | VERIFIED | **Methods** (what the null can test) + one sentence in **Discussion** linking it to occupancy |
| **Ranking vs threshold.** BA differences are uninterpretable (±0.01–0.02 from tie-breaks; primary split least favourable of 20); N_K-only frozen transfer has BA 0.500 with AUC 0.942; KK vs FF at K = 1000 differs in BA but not AUC or log loss. | VERIFIED | **Methods** (estimands) + **Results** (report AUC and log loss with every transfer contrast) |
| **Sampled-view information vs training regime.** Sampling cannot add information about the full graph; "views beat full graphs" at K = 1000 is a threshold effect; the struct6 retraining effect mixes regime with features changing meaning. | VERIFIED | **Results** (reworded Study 2) + **Limitations** |
| **Size as predictor vs confounder.** The label is predictable from size in this archive. The LEN-Small selection is undocumented, and its stated rule contradicts its tables, so size could be partly a selection artefact. Content features are not size-free either (frequency Gini ρ 0.63 with log nodes). | VERIFIED (contradiction); UNRESOLVED (mechanism) | **Discussion** (size as a benchmark property, not a coordination signal) + **Limitations** |
| **Dataset provenance.** The archive is not the tabulated LEN-Small; the stated rule contradicts the published tables; there are 27.5% null texts, unevenly by class (new). | VERIFIED | **Data section** (main text, short) + **Limitations** |
| **Cross-event account overlap.** Not measurable (no identifiers); 92.7% is index reuse. | DISPROVEN (figure); UNRESOLVED (question) | **Limitations** (one sentence). Remove any overlap claim |
| **Repeated hashtags.** Grouped folds attenuate C1 by about 0.01. | VERIFIED (sensitivity) | **Limitations**, with the number |
| **Exploratory size matching.** 20–30 pairs, no intervals. | Weak | Keep as a short sensitivity or move to a supplement; do not build arguments on it |
| **HGBT secondary model.** Metric-specific disagreement; no extra feature value. | VERIFIED | **Methods** sentence + supplement table; cut from the main narrative |
| **E[N_K] degree-heterogeneity "beyond counts".** Advantage only over linear counts in AUC. | Mostly explained by nonlinear size | **Nowhere** as a claim; at most a footnote in the occupancy paragraph |
| **Degree Gini.** Harms calibration in 20/20 splits; adds no explained variance for log E[N_K]. | VERIFIED | **Results**, one sentence: the common degree-concentration summary carries no label information beyond counts here |

---

## Part IV — Research contribution

**What we can confidently claim** (for this 103-graph archive only):
1. Graph size alone predicts the file-name labels well: counts reach AUC 0.93 with LR and 0.95 with
   a quadratic discriminant; BA is about 0.86–0.88.
2. Adding the evaluated structural and content features improves probability quality and ranking
   over LR count baselines: about −0.09 log loss (repeat-averaged; −0.11 on the primary split) and
   about +0.03 AUC. This holds across every partition examined (AUC 20/20, log loss 19/20) and after
   removing any single event.
3. No balanced-accuracy improvement can be established; BA contrasts are dominated by tie-breaks and
   partitioning.
4. Structural features (degree Gini, reciprocity, largest component, coreness) add no detectable
   information beyond counts. Degree Gini alone consistently worsens calibration.
5. Content adds information beyond counts and structure. This holds after controlling for text
   availability and without the two no-text events.
6. The content features are computed correctly. The release withholds 27.5% of message texts,
   disproportionately in campaign events.
7. Endpoint occupancy is a degree-sequence functional, exactly invariant in expectation under
   degree-preserving rewiring. Rewiring nulls therefore cannot detect degree-sequence-driven signal.
8. The archive is not the tabulated LEN-Small, and the published selection rule contradicts the
   published tables.

**What we can cautiously claim:**
1. The content signal is essentially message-length dispersion: campaign events have more uniform
   message lengths. Counts plus this one feature match the full model. *(Post hoc on the same events.)*
2. The full model's log-loss gain is probably not only nonlinear size. Its point estimate exceeds
   every count model's, and its direction holds against QDA and spline counts, but it is not
   statistically established against the most flexible count baseline.
3. Single fixed-budget views were not detectably less informative than full graphs at K = 250–1000.
   What a view carries is predominantly size-like.
4. The gain is tail-borne: most events change little, and a minority of size-atypical events are
   corrected (or, in a few cases, worsened) by content.

**What remains exploratory:**
1. Degree heterogeneity beyond (n, m) as a label signal (E[N_K] beyond linear counts).
2. Whether message-length homogeneity reflects coordinated templating (an interpretation, not tested).
3. Whether the content signal survives restricted observation (not yet examined; Part V).
4. The mechanism behind missing text (deletion or suspension is plausible but unverified).

**What we should no longer claim:**
1. "LEN-Small consists of the 100 smallest LEN graphs", or that the archive is "the official release
   plus three events".
2. Any cross-event account overlap figure (92.7%).
3. "Neither … content alone (C3) accounts for this gain" and "complementary information in the
   combined feature set". Content, specifically one feature, accounts for nearly all of it; the
   apparent complementarity is dilution by two redundant content features.
4. C1 −0.110 [−0.181, −0.039] as the *only* uncertainty statement. It is a typical partition (8th
   of 20), but its interval omits partition variability of comparable size. The repeat-averaged
   −0.094 [−0.172, −0.013] should accompany it.
5. "Training on observations of the kind being scored matters far more than averaging repeated
   views" in its current general form. For N_K it is a threshold shift; for struct6 it is confounded
   with features that change meaning.
6. Any suggestion that sampling improves classification (the K = 1000 BA gain).
7. That the null-model result bears on degree-sequence information.

---

## Part V — Opportunities to improve

**What is genuinely interesting.**
1. **One coherent account of the benchmark's label signal: size, in several disguises.**
   - Size appears as counts, nonlinear count functions, occupancy of sampled views, and structural
     features that become size proxies under sampling.
   - Degree-preserving nulls are blind to all of these by construction.
   - Most benchmark audits stop at "size predicts labels"; this one shows the *routes* by which size
     re-enters.
2. **A small, interpretable, non-size residual.**
   - That the only robust beyond-size signal is message-length homogeneity, not topology, is a
     substantive finding for coordination research.
   - Graph-learning methods on LEN are motivated by topology, yet the topology summaries tested add
     nothing beyond size here.
3. **A worked methodological lesson.**
   - Four evaluation choices change the conclusions: linear vs flexible count baselines, BA vs log
     loss vs AUC, single vs repeated partitions, and set-level vs single-feature contrasts.
   - The C3 null hid the strongest single feature.
   - These are reusable recommendations for anyone evaluating on LEN.

**Coherence gaps in the current paper.**
1. Study 1 and Study 2 are presented side by side, not as one argument. Size, and the occupancy
   mechanism, is the bridge.
2. The paper currently treats "content" as one block. The finding is one feature.
3. Text missingness, a release property correlated with the label, is not mentioned.

**Results that deserve more attention:**
- the single-feature content result;
- the consistent harm from degree Gini;
- QDA's count-only AUC of 0.95, the honest ceiling for "size alone";
- the null-model invariance of occupancy, which explains why "arrangement shows no gain" is the
  expected outcome for size-driven signal.

**Recommended experiments (at most two), ranked:**

**Experiment 1 — Does the non-size signal survive restricted observation? (recommended)**
- **Question:** In fixed-K views, does message-length dispersion computed from the K sampled edges
  add information beyond the view's N_K, and is it attenuated relative to the full graph?
- **Design (fixed before running):**
  - Existing views (`data/processed/sampled_views_v2.parquet`, which already contains
    `msg_length_dispersion` per view), K ∈ {250, 500, 1000}.
  - Existing Study 2 folds, single-view estimand, KK regime.
  - One contrast per K: (N_K + lensd) − N_K, in log loss and AUC, with event-level bootstrap and
    Holm across the three K.
  - Plus one descriptive comparison of per-event view lensd against full-graph lensd.
- **Scores:**

  | Criterion | Rating | Reason |
  |---|---|---|
  | Expected value | High | It joins the two studies on the one beyond-size signal, and answers whether that signal is a property of the observed messages (survives sampling) or of complete text pools |
  | Validity | Good | Existing views and folds; one contrast per budget |
  | Feasibility | High | Hours, no new data |
  | Overfitting risk | Moderate | The feature was singled out post hoc on the same events. Pre-specifying the contrast limits but does not remove this; report as exploratory |
  | Changes the paper? | Yes | It decides whether the Discussion can say the content signal is observation-robust |

**Experiment 2 — Is length homogeneity a duplication effect? (optional, lower priority)**
- **Question:** Is the length-dispersion signal carried by repeated (templated) messages or by the
  distinct message pool?
- **Design:** recompute the token-count SD over *distinct* cleaned texts. This is a documented
  diagnostic variant; the original feature stays primary. Then repeat the single contrast
  "counts + variant − counts".
- **Scores:**

  | Criterion | Rating | Reason |
  |---|---|---|
  | Value | Moderate | It sharpens the interpretation ("templating" vs "length style") rather than the claim |
  | Validity | Good | — |
  | Feasibility | High | — |
  | Overfitting risk | Moderate | — |
  | Changes the paper? | Only the Discussion wording | — |

**Deliberately not recommended:**
- full-LEN replication (multi-GB download; a separate project);
- GNNs or further model families;
- more count-baseline variants;
- more rewiring realisations;
- conditional arrangement tests.

None would change what this paper can claim.

---

## Part VI — Final research direction

**Refined central question.** *How much of LEN-Small's label signal lies beyond graph size once size
is modelled flexibly, and where does any remainder reside — in graph structure, in message content,
or in what a partial observation of the graph reveals?*

**Relationship between the studies.**
- **Study 1 (full graphs)** measures the signal beyond size and locates it: not in structure, but
  modestly in content, specifically message-length homogeneity.
- **Study 2 (fixed-budget views)** shows that what an observer of a partial graph gets is mainly size
  again, through endpoint occupancy. It also explains, through the invariance result, why
  degree-preserving nulls cannot see this.
- Together: *size dominates the benchmark through several routes; topology summaries add nothing
  beyond it; a small content residual remains.* Experiment 1, if run, tests whether that residual
  survives partial observation.

**Key results the paper should communicate.**
1. **Size ceiling:** counts reach AUC 0.93 (LR) to 0.95 (QDA). Report the flexible baseline.
2. **Beyond-size gain:** about −0.09 log loss and +0.03 AUC over LR count baselines.
   - Robust to any single event and to every partition examined.
   - Not established against the most flexible count baseline.
   - No BA gain established.
   - Report the repeat-averaged estimate alongside the primary-split one.
3. **Locating the gain:** structure adds nothing beyond counts; content adds beyond counts and
   structure, robust to text availability; the content signal is message-length dispersion
   (exploratory).
4. **Partial observation:** single views are not detectably less informative; their signal is
   size-like through endpoint occupancy, a degree-sequence functional invariant under rewiring.
   Transfer contrasts are threshold- versus ranking-dependent, so report AUC and log loss.
5. **Evaluation lessons:** flexible count baselines; separate estimands; repeated partitions;
   single-feature as well as set-level contrasts.

**Suggested structure (IEEE, about 7 pages).**
1. **Introduction:** benchmark validity, the RQ above, three findings.
2. **Data and provenance:**
   - the archive, compactly;
   - the selection-rule contradiction;
   - "not the tabulated release";
   - text availability by class;
   - no account identifiers.
3. **Methods:**
   - features;
   - count baselines, including QDA;
   - estimands (BA, log loss, AUC) and why they differ;
   - repeated partitions with event bootstrap;
   - the rewiring null and what it can test;
   - the view design and the occupancy equation.
4. **Results I — size and beyond:**
   - count ceiling;
   - C1 (primary split and repeat-averaged);
   - influence summary;
   - structure vs content;
   - the single-feature result;
   - flexible baselines.
5. **Results II — partial observation:**
   - single view vs full graph (AUC and log loss alongside BA);
   - occupancy as mechanism;
   - null-model invariance;
   - reworded training-regime result.
6. **Discussion:**
   - size as a benchmark property;
   - what the content residual may and may not mean;
   - implications for LEN evaluations.
7. **Limitations:**
   - one archive;
   - post-hoc localisation;
   - text missingness;
   - repeated hashtags;
   - no account data;
   - unverified timestamps;
   - n = 103.
8. **Corrections and reproducibility** (as now).

**Limitations that must be acknowledged.**
- 103 events from one archive of undefined relation to the published release; no generalisation
  beyond it.
- The beyond-size feature was identified post hoc on the same events.
- 27.5% of texts withheld, unevenly by class.
- Mild event dependence through repeated hashtags.
- Partition variability comparable to event uncertainty.
- BA contrasts uninterpretable.
- The rewiring null tests only a narrow set of properties.
- Labels come from file names.
- No account identifiers or subtypes.
- Uniform edge sampling is one observation model among many.

---

## Part VII — Stopping assessment

**Are there critical analyses that must still be completed before manuscript development? No.**

All four robustness questions are answered with the evidence above:
- event influence: no single event is decisive; the gain is tail-borne;
- split stability: direction stable, magnitude variable;
- content: real beyond structure; one feature; not a retention artefact;
- flexible baselines: survives LR baselines, unresolved against QDA.

The remaining uncertainties (provenance, independent replication) cannot be resolved with this
archive.

**Recommendation: move to paper development now.** Experiment 1 is worth running *before writing
the Discussion* if you want the Study 1–Study 2 bridge to extend to the content residual. It is
small, but it is optional, not blocking. If you do not run it, state the question as future work.
Do not run further robustness checks; the marginal value is now low and the risk of exploratory
drift is real.

The `INVESTIGATION_LEDGER.md` was left unchanged, to preserve the earlier audit record. If you want
it updated, the new rows would be:
- Study 1 split stability (RESOLVED);
- event influence (RESOLVED);
- content verification and text availability (RESOLVED);
- flexible count baselines (RESOLVED; QDA comparison UNRESOLVED).
