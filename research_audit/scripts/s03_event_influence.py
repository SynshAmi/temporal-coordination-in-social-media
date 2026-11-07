"""
s03_event_influence.py — event influence on C1 (M4 vs M0q), Study 1 robustness phase.

1. Fixed-prediction decomposition (from s02_oof.npz, 20 repeats): each event's repeat-averaged log-loss
   difference d_i (C1 dLL = mean d_i), its share of the total, and delete-one (jackknife) values of
   dLL, dAUC and dBA without refitting.
2. Refit leave-one-event-out: every event is removed in turn and M4 and M0q are refitted on the
   remaining 102 events (paper's 10 split seeds, both tuning objectives; each remaining event keeps
   its fold). Shows how much each event affects the *other* events' predictions through training.
3. Diagnostic exclusion sets, refitted with all 20 seeds. Sets are chosen from the same data (most
   favourable / unfavourable events), so they are stress tests, not corrected estimates.
Outputs: research_audit/outputs/s03_*.csv/json/png, s03.log
"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from s00_engine import LEVELS, OUT, SEEDS, auc_rows, ba_rows, contrast, fold_maps, load, loss, oof

sys.stdout.reconfigure(encoding="utf-8")
F, man = load()
y = F.label.to_numpy().astype(int)
Z = np.load(OUT / "s02_oof.npz", allow_pickle=True)
assert (Z["event_id"] == F.index.to_numpy()).all()
P4, P0 = Z["M4|ll|all"], Z["M0q|ll|all"]
B4, B0 = Z["M4|ba|all"], Z["M0q|ba|all"]
FM = fold_maps(man)
n = len(y)

# ---- 1. decomposition and jackknife on fixed predictions
L4, L0 = loss(y, P4), loss(y, P0)
d = (L4 - L0).mean(0)
ev = pd.DataFrame({"label": y, "p_M0q": P0.mean(0), "p_M4": P4.mean(0), "loss_M0q": L0.mean(0), "loss_M4": L4.mean(0), "d_LL": d,
                   "share_of_total": d / d.sum(), "usable_text_share": F.usable_text_share.values}, index=F.index)
auc_full = (auc_rows(y, P4) - auc_rows(y, P0)).mean()
ba_full = (ba_rows(y, B4) - ba_rows(y, B0)).mean()
jk = []
for i in range(n):
    k = np.arange(n) != i
    jk.append({"jk_dLL": float(d[k].mean()), "jk_dAUC": float((auc_rows(y[k], P4[:, k]) - auc_rows(y[k], P0[:, k])).mean()),
               "jk_dBA": float((ba_rows(y[k], B4[:, k]) - ba_rows(y[k], B0[:, k])).mean())})
ev = ev.join(pd.DataFrame(jk, index=F.index))
ev["infl_dLL"], ev["infl_dAUC"], ev["infl_dBA"] = ev.jk_dLL - d.mean(), ev.jk_dAUC - auc_full, ev.jk_dBA - ba_full
srt = np.sort(d)
conc = {"dLL": float(d.mean()), "events_improved": int((d < 0).sum()), "events_worse": int((d > 0).sum()),
        "share_from_top5_favouring_M4": float(srt[:5].sum() / d.sum()), "share_from_top10_favouring_M4": float(srt[:10].sum() / d.sum()),
        "share_from_top5_favouring_M0q": float(srt[-5:].sum() / d.sum()),
        "median_d": float(np.median(d)), "trimmed_mean_d_5pct": float(np.sort(d)[5:-5].mean()),
        "dLL_jackknife_range": [float(ev.jk_dLL.min()), float(ev.jk_dLL.max())],
        "dAUC_jackknife_range": [float(ev.jk_dAUC.min()), float(ev.jk_dAUC.max())],
        "dBA_jackknife_range": [float(ev.jk_dBA.min()), float(ev.jk_dBA.max())]}
# which repeat reversed, and why
rep_d = (L4 - L0).mean(1)
worst = int(np.argmax(rep_d))
ctrib = pd.Series((L4[worst] - L0[worst]) / n, index=F.index).sort_values(ascending=False)
reversal = {"seed": SEEDS[worst], "dLL": float(rep_d[worst]), "top_contributors": {k: float(v) for k, v in ctrib.head(5).items()},
            "dLL_without_top1": float(np.delete(L4[worst] - L0[worst], F.index.get_loc(ctrib.index[0])).mean())}
print("concentration:", json.dumps(conc, indent=0), "\nreversal:", json.dumps(reversal, ensure_ascii=False, indent=0), flush=True)

# ---- 2. refit leave-one-event-out (10 paper seeds, both objectives)
S10 = SEEDS[:10]


def loeo(i, lv, o, s):
    return oof(F.drop(F.index[i]), LEVELS[lv], "lr", FM[s], o)


jobs = [(i, lv, o, s) for i in range(n) for lv in ("M4", "M0q") for o in ("ll", "ba") for s in S10]
print(f"refit LOEO: {len(jobs)} runs", flush=True)
res = Parallel(n_jobs=-1)(delayed(loeo)(*j) for j in jobs)
R = {}
for (i, lv, o, s), p in zip(jobs, res):
    R.setdefault((i, lv, o), []).append(p)
lo = []
for i in range(n):
    k = np.arange(n) != i
    yy = y[k]
    a4, a0 = np.vstack(R[(i, "M4", "ll")]), np.vstack(R[(i, "M0q", "ll")])
    b4, b0 = np.vstack(R[(i, "M4", "ba")]), np.vstack(R[(i, "M0q", "ba")])
    lo.append({"refit_dLL": float((loss(yy, a4) - loss(yy, a0)).mean()), "refit_dAUC": float((auc_rows(yy, a4) - auc_rows(yy, a0)).mean()),
               "refit_dBA": float((ba_rows(yy, b4) - ba_rows(yy, b0)).mean()),
               # same 102 events, fixed (non-refit) predictions from the same 10 seeds, for a like-for-like comparison
               "fixed10_dLL": float((loss(yy, P4[:10, k]) - loss(yy, P0[:10, k])).mean())})
ev = ev.join(pd.DataFrame(lo, index=F.index))
ev["training_effect_dLL"] = ev.refit_dLL - ev.fixed10_dLL
full10 = float((L4[:10] - L0[:10]).mean())
loeo_sum = {"dLL_full_10seeds": full10, "refit_dLL_range": [float(ev.refit_dLL.min()), float(ev.refit_dLL.max())],
            "refit_dAUC_range": [float(ev.refit_dAUC.min()), float(ev.refit_dAUC.max())],
            "refit_dBA_range": [float(ev.refit_dBA.min()), float(ev.refit_dBA.max())],
            "events_whose_removal_makes_dLL_nonnegative": ev.index[ev.refit_dLL >= 0].tolist(),
            "events_whose_removal_makes_dAUC_nonpositive": ev.index[ev.refit_dAUC <= 0].tolist(),
            "largest_training_effects": ev.training_effect_dLL.abs().sort_values(ascending=False).head(5).index.tolist()}
print("refit LOEO:", json.dumps(loeo_sum, ensure_ascii=False, indent=0), flush=True)

# ---- 3. diagnostic exclusion sets (20 seeds, refit)
order = ev.d_LL.sort_values().index  # most favourable to M4 first
ozur = [e for e in F.index if e.startswith("Özür_Dilerim")]
sets = {"none": [], "Özür_Dilerim only": ozur,
        "top 1 favouring M4": list(order[:1]), "top 3 favouring M4": list(order[:3]), "top 5 favouring M4": list(order[:5]),
        "top 10 favouring M4": list(order[:10]), "top 5 favouring M0q": list(order[-5:]),
        "symmetric trim (5 + 5)": list(order[:5]) + list(order[-5:]),
        "5 highest M4 losses": list(ev.loss_M4.sort_values(ascending=False).index[:5]),
        "5 highest M0q losses": list(ev.loss_M0q.sort_values(ascending=False).index[:5]),
        "11 campaign events with < 20% usable text": list(F.index[F.usable_text_share < 0.2])}


def excl(name, lv, o, s):
    return oof(F.drop(sets[name]), LEVELS[lv], "lr", FM[s], o)


jobs = [(nm, lv, o, s) for nm in sets for lv in ("M4", "M0q") for o in ("ll", "ba") for s in SEEDS]
res = Parallel(n_jobs=-1)(delayed(excl)(*j) for j in jobs)
E = {}
for (nm, lv, o, s), p in zip(jobs, res):
    E.setdefault((nm, lv, o), []).append(p)
ex = []
for nm, drop in sets.items():
    yy = F.drop(drop).label.to_numpy().astype(int)
    c = contrast(yy, np.vstack(E[(nm, "M4", "ll")]), np.vstack(E[(nm, "M0q", "ll")]), np.vstack(E[(nm, "M4", "ba")]), np.vstack(E[(nm, "M0q", "ba")]))
    ex.append({"set": nm, "n_removed": len(drop), "removed": drop, **c})
    print(f"{nm:45s} n={len(yy)} dLL {c['dLL']:+.3f} [{c['dLL_ci'][0]:+.3f}, {c['dLL_ci'][1]:+.3f}] | dAUC {c['dAUC']:+.3f} "
          f"[{c['dAUC_ci'][0]:+.3f}, {c['dAUC_ci'][1]:+.3f}] | dBA {c['dBA']:+.3f} [{c['dBA_ci'][0]:+.3f}, {c['dBA_ci'][1]:+.3f}] | reps LL {c['repeats_favouring_A_LL']}/20", flush=True)
EX = pd.DataFrame(ex)

ev.to_csv(OUT / "s03_event_influence.csv")
flat = EX.copy()
for c in ("dLL_ci", "dAUC_ci", "dBA_ci"):
    flat[c] = flat[c].map(lambda v: f"[{v[0]:+.3f}, {v[1]:+.3f}]")
flat["removed"] = flat.removed.map(lambda v: "; ".join(v))
flat.to_csv(OUT / "s03_exclusions.csv", index=False)
top = ev.reindex(ev.d_LL.abs().sort_values(ascending=False).index).head(12)
print(top[["label", "p_M0q", "p_M4", "loss_M0q", "loss_M4", "d_LL", "share_of_total", "refit_dLL", "refit_dAUC", "refit_dBA", "usable_text_share"]]
      .rename(index=lambda s: s[:40]).round(3).to_string(), flush=True)

# ---- figure
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#222222", "#8a8a85"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUTED})
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.6, 1]})
s = ev.sort_values("d_LL")
ax[0].bar(np.arange(n), s.d_LL, color=[ORANGE if v == 1 else BLUE for v in s.label], width=0.8)
ax[0].axhline(0, color=MUTED, lw=0.8)
for j, (e, r) in enumerate(s.iterrows()):
    if j < 4 or j >= n - 2:
        ax[0].annotate(e.split("___")[0].replace("_noncampaign_fulldata", "")[:18], (j, r.d_LL), fontsize=6.5, ha="left" if j < 4 else "right",
                       xytext=(4 if j < 4 else -4, 0), textcoords="offset points", color=INK)
ax[0].set_xticks([])
ax[0].set_xlabel("events, ordered by contribution (orange campaign, blue comparison)")
ax[0].set_ylabel("per-event Δ log loss, M4 − M0q\n(mean over 20 splits; negative favours M4)")
ax[0].set_title(f"C1 = mean of these bars = {d.mean():+.3f}; {int((d < 0).sum())}/{n} events favour M4", fontsize=9)
ex_plot = EX.iloc[::-1]
yy_ = np.arange(len(ex_plot))
for yv, (_, r) in zip(yy_, ex_plot.iterrows()):
    excl_ = r.dLL_ci[1] < 0
    ax[1].plot(r.dLL_ci, [yv, yv], color=INK if excl_ else MUTED, lw=1.6)
    ax[1].plot(r.dLL, yv, "o", color=ORANGE if excl_ else "white", mec=INK if excl_ else MUTED, ms=6)
ax[1].axvline(0, color=MUTED, lw=0.8)
ax[1].set_yticks(yy_)
ax[1].set_yticklabels(ex_plot.set, fontsize=7)
ax[1].set_xlabel("C1 Δ log loss after removal\n(refit, 20 splits, 95% event bootstrap)")
ax[1].set_title("Diagnostic exclusions (data-chosen sets)", fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "s03_fig_event_influence.png", dpi=200)
s[["label", "d_LL"]].to_csv(OUT / "s03_fig_data.csv")


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


out = {"concentration": conc, "reversal_repeat": reversal, "refit_loeo": loeo_sum, "exclusions": EX.to_dict("records"),
       "ozur_dilerim": ev.loc[ozur].reset_index().to_dict("records")}
(OUT / "s03_results.json").write_text(json.dumps(clean(out), indent=2, ensure_ascii=False), encoding="utf-8")
