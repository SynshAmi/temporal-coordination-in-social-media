"""
Paths used by the tests, read from the pipeline config so the suite checks the
run that produced them. run_pipeline.py sets LEN_CONFIG; the default is the
authoritative config.
"""

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / os.environ.get("LEN_CONFIG", "configs/v2_coreness_fix.yaml")
CFG = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

PROCESSED_DIR = ROOT / CFG["data"]["processed_dir"]
MANIFESTS_DIR = ROOT / CFG["data"]["manifests_dir"]
RUN_DIR = ROOT / CFG["output"]["run_dir"]
VIEWS_PATH = PROCESSED_DIR / CFG["edge_budgets"].get("views_file", "sampled_views.parquet")
PAYLOAD_PATH = ROOT / CFG["output"].get("frontend_payload", "frontend/public/data/research_data.json")


def require(path, what):
    """Generated data that a test needs. Inside the pipeline (LEN_REQUIRE_DATA=1) a missing
    file is a failure; elsewhere, e.g. a fresh clone without the raw archive, the test is
    skipped with the reason printed (pytest.ini enables -rs)."""
    import pytest
    path = Path(path)
    if path.exists():
        return
    msg = (f"{what} not found ({path.relative_to(ROOT).as_posix()}); it is regenerated from the raw "
           f"LEN archive by `python run_pipeline.py`")
    if os.environ.get("LEN_REQUIRE_DATA") == "1":
        pytest.fail(msg)
    pytest.skip(msg)
