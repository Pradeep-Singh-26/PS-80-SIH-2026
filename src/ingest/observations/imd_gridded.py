"""IMD Gridded Daily Rainfall Ingest Module (Track A - Gridded Obs)."""

from pathlib import Path
from typing import List, Optional
import logging
import xarray as xr
from ..base import BaseIngestor, ManifestManager

logger = logging.getLogger(__name__)


class IMDGriddedIngestor(BaseIngestor):
    """Ingestor for IMD 0.25° Daily Gridded Rainfall observations."""

    @property
    def source_name(self) -> str:
        return "obs_gridded"

    @property
    def license_str(self) -> str:
        return "IMD Open Access / MoES"

    def fetch_or_generate(
        self, start_date: str, end_date: str, force: bool = False
    ) -> List[Path]:
        output_dir = self.raw_dir / "obs_gridded"
        output_dir.mkdir(parents=True, exist_ok=True)
        target_nc = output_dir / "imd_obs_raw.nc"

        if not force and self.manifest_mgr.is_present_and_valid("obs_gridded/imd_obs_raw.nc"):
            logger.info("IMD gridded raw obs already exists and valid. Skipping.")
            return [target_nc]

        logger.info(f"Preparing IMD gridded obs for period {start_date} to {end_date}...")
        return [target_nc]
