# LEN-Small — Research Audit and Evidence Verification

Date: 2026-11-04. Scope: the authoritative manuscript `paper/main.tex` (7-page IEEE version, PDF
`paper/LEN_Small_Predictive_Information_Beyond_Scale.pdf`), the pipeline in `src/`, the corrected
run `outputs/run_v2/`, the revision outputs `outputs/revision_*`, the raw archive
`small_encoder_final.tar`, and the official LEN sources. Nothing outside `research_audit/` was
modified. Labels: **VERIFIED**, **STRONGLY SUPPORTED**, **EXPLORATORY**, **UNRESOLVED**, **DISPROVEN**.
The issue-by-issue record is `INVESTIGATION_LEDGER.md`.

---

## A. Executive summary

Ranked by scientific impact × severity × confidence.

| Rank | Finding | Label | Changes direction? |
|---|---|---|---|
| 1 | **The published LEN-Small composition is incompatible with its stated selection rule.** From the paper's own Tables 2–3, at least 113 LEN graphs have fewer than 8,355 nodes (the LEN-Small maximum), including at least 52 of 58 Reform campaigns, of which LEN-Small contains 16. "Smallest 100 by node count" (and "smallest 51 / 49 per class") cannot produce Table 3. The paper's motivating statement that LEN-Small is "the 100 smallest graphs" — and therefore our framing of a size difference *surviving* a size-based selection — rests on a documented contradiction. | VERIFIED (contradiction); selection mechanism UNRESOLVED | Yes |
| 2 | **Our archive is not the tabulated LEN-Small.** It overlaps heavily (17/25 published node extremes and 14/25 published edge extremes — the latter with self-loops excluded — match local graphs exactly), but two local campaign graphs exceed the published campaign edge maximum (6,697 and 4,157 vs 2,027, even without self-loops), and two local comparison graphs are smaller than the published comparison minimum (433 and 468 nodes vs 469; 433 is below every comparison graph in the full LEN tables). No 51-of-52 campaign subset reproduces Table 3. It cannot be described as "the official release plus three events". | VERIFIED | Yes (framing) |
| 3 | **The 92.7% "account overlap" is an artefact.** It is exactly reproduced (92.66%) as the share of distinct *local integer node indices* that appear in ≥ 2 events. Ids are 0..N−1 per graph and the archive contains no account identifier. Cross-event overlap cannot be established from this release. | DISPROVEN (as an overlap measure) | No (paper already says overlap is unmeasurable) |
| 4 | **The headline probabilistic result reproduces exactly; the decision (BA) results are fragile.** An independent reimplementation reproduces all scale/structural features exactly and the C1 log-loss gain exactly (−0.110 [−0.181, −0.039]), M4 log loss 0.216 and AUC 0.971. BA values move by ≈ 0.01 with inner-CV tie-breaks alone (independent refit: C1 ΔBA 0.000 vs reported +0.010; M4 BA 0.884 vs 0.893). | VERIFIED | No (supports existing hedging) |
| 5 | **The frozen-transfer and KK-vs-FF effects are partly threshold effects, and the struct6 "training regime" contrast confounds regime with feature meaning.** N_K-only frozen transfer predicts every view as campaign (BA 0.500) while ranking well (AUC 0.942). At K = 1000, KK beats FF in BA (0.915 vs 0.860) but not in AUC (0.953 vs 0.951) or log loss (0.250 vs 0.255). With the six structural features, full-graph AUC is 0.767 but view-trained AUC is 0.947: in a fixed-K view, structural features become size proxies, so the +0.254 "retraining effect" mixes training regime with features that change meaning under sampling. | VERIFIED (diagnostics) | Yes (Study 2 interpretation) |
| 6 | **E[N_K] is a degree-sequence quantity and is exactly invariant under the degree-preserving null.** The formula is correct for the archive's conventions and matches simulation. Rewiring preserves every node's distinct incident-edge count, hence E[N_K] exactly; the N_K *distribution* is not preserved (its SD rises by ≈ 8–10%). Any arrangement-null comparison is blind to this signal by construction. | VERIFIED (proof + computation) | Yes (connects Studies 1 and 2) |
| 7 | **Exploratory: degree heterogeneity beyond size carries ranking signal that the paper's Gini features do not capture.** On 102 events, E[N_K] alone gives AUC 0.960 (counts 0.923); adding E[N_K] to counts: ΔAUC +0.035 [+0.014, +0.061] (log loss interval includes zero); adding degree Gini to counts *worsens* log loss (+0.060). Post-hoc, single dataset, uncorrected. | EXPLORATORY | Possibly (candidate research question) |
| 8 | **The rewiring null mainly tests reciprocity, connectivity and maximum core number.** Reciprocity did not vary across the 5 realisations in 46% of events, median coreness in 99%; ≈ 13% of edges never move. The narrowest defensible conclusion is model- and feature-specific. | VERIFIED | No (paper already narrowed) |
| 9 | **Official documentation is internally inconsistent** (314/179 vs 305/170; "7 campaign sub-types" vs 8 tabulated; README places the full table under the LEN-Small heading; 190 − 20 ≠ 179). | VERIFIED | Context |

