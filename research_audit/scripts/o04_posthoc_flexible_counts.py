"""
o04_posthoc_flexible_counts.py — POST-HOC check, added after o03 showed that QDA on (log n, log m)
reaches AUC ~0.95: is E[N_250]'s advantage over "counts" an advantage over *linear* counts only?

Same 102 events (m >= 250), same outer splits (StratifiedKFold(5, shuffle, seed 1000 + r), 20 repeats),
same LR tuning as o03 configuration A. Contrasts use the event bootstrap (2,000, seed 7) of
repeat-averaged out-of-fold probabilities. Not pre-specified; no multiplicity correction.

Output: research_audit/outputs/o04_posthoc.json
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
# reuse o03's functions without executing its analysis
src = (ROOT / "research_audit/scripts/o03_occupancy_analysis.py").read_text(encoding="utf-8")
head = src.split("results = {}")[0]
ns = {"__name__": "o03_functions", "__file__": str(ROOT / "research_audit/scripts/o03_occupancy_analysis.py")}
exec(compile(head, "o03_functions", "exec"), ns)

F0 = pd.read_csv(ROOT / "research_audit/outputs/o02_features.csv")
FA = F0[F0.m >= 250].reset_index(drop=True)
X, y = ns["design"](FA, "E250"), FA.label.values.astype(int)
C = ns["COUNTS"]
models = {
    "counts + nonlinear": C + ["log_n_sq", "log_m_sq", "log_n_x_m"],
    "QDA on counts": C,
    "E[N_K] alone": ["log_E"],
    "counts + nonlinear + E[N_K]": C + ["log_n_sq", "log_m_sq", "log_n_x_m", "log_E"],
}
P, fold = ns["run"](X, y, models, [1000 + r for r in range(20)], list(np.logspace(-3, 3, 7)))
out = {}
for a, b in [("E[N_K] alone", "QDA on counts"), ("E[N_K] alone", "counts + nonlinear"), ("counts + nonlinear + E[N_K]", "counts + nonlinear")]:
    eb = ns["event_boot"](y, P[a].mean(0), P[b].mean(0))
    M = ns["per_repeat"]({a: P[a], b: P[b]}, y)
    d = M[a] - M[b]
    out[f"{a} − {b}"] = {"event_bootstrap": {k: v for k, v in eb.items() if k != "per_event_dLL"},
                         "repeat_mean": {"dBA": float(d[:, 0].mean()), "dAUC": float(d[:, 1].mean()), "dLL": float(d[:, 2].mean())}}
    print(f"{a} − {b}: dAUC {eb['dAUC']:+.3f} [{eb['dAUC_ci'][0]:+.3f}, {eb['dAUC_ci'][1]:+.3f}] | dLL {eb['dLL']:+.3f} "
          f"[{eb['dLL_ci'][0]:+.3f}, {eb['dLL_ci'][1]:+.3f}] | dBA {eb['dBA']:+.3f} [{eb['dBA_ci'][0]:+.3f}, {eb['dBA_ci'][1]:+.3f}]")
(ROOT / "research_audit/outputs/o04_posthoc.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
