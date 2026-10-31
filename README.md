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
- **Richer features help probabilities, not decisions.** Adding degree, arrangement and content features did not detectably improve balanced accuracy (difference +0.010, 95% interval −0.049 to +0.076). This result is inconclusive rather than evidence of equivalence. The same features did improve **log loss** (a measure of probability quality) by 0.110 and **AUC** (ranking quality) by 0.039.
- **Arrangement adds nothing beyond degree here.** The arrangement features did not outperform the same features computed on randomly rewired graphs with identical degrees. This does not show that graph structure is uninformative; it shows that these features, with these models, carried no extra label information.
- **Size matching removes the count signal.** In an exploratory analysis of 15–17 size-matched pairs, counts fell to near chance (median balanced accuracy 0.531), while content stayed above chance (median 0.781).
- **One small sample of edges is enough, and training on such samples matters.** From a single random sample of 250 edges, the number of distinct accounts the sample touches (N_K) alone gives a balanced accuracy of 0.922. The expected value of N_K is strongly associated with the full graph's node count and mean degree, which together explain 93.0% of its variation. With the same structural features, a model trained on 250-edge samples scored 0.254 higher in balanced accuracy (95% interval 0.162 to 0.348) than the full-graph model applied to those samples. Averaging ten samples instead of using one changed accuracy by at most 0.004.

**In short:** LEN-Small's labels, as distributed, are largely predictable from how large an event graph is. Benchmark results on it should be read against a count-only baseline, with decision and probability metrics reported separately. Full results, tables and figures are in the [paper](paper/LEN_Small_Predictive_Information_Beyond_Scale.pdf) and on the [website](https://temporal-coordination-in-social-media.pages.dev/).

## Repository structure

| Directory | Contents |
|---|---|
| `paper/` | The paper: LaTeX source, bibliography, figures, generated result macros, build script and compiled PDF |
| `src/` | The analysis pipeline: data ingestion, feature extraction, both studies, independent verification and result exports |
| `tests/` | Automated checks, including agreement between the paper, the website and the results |
| `outputs/run_v2/` | The verified results; `paper_results.json` is the single source of every reported number |
| `frontend/` | Source of the research website |
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
python run_pipeline.py                # about 53 minutes; ends by running the test suite
```

The pipeline runs every step from the raw archive to the final results, figures and website data, with fixed random seeds. It writes its results to `outputs/run_v2/`.

### Check the results without the dataset

The results, the paper PDF and its compiled bibliography are committed, so the test suite also runs on a fresh clone without the dataset or LaTeX:

```bash
python -m pytest                      # 35 pass; 6 skip because they need the dataset
```

## Building the paper

The paper is written in IEEE conference LaTeX (`paper/main.tex`). It contains no hand-typed results: every number and table is filled in from `outputs/run_v2/paper_results.json` through generated macros in `paper/generated/results.tex`.

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
- **Data.** The repository contains no raw LEN data: no graphs, messages, account identifiers or timestamps. It does include derived event-level outputs (event names, counts, file hashes, features and predictions) for reproducibility. We could not identify an explicit licence for LEN-Small, and these files are not endorsed by the LEN authors. See [`data/DATA_MANIFEST.md`](data/DATA_MANIFEST.md).

## Licence and citation

The **source code** is released under the [MIT licence](LICENSE). The licence does not cover the paper, its figures or documentation (© the authors), or any LEN-derived data. [`NOTICE.md`](NOTICE.md) sets out exactly what falls under each.

If you use this work, please cite the paper and the dataset it analyses:

> S. Singh and D. Kewlani, "What Does LEN-Small Measure? Predictive Information Beyond Scale in Retained Engagement Graphs," 2026. [Online]. Available: https://github.com/SynshAmi/temporal-coordination-in-social-media

> A. A. Gopalakrishnan, J. Hossain, T. Elmas and A. E. Sarıyüce, "Large engagement networks for classifying coordinated campaigns and organic Twitter trends," in *Proc. ICWSM*, vol. 19, no. 1, pp. 688–702, 2025, doi:10.1609/icwsm.v19i1.35839.
