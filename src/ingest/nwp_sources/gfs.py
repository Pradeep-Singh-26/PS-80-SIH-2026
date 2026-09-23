"""NOAA GFS Archive Ingest Module (Track A - NWP Source 1)."""

from pathlib import Path
from typing import List, Optional
import logging
import xarray as xr
from ..base import BaseIngestor, ManifestManager

logger = logging.getLogger(__name__)


class GFSIngestor(BaseIngestor):
    """Ingestor for NOAA Global Forecast System (GFS) 0.25° 24h precipitation forecasts."""

    @property
    def source_name(self) -> str:
        return "nwp_gfs"

    @property
    def license_str(self) -> str:
        return "NOAA Open Data / Public Domain"

    def fetch_or_generate(
        self, start_date: str, end_date: str, force: bool = False
    ) -> List[Path]:
        output_dir = self.raw_dir / "nwp_gfs"
        output_dir.mkdir(parents=True, exist_ok=True)
        target_nc = output_dir / "gfs_raw_forecasts.nc"

        if not force and self.manifest_mgr.is_present_and_valid("nwp_gfs/gfs_raw_forecasts.nc"):
            logger.info("GFS raw forecast already exists and valid. Skipping.")
            return [target_nc]

        logger.info(f"Preparing GFS raw forecasts for period {start_date} to {end_date}...")
        return [target_nc]
