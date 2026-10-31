# What Does LEN-Small Measure? Predictive Information Beyond Scale in Retained Engagement Graphs

Research website: **Temporal Coordination in Social Media**

Suryansh Singh (Reg. No. 245816214) and Devansh Kewlani (Reg. No. 245816052)
Department of Computer Science and Engineering (Data Science), Manipal Institute of Technology, Bengaluru, India

LEN-Small is a benchmark of Twitter engagement graphs labeled as campaign-associated or comparison events [Gopalakrishnan et al., ICWSM 2025]. A high score on it is usually read as evidence that a model has learned something about coordination. This project asks what the labels can actually be predicted from:

- **Study 1 (RQ1):** what degree concentration, higher-order arrangement and retained content add beyond node and edge counts.
- **Study 2 (RQ2):** how much label information survives in a single fixed-size sample of edges, and what makes it predictive.

The unit of analysis is the event graph. No claims are made about individual accounts, bots, intent or causal effects.

## What is in this repository

| Artifact | Path |
|---|---|
| Research paper (Word and PDF) | `reports/LEN_Small_Measurement_Validity_Audit_Research_Paper.{docx,pdf}` |
| All reported numbers (single source for paper and website) | `outputs/run_v2/paper_results.json` |
| Research website | `frontend/` (reads the same results file) |
| Claim-to-evidence audit (25 headline claims) | `reports/audit/claim_evidence.md` |
| End-to-end reproducibility report | `reports/reproducibility/REPRODUCIBILITY_REPORT.md` |
| Independent verification report | `outputs/run_v2/verification/verification_report.json` |
| Data source, hashes and licence notes | `data/DATA_MANIFEST.md`, `data/manifests/file_hashes.csv` |
| Research planning documents | `docs/research/` |
| Superseded material (correction history only) | `outputs/run_final/`, `configs/final.yaml`, `archive/` |

