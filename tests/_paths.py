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
