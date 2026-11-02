# Licensing Scope

This repository contains three kinds of material under different terms. The MIT licence in `LICENSE` applies **only** to the first.

## 1. Source code: MIT licence

The MIT licence covers the project's own source code and build configuration:

- `src/`, `tests/`, `run_pipeline.py`, `configs/`, `requirements.txt`
- `paper/build.py`, `paper/make_paper_figures.py`, `paper/export_references.py`
- the website source: `frontend/src/`, `frontend/index.html`, `frontend/package.json`, `frontend/vite.config.js` and the other configuration files in `frontend/`

## 2. Research paper and documentation: all rights reserved

The paper and its source (`paper/main.tex`, `paper/references.bib`, `paper/generated/`, `paper/figures/`, the PDF in `paper/` and its copy in `frontend/public/`), the website's text, and the project's reports and documentation are © 2026 Suryansh Singh and Devansh Kewlani. They are **not** covered by the MIT licence. You may read them, cite them and link to them. Please cite the paper when you use its results.

## 3. Data: not covered by any licence of ours

- **LEN-Small dataset (third-party).** LEN-Small is a subset of LEN (Large Engagement Networks), created by A. A. Gopalakrishnan, J. Hossain, T. Elmas and A. E. Sarıyüce and described in their ICWSM 2025 paper (doi:10.1609/icwsm.v19i1.35839). That paper states: "The dataset is released under a CC-BY license, enabling free sharing and adaptation for research or development purpose." It does not give a licence version, and the project page and repositories carry no separate licence file. The raw archive is not included in this repository and must be obtained from the LEN project (https://erdemub.github.io/large-engagement-network/). The terms for the data are the LEN authors'; nothing in this repository changes or adds to them.
- **LEN-derived research outputs.** The files in `data/manifests/`, `outputs/` and `frontend/public/data/` contain event-level values derived from LEN-Small: event names taken from the archive's file names, counts, file digests, features and model predictions. Apart from the files described next, they contain no graphs, edges, message texts, node or account identifiers, timestamps or embeddings. They are provided only so the reported results can be checked and reproduced. They are adaptations of LEN-Small, computed as described in the paper and shared with attribution to the LEN authors. They are **not** covered by the MIT licence and are not endorsed by the LEN authors. See `data/DATA_MANIFEST.md`.
- **LEN-Small graph structure (dataset explorer).** `frontend/public/data/len/` holds, for each of the 103 analysed events, its graph structure: node count, directed edges between per-graph node indices (0 to N−1, as in the release; not account identifiers), interaction counts and core numbers, plus the edge indices of the Study 2 sampled observations. It holds no message texts, timestamps, embeddings or account identifiers. It is shared, with attribution, under the LEN authors' CC-BY statement quoted above, so that the website's dataset explorer can display the graphs. It is not covered by the MIT licence and is not endorsed by the LEN authors.

## Third-party software

Python and JavaScript dependencies (`requirements.txt`, `frontend/package.json`) are installed separately and remain under their own licences. None are vendored in this repository.
