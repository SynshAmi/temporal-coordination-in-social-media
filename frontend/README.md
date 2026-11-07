# Research website: Temporal Coordination in Social Media

Results site for the paper *Finding Signal in Network Simplicity*. It is built with React 19, Vite and Tailwind CSS v4, and the equations on the Methods page use KaTeX.

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
python src/export_paper_results.py      # outputs/run_v2/paper_results.json
python src/export_audit_results.py      # outputs/research_audit/audit_results.json
python src/export_frontend_data.py      # frontend/public/data/research_data.json
python paper/export_references.py       # frontend/src/lib/references.json (the paper's compiled reference list)
```

The payload embeds three files unchanged: `paper_results.json` under `paper`, the revision supplement under `revision`, and the audit results under `audit` (checked by `tests/test_frontend_payload.py`). The site and the paper therefore read the same values. `tests/test_paper_website_parity.py` also checks:
- the served PDF is the current paper;
- the site's title and reference list match the paper's;
- no result values are typed by hand into page source;
- no superseded headline values appear on the site.

Page text builds its numbers from the payload. `src/lib/results.js` assembles the paper's tables from it, and `src/lib/fmt.js` formats values exactly as the paper's LaTeX macros do.

## Pages

| Route | Content |
|---|---|
| `#overview` | The paper: question, motivation, the two studies, findings with status labels, abstract, data and provenance, limitations, PDF link |
| `#results` | Study 1 (size figure, full-observation contrasts by metric and partitioning) and Study 2 (performance by budget, within-budget contrasts, token-count dispersion), plus the searchable results table |
| `#methods` | Data, features (KaTeX), models and metrics, uncertainty and status labels, null model, edge-limited design, reproduction commands, availability, references |
| `#dataset` | Interactive dataset explorer: every event's network, comparisons and the sampled views used in Study 2 |

`#explorer`, the earlier name of the Results page, still opens it.

## Design

The website follows an editorial research direction: paper and ink, with the campaign red used sparingly. Its signature detail is the status tag (Primary, Sensitivity, Exploratory, Post hoc) that each result carries. The design pass followed the [unslop](https://github.com/heydamir/unslop) skill by Damir Sokolovsky ([@heydamir](https://x.com/heydamir)), licensed CC BY 4.0, which is installed locally in `.claude/skills/unslop/`.

## Downloads served from `public/`

- `Finding_Signal_in_Network_Simplicity.pdf`: the research paper. It is not edited here; `npm run dev` and `npm run build` copy it from `../paper/` first (the `sync-paper` script).
- `data/research_data.json`: the exported results payload.
- `_redirects`: Cloudflare Pages rules that permanently redirect the paper's earlier file names to the current PDF.
