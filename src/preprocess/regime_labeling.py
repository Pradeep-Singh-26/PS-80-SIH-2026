"""Multi-Label Weather Regime Ground-Truth Labeling Module (Track A - Task 2).

Generates multi-label ground truth across 6 meteorological classes:
1. active
2. break
3. low_depression
4. western_disturbance
5. orographic
6. coastal

Produces:
- data/processed/regime_labels.csv
  Columns: date, active, break, low_depression, western_disturbance, orographic, coastal
"""

import logging
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

logger = logging.getLogger(__name__)

REGIME_CLASSES = [
    "active",
    "break",
    "low_depression",
    "western_disturbance",
    "orographic",
    "coastal",
]


def generate_regime_labels(processed_dir: Path) -> pd.DataFrame:
    """Assign multi-label ground-truth weather regime flags for each date."""
    features_file = processed_dir / "features_daily.csv"
    obs_file = processed_dir / "obs_grid.nc"

    if not features_file.exists():
        raise FileNotFoundError(f"Missing features file: {features_file}")
    if not obs_file.exists():
        raise FileNotFoundError(f"Missing obs grid file: {obs_file}")

    df_feat = pd.read_csv(features_file)
    ds_obs = xr.open_dataset(obs_file)
    obs_rain = ds_obs["precip_mm"].values
    lats = ds_obs["lat"].values
    lons = ds_obs["lon"].values

    lon_mesh, lat_mesh = np.meshgrid(lons, lats)
    orog_mask = (
        (((lat_mesh >= 18.0) & (lat_mesh <= 20.0) & (lon_mesh <= 75.5))) |
        (((lat_mesh >= 21.5) & (lat_mesh <= 22.8) & (lon_mesh >= 77.0) & (lon_mesh <= 81.0)))
    )
    coastal_mask = (lon_mesh <= 74.5) | (lon_mesh >= 85.0)

    dates = df_feat["date"].values

    # Vectorized computation of terrain and coastal mean rainfall over all dates
    terrain_rain = obs_rain[:, orog_mask].mean(axis=1)
    coastal_rain = obs_rain[:, coastal_mask].mean(axis=1)

    rain_anom = df_feat["rainfall_anomaly"].values
    mslp_anom = df_feat["mslp_anomaly"].values
    trough_lat = df_feat["trough_position_lat"].values
    is_lps = df_feat["lps_flag"].values
    is_wd = df_feat["wd_flag"].values
    orog_idx = df_feat["orographic_index"].values
    coast_idx = df_feat["coastal_convergence_index"].values

    # 1. Active Monsoon
    active_flags = ((rain_anom >= 0.65) & (trough_lat <= 22.5) & (mslp_anom <= 0.5)).astype(int)

    # 2. Break Monsoon
    break_flags = ((rain_anom <= -0.65) & ((trough_lat >= 23.5) | (mslp_anom >= 0.8))).astype(int)

    # 3. Low Pressure System / Depression
    lps_flags = (is_lps == 1).astype(int)

    # 4. Western Disturbance
    wd_flags = (is_wd == 1).astype(int)

    # 5. Orographic Enhancement
    orog_flags = ((orog_idx >= 1.25) & (terrain_rain >= 8.0)).astype(int)

    # 6. Coastal Convergence
    coastal_flags = ((coast_idx >= 1.20) & (coastal_rain >= 5.0)).astype(int)

    df_labels = pd.DataFrame({
        "date": dates,
        "active": active_flags,
        "break": break_flags,
        "low_depression": lps_flags,
        "western_disturbance": wd_flags,
        "orographic": orog_flags,
        "coastal": coastal_flags,
    })

    return df_labels


def run_regime_labeling(processed_dir: Path) -> Path:
    """Run multi-label regime ground-truth labeling and save regime_labels.csv."""
    processed_dir = Path(processed_dir)
    df_labels = generate_regime_labels(processed_dir)
    out_file = processed_dir / "regime_labels.csv"
    df_labels.to_csv(out_file, index=False)
    logger.info(f"Saved {out_file} with {len(df_labels)} rows. Label counts:")
    for col in REGIME_CLASSES:
        logger.info(f"  {col}: {df_labels[col].sum()} positive days")
    return out_file
