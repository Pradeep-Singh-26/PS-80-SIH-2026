"""Track A (Pradeep): Ingestion modules for downloading and preparing raw data.

Tasks owned:
- Task 1: Data ingestion (NWP, obs, MSLP/OLR reanalysis, LPS tracks, district shapefile)
Raw data destination: data/raw/
"""

import logging
from pathlib import Path

from .base import ManifestManager
from .realtime_feed.scheduler import IngestionScheduler
from .sample_generator import BenchmarkDataGenerator

logger = logging.getLogger(__name__)


def run(force: bool = False) -> None:
    """Execute Track A multi-source data ingestion pipeline stage."""
    project_root = Path(__file__).resolve().parent.parent.parent
    try:
        from src.config import get_path
        shapefile_path = get_path("data.district_shapefile")
        if "tests" in shapefile_path.parts:
            raw_dir = project_root / "data" / "raw"
        elif shapefile_path.name == "district_shapefile":
            raw_dir = shapefile_path.parent
        else:
            raw_dir = project_root / "data" / "raw"
    except Exception:
        raw_dir = project_root / "data" / "raw"

    if not raw_dir.exists():
        raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing Ingestion Runner for {raw_dir}...")
    scheduler = IngestionScheduler(raw_dir)
    scheduler.run_ingest(force=force)

    status = scheduler.check_status()
    all_ok = all(status.values())
    if all_ok:
        logger.info("Task 1 Ingestion: ALL SOURCES VERIFIED AND REGISTERED IN MANIFEST.")
    else:
        logger.warning(f"Task 1 Ingestion: Sources status: {status}")


__all__ = [
    "run",
    "IngestionScheduler",
    "BenchmarkDataGenerator",
    "ManifestManager",
]
