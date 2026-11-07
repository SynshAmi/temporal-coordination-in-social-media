# Final pre-submission audit

**Date:** 2026-11-06
**Scope:** `paper/main.tex` with its generated macros, figures and bibliography, checked against the repository's outputs, the audit reports and the decisions in this folder.

**Constraints observed:**
- No experiment, refit or new analysis was run.
- No research code, output or data file was changed.
- One project file was edited (`paper/main.tex`).
- All checks that write files ran against scratch copies.

---

## A. Executive verdict

**Not ready: material issues remain.**

The numbers are sound.
- Every value in the manuscript is a generated macro.
- The macros regenerate byte-identically from `paper_results.json`.
- The independent verification script passes 21/21 and reproduces its stored report byte for byte.
- All 46 tests pass, and all 25 headline claims are found in the built PDF.

**The manuscript is the pre-audit version.** None of the decisions in `AUTHOR_DECISIONS.md` or `FINAL_MANUSCRIPT_PLAN.md` has been carried into it yet. I corrected the retired or factually wrong statements that could be fixed without new numbers or framing choices (§B.3). Six material problems remain, and each needs an author decision or new manuscript text:

1. **The framing contradicts the provenance finding.**
   - The title ("What Does LEN-Small Measure? … Beyond Scale"), the first abstract sentence, the keyword "benchmark validity" and the Discussion still present the archive as the LEN-Small benchmark.
   - "Scale", "size-like" and "label information" are used without definition (K02; plan §8 item 18).
2. **Table I prints a retired claim.** Its row "Official LEN-Small … smallest 100 of 314 by node count" comes from `src/export_latex_results.py`, so it cannot be fixed in `main.tex` (§E).
3. **Results the plan treats as core are missing from the paper:**
   - the 20-partition sensitivity estimate for C1 (−0.094, AUTHOR_DECISIONS §1);
   - structure beyond counts alone vs beyond counts and content (§2);
   - the no-text exclusion (§3);
   - text-retention figures;
   - every `token_std` result (plan R4).

   Adding them requires new macros from existing outputs and new prose. That is drafting, not correction.
4. **Edge-limited results are reported almost only in balanced accuracy (BA):** Table VI, Table VII, Fig. 3, and most of §V-D. Full-graph conclusions rest on log loss, so the two halves of the paper use different evidence standards (§D.2).
5. **The audit outputs the paper will cite are not in version control.** `research_audit/` is untracked in git. Any number taken from it must be committed, or moved into the pipeline's outputs, before the paper can claim one-command reproducibility.
6. **Length and structure.** The edited build is about 7.1 pages of text, against a 10–11-page target. The Results order (counts → null → matching → edge-limited → mechanism) does not follow the plan's four-step argument (§D.1).

Items 2 and 5 are technical. Items 1, 3, 4 and 6 need author input and writing. None needs a new experiment.

---

## B. Scientific verification

### B.1 Checks performed

| Check | Result |
|---|---|
| All 184 inline macros and 7 table bodies, regenerated from `outputs/run_v2/paper_results.json` | Byte-identical to `paper/generated/results.tex` |
| Independent recomputation of every reported comparison (`src/verify_studies.py`) | 21/21 pass; report byte-identical to the stored one |
| 25 headline claims searched in the built PDF (`claim_evidence_audit.check`) | 25/25, both before and after the edits |
| "Primary split shows the smallest C1 BA gain" | **Wrong.** Seeds 42 and 5 both give +0.0098 (`outputs/run_v2/study1/repeated_splits_lr.csv`). Corrected to "tied for the smallest" |
| "C2 and C3 BA differences changed sign across splits" | Confirmed (same CSV) |
| Duplicate file: dotless "ı" vs "i" | Confirmed (`data/manifests/duplicate_files.json`; identical SHA-256) |
| E[N_K] Monte Carlo check on three events | Confirmed: 114.2 vs 113.7, 301.5 vs 301.4, 334.7 vs 334.4 (verification log) |
| R² of log E[N_K] (77.2% / 93.0% / 93.0% with Gini) | Confirmed by the independent script |
| LEN counts in Related Work | The LEN arXiv abstract says 179 campaign and 135 non-campaign (314). The project page says 305 graphs (170 campaign), but its own subtype rows sum to 179. LEN-Small is 51/49 on the project page. The selection rule is not stated on the project page or the arXiv abstract page |
| "A complete rerun reproduced every reported value" (P49, previously UNVERIFIED) | **Now verified.** `reports/reproducibility/REPRODUCIBILITY_REPORT.md` and `comparison.json`: 37/37 artifacts identical. The sentence is kept |
| Content-feature definition vs `src/features.py` | The manuscript said only "cleaned message texts" and "standard deviation of message token counts". Now stated exactly (§B.3) |
| Gini in eq. (1) vs `features.gini` | Identical formula |

