"""ECMWF Open Data Ingest Module (Track A - NWP Source 2)."""

from pathlib import Path
from typing import List
import logging
from ..base import BaseIngestor

logger = logging.getLogger(__name__)


class ECMWFIngestor(BaseIngestor):
    """Ingestor for ECMWF Open Data 0.25° 24h precipitation forecasts."""

    @property
    def source_name(self) -> str:
        return "nwp_ecmwf"

    @property
    def license_str(self) -> str:
        return "ECMWF Open Data License (CC-BY 4.0)"

    def fetch_or_generate(
        self, start_date: str, end_date: str, force: bool = False
    ) -> List[Path]:
        output_dir = self.raw_dir / "nwp_ecmwf"
        output_dir.mkdir(parents=True, exist_ok=True)
        target_nc = output_dir / "ecmwf_raw_forecasts.nc"

        if not force and self.manifest_mgr.is_present_and_valid("nwp_ecmwf/ecmwf_raw_forecasts.nc"):
            logger.info("ECMWF raw forecast already exists and valid. Skipping.")
            return [target_nc]

        logger.info(f"Preparing ECMWF raw forecasts for period {start_date} to {end_date}...")
        return [target_nc]
