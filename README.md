# Temporal Coordination in Social Media

### 🌐 [Visit the live research website](https://temporal-coordination-in-social-media.pages.dev/)

**Paper:** *What Does LEN-Small Measure? Predictive Information Beyond Scale in Retained Engagement Graphs* ([PDF](paper/LEN_Small_Predictive_Information_Beyond_Scale.pdf))
**Authors:** Suryansh Singh and Devansh Kewlani, Department of Computer Science and Engineering (Data Science), Manipal Institute of Technology, Bengaluru, India

---

## About the research

Coordinated campaigns on social media, such as organised efforts to push a hashtag into a trending list, are often studied through **engagement graphs**. In these graphs, accounts are nodes, and retweets, replies or quotes are directed edges. *Temporal Coordination in Social Media* is our project on how such campaigns are measured. This repository holds its first study: a close look at a benchmark used to train and evaluate campaign detectors.

That benchmark is **LEN-Small**, part of the Large Engagement Networks (LEN) release (Gopalakrishnan et al., ICWSM 2025). Each graph is one Twitter event, labelled either campaign-associated or comparison. When a model scores well on LEN-Small, it is natural to assume it has learned something about coordination. That assumption only holds if the labels cannot be predicted from simpler properties of the graphs, which is what we test.

## Research questions

We analysed the 103 event graphs in the distributed LEN-Small archive and asked:

1. **What do graph features add beyond size?** How much do degree concentration (how unevenly engagement is spread across accounts), higher-order arrangement (reciprocity, connectivity, core structure) and message content add beyond simple node and edge counts?
2. **What survives in a partial view?** If we see only a fixed-size random sample of a graph's edges, how much label information remains, and what makes it predictive?

All comparisons are made on the same events and the same cross-validation folds, with paired event-level bootstrap intervals. A degree-preserving rewiring null model tests whether arrangement matters beyond the degree of each node, and an exploratory analysis matches campaign and comparison events on size. The unit of analysis is always the whole event graph; we make no claims about individual accounts, bots, intent or causal effects.

## Key findings

- **Size dominates.** Comparison events are several times larger than campaign events (median 3,227 vs 506 nodes). Logistic regression given only node and edge counts reaches a **balanced accuracy of 0.884**.
- **Richer features help probabilities, not decisions.** Adding degree, arrangement and content features did not detectably improve balanced accuracy (difference +0.010, 95% interval −0.049 to +0.076). This result is inconclusive rather than evidence of equivalence. The difference was positive but small in all ten cross-validation fold splits we examined; because the splits reuse the same events, that is not evidence of a reliable gain. The same features did improve **log loss** (a measure of probability quality) by 0.110 and **AUC** (ranking quality) by 0.039. A wider regularisation search made the count model's log loss worse (0.326 → 0.364), so its apparent under-tuning does not explain the gap.
- **No detectable gain from arrangement beyond degree.** The arrangement features showed no detectable improvement over the same features computed on degree-preserving rewired graphs (balanced-accuracy difference 0.000, 95% interval −0.048 to +0.047). This is not evidence of equivalence, and the rewiring is a constrained comparison: it changed reciprocity in 92% of events and the largest-component fraction in 99%, but the median core number in only 4%. It does not show that graph structure is uninformative.
- **Size matching removes the count signal.** In an exploratory analysis of 15–17 size-matched pairs, counts fell to near chance (median balanced accuracy 0.531), while the content model's median was 0.781. These are imprecise point estimates without sampling intervals, not evidence that content performs reliably above chance.
- **A small sample of edges loses no detectable signal, and training on such samples matters.** On the same events, a model trained on single random samples of K edges was not detectably less accurate than the full-graph model with the same features (balanced-accuracy difference +0.002, 95% interval −0.031 to +0.038, at K = 250; +0.027, −0.003 to +0.065, at K = 500). At K = 1000 the sample-trained model was ahead (+0.056, +0.009 to +0.114), but that exploratory result comes from a small, imbalanced cohort of 73 events and does not mean sampling generally improves classification.
- **Much of a sample's information is size-like.** The number of distinct accounts a 250-edge sample touches (N_K) gives a balanced accuracy of 0.922 on its own. Its expected value is strongly associated with the full graph's node count and mean degree, which together explain 93.0% of its variation, and the structural features also encode it closely (cross-validated R² 0.92–0.95). N_K alone and structure alone did not differ detectably, so the two carry largely overlapping information, and we do not attribute the signal to N_K rather than structure.
- **Training on samples matters far more than averaging them.** With the same structural features, a model trained on 250-edge samples scored 0.254 higher in balanced accuracy (95% interval 0.162 to 0.348) than the full-graph model applied to those samples. Averaging ten samples instead of using one changed accuracy by at most 0.004.

**In short:** LEN-Small's labels, as distributed, are highly predictable from how large an event graph is, although we do not show that size is the only relevant property. Benchmark results on it should be read against a count-only baseline, with decision and probability metrics reported separately. Full results, tables and figures are in the [paper](paper/LEN_Small_Predictive_Information_Beyond_Scale.pdf) and on the [website](https://temporal-coordination-in-social-media.pages.dev/).

## Repository structure

