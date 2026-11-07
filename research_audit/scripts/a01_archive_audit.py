"""
a01_archive_audit.py — independent audit of the raw LEN-Small archive.

Reads small_encoder_final.tar directly (does not use the project's ingestion code) and
records, for every JSON member: SHA-256, byte size, Unicode normalisation of the name,
label token, node/edge counts, directed/multigraph flags, graph/node/edge attribute
keys, node-id type and range, self-loops, repeated (source, target) pairs, and any
node attribute that could be an account identifier.

Output: research_audit/outputs/a01_archive_members.csv, a01_archive_summary.json
Usage:  python research_audit/scripts/a01_archive_audit.py
"""
import hashlib
import json
import sys
import tarfile
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
TAR = ROOT / "small_encoder_final.tar"
OUT = ROOT / "research_audit" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

rows, node_keys, edge_keys, graph_keys = [], Counter(), Counter(), Counter()
sample_node_attrs = {}
with tarfile.open(TAR) as t:
    for m in t:
        if not m.isfile():
            continue
        raw = t.extractfile(m).read()
        name = m.name.split("/")[-1]
        rec = {"member": m.name, "name": name, "bytes": m.size, "sha256": hashlib.sha256(raw).hexdigest(),
               "nfc_equal": unicodedata.normalize("NFC", name) == name,
               "nfkd_ascii": unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode(),
               "label_token": "noncampaign" if "_noncampaign_" in name else "campaign" if "_campaign_" in name else "none"}
        if not name.endswith(".json"):
            rows.append(rec)
            continue
        g = json.loads(raw)
        del raw
        nodes = g.get("nodes", [])
        links = g.get("links", g.get("edges", []))
        rec.update(directed=g.get("directed"), multigraph=g.get("multigraph"), n_nodes=len(nodes), n_links=len(links))
        graph_keys.update(k for k in g if k not in ("nodes", "links", "edges"))
        rec["graph_attrs"] = json.dumps({k: g[k] for k in g if k not in ("nodes", "links", "edges", "directed", "multigraph")}, ensure_ascii=False)[:300]
        ids = [n.get("id") for n in nodes]
        rec["id_types"] = ",".join(sorted({type(i).__name__ for i in ids}))
        int_ids = [i for i in ids if isinstance(i, int)]
        rec["ids_are_0_to_n_minus_1"] = sorted(int_ids) == list(range(len(nodes)))
        for n in nodes:
            node_keys.update(n.keys())
        for e in links:
            edge_keys.update(e.keys())
        pairs = [(e.get("source"), e.get("target")) for e in links]
        rec["self_loops"] = sum(1 for s, d in pairs if s == d)
        rec["repeated_pairs"] = len(pairs) - len(set(pairs))
        rec["undirected_repeated_pairs"] = len(pairs) - len({tuple(sorted((s, d))) for s, d in pairs})
        rec["isolated_nodes"] = len(set(ids) - {x for p in pairs for x in p})
        if not sample_node_attrs and nodes:
            sample_node_attrs = {k: (str(v)[:80] if not isinstance(v, list) else f"list[{len(v)}]") for k, v in nodes[0].items()}
            sample_edge_attrs = {k: (str(v)[:80] if not isinstance(v, list) else f"list[{len(v)}]") for k, v in links[0].items()}
        rows.append(rec)
        print(f"{len(rows):4d} {name[:60]:60s} n={len(nodes):6d} m={len(links):7d}", flush=True)

df = pd.DataFrame(rows)
df.to_csv(OUT / "a01_archive_members.csv", index=False, encoding="utf-8")
js = df[df.name.str.endswith(".json")]
dup = js[js.duplicated("sha256", keep=False)]
canon = js.drop_duplicates("sha256")
summary = {
    "tar_bytes": TAR.stat().st_size,
    "members_total": int(len(df)), "json_members": int(len(js)),
    "duplicate_groups": dup.groupby("sha256").name.apply(list).tolist(),
    "canonical_json": int(len(canon)),
    "canonical_labels": canon.label_token.value_counts().to_dict(),
    "non_nfc_names": js.loc[~js.nfc_equal, "name"].tolist(),
    "directed_values": js.directed.value_counts(dropna=False).astype(int).to_dict() if "directed" in js else None,
    "multigraph_values": js.multigraph.value_counts(dropna=False).astype(int).to_dict() if "multigraph" in js else None,
    "graph_keys": dict(graph_keys), "node_attribute_keys": dict(node_keys), "edge_attribute_keys": dict(edge_keys),
    "sample_node_attributes": sample_node_attrs, "sample_edge_attributes": sample_edge_attrs,
    "all_ids_0_to_n_minus_1": bool(js.ids_are_0_to_n_minus_1.all()),
    "files_with_self_loops": int((canon.self_loops > 0).sum()), "self_loops_total": int(canon.self_loops.sum()),
    "repeated_directed_pairs_total": int(canon.repeated_pairs.sum()),
    "isolated_nodes_total": int(canon.isolated_nodes.sum()),
    "nodes_total": int(canon.n_nodes.sum()), "links_total": int(canon.n_links.sum()),
}
(OUT / "a01_archive_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k not in ("sample_node_attributes",)}, indent=1, ensure_ascii=False, default=str)[:3000])
