# End-to-End Reproducibility Audit

**Date:** 2026-10-31 · **Pipeline:** `run_pipeline.py` (14 stages) · **Result:** the complete raw-to-results pipeline succeeded, and every verified artifact was reproduced.

## Method

- **Isolated run.** The full pipeline ran from the raw archive with `configs/repro_check.yaml`. That file is identical to the default `configs/v2_coreness_fix.yaml` except that every *write* location is moved under `repro/` (processed data, manifests, run directory, paper figures, website payload). The archive is read from the same place.
- **Clean start.** `repro/` did not exist beforehand, so no stage could reuse earlier intermediates.
- **Protected artifacts.** `outputs/`, `data/`, `reports/` and `frontend/public/` were SHA-256-hashed before and after the run. No result, paper or website file changed.
- **Comparison.** `src/repro_compare.py` compared every file of the verified run with its regenerated counterpart. The full table is in `comparison.json`.

## Stage outcomes

| # | Stage | Outcome | Time (s) |
|---|---|---|---|
| 1 | Ingest archive (SHA-256 deduplication) | ok | 91.4 |
| 2 | Data quality and schema validation | ok | 1.3 |
| 3 | Size matching and SMD diagnostics | ok | 0.9 |
| 4 | Edge-budget sampling and view features | ok | 65.1 |
| 5 | Base experiment grid | ok | 31.9 |
| 6 | Fold-aligned frozen-model evaluation | ok | 15.4 |
| 7 | Checkpoint report and pipeline figures | ok | 49.3 |
| 8 | Study 1 (nested models, null model, matching) | ok | 730.5 |
| 9 | Study 2 (single-view conditions) | ok | 1930.1 |
| 10 | Independent verification | ok (21/21 checks) | 203.7 |
| 11 | Export paper results | ok | 32.7 |
| 12 | Paper figures | ok | 4.6 |
| 13 | Export website payload | ok | 20.1 |
| 14 | Test suite | ok (28 passed, 0 skipped) | 3.5 |
| | **Total** | **no stage skipped or manually substituted** | **3180.5 (53 min)** |

The stage log is in `repro/outputs/run_v2/pipeline_stages.json`, and the full console log is in `repro/pipeline.log`. Both are local files: `repro/` is gitignored, so they are not in the published repository. Repeating the audit (below) recreates them.

**Failure handling.** A run with a missing archive stopped at stage 1, ran no later stage, logged the failure and exited with code 1.

## Comparison with the verified run_v2

| Outcome | Artifacts |
|---|---|
| Byte-identical | 30, including all study outputs, the verification report, `metrics.json`, processed data and all four paper figures |
| Equal after ignoring run-specific fields | 5, listed below |
| Equal on shared columns, with an extra column in the repro run | 1 (`predictions.parquet`) |
| Different or missing | 0 |

**The five files that match only after ignoring run-specific fields:**
- `manifest.parquet` and `matched_manifest.parquet`: only the `ingested_at` timestamp differs.
- `validation_report.json`: only `validated_at` differs.
- `paper_results.json`: only provenance strings naming the run's own output directory differ.
- The website payload: `exported_at` and the path strings differ.

**The extra column.** The regenerated `predictions.parquet` has one more column, `tuned_C`, which records each fold's selected regularisation strength. It was added to `src/train.py` after the verified base grid had been generated. All other columns are identical, so no reported value is affected. The verified file predates that diagnostic column.

**Conclusion:** every number in the paper and on the website is reproduced exactly from the raw archive by the current code.

## Changes made for this audit (pipeline plumbing only; no results or conclusions changed)

- **Stages 12–14 now follow the config like stages 1–11.** Previously:
  - Stage 12 (`make_paper_figures.py`) always read `outputs/run_v2` and `data/`.
  - Stage 13 (`export_frontend_data.py`) always wrote into `frontend/public/`.
  - The tests read fixed paths, and `test_leakage`/`test_sampling` read the superseded `sampled_views.parquet`, not the `sampled_views_v2.parquet` the results use.

  Now `make_paper_figures.py` takes `--config`/`--out-dir`, the payload location is `output.frontend_payload`, and the tests read their paths from `LEN_CONFIG` (set by the pipeline; it defaults to the authoritative config) through `tests/_paths.py`. With the default config, `paper_results.json` regenerates byte-identically and all 28 tests pass.