### B.2 The ten known issues

| # | Issue | State in the manuscript before this pass | Action |
|---|---|---|---|
| 1 | 103 graphs (52/51), not LEN-Small | Abstract: "three more than the official 100-graph release". Data: "why the archive holds three additional events". Limitations: "103 events rather than the official 100" | **Corrected** in all three places. The title and Table I remain (§A items 1–2) |
| 2 | Account overlap | Not claimed. "Cross-event account overlap cannot be measured" (Data) | None needed |
| 3 | "Topology contributes nothing" | Not claimed. "Neither shows that topology is uninformative" (§V-B) | None needed |
| 4 | Structure beyond counts vs beyond counts and content | E2 (−0.091) reported. M2 − M0q not reported as a contrast. No sentence states the conditional distinction | **Not corrected.** It needs the 20-partition values (new macros) and the AUTHOR_DECISIONS §2 wording |
| 5 | "`token_std` accounts for most of the content gain" | Not claimed; `token_std` results are absent | None needed. The plan's R4 is still to be written |
| 6 | Stability vs utility of `token_std` | Absent | None needed now. Apply when R4 is drafted |
| 7 | Gain grows with K | Not claimed. The paper says ensembling and content effects are small at every budget | None needed |
| 8 | Cohorts differ by K | Stated, with the common cohort and per-K counts. "Content … intervals that include zero at every budget" was BA-only (K10) | **Qualified:** log-loss intervals for the same contrast exclude zero at K = 500 and 1000 (uncorrected) |
| 9 | C1 after excluding the no-text events | Not reported, so not overstated | Report it when the 20-partition results are added (AUTHOR_DECISIONS §3) |
| 10 | Prediction vs causation | Mostly sound. "Training regime mattered more than any feature choice" and "training … matters far more" were retired claims (P11, P39) | **Corrected** in the abstract, Introduction, Results, Discussion and Conclusion |

### B.3 Discrepancies corrected in `paper/main.tex`

