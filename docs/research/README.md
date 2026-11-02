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

## Revision analyses (November 2026)

Two analyses were added after the corrected run, during the paper revision. They read `outputs/run_v2/` without changing it, and their output locations are set in `configs/v2_coreness_fix.yaml`:

| Script | Output (config key) | What it does |
|---|---|---|
| `src/h1_c_grid.py` | `outputs/revision_h1_cgrid/` (`output.revision_h1_dir`) | Repeats the Study 1 logistic regression with a wider regularisation grid, after first checking that the original grid reproduces the stored predictions |
| `src/revision_supplement.py` | `outputs/revision_supplement/supplement.json` (`output.revision_supplement`) | Single view vs full graph on the same events, endpoint count vs structure, how often rewiring changes each arrangement feature, split sign counts, and repeated hashtags |

`python run_pipeline.py` runs both as stage 11. To run them on their own, use `python src/h1_c_grid.py`, then `python src/revision_supplement.py`, then `python src/export_latex_results.py` and `python src/export_frontend_data.py` to refresh the paper macros and the website payload.
