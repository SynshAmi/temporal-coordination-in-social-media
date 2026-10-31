# Research Planning Documents

These two documents are the **planning briefs** written before the corrected two-study analysis. They record what was proposed and why. They are not results.

| File | Role |
|---|---|
| `LEN_SMALL_CONSOLIDATED_RESEARCH_ROADMAP.md` | Consolidated research plan from two independent reviews of the original paper |
| `CLAUDE_CODE_EXECUTION_PROMPT_LEN_SMALL.md` | Implementation brief derived from the roadmap |

Read them with these outcomes in mind:

- **Numbers quoted in them are from the superseded run** (`outputs/run_final`), for example the combined-model balanced accuracy of 0.9229. The corrected results are in `outputs/run_v2/paper_results.json` and the paper.
- **The "92.7% cross-event account overlap" they mention is not a real measurement.** Node identifiers in the release are per-graph indices (0 to N−1 in every graph), so equal identifiers in different graphs need not be the same account. The figure counted index values that recur across graphs. Account overlap cannot be measured from this release, and the account-dependence study proposed in the roadmap was dropped for that reason (see the paper's Limitations).
- **Scope decisions taken after these briefs were written:**
  - Study 1 (incremental information beyond scale) and Study 2 (single-view observation) were carried out.
  - Account-level dependence was not studied (no account identifiers).
  - References that could not be verified were excluded.
  - The publication venue is undecided.
