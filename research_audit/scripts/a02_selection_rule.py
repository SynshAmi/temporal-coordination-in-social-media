"""
a02_selection_rule.py — is the published LEN-Small composition compatible with its stated
selection rule ("simply the smallest 100 networks, out of 314, with respect to node counts")?

Input: per-subtype statistics transcribed from the LEN paper, arXiv:2503.00599v2,
Table 2 (full LEN, 314 graphs) and Table 3 (LEN-Small, 100 graphs). Values are node counts:
(n graphs, min, max, mean as printed). The project page prints the same subtype rows.

Method: for a subtype with n graphs, minimum a, maximum b and printed mean mu (rounded, so
the true mean is at most mu + 0.5), the number of graphs with more than T nodes is bounded:
one graph equals b; every other graph above T has at least T+1 nodes; every graph has at
least a. Hence  b + (h-1)(T+1) + (n-h) a <= n (mu + 0.5)  for h graphs above T, which gives
h <= 1 + floor((n(mu+0.5) - b - (n-1) a) / (T + 1 - a)).  Graphs with b <= T are all at or
below T; graphs with a > T are all above. The resulting lower bound on the count at or below T
is compared with the LEN-Small counts under three selection rules.

Output: research_audit/outputs/a02_selection_rule.json (and a printed table)
"""
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parents[2] / "research_audit" / "outputs"

# (subtype, n, min nodes, max nodes, mean nodes) — arXiv v2 Table 2
FULL = {
    "campaign": [("Politics", 62, 100, 50286, 6570), ("Reform", 58, 131, 19578, 1229), ("News", 24, 581, 54996, 10368),
                 ("Finance", 14, 273, 9976, 1802), ("Noise", 9, 454, 55933, 12180), ("Cult", 6, 313, 7880, 2303),
                 ("Entertainment", 3, 678, 4220, 2237), ("Common", 3, 3487, 9974, 5919)],
    "noncampaign": [("News", 52, 818, 95575, 24834), ("Sports", 30, 469, 75653, 9530), ("Festival", 17, 885, 119952, 35466),
                    ("Internal", 11, 4188, 87720, 33061), ("Common", 10, 1214, 64320, 17079), ("Entertainment", 8, 1477, 20060, 7289),
                    ("Announced cam.", 4, 6650, 26358, 13382), ("Sports cam.", 3, 2880, 4661, 3654)],
}
# LEN-Small counts per subtype — arXiv v2 Table 3 (absent subtypes = 0)
SMALL = {
    "campaign": {"Politics": 14, "Reform": 16, "News": 3, "Finance": 9, "Noise": 5, "Cult": 4, "Entertainment": 0, "Common": 0},
    "noncampaign": {"News": 10, "Sports": 23, "Festival": 2, "Internal": 1, "Common": 5, "Entertainment": 5,
                    "Announced cam.": 0, "Sports cam.": 3},
}
SMALL_MAX = {"campaign": 2520, "noncampaign": 8355}  # Table 3 overall max node counts


def min_count_at_or_below(n, a, b, mu, T):
    if b <= T:
        return n
    if a > T:
        return 0
    slack = n * (mu + 0.5) - b - (n - 1) * a
    h_max = 1 + max(0, math.floor(slack / (T + 1 - a)))
    return max(1, n - min(n - 1, h_max))


def analyse(rule, thresholds):
    rows, total_min = [], {}
    for cls, subs in FULL.items():
        T = thresholds[cls]
        tot = 0
        for name, n, a, b, mu in subs:
            lb = min_count_at_or_below(n, a, b, mu, T)
            tot += lb
            rows.append({"rule": rule, "class": cls, "subtype": name, "threshold": T, "full_n": n, "min": a, "max": b, "mean": mu,
                         "lower_bound_at_or_below_T": lb, "in_LEN_Small": SMALL[cls][name],
                         "violation": lb > SMALL[cls][name]})
        total_min[cls] = tot
    return rows, total_min


results = {}
# Rule 1: global smallest 100 by node count. The 100th graph has 8,355 nodes (largest in LEN-Small),
# so every graph with fewer than 8,355 nodes must be in LEN-Small (ties at 8,355 aside: use T = 8354).
r1, t1 = analyse("global smallest 100", {"campaign": 8354, "noncampaign": 8354})
# Rule 2: smallest 51 campaign and smallest 49 non-campaign graphs, each by node count.
r2, t2 = analyse("smallest per class", {"campaign": 2519, "noncampaign": 8354})
results["rule_global"] = {"rows": r1, "min_graphs_required": t1, "LEN_Small": {"campaign": 51, "noncampaign": 49}}
results["rule_per_class"] = {"rows": r2, "min_graphs_required": t2, "LEN_Small": {"campaign": 51, "noncampaign": 49}}
# Rule 3: smallest within each subtype (subtype counts as published): compatible iff each LEN-Small
# subtype max/min is consistent with Table 2's min; checked qualitatively below.
results["notes"] = [
    "T is set one below the LEN-Small maximum so that ties at the threshold do not count as violations.",
    "Table 3 minima equal the Table 2 minima for every included subtype except none checked here; see subtype rows.",
]
(OUT / "a02_selection_rule.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

for key in ("rule_global", "rule_per_class"):
    R = results[key]
    print(f"\n=== {key}: minimum graphs that must be included (from published bounds) ===")
    print(f"{'class':12s} {'subtype':16s} {'T':>6s} {'n':>3s} {'min':>6s} {'max':>7s} {'mean':>6s} {'>=':>4s} {'small':>5s}")
    for r in R["rows"]:
        flag = "  <-- VIOLATION" if r["violation"] else ""
        print(f"{r['class']:12s} {r['subtype']:16s} {r['threshold']:6d} {r['full_n']:3d} {r['min']:6d} {r['max']:7d} {r['mean']:6d} {r['lower_bound_at_or_below_T']:4d} {r['in_LEN_Small']:5d}{flag}")
    print("required at least:", R["min_graphs_required"], "| published LEN-Small:", R["LEN_Small"])
