# Final verification report

**Date:** 2026-11-07
**Branch:** `research-finalization`
**Scope:** the final manuscript (`paper/main.tex`, `paper/Finding_Signal_in_Network_Simplicity.pdf`), the result exports, the tests and the research website, checked against the stored pipeline and audit outputs.

**Constraints observed:**
- No experiment, refit or resampling was run.
- No research code or stored output in `src/` analysis modules, `outputs/run_v2/`, `outputs/revision_*` or `research_audit/outputs/` was changed.
- The only new arithmetic is presentation-level. Holm adjustment of the pipeline's stored Study 2 bootstrap p-values across the three budgets is computed in `src/export_audit_results.py`; the script checks its Holm implementation against the audit's own stored Holm values. It also takes counts and ranges over stored rows.

Passing tests show that the paper, the website and the stored results agree. They do not show that the scientific claims are correct; the claim boundaries are in `research_audit/manuscript_readiness/FINAL_MANUSCRIPT_PLAN.md` §8.

## 1. Checks performed

| # | Check | Command or method | Result |
|---|---|---|---|
| 1 | Test suite | `python -m pytest` | **47 passed** (46 before this branch, plus a new payload test for the audit values) |
| 2 | Paper macros regenerate from the stored results | `python src/export_latex_results.py --out <tmp>` then compare | Identical; 486 inline values, 10 tables |
| 3 | No hand-typed results in `main.tex` | `test_paper_source_has_no_hand_typed_results` | Pass |
| 4 | Headline claims appear verbatim in the built PDF | `python src/claim_evidence_audit.py` | **32 of 32** (25 earlier claims and 7 new ones: 20 partitions, conditional structure, no-text exclusion, post-hoc dispersion, text retention, N_K AUC, edge-limited content and dispersion). The earlier 10-split claim was replaced by the 20-partition claim, and the rewiring claim now checks the percentage the paper prints |
| 5 | Paper build | `python paper/build.py` | 9 pages; no undefined references or citations; no overfull boxes; 3 underfull boxes (cosmetic: Related Work ¶2, the null-model paragraph, one float page) |
| 6 | Build reproducibility | Two consecutive `paper/build.py` runs | Byte-identical PDF (SHA-256 prefix `616885df349964e8`) |
| 7 | Figures regenerate | `python paper/make_paper_figures.py --out-dir <tmp>` | Fig. 1 and Fig. 2 byte-identical to the committed files; Fig. 3 is new, plotted from the stored audit values |
| 8 | Audit values consistent with the pipeline | Assertions in `src/export_audit_results.py` | Pass: edge-limited models A and C equal the pipeline's KK and FF values (BA, log loss, AUC; tolerance 1e-9); Holm-across-K reproduced exactly; the post-hoc single-feature row agrees between `s02` and `s04`; seeds 42 and 1–9 of the 20 partitions reproduce the pipeline's stored splits (max log-loss difference 5.8e-15) |
| 9 | Independent recomputation | `python src/verify_studies.py` on a scratch copy of `outputs/run_v2` | See §1a |
| 10 | Bibliography | Crossref and arXiv metadata, via a web-fetch agent | §3 |
| 11 | Visual check of the PDF | Every page rendered at 70–80 dpi; Tables IV–VI and the references at full size | No clipped cells, collisions or float problems after the column-width fixes |
| 12 | Website build | `npm run build` (runs `sync-paper` first) | Success; served PDF byte-identical to `paper/` |
| 13 | Website in a browser | Vite dev server with Playwright: Paper, Results, Methods and Dataset pages at 1440 px; Paper and Results at 390 px | No console errors or warnings on a clean load; no horizontal page overflow on mobile; PDF, results JSON and dataset index return HTTP 200 (the PDF starts with `%PDF-`); all figure toggles render |
| 14 | Website values come from the payload | `test_website_source_has_no_hand_typed_results`, `test_payload_embeds_*_unchanged` | Pass |

### 1a. Independent recomputation

`src/verify_studies.py` was run against a scratch copy of `outputs/run_v2`. Its config is identical to `configs/v2_coreness_fix.yaml` except for the run directory.
- **21 of 21 checks pass.**
- The report it writes is byte-identical to the stored `outputs/run_v2/verification/verification_report.json`.

