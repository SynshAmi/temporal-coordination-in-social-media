"""
features.py
-----------
Feature extraction module for LEN-Small robustness audit.

Extracts feature groups:
- Scale: log1p(node_count), log1p(edge_count)
- Structure: density, reciprocity, largest_wcc_fraction, indegree_gini,
             outdegree_gini, coreness_median, coreness_max
- Content: exact_dup_proportion, text_concentration, msg_length_dispersion
- Combined: concatenation of all available groups
"""

import re
import sys
import numpy as np
import pandas as pd
import networkx as nx

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def gini(values: np.ndarray) -> float:
    """
    Computes Gini coefficient in [0, 1].
    0 = perfectly equal distribution, 1 = maximum concentration.
    """
    if len(values) == 0:
        return 0.0
    v = np.sort(np.abs(values))
    n = len(v)
    cumsum = np.cumsum(v)
    if cumsum[-1] == 0:
        return 0.0
    return float((2 * np.dot(np.arange(1, n + 1), v) - (n + 1) * cumsum[-1]) / (n * cumsum[-1]))


def edges_to_digraph(edge_rows: pd.DataFrame) -> nx.DiGraph:
    """
    Reconstructs DiGraph from edge rows with 'source' and 'target' columns.
    Only nodes incident to existing edges are included.
    """
    G = nx.DiGraph()
    G.add_edges_from(zip(edge_rows["source"].astype(str), edge_rows["target"].astype(str)))
    return G


def extract_scale_features(G: nx.DiGraph) -> dict:
    return {
        "log_node_count": float(np.log1p(G.number_of_nodes())),
        "log_edge_count": float(np.log1p(G.number_of_edges())),
    }


def core_numbers_undirected(G: nx.DiGraph) -> np.ndarray:
    """
    Core numbers k(v) for every node of a directed engagement graph.

    Convention: k-cores are computed on the simple undirected projection with
    self-loops removed ({u, v} is an edge iff (u, v) or (v, u) is a directed
    edge and u != v). All nodes are kept; a node whose only edges are
    self-loops has core number 0. NetworkX's core_number rejects self-loops,
    so they must be removed explicitly; any other error propagates.
    """
    U = nx.Graph()
    U.add_nodes_from(G.nodes())
    U.add_edges_from((u, v) for u, v in G.edges() if u != v)
    return np.array(list(nx.core_number(U).values()), dtype=float)


def extract_structural_features(G: nx.DiGraph) -> dict:
    n = G.number_of_nodes()
    m = G.number_of_edges()

    density = nx.density(G) if n > 1 else 0.0
    reciprocity = nx.reciprocity(G) if m > 0 else 0.0

    if n > 0:
        wccs = sorted(nx.weakly_connected_components(G), key=len, reverse=True)
        largest_wcc_frac = len(wccs[0]) / n
    else:
        largest_wcc_frac = 0.0

    in_degrees = np.array([d for _, d in G.in_degree()], dtype=float)
    out_degrees = np.array([d for _, d in G.out_degree()], dtype=float)
    indegree_gini = gini(in_degrees)
    outdegree_gini = gini(out_degrees)

    core_vals = core_numbers_undirected(G)
    coreness_median = float(np.median(core_vals)) if len(core_vals) > 0 else 0.0
    coreness_max = float(core_vals.max()) if len(core_vals) > 0 else 0.0

    return {
        "density": float(density),
        "reciprocity": float(reciprocity),
        "largest_wcc_fraction": float(largest_wcc_frac),
        "indegree_gini": float(indegree_gini),
        "outdegree_gini": float(outdegree_gini),
        "coreness_median": float(coreness_median),
        "coreness_max": float(coreness_max),
    }


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"https?://\S+", "", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_content_features(edge_rows: pd.DataFrame, text_col: str = "text") -> dict:
    if text_col not in edge_rows.columns:
        return {
            "exact_dup_proportion": np.nan,
            "text_concentration": np.nan,
            "msg_length_dispersion": np.nan,
        }

    texts = edge_rows[text_col].dropna().apply(clean_text)
    texts = texts[texts != ""]

    if len(texts) == 0:
        return {
            "exact_dup_proportion": np.nan,
            "text_concentration": np.nan,
            "msg_length_dispersion": np.nan,
        }

    n_total = len(texts)
    n_unique = texts.nunique()
    exact_dup_proportion = 1.0 - (n_unique / n_total)

    freq = texts.value_counts().values.astype(float)
    text_concentration = gini(freq)

    lengths = texts.str.split().str.len().astype(float)
    msg_length_dispersion = float(lengths.std(ddof=1)) if len(lengths) > 1 else 0.0

    return {
        "exact_dup_proportion": float(exact_dup_proportion),
        "text_concentration": float(text_concentration),
        "msg_length_dispersion": float(msg_length_dispersion),
    }


def compute_all_features(
    edges_df: pd.DataFrame,
    manifest_df: pd.DataFrame,
    config: dict,
    event_ids: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    feat_cfg = config["features"]
    if event_ids is None:
        event_ids = manifest_df["event_id"].tolist()

    records = {g: [] for g in ["scale", "structure", "content", "combined"]}

    for eid in event_ids:
        ev_edges = edges_df[edges_df["event_id"] == eid]
        label_match = manifest_df[manifest_df["event_id"] == eid]
        if label_match.empty:
            continue
        label = int(label_match.iloc[0]["label"])

        G = edges_to_digraph(ev_edges)
        row_base = {"event_id": eid, "label": label}

        scale_feats = extract_scale_features(G) if feat_cfg.get("use_log_node_count", True) else {}
        records["scale"].append({**row_base, **scale_feats})

        struct_feats = extract_structural_features(G) if feat_cfg.get("use_density", True) else {}
        records["structure"].append({**row_base, **struct_feats})

        if feat_cfg.get("use_text_features", True):
            cont_feats = extract_content_features(ev_edges, "text")
        else:
            cont_feats = {}
        records["content"].append({**row_base, **cont_feats})

        all_feats = {**scale_feats, **struct_feats, **cont_feats}
        records["combined"].append({**row_base, **all_feats})

    result = {}
    for group, rows in records.items():
        df = pd.DataFrame(rows).set_index("event_id")
        result[group] = df

    return result


def compute_features_for_sampled_view(
    sampled_edges: pd.DataFrame,
    event_id: str,
    label: int,
    config: dict,
) -> dict:
    """
    Computes all features strictly from the sampled edge view.
    Never uses original full-graph counts.
    """
    G = edges_to_digraph(sampled_edges)
    feat_cfg = config["features"]

    feats = {"event_id": event_id, "label": label}
    feats.update(extract_scale_features(G))
    feats.update(extract_structural_features(G))

    if feat_cfg.get("use_text_features", True):
        feats.update(extract_content_features(sampled_edges, "text"))

    return feats
