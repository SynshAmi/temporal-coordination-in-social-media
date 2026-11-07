# Final manuscript plan

This plan consolidates three sources: `manuscript_blueprint.md`, `AUTHOR_DECISIONS.md` and the external editorial report *Manuscript Framing and Writing Strategy.md*. It also uses the other files in this folder.

**Precedence when sources disagree:**
1. Verified artifacts. `paper/main.tex` and `paper/generated/results.tex` are authoritative for existing manuscript values; the audit outputs are authoritative for added rows.
2. `AUTHOR_DECISIONS.md`.
3. `claim_ledger.md`, `contradictions.md` and `contrast_inventory.md`.
4. `manuscript_blueprint.md`.
5. The editorial report, which is guidance on presentation only.

Agreement between AI-written documents is not treated as evidence. Every value below is copied from `claim_ledger.md`, `AUTHOR_DECISIONS.md` or `contrast_inventory.md` with its artifact. Nothing was computed for this plan.

**Status labels** (defined in Methods and used in every table and caption):

| Label | Meaning | Applies to |
|---|---|---|
| **Primary** | Specified before the corrected run (not preregistered) | Study 1 C1–C3 on partition 42, with Holm over each 3-test family |
| **Sensitivity** | Same question, different partitioning, exclusion or baseline | 20 partitions, grouped folds, exclusions, flexible count baselines, row order |
| **Exploratory** | Planned but not part of the primary family | E1–E3, the degree-preserving null, all edge-limited contrasts not involving `token_std` |
| **Post hoc** | Chosen after inspecting results on these events | Everything singling out `token_std`: counts + `token_std`, models B and D |

---

## 1. Title

- **Working title:** *How Far Do Node and Edge Counts Go? Predicting Campaign Labels in Engagement Graphs Under Full and Edge-Limited Observation*
- **Alternative:** *Counts First: Structural and Message-Level Predictors of Campaign Labels in a 103-Graph Engagement Archive*

**Why this title:**
- It is the editorial report's first title, changed from "graph counts" to "node and edge counts" so the term is defined (K02).
- It makes no claim that the data are LEN-Small (K01).
- It does not foreground `token_std`, which is post hoc.
- Retired: "What Does LEN-Small Measure?" and "Beyond Scale" (P01).

## 2. Research question

**Assessment of the proposed question.** "How much label predictability can be recovered from graph counts, and what adds to it under full and edge-limited observation?" is the right question, with three refinements:

1. **"Recovered" implies a known total.** Use "predicted from".
2. **"Graph counts" must be defined for both regimes.** On a full graph the counts are n and m. In a view of exactly K edges, m is fixed by design, so the only count left to vary is the view's node count, N_K (distinct sampled endpoints). This is what links the two regimes. The answer to "what remains predictable with a fixed edge budget" begins with the observation that a count is still present.
3. **"What adds to it" must allow "nothing established".** For several feature families that is the answer.

**Final RQ.** In an archive of 103 engagement graphs, how well can the campaign label be predicted from node and edge counts, and what, if anything, adds to that prediction?
- **RQ1 (full observation):** counts, and degree, arrangement and content features added to them.
- **RQ2 (edge-limited observation):** the view's node count N_K under a fixed edge budget K, and structural and message-level statistics added to it.

**What the evidence answers:**
- **Counts:** strongly predictive in both regimes.
- **Full graphs:** the combined feature set improves log loss and AUC over counts. No single family has an established increment over counts alone.
- **Edge-limited views:** N_K remains highly predictive. Structure added to N_K shows no detectable change. Message-length dispersion added to N_K is directionally favourable, but uncertain and post hoc.

The "why" (collision-dependent statistics) is part of the answer, not a separate RQ.

## 3. Central argument

In this archive, node and edge counts alone predict the campaign label well, so any richer feature has to be judged against them.
- **Full graphs.**
  - The combined feature set improves probabilistic prediction over counts (log loss and AUC). There is no detectable gain in balanced accuracy.
  - Neither the structural nor the content features, added to counts on their own, show an established gain.
  - Structural features help only alongside content (exploratory).
- **Edge-limited views.** Fixing the number of observed edges does not remove count information. The view's node count N_K is a function of K and the full graph's degree sequence, so it remains highly predictive, and the structural features computed on a view largely track it.
- **Message-length dispersion.**
  - Collision-dependent statistics change meaning with K. A statistic computed edge by edge, such as the standard deviation of message token counts, estimates the same full-graph quantity at every K, and its view values track its full-graph values.
  - Whether it adds predictive value beyond N_K is a separate question. The answer is directionally favourable but uncertain, it varies by budget and cohort, it rests on retained text only, and the statistic was selected post hoc on these events.
- **Scope.** The paper's firm result is about counts. The message-level result is a lead for independent testing.

## 4. Contributions

Prose, not bullets. No "first" or "novel".

