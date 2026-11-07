# Manuscript blueprint (outline only, no prose)

**Working question.** In this archive, how much label predictability is recoverable from counts, which statistics retain incremental predictive value under edge-limited observation, and why?

**Unifying idea.** Two kinds of statistic behave differently when only K uniformly sampled edges are observed:
- **Collision-dependent statistics.** Their value depends on how often sampled edges share endpoints. Examples are N_K (distinct endpoints), and degree Gini, reciprocity, component and coreness computed on the view. Their expectation is a joint function of K and the full graph's degree sequence (E[N_K], eq. 3), so their meaning changes with K and they track N_K within a view.
- **Edge-by-edge statistics.** An example is `token_std`, a per-edge attribute summarised over the sampled edges. A uniform sample estimates the same full-graph quantity at every K, so close agreement between view and full-graph values is expected.

This framing is interpretive. The evidence behind it is P10, P41, A05, A06, V02 and T01. It explains *why* the two kinds transfer differently; it does not show that either is causally related to the labels.

**Status discipline.** Study 1 C1–C3 are the only pre-specified contrasts. Everything about `token_std` is Exploratory-post-hoc. Measurement agreement (V02, T01) and predictive utility (V04–V07) are reported as separate findings.

**Length budget.** About 10 pages in the current IEEE two-column format, with the supplement extra.

---

## 0. Front matter

**Title options.** None implies the archive is LEN-Small.
1. *Counts, Collisions and Message Lengths: What Edge-Limited Observation Preserves in an Archive of Campaign Engagement Graphs*
2. *How Much of a Campaign Label Is Node and Edge Count? Incremental Predictive Value Under Edge-Limited Observation in a 103-Graph Engagement Archive*
3. *Beyond Node and Edge Counts: Structural and Message-Length Statistics in Full and Edge-Sampled Engagement Graphs*

**Abstract (about 200 words).** One point per sentence:
1. The data: an archive of 103 graphs from the LEN project website, not established as LEN-Small (P02, P18).
2. Counts alone reach most of the predictability (P03, P24).
3. Added features improve log loss and AUC, not BA. Report the primary result and the 20-partition estimate (P06, R01, P07, P04).
4. Structure added to counts shows no detectable change. The improvement over counts is concentrated in one content statistic, identified post hoc (R09, R10, R11, K08).
5. Under edge sampling, collision-dependent statistics track the degree sequence, while the edge-by-edge statistic is preserved. Its incremental value is directionally consistent but uncertain (P10, P41, V02, V04, V05).
6. Scope: no claims about coordination or accounts (P12).

**Keywords.** Keep the current list, minus "benchmark validity" if the title changes. Add "edge sampling".

---

## 1. Introduction (about 1 page)

| ¶ | Single point | Claim IDs |
|---|---|---|
| 1.1 | Engagement-graph benchmarks are read as evidence about coordination, so what their labels are predictable from is a construct question | P12 |
| 1.2 | The data are a 103-graph archive from the LEN project website. Its relation to the published LEN-Small is unresolved, and the published selection rule conflicts with the published tables | P02, P13, A01, A02 |
| 1.3 | Simple graph properties often rival learned models, and comparison graphs here are much larger than campaign graphs | P14 |
| 1.4 | The working question, split into RQ1 (counts and increments on full graphs) and RQ2 (what survives edge-limited observation, and why) | — |
| 1.5 | Three findings stated without causal language, each with its status label: counts; increments in log loss and AUC, concentrated in a post-hoc content statistic; collision-dependent vs edge-by-edge behaviour under sampling | P03, P06, R10, P10, V02, V04 |

## 2. Related work (about 0.5 page)

| ¶ | Single point | Claim IDs |
|---|---|---|
| 2.1 | LEN and DECODE, with the official counts reported as the sources state them (314 vs 305) | P17, A09 |
| 2.2 | Simple baselines and benchmark audits; degree-preserving nulls; graph sampling distorts statistics; small-sample CV | — |

## 3. Data and provenance (about 0.75 page)

| ¶ | Single point | Claim IDs |
|---|---|---|
| 3.1 | Archive: 104 → 103 canonical graphs (52/51); labels from file names; directed simple graphs with self-loops in every graph | P18, P20 |
| 3.2 | It differs from the published LEN-Small tables. Cite the individual mismatching graphs, not unverified tallies. The selection rule is contradicted | A01, A02 (individual graphs only) |
| 3.3 | No account identifiers (overlap unmeasurable); timestamps not used; embeddings excluded | P21 |
| 3.4 | Retained text: 27.5% of edge texts are null, unevenly by class (0.58 vs 0.80 usable); two campaign graphs have no usable text | R12, T01 |
| 3.5 | Size difference between classes (Table 1, Fig. 1) | P14, P20 |