---

## B. Dataset provenance reconciliation

### B.1 Official counts (sources fetched 2026-11-04)

| Source | Total | Campaign | Non-campaign | Subtype rows sum to | Evidence |
|---|---:|---:|---:|---|---|
| arXiv:2503.00599v2 (abstract, intro, "Building networks", Table 2) | 314 | 179 | 135 | 179 + 135 | Table 2 "Overall" rows; text "LEN comprises of 314 graphs of which 179 are campaign" |
| Project page (erdemub.github.io/large-engagement-network) | 305 | 170 | 135 | **179** + 135 (same 8 campaign rows incl. Noise 9) | "We have a total of 305 engagement graphs, comprising of 170 campaign graphs" |
| GitHub erdemUB/LEN README | 305 | 170 | 135 | 179 + 135 | "The overall dataset contains 305 large networks, 170 campaign and 135 non-campaign graphs." |
| LEN-Small (arXiv Table 3; project page; README text) | 100 | 51 | 49 | 51 + 49 | Table 3 caption: "This is simply the smallest 100 networks, out of 314, with respect to node counts." |
| Local archive (raw tar) | 103 canonical (104 files) | 52 | 51 | no subtype labels in files | `outputs/a01_archive_summary.json` |

- **VERIFIED:** 170 = 179 − 9 (Noise). The seven non-Noise campaign rows sum to 170. The project page and README still list the Noise row (9) while stating 170. That the 170 excludes Noise is an **inference**, not a stated explanation.
- **VERIFIED:** the paper says "7 sub-types in campaign" but tabulates 8 (Noise included); Table 1 gives 15 classes for 16 tabulated subtypes.
- **VERIFIED:** paper text "identified 190 instances … removed 20 … annotated the remaining 179" is arithmetically inconsistent (190 − 20 = 170).
- **VERIFIED:** the README places the full-dataset table under the heading "Small Dataset (LEN-Small)"; it has no LEN-Small statistics table.
- **VERIFIED:** the download page lists the small archive as 1.9G, the project page as 5.4 GB; our copy is 5,792,081,920 bytes (5.39 GiB).
- No changelog or version history exists on any official page (both GitHub repos show no releases).

### B.2 Selection-rule reconstruction (`scripts/a02_selection_rule.py`)

**Method.** For a subtype with n graphs, minimum a, maximum b and printed mean μ (rounded, so the true
mean ≤ μ + 0.5): one graph equals b, every other graph above T has ≥ T+1 nodes, every graph has ≥ a, so
the number h above T satisfies b + (h−1)(T+1) + (n−h)a ≤ n(μ+0.5). This gives a guaranteed lower bound
on the count at or below T. T is set one below the LEN-Small maximum, so ties do not count as violations.

**Global "smallest 100" (T = 8,354).** Lower bounds vs LEN-Small:

| Class | Subtype | ≥ graphs < 8,355 nodes | In LEN-Small |
|---|---|---:|---:|
| campaign | Politics | 19 | 14 |
| campaign | Reform | 52 | 16 |
| campaign | Finance | 12 | 9 |
| campaign | Cult | 6 (max 7,880) | 4 |
| campaign | Entertainment | 3 (max 4,220) | 0 |
| campaign | Common | 2 | 0 |
| non-campaign | Announced cam. | 1 (min 6,650) | 0 |
| **total** | | **≥ 113 (97 campaign + 16 non-campaign)** | 100 |

If at least 113 graphs have fewer than 8,355 nodes, the 100 smallest cannot include a graph with 8,355 nodes,
yet Table 3 does. **The stated rule and the published tables are mutually incompatible** (VERIFIED, given the tables as printed).

**Per-class "smallest 51 campaign / 49 non-campaign".** Campaign threshold 2,519: Reform ≥ 39 (LEN-Small 16), Entertainment ≥ 2 (0), total ≥ 56 > 51. Non-campaign threshold 8,354: Announced cam. ≥ 1 (0). Incompatible (VERIFIED).