1. **A count-first evaluation of nested feature sets on full graphs**, with pre-specified contrasts, the BA and probabilistic metrics reported separately, and sensitivity to partitioning.
2. **An edge-limited evaluation that names the count still present in a fixed-K view (N_K)**, explains why it remains predictive (E[N_K] is determined by the degree sequence), and separates threshold effects from ranking in transfer comparisons.
3. **A comparison of collision-dependent and edge-by-edge statistics under uniform edge sampling.** Measurement agreement and incremental predictive value are reported as separate results.
4. **A documented description of the archive analysed:** its composition, text retention by class, and its differences from the published LEN-Small description.

Dropped from earlier drafts:
- "Complementary information" (K07).
- "Training regime matters more than features" (K09).
- Any coordination finding (K16).

## 5. Section-by-section outline

Page estimates assume the current IEEE two-column format, about 10 pages including figures. Whether references count toward the limit is unresolved (§12).

**Lead metric.**
- Log loss leads for incremental comparisons; AUC is reported next to it.
- BA is reported as the threshold-based decision metric. It is never cited as evidence of added information when AUC and log loss disagree (K04).
- Both the BA and log-loss C1–C3 families were pre-specified, and both are reported.

**Headings.** The paper does not use "Study 1" and "Study 2". It uses "full observation" and "edge-limited observation" (editorial report).

### 5.1 Introduction (about 1.0 page)

- **Purpose:** pose the problem and the RQ, state the data position, and preview the findings with status labels.
- **Question answered:** why should a reader check a classification score on engagement graphs against counts?
- **Allowed claims:** P12 scope; P14 (median nodes 3,227 vs 506); the RQ; three findings, each labelled.
- **Evidence:** none beyond one number per finding.
- **Supplement:** nothing.

Paragraph plan in §11.

### 5.2 Related work (about 0.5 page)

- **Purpose:** place the paper. This is not a survey.
- **Question answered:** what is already known about simple baselines, dataset construction and sampling, and what this design adds?
- **Allowed claims:**
  - The LEN and DECODE task (`len`, `decode`, `repo`).
  - Official counts, as the sources state them (P17), cited directly with access date (A09 is UNVERIFIED locally).
  - Simple baselines and benchmark critique (`li`, `errica`, `coupette`).
  - Graph sampling distorts statistics (`leskovec`).
  - Degree-preserving nulls (`maslov`).
  - Small-sample cross-validation (`varoquaux`).
  - Measurement framing (`jacobs`).
- **Not allowed:** claims that no prior work exists.
- **Supplement:** nothing.
- **Open:** whether to add the sampling and dataset-construction papers named in the editorial report (§12).

### 5.3 Data and provenance (about 0.75 page)

- **Purpose:** define what every claim applies to.
- **Question answered:** what exactly was analysed?
- **Allowed claims:**
  - 104 files → 103 canonical graphs (52 campaign / 51 comparison); labels from file names; directed simple graphs with self-loops (P18, P20).
  - The archive differs from the published LEN-Small tables in membership and content. Cite individual mismatching graphs (A02, individual counts only). The stated selection rule conflicts with the published tables (A01).
  - Node identifiers are per graph, so cross-event account overlap cannot be measured (P21).
  - 27.5% of edge texts are null; usable share 0.58 (campaign) vs 0.80 (comparison); two campaign graphs have no usable text (R12, T01).
  - Class size difference (Table 1, Fig. 1).
- **Not allowed:**
  - "LEN-Small plus three", or any superset wording (P02, P19).
  - The 17/25 and 14/25 tallies (A02), 92.66% overlap (A03), or 14/25 self-loop matches (A10).
- **Supplement:** member list; individual mismatches.

### 5.4 Methods (about 1.75 pages)

- **Purpose:** make each comparison traceable without narrating the audit.
- **Question answered:** what was compared, on which events, with which uncertainty?

**Contents, in order:**
1. **Feature ladder (Table 2).**
   - Counts: log n and log m (M0), plus squares and product (M0q). Mean degree m/n and density are functions of these (P22, K02).
   - Degree concentration: in- and out-degree Gini.
   - Arrangement: reciprocity, largest-WCC fraction, median and max coreness.
   - Content: duplicate fraction, frequency Gini, `token_std`.
   - A column marks each feature as **collision-dependent** (its view value depends on how often sampled edges share endpoints) or **edge-by-edge**.
2. **`token_std` definition** (T01):
   - per edge, repeats kept;
   - null texts dropped;
   - lower-case, remove `https?://\S+`, collapse whitespace;
   - whitespace tokens;
   - sample SD (ddof 1); 0 if one text, undefined if none;
   - training-fold median imputation;
   - verified against the raw archive (max difference 0.0 on full graphs, 3.6e-15 on views).
