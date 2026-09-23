"""Topography and Digital Elevation Model (DEM) ingestion package.

Supports ISRO Bhuvan CartoDEM data ingestion and processing.
"""

from .cartodem import CartoDEMIngestor

__all__ = ["CartoDEMIngestor"]