**Per-subtype selection.** Every LEN-Small subtype minimum equals the full-LEN subtype minimum (Politics 100, Reform 131, News 581, Finance 273, Noise 454, Cult 313; News 818, Sports 469, Festival 885, Internal 4,188, Common 1,214, Entertainment 1,477; Sports cam. identical). This is consistent with taking the smallest k graphs within each subtype for unexplained k (two campaign and one non-campaign subtype with k = 0). **Consistent, not demonstrated** (UNRESOLVED).

**Other explanations.** Manual or constrained selection, different node-count definitions between Tables 2 and 3, or different dataset versions cannot be distinguished with the available evidence. The previously reported "at least 72 campaign graphs" is a valid but weaker bound; this audit's bound is ≥ 97.

**Reconstruction of the actual subset.** Not verifiable with the currently available evidence. It requires graph-level node counts for all 314 (or 305) LEN graphs (`encoder_final.tar`, listed at 38G, or `metadata_graph.json`, listed at 1.9G; not downloaded) or the authors' selection list.

### B.3 Local archive (`scripts/a01_archive_audit.py`, raw tar)

VERIFIED from the raw files:
- 104 JSON members; 1 byte-identical duplicate pair (`#SesimiziDuyanVarMi…` / `#SesimiziDuyanVarMı…`; dotless ı vs i, not a Unicode-normalisation difference); 103 canonical graphs; 52 campaign / 51 non-campaign (file-name tokens).
- 41 file names are not in NFC form; no two canonical names collide after normalisation.
- All files `directed: true`, `multigraph: false`; node ids are integers 0..N−1 in every file.
- 211,875 nodes, 288,540 edges, 4,212 self-loops (every graph has at least one), 0 repeated directed pairs, 0 isolated nodes, 4,339 reciprocal pairs.
- Attributes. Node: `id`, `node_attr` (embedding), `kcore` (list), `author_description` (profile text). Edge: `source`, `target`, `timestamp`, `text`, `Interaction_Count`, `edge_attr` (embedding). Graph: `{}`.
- **No subtype label and no account identifier** are present.

### B.4 Archive vs published LEN-Small

| Check | Result |
|---|---|
| Published node extremes matched exactly by a local graph | 17 / 25 (e.g. 100, 1,908, 131, 581, 1,671, 273, 1,590, 454, 313; 818, 6,169, 885, 1,214, 1,477, 7,739, 2,880, 4,661) |
| Published edge extremes matched exactly by local edges − self-loops | 14 / 25 (incl. the comparison maximum 10,608 = 10,682 − 74) |
| Local campaign graphs above published campaign max edges (2,027, loops excluded) | 2 (`MebHazirandaDepremeTayin…05-23`: 6,697; `ŞartsızTayin_Şart…03-23`: 4,157) |
| Local campaign graph below published campaign min edges (203, loops excluded) | 1 (`Gelenekten_Geleceğe…`: 202) |
| Local comparison graphs below published comparison min nodes (469) | 2 (`Milliyol_Partisi`: 433; `#RealMadridManCity`: 468) |
| Node counts off by 1–4 from published extremes | 2,520→2,519; 8,355→8,352; 469→468; 4,188→4,185; 5,982→5,981; 4,962→4,961; 634→632; 705→701 |
| Best 51-of-52 campaign subset | still has max edges 4,157 > 2,027 — cannot reproduce Table 3 |

**STRONGLY SUPPORTED:** the published edge counts exclude self-loops (14 exact matches cannot be coincidence). The remaining mismatches suggest the tabulated version and our archive differ in content as well as convention.

**Answer to the critical question:** our 103-graph archive is **not** the same dataset version as the tabulated 100-graph LEN-Small, and it is not demonstrably a superset of it (VERIFIED). Which graphs are "extra" cannot be identified.

### B.5 Account identity (VERIFIED / DISPROVEN)

- Node ids are per-graph indices; the archive has no identifier field. The paper's Ethics section says identifying fields were hashed and withheld from the public version, available on request.
- The 92.7% figure is reproduced as 92.66% = (distinct integer id values occurring in ≥ 2 events) / (all distinct id values). Since ids are 0..N−1 in every graph, every id below the second-largest graph size recurs. **It measures index reuse, not shared accounts** (DISPROVEN as an overlap measure).
- Cross-event account overlap: not verifiable with the currently available evidence. It requires the withheld hashed user ids. `author_description` text exists but was deliberately not used to link accounts: it is not an identifier, and attempting re-identification would be unreliable and privacy-sensitive.

