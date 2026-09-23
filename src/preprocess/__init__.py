"""Track A (Pradeep): Preprocessing, regridding, feature computation, and regime labeling.

Tasks owned:
- Task 2: Regrid NWP + obs to common grid, compute daily circulation indices,
          build climatology reference, produce per-date regime labels.

Contracts produced:
- data/processed/features_daily.csv
- data/processed/nwp_grid_gfs.nc
- data/processed/nwp_grid_ecmwf.nc
- data/processed/obs_grid.nc
- data/processed/climatology.nc
- data/processed/station_obs.csv
- data/processed/regime_labels.csv
"""

from pathlib import Path
from .regrid import run_regridding
from .climatology import run_climatology
from .station_prep import run_station_prep
from .feature_engineering import run_feature_engineering
from .regime_labeling import run_regime_labeling


def run():
    """Execute Track A preprocessing, regridding, and feature engineering pipeline."""
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    run_regridding(raw_dir, processed_dir)
    run_climatology(processed_dir)
    run_station_prep(raw_dir, processed_dir)
    run_feature_engineering(raw_dir, processed_dir)
    run_regime_labeling(processed_dir)


__all__ = [
    "run",
    "run_regridding",
    "run_climatology",
    "run_station_prep",
    "run_feature_engineering",
    "run_regime_labeling",
]