The script reimplements the pipeline's metrics, bootstrap, Holm correction, LR cross-validation, tuning-leakage tests and the E[N_K] mechanism. It does not cover the audit outputs; for those, see check 8.

## 2. What changed in the manuscript

The previous technical audit (`research_audit/manuscript_readiness/FINAL_PRE_SUBMISSION_AUDIT.md`) listed six material issues. Status of each:

| Issue | Resolution |
|---|---|
| Framing presented the archive as LEN-Small | Title *Finding Signal in Network Simplicity* (locked by the authors). The abstract, Introduction, Data, Limitations and Table I describe 103 graphs (52/51) downloaded from the LEN project website and not identical to the published LEN-Small subset. "Size-like information" and "label information" are no longer used as undefined terms |
| Table I printed the retired "smallest 100 of 314" row | Exporter row changed to "Published LEN-Small: 100 graphs (51 / 49); not identical to this archive". Rows added for edge texts, usable-text share and edge-limited cohorts |
| Outstanding results missing | Added, all as generated macros: the 20-partition sensitivity; conditional structure (M2 − M0q, E2, single-family conditionals); the no-text exclusion; text retention; flexible count baselines; per-event concentration and leave-one-out; every token-count dispersion result, labelled post hoc |
| Edge-limited results in BA only | Table V gives log loss, AUC and BA for every condition. Table VI leads with Δ log loss, with ΔBA beside it, and marks nominal intervals (†) separately from Holm-adjusted p < 0.05 across budgets (*). ΔAUC intervals exist only for the dispersion contrasts (Fig. 3); the table note says so |
| Audit outputs not in version control | Now referenced through `outputs/research_audit/audit_results.json`, with a `research_audit/README.md`. **Still uncommitted** (see §4) |
| Length and structure | The Results follow the plan's four steps: counts, what adds under full observation, the count that remains, token-count dispersion. The paper is 9 pages including references |

Also changed:
- The lead metric is log loss throughout, stated in Methods as a presentation choice, since both metric families were pre-specified.
- The prose term is "token-count dispersion".
- Status labels are defined in Methods and used in tables and captions.
- The ensembling statement now gives the small but detectable log-loss change, not only BA.
- The common-cohort sentence now states the one contrast whose direction differs.
- The E[N_K] AUC is described as computed from the score without fitting a model, which resolves the earlier "in-sample" question.
- Material moved out of the main text: the size-matching table (one sentence now), the null-model table (key numbers in the text), the BA-only single-view figure and the duplicate contrast figure.
- `austin` and `stuart` were removed from the bibliography, because matching is no longer described in enough detail to cite them.

## 3. Bibliography