| Location | Was | Authority | Type | Now |
|---|---|---|---|---|
| Abstract | "a distributed archive … three more than the official 100-graph release" | claim_ledger P02; A B.4 | Factual error (implies a superset) | "an archive of 103 event graphs downloaded from the LEN project website, whose relation to the published 100-graph LEN-Small subset could not be established" |
| Abstract | AUC gain with no adjustment stated | P07 | Missing qualification | "(unadjusted)" |
| Abstract | "Training on observations of the kind being scored matters far more than averaging repeated views" | P11; A05 | Outdated (retired) claim | Mixed regime and feature-meaning wording |
| Abstract | "what the released labels are predictable from" | P42 | Outdated wording | "what the archive's labels are predictable from" |
| Intro ¶2 | "LEN-Small consists of the 100 smallest LEN graphs by node count, yet its comparison events are still …" | P13, P14; A01 | Factual error (the stated rule contradicts the published tables) | Rule attributed to the authors, with the inconsistency noted; the size difference attributed to the analysed archive |
| Intro ¶2–3 | "the released archive"; "the distributed LEN-Small archive" | K01 | Outdated wording | "the analysed archive"; "this archive" |
| Intro bullet 3 | "and training matters … far more than ensembling views" | P11 | Retired claim | Reworded as in the abstract |
| Related Work | "LEN provides 314 … (179/135) … LEN-Small, the 100 smallest graphs by node count" | P17, A09; LEN arXiv abstract and project page (fetched this pass) | Missing qualification | Both official counts given with their sources; the rule described as stated, not as fact |
| Data §III-A | "This archive does not match the official release … why the archive holds three additional events" | P19; A02 | Factual error | "not the published LEN-Small subset … differs in membership and graph sizes, not only in its number of events" |
| Data §III-A | No statement on missing text | R12; T01 | Missing qualification | Many texts are null, retention is lower in campaign graphs, two campaign graphs have none, and content features describe retained text only (no numbers added) |
| Methods §IV-A | Content features defined loosely | `src/features.py`; T01 | Methods–code mismatch by omission | Exact cleaning, null handling, per-edge counting, ddof-1 SD, the one-text rule, and median imputation |
| Methods §IV-E | Frozen-transfer fold rule stated only in the Corrections section | `src/train.frozen_model_test_events` | Moved | One clause in the FK definition |
| Results §V-A | "Neither arrangement beyond degree (C2) nor content alone (C3) accounts for this gain" | K07 | Ambiguous interpretation | "showed a detectable log-loss change" |
| Results §V-A | "this indicates complementary information in the combined feature set" | K07; AUTHOR_DECISIONS §2 | Retired interpretation | "LR is additive, so these contrasts do not identify a modelled interaction, and the source of the C1 gain is not isolated" |
| Results §V-A, Limitations | "primary split shows the smallest gain" | `repeated_splits_lr.csv`; P29, P44, K13 | Factual error (tie) | "tied for the smallest" |
| Results §V-D | "Content added at most a few points of BA, with intervals that include zero at every budget" | P38; contrast_inventory (S2 rows) | Missing qualification (selective metric) | Log-loss qualification added |
| Results §V-D | "The training regime mattered more than any feature choice we tested" | P39; A05; A13 | Retired claim | "Models trained on views scored higher than full-graph models applied to views", plus the feature-meaning caveat with a cross-reference to §V-E |
| Discussion | "released labels … how large an event graph is"; "Anyone using LEN-Small as a benchmark …"; "A model needs to be trained …"; "one released archive, which differs from the official release" | P42, P43, P11, K01 | Outdated wording | Counts-based, archive-scoped wording |
| Limitations | "103 events rather than the official 100, for an unknown reason"; "LEN-Small itself is selected by node count" | P46; A01 | Factual error | P46 wording; text-retention limitation added |
| §VIII "Methodological Corrections" | A full section | Your instruction: no formal corrections section | Editorial | Removed. The coreness rule was already in §IV-A, the fold rule is now in §IV-E, and one sentence in Code and Data Availability points to the repository record |
| Conclusion | "LEN-Small's labels … predictable from graph size"; "training … mattered far more than ensembling" | P42; P11 | Retired claims | Counts-based wording; mixed regime and feature-meaning wording |
| Data Availability | "the raw LEN-Small archive" | K01 | Outdated wording | "the raw archive" |

No number was typed into the manuscript. The only digits added are the K values 500 and 1000 and the word "two".

### B.4 Discrepancies found but not corrected

