# Robustness audit

This folder is the record of the robustness audit run on the corrected results (`outputs/run_v2/`) before the paper *Finding Signal in Network Simplicity* was finalized. It is kept for provenance. Nothing in `src/` or `outputs/run_v2/` was changed by it.

The paper and the website use a fixed set of values from these outputs:
- the 20-partition sensitivity analysis;
- the conditional structure contrasts;
- the exclusion of the two graphs without usable text;
- text retention;
- every token-count dispersion result.

`src/export_audit_results.py` collects those values into `outputs/research_audit/audit_results.json`, with the source file for each block. The paper macros (`src/export_latex_results.py`), the website payload (`src/export_frontend_data.py`) and the claim check (`src/claim_evidence_audit.py`) read only that file.

## Contents

| Path | What it holds |
|---|---|
| `AUDIT_REPORT.md`, `INVESTIGATION_LEDGER.md` | The first audit pass and its running ledger. The ledger is kept as written; some entries are stale, as noted in later files |
| `FINAL_ROBUSTNESS_AND_CONTRIBUTION_ASSESSMENT.md` | The robustness analyses for Study 1 (scripts `s01`–`s04`) |
| `VIEW_LENGTH_DISPERSION_EXPERIMENT.md` | The post-hoc edge-limited analysis of token-count dispersion (scripts `v01`, `v02`) |
| `OPUS_OCCUPANCY_REPRODUCTION.md` | A check of the endpoint-occupancy argument (scripts `o01`–`o04`) |
| `final_diagnostics/` | Text availability and the no-text exclusion in views (`d01`, `d02`) |
| `manuscript_readiness/` | The raw-archive check of token-count dispersion (`t01`), the claim ledger, the author decisions, the manuscript plan and the pre-submission audit |
| `scripts/`, `outputs/` | The audit scripts and everything they wrote |

The reports are written for the authors and record the audit as it happened. Where they disagree with the paper, the paper and `audit_results.json` are authoritative: some early report statements were later retired (see `manuscript_readiness/AUTHOR_DECISIONS.md` and `FINAL_MANUSCRIPT_PLAN.md`).

## Rerunning

Run the scripts from the project root, after `python run_pipeline.py` has produced `outputs/run_v2/` and `data/processed/`. Each script writes only into this folder.

| Scripts | Needs the raw archive (`small_encoder_final.tar`) |
|---|---|
| `scripts/a01_archive_audit.py`, `scripts/o01_export_equivalence.py`, `scripts/o02_occupancy_features.py`, `scripts/s01_content_verification.py`, `manuscript_readiness/t01_token_std_raw_verification.py` | yes |
| `scripts/a02`–`a06`, `o03`, `o04`, `s02`–`s04`, `v01`, `v02`; `final_diagnostics/scripts/d01_*.py`, `d02_*.py` | no |

Run them in their numbered order within each prefix. `s02` refits Study 1 on 20 partitions and is the slowest step. Then refresh the collected values:

```bash
python src/export_audit_results.py
```

These scripts were run once, on one machine. Unlike the main pipeline, they have no recorded end-to-end rerun. Where they overlap with the pipeline, they reproduce its stored values exactly:
- the 10 shared partitions;
- models A and C in views;
- the content features recomputed from the raw archive.

`export_audit_results.py` checks the overlap with models A and C each time it runs.
