"""
test_frontend_payload.py
------------------------
The website payload must carry the verified run_v2 results unchanged, so the
website and the paper cannot disagree.
"""

import sys
import json
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import CFG, PAYLOAD_PATH as PAYLOAD, RUN_DIR, SUPPLEMENT_PATH  # noqa: E402

RESULTS = RUN_DIR / "paper_results.json"

pytestmark = pytest.mark.skipif(not (PAYLOAD.exists() and RESULTS.exists()), reason="run the pipeline and exports first")


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_payload_embeds_paper_results_unchanged():
    data, R = load(PAYLOAD), load(RESULTS)
    assert data["paper"] == R
    assert data["metadata"]["source_run"] == CFG["output"]["run_dir"]
    assert R["verification"]["n_pass"] == R["verification"]["n_checks"]


def test_payload_embeds_revision_supplement_unchanged():
    assert load(PAYLOAD)["revision"] == load(SUPPLEMENT_PATH)


def test_payload_embeds_audit_results_unchanged():
    assert load(PAYLOAD)["audit"] == load(Path(__file__).resolve().parents[1] / CFG["output"]["audit_results"])


def test_payload_has_no_legacy_run_final_sections():
    data = load(PAYLOAD)
    for key in ("metrics", "audit_takeaways", "matching_diagnostics", "edge_eligibility", "validation_report"):
        assert key not in data, key


def test_table_rows_match_results():
    data, R = load(PAYLOAD), load(RESULTS)
    rows = {r["experiment_id"]: r for r in data["experiments"]}
    for model, label in (("logreg", "LogReg"), ("hgbt", "HGBT")):
        for lv, perf in R["study1"]["performance"][model].items():
            row = rows[f"S1_{label}_{lv}"]
            assert row["balanced_accuracy"] == perf["balanced_accuracy"]
            assert row["log_loss"] == perf["log_loss"]
            assert row["ba_ci_lower"] <= row["balanced_accuracy"] <= row["ba_ci_upper"]
            assert row["n_events"] == R["dataset"]["n_events"]
    s = R["study2"]["results"]["budget_specific_K250"]["conditions"]["KK|NK"]
    assert rows["S2_K250_KK_NK"]["balanced_accuracy"] == s["single_view_ba_mean"]


def test_cohort_counts():
    data = load(PAYLOAD)
    D = data["paper"]["dataset"]
    assert (D["n_events"], D["n_campaign"], D["n_comparison"]) == (103, 52, 51)
    assert len(data["event_points"]) == D["n_events"]
