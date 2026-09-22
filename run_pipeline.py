"""PS 26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts.

Single pipeline orchestrator (owned by Track C - Divyansh).
Chains Tasks 1–8 end-to-end across:
  - Track A (Pradeep): Ingestion (Task 1), Preprocessing (Task 2)
  - Track B (Baljeet): Regime Classifier (Task 3), Bias Correction (Task 4), Heavy Rain Prob (Task 5)
  - Track C (Divyansh): District Aggregation (Task 6), Verification (Task 7), Presentation (Task 8)

Usage:
  python run_pipeline.py [--stage {all,ingest,preprocess,classifier,correction,probability,district,verify,presentation}]
"""

import argparse
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the end-to-end Regime-Aware Rainfall Post-Processing Pipeline."
    )
    parser.add_argument(
        "--stage",
        choices=[
            "all",
            "ingest",
            "preprocess",
            "classifier",
            "correction",
            "probability",
            "district",
            "verify",
            "presentation",
        ],
        default="all",
        help="Pipeline stage to execute (default: all)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    workspace_dir = Path(__file__).resolve().parent
    print(f"=== Regime-Aware Rainfall Post-Processing Pipeline (PS 26080) ===")
    print(f"Workspace: {workspace_dir}")
    print(f"Selected stage: {args.stage}")
    print("Pipeline scaffolding initialized. Ready for track implementations.")


if __name__ == "__main__":
    main()