3. **Full observation:**
   - nested models M0–M4; C1 = M4 − M0q, C2 = M2 − M1, C3 = M3 − M0q;
   - pre-specified, not preregistered, with the earlier analysis of the same archive disclosed (P23);
   - separately tuned BA and log-loss fits; inner-CV tuning; no leakage found (P24, A11).
4. **Uncertainty:**
   - event-level paired bootstrap of fixed out-of-fold predictions (2,000 resamples);
   - Holm within each named family;
   - 20 outer partitions as sensitivity, stated as reusing the same events (K14).
5. **Degree-preserving null.** One sentence on its blind spot: it preserves every degree-sequence functional, including E[N_K] (P08, A06, K15). Details go to the supplement.
6. **Edge-limited observation:**
   - K ∈ {250, 500, 1000}; uniform edge sampling; seeds 100–109;
   - budget-specific cohorts 102 (51/51), 98 (48/50) and 73 (28/45); the common cohort is the K = 1000 cohort;
   - regimes KK, FF and FK; models A–D;
   - 1,000 bootstrap resamples, with Holm across K.
   - Uniform sampling is a controlled probe, not a model of platform API sampling.
7. **E[N_K] as a function of K and the degree sequence (one equation),** and why it makes N_K a count.
8. **Post-hoc status:**
   - `token_std` was singled out after examining full-graph results on these events.
   - Holm across K does not adjust for that selection (K05).
   - Models B and D on the common cohort below K = 1000 were not computed.

**Supplement:** null-model diagnostics; tuning grids; row-order and tie-break sensitivity; leakage checks; the full verification record.

### 5.5 Results (about 3.75 pages)

Each subsection opens with the finding and closes with the question that opens the next.

#### R1. Counts (about 0.5 page)

- **Question:** how much do counts alone predict?
- **Claims:**
  - LR on log node and edge counts reached BA 0.884 on the primary partition (mean over 20 partitions 0.864), AUC 0.931 (P03, A14).
  - Node count alone: BA 0.874 (P24).
- **Evidence:** Table 3 panel A; Fig. 1.
- **Supplement:** performance by feature level, LR and HGBT (S2).

#### R2. What adds to counts on full graphs (about 1.25 pages)

- **Question:** do degree, arrangement or content features improve prediction beyond counts?
- **Claims, in this order:**
  1. **C1, primary.**
     - Log loss −0.110 [−0.181, −0.039], Holm 0.009 (3 tests).
     - Sensitivity: −0.094 [−0.172, −0.013], unadjusted, with the same direction in 19 of 20 partitions of the same events. Use the wording in AUTHOR_DECISIONS §1.
     - AUC +0.039 [+0.009, +0.075], unadjusted.
     - BA +0.010 [−0.049, +0.076], Holm 1.000: no detectable gain. BA moves by about 0.01–0.02 with tuning tie-breaks (P04, A04).
  2. **By family** (AUTHOR_DECISIONS §2 wording):
     - structure added to counts: no detectable change (+0.002 [−0.048, +0.053]);
     - degree concentration added to counts: worse in every partition (+0.040 [+0.027, +0.053]);
     - three content features added to counts (C3): no detectable change (−0.019 [−0.136, +0.118], Holm 1.000);
     - structure added to counts plus content (E2): −0.059 [−0.110, −0.011], 20 partitions, exploratory (primary partition −0.091 [−0.182, −0.018]);
     - content added to counts plus structure (E3): −0.096 [−0.165, −0.032], exploratory.
  3. **Post hoc, single feature:**
     - counts + `token_std` vs counts: −0.080 [−0.160, +0.004], with AUC +0.031 [+0.003, +0.068] (R11);
     - M4 vs counts + `token_std`: no detectable difference, −0.014 [−0.055, +0.024]; equivalence not tested (R10, K12).
  4. **The gain is concentrated in a minority of events but not driven by one** (R03–R05):
     - leave-one-event-out range −0.106 to −0.070;
     - the 10 events most favourable to M4 contribute 94% of the net gain.
  5. **Without the two no-text events:** C1 −0.083 [−0.171, +0.008], the same direction with an interval that includes zero. AUC (+0.033 [+0.004, +0.069]) and E3 (−0.087 [−0.158, −0.015]) keep intervals excluding zero (AUTHOR_DECISIONS §3).
  6. **Against the most flexible count baselines, the gain is not established** (R16). One sentence.
  7. **Degree-preserving null:** no detectable difference for arrangement features. Give two key numbers (P34) and the blind spot.
- **Evidence:** Table 3.
- **Supplement:**
  - partition stability (S5); per-event contributions (S6); flexible baselines (S7); null table (S4);
  - grouped folds, −0.082 [−0.164, +0.005] (R06);
  - wider C grid (P31); row-order sensitivity (P30); HGBT (P32); size matching (S13).
- **Closing question:** if counts carry most of the signal, does fixing the number of observed edges remove it?

#### R3. Edge-limited observation: the count that remains (about 1.0 page)