### B.6 Unresolved provenance questions

1. Which 305 / 314 graphs constitute the current public full release?
2. The actual LEN-Small selection procedure.
3. Whether Table 2/3 node counts use the same definition as the released files.
4. Why our archive has 103 graphs, and which 3 are absent from the tabulated set.
5. Subtype labels for our 103 graphs (needed to test per-subtype selection).

---

## C. Claim-to-evidence matrix (headline results, manuscript `paper/main.tex`)

All values flow `src/* → outputs/run_v2/paper_results.json (+ outputs/revision_supplement/supplement.json) → src/export_latex_results.py → paper/generated/results.tex`. Config: `configs/v2_coreness_fix.yaml`. "Reproduced" means recomputed by audit code, not read from outputs.

| Claim (paper) | Reported | Source code | Output artifact | Reproduced? | Issues / recommended correction |
|---|---|---|---|---|---|
| Archive 104 files, 1 duplicate, 103 events 52/51 | as stated | `src/ingest_len.py` | `data/manifests/*` | **Yes** (raw tar, a01) | Add: archive is not the tabulated release (B.4) |
| LEN-Small = 100 smallest of 314 by node count (Sec. I, II) | cited from LEN | — | — | **Contradicted by LEN's own tables** (a02) | Replace with: "described by its authors as …; their published tables are inconsistent with that rule" |
| Comparison events several times larger | medians 3,227 vs 506 nodes | manifest | Table I | Yes (manifest) | — |
| Counts (M0, LR) BA 0.884 | 0.884 | `study1_incremental.py` `run_level` | `study1/oof_predictions.parquet` | **Yes, exactly** (a03) | — |
| M4 BA 0.893; C1 ΔBA +0.010 [−0.049, +0.076] | as stated | same | `paper_results.json` | **Partly**: independent refit 0.884 / 0.000 [−0.048, +0.047] | BA depends on inner-CV tie-breaks; already called inconclusive — keep, add tuning sensitivity |
| C1 Δlog loss −0.110 [−0.181, −0.039], Holm p = 0.009 | as stated | `paired_bootstrap` | same | **Yes, exactly** (a03) | — |
| M4 log loss 0.216, AUC 0.971 | as stated | same | same | **Yes, exactly** | — |
| Wider C grid: M0q log loss 0.326 → 0.364; C1 −0.147 | as stated | `src/h1_c_grid.py` | `outputs/revision_h1_cgrid` | Re-run earlier (byte-identical); boundary hits confirmed from outputs | — |
| Arrangement: no detectable gain over null (ΔBA 0.000 [−0.048, +0.047]) | as stated | `rewiring.py`, study1 null | `null_results.json` | From outputs; rewiring invariants re-verified (a05) | Add that the null is blind to degree-sequence signal (E[N_K] invariant) |
| Null coverage: reciprocity 92%, median core 4% changed; 46% zero z-variance | as stated | supplement | `supplement.json`, `null_features.parquet` | **Yes** (a05: 45.6%, 99.0% zero variance median core) | — |
| HGBT vs best count: ΔBA +0.048 [−0.018, +0.117], ΔAUC +0.008 | as stated | study1 | `paper_results.json` | From outputs | — |
| Study 2 eligibility 102 / 98 / 73; K=2000 infeasible (4 campaign) | as stated | `sample_views.py` | eligibility json | **Yes** | — |
| Study 2 views recomputed from sampled edges only | design | `features.compute_features_for_sampled_view` | `sampled_views_v2.parquet` | **Yes**: 2,730 views regenerated, features match to 1e-9 | — |
| Single view − full graph: +0.002 / +0.027 / +0.056 (K = 1000 interval excludes 0) | as stated | `revision_supplement.py` | `supplement.json` | From outputs; diagnosed (a04) | K = 1000 BA gain is threshold-driven: AUC and log loss equal |
| Retraining effect (struct6) +0.254 [0.162, 0.348] at K = 250 | as stated | `study2_observation.py` | `study2/results.json` | From outputs; diagnosed (a04) | Confounded: struct6 in views encodes size (view AUC 0.947 vs full-graph 0.767). Reword as training on views + features that change meaning under sampling |
| Frozen transfer loses 0.126 BA at K = 250 (struct6) | as stated | same | same | Diagnosed (a04) | Mostly a ranking loss for struct6; for N_K-only, a pure threshold collapse (BA 0.500, AUC 0.942) — report AUC alongside |
| E[N_K] formula; matches observed mean within 3.5% at K = 250 | as stated | `study2_observation.expected_endpoints` | `paper_results.json` | **Yes**: derivation, Monte Carlo, all 273 event-budgets (a05) | 3.5% max is 10-seed sampling noise (worst z ≈ 2.2) |
| E[N_K] AUC 0.965 vs log node count 0.934 | as stated | study2 mechanism | `paper_results.json` | Consistent with a06 (E[N_K] AUC 0.960 under CV) | The extra AUC is degree-sequence, not size (a06, exploratory) |
| Structure predicts log N_K, R² 0.92–0.95 | as stated | `revision_supplement.py` | `supplement.json` | From outputs | R² says nothing about where label signal comes from (prompt is correct) |
| 21/21 verification checks pass | as stated | `verify_studies.py` | `verification_report.json` | Not re-run in this audit (pytest suite passed: 46/46) | — |

