"""
build.py
--------
Builds the paper: refreshes the audit values and regenerates the result macros, compiles main.tex with
pdflatex and BibTeX, checks the log, and copies the PDF to the official name
used by the website.

Usage (from the project root): python paper/build.py [--config CONFIG]
Requires a TeX distribution with pdflatex and bibtex on PATH (TeX Live or MiKTeX).
"""

import re
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parent
OFFICIAL = PAPER / "Finding_Signal_in_Network_Simplicity.pdf"


def run(cmd):
    r = subprocess.run(cmd, cwd=PAPER, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        tail = "\n".join((r.stdout or "").splitlines()[-25:])
        raise SystemExit(f"FAILED: {' '.join(cmd)}\n{tail}")


def main(config):
    for tool in ("pdflatex", "bibtex"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} not found on PATH; install TeX Live or MiKTeX.")
    subprocess.run([sys.executable, str(ROOT / "src" / "export_audit_results.py"), "--config", config], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "src" / "export_latex_results.py"), "--config", config], cwd=ROOT, check=True)
    latex = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    run(latex)
    run(["bibtex", "main"])
    run(latex)
    run(latex)

    log = (PAPER / "main.log").read_text(encoding="utf-8", errors="replace")
    problems = re.findall(r"^(?:LaTeX Warning: (?:Reference|Citation).*undefined.*|LaTeX Warning: There were undefined references\.|Overfull \\hbox.*)$", log, re.M)
    pages = re.search(r"Output written on main\.pdf \((\d+) pages", log)
    shutil.copyfile(PAPER / "main.pdf", OFFICIAL)
    print(f"Built {OFFICIAL.relative_to(ROOT)} ({pages.group(1) if pages else '?'} pages)")
    if problems:
        print("Log problems:")
        for p in problems:
            print("  " + p)
        raise SystemExit(1)
    print("No undefined references or overfull boxes.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    main(ap.parse_args().config)