- **Question:** what is predictable when exactly K edges are observed?
- **Claims:**
  - In a fixed-K view, the node count N_K alone predicts the label: AUC 0.961, 0.952 and 0.890 at K = 250, 500 and 1000 (budget-specific cohorts, KK).
  - **E[N_K] is a function of K and the full graph's degree sequence.**
    - It matches the observed mean N_K within 3.5% at K = 250.
    - Its log is 77.2% explained by n, and 93.0% by n and mean degree (P10, P41).
    - It is invariant under the degree-preserving null (A06).
  - **Structural features on views largely track N_K** (R² for log N_K 0.92–0.95), and adding them to N_K gives no detectable change (C − A, all K; contrast_inventory).
  - **Single views were not detectably less predictive than full graphs** on the same events. At K = 1000 the BA difference is a threshold effect: AUC 0.953 vs 0.951 (P09, A05).
  - **Retraining vs transfer** (one paragraph, P11 wording, with AUC): for N_K, frozen transfer collapses at the threshold (BA 0.500, AUC 0.942); for the six structural features, AUC is 0.767 trained on full graphs vs 0.947 trained on views.
- **Evidence:** Fig. 2 (mechanism); Table 4 rows A and C.
- **Supplement:** single-view BA on the common cohort (S8); retraining and transfer table with AUC (S9).
- **Closing question:** is there a statistic whose meaning does not change with K, and does it add anything to N_K?

#### R4. Message-length dispersion (about 1.0 page)

- **Question:** does an edge-by-edge statistic add to N_K?
- **Claims, in this order:**
  1. **Measurement.** View values tracked full-graph values (ρ ≥ 0.995), as expected for a per-edge statistic estimated from hundreds of edges; at K = 1000 a view covers most edges of a typical campaign graph (K06). One or two sentences; it is not a finding.
  2. **Class difference (descriptive).** Campaign graphs had lower `token_std`. Univariate AUC is 0.78, 0.77 and 0.81 in views, the same as on full graphs (V02).
  3. **Incremental value (post hoc)** (V04, V05, V06):
     - B − A and D − C by K, log loss with AUC.
     - Log-loss direction favours B and D in 10 of 10 sampling seeds at every K. The seeds share events.
     - Intervals include zero at K = 250 and 500.
     - At K = 1000, use the AUTHOR_DECISIONS §4 wording: B − A −0.114 [−0.218, −0.011] and D − C −0.138 [−0.208, −0.076]; not compared; C has the highest log loss of the four.
  4. **No budget-dependence claim.** Cohort composition changes with K, and B and D were not computed on the common cohort below K = 1000 (contrast_inventory (b), (c)).
  5. **The planned three-feature content contrast** (combined − C), reported in log loss and BA and kept numerically separate from `token_std` (K10, P38):
     - log loss −0.067, −0.127, −0.173, uncorrected;
     - intervals exclude zero at K = 500 and 1000.
  6. **Text availability** (one paragraph):
     - Retention differs by class.
     - Within comparison events, views with more usable text had lower `token_std` (ρ −0.36 to −0.50).
     - Class separation by `token_std` remained within strata of text availability (AUC 0.77–0.93; descriptive).
     - Excluding the two no-text events changed Δ log loss by ≤ 0.014 in 5 of the 6 primary contrasts (D02–D05).
- **Evidence:** Table 4; Fig. 3.
- **Supplement:** view vs full scatter (S10); text availability (S11); exclusion (S12); 10-partition sensitivity (V09); FF reference contrasts (V08).

### 5.6 Discussion (about 1.0 page)

Interpretation only; no new numbers.
1. **Counts first.**
   - In this archive, most of the predictability comes from n and m.
   - The added features improve probabilistic prediction, not decisions (no detectable BA gain).
   - Practical implication: evaluations on these data should report a count-only baseline and separate metrics (P43).
   - Competing readings of the size–label association, unresolved here: event popularity, the archive's selection, and real differences between events.
2. **Structure is conditional, not absent.**
   - No detectable change added to counts or to N_K.
   - Exploratory improvement alongside content.
   - The null cannot see degree-sequence information.
   - Do not say "uninformative".
3. **Why a fixed edge budget does not remove size.** N_K re-encodes the degree sequence, and the view's structural features track it. Uniform sampling is a probe. Real API sampling differs.
4. **What message-length dispersion is and is not.**
   - A statistic of token-count variation on retained text.
   - Alternative explanations, stated as hypotheses: topic or event-type differences, text retention, cleaning choices.
   - What would test it: independent events, and a common-cohort evaluation across K.
   - No coordination or templating reading (K16).

### 5.7 Limitations (about 0.5 page)

See §9. One short paragraph per group. Limits already stated beside a result are referenced, not repeated in full.

### 5.8 Conclusion (about 0.25 page)

