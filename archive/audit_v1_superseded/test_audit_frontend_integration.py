"""
test_audit_frontend_integration.py
-----------------------------------
Verifies that:
1. Frontend exported data contains the full metrics mapping, 27 experiments, and valid stats.
2. Standardized Mean Difference (SMD) strictly matches matching_diagnostics.json.
3. The methodology audit PDF exists and is non-empty.
4. Scale baseline metric (B0a) matches verified value (0.8739 BA).
"""

import json
from pathlib import Path
import pytest


def test_research_data_json_integrity():
    json_path = Path("frontend/public/data/research_data.json")
    assert json_path.exists(), f"Missing {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "metrics" in data, "metrics dictionary missing from research_data.json!"
    assert "experiments" in data
    assert "matching_diagnostics" in data

    # 103 canonical events
    assert data["metadata"]["verified_events_count"] == 103
    assert data["metadata"]["campaign_count"] == 52
    assert data["metadata"]["comparison_count"] == 51

    # 27 total experiment records (26 evaluated + 1 infeasible K=2000)
    assert len(data["experiments"]) == 27

    # Metric B0a scale baseline
    b0a = data["metrics"].get("B0a_log_node_logreg")
    assert b0a is not None, "B0a_log_node_logreg missing from metrics dictionary"
    assert b0a["balanced_accuracy"] == pytest.approx(0.8739, abs=1e-3)
    assert b0a["roc_auc"] == pytest.approx(0.9340, abs=1e-3)

    # Combined model A
    comb = data["metrics"].get("A_combined_logreg")
    assert comb is not None
    assert comb["balanced_accuracy"] == pytest.approx(0.9229, abs=1e-3)


def test_smd_values_consistency():
    diag_path = Path("data/manifests/matching_diagnostics.json")
    assert diag_path.exists(), f"Missing {diag_path}"

    with open(diag_path, "r", encoding="utf-8") as f:
        diag = json.load(f)

    # Check verified SMD before and after
    assert diag["smd_before"] == pytest.approx(-2.2374, abs=1e-3)
    assert diag["smd_after"] == pytest.approx(-0.0954, abs=1e-3)
    assert diag["n_matched_pairs"] == 16
    assert diag["n_excluded"] == 71


def test_methodology_audit_pdf_exists():
    pdf_path = Path("frontend/public/LEN-Small_Methodology_Audit.pdf")
    assert pdf_path.exists(), "LEN-Small_Methodology_Audit.pdf missing from public directory"
    assert pdf_path.stat().st_size > 5000, "PDF artifact is too small or truncated"
