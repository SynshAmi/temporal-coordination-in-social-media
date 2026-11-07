"""
s02_study1_robustness.py — Study 1 robustness phase: split stability, flexible count baselines,
content-feature contribution, missing-text handling, grouped folds. Engine: s00_engine.py
(validated to reproduce every stored primary-split prediction of M0-M4, both objectives).

All analyses here are post-hoc robustness checks of the paper's pre-specified contrast C1 (M4 vs M0q);
none is confirmatory. The seven contrasts in HOLM_FAMILY are Holm-adjusted together (log loss);
everything else is exploratory and unadjusted.

Repeats: 20 outer 5-fold splits (seeds 42, 1-9 = the paper's 10 split seeds; 10-19 added).
Outputs (research_audit/outputs/): s02_results.json, s02_contrasts.csv, s02_performance.csv,
s02_per_repeat.csv, s02_content_correlations.csv, s02_oof.npz, s02_fig*.png (+ _data.csv), s02.log
"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import spearmanr
from sklearn.model_selection import StratifiedGroupKFold

from s00_engine import (ARRANGE, CONTENT, DEGREE, LEVELS, OUT, QUAD, ROOT, SCALE, SEEDS, auc_rows, ba_rows, contrast,
                        fold_maps, holm, load, loss, oof)

sys.stdout.reconfigure(encoding="utf-8")
F, man = load()
y = F.label.to_numpy().astype(int)
NONCOUNT = DEGREE + ARRANGE + CONTENT
SHORT = {"exact_dup_proportion": "dup", "text_concentration": "conc", "msg_length_dispersion": "lensd"}

# name -> (columns, count basis, objectives)
M = {lv: (cols, "lr", ("ll", "ba")) for lv, cols in LEVELS.items()}
M |= {"S (spline counts)": (SCALE, "spline", ("ll", "ba")), "P3 (cubic counts)": (SCALE, "poly3", ("ll", "ba")),
      "QDA (counts)": (SCALE, "qda", ("ll",)), "M4S (spline counts + all)": (SCALE + NONCOUNT, "spline", ("ll", "ba"))}
for c in CONTENT:
    M[f"M0q+{SHORT[c]}"] = (LEVELS["M0q"] + [c], "lr", ("ll",))
    M[f"M2+{SHORT[c]}"] = (LEVELS["M2"] + [c], "lr", ("ll",))
M["M3+degree"] = (LEVELS["M3"] + DEGREE, "lr", ("ll",))
M["M3+arrangement"] = (LEVELS["M3"] + ARRANGE, "lr", ("ll",))
for c in NONCOUNT:
    M[f"M4-{c}"] = ([x for x in LEVELS["M4"] if x != c], "lr", ("ll",))
for lv in ("M0q", "M2", "M3", "M4"):
    M[f"{lv}+textshare"] = (LEVELS[lv] + ["usable_text_share"], "lr", ("ll",))
M["M4+notext"] = (LEVELS["M4"] + ["no_text"], "lr", ("ll",))

FM = fold_maps(man)
# grouped folds: the two repeated campaign hashtags kept in one fold (StratifiedGroupKFold, same 20 seeds)
tag = pd.Series(F.index, index=F.index).str.replace(r"_(non)?campaign_fulldata$", "", regex=True).str.split("___").str[0].str.lower().str.replace("ı", "i")
GM = {}
for s in SEEDS:
    g = np.zeros(len(F), int)
    for k, (_, te) in enumerate(StratifiedGroupKFold(5, shuffle=True, random_state=s).split(F, y, groups=tag.values)):
        g[te] = k
    GM[s] = dict(zip(F.index, g))
TEXT = F.index[F.no_text == 0]  # 101 events with usable text

jobs = [(n, o, s, "all") for n, (_, _, objs) in M.items() for o in objs for s in SEEDS]
jobs += [(lv, o, s, "text101") for lv in ("M0q", "M2", "M3", "M4") for o in ("ll", "ba") for s in SEEDS]
jobs += [(lv, o, s, "grouped") for lv in ("M0q", "M4") for o in ("ll", "ba") for s in SEEDS]


def run(n, o, s, sub):
    cols, kind, _ = M[n]
    if sub == "text101":
        return oof(F.loc[TEXT], cols, kind, FM[s], o)
    return oof(F, cols, kind, (GM if sub == "grouped" else FM)[s], o)


print(f"{len(jobs)} cross-validation runs", flush=True)
res = Parallel(n_jobs=-1)(delayed(run)(*j) for j in jobs)
P = {}
for (n, o, s, sub), p in zip(jobs, res):
    P.setdefault((n, o, sub), []).append(p)
P = {k: np.vstack(v) for k, v in P.items()}  # repeats x events, rows in SEEDS order
np.savez_compressed(OUT / "s02_oof.npz", **{f"{n}|{o}|{sub}": v for (n, o, sub), v in P.items()},
                    event_id=np.array(F.index), label=y, seeds=np.array(SEEDS))

# ---- check: seeds 42, 1-9 reproduce the paper's stored repeated-split values
rep = pd.read_csv(ROOT / "outputs/run_v2/study1/repeated_splits_lr.csv").set_index("split_seed")
chk = {}
for lv in LEVELS:
    ll = loss(y, P[(lv, "ll", "all")][:10]).mean(1)
    ba = ba_rows(y, P[(lv, "ba", "all")][:10])
    chk[lv] = {"max_abs_diff_ll": float(np.abs(ll - rep.loc[SEEDS[:10], f"ll_{lv}"].values).max()),
               "max_abs_diff_ba": float(np.abs(ba - rep.loc[SEEDS[:10], f"ba_{lv}"].values).max())}
print("reproduction of stored repeated splits:", json.dumps(chk), flush=True)


def get(n, sub="all", o="ll"):
    if o == "ba" and M[n][1] == "qda":
        o = "ll"  # QDA is not tuned: one fit serves both estimands
    return P.get((n, o, sub))


def C(a, b, sub="all"):
    yy = y if sub != "text101" else F.loc[TEXT].label.to_numpy().astype(int)
    ba_a, ba_b = get(a, sub, "ba"), get(b, sub, "ba")
    if ba_a is None or ba_b is None:
        ba_a = ba_b = None
    return contrast(yy, get(a, sub), get(b, sub), ba_a, ba_b)


# ---- performance table (mean over 20 repeats)
perf = []
for (n, o, sub), Pm in P.items():
    if o != "ll":
        continue
    yy = y if sub != "text101" else F.loc[TEXT].label.to_numpy().astype(int)
    row = {"model": n, "subset": sub, "LL": float(loss(yy, Pm).mean()), "LL_repeat_sd": float(loss(yy, Pm).mean(1).std(ddof=1)),
           "AUC": float(auc_rows(yy, Pm).mean()), "AUC_repeat_sd": float(auc_rows(yy, Pm).std(ddof=1))}
    if get(n, sub, "ba") is not None:
        b = ba_rows(yy, get(n, sub, "ba"))
        row |= {"BA": float(b.mean()), "BA_repeat_sd": float(b.std(ddof=1)), "BA_min": float(b.min()), "BA_max": float(b.max())}
    perf.append(row)
perf = pd.DataFrame(perf)
perf.to_csv(OUT / "s02_performance.csv", index=False)
print(perf[perf.subset == "all"].round(3).to_string(index=False), flush=True)

# ---- contrasts
HOLM_FAMILY = {"C1: M4 - M0q": ("M4", "M0q"), "M4 - S (spline counts)": ("M4", "S (spline counts)"),
               "M4 - P3 (cubic counts)": ("M4", "P3 (cubic counts)"), "M4 - QDA (counts)": ("M4", "QDA (counts)"),
               "M4S - S (all beyond spline counts)": ("M4S (spline counts + all)", "S (spline counts)"),
               "C3: M3 - M0q (content beyond counts)": ("M3", "M0q"), "E3: M4 - M2 (content beyond counts+structure)": ("M4", "M2")}
EXPL = {"E1: M1 - M0q (degree Gini)": ("M1", "M0q"), "C2: M2 - M1 (arrangement)": ("M2", "M1"),
        "M2 - M0q (structure beyond counts)": ("M2", "M0q"), "E2: M4 - M3 (structure beyond counts+content)": ("M4", "M3"),
        "E4: M0q - M0": ("M0q", "M0"), "S - M0q": ("S (spline counts)", "M0q"), "P3 - M0q": ("P3 (cubic counts)", "M0q"),
        "QDA - M0q": ("QDA (counts)", "M0q"), "M3+degree - M3": ("M3+degree", "M3"), "M3+arrangement - M3": ("M3+arrangement", "M3"),
        "M4 - M3+degree (arrangement given content+degree)": ("M4", "M3+degree"),
        "M4 - M3+arrangement (degree given content+arrangement)": ("M4", "M3+arrangement")}
for c in CONTENT:
    EXPL[f"M0q+{SHORT[c]} - M0q"] = (f"M0q+{SHORT[c]}", "M0q")
    EXPL[f"M2+{SHORT[c]} - M2"] = (f"M2+{SHORT[c]}", "M2")
for c in NONCOUNT:
    EXPL[f"M4 - (M4 without {c})"] = ("M4", f"M4-{c}")
EXPL |= {"M0q+textshare - M0q": ("M0q+textshare", "M0q"), "M4+textshare - M4": ("M4+textshare", "M4"),
         "M3+textshare - M0q+textshare (content beyond counts+text share)": ("M3+textshare", "M0q+textshare"),
         "M4+textshare - M2+textshare (content beyond counts+structure+text share)": ("M4+textshare", "M2+textshare"),
         "M4+notext - M4 (missing-text indicator)": ("M4+notext", "M4")}
rows = []
for fam, D in (("holm", HOLM_FAMILY), ("exploratory", EXPL)):
    for name, (a, b) in D.items():
        rows.append({"family": fam, "subset": "all", "contrast": name, "A": a, "B": b, **C(a, b)})
for name, (a, b) in {"C1: M4 - M0q": ("M4", "M0q"), "C3: M3 - M0q": ("M3", "M0q"), "E3: M4 - M2": ("M4", "M2")}.items():
    rows.append({"family": "missing-text sensitivity (101 events)", "subset": "text101", "contrast": name, "A": a, "B": b, **C(a, b, "text101")})
rows.append({"family": "grouped folds (repeated hashtags together)", "subset": "grouped", "contrast": "C1: M4 - M0q", "A": "M4", "B": "M0q",
             **C("M4", "M0q", "grouped")})
H = holm({r["contrast"]: r["p_LL"] for r in rows if r["family"] == "holm"})
for r in rows:
    r["p_LL_holm"] = H.get(r["contrast"]) if r["family"] == "holm" else None
CT = pd.DataFrame(rows)
flat = CT.copy()
for c in ("dLL_ci", "dAUC_ci", "dBA_ci"):
    flat[c] = flat[c].map(lambda v: f"[{v[0]:+.3f}, {v[1]:+.3f}]" if isinstance(v, list) else "")
flat.to_csv(OUT / "s02_contrasts.csv", index=False)
for r in rows:
    ba = f" | dBA {r['dBA']:+.3f} [{r['dBA_ci'][0]:+.3f}, {r['dBA_ci'][1]:+.3f}]" if "dBA" in r else ""
    hp = f" holm {r['p_LL_holm']:.3f}" if r["p_LL_holm"] is not None else ""
    print(f"[{r['family'][:12]}] {r['contrast'][:62]:62s} dLL {r['dLL']:+.3f} [{r['dLL_ci'][0]:+.3f}, {r['dLL_ci'][1]:+.3f}] p {r['p_LL']:.3f}{hp} "
          f"| dAUC {r['dAUC']:+.3f} [{r['dAUC_ci'][0]:+.3f}, {r['dAUC_ci'][1]:+.3f}]{ba} | rep+ LL {r['repeats_favouring_A_LL']}/{r['n_repeats']}", flush=True)

# ---- primary split (seed 42) C1, single-split event bootstrap exactly as the paper
p0 = contrast(y, get("M4")[:1], get("M0q")[:1], get("M4", o="ba")[:1], get("M0q", o="ba")[:1])

# ---- split stability: per-repeat and per-fold family contrasts
FAMILY = {"C1 all vs counts": ("M4", "M0q"), "degree | counts": ("M1", "M0q"), "arrangement | counts+degree": ("M2", "M1"),
          "structure | counts": ("M2", "M0q"), "content | counts": ("M3", "M0q"), "content | counts+structure": ("M4", "M2"),
          "structure | counts+content": ("M4", "M3"), "all | spline counts": ("M4S (spline counts + all)", "S (spline counts)")}
pr = []
for fam, (a, b) in FAMILY.items():
    LA, LB = loss(y, get(a)), loss(y, get(b))
    dA = auc_rows(y, get(a)) - auc_rows(y, get(b))
    dB = ba_rows(y, get(a, o="ba")) - ba_rows(y, get(b, o="ba"))
    for r, s in enumerate(SEEDS):
        f = np.array([FM[s][e] for e in F.index])
        fold_d = [float((LA[r, f == k] - LB[r, f == k]).mean()) for k in range(5)]
        pr.append({"family": fam, "seed": s, "dLL": float((LA[r] - LB[r]).mean()), "dAUC": float(dA[r]), "dBA": float(dB[r]),
                   "folds_favouring_A_LL": int(sum(d < 0 for d in fold_d)), "fold_dLL_min": min(fold_d), "fold_dLL_max": max(fold_d)})
PR = pd.DataFrame(pr)
PR.to_csv(OUT / "s02_per_repeat.csv", index=False)
stab = PR.groupby("family", sort=False).agg(dLL_mean=("dLL", "mean"), dLL_sd=("dLL", "std"), dLL_min=("dLL", "min"), dLL_max=("dLL", "max"),
                                            reps_LL_better=("dLL", lambda d: int((d < 0).sum())), dAUC_mean=("dAUC", "mean"),
                                            dAUC_min=("dAUC", "min"), dAUC_max=("dAUC", "max"), reps_AUC_better=("dAUC", lambda d: int((d > 0).sum())),
                                            dBA_mean=("dBA", "mean"), dBA_min=("dBA", "min"), dBA_max=("dBA", "max"),
                                            reps_BA_better=("dBA", lambda d: int((d > 0).sum())), reps_BA_worse=("dBA", lambda d: int((d < 0).sum())),
                                            folds_LL_better=("folds_favouring_A_LL", "sum"))
print(stab.round(3).to_string(), flush=True)

# ---- content features: distinctness
cc = F[SCALE + CONTENT + ["usable_text_share"]].dropna()
rho = cc.corr(method="spearman")
# partial Spearman given the M0q count terms (rank-residualised)
R = cc.rank()
Z = np.column_stack([np.ones(len(R)), F.loc[cc.index, SCALE + QUAD].to_numpy()])
resid = R - Z @ np.linalg.lstsq(Z, R.to_numpy(), rcond=None)[0]
prho = pd.DataFrame(np.corrcoef(resid[CONTENT + ["usable_text_share"]].to_numpy().T), index=CONTENT + ["usable_text_share"], columns=CONTENT + ["usable_text_share"])
by_class = {str(k): g[CONTENT].corr(method="spearman").round(3).to_dict() for k, g in F.loc[cc.index].groupby("label")}
uni = {c: {"AUC_campaign": float(auc_rows(F.loc[cc.index].label.to_numpy().astype(int), cc[c].to_numpy()[None])[0]),
           "rho_with_text_share": float(spearmanr(cc[c], cc.usable_text_share)[0])} for c in CONTENT + ["usable_text_share"]}
pd.concat({"spearman": rho, "partial_spearman_given_counts": prho}).to_csv(OUT / "s02_content_correlations.csv")
print("content Spearman:\n", rho.round(2).to_string(), "\npartial given counts:\n", prho.round(2).to_string(), "\nunivariate:", json.dumps(uni, indent=0), flush=True)

# ---- figures (colours: validated default categorical slots 1-2)
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#222222", "#8a8a85"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUTED})

# Fig 1: split stability of C1
c1 = PR[PR.family == "C1 all vs counts"]
fig, ax = plt.subplots(1, 3, figsize=(9, 3.1))
c1r = CT[(CT.contrast == "C1: M4 - M0q") & (CT.subset == "all")].iloc[0]
for a, (col, lab, ci_key, better) in zip(ax, (("dLL", "Δ log loss (M4 − M0q)", "dLL_ci", "lower is better"),
                                             ("dAUC", "Δ AUC (M4 − M0q)", "dAUC_ci", "higher is better"),
                                             ("dBA", "Δ balanced accuracy (M4 − M0q)", "dBA_ci", "higher is better"))):
    jit = np.random.default_rng(0).uniform(-0.12, 0.12, len(c1))
    a.scatter(jit, c1[col], s=22, color=BLUE, edgecolor="white", linewidth=0.8, zorder=3, label="one 5-fold split")
    a.errorbar([0.45], [c1r[col]], yerr=[[c1r[col] - c1r[ci_key][0]], [c1r[ci_key][1] - c1r[col]]], fmt="o", color=INK, ms=6, capsize=3,
               label="repeat-averaged, 95% event bootstrap")
    a.axhline(0, color=MUTED, lw=0.8)
    a.set_xlim(-0.4, 0.8)
    a.set_xticks([])
    a.set_ylabel(lab)
    a.set_title(better, fontsize=8, color=MUTED)
ax[0].legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.02))
fig.suptitle("C1 across 20 outer splits: split-to-split spread vs event-level uncertainty", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "s02_fig1_split_stability.png", dpi=200)
c1.to_csv(OUT / "s02_fig1_data.csv", index=False)

# Fig 2: forest plot of log-loss contrasts
show = ["C1: M4 - M0q", "M4 - S (spline counts)", "M4 - P3 (cubic counts)", "M4 - QDA (counts)", "M4S - S (all beyond spline counts)",
        "C3: M3 - M0q (content beyond counts)", "M2 - M0q (structure beyond counts)", "E3: M4 - M2 (content beyond counts+structure)",
        "E2: M4 - M3 (structure beyond counts+content)",
        "M4+textshare - M2+textshare (content beyond counts+structure+text share)"]
fd = CT[(CT.subset == "all") & CT.contrast.isin(show)].set_index("contrast").loc[show]
extra = CT[CT.subset != "all"].copy()
extra["contrast"] = extra.contrast + "  [" + extra.subset + "]"
fd = pd.concat([fd.reset_index(), extra[["contrast", "dLL", "dLL_ci"]]], ignore_index=True)
fig, ax = plt.subplots(figsize=(7.6, 4.8))
yy_ = np.arange(len(fd))[::-1]
for yv, (_, r) in zip(yy_, fd.iterrows()):
    excl = r.dLL_ci[1] < 0 or r.dLL_ci[0] > 0
    ax.plot(r.dLL_ci, [yv, yv], color=INK if excl else MUTED, lw=1.6, solid_capstyle="round")
    ax.plot(r.dLL, yv, "o", color=ORANGE if excl else "white", mec=INK if excl else MUTED, ms=6)
ax.axvline(0, color=MUTED, lw=0.8)
ax.set_yticks(yy_)
ax.set_yticklabels(fd.contrast, fontsize=7)
ax.set_xlabel("Δ log loss, A − B (20 splits; 95% event bootstrap)")
ax.set_title("Log-loss contrasts (filled: interval excludes 0)", fontsize=10, loc="left")
fig.tight_layout()
fig.savefig(OUT / "s02_fig2_contrasts.png", dpi=200)
fd.assign(lo=fd.dLL_ci.str[0], hi=fd.dLL_ci.str[1]).drop(columns="dLL_ci").to_csv(OUT / "s02_fig2_data.csv", index=False)

# Fig 3: text availability and content features by class
fig, ax = plt.subplots(1, 3, figsize=(9, 3.1))
for a, c in zip(ax, CONTENT):
    for lab, col, nm in ((0, BLUE, "comparison"), (1, ORANGE, "campaign")):
        g = F[(F.label == lab) & F[c].notna()]
        a.scatter(g.usable_text_share, g[c], s=16, color=col, edgecolor="white", linewidth=0.6, label=nm)
    a.set_xlabel("share of edges with usable text")
    a.set_ylabel(c)
ax[0].legend(fontsize=7, frameon=False)
fig.suptitle("Content features vs text availability (2 campaign events with no text omitted)", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "s02_fig3_text_availability.png", dpi=200)
F[["label", "usable_text_share"] + CONTENT].to_csv(OUT / "s02_fig3_data.csv")


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


out = {"seeds": SEEDS, "reproduction_check_vs_stored_repeated_splits": chk, "primary_split_C1": p0,
       "contrasts": CT.to_dict("records"), "split_stability": stab.reset_index().to_dict("records"),
       "content": {"spearman": rho.round(4).to_dict(), "partial_spearman_given_counts": prho.round(4).to_dict(),
                   "spearman_by_class": by_class, "univariate": uni},
       "text101_events": int(len(TEXT)), "holm_family": list(HOLM_FAMILY)}
(OUT / "s02_results.json").write_text(json.dumps(clean(out), indent=2, ensure_ascii=False), encoding="utf-8")
print("primary split C1:", json.dumps(clean(p0)))