| Directory | Contents |
|---|---|
| `paper/` | The paper: LaTeX source, bibliography, figures, generated result macros, build script and compiled PDF |
| `src/` | The analysis pipeline: data ingestion, feature extraction, both studies, independent verification and result exports |
| `tests/` | Automated checks, including agreement between the paper, the website and the results |
| `outputs/run_v2/` | The verified results; `paper_results.json` is the main source of every reported number |
| `outputs/revision_h1_cgrid/`, `outputs/revision_supplement/` | Revision analyses: the wider regularisation search for the count model, and supplementary analyses (single view vs full graph, endpoint count vs structure, null-model coverage, split counts) read by the paper and website |
| `frontend/` | Source of the research website, including the interactive dataset explorer; its graph files are in `frontend/public/data/len/` |
| `data/` | Dataset manifest and file hashes; the dataset itself is not included |
| `reports/` | Claim-to-evidence audit and end-to-end reproducibility report |
| `configs/` | Pipeline configuration (`v2_coreness_fix.yaml` is the one used for all results) |
| `archive/`, `outputs/run_final/` | Superseded material, kept only for the correction history |

## Reproducing the research

### Requirements

- **Python 3.12** with the pinned packages in `requirements.txt`.
- **Node.js 18 or later**, only to build the website.
- **A LaTeX distribution** with `pdflatex` and `bibtex` (TeX Live or MiKTeX), only to compile the paper.
- **The LEN-Small archive** (about 5.4 GB), described below.

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

The pipeline runs every step from the raw archive to the final results, figures and website data, with fixed random seeds. It writes its results to `outputs/run_v2/` and the revision analyses to the two `outputs/revision_*` directories; all output locations are set in `configs/v2_coreness_fix.yaml`.

The revision analyses can also be run on their own once `outputs/run_v2/` exists. They only read it:

```bash
python src/h1_c_grid.py               # count-model regularisation grid -> outputs/revision_h1_cgrid/ (output.revision_h1_dir)
python src/revision_supplement.py     # supplementary analyses -> outputs/revision_supplement/supplement.json (output.revision_supplement)
python src/export_latex_results.py    # refreshes the paper's result macros
python src/export_frontend_data.py    # refreshes the website payload
python src/export_dataset_explorer.py # rebuilds the dataset explorer's graph files (needs the raw archive)
```

### Check the results without the dataset

The results, the paper PDF and its compiled bibliography are committed, so the test suite also runs on a fresh clone without the dataset or LaTeX:

```bash
python -m pytest                      # 36 pass; 6 skip because they need the dataset
```

## Building the paper

The paper is written in IEEE conference LaTeX (`paper/main.tex`). It contains no hand-typed results: every number and table is filled in from `outputs/run_v2/paper_results.json` and `outputs/revision_supplement/supplement.json` through generated macros in `paper/generated/results.tex`.

```bash
python paper/build.py                 # writes paper/LEN_Small_Predictive_Information_Beyond_Scale.pdf
python paper/export_references.py     # updates the website's reference list
python -m pytest                      # checks the paper and website against the results
```

To run the website locally, use `npm install` and then `npm run dev` inside `frontend/`.

## Limitations and data availability

- **Small sample.** With 103 events, the confidence intervals are wide, and a result showing no difference is not evidence that none exists.
- **Archive provenance.** The analysed archive holds 103 events (52 campaign, 51 comparison), three more than the official 100-graph LEN-Small release, for a reason we could not determine.
- **Missing metadata.** The release has no account identifiers or campaign subtypes, so links between events through shared accounts cannot be assessed. Timestamp meanings are unverified, so no temporal features are used.
- **Scope.** Only logistic regression and gradient-boosted trees on hand-crafted features were evaluated. The full pipeline was reproduced on one machine; reproduction on other hardware has not been tested.
- **Corrections.** Two errors in an earlier version of the analysis, a coreness calculation that ignored self-loops and a cross-validation fold-assignment error, were identified during validation and corrected before the results reported in this paper were finalized. For example, one superseded model reported a balanced accuracy of 0.923, which became 0.894 after correction; **0.923 is not a current result.** Details are in Section VIII of the paper.
- **Data.** The repository does not include the raw LEN archive, and contains no messages, account identifiers or timestamps. It does include derived event-level outputs (event names, counts, file hashes, features and predictions) for reproducibility, and, for the website's dataset explorer, the graph structure of the 103 analysed events (directed edges between per-graph node indices). The LEN authors release the dataset under a CC-BY licence (their paper gives no version); these derived files and the graph structure are shared with attribution to them and are not endorsed by them. See [`data/DATA_MANIFEST.md`](data/DATA_MANIFEST.md).

## Licence and citation

The **source code** is released under the [MIT licence](LICENSE). The licence does not cover the paper, its figures or documentation (© the authors), or any LEN-derived data. [`NOTICE.md`](NOTICE.md) sets out exactly what falls under each.

If you use this work, please cite the paper and the dataset it analyses:

> S. Singh and D. Kewlani, "What Does LEN-Small Measure? Predictive Information Beyond Scale in Retained Engagement Graphs," 2026. [Online]. Available: https://github.com/SynshAmi/temporal-coordination-in-social-media

> A. A. Gopalakrishnan, J. Hossain, T. Elmas and A. E. Sarıyüce, "Large engagement networks for classifying coordinated campaigns and organic Twitter trends," in *Proc. ICWSM*, vol. 19, no. 1, pp. 688–702, 2025, doi:10.1609/icwsm.v19i1.35839.
