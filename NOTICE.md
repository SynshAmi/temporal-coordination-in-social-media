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

- **LEN-Small dataset (third-party).** The dataset is not included in this repository. It belongs to its creators and must be obtained from the LEN project (https://erdemub.github.io/large-engagement-network/). We could not identify an explicit licence or redistribution terms for LEN or LEN-Small. Nothing in this repository grants any rights to that data.
- **LEN-derived research outputs.** The files in `data/manifests/`, `outputs/` and `frontend/public/data/` contain event-level values derived from LEN-Small: event names taken from the archive's file names, counts, file digests, features and model predictions. They contain no graphs, edges, message texts, node or account identifiers, timestamps or embeddings. They are provided only so the reported results can be checked and reproduced. They are **not** covered by the MIT licence, are not officially licensed or endorsed by the LEN authors, and their inclusion is not a claim that their redistribution has been cleared. See `data/DATA_MANIFEST.md`.

## Third-party software

Python and JavaScript dependencies (`requirements.txt`, `frontend/package.json`) are installed separately and remain under their own licences. None are vendored in this repository.
