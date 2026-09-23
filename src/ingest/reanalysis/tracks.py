"""IMD Best-Track (LPS/Depressions) and Western Disturbance Event Ingest (Track A)."""

from pathlib import Path
from typing import List, Optional
import logging
from ..base import BaseIngestor

logger = logging.getLogger(__name__)


class SynopticTracksIngestor(BaseIngestor):
    """Ingestor for Low Pressure Systems (LPS) and Western Disturbance (WD) tracks."""

    @property
    def source_name(self) -> str:
        return "synoptic_tracks"

    @property
    def license_str(self) -> str:
        return "RSMC New Delhi / IMD Public Data"

    def fetch_or_generate(
        self, start_date: str, end_date: str, force: bool = False
    ) -> List[Path]:
        output_dir = self.raw_dir / "lps_wd_tracks"
        output_dir.mkdir(parents=True, exist_ok=True)
        lps_csv = output_dir / "lps_tracks.csv"
        wd_csv = output_dir / "wd_tracks.csv"

        if (
            not force
            and self.manifest_mgr.is_present_and_valid("lps_wd_tracks/lps_tracks.csv")
            and self.manifest_mgr.is_present_and_valid("lps_wd_tracks/wd_tracks.csv")
        ):
            logger.info("Synoptic track data already exists and valid. Skipping.")
            return [lps_csv, wd_csv]

        logger.info(f"Preparing Synoptic tracks for period {start_date} to {end_date}...")
        return [lps_csv, wd_csv]