**The LEN dataset itself is not included.** See [Data](#data).

## Main findings

All values are out-of-fold estimates from event-level stratified five-fold cross-validation. BA = balanced accuracy; LR = logistic regression. Intervals are 95% event-level paired bootstrap intervals (2,000 resamples) of fixed out-of-fold predictions.

| Result | Value |
|---|---|
| Analysed archive | 104 files, 1 SHA-256 duplicate removed: 103 events (52 campaign, 51 comparison). The official release has 100 (51/49); the reason for the difference is unknown. |
| Counts only (LR, M0) | BA 0.884 |
| All features vs counts (C1, LR) | ΔBA +0.010 [−0.049, +0.076], inconclusive; Δ log loss −0.110 [−0.181, −0.039], Holm p = 0.009; ΔAUC +0.039 [+0.009, +0.075] |
| Arrangement beyond degree (C2), content beyond counts (C3) | no detectable BA or log-loss gain |
| Real vs degree-preserving rewired arrangement | ΔBA 0.000 [−0.048, +0.047] |
| Exploratory size matching (15–17 pairs, 20 orderings) | counts near chance (median BA 0.531); content above chance (median 0.781) |
| Single 250-edge view, retrained, sampled endpoint count N_K only | BA 0.922 (0.880 at K = 500, 0.851 at K = 1000) |
| Training on views vs frozen full-graph model, same structural features, K = 250 | +0.254 [0.162, 0.348] |
| Averaging 10 views vs a single view | \|ΔBA\| ≤ 0.004 |
| E[N_K] at K = 250 | variation explained by log node count and log mean degree: 93.0%; in/out-degree Gini adds nothing |
| K = 2000 | infeasible for five-fold CV (only 4 campaign events have ≥ 2,000 edges) |

Richer features improve probability quality (log loss) and ranking (AUC), not classification decisions (BA). Log loss reflects both calibration and discrimination; calibration was not assessed separately. The null-model result shows only that the tested arrangement features did not outperform their degree-preserving counterparts; it does not show that topology is uninformative.

## Limitations

- **Sample size.** With 103 events, null BA results are inconclusive, not evidence of equivalence. Paired intervals exclude refitting and split variability (reported separately over 10 re-drawn splits), and hyperparameter selection in small inner folds was sensitive to row order.
- **Provenance.** The archive differs from the official release for an unknown reason. Labels come from file names. The release has no account identifiers (node IDs are per-graph indices) and no campaign subtypes, so dependence between events through shared accounts, and subtype heterogeneity, cannot be assessed.
- **Null model and matching.** Rewiring mixes incompletely in hub-dominated graphs. Matching keeps 15–17 pairs and is exploratory.
- **Scope.** Timestamp semantics are unverified, so no temporal features are used. Only LR and HGBT on hand-crafted features were evaluated.
- **Reproduction.** The full raw-to-results run was reproduced on one machine only (see the reproducibility report); reproduction on other machines has not been tested.

## Correction history

An earlier version of this analysis had two defects:

1. Every graph contains self-loops, which the core-number routine rejects; the coreness features were silently set to zero.
2. The frozen-model evaluation used a budget-specific fold split, so some sampled events were scored by a model trained on their own full graph.

Both are fixed and covered by regression tests (`tests/test_features.py`). For example, logistic regression on all twelve features in the base experiment grid reported BA 0.923 in the earlier run and reaches 0.894 after correction. **0.923 is a superseded value, not a current result.** Superseded material is labelled as such in `outputs/run_final/`, `configs/final.yaml` and `archive/`.

## Data

The analysis uses the LEN-Small archive `small_encoder_final.tar` from the LEN project (https://erdemub.github.io/large-engagement-network/, "Small Dataset" on the download page). It is **not redistributed here**, and `.gitignore` excludes it along with all regenerated raw-derived data (`data/processed/`).

We could not identify an explicit licence or redistribution terms for LEN or LEN-Small. The repository therefore contains no raw data: no graphs, edges, message texts, node or account identifiers, timestamps or embeddings. It does include derived event-level research outputs (event names, counts, file hashes, features and predictions) for reproducibility. These are the authors' own computations, not officially licensed or endorsed by the LEN authors. If you use the data, cite the LEN paper. Details are in `data/DATA_MANIFEST.md`.

## Reproducing the results

### Prerequisites

| Requirement | Version used | Needed for |
|---|---|---|
| Python | 3.12.10 | pipeline, tests |
| Python packages | pinned in `requirements.txt` | pipeline, tests |
| Node.js / npm | 22.20.0 / 10.9.3 (Node 18+ should work) | website; paper `.docx` builder |
| Microsoft Word on Windows | Word 16.0 (build 16.0.20527), Windows 11 | native equations and PDF export of the paper only |
| Disk | about 6 GB for the archive | |

### Step-by-step

```bash
# 1. Obtain the archive, place it at the project root, and verify it
#    (expected SHA-256 in data/DATA_MANIFEST.md)
sha256sum small_encoder_final.tar             # macOS: shasum -a 256; Windows: Get-FileHash

# 2. Install dependencies
python -m pip install -r requirements.txt
cd frontend && npm install && cd ..
cd reports/paper && npm install && cd ../..

# 3. Run the whole pipeline: 14 stages, about 53 minutes on a 16-thread laptop
python run_pipeline.py                        # default config: configs/v2_coreness_fix.yaml

# 4. Tests only (also run as the pipeline's last stage)
python -m pytest tests/ -v

# 5. Website: development server or production build
cd frontend
npm run dev                                   # http://localhost:5173/
npm run build && npm run preview              # http://localhost:4173/
cd ..
```

The 14 stages are: ingest, validate, size matching, edge sampling, base grid training, fold-aligned frozen-model evaluation, checkpoint report, Study 1, Study 2, independent verification, paper results, paper figures, website payload and tests. Every stage reads its paths from the config. The pipeline stops at the first failing stage and records per-stage times in `<run_dir>/pipeline_stages.json`.

**Expected outputs:**
- `data/manifests/*` and `data/processed/*`
- `outputs/run_v2/`: `metrics.json`, `predictions.parquet`, `study1/`, `study2/`, `verification/verification_report.json` (21/21 checks) and `paper_results.json`
- `reports/paper/figures/*.png`
- `frontend/public/data/research_data.json`

### Paper

The paper is built outside the pipeline from `reports/paper/paper_content.js`, which reads `outputs/run_v2/paper_results.json`:

```bash
node reports/paper/build_paper.js             # writes reports/...Research_Paper.docx (equation placeholders)
# Windows with Microsoft Word only (COM automation): native equations, then PDF
powershell -ExecutionPolicy Bypass -File reports/paper/finalize_equations.ps1 -Docx reports/LEN_Small_Measurement_Validity_Audit_Research_Paper.docx
powershell -ExecutionPolicy Bypass -File reports/paper/export_pdf.ps1 -Docx reports/LEN_Small_Measurement_Validity_Audit_Research_Paper.docx -Pdf reports/LEN_Small_Measurement_Validity_Audit_Research_Paper.pdf
node reports/paper/export_references.js        # website reference list, from the paper source
python src/claim_evidence_audit.py             # checks all 25 headline claims against the PDF
```

Without Word, the `.docx` still builds, but its three equations remain as `[[EQn]]` placeholders and no PDF is produced. `npm run dev` and `npm run build` copy the current PDF into the website.

### Checking a reproduction without overwriting the verified results

```bash
python run_pipeline.py --config configs/repro_check.yaml   # writes everything under repro/
python src/repro_compare.py                                 # compares repro/ with outputs/run_v2 and data/
```

Fixed seeds: folds 42; matching 42 (plus 19 further visiting orders); edge sampling 100–109; rewiring 2024; bootstrap 7; re-drawn splits 42 and 1–9.

## Repository layout

```
├── run_pipeline.py                 14-stage pipeline
├── requirements.txt                Python dependencies (pinned)
├── configs/
│   ├── v2_coreness_fix.yaml        Authoritative configuration (writes outputs/run_v2)
│   ├── repro_check.yaml            Same, but writes under repro/ (reproduction check)
│   └── final.yaml                  SUPERSEDED original configuration
├── src/                            Pipeline stages, studies, verification, exports, audits
├── tests/                          pytest suite, including paper/website parity checks
├── data/
│   ├── DATA_MANIFEST.md            Source, archive hash, licence notes
│   ├── manifests/                  Per-event metadata and hashes (derived)
│   └── processed/                  Regenerated from the archive; never committed
├── outputs/
│   ├── run_v2/                     Authoritative run
│   └── run_final/                  SUPERSEDED original run (correction history)
├── reports/
│   ├── LEN_Small_..._Research_Paper.docx / .pdf
│   ├── audit/                      Claim-to-evidence audit
│   ├── reproducibility/            End-to-end reproducibility report and comparison
│   └── paper/                      Paper source, figures and build scripts
├── frontend/                       Research website (React + Vite); see frontend/README.md
├── docs/research/                  Research planning documents
└── archive/                        SUPERSEDED plan, paper and first audit (provenance only)
```

## Licence

Source code is released under the MIT licence (`LICENSE`). The licence does not cover:
- the LEN dataset, which is not included;
- the derived event-level files, which are provided for research reproducibility only (see Data);
- the paper's text and figures, which remain © the authors.

## Citation

If you use this work, please cite the paper above and the LEN dataset:

> A. A. Gopalakrishnan, J. Hossain, T. Elmas and A. E. Sarıyüce, "Large engagement networks for classifying coordinated campaigns and organic Twitter trends," in *Proc. ICWSM*, vol. 19, no. 1, pp. 688–702, 2025, doi:10.1609/icwsm.v19i1.35839.