- **`run_pipeline.py`** times each stage, stops at the first failure with a clear message, and writes `pipeline_stages.json`.
- **`export_paper_results.py`** provenance strings name the configured run, not a hardcoded `outputs/run_v2`.

## Environment

- **System:** Windows 11 (10.0.26200), Intel 64-bit CPU with 16 logical cores, Python 3.12.10, Node v22.20.0, npm 10.9.3.
- **Python packages:** numpy 1.26.4, pandas 3.0.6, pyarrow 25.0.1, scikit-learn 1.9.0, networkx 3.6.1, scipy 1.17.1, PyYAML 6.0.3, matplotlib 3.11.1, pillow 12.3.0, tqdm 4.70.0, pytest 9.1.1, pypdf 6.19.0. These match `requirements.txt`.
- **Paper builder:** docx 9.5.1; Microsoft Word 16.0 (build 16.0.20527) for equations and PDF export.

The full record is in `repro/environment.txt`.

## Manual prerequisites and non-automated steps

1. **Raw archive.** Download `small_encoder_final.tar` from the LEN project (https://erdemub.github.io/large-engagement-network/), place it at the project root, and check its SHA-256 (`data/DATA_MANIFEST.md`). It is 5.8 GB and not redistributed.
2. **Dependencies.** Run `pip install -r requirements.txt`, then `npm install` in `frontend/` and `reports/paper/`.
3. **Paper documents are outside the pipeline.** `node reports/paper/build_paper.js` produces the .docx. The native equations (`finalize_equations.ps1`) and the PDF export (`export_pdf.ps1`) **require Microsoft Word on Windows**, driven through COM automation. On other systems the .docx builds, but its equations remain placeholders and no PDF is produced. The paper was not rebuilt in this audit; its inputs (paper results and figures) were verified identical instead.
4. **Claim-to-evidence audit.** Run `python src/claim_evidence_audit.py` after the PDF exists. It was re-run: 25/25 claims were found verbatim.
5. **Website build.** Run `npm run build` in `frontend/`. It was re-run successfully.

## How to repeat this audit

With the archive in place and dependencies installed (see the README):

```bash
python run_pipeline.py --config configs/repro_check.yaml   # about 53 min; writes only under repro/
python src/repro_compare.py                                 # writes reports/reproducibility/comparison.json
```

The comparison passes if every artifact is reported as `identical`: byte-identical, or equal after ignoring timestamps and run paths. A `numeric drift` result means floating-point differences, and the comparison shows their size. `DIFFERENT` or `MISSING` means the run did not reproduce.

## Addendum (2026-11-01): changes after this audit

Two pipeline stages were edited after the audit run. Neither change affects any reported number:

- **Stage 2 (`validate_len.py`).** The validation report previously stated "92.7% of accounts appear in more than one event". Node identifiers are per-graph indices (0 to N−1 in every graph), so that figure counted recurring index values, not accounts. The check now records the identifier scheme and states that account overlap cannot be measured.
- **Stage 7 (`evaluate.py`).** The checkpoint report and base-grid figures are now labelled as diagnostics. They were previously titled "Figure 1–4" and framed as conclusions. Their numbers are unchanged, and re-running the stage left `metrics.json` byte-identical.

The results file's label for the superseded 0.923 value was also strengthened; only that label string changed.

The affected stages (2, 7, 11 and 13) were re-run with both the default and the isolated configuration, and `src/repro_compare.py` again reports all 36 artifacts as identical. Stages 1, 3–6, 8–10 and 12 were not re-run, because their code and outputs did not change. The test suite now has 37 tests: new paper/website parity checks, a check of every ingested file's SHA-256 against `data/manifests/file_hashes.csv`, and a node-identifier check. All 37 pass against both configurations. The paper PDF was rebuilt with Microsoft Word 16.0 (build 16.0.20527).

## Limitations and remaining caveats

- **One machine.** Reproduced on the machine and package versions above only. Other BLAS builds, CPUs or library versions may produce small floating-point differences, and tuned hyperparameters are known to be sensitive to small changes (see the paper's Limitations).
- **Superseded run is an input.** `export_paper_results.py` reads the archived `outputs/run_final/metrics.json` for the one correction-history number (0.923). That file is an input, not regenerated by the pipeline.
- **Word dependency.** The paper .docx/.pdf build depends on Microsoft Word, as described above.
- **Disk space.** `repro/` (15 MB) is kept for inspection and is gitignored; it can be deleted.
