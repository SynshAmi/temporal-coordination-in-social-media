"""
test_paper_website_parity.py
----------------------------
The paper and the website must present the same research. These tests catch
divergence between them:

- every headline claim's value appears verbatim in the built paper PDF;
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
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import RUN_DIR, PAYLOAD_PATH  # noqa: E402

PDF = ROOT / "reports" / "LEN_Small_Measurement_Validity_Audit_Research_Paper.pdf"
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


def test_website_serves_current_paper_pdf():
    if not PUBLIC_PDF.exists():
        pytest.skip("public PDF is copied by `npm run dev/build` (sync-paper)")
    assert PUBLIC_PDF.read_bytes() == PDF.read_bytes(), "frontend/public PDF differs from reports/ PDF; run `npm run sync-paper`"


@need_results
def test_website_title_is_paper_title():
    pytest.importorskip("pypdf")
    from claim_evidence_audit import pdf_text
    title = load(PAYLOAD_PATH)["metadata"]["paper_title"]
    assert title in pdf_text(PDF)
    assert title in (ROOT / "reports" / "paper" / "build_paper.js").read_text(encoding="utf-8")


@need_results
def test_website_references_equal_paper_references(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    out = tmp_path / "refs.json"
    subprocess.run([node, str(ROOT / "reports" / "paper" / "export_references.js"), str(out)], check=True, cwd=ROOT,
                   capture_output=True)
    assert load(out) == load(SITE_SRC / "lib" / "references.json"), "run `node reports/paper/export_references.js`"


def test_website_source_has_no_hand_typed_results():
    # Result values are three-decimal numbers; on the site they must come from the payload, not literals.
    offenders = []
    for f in SITE_SRC.rglob("*.jsx"):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"(?<![\w.])0\.\d{3,4}\b", line):
                offenders.append(f"{f.relative_to(ROOT)}:{i}")
    assert not offenders, offenders


def test_no_superseded_headlines_on_website():
    superseded = ["0.923", "0.9229", "0.594", "0.598", "92.7", "Zero Score-Peeking", "Methodology_Audit"]
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
