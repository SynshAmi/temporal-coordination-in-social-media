"""
o02_occupancy_features.py — per-event features for the occupancy reproduction, computed directly
from the raw archive (small_encoder_final.tar). The byte-identical duplicate is dropped as in the
pipeline (only archive names present in the manifest are used).

Graph convention (matches the raw files and the pipeline): directed, simple (no repeated directed
pair), self-loops present; nodes = the file's node list (ids 0..N-1, no isolated nodes in this archive).

  n, m         node count; directed edge count including self-loops
  d_v          distinct directed edges incident to v = out_v + in_v - [self-loop at v]
  E_K          exact expected distinct endpoints of K edges drawn uniformly without replacement:
               sum_v [1 - C(m - d_v, K) / C(m, K)]   (NaN if m < K)
  E250_clip    same with K = min(250, m) (the external pilot's choice for the one event with m < 250)
  hom_binom    n [1 - (1 - K/m)^(2m/n)], K = min(250, m)  (the pilot's homogeneous approximation)
  hom_hyper    n [1 - C(m - dbar, K) / C(m, K)], dbar = mean d_v, K = 250 (exact form, every node at mean d)
  sum_d2       sum_v d_v^2;  deg1_frac  share of nodes with d_v = 1
  gini_in, gini_out   Gini of in- and out-degree (paper definition, eq. 1)

Output: research_audit/outputs/o02_features.csv
"""
import json
import unicodedata
import sys
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import gammaln

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet").set_index("event_id")
logC = lambda a, k: gammaln(a + 1) - gammaln(k + 1) - gammaln(a - k + 1)


def gini(x):
    x = np.sort(np.asarray(x, float))
    n, s = len(x), x.sum()
    return 0.0 if s == 0 else float((2 * np.arange(1, n + 1) @ x - (n + 1) * s) / (n * s))


def expected(d, m, K):
    q = np.where(m - d >= K, np.exp(logC(m - d, K) - logC(m, K)), 0.0)
    return float(np.sum(1 - q))


rows = []
with tarfile.open(ROOT / "small_encoder_final.tar") as tar:
    for mem in tar:
        if not mem.isfile() or not mem.name.endswith(".json"):
            continue
        eid = unicodedata.normalize("NFC", mem.name.split("/")[-1][:-5])  # as src/ingest_len.py
        if eid not in man.index:
            continue  # the dropped byte-identical duplicate
        g = json.loads(tar.extractfile(mem).read())
        n = len(g["nodes"])
        s = np.array([int(e["source"]) for e in g["links"]])
        t = np.array([int(e["target"]) for e in g["links"]])
        del g
        m = len(s)
        outd, ind = np.bincount(s, minlength=n), np.bincount(t, minlength=n)
        d = outd + ind - np.bincount(s[s == t], minlength=n)
        r = {"event_id": eid, "label": int(man.loc[eid, "label"]), "n": n, "m": m, "self_loops": int((s == t).sum()),
             "min_d": int(d.min()), "sum_d2": float((d.astype(float) ** 2).sum()), "deg1_frac": float((d == 1).mean()),
             "gini_in": gini(ind), "gini_out": gini(outd)}
        for K in (250, 500, 1000):
            r[f"E{K}"] = expected(d, m, K) if m >= K else np.nan
        Kc = min(250, m)
        r["E250_clip"] = expected(d, m, Kc)
        r["hom_binom"] = n * (1 - (1 - Kc / m) ** (2 * m / n))
        dbar = d.mean()
        r["hom_hyper"] = n * (1 - np.exp(logC(m - dbar, 250) - logC(m, 250))) if m >= 250 else np.nan
        rows.append(r)
        print(f"{eid[:50]:50s} n={n} m={m} E250={r['E250']}", flush=True)

F = pd.DataFrame(rows).sort_values("event_id").reset_index(drop=True)
assert len(F) == 103 and F.event_id.is_unique and (F.min_d >= 1).all()
assert (F.n.values == man.loc[F.event_id, "n_nodes"].values).all() and (F.m.values == man.loc[F.event_id, "n_edges"].values).all()
F.to_csv(ROOT / "research_audit/outputs/o02_features.csv", index=False, encoding="utf-8")
print("events", len(F), "| m >= 250:", int((F.m >= 250).sum()), "| labels", F.label.value_counts().to_dict())
