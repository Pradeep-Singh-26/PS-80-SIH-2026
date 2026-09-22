"""PS 26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts.

Single pipeline orchestrator (owned by Track C - Divyansh).
Chains Tasks 1–12 end-to-end across:
  - Track A (Pradeep): Ingestion (Task 1), Preprocessing (Task 2), Regime Classifier (Task 3)
  - Track B (Baljeet): Correction (Task 4), Heavy Rain Prob (Task 5), MLOps (Task 11)
  - Track C (Divyansh): Aggregation (Task 6), Verification (Task 7), API (Task 8),
                         Dashboard (Task 9), Alerts (Task 10), Ops (Task 12)

All data paths come from config.yaml (or CONFIG_PATH env var).

Usage:
  python run_pipeline.py [--stage STAGE] [--config CONFIG_PATH]
"""

import argparse
import importlib
import sys
import traceback
from pathlib import Path


STAGES = [
    # (stage_name, module_path, function_name, track_owner)
    ("ingest", "src.ingest", "run", "Track A"),
    ("preprocess", "src.preprocess", "run", "Track A"),
    ("classifier", "src.regime_classifier", "run", "Track A"),
    ("correction", "src.bias_correction", "run", "Track B"),
    ("probability", "src.heavy_rain_prob", "run", "Track B"),
    ("aggregate", "src.district_agg", "run", "Track C"),
    ("verify", "src.verification", "run", "Track C"),
    ("alerts", "src.alerts", "run", "Track C"),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the end-to-end Regime-Aware Rainfall Post-Processing Pipeline."
    )
    parser.add_argument(
        "--stage",
        choices=["all"] + [s[0] for s in STAGES],
        default="all",
        help="Pipeline stage to execute (default: all)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config YAML (default: config.yaml at repo root)",
    )
    return parser.parse_args()


def _run_stage(name: str, module_path: str, func_name: str, track: str) -> bool:
    """Attempt to import and run a stage. Returns True on success."""
    print(f"\n{'='*60}")
    print(f"  Stage: {name} ({track})")
    print(f"{'='*60}")
    try:
        mod = importlib.import_module(module_path)
        fn = getattr(mod, func_name, None)
        if fn is None:
            print(f"  [SKIP] {module_path}.{func_name}() not implemented yet -- skipping.")
            return True  # not a failure, just not built yet
        fn()
        print(f"  [OK] {name} completed.")
        return True
    except ImportError:
        print(f"  [SKIP] Module {module_path} not available yet -- skipping.")
        return True
    except Exception as exc:
        print(f"  [FAIL] {name} FAILED: {exc}")
        traceback.print_exc()
        return False


def main():
    args = parse_args()

    # Set config path if provided
    if args.config:
        import os
        os.environ["CONFIG_PATH"] = str(Path(args.config).resolve())

    workspace_dir = Path(__file__).resolve().parent

    print("=" * 60)
    print("  Regime-Aware Rainfall Post-Processing Pipeline (PS 26080)")
    print(f"  Workspace : {workspace_dir}")
    print(f"  Stage     : {args.stage}")
    print("=" * 60)

    stages_to_run = STAGES if args.stage == "all" else [
        s for s in STAGES if s[0] == args.stage
    ]

    results = {}
    for name, module_path, func_name, track in stages_to_run:
        ok = _run_stage(name, module_path, func_name, track)
        results[name] = ok

    # Summary
    print(f"\n{'='*60}")
    print("  Pipeline Summary")
    print(f"{'='*60}")
    for stage, ok in results.items():
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {stage:20s} {status}")

    failed = [s for s, ok in results.items() if not ok]
    if failed:
        print(f"\n[WARN] {len(failed)} stage(s) failed: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\n[DONE] Pipeline complete.")


if __name__ == "__main__":
    main()
