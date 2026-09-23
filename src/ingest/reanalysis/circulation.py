"""Circulation and Atmospheric Reanalysis Ingest Module (Track A)."""

from pathlib import Path
from typing import List, Optional
import logging
from ..base import BaseIngestor

logger = logging.getLogger(__name__)


class CirculationIngestor(BaseIngestor):
    """Ingestor for ERA5 / Reanalysis circulation indicators (MSLP, 850 hPa winds)."""

    @property
    def source_name(self) -> str:
        return "reanalysis_circulation"

    @property
    def license_str(self) -> str:
        return "Copernicus Open Access License / ECMWF"

    def fetch_or_generate(
        self, start_date: str, end_date: str, force: bool = False
    ) -> List[Path]:
        output_dir = self.raw_dir / "reanalysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        target_nc = output_dir / "circulation_raw.nc"

        if not force and self.manifest_mgr.is_present_and_valid("reanalysis/circulation_raw.nc"):
            logger.info("Circulation reanalysis raw data already exists and valid. Skipping.")
            return [target_nc]

        logger.info(f"Preparing Circulation reanalysis for period {start_date} to {end_date}...")
        return [target_nc]