## 4. Methods (about 2 pages)

| ¶ | Single point | Claim IDs |
|---|---|---|
| 4.1 | Feature taxonomy. Node count n, edge count m and their ratio m/n, with density a function of n and m (counts); degree-related properties (degree Gini); arrangement (reciprocity, largest WCC, coreness); content (duplicate fraction, frequency Gini, `token_std`). Define each precisely | P22, K02 |
| 4.2 | Exact `token_std` definition: per edge, nulls dropped, cleaning, whitespace tokens, ddof 1, edge cases; verified against the raw archive | T01 |
| 4.3 | Study 1 design: nested sets M0–M4; C1–C3 pre-specified, not preregistered, earlier analysis of the same archive disclosed | P23 |
| 4.4 | Estimands and fitting: separately tuned BA and log-loss fits; inner-CV tuning; no leakage | P24, A11 |
| 4.5 | Uncertainty: the fixed-prediction bootstrap is primary; 20 partitions as sensitivity (not replication); Holm families named | P06, R01, K14 |
| 4.6 | Degree-preserving null, and what it can and cannot test (degree-sequence functionals are invariant) | P08, P35, A06, K15 |
| 4.7 | Study 2 design: K ∈ {250, 500, 1000}, seeds 100–109, budget-specific and common cohorts (the common cohort = the K = 1000 cohort); KK / FF / FK; models A–D | P50, L12; contrast_inventory.md |
| 4.8 | Collision-dependent vs edge-by-edge statistics; the E[N_K] equation as the formal example | P41, A06 |
| 4.9 | Post-hoc status of `token_std`: the selection history, and what Holm across K does not cover | K05 |

## 5. Results I: counts and incremental information on full graphs (about 2 pages)

| ¶ | Single point | Claim IDs |
|---|---|---|
| 5.1 | Counts alone reach BA 0.884 (20-partition mean 0.864) and AUC 0.93 | P03, P24, A14 |
| 5.2 | C1: no detectable BA gain; BA tie-break sensitivity | P04, P05, P30, A04 |
| 5.3 | C1: log loss −0.110 [−0.181, −0.039], Holm 0.009 (3 tests); repeat-averaged −0.094 [−0.172, −0.013]; AUC +0.039 | P06, R01, P07, R02 |
| 5.4 | The gain is not driven by one event, but it is concentrated in a minority of events | R03, R04, R05 |
| 5.5 | Count-baseline form: wider C grid; polynomial, spline and QDA baselines; not established against the most flexible count models | P31, R16 |
| 5.6 | Feature families: degree Gini worsens log loss; structure added to counts shows no detectable change; given content, structure −0.059 [−0.110, −0.011] (exploratory) | R09, R08, K08 |
| 5.7 | Content: the three-feature C3 shows no detectable change. Post hoc, counts plus `token_std` show no detectable difference from M4, and E3 is reported as exploratory | P27, R07, R10, R11 |
| 5.8 | Text-availability controls and the two no-text events (C1 interval includes zero without them) | R19, R18 |
| 5.9 | Degree-preserving null: no detectable difference; narrow coverage | P08, P33, P34, P35 |

## 6. Results II: edge-limited observation (about 2 pages)

| ¶ | Single point | Claim IDs |
|---|---|---|
| 6.1 | Single views were not detectably less predictive than full graphs, on all three metrics; the K = 1000 BA gain is a threshold effect | P09, P16, A05 |
| 6.2 | Collision-dependent statistics: E[N_K] is degree-sequence determined; structure predicts log N_K (R² 0.92–0.95); struct6 AUC 0.767 full vs 0.947 in views | P10, P41, A05, A06 |
| 6.3 | Retraining vs transfer, reported with AUC; for N_K, frozen transfer is a threshold collapse | P39, A05, L13 |
| 6.4 | Edge-by-edge statistic: view and full `token_std` agree (ρ ≥ 0.995), an expected property presented as a measurement check | V01, V02, T01, K06 |
| 6.5 | Incremental value of `token_std` (post hoc): B − A and D − C by K, log-loss direction in 10/10 seeds, mostly uncertain; D − C at K = 1000 against a comparator with poor log loss | V04, V05, V06, contrast_inventory.md (a) |
| 6.6 | No supportable budget-dependence claim (cohort change; B and D NOT COMPUTED on the common cohort below K = 1000) | contrast_inventory.md (b, c) |
| 6.7 | Text availability: within-class association with `m_K`; class separation persists within availability strata (descriptive); the no-text events do not change the comparisons | D02, D03, D04, D05 |
| 6.8 | The three-feature content contrast, BA and log loss, kept numerically separate from `token_std` | P38, P40, K10 |

