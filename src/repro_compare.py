"""
repro_compare.py
----------------
Compares an isolated pipeline run (default: configs/repro_check.yaml) with the
verified run (configs/v2_coreness_fix.yaml), artifact by artifact.

For every file present in the verified run it reports one of:
  identical       byte-identical, or equal after ignoring run-specific fields
                  (timestamps, output paths)
  numeric drift   same structure, floating-point differences (max |diff| shown)
  DIFFERENT       structure or non-numeric content differs
  MISSING         not produced by the isolated run

Usage: python src/repro_compare.py [--repro configs/repro_check.yaml] [--ref configs/v2_coreness_fix.yaml]
Writes reports/reproducibility/comparison.json and prints a summary.
"""

import sys
import json
import hashlib
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.stdout.reconfigure(encoding="utf-8")

# Fields that legitimately differ between runs: wall-clock stamps and locations
IGNORE_KEYS = {"exported_at", "ingested_at", "generated_at", "timestamp", "source_run", "config", "_source",
               "_row_order_source", "run_dir", "elapsed_seconds", "runtime_seconds", "validated_at"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def strip_paths(o, roots):
    """Drop ignorable keys; normalise strings that embed the run's own paths."""
    if isinstance(o, dict):
        return {k: strip_paths(v, roots) for k, v in o.items() if k not in IGNORE_KEYS}
    if isinstance(o, list):
        return [strip_paths(v, roots) for v in o]
    if isinstance(o, str):
        for a, b in roots:
            o = o.replace(a, b)
        return o
    return o


def json_diff(a, b, path="", out=None):
    out = out if out is not None else {"max_abs": 0.0, "n_num": 0, "other": []}
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out["other"].append(f"{path}/{k}: key only in {'reference' if k in a else 'repro'}")
            else:
                json_diff(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out["other"].append(f"{path}: length {len(a)} vs {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            json_diff(x, y, f"{path}[{i}]", out)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        d = abs(float(a) - float(b))
        if d > 0:
            out["n_num"] += 1
            if d > out["max_abs"]:
                out["max_abs"], out["max_at"] = d, path
    elif a != b:
        out["other"].append(f"{path}: {str(a)[:60]!r} vs {str(b)[:60]!r}")
    return out


def frame_diff(a, b):
    a = a.drop(columns=[c for c in a.columns if c in IGNORE_KEYS])
    b = b.drop(columns=[c for c in b.columns if c in IGNORE_KEYS])
    added = [c for c in b.columns if c not in a.columns]
    if added and list(b.columns[: len(a.columns)]) == list(a.columns):
        r = frame_diff(a, b[list(a.columns)])  # repro adds columns: compare the shared ones
        r["note"] = f"repro adds column(s) {added}; shared columns compared"
        return r
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return {"other": [f"shape/columns {a.shape} {list(a.columns)[:6]} vs {b.shape} {list(b.columns)[:6]}"], "max_abs": 0.0, "n_num": 0}
    out = {"max_abs": 0.0, "n_num": 0, "other": []}
    for c in a.columns:
        x, y = a[c], b[c]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y) and not pd.api.types.is_bool_dtype(x):
            xa, ya = x.to_numpy(dtype=float), y.to_numpy(dtype=float)
            both_nan = np.isnan(xa) & np.isnan(ya)
            d = np.where(both_nan, 0.0, np.abs(xa - ya))
            if np.isnan(d).any():
                out["other"].append(f"{c}: NaN pattern differs")
                continue
            if d.max() > 0:
                out["n_num"] += int((d > 0).sum())
                if d.max() > out["max_abs"]:
                    out["max_abs"], out["max_at"] = float(d.max()), c
        elif not x.astype(str).equals(y.astype(str)):
            out["other"].append(f"{c}: {int((x.astype(str) != y.astype(str)).sum())} values differ")
    return out


def image_diff(a, b):
    from PIL import Image
    x, y = np.asarray(Image.open(a).convert("RGB"), dtype=int), np.asarray(Image.open(b).convert("RGB"), dtype=int)
    if x.shape != y.shape:
        return {"other": [f"image size {x.shape} vs {y.shape}"], "max_abs": 0.0, "n_num": 0}
    d = np.abs(x - y)
    return {"max_abs": float(d.max()), "n_num": int((d.max(axis=2) > 0).sum()), "other": [], "unit": "pixel channel (0-255)"}


def compare(ref, rep, roots):
    if not rep.exists():
        return {"status": "MISSING"}
    if sha(ref) == sha(rep):
        return {"status": "identical", "how": "byte-identical"}
    suf = ref.suffix.lower()
    if suf == ".json":
        r = json_diff(strip_paths(json.loads(ref.read_text(encoding="utf-8")), roots),
                      strip_paths(json.loads(rep.read_text(encoding="utf-8")), roots))
    elif suf == ".parquet":
        r = frame_diff(pd.read_parquet(ref), pd.read_parquet(rep))
    elif suf == ".csv":
        r = frame_diff(pd.read_csv(ref), pd.read_csv(rep))
    elif suf == ".png":
        r = image_diff(ref, rep)
    else:  # text (markdown reports)
        ta, tb = ref.read_text(encoding="utf-8"), rep.read_text(encoding="utf-8")
        for a, b in roots:
            tb = tb.replace(a, b)
        ta_l = [l for l in ta.splitlines() if "generated" not in l.lower() and "timestamp" not in l.lower()]
        tb_l = [l for l in tb.splitlines() if "generated" not in l.lower() and "timestamp" not in l.lower()]
        diff = [f"{x!r} vs {y!r}" for x, y in zip(ta_l, tb_l) if x != y][:5]
        if len(ta_l) != len(tb_l):
            diff.insert(0, f"line count {len(ta_l)} vs {len(tb_l)}")
        r = {"max_abs": 0.0, "n_num": 0, "other": diff}
    if r["other"]:
        status = "DIFFERENT"
    elif r["n_num"]:
        status = "numeric drift"
    else:
        status = "identical"
        r["how"] = r.pop("note", "equal after ignoring run-specific fields")
    return {"status": status, **r}


def main(repro_cfg, ref_cfg):
    A = yaml.safe_load(open(ref_cfg, encoding="utf-8"))
    B = yaml.safe_load(open(repro_cfg, encoding="utf-8"))
    pairs = []
    for key in ("manifests_dir", "processed_dir"):
        pairs.append((Path(A["data"][key]), Path(B["data"][key])))
    pairs.append((Path(A["output"]["run_dir"]), Path(B["output"]["run_dir"])))
    # strings in the repro outputs that name repro locations are mapped back to the reference ones
    roots = [(Path(b).as_posix(), Path(a).as_posix()) for a, b in pairs] + [(repro_cfg, ref_cfg)]

    rows = []
    for ref_dir, rep_dir in pairs:
        for f in sorted(p for p in ref_dir.rglob("*") if p.is_file()):
            if f.name in ("sampled_views.parquet", "file_hashes.csv", "pipeline_stages.json"):
                continue  # superseded-run views, a hand-exported table, and the run log
            rel = f.relative_to(ref_dir)
            rows.append({"reference": f.as_posix(), "repro": (rep_dir / rel).as_posix(), **compare(f, rep_dir / rel, roots)})
    fig_ref = Path(A["output"].get("paper_figures_dir", "paper/figures"))
    fig_rep = Path(B["output"]["paper_figures_dir"])
    for f in sorted(fig_ref.glob("*.pdf")):
        rows.append({"reference": f.as_posix(), "repro": (fig_rep / f.name).as_posix(), **compare(f, fig_rep / f.name, roots)})
    tex_ref = Path(A["output"].get("paper_results_tex", "paper/generated/results.tex"))
    tex_rep = Path(B["output"]["paper_results_tex"])
    rows.append({"reference": tex_ref.as_posix(), "repro": tex_rep.as_posix(), **compare(tex_ref, tex_rep, roots)})
    pay_ref = Path(A["output"].get("frontend_payload", "frontend/public/data/research_data.json"))
    pay_rep = Path(B["output"]["frontend_payload"])
    rows.append({"reference": pay_ref.as_posix(), "repro": pay_rep.as_posix(), **compare(pay_ref, pay_rep, roots)})

    out = Path("reports/reproducibility/comparison.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    counts = pd.Series([r["status"] for r in rows]).value_counts().to_dict()
    print(f"{len(rows)} artifacts compared: {counts}")
    for r in rows:
        if r["status"] != "identical" or r.get("how", "").startswith("repro adds"):
            extra = f"max|diff| {r.get('max_abs', 0):.3g} at {r.get('max_at', '')} ({r.get('n_num', 0)} values)" if r["status"] == "numeric drift" else ("; ".join(r.get("other", [])) or r.get("how", ""))[:300]
            print(f"  {r['status']:<13} {r['reference']}: {extra}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repro", default="configs/repro_check.yaml")
    ap.add_argument("--ref", default="configs/v2_coreness_fix.yaml")
    a = ap.parse_args()
    main(a.repro, a.ref)
