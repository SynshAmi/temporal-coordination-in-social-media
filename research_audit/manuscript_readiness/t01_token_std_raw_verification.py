"""
t01_token_std_raw_verification.py — independent recomputation of token_std (stored as msg_length_dispersion)
from the RAW archive, on full graphs and on the STORED sampled-view edge sets, compared with the stored values.
Verification only: no model, no resampling, no pipeline code imported, nothing outside this directory written.

Definition implemented here (written from the paper's description, not imported from src/):
  unit        one directed edge ("link") of the raw node-link JSON; texts are taken per edge, so a text that
              occurs on several edges counts once per edge (repeats kept; NOT deduplicated to unique texts)
  missing     link text that is null / not a string is dropped
  cleaning    lower-case (Python str.lower); remove every match of https?://\\S+; collapse runs of whitespace to
              one space; strip; texts empty after cleaning are dropped
  tokens      Python str.split() (whitespace); token count = number of tokens of a cleaned text
  token_std   sample standard deviation (ddof = 1) of token counts over the usable texts;
              0 if exactly one usable text; undefined (NaN) if none
  m           number of usable texts (m_K for a K-edge view)

Inputs (read only):
  small_encoder_final.tar                              raw archive (links read in file order)
  data/manifests/manifest.parquet                      canonical events (the byte-identical duplicate excluded)
  frontend/public/data/len/index.json, samples/eNNN.json   stored sampled-edge positions per (event, K, seed)
  data/processed/sampled_views_v2.parquet              stored view features
  outputs/run_v2/study1/full_graph_features.parquet    stored full-graph features
Outputs: research_audit/manuscript_readiness/t01_full.csv, t01_views.csv, t01_summary.json, t01.log
"""
import json
import re
import sys
import tarfile
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
URL, WS = re.compile(r"https?://\S+"), re.compile(r"\s+")
FE = ROOT / "frontend/public/data/len"


def token_std(texts):
    cl = [WS.sub(" ", URL.sub("", t.lower())).strip() for t in texts if isinstance(t, str)]
    cl = [t for t in cl if t]
    if not cl:
        return np.nan, 0
    n = np.array([len(t.split()) for t in cl], float)
    return (float(n.std(ddof=1)) if len(n) > 1 else 0.0), len(cl)


man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet").set_index("event_id")
full_st = pd.read_parquet(ROOT / "outputs/run_v2/study1/full_graph_features.parquet")
views_st = pd.read_parquet(ROOT / "data/processed/sampled_views_v2.parquet").set_index(["event_id", "K", "seed"])
index = json.loads((FE / "index.json").read_text(encoding="utf-8"))
id_of = {e["i"]: e["id"] for e in index["events"]}

# raw texts per canonical event, in file (link) order
raw = {}
with tarfile.open(ROOT / "small_encoder_final.tar") as tar:
    for mem in tar:
        if not mem.isfile() or not mem.name.endswith(".json"):
            continue
        eid = unicodedata.normalize("NFC", mem.name.split("/")[-1][:-5])
        if eid not in man.index or eid in raw:
            continue
        raw[eid] = [l.get("text") for l in json.loads(tar.extractfile(mem).read())["links"]]
print(f"raw events read: {len(raw)}", flush=True)
assert len(raw) == 103 and all(len(raw[e]) == man.loc[e, "n_edges"] for e in raw)

frows = []
for eid, texts in raw.items():
    sd, m = token_std(texts)
    frows.append({"event_id": eid, "label": int(man.loc[eid, "label"]), "n_edges": len(texts), "m_usable": m,
                  "token_std_raw": sd, "token_std_stored": float(full_st.loc[eid, "msg_length_dispersion"])})
F = pd.DataFrame(frows)

vrows = []
for f in sorted((FE / "samples").glob("e*.json")):
    s = json.loads(f.read_text(encoding="utf-8"))
    eid = id_of[s["i"]]
    texts = raw[eid]
    for K, rec in s["budgets"].items():
        for seed, idx in zip(rec["seeds"], rec["edges"]):
            assert len(idx) == int(K) and len(set(idx)) == int(K) and max(idx) < len(texts)
            sd, m = token_std([texts[i] for i in idx])
            vrows.append({"event_id": eid, "label": int(man.loc[eid, "label"]), "K": int(K), "seed": int(seed), "m_K": m,
                          "token_std_raw": sd, "token_std_stored": float(views_st.loc[(eid, int(K), int(seed)), "msg_length_dispersion"])})
V = pd.DataFrame(vrows)


def cmp(df):
    both = df.token_std_raw.notna() & df.token_std_stored.notna()
    return {"n": int(len(df)), "max_abs_diff": float(np.abs(df.token_std_raw[both] - df.token_std_stored[both]).max()),
            "n_abs_diff_gt_1e-9": int((np.abs(df.token_std_raw[both] - df.token_std_stored[both]) > 1e-9).sum()),
            "nan_pattern_identical": bool((df.token_std_raw.isna() == df.token_std_stored.isna()).all()),
            "n_undefined": int(df.token_std_raw.isna().sum())}


summ = {"full_graphs": cmp(F), "views": cmp(V),
        "views_total_expected_in_sampled_views_v2": int(len(views_st)),
        "views_covered_by_stored_edge_sets": int(len(V)),
        "undefined_full_graph_events": F[F.token_std_raw.isna()].event_id.tolist(),
        "undefined_view_events_by_K": {str(K): sorted(g[g.token_std_raw.isna()].event_id.unique().tolist()) for K, g in V.groupby("K")},
        "undefined_views_by_K_event": {f"{K}|{e}": int(n) for (K, e), n in V[V.token_std_raw.isna()].groupby(["K", "event_id"]).size().items()},
        "m_K_by_K_class": {}}
for (K, lab), g in V.groupby(["K", "label"]):
    summ["m_K_by_K_class"][f"K{K}|{'campaign' if lab == 1 else 'comparison'}"] = {
        "views": int(len(g)), "events": int(g.event_id.nunique()), "min": int(g.m_K.min()), "median": float(g.m_K.median()),
        "max": int(g.m_K.max()), "views_m_K_0": int((g.m_K == 0).sum()), "views_m_K_1": int((g.m_K == 1).sum()),
        "views_m_K_lt_10": int((g.m_K < 10).sum())}
F.to_csv(OUT / "t01_full.csv", index=False, encoding="utf-8")
V.to_csv(OUT / "t01_views.csv", index=False, encoding="utf-8")
(OUT / "t01_summary.json").write_text(json.dumps(summ, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summ, indent=1, ensure_ascii=False))
