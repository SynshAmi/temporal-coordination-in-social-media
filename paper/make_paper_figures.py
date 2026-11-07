"""
make_paper_figures.py
---------------------
Single-column (3.5 in) figures for the research paper, built only from the
corrected run's verified outputs (outputs/run_v2/paper_results.json) and the
canonical manifest, plus the stored audit values collected by
src/export_audit_results.py (output.audit_results) for Fig. 3. No metric is
typed in by hand.

Run from the project root:
    python paper/make_paper_figures.py [--config CONFIG] [--out-dir DIR]
The config selects the run (output.run_dir) and data directories; the default
output directory is paper/figures (vector PDFs read by paper/main.tex).
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from study2_observation import expected_endpoints  # noqa: E402

import yaml  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config", default="configs/v2_coreness_fix.yaml")
ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent / "figures"))
args = ap.parse_args()
CFG = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
OUT = ROOT / args.out_dir
OUT.mkdir(parents=True, exist_ok=True)
R = json.loads((ROOT / CFG["output"]["run_dir"] / "paper_results.json").read_text(encoding="utf-8"))
manifest = pd.read_parquet(ROOT / CFG["data"]["manifests_dir"] / "manifest.parquet")

CAMP, COMP, INK, MUTE, ACC = "#8f2626", "#23527c", "#15263a", "#9a948a", "#c27d38"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6, "savefig.dpi": 600, "pdf.fonttype": 42,
})
W = 3.5


def save(fig, name):
    # Vector PDF for the paper; no creation date, so rebuilds are byte-stable
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02, metadata={"CreationDate": None})
    plt.close(fig)


# Fig. 1 - graph size by class (log scale)
fig, axes = plt.subplots(1, 2, figsize=(W, 1.9))
rng = np.random.default_rng(0)
for ax, col, title in zip(axes, ["n_nodes", "n_edges"], ["Nodes |V|", "Edges |E|"]):
    for pos, lab, color in [(0, 0, COMP), (1, 1, CAMP)]:
        v = np.log1p(manifest.loc[manifest.label == lab, col].values)
        ax.boxplot(v, positions=[pos], widths=0.45, showfliers=False,
                   medianprops=dict(color=color, linewidth=1.2), boxprops=dict(color=color, linewidth=0.7),
                   whiskerprops=dict(color=color, linewidth=0.7), capprops=dict(color=color, linewidth=0.7))
        ax.scatter(pos + rng.uniform(-0.17, 0.17, len(v)), v, s=4, color=color, alpha=0.55, linewidths=0)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"Comparison\n(n={int((manifest.label == 0).sum())})", f"Campaign\n(n={int((manifest.label == 1).sum())})"])
    ax.set_title(title)
    ticks = [100, 300, 1000, 3000, 10000]
    ax.set_yticks(np.log1p(ticks))
    ax.set_yticklabels(["100", "300", "1k", "3k", "10k"])
axes[0].set_ylabel("Count (log scale)")
fig.tight_layout(w_pad=1.0)
save(fig, "fig1_size_distributions")

# Fig. 2 - endpoint mechanism at K=250: expected sampled endpoints vs full-graph node count
edges = pd.read_parquet(ROOT / CFG["data"]["processed_dir"] / "edges.parquet")
elig250 = sorted(set(manifest.event_id) & set(edges.groupby("event_id").size().loc[lambda s: s >= 250].index))
rows = []
for eid in elig250:
    ev = edges[edges.event_id == eid]
    rows.append({"logN": np.log1p(manifest.set_index("event_id").loc[eid, "n_nodes"]),
                 "ENK": expected_endpoints(ev, 250), "label": int(manifest.set_index("event_id").loc[eid, "label"])})
md = pd.DataFrame(rows)
assert len(md) == R["eligibility"]["250"]["total_eligible"]
fig, ax = plt.subplots(figsize=(W, 2.0))
for lab, color, name in [(0, COMP, "Comparison"), (1, CAMP, "Campaign")]:
    s = md[md.label == lab]
    ax.scatter(np.expm1(s.logN), s.ENK, s=7, color=color, alpha=0.75, linewidths=0, label=f"{name} (n={len(s)})")
ax.set_xscale("log")
ax.set_xlabel("Full-graph node count |V| (log scale)")
ax.set_ylabel("Expected endpoints E[N$_K$], K=250")
r2 = R["study2"]["mechanism_r2_K250"]
ax.text(0.02, 0.97, f"R$^2$: log N {r2['log N only']:.2f}; + log mean degree {r2['log N + log mean degree']:.2f}\n"
                    f"+ in/out-degree Gini {r2['size + degree concentration']:.2f}",
        transform=ax.transAxes, va="top", fontsize=6.3)
ax.legend(loc="lower right", frameon=False)
fig.tight_layout()
save(fig, "fig2_endpoint_mechanism")

# Fig. 3 - token-count dispersion added to N_K (B - A) and to N_K + structure (D - C), by budget.
# Post hoc. Filled: trained and evaluated on single views (KK); open: full graphs of the same events (FF).
A = json.loads((ROOT / CFG["output"]["audit_results"]).read_text(encoding="utf-8"))
V = A["edge_limited_token_std"]["contrasts"]["primary"]
el = R["eligibility"]
fig, axes = plt.subplots(1, 2, figsize=(W, 2.2), sharey=True)
# vertical position within each budget row: (contrast, condition) -> offset
POS = {("B-A", "KK"): -0.27, ("B-A", "FF"): -0.11, ("D-C", "KK"): 0.11, ("D-C", "FF"): 0.27}
series = [("B-A", "Added to $N_K$ (B $-$ A)", INK), ("D-C", "Added to $N_K$ + structure (D $-$ C)", ACC)]
for ax, (key, cikey, xlab) in zip(axes, [("dLL", "dLL_ci", "Δ log loss (lower is better)"),
                                         ("dAUC", "dAUC_ci", "Δ AUC (higher is better)")]):
    for name, label, color in series:
        for cond in ("KK", "FF"):
            for j, k in enumerate((250, 500, 1000)):
                x = V[cond][name][f"K{k}"]
                v, (lo, hi) = x[key], x[cikey]
                first = j == 0 and key == "dLL"
                ax.errorbar(v, j + POS[(name, cond)], xerr=[[v - lo], [hi - v]], fmt="o" if cond == "KK" else "s",
                            ms=3.0 if cond == "KK" else 2.6, capsize=1.6, lw=0.9 if cond == "KK" else 0.6, color=color,
                            mfc=color if cond == "KK" else "white",
                            label=(f"{label}, {'single views (KK)' if cond == 'KK' else 'full graphs (FF)'}" if first else None))
    ax.axvline(0, color=MUTE, lw=0.6, ls="--")
    ax.set_xlabel(xlab, fontsize=7)
    ax.tick_params(axis="x", labelsize=6)
axes[0].set_yticks(range(3))
axes[0].set_yticklabels([f"K={k}\n(n={el[str(k)]['total_eligible']})" for k in (250, 500, 1000)], fontsize=6.5)
axes[0].set_ylim(2.5, -0.5)
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=2, frameon=False, fontsize=5.8,
           handletextpad=0.3, columnspacing=0.8)
fig.tight_layout(w_pad=0.6)
save(fig, "fig3_dispersion_contrasts")
print("figures ->", OUT)
