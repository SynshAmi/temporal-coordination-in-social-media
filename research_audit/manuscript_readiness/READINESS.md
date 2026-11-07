# Manuscript readiness

This assessment covers the authoritative manuscript, `paper/main.tex` (+ `generated/results.tex`, built from `outputs/run_v2`). Evidence is in `claim_ledger.md`, `contradictions.md`, `contrast_inventory.md` and `token_std_verification.md`. The `token_std` raw-archive verification found no discrepancy.

## Section status

| Section | Status | What is needed |
|---|---|---|
| Title | Ready after a wording fix | Replace it; it presents the archive as LEN-Small (K01, K02) |
| Abstract | **Blocked** (B1–B3) | It summarises retired claims (P02, P11); rewrite once B1–B3 are settled |
| Introduction | Ready after a wording fix | P13, P14 and P19 wording; RQ wording per the blueprint |
| Related work | Ready after a wording fix | Official counts as the sources give them (P17) |
| Data and provenance | Ready after a wording fix | Add the retained-text row; cite individual mismatching graphs, not unverified tallies (A02) |
| Methods | Ready after a wording fix | Feature taxonomy (K02); `token_std` definition (T01); the null's blind spot (K15); the post-hoc statement (K05) |
| Results I (full graphs) | Ready after a wording fix | Retire P27/P28 interpretations (K07); add the 20-partition estimate (K14); BA as secondary (K04); "tied smallest" (K13) |
| Results II (edge-limited) | Ready after a wording fix | Retire "regime matters" (K09); add AUC/log loss (K04, K10); mark `token_std` as post hoc; no budget-dependence claim (inventory (c)) |
| Discussion | Ready after a wording fix | Remove causal and construct language (K03, K16) |
| Limitations | Ready after a wording fix | Replace P46 (K18); add post-hoc selection, text retention and the cohort confound (blueprint list) |
| Conclusion | **Blocked** (B1–B3) | It depends on the abstract-level decisions |
| Corrections / Data availability | Ready after a wording fix | B4 |

## Blockers, in order

1. **B1 — Framing decision.** Decide whether to describe the data as "a 103-graph archive from the LEN project website" throughout, and which title to use. Every section's wording depends on it.
2. **B2 — Primary uncertainty for C1.** Confirm that the pre-specified partition-42 result (Holm over three tests) stays primary and that the 20-partition repeat-averaged estimate (Holm over seven) is reported as sensitivity, each with its family named.
3. **B3 — Placement of `token_std`.** Decide whether the post-hoc `token_std` results appear in the main text or the supplement. Either way they carry "exploratory, post hoc" labels, BA significance is not cited as evidence, and no budget-dependence claim is made.
4. **B4 — Two untraced statements.**
   - The "complete rerun reproduced every value" sentence (P49) must be checked against `reports/reproducibility/REPRODUCIBILITY_REPORT.md`, or dropped.
   - The unverified tallies (A02, A03, A09, A10, R13, R14) must be dropped or cited with their source.

## Gaps that reporting cannot close

| Gap | Why it is material |
|---|---|
| **G1. Population identity.** The archive is not established as LEN-Small, and the selection is undocumented. | Every size–label association could partly reflect an unknown selection, so no result generalises beyond these 103 graphs, and the benchmark-level framing cannot be supported. |
| **G2. Post-hoc selection of `token_std` with no independent events.** | It is the only statistic with a notable increment beyond counts. No analysis within this archive can test it out of sample, so its incremental value remains a hypothesis. |
| **G3. Text-retention mechanism unknown.** 27.5% null texts, unevenly by class. | `token_std` is defined on retained text only. Without knowing why text is missing, its class difference cannot be separated from retention, which limits any interpretation of what it measures. |
| **G4. Dependence between events unmeasurable.** No account identifiers. | The effective sample size is unknown, so all intervals may be too narrow; the repeated hashtags show a small optimism. |
| **G5. B and D not evaluated on the common cohort below K = 1000.** | This is material only if the paper discusses budget dependence of `token_std`. Without these values the cohort change cannot be separated from K, and closing the gap would need a computation, not wording. |
