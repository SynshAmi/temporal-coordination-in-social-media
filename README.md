# Temporal Coordination in Social Media

### 🌐 [Visit the live research website](https://temporal-coordination-in-social-media.pages.dev/)

**Paper:** *Finding Signal in Network Simplicity* ([PDF](paper/Finding_Signal_in_Network_Simplicity.pdf))
**Authors:** Suryansh Singh (co-first author), Devansh Kewlani (co-first author) and Yashaswini K A (second author), Manipal Institute of Technology, Bengaluru, India

---

## About the research

Coordinated campaigns on social media, such as organised efforts to push a hashtag into a trending list, are often studied through **engagement graphs**. In these graphs, accounts are nodes, and retweets, replies or quotes are directed edges. *Temporal Coordination in Social Media* is our project on how such campaigns are measured. This repository holds its first study.

Benchmarks such as the Large Engagement Networks (LEN) release (Gopalakrishnan et al., ICWSM 2025) label each Twitter event graph as campaign-associated or comparison, and graph-learning methods are evaluated on them. A high score invites the reading that a model has learned how campaigns spread. That reading depends on what the labels can be predicted from, and engagement graphs give a specific reason for caution: the two classes differ strongly in size.

## Research question

How well can the campaign label be predicted from node and edge counts, and what, if anything, adds to that prediction?

1. **Full observation (Study 1).** What do degree concentration, higher-order arrangement and message content add to the counts?
2. **Edge-limited observation (Study 2).** When only K edges of a graph are seen, the edge count is fixed. The count that still varies is the view's node count N_K. What do structural and message-level statistics add to it?

All comparisons use the same events and the same cross-validation folds, with paired event-level bootstrap intervals. Each result carries a status, as in the paper:
- **primary**: the three contrasts specified in advance, Holm-adjusted;
- **sensitivity**: other partitions, exclusions or fold grouping;
- **exploratory**: planned, but outside the primary family;
- **post hoc**: chosen after inspecting these events.

The unit of analysis is the event graph; we make no claims about individual accounts, bots, intent or causal effects.

## Data

We analysed the **103-graph LEN project archive (52 campaign, 51 comparison)**, obtained from the LEN project website: 104 files, with one exact duplicate removed. It is distinct from the dataset described in the published LEN paper, which reports LEN-Small as 100 graphs (51/49), and every result refers to this archive. Of the 288,540 edge texts, 27.5% are null; campaign graphs keep less usable text than comparison graphs (mean share 0.58 against 0.80), and two campaign graphs have none.

## Key findings

- **Counts alone predict the label well.** Logistic regression on node and edge counts reaches balanced accuracy 0.884 and AUC 0.931 (primary). Comparison graphs are several times larger than campaign graphs (median 3,227 against 506 nodes).
- **More features sharpen probabilities, not decisions.**
  - On the prespecified partition, adding degree, arrangement and content features changed log loss by −0.110 [−0.181, −0.039] (Holm-adjusted p = 0.009) and AUC by +0.039 [+0.009, +0.075] (primary).
  - Over 20 repartitions of the same events, the log-loss difference was −0.094 [−0.172, −0.013], in the same direction in 19 of 20 (sensitivity).
  - Balanced accuracy showed no detectable gain: +0.010 [−0.049, +0.076].
- **Structure is conditional, not absent.**
  - Added to counts alone, the structural features produced no detectable change: +0.002 [−0.048, +0.053].
  - Added alongside content, they changed log loss by −0.059 [−0.110, −0.011] (exploratory).
  - Without the two no-text graphs, the main log-loss difference kept its direction (−0.083 [−0.171, +0.008]), with an interval that includes zero.
- **A fixed edge budget does not remove size.**
  - In views, N_K alone reaches AUC 0.961, 0.952 and 0.890 at K = 250, 500 and 1000.
  - Its expectation depends only on K and the full graph's degree sequence. At K = 250, node count and mean degree explain 93.0% of its variation.
  - The structural features of a view largely track it, and adding them to N_K produced no detectable change.
