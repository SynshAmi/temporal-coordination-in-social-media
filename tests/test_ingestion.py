"""
test_ingestion.py
-----------------
Tests for ingestion, authoritative label mapping, and schema integrity.
"""

import sys
import json
from pathlib import Path
import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import MANIFESTS_DIR, PROCESSED_DIR  # noqa: E402


@pytest.fixture(scope="module")
def manifest():
    path = MANIFESTS_DIR / "manifest.parquet"
    if not path.exists():
        pytest.skip("manifest.parquet not found - run src/ingest_len.py first")
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def validation_report():
    path = MANIFESTS_DIR / "validation_report.json"
    if not path.exists():
        pytest.skip("validation_report.json not found - run src/validate_len.py first")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_event_count(manifest):
    assert len(manifest) == 103, f"Expected 103 unique events, got {len(manifest)}"


def test_campaign_count(manifest):
    assert (manifest["label"] == 1).sum() == 52


def test_comparison_count(manifest):
    assert (manifest["label"] == 0).sum() == 51


def test_no_duplicate_event_ids(manifest):
    assert manifest["event_id"].nunique() == len(manifest)


def test_no_zero_node_events(manifest):
    assert (manifest["n_nodes"] == 0).sum() == 0, "Some events have 0 nodes"


def test_labels_are_binary(manifest):
    assert set(manifest["label"].unique()).issubset({0, 1})


def test_sha256_present(manifest):
    assert "sha256" in manifest.columns
    assert manifest["sha256"].notna().all()


def test_file_hashes_match_published_list(manifest):
    # Every ingested graph file must match the SHA-256 published in data/manifests/file_hashes.csv
    published = pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "manifests" / "file_hashes.csv")
    got = dict(zip(manifest["file_name"], manifest["sha256"]))
    want = dict(zip(published["file_name"], published["sha256"]))
    assert got == want


def test_node_ids_are_per_graph_indices(validation_report):
    # Node IDs are 0..N-1 in every graph, so they are not account identifiers
    assert validation_report["node_id_scheme"]["per_graph_indices_0_to_n_minus_1"] is True
    assert "account_overlap" not in validation_report


def test_validation_passes(validation_report):
    if not validation_report["pass"]:
        failing = [k for k, v in validation_report["checks"].items() if v["status"] == "FAIL"]
        pytest.fail(f"Validation FAILED on checks: {failing}")
