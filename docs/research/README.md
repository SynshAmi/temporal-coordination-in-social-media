# Research Planning Documents

This document is the **research plan** written before the corrected two-study analysis. It records what was proposed and why. It is not a results document.

| File | Role |
|---|---|
| `LEN_SMALL_CONSOLIDATED_RESEARCH_ROADMAP.md` | Consolidated research plan from two independent reviews of the original paper |

Read it with these outcomes in mind:

- **Numbers quoted in it are from the superseded run** (`outputs/run_final`), for example the combined-model balanced accuracy of 0.9229. The corrected results are in `outputs/run_v2/paper_results.json` and the paper.
- **The "92.7% cross-event account overlap" it mentions is not a real measurement.** Node identifiers in the release are per-graph indices (0 to N−1 in every graph), so equal identifiers in different graphs need not be the same account. The figure counted index values that recur across graphs. Account overlap cannot be measured from this release, and the account-dependence study proposed in the roadmap was dropped for that reason (see the paper's Limitations).
- **Scope decisions taken after the plan was written:**
  - Study 1 (incremental information beyond scale) and Study 2 (single-view observation) were carried out.
  - Account-level dependence was not studied (no account identifiers).
  - References that could not be verified were excluded.
  - The publication venue is undecided.
