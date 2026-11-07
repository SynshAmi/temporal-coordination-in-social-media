"""
o01_export_equivalence.py — Do the repository-exported graphs (frontend/public/data/len/events/*.json,
the input of the external pilot) equal the raw archive graphs (small_encoder_final.tar)?

For each raw JSON member (the byte-identical duplicate is dropped exactly as in the pipeline: names are NFC-normalised exactly
as src/ingest_len.py does; the raw tar stores 41 names in decomposed form), compares with the exported graph of the same event_id:
node count, node-id set, the multiset of directed (source, target) pairs, edge order, self-loops,
interaction counts, label token, and the distinct-incident-edge degree d_v used by E[N_K].

Output: research_audit/outputs/o01_export_equivalence.csv and .json
"""
import json
import unicodedata
import sys
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
LEN = ROOT / "frontend/public/data/len"
idx = json.loads((LEN / "index.json").read_text(encoding="utf-8"))
by_id = {e["id"]: e for e in idx["events"]}
man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet").set_index("event_id")


def incident(n, s, t):
    return np.bincount(s, minlength=n) + np.bincount(t, minlength=n) - np.bincount(s[s == t], minlength=n)


rows, seen = [], set()
with tarfile.open(ROOT / "small_encoder_final.tar") as tar:
    for m in tar:
        if not m.isfile() or not m.name.endswith(".json"):
            continue
        name = unicodedata.normalize("NFC", m.name.split("/")[-1][:-5])  # as src/ingest_len.py
        if name not in by_id:
            rows.append({"raw_name": name, "in_export": False})
            continue
        g = json.loads(tar.extractfile(m).read())
        n_raw = len(g["nodes"])
        ids = sorted(int(x["id"]) for x in g["nodes"])
        s_raw = np.array([int(e["source"]) for e in g["links"]])
        t_raw = np.array([int(e["target"]) for e in g["links"]])
        w_raw = [int(e.get("Interaction_Count", 1)) for e in g["links"]]
        del g
        e = by_id[name]
        x = json.loads((LEN / e["graph"]).read_text(encoding="utf-8"))
        ex = np.array(x["edges"]).reshape(-1, 2)
        s_ex, t_ex = ex[:, 0], ex[:, 1]
        w_ex = x["w"] if x["w"] is not None else [1] * len(ex)
        same_order = len(s_raw) == len(s_ex) and bool((s_raw == s_ex).all() and (t_raw == t_ex).all())
        same_set = sorted(zip(s_raw.tolist(), t_raw.tolist())) == sorted(zip(s_ex.tolist(), t_ex.tolist()))
        rows.append({
            "raw_name": name, "in_export": True, "i": e["i"],
            "n_raw": n_raw, "n_export": x["n"], "node_ids_0_to_n_1": ids == list(range(n_raw)),
            "m_raw": len(s_raw), "m_export": len(s_ex), "edge_multiset_equal": same_set, "edge_order_equal": same_order,
            "loops_raw": int((s_raw == t_raw).sum()), "loops_export": int((s_ex == t_ex).sum()),
            "weights_equal_in_order": same_order and list(map(int, w_ex)) == w_raw,
            "d_v_equal": bool(np.array_equal(incident(n_raw, s_raw, t_raw), incident(x["n"], s_ex, t_ex))) if n_raw == x["n"] else False,
            "label_token": 0 if "_noncampaign_" in name + "_" else 1, "label_export": e["label"], "label_manifest": int(man.loc[name, "label"]),
        })
        seen.add(name)
        print(f"{e['i']:3d} {name[:50]:50s} nodes {n_raw}/{x['n']} edges {len(s_raw)}/{len(s_ex)} set={same_set} order={same_order}", flush=True)

D = pd.DataFrame(rows)
D.to_csv(ROOT / "research_audit/outputs/o01_export_equivalence.csv", index=False, encoding="utf-8")
E = D[D.in_export]
summary = {
    "raw_json_members": int(len(D)), "raw_members_matched_to_export": int(len(E)),
    "raw_members_not_in_export": D.loc[~D.in_export, "raw_name"].tolist(),
    "export_events_without_raw": sorted(set(by_id) - seen),
    "all_node_counts_equal": bool((E.n_raw == E.n_export).all()),
    "all_node_ids_0_to_n_1": bool(E.node_ids_0_to_n_1.all()),
    "all_edge_multisets_equal": bool(E.edge_multiset_equal.all()),
    "all_edge_orders_equal": bool(E.edge_order_equal.all()),
    "all_self_loop_counts_equal": bool((E.loops_raw == E.loops_export).all()),
    "all_interaction_counts_equal": bool(E.weights_equal_in_order.all()),
    "all_d_v_equal": bool(E.d_v_equal.all()),
    "labels_token_export_manifest_agree": bool(((E.label_token == E.label_export) & (E.label_export == E.label_manifest)).all()),
    "label_counts_export": E.label_export.value_counts().to_dict(),
}
(ROOT / "research_audit/outputs/o01_export_equivalence.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=int), encoding="utf-8")
print(json.dumps(summary, indent=1, ensure_ascii=False, default=int))