## 7. Discussion (about 1 page)

| ¶ | Single point | Claim IDs |
|---|---|---|
| 7.1 | In this archive, most predictability is recoverable from n and m, and the residual is probabilistic, not decisional | P03, P06, P04 |
| 7.2 | Why sampling preserves label information: the collision-dependent statistics re-encode the degree sequence, and the degree-preserving null is blind to this by construction | P10, A06, K15 |
| 7.3 | Why `token_std` is the candidate that transfers: it is an edge-by-edge statistic. Its incremental value is uncertain and post hoc, and it depends on retained text | V02, V05, D02, K16 |
| 7.4 | Implications for evaluation on LEN data: count baselines, separate metrics, repeated partitions, single-feature as well as set-level contrasts | P43, K04, K14 |

## 8. Limitations (about 0.75 page)

See "Required limitations" below. One paragraph per group: provenance; sample size and uncertainty; post-hoc selection; text retention; null model; observation model; models evaluated.

## 9. Conclusion (about 0.25 page)

| ¶ | Single point | Claim IDs |
|---|---|---|
| 9.1 | Three statements mirroring §1.5 with status labels, and next steps (official release and selection list; an independent test of `token_std`) | P03, P06, R10, V02, V05 |

## Corrections and Data availability (about 0.25 page)

The current text stays with minor edits: shorten, and verify P49 before keeping the "complete rerun" sentence (P47, P48, P49).

---

## Tables and figures

All use existing outputs. Regenerating a figure only reformats an existing artifact; it adds no analysis.

| # | Purpose | Source artifact | Cohort | x / y (or columns) | Exists? |
|---|---|---|---|---|---|
| T1 | Archive and cohort, with provenance caveats | `paper_results.json` → `results.tex` `\RTabCohort`; `s01_content_verification.json` (text share) | 103 (52/51) | Item / value; add a usable-text row | Yes (Table I). Add one row from an existing artifact; change the "Official LEN-Small" wording |
| F1 | Class size difference | `paper/figures/fig1_size_distributions.pdf` | 103 | class / node count, edge count (log) | Yes |
| T2 | Study 1 performance by feature level, primary partition and 20-partition mean | `results.tex` `\RTabLevels`; `research_audit/outputs/s02_performance.csv` | 103 | model / LR BA, log loss, AUC (partition 42; 20-mean) | Both parts exist; the combined table must be assembled |
| T3 | Study 1 contrasts: C1–C3 (primary, Holm over 3), repeat-averaged C1 and E2/E3 (Holm over 7), post-hoc single-feature `token_std` rows marked | `paper_results.json`; `s02_contrasts.csv`; `s04_posthoc_lensd.json` | 103 | contrast / ΔBA, Δ log loss, ΔAUC [CI] (p) | All values exist; table to assemble |
| F2 | Study 1 contrasts graphic | `paper/figures/fig2_study1_contrasts.pdf` or `research_audit/outputs/s02_fig2_contrasts.png` | 103 | Δ / contrast | Yes |
| T4 | Degree-preserving null | `results.tex` `\RTabNull` | 103 | quantity / value | Yes |
| F3 | Collision-dependent mechanism: E[N_K] vs node count | `paper/figures/fig4_endpoint_mechanism.pdf` | 102 (K = 250) | log n / E[N_250]; inset R² | Yes |
| T5 | Study 2 models A–D, KK and FF, by K: log loss, AUC, BA | `research_audit/outputs/v02_performance.csv`; common-cohort A and C from `outputs/run_v2/study2/results.json` | BS 102 / 98 / 73; CO 73 | model × K / three metrics; B and D on the common cohort marked NOT COMPUTED | Values exist; table to assemble (as contrast_inventory.md Table 1) |
| T6 | Study 2 contrasts B − A, D − C (post hoc) and C − A, with retraining and transfer rows showing AUC | `v02_contrasts.csv`; `study2/results.json`; `a04_study2_diagnostics.csv` | BS | contrast × K / Δ [CI] (Holm or unc.) | Values exist; table to assemble |
| F4 | Single-view performance by K on the common cohort | `paper/figures/fig3_study2_single_view.pdf` | CO 73 | K / BA (seed range) | Yes (BA only; an AUC panel would need a re-plot of existing values) |
| F5 | `token_std` contrasts by K, views and full-graph reference | `research_audit/outputs/v02_fig2_contrasts.png` (+ `v02_fig2_data.csv`) | BS | K / Δ log loss, ΔAUC, ΔBA | Yes |
| F6 (supp.) | Edge-by-edge measurement check: view vs full `token_std` | `v02_fig3_view_vs_full.png` | BS | full-graph `token_std` / mean view `token_std` | Yes |
| F7 (supp.) | Text availability by class and K | `v02_fig1_text_availability.png`; `final_diagnostics/outputs/d01_fig_mK_vs_tokenstd.png` | BS | K × class / usable share; `m_K/K` vs `token_std` | Yes |
| S1 (supp.) | Partition stability of C1 | `s02_fig1_split_stability.png` | 103 | partition / Δ | Yes |
| S2 (supp.) | Event contributions to C1 | `s03_fig_event_influence.png` | 103 | event rank / d_i | Yes (rename "influence" to "per-event contribution" in the caption) |
| S3 (supp.) | Exploratory matching | `results.tex` `\RTabMatching` | 15–17 pairs | matching / BA | Yes |
| S4 (supp.) | HGBT secondary results | `results.tex` `\RTabLevels` (HGBT columns) | 103 | model / metrics | Yes |
| S5 (supp.) | Exclusion of the no-text events, Study 2 | `final_diagnostics/outputs/d02_comparison_with_original.csv` | BS minus 2 | contrast × K / original vs excluded | Yes (CSV; table to assemble) |

