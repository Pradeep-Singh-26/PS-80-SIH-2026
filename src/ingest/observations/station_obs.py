"""IMD Station Observations Ingest Module (Track A - Station Obs)."""

from pathlib import Path
from typing import List
import logging
from ..base import BaseIngestor

logger = logging.getLogger(__name__)


class StationObsIngestor(BaseIngestor):
    """Ingestor for IMD Automated Weather Station (AWS) network observations."""

    @property
    def source_name(self) -> str:
        return "obs_station"

    @property
    def license_str(self) -> str:
        return "IMD AWS Public Domain"

    def fetch_or_generate(
        self, start_date: str, end_date: str, force: bool = False
    ) -> List[Path]:
        output_dir = self.raw_dir / "obs_station"
        output_dir.mkdir(parents=True, exist_ok=True)
        target_csv = output_dir / "station_obs_raw.csv"
        meta_csv = self.raw_dir / "station_metadata.csv"

        if not force and self.manifest_mgr.is_present_and_valid("obs_station/station_obs_raw.csv"):
            logger.info("Station raw obs already exists and valid. Skipping.")
            return [target_csv, meta_csv]

        logger.info(f"Preparing Station raw obs for period {start_date} to {end_date}...")
        return [target_csv, meta_csv]
