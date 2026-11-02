"""
make_paper_figures.py
---------------------
Single-column (3.5 in) figures for the research paper, built only from the
corrected run's verified outputs (outputs/run_v2/paper_results.json) and the
canonical manifest. No metric is typed in by hand.

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

# Fig. 2 - Study 1 confirmatory paired contrasts (LR), one panel per estimand
conf = R["study1"]["confirmatory"]["logreg"]
names = {"C1": "C1: all features\nvs counts", "C2": "C2: arrangement\nvs degree", "C3": "C3: content\nvs counts"}
panels = [("BA\n(BA-tuned)", "ba", "delta_ba", "delta_ba_ci"),
          ("Log loss\n(log-loss-tuned)", "log_loss", "delta_logloss", "delta_logloss_ci"),
          ("AUC\n(log-loss-tuned)", "auc_ll_fit", "delta_auc", "delta_auc_ci")]
fig, axes = plt.subplots(1, 3, figsize=(W, 1.85), sharey=True)
for ax, (title, block, key, cikey) in zip(axes, panels):
    for i, c in enumerate(["C1", "C2", "C3"]):
        d = conf[c][block]
        v, (lo, hi) = d[key], d[cikey]
        sig = lo > 0 or hi < 0
        ax.errorbar(v, i, xerr=[[v - lo], [hi - v]], fmt="o", ms=3.2, capsize=1.8, lw=0.9,
                    color=(CAMP if sig else INK), mfc=(CAMP if sig else "white"))
    ax.axvline(0, color=MUTE, lw=0.6, ls="--")
    ax.set_title(title, fontsize=6.8)
    ax.tick_params(axis="x", labelsize=6)
axes[0].set_yticks(range(3))
axes[0].set_yticklabels([names[c] for c in ["C1", "C2", "C3"]], fontsize=6.5)
axes[0].invert_yaxis()
for ax, lab in zip(axes, ["Δ BA", "Δ log loss", "Δ AUC"]):
    ax.set_xlabel(lab, fontsize=7)
fig.tight_layout(w_pad=0.4)
save(fig, "fig2_study1_contrasts")

# Fig. 3 - Study 2 single-view BA by budget on the COMMON cohort (the events eligible at every
# budget), so that every line compares the same events. Full-graph (FF) values do not depend on K.
ks = [250, 500, 1000]
series = [("FF|combined", "Full graph → full graph (all features)", MUTE, "-.", "x"),
          ("FF|struct6", "Full graph → full graph (6 structural)", MUTE, ":", "s"),
          ("FK|struct6", "Full graph → single view (frozen, 6 structural)", COMP, "--", "s"),
          ("KK|struct6", "View-trained (6 structural)", ACC, "-", "^"),
          ("KK|NK", "View-trained (sampled node count only)", INK, "-", "o"),
          ("KK|combined", "View-trained (node count + structure + content)", CAMP, "-", "D")]
fig, ax = plt.subplots(figsize=(W, 2.75))
x = np.arange(3)
for key, label, color, ls, mk in series:
    rr = [R["study2"]["results"][f"common_K{k}"]["conditions"][key] for k in ks]
    m = np.array([r["single_view_ba_mean"] for r in rr])
    lo = np.array([r["single_view_ba_min"] for r in rr])
    hi = np.array([r["single_view_ba_max"] for r in rr])
    # full-graph rows have no sampling, so their seed range is zero (clip rounding noise)
    ax.errorbar(x, m, yerr=[np.maximum(m - lo, 0), np.maximum(hi - m, 0)], color=color, ls=ls, marker=mk, ms=3.2, lw=1.0,
                capsize=1.8, label=label)
ax.axhline(0.5, color=CAMP, ls="--", lw=0.4)
ax.set_xticks(x)
el = R["eligibility"]["1000"]   # the common cohort is the set eligible at the largest budget
ax.set_xticklabels([f"K={k}" for k in ks])
ax.set_xlabel(f"Edge budget (common cohort: n={el['total_eligible']}; {el['campaign_eligible']}/{el['comparison_eligible']})")
ax.set_ylabel("Single-view balanced accuracy")
ax.set_ylim(0.5, 1.0)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=1, frameon=False)
fig.tight_layout()
save(fig, "fig3_study2_single_view")

# Fig. 4 - endpoint mechanism at K=250: expected sampled endpoints vs full-graph node count
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
save(fig, "fig4_endpoint_mechanism")
print("figures ->", OUT)