Answer the RQ in three sentences mirroring the Introduction's findings, with status labels, then two next steps: the official release and its selection list, and an independent test of `token_std`.

### 5.9 Verification, corrections and data availability (about 0.25 page)

- **Keep:**
  - the coreness and fold-assignment corrections, covered by regression tests (P47);
  - the independent recomputation script, 21/21 checks (P48);
  - the code and data location.
- **Drop:** the "complete rerun reproduced every value" sentence (P49), unless `reports/reproducibility/REPRODUCIBILITY_REPORT.md` is checked first.
- The record of retired claims goes to the supplement. One main-text sentence points to it.

**Approximate total:** 9.75 pages plus references.

## 6. Main-paper figures and tables

Four tables and three figures. Every value exists. "Assemble" means copying existing values into a table, with no computation. No item needs a cell marked NOT COMPUTED except where the table states that explicitly.

| # | Title | Communicates | Why necessary | Source | Status |
|---|---|---|---|---|---|
| **Table 1** | Archive and cohorts | What the claims apply to: 103 graphs (52/51), node and edge medians by class, usable-text share by class (0.58 / 0.80), no-text graphs (2), and the edge-limited cohorts by K with class split | Every result is scoped to this archive; the cohort change with K must be visible from the start | `results.tex` `\RTabCohort`; `s01_content_verification.json`; contrast_inventory cohorts | Exists; add the text and cohort rows; replace "Official LEN-Small" wording |
| **Table 2** | Feature ladder | Each feature, its family, and whether it is collision-dependent or edge-by-edge; which models (M0–M4, A–D) contain it | Carries the device that links the two regimes. It replaces Methods prose, so it saves space | Definitions in `main.tex` §Features and `token_std_verification.md` §2 | Assemble from existing definitions (no results) |
| **Figure 1** | Node and edge counts by class | The class size difference and its overlap, seen directly | The counts-first argument needs the reader to see why counts predict, and why not perfectly | `paper/figures/fig1_size_distributions.pdf` | Exists; single column. **First item to move to the supplement if over length** |
| **Table 3** | Full observation: counts and what adds to them | Panel A: M0q and M4, absolute BA, log loss and AUC, primary and 20-partition mean. Panel B: Δ log loss and ΔAUC (with ΔBA for C1–C3), primary and 20-partition columns, for C1, C2, C3, M2 − M0q, E1, E2, E3, the 101-event C1, and the post-hoc rows (counts + `token_std` vs counts; M4 vs counts + `token_std`) | One table answers RQ1 with every status label visible | `paper_results.json`; `s02_performance.csv`; `s02_contrasts.csv`; `s04_posthoc_lensd.json` | Assemble. Cells absent from the artifacts (for example M2 − M0q on the primary partition) are shown as "—", not filled |
| **Figure 2** | Endpoint occupancy | E[N_250] against node count, with R² inset: N_K is set by the degree sequence | The "why" of R3; it turns "views remain predictive" into a mechanism | `paper/figures/fig4_endpoint_mechanism.pdf` | Exists |
| **Table 4** | Edge-limited observation: models A–D by K | Log loss, AUC and BA for A–D (KK, budget-specific cohorts, n and class split per K), then B − A, D − C (post hoc) and C − A beneath. Footnotes: post hoc; Holm across K only; B and D not computed on the common cohort below K = 1000; C's log loss at K = 1000 | Answers RQ2 in one place, and keeps cohort sizes beside every budget | `v02_performance.csv`; `v02_contrasts.csv`; `outputs/run_v2/study2/results.json` | Assemble |
| **Figure 3** | `token_std` contrasts by K | B − A and D − C, Δ log loss and ΔAUC with intervals, full-graph reference marked; cohort n on the axis; "post hoc" in the panel title | Shows direction and uncertainty together; makes the overlapping K = 1000 intervals visible | `research_audit/outputs/v02_fig2_contrasts.png` (data `v02_fig2_data.csv`) | Exists. A re-plot from the CSV for print, dropping or greying BA, is formatting only |

**Considered and not placed in the main text:**

