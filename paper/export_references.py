"""
export_references.py
--------------------
Converts the compiled bibliography (paper/main.bbl, produced by BibTeX with
IEEEtran.bst) into the website's reference list, frontend/src/lib/references.json,
so the site lists exactly the paper's references, in citation order.
Italics are kept as *...* (rendered by the Methods page).

Usage (after building the paper): python paper/export_references.py [output path]
"""

import re
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PAPER = Path(__file__).resolve().parent
DEFAULT_OUT = PAPER.parent / "frontend" / "src" / "lib" / "references.json"

REPLACEMENTS = [
    (r"\BIBentryALTinterwordspacing", ""), (r"\BIBentrySTDinterwordspacing", ""), (r"\newblock", ""),
    ("``", "\u201c"), ("''", "\u201d"), ("---", "\u2014"), ("--", "\u2013"),
    (r"\,", "\u202f"), (r"{\i}", "\u0131"), (r'{\"u}', "\u00fc"), (r"\&", "&"), (r"\_", "_"), ("~", " "),
]


def to_text(tex):
    tex = re.sub(r"\\hskip[^\\]*\\relax", " ", tex)  # IEEEtran spacing after a book title
    for a, b in REPLACEMENTS:
        tex = tex.replace(a, b)
    tex = re.sub(r"\\emph\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", lambda m: "*" + m.group(1) + "*", tex)
    tex = re.sub(r"\\url\{([^}]*)\}", r"\1", tex)
    tex = tex.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", tex).strip()


def references(bbl_path=PAPER / "main.bbl"):
    bbl = Path(bbl_path).read_text(encoding="utf-8")
    items = re.split(r"\\bibitem\{[^}]*\}", bbl.split(r"\end{thebibliography}")[0])[1:]
    refs = [to_text(i) for i in items]
    return [r for r in refs if not r.startswith("IEEEtranBSTCTL")]


def main(out):
    refs = references()
    out.write_text(json.dumps(refs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(refs)} references -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT)
