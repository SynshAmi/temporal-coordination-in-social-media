"""
run_pipeline.py
---------------
Reproducible pipeline for the LEN-Small study. The default config
(configs/v2_coreness_fix.yaml) writes the authoritative run, outputs/run_v2.

Executes:
   1. Ingestion (src/ingest_len.py)
   2. Validation (src/validate_len.py)
   3. Cohort Matching (src/build_cohorts.py)
   4. Edge-budget Sampling (src/sample_views.py)
   5. Training & Cross-Validation (src/train.py)
   6. Fold-aligned frozen-model evaluation (src/reevaluate_d1.py --apply)
   7. Evaluation & Checkpoint Report (src/evaluate.py)
   8. Study 1: incremental information, null model, matching (src/study1_incremental.py)
   9. Study 2: single-view observation (src/study2_observation.py)
  10. Independent verification (src/verify_studies.py)
  11. Paper results file (src/export_paper_results.py)
  12. Paper inputs: figures (paper/make_paper_figures.py) and LaTeX result macros
      (src/export_latex_results.py)
  13. Website payload (src/export_frontend_data.py)
  14. Test Suite (pytest tests/ -v)

The paper PDF itself is compiled separately with LaTeX: python paper/build.py (see README).
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def run_stage(commands: list, stage_name: str, env: dict | None = None) -> float:
    """Runs one command, or a list of commands in order, as a single stage."""
    if isinstance(commands[0], str):
        commands = [commands]
    print("\n" + "=" * 70)
    print(f"STAGE: {stage_name}")
    for command in commands:
        print(f"Command: {' '.join(command)}")
    print("=" * 70 + "\n", flush=True)
    t0 = time.time()
    for command in commands:
        res = subprocess.run(command, env=env)
        if res.returncode != 0:
            raise RuntimeError(f"Stage '{stage_name}' failed with return code {res.returncode}")
    return time.time() - t0


def main():
    parser = argparse.ArgumentParser(description="Run the complete LEN-Small pipeline (both studies, verification, exports, tests)")
    parser.add_argument("--config", default="configs/v2_coreness_fix.yaml")
    parser.add_argument("--skip-tests", action="store_true", help="Skip test suite execution")
    args = parser.parse_args()

    py, cfg_path = sys.executable, args.config
    out_cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))["output"]
    run_dir = Path(out_cfg["run_dir"])
    c = ["--config", cfg_path]
    # tests read paths from the same config; inside the pipeline, missing generated data is a failure, not a skip
    test_env = {**os.environ, "LEN_CONFIG": cfg_path, "LEN_REQUIRE_DATA": "1"}

    stages = [
        ("1. Ingest Archive", [py, "src/ingest_len.py", *c]),
        ("2. Data Quality & Schema Validation", [py, "src/validate_len.py", *c]),
        ("3. Node-Count Matching & SMD Diagnostics", [py, "src/build_cohorts.py", *c]),
        ("4. Edge-Budget Sampling & Feature Reconstruction", [py, "src/sample_views.py", *c]),
        ("5. Train & Evaluate Base Experiment Grid", [py, "src/train.py", *c]),
        # refits the frozen models, checks they reproduce the stored predictions, adds complete-graph references
        ("6. Fold-Aligned Frozen-Model Evaluation", [py, "src/reevaluate_d1.py", *c, "--apply"]),
        ("7. Checkpoint Report & Pipeline Figures", [py, "src/evaluate.py", *c]),
        ("8. Study 1: Incremental Information", [py, "src/study1_incremental.py", *c]),
        ("9. Study 2: Single-View Observation", [py, "src/study2_observation.py", *c]),
        ("10. Independent Verification", [py, "src/verify_studies.py", *c]),
        ("11. Export Paper Results", [py, "src/export_paper_results.py", *c]),
        ("12. Paper Inputs (Figures & LaTeX Result Macros)", [
            [py, "paper/make_paper_figures.py", *c, "--out-dir", out_cfg.get("paper_figures_dir", "paper/figures")],
            [py, "src/export_latex_results.py", *c],
        ]),
        ("13. Export Website Payload", [py, "src/export_frontend_data.py", *c]),
    ]
    if not args.skip_tests:
        stages.append(("14. Run Test Suite", [py, "-m", "pytest", "tests/", "-v"]))

    log, t_start = [], time.time()
    for name, cmd in stages:
        try:
            secs = run_stage(cmd, name, env=test_env if name.startswith("14.") else None)
            log.append({"stage": name, "status": "ok", "seconds": round(secs, 1)})
        except RuntimeError as e:
            log.append({"stage": name, "status": "failed", "error": str(e)})
            print(f"\nPIPELINE STOPPED: {e}. Later stages were not run.", file=sys.stderr)
            break
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "pipeline_stages.json").write_text(json.dumps(
        {"config": cfg_path, "total_seconds": round(time.time() - t_start, 1), "stages": log}, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    for r in log:
        print(f"  {r['status']:>6}  {r.get('seconds', '-'):>8}  {r['stage']}")
    if any(r["status"] != "ok" for r in log):
        sys.exit(1)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Outputs are in {run_dir.as_posix()} (stage log: pipeline_stages.json).")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