| Item | Reason |
|---|---|
| Study 1 contrast graphic (`fig2_study1_contrasts.pdf`) | Duplicates Table 3. Moved to the supplement |
| Single-view BA figure (`fig3_study2_single_view.pdf`) | BA only, and duplicates Table 4 |
| View vs full `token_std` scatter (the editorial report's Fig. 3 panel A) | In the main text it reads as a finding. It is an expected sampling property (K06; AUTHOR_DECISIONS §5). One sentence in R4 instead |
| Separate observation-conditions table (the editorial report's Table 3) | Regime results are a paragraph plus S9. A table would add a fifth table for a secondary diagnostic |

**Change from AUTHOR_DECISIONS §5.** That file listed 3 tables and 2 figures. This plan adds the following, with no new values:
- **Table 2 (feature ladder),** from the editorial report.
- **Figure 1 (size distributions),** promoted from supplement S1 because the counts-first narrative now leads the paper.

## 7. Supplementary material

| # | Item | Source |
|---|---|---|
| S1 | Archive member list and individual mismatches with published tables | `manifest.parquet`; `a01_archive_members.csv` |
| S2 | Full-observation performance by feature level, LR and HGBT, primary and 20-partition | `\RTabLevels`; `s02_performance.csv` |
| S3 | Full-observation contrast graphic | `fig2_study1_contrasts.pdf` |
| S4 | Degree-preserving null: table and coverage diagnostics | `\RTabNull`; P33, P35 |
| S5 | C1 across 20 partitions | `s02_fig1_split_stability.png` |
| S6 | Per-event contributions to C1 (caption without "influence") | `s03_fig_event_influence.png`; `s03_exclusions.csv` |
| S7 | Flexible count baselines (polynomial, spline, QDA); wider C grid | `s02_contrasts.csv`; `outputs/revision_h1_cgrid/` |
| S8 | Single-view BA, common cohort | `fig3_study2_single_view.pdf` |
| S9 | Retraining and transfer, with AUC | `study2/results.json`; `a04_study2_diagnostics.csv` |
| S10 | View vs full `token_std` (measurement check) | `v02_fig3_view_vs_full.png` |
| S11 | Text availability by class and K; `m_K/K` vs `token_std`; stratified class separation | `v02_fig1_text_availability.png`; `d01_*` |
| S12 | Edge-limited exclusion of the two no-text events | `d02_comparison_with_original.csv` |
| S13 | Exploratory size matching (point estimates without intervals) | `\RTabMatching` |
| S14 | 10-partition sensitivity for B − A and D − C; FF reference contrasts | `v02_contrasts.csv` |
| S15 | Sensitivity notes: grouped folds; row order and tuning tie-breaks | `s02_results.json`; `paper_results.json` |
| S16 | Verification and corrections record, including retired claims | this folder; `verification_report.json` |

## 8. Claim boundaries

**Can conclude** (in this archive, as predictive association):
- Node and edge counts predict the file-name label well (primary partition BA 0.884, AUC 0.931).
- Adding degree, arrangement and content features to counts lowered log loss on the pre-specified partition (−0.110, Holm 0.009), with the same direction in 19 of 20 partitions (−0.094 averaged). No BA gain was detected.
- Neither structure nor the three-feature content set, added to counts alone, produced a detectable change. Structure added alongside content did (exploratory).
- In fixed-K views, N_K is a degree-sequence quantity and remains highly predictive. Structural features on views largely track it.
- `token_std` view values track full-graph values (a measurement property).
- Adding `token_std` was associated with lower log loss in every budget and seed direction, with intervals excluding zero only at K = 1000 (post hoc).

**Cannot conclude** (consolidated from the blueprint, K01–K19 and AUTHOR_DECISIONS):
1. That the archive is LEN-Small, the official release, or the release plus three events.
2. That LEN-Small is the 100 smallest graphs, as a fact.
3. Anything about account overlap or cross-event identities. Do not cite 92.66% or any overlap figure.
4. Any causal relation: "drives", "influences", "explains", "corrects".
5. That topology or structure "contributes nothing", "contains no information" or "is uninformative".
6. That counts plus `token_std` is "equivalent" or "indistinguishable" from M4.
7. That `token_std` "accounts for" or "carries" the content gain. The post-hoc evidence is suggestive (R10, R11), not established.
8. That `token_std` measures coordination, templating, linguistic structure or intent.
9. Any `token_std` result as confirmatory, established or significant without "post hoc".
10. That `token_std`'s added value grows with K, is absent at small K, or is larger beyond structure than beyond N_K.
11. That D is the best model, or any ranking of B against D.
12. That sampling "preserves information", improves classification, or models platform APIs.
13. "Training regime matters more than features".
14. BA differences as effects, or BA significance as evidence of added information.
15. "Complementary information" or an interaction explanation of E2.
16. Repeated partitions or sampling seeds as replications.
17. "Survives", "robust to" or "unchanged by" exclusion, for C1 log loss.
18. Predictive performance as information content (no bits, no mutual information).
19. Any UNVERIFIED value: A02 tallies, A03, A09 (without a dated source), A10, R13's 0.64 (use 0.62 from `s02_results.json` or omit), R14's means 7.9 / 9.9, and P49.
20. Comparing our BA directly with published GNN accuracy.

## 9. Limitations and how to present them

**Placement.**
- State each limit beside the result it affects, in one clause.
- Consolidate in §5.7 in seven short paragraphs. Each names the limit and what it constrains. No generic disclaimers.

| Group | Limit | What it constrains | Beside which result |
|---|---|---|---|
| Provenance | Archive not established as LEN-Small. Selection undocumented, and the stated rule conflicts with the published tables | Generalisation beyond these 103 graphs. Size–label associations may reflect selection | Data; Discussion ¶1 |
| Sample and uncertainty | 103 events (73 at K = 1000). Bootstrap intervals exclude refitting; partition variability is comparable (SD 0.035 vs 0.040). Two hashtags appear twice (grouped folds −0.082 [−0.164, +0.005]). No account identifiers, so dependence is unmeasurable | Null results are inconclusive, not equivalence. Intervals may be too narrow | R2 C1 paragraph |
| Post-hoc selection | `token_std` was chosen on these events, with no independent sample. Holm across K does not address the selection | Its incremental value is a hypothesis | R2 item 3; R4 |
| Text retention | Computed on retained text only. Retention 0.58 vs 0.80 by class; two graphs have none (imputed); within-class association with usable-text count; cause of missing text unknown | What `token_std` measures cannot be separated from retention | Data; R4 item 6 |
| Edge-limited design | K confounded with cohort. B and D absent on the common cohort below K = 1000. Comparator C has poor log loss at K = 1000. Uniform sampling only | No budget-dependence claim, and no claim about real API data | R3; R4 items 3 and 4 |
| Null model | Mixes incompletely; rarely changes median coreness; five realisations; blind to degree-sequence functionals | The arrangement null result is narrow | R2 item 7 |
| Models and scope | LR (and secondary HGBT) on hand-crafted features; no GNN or published LEN methods. BA depends on tuning tie-breaks and row order. Predictive association only | No claim about learned models or mechanisms | Methods; Discussion |

## 10. Writing principles

1. **One question, returned to.** Open each Results subsection with the part of the RQ it answers, and close it with the question the next subsection takes up.
2. **Finding first.** Begin a Results paragraph with what was found, then give the evidence.
3. **Firm where the evidence is firm.** Counts and C1 are stated plainly. Hedging is reserved for interpretation and post-hoc results. Do not hedge every sentence.
4. **Status label on first mention, in every table row and every caption:** Primary, Sensitivity, Exploratory or Post hoc.
5. **Fixed terms.** Use these and only these:
   - "counts" (n, m) and "N_K" (view node count);
   - "degree concentration" (Gini) and "arrangement";
   - "content" and "`token_std`" or "message-length dispersion" (pick one for the prose and keep it);
   - "full observation" and "edge-limited observation";
   - "partition", never "split" and "fold" interchangeably.
6. **Predictive verbs only:** "predicts", "is associated with", "changed log loss by".
7. **Non-significance wording:** "no detectable change; the interval [a, b] is compatible with …". Never "no effect".
8. **Numbers once.** Put a value in a table, and cite it in prose only where the argument needs it. Every interval names its method and adjustment on first use.
9. **The audit stays out of the narrative.** One Methods sentence on verification, with the record in the supplement. No "we initially …".
10. **Short paragraphs, one point each.** Plain words. Define a technical term once, where it first matters.
11. **Neutral provenance language.** No speculation about why the archive differs, and no fault attributed to LEN's authors.
12. **No "first", "novel" or "unique".**

## 11. Introduction, paragraph by paragraph

Six paragraphs, about one page. The RQ arrives in ¶4. The available citations are the existing `references.bib` keys. Any addition needs author verification (§12).

| ¶ | Point | Content | Citations | Transition into the next ¶ |
|---|---|---|---|---|
| 1 | What a score on engagement graphs is taken to mean | LEN poses campaign vs organic classification on engagement graphs, and graph models are evaluated on it. A high score invites the reading that the model has learned something about how campaigns spread. That reading depends on what the labels can be predicted from. No generic opening about social media. No published accuracy figures unless checked against the source | `len`, `decode` | "What else could a high score reflect?" |
| 2 | The tension: size | Graph-classification benchmarks are often matched by simple baselines. In the archive analysed here, comparison graphs are several times larger than campaign graphs (median nodes 3,227 vs 506). So the first quantity to measure is what node and edge counts alone achieve | `li`, `errica`, `coupette`; P14 | "Full graphs are not the only way such data are observed." |
| 3 | Observation as a second problem | Engagement data are usually observed partially. Fixing the number of observed edges looks like a way to hold size constant, but sampling changes graph statistics. Uniform edge sampling is used as a controlled probe, not as a model of any platform's sampling | `leskovec` | "Does a fixed edge budget remove size?" |
| 4 | The research question | The RQ with RQ1 (full) and RQ2 (edge-limited). The unit is the event graph, and the claims are predictive. Out of scope: accounts, coordination mechanisms, learned graph models | — | "We address it on one archive whose status needs stating." |
| 5 | The data position | 103 event graphs downloaded from the LEN project website. Their relation to the published 100-graph LEN-Small subset could not be established: membership and content differ, and the published selection rule conflicts with the published tables. All claims are about this archive | `repo`, `len` | "On this archive, we find …" |
| 6 | Findings and contributions | Three findings in RQ order, each with its label:<br>(1) counts predict strongly (BA 0.884);<br>(2) the combined feature set improves log loss over counts (−0.110, pre-specified; same direction in 19/20 partitions), with no detectable BA gain and no established gain from any single family;<br>(3) in fixed-K views N_K remains predictive because it reflects the degree sequence; message-length dispersion, chosen post hoc, tracks its full-graph value and is directionally but uncertainly associated with lower log loss.<br>Then the contributions as prose (§4). No section roadmap unless the venue requires one | — | Into Related work |

**Keep out of the Introduction:**
- Coordination mechanisms.
- `token_std` effect sizes.
- Criticism of LEN.
- Claims about GNNs in general.
- The audit history.

**Self-test.** A reader who stops after ¶6 can say:
- what is asked;
- what data are used and what their status is;
- which result is firm (counts) and which is tentative (message-length dispersion).

## 12. Source disagreements and how they were resolved

| Topic | Disagreement | Resolution and authority |
|---|---|---|
| What adds on full graphs | The editorial report says message-length dispersion "accounts for most of the content gain". The blueprint abstract says the improvement is "concentrated in one content statistic" | Neither holds. Counts + `token_std` vs counts is −0.080 [−0.160, +0.004], an interval including zero; the difference from M4 was not detected but equivalence was not tested (R10, R11). Use R2 item 3 wording |
| Stability vs utility | The editorial report (narrative step 4) says the statistic "retains predictive value under sampling" | Split into the measurement (ρ ≥ 0.995) and incremental value (post hoc, uncertain) (K06) |
| Visual for `token_std` | The editorial report puts the view-vs-full scatter as Fig. 3 panel A. AUTHOR_DECISIONS keeps it out of the main text | AUTHOR_DECISIONS. One sentence in the main text; S10 in the supplement |
| Size-distribution figure | Main text in the editorial report; supplement in AUTHOR_DECISIONS | Main text (Figure 1), because the narrative now leads with counts. Marked as the first item to move if over length |
| Results headings | The blueprint has two Results sections (Results I and Results II); the editorial report has one section in four steps | One Results section in four steps (R1–R4), using the blueprint's paragraph content |
| Discussion wording | The blueprint ¶7.2: "why sampling preserves label information" | Reworded as "why a fixed edge budget does not remove size". "Preserves information" is a banned phrase |
| C1 interval | The paper gives [−0.181, −0.039]; the audit re-bootstrap gives [−0.184, −0.039] | Use the paper's value (AUTHOR_DECISIONS §1) |
| Missingness AUC | The robustness report gives 0.64; the artifact gives 0.622 | 0.62 from `s02_results.json`, or omit (R13) |
| "Survives exclusion" | The robustness report, Part I vs Part C.3 | The interval includes zero; use the AUTHOR_DECISIONS §3 wording |
| Topology | "Contributes nothing" (robustness report) vs E2 | Both statements are conditional; use the AUTHOR_DECISIONS §2 wording |
| Opening paragraph | The blueprint ¶1.1 opens on benchmarks as coordination evidence; the editorial report opens on what a score is taken to mean | The two merge in §11 ¶1. Coordination appears only as the reason scores get read that way |
| Provenance placement | The blueprint has it in Introduction ¶2; the editorial report has it after the RQ | After the RQ (¶5), so the problem and question come first. It is still stated before any finding |

## 13. Decisions that still require author input

1. **Venue and length rules.** Is the target about 10 pages including references, and are a Corrections section and an online supplement allowed? Page estimates and Figure 1's place depend on this.
2. **Literature additions.** The editorial report names five papers not in `references.bib`: Hays et al. 2023, Morstatter et al. 2013, González-Bailón et al. 2014, Pfeffer et al. 2018 and Pacheco et al. 2021. They would support Intro ¶2–3 and Related work. Each needs reading and citation checking by you before use. The report itself flags the Nizzoli et al. citation as unconfirmed, and it is not recommended here.
3. **Official LEN counts (A09).** They have no local snapshot, so they must be cited from the sources with an access date, or the 314 vs 305 detail dropped.
4. **The reproducibility sentence (P49).** Check `reports/reproducibility/REPRODUCIBILITY_REPORT.md`, or drop it.
5. **The Corrections section.** Was the earlier manuscript version circulated publicly? If not, the corrections can move entirely to the supplement.
6. **Contact with LEN's authors.** Has anyone written to them about the archive's composition? If a reply exists, the provenance wording in Data and Limitations may change.
7. **Lead metric.** Confirm that log loss leads the text, with BA reported as the secondary decision metric. The current abstract leads with BA. Both families were pre-specified, so this is a presentation change only.
8. **Title.** Choose between the working title and the alternative (§1).
9. **Prose name for `token_std`.** "Message-length dispersion" or "token-count dispersion". The second is more literal, since lengths are counted in whitespace tokens.
