"""Schedulable, Idempotent Ingestion Scaffolding (Track A).

Per PLAN.md Section 2.1 Task 1:
"Automated ingestion pipeline scaffolding (schedulable, idempotent, re-runnable) —
built to run on a schedule even though this team will run it manually/on-demand
rather than against a live operational feed."
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..base import ManifestManager
from ..sample_generator import BenchmarkDataGenerator

logger = logging.getLogger(__name__)


class IngestionScheduler:
    """Orchestrates scheduled/batch multi-source ingestion runs."""

    def __init__(self, raw_dir: Path):
        self.raw_dir = Path(raw_dir)
        self.manifest_mgr = ManifestManager(self.raw_dir)

    def check_status(self) -> Dict[str, bool]:
        """Check presence and checksum validity of all expected raw sources."""
        expected = [
            "district_shapefile/districts.geojson",
            "lps_wd_tracks/lps_tracks.csv",
            "lps_wd_tracks/wd_tracks.csv",
            "obs_gridded/imd_obs_raw.nc",
            "nwp_gfs/gfs_raw_forecasts.nc",
            "nwp_ecmwf/ecmwf_raw_forecasts.nc",
            "reanalysis/circulation_raw.nc",
            "satellite_proxy/olr_proxy_raw.nc",
            "obs_station/station_obs_raw.csv",
            "station_metadata.csv",
        ]
        status = {}
        for rel_p in expected:
            status[rel_p] = self.manifest_mgr.is_present_and_valid(rel_p)
        return status

    def run_ingest(self, force: bool = False) -> None:
        """Run complete idempotent ingestion. Generates benchmark sample if needed."""
        status = self.check_status()
        all_present = all(status.values())

        if all_present and not force:
            logger.info("All raw datasets are already present and valid. Nothing to do.")
            return

        logger.info("One or more raw datasets missing or checksum mismatch. Generating raw sources...")
        generator = BenchmarkDataGenerator(self.raw_dir, manifest_mgr=self.manifest_mgr)
        generator.generate_all()
        self.manifest_mgr.load()
        logger.info("Ingestion completed successfully.")