---

## D. Methodological audit

| Area | What is wrong or uncertain | Why it matters | Affects | Fixable with existing data? | Evidence that would resolve |
|---|---|---|---|---|---|
| Dataset identity | Archive ≠ tabulated LEN-Small; selection rule contradicted | The paper's framing ("size difference survives a size-based selection") is unsupported; the population is undefined | Interpretation | Partly (reword) | Full LEN node counts or authors' list |
| Density / mean degree | Exact functions of (n, m): density = m / (n(n−1)) (max rel. error 2e-15); mean degree m/n | Treating density as structure would double-count size; the paper already treats it as scale-encoding | Neither (handled) | — | — |
| Self-loops | Counted in m, degrees and N_K; excluded from coreness and drawing; published LEN edge counts appear to exclude them | Cross-source comparisons of edge counts must state the convention | Interpretation of provenance | Yes | — |
| Coreness | Correct on undirected projection without self-loops (reproduced exactly); appropriate and documented | — | — | — | — |
| Leakage | None found: imputation, scaling, model and C tuning inside training folds; per-graph features | — | — | — | — |
| Count baseline | Original grid optimum at the upper bound (C = 10) in 5/5 log-loss folds; wider grid does not help the baseline (log loss worse). Nonlinear count terms add nothing (E4 ΔLL −0.005 [−0.016, +0.009]) | Baseline was not unfairly handicapped; M0q is a harmless but unnecessary control | Neither | Done | — |
| BA instability | BA differences of ±0.01–0.02 arise from inner-CV tie-breaks / row order (a03; paper's own row-permutation check) | BA contrasts at this sample size are not interpretable beyond "no detectable difference" | Numerical BA values | Yes (report) | More events |
| LR vs HGBT | Metric-specific disagreement; HGBT count model has poor decision placement but good ranking | Within-HGBT BA gains are inflated; no model-family evidence of extra feature value | Interpretation | Done | — |
| Uncertainty | Bootstrap over fixed OOF predictions (refit variability excluded); 10 splits reuse the same 103 events; views are not independent events | All intervals are conditional; the effective sample size is ≈ 103 events (fewer if repeated hashtags are dependent) | Interpretation | Partly | Independent data (full LEN) |
| Study 2 transfer | Penalty mixes ranking loss and threshold shift, differently by feature set | "Training regime matters" is overstated for N_K (threshold) and confounded for struct6 (feature meaning changes) | Interpretation | Yes (a04) | — |
| KK vs FF | K = 1000 BA gain is threshold, not information; sampling cannot add information about the full graph | Avoid "views outperform full graphs" | Interpretation | Yes | — |
| Endpoint occupancy | Correct; invariant (in expectation) under the null | The arrangement null cannot detect degree-sequence signal; E[N_K] links Study 2 to the degree sequence (Study 1) | Interpretation | Yes | — |
| Rewiring | Chains reach target; 13% edges unmoved; reciprocity/median core rarely change; 5 realisations | The null tests a narrow set of arrangement properties; z-scores undefined for many events | Interpretation | Partly (more realisations cheap; Curveball optional) | Mixing diagnostics with more chains |
| Repeated hashtags | Two campaign hashtags appear twice (one pair split across folds) | Mild dependence; slightly optimistic CV | Numerical (small) | Yes (grouped folds as sensitivity) | — |

**Narrowest defensible conclusion from the null model:** for logistic regression with these four
arrangement features, computing them on the real graphs rather than on degree-preserving rewired graphs
(10 swaps/edge, 5 realisations) did not detectably change predictive performance. It does **not** show
that arrangement carries no information beyond the degree sequence. The model already contains counts
and degree concentration, so redundancy and absence cannot be separated by a performance comparison.
Conditional-information questions would need conditional tests, such as permuting arrangement features
within degree-matched strata, which is beyond this audit.

---

## E. Verified versus unverified findings

**1. Verified**
- Official sources disagree (314/179 vs 305/170), and their subtype rows sum to 179 in both.
- The stated LEN-Small selection rule is incompatible with the published Tables 2 and 3 (≥ 113 graphs below the LEN-Small maximum).
- The local archive: 104 → 103 canonical graphs, 52/51; no account or subtype identifiers; node ids are 0..N−1.
- The local archive is not the tabulated LEN-Small. It has campaign graphs outside the published edge range and comparison graphs below the published node minimum.
- The 92.7% overlap is an index-reuse artefact.
- Scale and structural features, density identity, coreness, log-loss/AUC headline results and the C1 log-loss contrast reproduce exactly. BA contrasts reproduce only up to tuning tie-breaks.
- No preprocessing leakage was found.
- Study 2 views regenerate exactly and are computed from sampled edges only.
- The E[N_K] formula is correct and matches simulation and the observed views. It is exactly invariant in expectation under the pipeline's rewiring, but not in distribution.
- Frozen-transfer diagnostics: N_K-only transfer collapses to one class with high AUC. At K = 1000, KK vs FF differs in BA but not in AUC or log loss.

**2. Strongly supported**
- Published LEN edge counts exclude self-loops (14/25 exact matches).
- The project page and README total of 170 campaigns excludes the 9 Noise graphs.
- The struct6 "retraining effect" is largely driven by structural features encoding size in fixed-K views.

**3. Exploratory**
- Degree heterogeneity beyond (n, m), summarised by the occupancy expectation, carries ranking signal (ΔAUC +0.035 [+0.014, +0.061] over counts). Gini summaries do not capture it.
- Sources and targets do not add to N_K.

**4. Unresolved**
- The actual LEN-Small selection procedure and the official membership of LEN-Small.
- Identity of the 3 extra local graphs.
- The subtype labels of local graphs.
- Cross-event account overlap.
- Whether the exploratory degree-heterogeneity signal replicates on independent graphs (full LEN).
- Whether arrangement carries conditional information beyond the degree sequence.

---

## F. Research direction implications (max. three)

**F1. A provenance and selection audit of LEN-Small (benchmark validity).**
- *Question:* Is LEN-Small what its documentation says it is, and how does its undocumented selection shape what its labels can be predicted from?
- *Why it matters:* published LEN-Small results are interpreted against a size-controlled selection that the published tables contradict.
- *Evidence in hand:* B.1–B.5 (verified).
- *Missing:* full-LEN graph-level metadata (`metadata_graph.json` or `encoder_final.tar`) to reconstruct the selection; subtype labels.
- *Minimum work:* download the metadata (≈ 1.9 GB, needs your approval); recompute per-graph sizes; test candidate rules; quantify the size–label association under the documented rule vs the actual subset.
- *Threats:* the public full release may itself differ from the paper's 314.
- *Contribution:* a concrete, checkable benchmark-documentation finding; modest but solid.

**F2. Endpoint occupancy as the bridge between degree sequence and partial observation.**
- *Question:* Under uniform edge sampling, how much of a sampled view's label signal is determined by the full graph's degree sequence (via E[N_K]), and does degree heterogeneity beyond size carry label information?
- *Why it matters:* it explains *why* fixed-budget views are predictive, and *why* arrangement nulls cannot see this signal (exact invariance).
- *Evidence in hand:* proof and verification (a05); exploratory signal (a06).
- *Missing:* replication on independent graphs (full LEN), a pre-specified analysis, and comparison against simple heterogeneity summaries.
- *Minimum work:* pre-register the a06 contrasts; run them on full LEN.
- *Threats:* size confounding through the LEN-Small selection; post-hoc discovery on 102 events; dependence between repeated hashtags.
- *Contribution:* a potentially novel, mathematically grounded empirical finding. Novelty is **not** established; a focused search did not find it, which is not proof.

**F3. Narrowed version of the current paper (no new data).**
- *Question:* as now, with Study 2 reframed (threshold vs ranking; size leakage into structural features) and the provenance corrected.
- *Evidence:* sections C–D.
- *Missing:* nothing essential.
- *Minimum work:* rewording plus reporting AUC/log loss for transfer contrasts.
- *Threats:* the population is undefined (F1), which limits generalisation.
- *Contribution:* honest benchmark-audit note; incremental.

---

## G. Prioritised action plan

**Must resolve before further experiments**
1. Decide whether to download LEN metadata (≈ 1.9 GB) or the full archive (38G listed), and/or contact the LEN authors about the selection rule, version and the 3 extra graphs. (Blocks F1 and F2 replication.)
2. Fix the analysis population: the 103-graph archive as-is, with explicit provenance caveats.

**Must resolve before revising the paper** (depends on 1 for wording)
3. Replace "LEN-Small consists of the 100 smallest LEN graphs by node count" with the documented contradiction, and state that our archive is not the tabulated release (B.2, B.4).
4. Reframe Study 2: report AUC/log loss for transfer and KK-vs-FF; state that the K = 1000 BA gain is threshold-driven; qualify the struct6 retraining effect (size leakage into structure).
5. State the null's blind spot: degree-sequence quantities, including E[N_K], are invariant under it.
6. Keep BA contrasts explicitly inconclusive; mention tie-break sensitivity.

**Useful additional analyses** (existing data)
7. Grouped folds for the two repeated hashtags (sensitivity).
8. Transfer contrasts with prevalence- or rank-based thresholds, as diagnostics only.
9. More rewiring realisations (e.g. 20) to make z-scores defined. Cheap; does not change the narrow claim.

**Optional future research**
10. F2 on full LEN with a pre-specified protocol.
11. Conditional-information tests for arrangement (degree-stratified permutation).
12. Curveball sampler, only if a broader arrangement claim is wanted.

Dependencies: 1 → (3, 10); 4 and 5 are independent of 1; 10 depends on 1.

---

## H. Reproducibility package

**Scripts** (`research_audit/scripts/`; run from the project root, Python 3.12.10, numpy 1.26.4, pandas 3.0.6, scikit-learn 1.9.0, networkx 3.6.1, scipy 1.17.1):

| Script | Purpose | Inputs | Outputs | Seeds |
|---|---|---|---|---|
| `a01_archive_audit.py` | Raw archive audit (hashes, duplicates, attributes, counts) | `small_encoder_final.tar` | `outputs/a01_archive_members.csv`, `a01_archive_summary.json`, `.log` | — |
| `a02_selection_rule.py` | Selection-rule compatibility from published tables | values transcribed from arXiv:2503.00599v2 Tables 2–3 | `outputs/a02_selection_rule.json`, `.log` | — |
| `a03_study1_reproduce.py` | Independent features + LR refit + C1 bootstrap; tuned-C and LR/HGBT extraction | `data/processed/edges.parquet`, `data/manifests/manifest.parquet`, `outputs/run_v2/study1/*`, `outputs/revision_h1_cgrid/results.json` | `outputs/a03_study1.json`, `.log` | folds 42, inner 0, bootstrap 7 |
| `a04_study2_diagnostics.py` | Transfer / threshold / calibration diagnostics | `outputs/run_v2/study2/view_predictions.parquet` | `outputs/a04_study2_diagnostics.csv`, `.log` | — |
| `a05_endpoint_rewiring.py` | E[N_K] proof checks, exact variance, rewiring invariance, null outputs | `frontend/public/data/len/*` (exported graphs and Study 2 views), `src/rewiring.py`, `outputs/run_v2/study1/null_*` | `outputs/a05_endpoint_rewiring.json`, `a05.log` | MC 2026; rewiring 1000–1004 |
| `a06_nk_signal.py` | Exploratory N_K signal decomposition | `frontend/public/data/len/*`, manifest | `outputs/a06_nk_signal.json`, `a06.log` | folds 42, inner 0, bootstrap 7 |

The 92.7% overlap recomputation and the archive-vs-Table-3 matching were run as short inline commands from the manifest. Their logic is described in B.4–B.5 and fully reproducible from `data/manifests/manifest.parquet` and `frontend/public/data/len/index.json`.

**Commands:** `python research_audit/scripts/a0N_*.py` for N = 1..6 (a01 reads 5.4 GB, ≈ 2 min; a05 ≈ 1 min; others < 1 min).

**Tests:** project suite `python -m pytest` → 46 passed, 0 failed. Audit checks are embedded in the scripts:
- a05 asserts degree preservation for every rewired realisation;
- the regenerated Study 2 views were checked against stored features, 2,730/2,730 matching, by `src/export_dataset_explorer.py` (earlier session) and again here.

**Sources (fetched 2026-11-04):** arXiv:2503.00599v2 HTML; erdemub.github.io/large-engagement-network (+ download page); github.com/erdemUB/LEN and erdemUB/large-engagement-network; arXiv abs pages 2506.13912, 2010.08853, 2103.05045, 1912.09893, 1811.03508 (+ HTML v3), 2502.02379, 2407.04999; cs.stanford.edu/people/jure/pubs (listing only).

**Not accessed:** arXiv v1 of the LEN paper; the ICWSM/AAAI OJS page (bot-blocked); the full LEN archive and `metadata_graph.json` (multi-GB, not downloaded without approval); full texts of most prior works.

---

## Literature positioning (focused)

| Work (verified primary page) | Question / data / finding | Relation to us |
|---|---|---|
| Gopalakrishnan et al., LEN, ICWSM 2025 (arXiv:2503.00599v2) | Releases LEN; GNN and baseline classification | Source of the contradictions in B.1–B.2 |
| Gopalakrishnan et al., DECODE, ECML-PKDD 2025 (arXiv:2506.13912) | Density-aware walks (degree, core, truss) on LEN; ~12% / 5% accuracy gains; GNNs "struggle … due to the large size of its networks" | Uses degree/core density, closely related to our size and degree findings; abstract does not mention LEN-Small (full text not read) |
| Errica et al., ICLR 2020 (arXiv:1912.09893) | Structure-agnostic baselines rival GNNs on some benchmarks | Establishes the general phenomenon; we apply it to LEN |
| Cai & Wang 2018/2019 (arXiv:1811.03508) | Local degree profile matches kernels/GNNs on non-attributed benchmarks | Degree-based simple baselines are established; our degree-occupancy idea is related |
| Li et al., IJCAI 2024 (arXiv:2407.04999) | Dataset-effectiveness metric; correlation of intrinsic graph properties with labels | Establishes property–label audits across 16 datasets |
| Coupette et al., ICML 2025 (arXiv:2502.02379) | Mode-perturbation (RINGS) dataset evaluation | Methodological neighbour for benchmark audits |
| Yehudai et al., ICML 2021; Bevilacqua et al., ICML 2021 | Size generalisation / OOD extrapolation in graph classification | Size-shift literature; not about size as a label shortcut |
| Leskovec & Faloutsos, KDD 2006 | Graph sampling (bibliographic entry only verified) | Sampling distorts statistics; content not verified here |

Assessment:
- **Already established:** simple size/degree baselines rival complex models; dataset-effectiveness audits.
- **New application:** these checks on LEN-Small.
- **Potentially novel:** the selection-rule contradiction (a documentation finding), and the occupancy-based link between degree sequence and partial observation, with null-model invariance.
- **Not sufficiently supported:** any claim of novelty for F2. The search was focused, not exhaustive.

---

## Direct verdict

**1. What we know with confidence.**
- In the analysed 103-graph archive, graph size strongly predicts the file-name labels (counts alone: BA 0.884, AUC 0.931).
- Adding structure and content improves log loss and AUC; that result reproduces exactly.
- Balanced-accuracy differences are too small and too tuning-sensitive to interpret.
- Expected sampled-endpoint occupancy is a correct, degree-sequence-determined quantity.

**2. What we got wrong or overstated.**
- We described LEN-Small as "the 100 smallest graphs" and implied our archive is that release plus three events. The published tables contradict the rule, and our archive is not the tabulated release.
- Study 2's "training regime matters far more than feature choice" is partly a threshold effect (N_K) and partly size leaking into structural features (struct6).
- The K = 1000 single-view advantage is a decision-threshold effect, not additional information.
- The arrangement null cannot speak to degree-sequence signal, by construction.

**3. The single most important unresolved issue.** The identity of the dataset: which graphs LEN-Small officially contains, how they were selected, and how our archive relates to them. Every population-level interpretation depends on it.

**4. What to investigate next, and why.** Obtain LEN graph-level metadata, with your approval for a ≈ 1.9 GB download, or ask the authors, to reconstruct the selection and identify our 3 extra graphs. This is cheap, decisive, and gates both the paper's framing and any replication of the occupancy finding.

**5. What to avoid.**
- Do not claim the archive is the official LEN-Small or a superset of it.
- Do not claim the 92.7% overlap or any account-level dependence.
- Do not read BA differences at this sample size as effects.
- Do not present the exploratory degree-heterogeneity result as established, or as novel, before replication.
- Do not interpret sampled views as containing more information than full graphs.
- Do not add model families, GNNs or hyperparameter searches to chase a positive result.
