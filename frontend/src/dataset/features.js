import { f3 } from "../lib/fmt";

// Formatting for the paper's structural features
export const FEATURE_ROWS = [
  ["reciprocity", "Reciprocity", "Share of directed edges whose reverse edge is also present."],
  ["largest_wcc_fraction", "Largest component", "Fraction of nodes in the largest weakly connected component."],
  ["indegree_gini", "In-degree Gini", "Concentration of incoming edges: 0 = evenly spread, 1 = all on one node."],
  ["outdegree_gini", "Out-degree Gini", "Concentration of outgoing edges across nodes."],
  ["coreness_median", "Median core number", "k-core number on the undirected projection without self-loops (paper convention)."],
  ["coreness_max", "Maximum core number", "Largest k such that a k-core exists."],
  ["density", "Density", "|E| / (|V|(|V|−1)); fixed by the counts, so it encodes scale rather than structure."],
];
export const fmtFeature = (key, v) => (v == null ? "—" : key.startsWith("coreness") ? (Number.isInteger(v) ? String(v) : v.toFixed(1)) : key === "density" ? v.toExponential(2) : f3(v));