- **Token-count dispersion is a lead, not a result.**
  - The standard deviation of message token counts is an edge-by-edge statistic, so a view estimates the same quantity at every budget.
  - Added to N_K, it was associated with lower log loss at K = 1000: −0.114 [−0.218, −0.011]. At the smaller budgets the intervals include zero.
  - It was chosen post hoc on these events and needs testing on independent data.

**In short:** in this archive, most of the predictive signal sits in the simplest network measurements. Evaluations on these data should report a count-only baseline and report probability and decision metrics separately. Full results are in the [paper](paper/Finding_Signal_in_Network_Simplicity.pdf) and on the [website](https://temporal-coordination-in-social-media.pages.dev/).

## Repository structure

| Directory | Contents |
|---|---|
| `paper/` | LaTeX source, bibliography, figures, generated result macros, the build script and the compiled PDF |
| `src/` | The analysis pipeline (ingestion, features, both studies, independent verification) and the exports to the paper and website |
| `tests/` | Automated checks, including agreement between the paper, the website and the results |
| `outputs/run_v2/` | The verified pipeline results; `paper_results.json` is the main source of every reported number |
| `outputs/revision_h1_cgrid/`, `outputs/revision_supplement/` | Revision analyses that only read `run_v2` (wider regularisation grid; supplementary Study 2 and null-model diagnostics) |
| `research_audit/` | The robustness audit: reports, scripts and outputs (20 partitions, exclusions, text retention, token-count dispersion). See its [README](research_audit/README.md) |
| `outputs/research_audit/audit_results.json` | The audit values the paper and website report, collected with their source files by `src/export_audit_results.py` |
| `frontend/` | The research website, including the interactive dataset explorer (graph files in `frontend/public/data/len/`) |
| `data/` | Dataset manifest and file hashes; the dataset itself is not included |
| `reports/` | Claim-to-evidence audit and end-to-end reproducibility report |
| `configs/` | Pipeline configuration (`v2_coreness_fix.yaml` is used for all results) |
| `docs/research/` | The research plan written before the corrected analysis |
| `archive/`, `outputs/run_final/` | Superseded material, kept for the correction history |

## Reproducing the research

### Requirements

- **Python 3.12** with the pinned packages in `requirements.txt`.
- **Node.js 18 or later**, only to build the website.
- **A LaTeX distribution** with `pdflatex` and `bibtex` (TeX Live or MiKTeX), only to compile the paper.
- **The LEN archive** (`small_encoder_final.tar`, about 5.4 GB), described below.

### Data

The dataset is not redistributed here. Download `small_encoder_final.tar` ("Small Dataset") from the [LEN project](https://erdemub.github.io/large-engagement-network/), place it in the repository root, and check that its SHA-256 matches the one in [`data/DATA_MANIFEST.md`](data/DATA_MANIFEST.md):

```bash
sha256sum small_encoder_final.tar     # macOS: shasum -a 256 · Windows: Get-FileHash
```

### Run the analysis

```bash
python -m pip install -r requirements.txt
python run_pipeline.py                # about 70 minutes; ends by running the test suite
```

The pipeline runs every step from the raw archive to the results, figures and website data, with fixed seeds. It writes to `outputs/run_v2/` and the two `outputs/revision_*` directories, and it collects the stored audit values into `outputs/research_audit/`. All output locations are set in `configs/v2_coreness_fix.yaml`.

The robustness-audit scripts are separate from the pipeline. They read its outputs and write only into `research_audit/`; how to rerun them is in [`research_audit/README.md`](research_audit/README.md). After rerunning any of them, refresh the collected values and the downstream files:

```bash
python src/export_audit_results.py    # -> outputs/research_audit/audit_results.json
python src/export_latex_results.py    # refreshes the paper's result macros
python src/export_frontend_data.py    # refreshes the website payload
```

### Check the results without the dataset

The results, the audit outputs, the paper PDF and its compiled bibliography are committed, so the test suite also runs on a fresh clone without the dataset or LaTeX. Tests that need the raw archive are skipped, with the reason printed.

```bash
python -m pytest
```

## Building the paper

The paper is written in IEEE conference LaTeX (`paper/main.tex`). It contains no hand-typed results: every number and table is filled in through generated macros in `paper/generated/results.tex`. The macros come from three files:
- `outputs/run_v2/paper_results.json`;
- `outputs/revision_supplement/supplement.json`;
- `outputs/research_audit/audit_results.json`.

```bash
python paper/make_paper_figures.py    # figures (needs data/processed from the pipeline)
python paper/build.py                 # writes paper/Finding_Signal_in_Network_Simplicity.pdf
python paper/export_references.py     # updates the website's reference list
python -m pytest                      # checks the paper and website against the results
```

To run the website locally, use `npm install` and then `npm run dev` inside `frontend/`. `npm run build` copies the current paper PDF into the site first.

## Limitations and data availability

- **Small sample.** With 103 events (73 at K = 1000), intervals are wide, and a result showing no difference is not evidence that none exists. Bootstrap intervals exclude refitting variability, which the repartitions show to be of comparable size.
- **Scope.** Results describe the 103-graph LEN project archive; size–label associations may reflect how its events were selected and need not hold for other LEN data.
- **Post-hoc selection and text.** Token-count dispersion was chosen after inspecting these events. All content features describe retained text only, and retention differs by class.
- **Missing metadata.** The release has no account identifiers or campaign subtypes, so links between events through shared accounts cannot be assessed. Timestamp meanings are unverified, so no temporal features are used.
- **Scope.** Only logistic regression and gradient-boosted trees on hand-crafted features were evaluated, and only uniform edge sampling was studied. The full pipeline was reproduced on one machine; reproduction on other hardware has not been tested. The audit scripts were run once.
- **Correction history.** Two implementation errors in an earlier internal version were found and fixed before the reported results were produced: a coreness calculation that ignored self-loops, and a fold-assignment error for frozen models. Both are now covered by regression tests. For example, one superseded model reported a balanced accuracy of 0.923, which became 0.894 after correction; **0.923 is not a current result.** The superseded run is kept in `outputs/run_final/` and `archive/`.
- **Data.** The repository does not include the raw LEN archive, and it contains no messages, account identifiers or timestamps. It does include:
  - derived event-level outputs (event names, counts, file hashes, features and predictions) for reproducibility;
  - for the website's dataset explorer, the graph structure of the 103 analysed events (directed edges between per-graph node indices).

  The LEN authors release the dataset under a CC-BY licence (their paper gives no version); these derived files are shared with attribution to them and are not endorsed by them. See [`data/DATA_MANIFEST.md`](data/DATA_MANIFEST.md).

## Licence and citation

The **source code** is released under the [MIT licence](LICENSE). The licence does not cover the paper, its figures or documentation (© the authors), or any LEN-derived data. [`NOTICE.md`](NOTICE.md) sets out exactly what falls under each. The website design pass used the [unslop](https://github.com/heydamir/unslop) skill by Damir Sokolovsky (CC BY 4.0), installed locally in `.claude/skills/unslop/`; no part of it is redistributed in this repository.

If you use this work, please cite the paper and the dataset it analyses:

> S. Singh, D. Kewlani and Y. K A, "Finding Signal in Network Simplicity," 2026. [Online]. Available: https://github.com/SynshAmi/temporal-coordination-in-social-media

> A. A. Gopalakrishnan, J. Hossain, T. Elmas and A. E. Sarıyüce, "Large engagement networks for classifying coordinated campaigns and organic Twitter trends," in *Proc. ICWSM*, vol. 19, no. 1, pp. 688–702, 2025, doi:10.1609/icwsm.v19i1.35839.
