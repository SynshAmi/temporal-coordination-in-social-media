"""
v01_view_text_availability.py — do the Study 2 K-edge views retain the message text needed for
message-length dispersion, and how much text does each view have?

Regenerates every Study 2 view's sampled edge set exactly as src/sample_views.py does (no new samples):
for each K, seed = 100 + i (i = 0..9), rng = numpy default_rng(seed) created per (K, seed), events
eligible if n_edges >= K iterated in manifest order, and K row positions drawn without replacement from
that event's rows of data/processed/edges.parquet. The regenerated views are checked against the stored
data/processed/sampled_views_v2.parquet (N_K and msg_length_dispersion must match).

Message-length dispersion is recomputed with the Study 1 definition (same as s01, written for the
audit): texts of the K sampled edges; null texts dropped; lower-case, URLs removed, whitespace
collapsed, stripped; empty texts dropped; repeated texts kept (each sampled edge counts once); sample
SD (ddof 1) of whitespace token counts; 0 if exactly one usable text; undefined (NaN) if none.

Output: research_audit/outputs/v01_view_text.csv (one row per view), v01_view_text.json, v01.log
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research_audit/outputs"
URL, WS = re.compile(r"https?://\S+"), re.compile(r"\s+")

man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet")
edges = pd.read_parquet(ROOT / "data/processed/edges.parquet", columns=["event_id", "source", "target", "text"])
stored = pd.read_parquet(ROOT / "data/processed/sampled_views_v2.parquet").set_index(["K", "seed", "event_id"])
groups = {e: g for e, g in edges.groupby("event_id", sort=False)}


def lensd(texts):
    cl = [WS.sub(" ", URL.sub("", t.lower())).strip() for t in texts if isinstance(t, str)]
    cl = [t for t in cl if t]
    if not cl:
        return np.nan, 0
    lens = np.array([len(t.split()) for t in cl], float)
    return (float(lens.std(ddof=1)) if len(lens) > 1 else 0.0), len(cl)


rows = []
for K in (250, 500, 1000):
    eligible = man[man.n_edges >= K].event_id.tolist()
    for i in range(10):
        seed = 100 + i
        rng = np.random.default_rng(seed)
        for eid in eligible:
            ev = groups[eid]
            s = ev.iloc[rng.choice(len(ev), size=K, replace=False)]
            sd, n_use = lensd(s.text.tolist())
            st = stored.loc[(K, seed, eid)]
            rows.append({"K": K, "seed": seed, "event_id": eid, "label": int(st.label),
                         "n_nodes_view": int(len(pd.unique(pd.concat([s.source, s.target])))),
                         "n_text_null": int(s.text.isna().sum()), "n_usable_text": n_use, "usable_share": n_use / K,
                         "lensd_recomputed": sd, "lensd_stored": float(st.msg_length_dispersion),
                         "log_nk_stored": float(st.log_node_count)})
    print(f"K={K}: {len(eligible)} events x 10 seeds regenerated", flush=True)

V = pd.DataFrame(rows)
assert len(V) == len(stored) == 2730
nk_ok = bool(np.allclose(np.log1p(V.n_nodes_view), V.log_nk_stored, rtol=0, atol=1e-12))
both = V.lensd_recomputed.notna() & V.lensd_stored.notna()
lensd_diff = float(np.abs(V.lensd_recomputed[both] - V.lensd_stored[both]).max())
nan_same = bool((V.lensd_recomputed.isna() == V.lensd_stored.isna()).all())
V.to_csv(OUT / "v01_view_text.csv", index=False, encoding="utf-8")

summ = {"views": len(V), "regenerated_NK_matches_stored": nk_ok, "lensd_max_abs_diff_vs_stored": lensd_diff,
        "lensd_nan_pattern_identical": nan_same, "by_K": {}}
for K, g in V.groupby("K"):
    d = {"events": int(g.event_id.nunique()), "campaign_events": int(g[g.label == 1].event_id.nunique()),
         "comparison_events": int(g[g.label == 0].event_id.nunique())}
    for lab, nm in ((1, "campaign"), (0, "comparison")):
        h = g[g.label == lab]
        ev_mean = h.groupby("event_id").usable_share.mean()
        d[nm] = {"views": int(len(h)), "usable_text_share_mean": float(h.usable_share.mean()),
                 "usable_text_share_median": float(h.usable_share.median()), "usable_text_share_min": float(h.usable_share.min()),
                 "views_lensd_undefined_no_text": int(h.lensd_stored.isna().sum()),
                 "views_with_lt_10_usable_texts": int((h.n_usable_text < 10).sum()),
                 "views_with_lt_25pct_usable_text": int((h.usable_share < 0.25).sum()),
                 "events_mean_usable_share_lt_0.2": int((ev_mean < 0.2).sum())}
    summ["by_K"][str(K)] = d
(OUT / "v01_view_text.json").write_text(json.dumps(summ, indent=2), encoding="utf-8")
print(json.dumps(summ, indent=1))