| Location | Issue | Authority | Why not corrected |
|---|---|---|---|
| Title, `pdftitle`, keywords | "LEN-Small", "Beyond Scale", "benchmark validity", "Retained" | K01, K02 | Title deferred by you |
| Abstract sentence 1 | "LEN-Small is a benchmark … We ask what these labels can be predicted from" | K01 | Part of the framing rewrite (plan §1–3) |
| Table I, row 3 | "Official LEN-Small: 100 (51/49); smallest 100 of 314 by node count" | A01, A09 | Generated by `src/export_latex_results.py`; see §H.2 |
| §V-A | C1 reported only on the primary partition and 10 splits; the 20-partition estimate is absent | AUTHOR_DECISIONS §1 | Needs new macros from `research_audit/outputs/s02_contrasts.csv` |
| §V-A | M2 − M0q not reported; E2 not framed as conditional on content | AUTHOR_DECISIONS §2 | Same |
| §V-D, §V-E, abstract | "size-like information", "label information", "sampling did not detectably reduce the label information" | K02; plan §8 item 18 | Pervasive wording tied to the framing decision. Recommended replacement: "information" → "predictive performance"; "size-like" → "determined largely by node count and the degree sequence" (P10) |
| §V-D | K = 1000 KK − FF ΔBA +0.056 presented without AUC (0.953 vs 0.951) | P09, A05 | The AUC values are not in the macros |
| §V-E | E[N_K] univariate AUC 0.965 vs 0.934 is in-sample and not cross-validated | P41 | "In-sample" should be added. I left it because the macro context is unclear about whether the 0.934 node-count AUC is also in-sample; check `paper_results.json` `mechanism` before rewording |
| Related Work | "DECODE adds density-aware random-walk embeddings built on degree, core and truss numbers" | Not checked against the DECODE paper body | Not verifiable from the abstract page alone |

---

## C. Methodology and reproducibility

### C.1 Commands run

All from the project root. Scratch path: `<scratch-dir>/final_audit` (S below).

