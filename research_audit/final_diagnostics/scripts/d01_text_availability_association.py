"""
d01_text_availability_association.py — Check 1: how strongly is message-length dispersion (token_std,
stored as msg_length_dispersion) associated with text availability in the Study 2 K-edge views?

Input (read only): research_audit/outputs/v01_view_text.csv, one row per view, written by
research_audit/scripts/v01_view_text_availability.py, which regenerated every view with the original sampler
and verified N_K and token_std against data/processed/sampled_views_v2.parquet (max |diff| 0.0).
  m_K   = n_usable_text: number of the K sampled edges whose text is non-null and non-empty after cleaning
          (lower-case, URLs removed, whitespace collapsed, stripped); exactly the texts token_std is computed on.
  m_K/K = usable_share. Within one K it is a fixed rescaling of m_K, so every rank or linear correlation
          with it is identical to that with m_K; it is used only where K is pooled (not done here).
  token_std = lensd_stored (the stored feature). Views with undefined token_std (m_K = 0) are excluded here.

Units: the 10 views of an event are not independent, so three levels are reported, each by K and by class:
  (a) per-seed view level: for each sampling seed one view per event (independent units); Spearman and
      Pearson computed per seed, then averaged over the 10 seeds;
  (b) between-event level: event means of m_K and token_std over its 10 views; Spearman and Pearson, with
      event bootstrap 95% CIs (2,000 resamples, seed 7) and a bootstrap CI for the campaign - comparison
      difference in Spearman (classes resampled separately, as stratified);
  (c) within-event level: the 10 views of each event differ only by sampling; Spearman between m_K and
      token_std across an event's 10 views, summarised (median, share positive) over events.
Also: class-wise descriptive statistics of m_K, m_K/K and token_std, and the pooled (both-class) Spearman for
comparison with the class-separated values. Descriptive only: no model is fitted, no causal claim is made.
Output: research_audit/final_diagnostics/outputs/d01_*.csv, d01_results.json, d01_fig_mK_vs_tokenstd.png
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "research_audit/final_diagnostics/outputs"
OUT.mkdir(parents=True, exist_ok=True)
KS = (250, 500, 1000)
NB, BS = 2000, 7
CLS = {1: "campaign", 0: "comparison"}

V = pd.read_csv(ROOT / "research_audit/outputs/v01_view_text.csv")
assert V.groupby(["K", "seed", "event_id"]).size().max() == 1
assert np.allclose(V.usable_share, V.n_usable_text / V.K)
V = V.rename(columns={"n_usable_text": "m_K", "usable_share": "m_K_over_K", "lensd_stored": "token_std"})


def sp(x, y):
    return float(spearmanr(x, y)[0]) if len(x) > 2 and np.ptp(x) > 0 and np.ptp(y) > 0 else np.nan


def pe(x, y):
    return float(pearsonr(x, y)[0]) if len(x) > 2 and np.ptp(x) > 0 and np.ptp(y) > 0 else np.nan


rng = np.random.default_rng(BS)
desc, levels, within_rows, res = [], [], [], {}
for K in KS:
    vk = V[(V.K == K)]
    res[K] = {}
    ev = vk.groupby("event_id").agg(label=("label", "first"), m_K=("m_K", "mean"), m_K_over_K=("m_K_over_K", "mean"),
                                    token_std=("token_std", "mean"), n_defined=("token_std", "count"))
    for lab in (1, 0, None):
        nm = CLS.get(lab, "pooled")
        h = vk if lab is None else vk[vk.label == lab]
        d = h[h.token_std.notna()]
        e = ev if lab is None else ev[ev.label == lab]
        e = e[e.n_defined == 10]  # events with token_std defined in all 10 views
        # descriptive statistics (all views of the class; token_std over defined views)
        if lab is not None:
            desc.append({"K": K, "class": nm, "events": int(h.event_id.nunique()), "views": len(h),
                         "views_token_std_undefined": int(h.token_std.isna().sum()),
                         "m_K_median": float(h.m_K.median()), "m_K_q25": float(h.m_K.quantile(.25)), "m_K_q75": float(h.m_K.quantile(.75)),
                         "m_K_min": int(h.m_K.min()), "m_K_max": int(h.m_K.max()),
                         "m_K_over_K_mean": float(h.m_K_over_K.mean()), "m_K_over_K_median": float(h.m_K_over_K.median()),
                         "token_std_median": float(d.token_std.median()), "token_std_q25": float(d.token_std.quantile(.25)),
                         "token_std_q75": float(d.token_std.quantile(.75))})
        # (a) per-seed view level
        per_s = [sp(s.m_K, s.token_std) for _, s in d.groupby("seed")]
        per_p = [pe(s.m_K, s.token_std) for _, s in d.groupby("seed")]
        # (b) between-event level with bootstrap
        x, y = e.m_K.to_numpy(), e.token_std.to_numpy()
        bs = []
        for _ in range(NB):
            i = rng.integers(0, len(x), len(x))
            bs.append(sp(x[i], y[i]))
        bs = np.array(bs)
        bs = bs[~np.isnan(bs)]
        # (c) within-event level
        w = [sp(g.m_K, g.token_std) for _, g in d.groupby("event_id") if len(g) == 10]
        w = np.array([v for v in w if not np.isnan(v)])
        r = {"class": nm, "K": K,
             "a_per_seed_view_spearman_mean": float(np.mean(per_s)), "a_per_seed_view_spearman_min": float(np.min(per_s)),
             "a_per_seed_view_spearman_max": float(np.max(per_s)), "a_per_seed_view_pearson_mean": float(np.mean(per_p)),
             "a_views_per_seed": int(len(d) / 10) if len(d) % 10 == 0 else float(len(d) / 10),
             "b_events": int(len(e)), "b_event_spearman": sp(x, y), "b_event_spearman_ci": np.percentile(bs, [2.5, 97.5]).tolist(),
             "b_event_pearson": pe(x, y),
             "c_events": int(len(w)), "c_within_event_spearman_median": float(np.median(w)),
             "c_within_event_spearman_q25": float(np.percentile(w, 25)), "c_within_event_spearman_q75": float(np.percentile(w, 75)),
             "c_share_events_positive": float((w > 0).mean())}
        levels.append(r)
        res[K][nm] = {"x": x, "y": y, "bs": bs}
    # campaign - comparison difference in between-event Spearman (classes resampled separately)
    ca, co = res[K]["campaign"], res[K]["comparison"]
    dd = []
    for _ in range(NB):
        i, j = rng.integers(0, len(ca["x"]), len(ca["x"])), rng.integers(0, len(co["x"]), len(co["x"]))
        dd.append(sp(ca["x"][i], ca["y"][i]) - sp(co["x"][j], co["y"][j]))
    dd = np.array(dd)
    dd = dd[~np.isnan(dd)]
    res[K]["diff"] = {"campaign_minus_comparison_event_spearman": sp(ca["x"], ca["y"]) - sp(co["x"], co["y"]),
                      "ci": np.percentile(dd, [2.5, 97.5]).tolist(),
                      "p_two_sided_bootstrap": float(min(1.0, 2 * min((dd <= 0).mean(), (dd >= 0).mean())))}
    print(f"K={K} difference in event-level Spearman (campaign - comparison): {res[K]['diff']}", flush=True)

# class separation of token_std within strata of text availability (descriptive): per seed, views are split into
# thirds of m_K/K (cut points from that K's pooled defined views); AUC = P(comparison view has higher token_std
# than campaign view) within each third, averaged over seeds; also AUC of m_K/K itself, for reference.
def auc(pos, neg):
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    a = np.concatenate([pos, neg])
    r = pd.Series(a).rank().to_numpy()
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


strat = []
for K in KS:
    d = V[(V.K == K) & V.token_std.notna()].copy()
    cuts = d.m_K_over_K.quantile([1 / 3, 2 / 3]).to_numpy()
    d["third"] = np.digitize(d.m_K_over_K, cuts)
    for t, nm in enumerate(("lowest third", "middle third", "highest third")):
        g = d[d.third == t]
        a = [auc(s[s.label == 0].token_std.to_numpy(), s[s.label == 1].token_std.to_numpy()) for _, s in g.groupby("seed")]
        strat.append({"K": K, "stratum_m_K_over_K": nm, "range": f"{g.m_K_over_K.min():.2f}-{g.m_K_over_K.max():.2f}",
                      "campaign_views": int((g.label == 1).sum()), "comparison_views": int((g.label == 0).sum()),
                      "auc_token_std_comparison_higher_mean_over_seeds": float(np.nanmean(a))})
    a_all = [auc(s[s.label == 0].token_std.to_numpy(), s[s.label == 1].token_std.to_numpy()) for _, s in d.groupby("seed")]
    a_mk = [auc(s[s.label == 0].m_K_over_K.to_numpy(), s[s.label == 1].m_K_over_K.to_numpy()) for _, s in d.groupby("seed")]
    strat.append({"K": K, "stratum_m_K_over_K": "all views", "range": f"{d.m_K_over_K.min():.2f}-{d.m_K_over_K.max():.2f}",
                  "campaign_views": int((d.label == 1).sum()), "comparison_views": int((d.label == 0).sum()),
                  "auc_token_std_comparison_higher_mean_over_seeds": float(np.mean(a_all)),
                  "auc_m_K_over_K_comparison_higher_mean_over_seeds": float(np.mean(a_mk))})
S = pd.DataFrame(strat)
S.to_csv(OUT / "d01_stratified_class_separation.csv", index=False)
print(S.round(3).to_string(index=False))

D = pd.DataFrame(desc)
Lv = pd.DataFrame(levels)
D.to_csv(OUT / "d01_descriptives.csv", index=False)
flat = Lv.copy()
flat["b_event_spearman_ci"] = flat.b_event_spearman_ci.map(lambda v: f"[{v[0]:+.3f}, {v[1]:+.3f}]")
flat.to_csv(OUT / "d01_associations.csv", index=False)
print(D.round(3).to_string(index=False))
print(flat.round(3).to_string(index=False))

# fig: event means of m_K/K vs token_std, by class and K
BLUE, ORANGE, MUTED = "#2a78d6", "#eb6834", "#8a8a85"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUTED})
fig, ax = plt.subplots(1, 3, figsize=(10, 3.3), sharey=True)
for a, K in zip(ax, KS):
    for lab, col in ((0, BLUE), (1, ORANGE)):
        r = res[K][CLS[lab]]
        a.scatter(r["x"] / K, r["y"], s=14, color=col, edgecolor="white", linewidth=0.5,
                  label=f"{CLS[lab]} (ρ = {sp(r['x'], r['y']):+.2f})")
    a.set_xlim(-0.02, 1.02)
    a.set_xlabel("mean m_K / K over the event's 10 views")
    a.set_title(f"K = {K}", fontsize=9)
    a.legend(fontsize=7, frameon=False, loc="upper left")
ax[0].set_ylabel("mean token_std over 10 views (tokens)")
fig.suptitle("Text availability vs message-length dispersion, event level (events with token_std defined in all views)", fontsize=9.5)
fig.tight_layout()
fig.savefig(OUT / "d01_fig_mK_vs_tokenstd.png", dpi=200)
pd.concat([pd.DataFrame({"K": K, "class": CLS[lab], "m_K_mean": res[K][CLS[lab]]["x"], "token_std_mean": res[K][CLS[lab]]["y"]})
           for K in KS for lab in (0, 1)]).to_csv(OUT / "d01_fig_data.csv", index=False)

(OUT / "d01_results.json").write_text(json.dumps({"descriptives": D.to_dict("records"), "associations": Lv.to_dict("records"),
                                                  "stratified_class_separation": S.to_dict("records"),
                                                  "class_difference_event_spearman": {str(K): res[K]["diff"] for K in KS}},
                                                 indent=2, default=float), encoding="utf-8")
