# Data Manifest

The raw LEN-Small archive is **not included in this repository** and must never be committed (it is excluded by `.gitignore`). Everything under `data/processed/` is regenerated from it by `run_pipeline.py`.

## Source and Acquisition

| Item | Value |
|---|---|
| Dataset | LEN-Small, from LEN: Large Engagement Networks |
| Reference | A. A. Gopalakrishnan, J. Hossain, T. Elmas and A. E. Sarıyüce, "Large engagement networks for classifying coordinated campaigns and organic Twitter trends," ICWSM 2025, doi:10.1609/icwsm.v19i1.35839 |
| Project page | https://erdemub.github.io/large-engagement-network/ |
| Download page | https://erdemub.github.io/large-engagement-network/download_page.html ("Small Dataset") |
| Archive file | `small_encoder_final.tar`, placed at the project root (path set by `data.archive_path` in the config) |
| Size of the copy analysed | 5,792,081,920 bytes (5.39 GiB) |
| SHA-256 of the copy analysed | `aaa1fdc13f5ee581b4006f024c0753871b652debbe31f97958082399729b1c75` |

As checked on 2026-11-01, the project page describes the small dataset as 5.4 GB, which matches the copy analysed. The download page, however, lists the file as 1.9G. If a newly downloaded archive has a different size or hash, it is not the archive analysed here, and results may differ.

### Verifying the archive

```bash
# Linux
sha256sum small_encoder_final.tar
# macOS
shasum -a 256 small_encoder_final.tar
# Windows (PowerShell)
Get-FileHash small_encoder_final.tar -Algorithm SHA256
```

The digest must equal the SHA-256 above. After `run_pipeline.py` (stage 1), `tests/test_ingestion.py` also checks every extracted graph file's SHA-256 against `data/manifests/file_hashes.csv`.

## Licence and Redistribution

- We could not identify an explicit licence or redistribution terms for LEN or LEN-Small. As of 2026-11-01, the project page, download page and GitHub repository (`erdemUB/large-engagement-network`) state none.
- Therefore **no raw LEN data is included**: no graph structures, edge lists, message texts, node or account identifiers, timestamps or embeddings.
- This repository does include derived event-level research outputs: event names (the archive's file names), per-event node and edge counts, file SHA-256 digests, per-event features and model predictions. They are the authors' own computations, published only so the results can be checked and reproduced. They are **not** officially licensed or endorsed by the LEN authors, and they are excluded from the repository's MIT licence (see `NOTICE.md`).
- To use the data itself, obtain it from the LEN project and cite the LEN paper above.

## Contents and Provenance Notes

- The archive holds 104 NetworkX node-link JSON files. One campaign graph appears twice under file names that differ only in a Turkish dotless `ı` versus ASCII `i`; the two files are byte-identical (`data/manifests/duplicate_files.json`). Ingestion keeps one copy, leaving **103 canonical events (52 campaign, 51 comparison)**.
- **This does not match the official release.** The LEN paper describes LEN-Small as 100 graphs (51 campaign, 49 non-campaign), the smallest 100 of 314 LEN graphs by node count. Why the archive holds three additional events is unknown; all results refer to the 103-event archive.
- Labels come from the file-name tokens `_campaign_` and `_noncampaign_`. In every graph the node identifiers are exactly 0 to N−1 (checked by `src/validate_len.py`): they are per-graph indices, not account identifiers. Cross-event account overlap therefore cannot be measured.
- Pretrained text and profile embeddings in the archive are not used.

## Derived Files Included in the Repository

None of these contain message text, node or account identifiers, edges or timestamps.

| File | Contents |
|---|---|
| `data/manifests/file_hashes.csv` | Per event: file name, label, size in bytes, SHA-256, node and edge counts (103 rows) |
| `data/manifests/manifest.parquet` | The same per-event metadata, as read by the pipeline |
| `data/manifests/duplicate_files.json` | The removed duplicate and its SHA-256 |
| `data/manifests/validation_report.json` | Schema and data-quality checks from `src/validate_len.py` |
| `data/manifests/matching_diagnostics.json`, `matched_manifest.parquet` | Primary-ordering size matching (exploratory analysis) |
| `data/manifests/edge_budget_eligibility.json` | Events with at least K edges, per budget K |
| `outputs/run_v2/` | Per-event features and out-of-fold predictions, summary metrics, verification report |
| `frontend/public/data/research_data.json` | Website payload: results file plus per-event node and edge counts |

## Regenerated, Never Committed: `data/processed/`

`nodes.parquet`, `edges.parquet` (which contain edges and cleaned message text from the raw data), `sampled_views.parquet` and `sampled_views_v2.parquet` are rebuilt by `python run_pipeline.py`. They are excluded by `.gitignore`.