| # | Command | Outcome | What it verifies |
|---|---|---|---|
| 1 | `python src/export_latex_results.py --out S/results_regen.tex` then `diff -q paper/generated/results.tex S/results_regen.tex` | Pass: identical (184 inline values, 7 tables) | The paper's numbers are exactly what the current exporter produces from `paper_results.json` |
| 2 | `python -m pytest -q`, run twice (before and after the edits) | Pass: 46 passed, both times | Feature definitions, ingestion hashes, rewiring invariants, sampling, leakage guards, macro currency, no typed results in `main.tex`, bibliography currency, paper–website parity |
| 3 | `python src/verify_studies.py --config S/verify_config.yaml`. The config is identical to `configs/v2_coreness_fix.yaml` except `run_dir` points to a copy of `outputs/run_v2` | Pass: 21/21; output byte-identical to `outputs/run_v2/verification/verification_report.json`; 2 min 37 s | Independent reimplementation of metrics, bootstrap, Holm, LR cross-validation, tuning-leakage tests and the E[N_K] mechanism |
| 4 | `claim_evidence_audit.check(...)` in memory, on the scratch PDFs from before and after the edits (the script's own writer was not called) | Pass: 25/25 both | Headline values appear verbatim in the built paper |
| 5 | pdflatex → bibtex → pdflatex ×2, in scratch copies, before and after the edits | See §F | Build health |

**Not run:**
- **The full pipeline** (`run_pipeline.py`, about 53 min). It was unnecessary: command 1 shows the macros match the stored results, and the 2026-10-31 reproducibility audit already reproduced all 37 artifacts from the raw archive.
- **`src/repro_compare.py`.** It would overwrite `reports/reproducibility/comparison.json`, and its `repro/` input no longer exists.

**Interpretation.** These checks establish implementation consistency on one machine. They are not independent scientific replication.

### C.2 Methods text vs code

| Methods statement | Code | Status |
|---|---|---|
| Counts are log(1+\|V\|), log(1+\|E\|) | `features.extract_scale_features`, `np.log1p` | Matches |
| LR with median imputation, standardisation, balanced class weights | `train.make_logreg_pipeline` | Matches |
| Inner three-fold CV inside each outer fold | `train.run_cv` → `tune_logreg_C(inner_cv=3)`, StratifiedKFold with shuffle | Matches. The inner CV's `random_state=0` is not stated (minor) |
| Five-fold stratified outer folds | `splits.make_event_folds`; config `n_folds: 5`, seed 42 | Matches. The seed is not stated in Methods (minor) |
| Bootstrap resamples 2,000 (Study 1) and 1,000 (Study 2) | config `study1.n_bootstrap`, `study2.n_bootstrap`; seed 7 | Matches. The seed is not stated (minor) |
| Gini, eq. (1) | `features.gini` | Matches |
| Content cleaning and `token_std` | `features.clean_text`, `extract_content_features` | Now matches (it was underspecified) |
| Coreness on the undirected projection without self-loops | `features.core_numbers_undirected`; `tests/test_features.py` | Matches (tested) |
| Directed double-edge swaps preserving degrees, self-loops fixed | `src/rewiring.py`; `tests/test_rewiring.py` | Covered by tests; code not re-read this pass |
| K uniform edges without replacement, 10 seeds, features from sampled edges only | `src/sample_views.py`; `tests/test_sampling.py`; t01 raw-archive check of the stored samples | Matches |
| FK: each event scored by the held-out full-cohort fold model | `train.frozen_model_test_events`; `tests/test_leakage.py` | Matches; now stated in Methods |
| Training-fold preprocessing (imputation and scaling inside the pipeline) | sklearn `Pipeline` | Matches |

**Not described in the manuscript, though it should be:**
- the random seeds;
- that the two campaign graphs without text are imputed, which is now stated qualitatively;
- that `token_std` is post hoc. This only matters once its results are added.

### C.3 Remaining reproducibility limitations

- `research_audit/` is untracked (§A item 5).
- The official PDFs (`paper/main.pdf`, `paper/LEN_Small_Predictive_Information_Beyond_Scale.pdf`) and the website copy were **not rebuilt**. They still show the pre-edit text. `python paper/build.py` overwrites the official PDF, and the parity tests (`test_website_serves_current_paper_pdf`, `test_website_title_is_paper_title`) will then fail until the website payload is regenerated. Do both together once you accept the edits.
- Reproduction has been demonstrated on one machine only (stated in the paper).

---

## D. Manuscript and editorial review

### D.1 Structure and narrative

**Against the plan's four-step argument:**

| Plan step | Current manuscript | Gap |
|---|---|---|
| 1. Counts | §V-A ¶1, Table II | Present. It leads with BA; see D.2 |
| 2. Beyond counts on full graphs | §V-A, §V-B (null), §V-C (matching) | The conditional structure result is missing. Matching (an exploratory point estimate with no intervals) sits in the main line of the argument; the plan moves it to the supplement |
| 3. Edge-limited: the count that remains | §V-D, then §V-E | The mechanism (§V-E) comes *after* the retraining paragraph that depends on it. I added a forward reference; reordering §V-E before the retraining paragraph is better |
| 4. Message-length dispersion | Absent | To be drafted (plan §5.5 R4) |

**Other structural observations:**
- **Introduction.** It opens with a general description of coordinated campaigns; the plan's ¶1 opens on what a score is taken to mean. The research questions arrive in ¶2, which is good. The three-bullet findings list conflicts with the plan's prose contributions.
- **Related Work** is proportionate (two paragraphs).
- **Discussion** mostly interprets without repeating numbers. ¶3 still relies on "size-like".
- **Limitations** are specific. Missing: the post-hoc selection of `token_std` (once added) and the K-cohort confound for any budget comparison.
- **Conclusion** answers the research questions in three points. It will need updating when R4 is added.

**Long paragraph.** §V-A ¶4 (about 300 words) mixes split variability, row-order sensitivity, the C grid and HGBT. Recommendation:
- keep one or two sentences on split variability;
- move row order, the C grid and HGBT to the supplement, as in the plan;
- this also frees space for the R4 material.

### D.2 Metrics

**Current state.**
- **Methods** declares BA and log loss as "distinct estimands", with AUC "secondary". No primary metric is named.
- **The abstract and Results** lead with BA.
- **Edge-limited tables and Fig. 3** are BA only.
- **The Conclusion** treats probability quality and decisions as parallel findings.

**Recommendation (your decision).**
- **Lead metric: log loss** for every incremental (nested) comparison.
  - It is a proper scoring rule that uses the full predicted probability, so it is the most sensitive comparison available with 103 events.
  - It does not depend on a threshold. BA moves by ±0.01–0.02 with tuning tie-breaks and row order (A04, and the paper's own row-order result).
  - It is the metric on which the main full-graph result rests.
- **AUC** as the supporting ranking metric. It separates genuine ranking change from threshold shifts, as in the K = 1000 BA gain and the N_K frozen-transfer collapse.
- **BA** as the decision-level metric. Report it beside the others, with its pre-specified null C1 result stated as prominently as the log-loss gain.

**Two cautions:**
1. Both the BA and log-loss families were pre-specified. Say so, and present the lead-metric choice as a presentation decision. Otherwise, leading with the metric that shows an effect reads as metric selection.
2. Applying this consistently means adding log loss and AUC to the edge-limited results. Those values exist in `outputs/run_v2/study2/results.json` and `research_audit/outputs/v02_performance.csv`, but they are not in the macros.

**Consistency points to fix when redrafting:**
- abstract sentence 2 (BA first);
- §V-A ¶1 (BA first);
- Table VI, Table VII and Fig. 3 (BA only);
- the Conclusion's second point (already balanced).

### D.3 Terminology

- **`token_std`** is now defined exactly in §IV-A as "the sample standard deviation of per-text whitespace token counts". Elsewhere the paper says only "the standard deviation of message token counts" (consistent).
- **Recommendation: "token-count dispersion".** It names what is measured (whitespace tokens, not characters), and the reader never has to translate "length". The final choice is yours.

**Inconsistent pairs to settle in the glossary (plan §10.5):**
- "fold split" / "split" / "partition";
- "comparison" / "non-campaign" (Related Work uses LEN's term, which is defensible if it is said once);
- "size" / "scale" / "counts";
- "Study 1/2" / "RQ1/RQ2" / "full / edge-limited";
- "view" / "sample".

### D.4 Language

The edits above remove the retired causal-sounding claims. Remaining patterns:
- **Bolded run-in claims** ("For classification decisions, no contrast shows …"). They are clear, but they emphasise conclusions in the Results. Consider plain topic sentences.
- **Long sentences** that list three or more macros in sequence (§V-D ¶1). Readers would be better served by a table reference.
- **One hedge stack:** "These are point estimates … so they are not evidence of above-chance performance, and matching also changes the evaluated population" (§V-C). This resolves itself if matching moves to the supplement.

---

## E. Figures, tables and bibliography

### E.1 Current visuals

All 11 are referenced in the text and numbered in order of first reference.

| Item | Issue | Resolution |
|---|---|---|
| Table I (cohort) | Row "Official LEN-Small … smallest 100 of 314 by node count" is retired. Missing usable-text row | **Open (technical):** change the row text in `src/export_latex_results.py` (§H.2) |
| Table II (levels) | Fine. Plan: keep a compact version (M0q, M4) in the main text, with the full table to the supplement | Author decision |
| Table III (primary contrasts) | Stacked cells collided with the rule above | **Fixed** (layout only, §G) |
| Fig. 2 (contrast graphic) | Duplicates Table III | Recommend the supplement (plan §6) |
| Table IV (null) | Fine. Plan: supplement, with two numbers in the text | Author decision |
| Table V (matching) | Stacked-cell collision **fixed**. Exploratory, with no intervals | Recommend the supplement |
| Table VI (single-view BA) | BA only | Replace with the plan's Table 4 (A–D, log loss / AUC / BA) or add columns |
| Fig. 3 (single-view BA, common cohort) | BA only; the seven-line legend is wider than the plot; small tick labels | Recommend the supplement (plan S8). Not redrawn |
| Table VII (Study 2 contrasts) | Collision **fixed**. BA only | As Table VI |
| Fig. 4 (endpoint mechanism) | Inset text is small but legible at print size | Keep in the main text (plan Figure 2) |
| Fig. 1 (sizes) | Fine | Keep (plan Figure 1) |

The plan's Table 2 (feature ladder), Table 4 (A–D) and Figure 3 (`token_std` contrasts) do not exist in the manuscript yet. Their sources exist (plan §6).

### E.2 Bibliography

**Coverage.** All 16 entries are cited, and every citation has an entry (`test_bibliography_is_current` passes). There are no placeholders.

**Verification this pass** (authoritative pages fetched):

| Key | Status |
|---|---|
| `li` | Authors, title, IJCAI 2024, pp. 2144–2152 and DOI all match the IJCAI page |
| `coupette` | Authors, title, PMLR 267:11405–11434 match. No DOI exists, which is correct as entered |
| `len` | Authors and title match arXiv 2503.00599 ("ICWSM 2025"). Volume, pages and DOI not confirmed: the AAAI OJS page blocked automated access. **Check manually** |
| `decode` | Authors and title match arXiv 2506.13912 ("Accepted at ECML-PKDD 2025"). **Pages 283–298 not confirmed.** Check the Springer LNCS record |
| `jacobs`, `errica` | Publisher pages blocked. Details agree with standard records and with the IJCAI paper's reference list (`errica`). **Check manually** |
| `maslov`, `leskovec`, `varoquaux`, `nx`, `sklearn`, `efron`, `holm`, `austin`, `stuart` | Standard references. Details are consistent with the well-known published versions, but were not fetched |
| `repo` | No access date. Add the download date of the archive (`note = {Accessed …}`) |

**Do claims match their sources?**
- `len` now carries only what its abstract supports (314 graphs, 179/135).
- `repo` carries 305/170.
- The selection-rule statement relies on the LEN paper body, which I did not re-read; A01 was established from transcribed published tables.
- The other citations attach to general claims they support: simple baselines, sampling distortion, null models, small-sample CV.

**New citations.** None is needed for any current claim. None of the five papers from the Opus review was added.
- If the redrafted Introduction says that simple collection or labelling rules can drive benchmark scores in social-media classification, Hays et al., WWW 2023 (doi 10.1145/3543507.3583214), would directly support it.
- If it says that platform sampling differs from uniform sampling, Morstatter et al., ICWSM 2013 (doi 10.1609/icwsm.v7i1.14401), would support it.
- Read each before citing. The existing `leskovec` citation already covers sampling distortion in general.

---

## F. Build verification

| Item | Before edits | After edits |
|---|---|---|
| Compilation (pdflatex, bibtex, pdflatex ×2; MiKTeX) | Success | Success |
| Pages | 7 | 8: about 7.1 pages of text, with references [15]–[16] on page 8 |
| Undefined references or citations | None | None |
| Overfull boxes | None | None |
| Underfull boxes | 2 (Related Work ¶1, §IV-C) | 2 (same paragraphs; badness 7273 and 1902, cosmetic) |
| BibTeX warnings | 0 | 0 |
| Missing figures | None | None |
| Visual inspection (70 and 200 dpi renders) | Stacked table cells overlapped rules in Tables III, V and VII | Overlap resolved; no clipped captions; floats placed near their references |

The scratch builds are in S/`build_before` and S/`build_after`. The repository PDFs were not rebuilt (§C.3).

**Page estimate after implementing the plan:** about 9.5–10.5 pages including references.
- **Adds about 2.5–3 pages:** R4, the feature-ladder table, the A–D table, the `token_std` figure, the 20-partition and conditional-structure rows, and the data-retention text.
- **Saves about 1 page:** moving Fig. 2, Table V and most of §V-A ¶4 to the supplement.

This fits the 10–11-page target without padding.

---

## G. Modified files

| File | Change | Reason |
|---|---|---|
| `paper/main.tex` | About two dozen text edits, listed row by row in §B.3 | Correct retired or factually wrong claims; add missing qualifications; make Methods match the code for content features and frozen-transfer folds |
| `paper/main.tex` | Section "Methodological Corrections" removed; one sentence added to Code and Data Availability | Your decision: no formal corrections section. The two procedures are stated in Methods |
| `paper/main.tex` | Preamble: `\shortstack` redefined as a nested `tabular` | Layout defect: stacked cells overlapped table rules. No content change |
| `research_audit/manuscript_readiness/FINAL_PRE_SUBMISSION_AUDIT.md` | New | This report |

**Not modified:**
- `paper/generated/results.tex` and all of `src/`;
- `outputs/`, `data/` and `reports/`;
- the frontend, the bibliography, the figures and the existing audit files;
- the repository PDFs.

---

## H. Remaining decisions

### H.1 Subjective (yours)

1. **Framing rewrite:** title, abstract, Introduction ¶1, keywords, and the terms "information" and "size-like". The plan §1–3 gives the recommended direction.
2. **Lead metric:** see the recommendation in §D.2.
3. **`token_std` name:** "token-count dispersion" is recommended (§D.3).
4. **Supplement moves:** Fig. 2, Table V (matching) and Fig. 3 to the supplement; Table IV reduced to two numbers in the text (plan §6–7).
5. **Results order:** place the endpoint mechanism (§V-E) before the retraining paragraph.
6. **Introduction findings:** keep the three bullets, or change to prose (plan §4).

### H.2 Technical (must be done; no judgement required)

1. **Table I row.** In `src/export_latex_results.py`, change the "Official LEN-Small" row text, for example "Published LEN-Small: 100 (51 / 49); not the analysed archive". Then regenerate the macros and update `tests/test_paper_website_parity.py` expectations if any. This is a change to paper tooling, so you should authorise it.
2. **New macros for audit-derived values.** The plan's added results need exporter support:
   - 20-partition C1, M2 − M0q, E1, E2, E3 and the 101-event exclusion;
   - post-hoc `token_std` rows;
   - text retention;
   - Study 2 log loss / AUC and A–D.

   Typing them by hand would break the repository's "no typed results" test and convention.
3. **Commit the audit outputs** the paper will cite (`research_audit/outputs/`, `final_diagnostics/outputs/`, `manuscript_readiness/t01_*`), or move them into the pipeline. They are currently untracked.
4. **Rebuild the paper and website together** (`python paper/build.py`, then the website payload export), and rerun `pytest`.
5. **Confirm bibliographic details manually:** `len` (volume, pages, DOI), `decode` (pages), `jacobs`, `errica`; add an access date to `repo`.
6. **Check the in-sample status of the E[N_K] AUC comparison** (0.965 vs 0.934) in `paper_results.json`, and label it.

---

## I. Checklist before sending to your faculty mentor

- [ ] Decide on the framing and title, then rewrite the abstract, Intro ¶1 and the "information" / "size-like" wording (H.1-1).
- [ ] Decide the lead metric; make the abstract, Methods, Results, tables and Conclusion consistent (D.2).
- [ ] Authorise and make the exporter changes: Table I row, then new macros for the planned rows (H.2-1, H.2-2).
- [ ] Draft R4 (`token_std`), the conditional-structure paragraph, the 20-partition sensitivity and the no-text exclusion, using the AUTHOR_DECISIONS wording.
- [ ] Add the plan's Table 2 (feature ladder), Table 4 (A–D) and Figure 3; move Fig. 2, Table V and Fig. 3 (current) to the supplement.
- [ ] Commit the audit outputs the paper cites (H.2-3).
- [ ] Rebuild the paper and website; `pytest` 46/46; `claim_evidence_audit` passes; no undefined references.
- [ ] Verify the four bibliography entries by hand and add the `repo` access date.
- [ ] Read the full PDF once, start to finish, against `FINAL_MANUSCRIPT_PLAN.md` §8 (claim boundaries).
- [ ] Prepare the supplement (plan §7).
