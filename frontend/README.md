# Research Website — Temporal Coordination in Social Media

Results site for the paper *What Does LEN-Small Measure? Predictive Information Beyond Scale in Retained Engagement Graphs*. Built with React 19, Vite and Tailwind CSS v4; equations on the Methods page use KaTeX.

## Run

Requires Node.js 18+ (built and tested with Node v22.20.0).

```bash
npm install
npm run dev        # development server: http://localhost:5173/
npm run build      # production build -> dist/
npm run preview    # serve the production build: http://localhost:4173/
```

## Data flow

Every result value on the site is read at runtime from `public/data/research_data.json`. That file is generated, not hand-edited:

```bash
# from the project root
python src/export_paper_results.py      # outputs/run_v2/paper_results.json (also used by the paper)
python src/export_frontend_data.py      # frontend/public/data/research_data.json
node reports/paper/export_references.js # frontend/src/lib/references.json (the paper's reference list)
```

The payload embeds `paper_results.json` unchanged under `paper` (checked by `tests/test_frontend_payload.py`), so the site and the paper cannot disagree. `tests/test_paper_website_parity.py` also checks:
- the served PDF is the current paper;
- the site's title and reference list match the paper's;
- no result values are typed by hand into page source;
- no superseded headline values appear on the site. Page text builds its numbers from that object. `src/lib/fmt.js` formats them exactly as the paper does.

## Pages

| Route | Content |
|---|---|
| `#overview` | Core finding, abstract, research questions, Fig. 1 (graph size by class), Fig. 2 (Study 1 confirmatory contrasts), interpretation and limitations |
| `#explorer` | Fig. 3 (exploratory size matching), Fig. 4 (Study 2 single-view performance), study design flowchart, searchable results table |
| `#methods` | Protocol, feature and estimand definitions (KaTeX), evaluation and inference, null model and observation conditions, correction history, reproduction commands, references |

## Downloads served from `public/`

- `LEN_Small_Measurement_Validity_Audit_Research_Paper.pdf`: the research paper. Not edited here; `npm run dev` and `npm run build` copy it from `../reports/` first (`sync-paper` script).
- `data/research_data.json`: the exported results payload.
