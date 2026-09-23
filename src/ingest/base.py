"""Base ingestion classes and manifest utilities for Track A (Pradeep).

Provides idempotent file acquisition, SHA-256 checksum verification,
and structured manifest generation required by TEAM_SPLIT.md.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file for manifest tracking."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


class ManifestManager:
    """Manages the raw data manifests under data/raw/manifest.json."""

    def __init__(self, raw_dir: Path):
        self.raw_dir = Path(raw_dir)
        self.manifest_path = self.raw_dir / "manifest.json"
        self._entries: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing manifest: {e}. Starting fresh.")
                self._entries = {}
        else:
            self._entries = {}

    def register(
        self,
        rel_path: str,
        source: str,
        date_range: str,
        license_str: str,
        description: str,
    ) -> Dict[str, Any]:
        """Register or update a file in the manifest."""
        abs_path = self.raw_dir / rel_path
        if not abs_path.exists():
            raise FileNotFoundError(f"Cannot register non-existent file: {abs_path}")

        file_stat = abs_path.stat()
        entry = {
            "path": rel_path,
            "source": source,
            "date_range": date_range,
            "license": license_str,
            "description": description,
            "size_bytes": file_stat.st_size,
            "mtime": file_stat.st_mtime,
            "sha256": compute_sha256(abs_path),
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        self._entries[rel_path] = entry
        return entry

    def save(self) -> None:
        """Persist manifest to disk."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, indent=2)

    def is_present_and_valid(self, rel_path: str) -> bool:
        """Check if file exists and matches its manifest checksum.

        Uses cached size and mtime for O(1) instant verification,
        falling back to full SHA-256 calculation if modified.
        """
        abs_path = self.raw_dir / rel_path
        if not abs_path.exists():
            return False
        entry = self._entries.get(rel_path)
        if not entry:
            return True
        st = abs_path.stat()
        # Fast path: unchanged size and mtime
        if "mtime" in entry and entry["size_bytes"] == st.st_size and entry["mtime"] == st.st_mtime:
            return True
        # If size differs, definitely invalid
        if entry.get("size_bytes") != st.st_size:
            return False
        # Fallback to full cryptographic hash
        return compute_sha256(abs_path) == entry.get("sha256")


class BaseIngestor(ABC):
    """Abstract base class for all data ingestion handlers."""

    def __init__(self, raw_dir: Path, manifest_mgr: Optional[ManifestManager] = None):
        self.raw_dir = Path(raw_dir)
        self.manifest_mgr = manifest_mgr or ManifestManager(self.raw_dir)

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier of the source (e.g. 'nwp_gfs', 'obs_gridded')."""
        pass

    @property
    @abstractmethod
    def license_str(self) -> str:
        """License string for the source."""
        pass

    @abstractmethod
    def fetch_or_generate(
        self, start_date: str, end_date: str, force: bool = False
    ) -> List[Path]:
        """Fetch or generate raw data for the specified date range.

        Should be idempotent: skip existing files if force=False.
        """
        pass
