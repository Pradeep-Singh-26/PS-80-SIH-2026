"""Track A (Pradeep): Ingestion modules for downloading and preparing raw data.

Tasks owned:
- Task 1: Data ingestion (NWP, obs, MSLP/OLR reanalysis, LPS tracks, district shapefile)
Raw data destination: data/raw/
"""

from pathlib import Path
from .realtime_feed.scheduler import IngestionScheduler


def run(force: bool = False):
    """Execute Track A multi-source data ingestion pipeline."""
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    scheduler = IngestionScheduler(raw_dir)
    scheduler.run_ingest(force=force)


__all__ = ["run", "IngestionScheduler"]

