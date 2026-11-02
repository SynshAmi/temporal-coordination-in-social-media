"""
test_paper_website_parity.py
----------------------------
The paper and the website must present the same research. These tests catch
divergence between them:

- every headline claim's value appears verbatim in the built paper PDF;
- the paper's result macros are current, and main.tex types no result by hand;
- the website serves the current paper PDF and the paper's title;
- the website reference list is the paper's reference list, in citation order;
- the website source contains no hand-typed result values (all come from the
  payload) and no superseded headline values;
- the superseded 0.923 result appears in the results file only under the key
  that labels it as superseded.
"""

import re
import sys
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "paper"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import CFG, RUN_DIR, PAYLOAD_PATH, SUPPLEMENT_PATH as SUPPLEMENT  # noqa: E402

PAPER = ROOT / "paper"
PDF = PAPER / "LEN_Small_Predictive_Information_Beyond_Scale.pdf"
MAIN_TEX = PAPER / "main.tex"
BBL = PAPER / "main.bbl"
PUBLIC_PDF = ROOT / "frontend" / "public" / PDF.name
RESULTS = RUN_DIR / "paper_results.json"
SITE_SRC = ROOT / "frontend" / "src"

need_results = pytest.mark.skipif(not RESULTS.exists(), reason="run the pipeline first")


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


@need_results
def test_every_headline_claim_appears_in_paper_pdf():
    pytest.importorskip("pypdf")
    from claim_evidence_audit import check, pdf_text
    rows = check(load(RESULTS), pdf_text(PDF))
    missing = [(claim, [v for (_, v), ok in zip(vals, found) if not ok]) for claim, vals, _, _, found in rows if not all(found)]
    assert len(rows) >= 25
    assert not missing, missing


@need_results
@pytest.mark.skipif(not SUPPLEMENT.exists(), reason="run src/revision_supplement.py first")
def test_paper_result_macros_are_current():
    from export_latex_results import build
    expected, _, _ = build(load(RESULTS), load(SUPPLEMENT))
    current = ROOT / CFG["output"].get("paper_results_tex", "paper/generated/results.tex")
    assert current.read_text(encoding="utf-8") == expected, "run `python src/export_latex_results.py`"


def test_paper_source_has_no_hand_typed_results():
    # Every result in main.tex must be a macro from generated/results.tex.
    offenders = [f"main.tex:{i}" for i, line in enumerate(MAIN_TEX.read_text(encoding="utf-8").splitlines(), 1)
                 if not line.lstrip().startswith("%") and re.search(r"(?<![\w.])0\.\d{3}\b", line)]
    assert not offenders, offenders


def test_bibliography_is_current():
    # paper/main.bbl is committed (so the reference tests run without TeX); it must match main.tex and references.bib.
    tex = MAIN_TEX.read_text(encoding="utf-8")
    cited = []
    for group in re.findall(r"\\cite\{([^}]*)\}", tex):
        for key in (k.strip() for k in group.split(",")):
            if key not in cited:
                cited.append(key)
    bbl = BBL.read_text(encoding="utf-8")
    items = [k for k in re.findall(r"\\bibitem\{([^}]*)\}", bbl) if k != "BSTcontrol"]
    assert items == cited, "paper/main.bbl is stale; run `python paper/build.py`"
    norm = lambda t: re.sub(r"[^a-z0-9]", "", re.sub(r"\\[a-zA-Z]+|[{}]", "", t).lower())
    bib = (PAPER / "references.bib").read_text(encoding="utf-8")
    for key, title in re.findall(r"@\w+\{(\w+),[^@]*?\btitle\s*=\s*\{(.*?)\},\s*\n", bib, re.S):
        assert norm(title) in norm(bbl), f"title of [{key}] in references.bib differs from main.bbl; rebuild the paper"


def test_website_serves_current_paper_pdf():
    assert PUBLIC_PDF.exists(), "frontend/public PDF missing; run `npm run sync-paper` in frontend/"
    assert PUBLIC_PDF.read_bytes() == PDF.read_bytes(), "frontend/public PDF differs from paper/ PDF; run `npm run sync-paper`"


def test_old_paper_url_redirects_to_current_pdf():
    # Cloudflare Pages _redirects: "<from> <to> <status>"
    rules = [l.split() for l in (ROOT / "frontend" / "public" / "_redirects").read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.lstrip().startswith("#")]
    assert ["/LEN_Small_Measurement_Validity_Audit_Research_Paper.pdf", f"/{PDF.name}", "301"] in rules
    for rule in rules:
        assert len(rule) == 3 and rule[0].startswith("/") and rule[2] in ("301", "302", "307", "308"), rule
        assert (ROOT / "frontend" / "public" / rule[1].lstrip("/")).exists(), f"redirect target missing: {rule[1]}"


@need_results
def test_website_title_is_paper_title():
    pytest.importorskip("pypdf")
    from claim_evidence_audit import pdf_text
    title = load(PAYLOAD_PATH)["metadata"]["paper_title"]
    assert title in pdf_text(PDF)
    assert f"\\title{{{title}}}" in MAIN_TEX.read_text(encoding="utf-8")


def test_website_references_equal_paper_references():
    from export_references import references
    assert references(BBL) == load(SITE_SRC / "lib" / "references.json"), "run `python paper/export_references.py`"


def test_website_source_has_no_hand_typed_results():
    # Result values are three-decimal numbers; on the site they must come from the payload, not literals.
    offenders = []
    for f in SITE_SRC.rglob("*.jsx"):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"(?<![\w.])0\.\d{3,4}\b", line):
                offenders.append(f"{f.relative_to(ROOT)}:{i}")
    assert not offenders, offenders


def test_no_superseded_headlines_on_website():
    superseded = ["0.923", "0.9229", "0.594", "0.598", "92.7", "Zero Score-Peeking", "Methodology_Audit",
                  "Measurement_Validity_Audit", "outputs/run_v2"]
    text = "\n".join(f.read_text(encoding="utf-8") for f in SITE_SRC.rglob("*.js*")) + (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert not [s for s in superseded if s in text]


@need_results
def test_superseded_value_is_labelled():
    R = load(RESULTS)
    hits = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
        elif isinstance(o, float) and round(o, 4) == 0.9229:
            key = path.rsplit("/", 1)[-1]
            if "balanced_accuracy" in key or key.endswith("_ba") or "ba_mean" in key:  # 0.923 is a BA value
                hits.append(path)

    walk(R, "")
    assert hits == ["/superseded_run_final/A_combined_logreg_ba"], hits
    assert "superseded" in R["superseded_run_final"]["_note"].lower()
