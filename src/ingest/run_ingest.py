"""CLI entry point for Track A Data Ingestion (Task 1).

Usage:
    python -m src.ingest.run_ingest [--force]
"""

import argparse
import logging
from pathlib import Path
from .realtime_feed.scheduler import IngestionScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_ingest")


def main():
    parser = argparse.ArgumentParser(description="Track A - Multi-Source Ingestion Runner (Task 1)")
    parser.add_argument("--force", action="store_true", help="Force re-generation of all raw data")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw"

    logger.info(f"Initializing Ingestion Runner for {raw_dir}...")
    scheduler = IngestionScheduler(raw_dir)
    scheduler.run_ingest(force=args.force)

    status = scheduler.check_status()
    all_ok = all(status.values())
    if all_ok:
        logger.info("Task 1 Ingestion: ALL SOURCES VERIFIED AND REGISTERED IN MANIFEST.")
    else:
        logger.error(f"Task 1 Ingestion: Some sources failed: {status}")


if __name__ == "__main__":
    main()