| Key | Source checked | Result |
|---|---|---|
| `len` | Crossref record for doi 10.1609/icwsm.v19i1.35839 | Title, authors, ICWSM vol. 19, pp. 688–702, 2025 and DOI match. Crossref has no issue field; "no. 1" rests on the DOI suffix. Crossref writes "Sariyüce"; the entry keeps the authors' Turkish spelling "Sarıyüce" |
| `decode` | Crossref bibliographic search | Matches: LNCS, *Machine Learning and Knowledge Discovery in Databases. Applied Data Science Track and Demo Track*, pp. 283–298, online 2025 (print 2026), doi 10.1007/978-3-032-06129-4_17. **Entry updated** with the track title and the DOI. The LNCS volume number is not in the record |
| `jacobs` | Crossref record for doi 10.1145/3442188.3445901 | Title, authors, FAccT 2021 and pp. 375–385 match |
| `errica` | arXiv 1912.09893 (DBLP and OpenReview blocked automated access) | Title and the four authors match; the arXiv comment states publication at ICLR 2020. **Entry updated** with the arXiv identifier. ICLR proceedings have no page numbers |
| `repo` | `data/DATA_MANIFEST.md` | **Access date added** (Nov. 1, 2026, the manifest's recorded check of the project page) |

The other entries are standard references and were not re-fetched.

## 4. Remaining limitations and unresolved items

**Scientific:**
- One archive, of unknown provenance. Results need not generalize.
- Token-count dispersion was selected post hoc and no independent sample exists.
- In the edge-limited design, budget is confounded with cohort, and B and D were not computed on the common cohort below K = 1000.
- The Holm family for the pipeline's Study 2 contrasts (three budgets per contrast and metric) was chosen to match the audit's convention. A larger family would be more conservative. This is an author decision.

**Reproducibility:**
- The audit scripts are not part of the one-command pipeline, have no recorded end-to-end rerun, and were run on one machine.
- `research_audit/`, `outputs/research_audit/` and the new source files are **untracked until committed**. The paper's availability statement assumes they are.

**Length:** 9 pages against the 10-page target. Nothing was added to fill space.

**Website:**
- Not deployed, by instruction.
- Two lint warnings in `ResultsTable.jsx` (components defined during render) and the bundle-size warning predate this branch.

**Tooling:**
- The unslop skill is installed in `.claude/skills/unslop/`, but `.claude/` is gitignored, so the install is local to this machine.
- `/unslop` can be invoked only from a new Claude Code session, because skills are registered when a session starts. This pass followed its SKILL.md directly.

**Unresolved discrepancies:** none found between the paper, the website and the stored results.

---

# Addendum: refinement pass (2026-11-08)

Same branch and constraints: no experiments, no refits, no change to stored outputs. Main changes:
- authors and the equal-contribution note;
- the abstract;
- more explanation in the manuscript;
- the Holm family for the token-count dispersion contrasts;
- website refinements.

## Statistical review: Holm family for B − A and D − C

**How the contrasts were defined.** `research_audit/VIEW_LENGTH_DISPERSION_EXPERIMENT.md` §1 poses one research question with two parts: does dispersion add predictive value beyond N_K (B − A), and beyond N_K plus structure (D − C)? Its multiplicity rule ("Holm correction is applied across the three budgets, separately for each contrast and each metric") was a convention the audit chose; it is not tied to a pre-specified hypothesis, since the whole analysis is post hoc.

**The alternatives**, for each metric:
- **Three tests per contrast.** This is the audit's convention, and it treats B − A and D − C as two separate questions.
- **Six tests together.** This treats both contrasts at all three budgets as one family of tests of a single post-hoc claim.

**Effect of the six-test family** (adjusted p-values from the stored bootstrap p-values, primary partition, KK):

| Metric | Cells with adjusted p < 0.05 (3 per contrast) | Cells with adjusted p < 0.05 (6 together) | Printed values that change |
|---|---|---|---|
| Log loss | D − C at K = 1000 | D − C at K = 1000 | B − A at K = 1000: 0.084 → 0.140; D − C at K = 500: 0.096 → 0.192; bound for D − C at K = 1000: < 0.003 → < 0.006 |
| AUC | none | none | e.g. D − C at K = 1000: 0.066 → 0.132 |
| BA | B − A at K = 500 | B − A at K = 500 | bound: < 0.003 → < 0.006 |

No significance label in the paper or on the website changes.

**Recommendation: six tests together.**
- Both contrasts serve one claim (dispersion adds predictive value), and that claim was selected after looking at the data. Splitting the family in two adjusts for fewer tests than were run in support of it.
- The regime and feature contrasts from the pipeline are separate questions and keep three-budget families.
- Neither family corrects for the post-hoc selection itself; the paper says so.

**Implemented and reversible.**
- `src/export_audit_results.py` now stores `p_*_holm_family6` alongside the audit's `p_*_holm_across_K`.
- The paper (Methods, Table VI note, §V-D) and the website (Figures 4 and 5, Methods) use the six-test values and state the family.
- To revert, point `src/export_latex_results.py` (two lines in `vc()` and the `Tok*Holm` macro) and `frontend/src/lib/results.js` (two lines) back to `p_*_holm_across_K`.

## Other statistical checks (stored values)

- **Ten-view ensemble.** Single view − ensemble, log loss: −0.022 [−0.044, −0.007], −0.006 [−0.011, −0.002] and −0.002 [−0.004, −0.001] at K = 250, 500 and 1000. Balanced-accuracy intervals include zero. The paper says "lowered log loss by at most 0.022: detectable, but small". Correct.
- **Structure beyond N_K at K = 250.**
  - Budget-specific cohort (102 events): −0.006 [−0.079, +0.062].
  - Common cohort (73 events): +0.049 [−0.015, +0.137].
  - The sign changes and both intervals include zero. The paper now gives both values and states that this is not a reversal of a detected effect.
- **Log loss, AUC and BA.** They are kept distinct in every table and caption. One new point is reported: the BA gain for B − A at K = 500 survives adjustment, but its AUC difference is +0.002 [−0.037, +0.038], which marks it as a threshold effect.

## Checks performed in this pass

| Check | Result |
|---|---|
| `python paper/build.py` | 10 pages; no undefined references or overfull boxes; rebuild byte-identical (SHA-256 prefix `43710c3c6fc76b48`) |
| Author block and footnote | One centred block (three names, one affiliation). The equal-contribution note is the first, unmarked title-page footnote. It uses `\IEEEoverridecommandlockouts`, as in IEEE's conference template, because conference mode locks out `\thanks` otherwise (the log showed the lock-out warning before the fix) |
| Abstract length | 249 words (source text, each number counted as one word) |
| Generated values | Macros regenerate from the stored files (`test_paper_result_macros_are_current`); no hand-typed results |
| `python -m pytest` | 47 passed. The title test now accepts a `\thanks` after the title text |
| `python src/claim_evidence_audit.py` | 32 of 32 claims found verbatim in the PDF |
| `python src/verify_studies.py` (scratch copy) | 21 of 21 checks pass; report byte-identical to the stored one |
| Website build | Passes; served PDF byte-identical to `paper/` |
| Browser, 1440 px and 390 px | Results navigation scrolls to each section, stays under the header and marks the active section; the bar scrolls horizontally on mobile. Status labels sit inline. "Not computed" appears only in the value column. No horizontal page overflow. No console errors or warnings. PDF and data links return 200. Fonts load (Source Serif 4, IBM Plex Sans, IBM Plex Mono, with system fallbacks) |

---

# Addendum: final editorial pass (2026-11-08)

Presentation only. No numbers, analyses or statistical decisions changed. The six-test Holm family for B − A and D − C is kept, as approved.

## Paper

- **Author block.** Three IEEE conference columns (name, affiliation, email), in the order Suryansh Singh, Devansh Kewlani, Yashaswini K A, using the class's standard `\IEEEauthorblockN`/`\IEEEauthorblockA` with `\and`.
- **First-page footnote.** Unmarked, as before: "Suryansh Singh and Devansh Kewlani contributed equally to this work and are co-first authors; Yashaswini K A is the second author."
- **Build.** 10 pages; no undefined references or overfull boxes; abstract 249 words; two consecutive builds byte-identical (SHA-256 prefix `862a77f7bd8807ca`). All three emails are present verbatim in the PDF text.

## Website

- **Type.** EB Garamond for headings; STIX Two Text for text, interface and figures, with tabular lining numerals; a system monospace for code only.
  - Candidates were compared side by side on a temporary page, since deleted:
    - EB Garamond with STIX Two;
    - Computer Modern (CMU Serif and CMU Typewriter);
    - EB Garamond with Tinos and CMU Typewriter.
  - Computer Modern rendered light on screen, its typewriter numerals wrapped, and it needed over 2 MB of TTF.
  - Both fonts are confirmed loaded with no fallback.
- **Evidence status.** The per-result badges are removed. Status is now carried by italic running heads (Prespecified comparisons, Sensitivity analyses, Exploratory analyses, Post-hoc analyses), group notes on adjustment, and short italic notes where one finding has a secondary qualification. The paper's "primary" status is described on the Methods page as the prespecified comparisons.
- **Comparison charts.** Now an HTML table: comparison, interval plot, estimate, 95% interval, and adjusted p or partition count, with group heads. "Not computed" is shown only in the value columns.
- **Other changes.**
  - The title's negative letter-spacing was removed; it made the word spaces look oversized beside tightened letters.
  - The byline is one shared component.
  - The footer has no test counts.
  - The download reads "Research paper (PDF), 10 pages, full manuscript", with the page count read from the PDF.
  - The Methods numerals are enlarged.
  - The features table and equations no longer clip.
  - The mobile overflow on Methods is fixed.
  - The Results navigation finishes its scroll even when smooth scrolling is interrupted.

## Checks

| Check | Result |
|---|---|
| `python -m pytest` | 47 passed |
| `python src/claim_evidence_audit.py` | 32 of 32 claims found verbatim |
| `python src/verify_studies.py` (scratch copy) | 21 of 21 checks pass; report byte-identical to the stored one |
| Served PDF | Byte-identical to `paper/` |
| Browser, 1440 px and 390 px, all four pages | No horizontal overflow, no clipped text, no unnamed controls or images without alt text, no console errors or warnings. PDF and JSON return 200 (the PDF starts `%PDF-`). The mailto links are exact. Both external links return 200. Fonts load |

---

# Addendum: closure pass (2026-11-08)

Editorial and presentation closure. No experiment, stored prediction, estimate, interval, p-value or correction family changed. The six-test Holm family for B − A and D − C is unchanged.

## Changes

- **Authors (paper, website, README).** Suryansh Singh (co-first author), Devansh Kewlani (co-first author), Yashaswini K A (second author), each with the affiliation and exact email. The paper shows roles in the IEEE author blocks; the footnote and `\IEEEoverridecommandlockouts` are removed. The phrase "equal contribution" no longer appears in the paper, website, payload or README.
- **Abstract.** Rewritten as a broad-to-specific narrative, 250 words. The dataset is described neutrally; sampled nodes are "distinct nodes".
- **Provenance.**
  - Stated once in the paper, in the first Data and Provenance paragraph: obtained from the LEN project website; 104 files; one exact duplicate removed; 103 unique graphs (52/51); distinct from the dataset described in the published LEN paper.
  - The Introduction, Related Work, Table I, Limitations and Conclusion now refer to the 103-graph LEN project archive without restating it.
  - The README, `data/DATA_MANIFEST.md` and the dataset-explorer note were corrected to match. The latter two still carried the retired "three additional events" wording; the exporter string and the one served field in `index.json` were updated.
- **Terminology.** "Prespecified" throughout the paper, website, README and exporter labels.
- **Website.**
  - Body text 17.5 px, with small text and labels raised on a fixed scale; headings and metric values unchanged.
  - Header-title descender clipping fixed. The cause was `leading-none` combined with `truncate` (`overflow: hidden`); the hero title's leading was raised from 1.02 to 1.1.
  - Authors shown with one role line each.
  - Results navigation is event-driven: `scrollIntoView` with CSS `scroll-margin-top`, and the active item is held until `scrollend` or user scroll input. The timer fallback is removed.
  - Mobile results rows no longer overflow.
  - The 20-partition column is labelled "Partitions with lower log loss", which is what it counts, as in paper Table IV.
- **Lint.** The `ResultsTable.jsx` warnings (`SortHead` defined during render, reported at five call sites) are fixed by moving the component to module scope. The sort headers are now buttons. `oxlint` reports none.

## Checks

| Check | Result |
|---|---|
| `python paper/build.py`, twice | 10 pages; no undefined references or overfull boxes; byte-identical rebuilds (SHA-256 prefix `106338470ed4a5b5`); 6 underfull boxes (cosmetic spacing notes, no overflow) |
| Abstract | 250 words (source text, each number counted as one word) |
| PDF text | All three emails exact; "Co-first author" ×2, "Second author" ×1; no "equal contribution", "pre-specified", "distinct accounts", "mentor" or "supervisor" |
| `python -m pytest` | 47 passed |
| `python src/verify_studies.py` (scratch copy) | 21 of 21 pass; report byte-identical to the stored one |
| `python src/claim_evidence_audit.py` | 32 of 32 claims found verbatim |
| Served PDF vs `paper/` | Byte-identical |
| Stored results | `outputs/run_v2`, `outputs/revision_*` and `data/manifests` unchanged against HEAD; no file under `research_audit/outputs` modified after the audit runs |
| Website build, `oxlint` | Pass; 0 warnings |
| Browser (Playwright Chromium), 1440 px and 390 px, four pages | No overflow (all Results selector states checked on mobile), no clipped text, no broken images, no console errors or warnings, no retired wording in rendered text. EB Garamond and STIX Two Text loaded (body 17.5 px STIX). PDF, JSON and explorer index return 200. The download reads "Research paper (PDF) 10 pages · full manuscript" |
| Headed Google Chrome (installed Chrome, Playwright `channel: "chrome"`, `headless: false`) | Desktop 1440×900, mobile 390×844, and desktop with `prefers-reduced-motion: reduce`: 14 of 14 link clicks (all seven sections, forward and back) reach the section with the correct active item; the sticky bar is flush under the header; manual wheel scrolling marks all seven sections in order; reduced motion jumps immediately; no console errors. Frames ran at normal speed (2–9 ms for two frames) |
