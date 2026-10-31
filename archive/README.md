# Archive (superseded, kept for provenance)

| File | Status | Why it is kept |
|---|---|---|
| `LEN_Small_Implementation_Guide.md` | **Superseded.** Original implementation plan written before the archive was inspected. Several of its assumptions are wrong (it expects a ZIP of edge lists, a `metadata.csv` label file and 100 events, 51/49). | `reports/methodology_audit.md` compares the plan's assumptions with what the audit actually found ("Initial Guide Assumption" vs "Verified Empirical Reality"). Do not use it as a description of the final pipeline; see the top-level `README.md`. |
| `paper_v1_superseded/` | **Superseded.** The first paper ("Measurement validity audit"), as the PDF that the website served (its Word source, identical in content, was removed), built from `outputs/run_final` before the coreness and frozen-model fold-alignment corrections. | Correction history. Current paper: `paper/LEN_Small_Predictive_Information_Beyond_Scale.pdf` (IEEE LaTeX source in `paper/`), built from `outputs/run_v2`. |
| `audit_v1_superseded/` | **Superseded.** The first methodology-audit report (`methodology_audit.md`, its PDF website download and `generate_audit_pdf.py`), the `run_final` checkpoint report, and the website test that pinned `run_final` values. Their numbers predate the corrections (e.g. combined-model BA 0.923, now 0.894). | Correction history only. Every current number is in `outputs/run_v2/paper_results.json`. |

`LEN_Small_Implementation_Guide.md` refers to `reports/methodology_audit.md`, which now lives in `audit_v1_superseded/`.
