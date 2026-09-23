"""Radar Data Ingest / Availability Module (Track A)."""

from pathlib import Path
from typing import List, Optional
import logging
from ..base import BaseIngestor

logger = logging.getLogger(__name__)


class RadarIngestor(BaseIngestor):
    """Handler for operational radar mosaic.

    Per PLAN.md Section 2.2, live DWR mosaic feeds require institutional MoES radar access
    which is unavailable for this build. This handler documents fallback status.
    """

    @property
    def source_name(self) -> str:
        return "radar_mosaic"

    @property
    def license_str(self) -> str:
        return "IMD Restricted (Fallback: marked unavailable)"

    def fetch_or_generate(
        self, start_date: str, end_date: str, force: bool = False
    ) -> List[Path]:
        logger.info(
            "IMD radar mosaic live feeds are deferred per PLAN.md Section 2.2. "
            "Pipeline proceeds using satellite OLR proxy as convective indicator."
        )
        return []
