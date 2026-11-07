"""
s01_content_verification.py — independent check of the three Study 1 content features against the raw
archive (small_encoder_final.tar), and of message-text availability per event.

Content features (paper Sec. III-A; definitions re-implemented here, not imported from src/):
  cleaned text   lower-case, URLs (http/https up to whitespace) removed, whitespace collapsed, stripped;
                 null and empty-after-cleaning texts are dropped
  exact_dup_proportion   1 - (#distinct cleaned texts / #cleaned texts)
  text_concentration     Gini (paper eq. 1) of the frequency vector of distinct cleaned texts
  msg_length_dispersion  sample SD (ddof 1) of whitespace token counts of cleaned texts (0 if one text)
An event with no usable text has all three undefined (NaN), as in the pipeline.

Also records, per event and from the raw links: edges, links whose `text` is absent / null / empty
before cleaning, and the share of usable texts. The byte-identical duplicate is dropped as in the
pipeline (names NFC-normalised, only manifest events kept).

Outputs: research_audit/outputs/s01_content_verification.csv, .json
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
OUT = ROOT / "research_audit/outputs"
man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet").set_index("event_id")
stored = pd.read_parquet(ROOT / "outputs/run_v2/study1/full_graph_features.parquet")
URL, WS = re.compile(r"https?://\S+"), re.compile(r"\s+")
CONTENT = ["exact_dup_proportion", "text_concentration", "msg_length_dispersion"]


def gini(x):
    x = np.sort(np.asarray(x, float))
    n, s = len(x), x.sum()
    return 0.0 if n == 0 or s == 0 else float((2 * np.arange(1, n + 1) @ x - (n + 1) * s) / (n * s))


def content(texts):
    cleaned = [WS.sub(" ", URL.sub("", t.lower())).strip() for t in texts if isinstance(t, str)]
    cleaned = [t for t in cleaned if t]
    if not cleaned:
        return {c: np.nan for c in CONTENT} | {"n_usable_text": 0}
    _, freq = np.unique(cleaned, return_counts=True)
    lens = np.array([len(t.split()) for t in cleaned], float)
    return {"exact_dup_proportion": 1 - len(freq) / len(cleaned), "text_concentration": gini(freq),
            "msg_length_dispersion": float(lens.std(ddof=1)) if len(lens) > 1 else 0.0, "n_usable_text": len(cleaned)}


rows = []
with tarfile.open(ROOT / "small_encoder_final.tar") as tar:
    for mem in tar:
        if not mem.isfile() or not mem.name.endswith(".json"):
            continue
        eid = unicodedata.normalize("NFC", mem.name.split("/")[-1][:-5])
        if eid not in man.index:
            continue
        links = json.loads(tar.extractfile(mem).read())["links"]
        texts = [l.get("text") for l in links]
        r = {"event_id": eid, "label": int(man.loc[eid, "label"]), "m": len(links),
             "text_key_absent": sum("text" not in l for l in links), "text_null": sum(t is None for t in texts),
             "text_empty_raw": sum(isinstance(t, str) and not t.strip() for t in texts), **content(texts)}
        r["usable_text_share"] = r["n_usable_text"] / r["m"]
        rows.append(r)
        del links, texts
        print(f"{eid[:50]:50s} m={r['m']:6d} null={r['text_null']:6d} usable={r['n_usable_text']}", flush=True)

D = pd.DataFrame(rows).set_index("event_id").sort_index()
assert len(D) == 103 and (D.m.values == man.loc[D.index, "n_edges"].values).all()
S = stored.loc[D.index, CONTENT]
diff = {c: float(np.nanmax(np.abs(D[c] - S[c]))) for c in CONTENT}
nan_agree = bool((D[CONTENT].isna().values == S.isna().values).all())
D.to_csv(OUT / "s01_content_verification.csv", encoding="utf-8")
by = D.groupby("label").usable_text_share
summary = {
    "events": len(D), "content_max_abs_diff_vs_pipeline": diff, "nan_pattern_identical": nan_agree,
    "events_without_usable_text": D.index[D.n_usable_text == 0].tolist(),
    "links_text_key_absent": int(D.text_key_absent.sum()), "links_text_null": int(D.text_null.sum()),
    "links_text_empty_raw": int(D.text_empty_raw.sum()), "links_total": int(D.m.sum()),
    "usable_text_share_by_label": {str(k): {"mean": float(v.mean()), "median": float(v.median()), "min": float(v.min()), "max": float(v.max())}
                                   for k, v in by},
    "events_usable_share_below_0.2": {str(k): int((v < 0.2).sum()) for k, v in by},
}
(OUT / "s01_content_verification.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=1, ensure_ascii=False))
