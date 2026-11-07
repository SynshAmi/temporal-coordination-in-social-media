"""
s04_posthoc_lensd.py — POST-HOC contrasts, chosen after s02 showed that message-length dispersion
carries almost all of the content signal: how close are counts + that single feature to the full model?
No refitting: uses the 20-repeat out-of-fold predictions saved by s02 (s02_oof.npz). Event bootstrap
(2,000, seed 7) of repeat-averaged quantities; not multiplicity-corrected.
Output: research_audit/outputs/s04_posthoc_lensd.json
"""
import json

import numpy as np

from s00_engine import OUT, contrast

Z = np.load(OUT / "s02_oof.npz", allow_pickle=True)
y = Z["label"]
out = {}
for a, b in (("M4", "M0q+lensd"), ("M2+lensd", "M0q+lensd"), ("M0q+lensd", "M0q"), ("M4", "M2+lensd")):
    c = contrast(y, Z[f"{a}|ll|all"], Z[f"{b}|ll|all"])
    out[f"{a} - {b}"] = c
    print(f"{a} - {b}: dLL {c['dLL']:+.3f} [{c['dLL_ci'][0]:+.3f}, {c['dLL_ci'][1]:+.3f}] | dAUC {c['dAUC']:+.3f} "
          f"[{c['dAUC_ci'][0]:+.3f}, {c['dAUC_ci'][1]:+.3f}] | repeats favouring A {c['repeats_favouring_A_LL']}/20")
(OUT / "s04_posthoc_lensd.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
