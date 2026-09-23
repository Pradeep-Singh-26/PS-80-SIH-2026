"""Satellite Convective Proxy / OLR Ingest Module (Track A)."""

from pathlib import Path
from typing import List, Optional
import logging
from ..base import BaseIngestor, ManifestManager

logger = logging.getLogger(__name__)


class SatelliteProxyIngestor(BaseIngestor):
    """Ingestor for Daily Interpolated OLR / INSAT Convective Proxy data."""

    @property
    def source_name(self) -> str:
        return "satellite_proxy"

    @property
    def license_str(self) -> str:
        return "NOAA / ESRL Open Access (INSAT proxy)"

    def fetch_or_generate(
        self, start_date: str, end_date: str, force: bool = False
    ) -> List[Path]:
        output_dir = self.raw_dir / "satellite_proxy"
        output_dir.mkdir(parents=True, exist_ok=True)
        target_nc = output_dir / "olr_proxy_raw.nc"

        if not force and self.manifest_mgr.is_present_and_valid("satellite_proxy/olr_proxy_raw.nc"):
            logger.info("Satellite proxy already exists and valid. Skipping.")
            return [target_nc]

        logger.info(f"Preparing Satellite proxy for period {start_date} to {end_date}...")
        return [target_nc]
