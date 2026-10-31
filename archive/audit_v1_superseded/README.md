# SUPERSEDED: first methodology audit (historical record only)

**Do not cite or reuse any number in this folder.** Everything here was produced from
`outputs/run_final`, before two defects were corrected (coreness features silently set to
zero because every graph contains self-loops; frozen full-graph models scoring some sampled
events with a model trained on their own full graph). For example, the combined-model balanced
accuracy reported here (0.923) is 0.894 in the corrected run.

| File | What it was |
|---|---|
| `methodology_audit.md`, `LEN-Small_Methodology_Audit.{md,pdf}` | First audit report and its website downloads |
| `generate_audit_pdf.py` | Script that rendered that PDF |
| `checkpoint_report.md` | `run_final` checkpoint report |
| `test_audit_frontend_integration.py` | Website test that pinned `run_final` values |

Current results: `outputs/run_v2/paper_results.json`, the paper in `reports/`, and the
correction history in its "Reproducibility and Correction History" section.