---

## Claims to avoid

1. That the archive is LEN-Small, the official release, or "the release plus three events".
2. That LEN-Small is "the 100 smallest graphs by node count" as a fact.
3. Any cross-event account-overlap figure (92.7%), or any unverified tally (17/25, 14/25, AUC 0.64, means 7.9/9.9).
4. That `token_std` measures coordination, templating, linguistic structure or campaign intent.
5. Any `token_std` result described as confirmatory, confirmed or established, or presented without "post hoc".
6. That structure or topology "contains no information" or "contributes nothing".
7. That counts plus `token_std` is "equivalent" or "indistinguishable" to M4.
8. That `token_std`'s added value increases with K, is absent at small K, or is larger beyond structure than beyond N_K.
9. That sampling improves classification, or that views carry more information than full graphs.
10. "Training regime matters more than features" in general form.
11. BA differences as effects, or BA significance as evidence of added information.
12. "Complementary information in the combined feature set".
13. Predictive performance described as an information measurement (no "information content", "bits" or "mutual information").
14. Repeated partitions or sampling seeds described as replications.
15. Any causal verb linking features to labels ("drives", "causes", "influences").

## Required limitations

1. **Provenance.** The population is undefined. The archive's relation to the published LEN-Small is unresolved, and the published selection rule conflicts with the published tables.
2. **Labels** come from file names. There are no subtype labels and no account identifiers, so dependence through shared accounts cannot be assessed. Two campaign hashtags appear twice (grouped-fold C1 −0.082 [−0.164, +0.005]).
3. **Sample size.** 103 events (73 at K = 1000). Null results are inconclusive, not equivalence. The bootstrap intervals exclude refitting, and partition variability is comparable in size.
4. **Post-hoc selection.** `token_std` was identified post hoc on the same events. No independent test exists within this archive, and Holm across K does not address the selection.
5. **Text retention.** `token_std` is computed on retained text only. Retention differs by class (0.58 vs 0.80), two campaign graphs have none (median-imputed), and within comparison graphs `token_std` is associated with the number of usable texts. The cause of the missing text is unknown.
6. **Study 2 cohorts.** K is confounded with cohort composition in the budget-specific cohorts. B and D were not evaluated on the common cohort below K = 1000, and C's log loss at K = 1000 is poor.
7. **Null model.** It mixes incompletely, rarely changes median coreness, uses five realisations, and is blind to degree-sequence functionals.
8. **Observation model.** Only uniform edge sampling was studied. Only LR (and secondary HGBT) on hand-crafted features were evaluated; no GNN and no published LEN methods.
9. **Tuning.** BA depends on tuning tie-breaks and row order. Grid-boundary hits remain for some fits.
10. **Interpretation.** All results describe predictive association in one archive and do not establish mechanisms.
