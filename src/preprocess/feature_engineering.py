"""Daily Feature Engineering Module (Track A - Task 2).

Computes daily dynamical, thermodynamical, satellite-proxy, synoptic storm flags,
and terrain/coastal indicators.
Produces:
- data/processed/features_daily.csv
  Columns: date, mslp_anomaly, olr_anomaly, satellite_proxy, rainfall_anomaly,
           lps_flag, wd_flag, trough_position_lat, zonal_shear_850,
           orographic_index, coastal_convergence_index
"""

import logging
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd
import xarray as xr

logger = logging.getLogger(__name__)


def compute_daily_features(
    raw_dir: Path, processed_dir: Path
) -> pd.DataFrame:
    """Extract and synthesize daily model input features across all sources."""
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)

    # 1. Load Processed Gridded Obs & Climatology
    obs_file = processed_dir / "obs_grid.nc"
    clim_file = processed_dir / "climatology.nc"
    if not obs_file.exists() or not clim_file.exists():
        raise FileNotFoundError("obs_grid.nc or climatology.nc missing in processed dir.")

    ds_obs = xr.open_dataset(obs_file)
    ds_clim = xr.open_dataset(clim_file)

    dates = ds_obs["date"].values
    n_dates = len(dates)
    lats = ds_obs["lat"].values
    lons = ds_obs["lon"].values

    obs_rain = ds_obs["precip_mm"].values  # (date, lat, lon)
    clim_rain = ds_clim["precip_mm_clim"].values

    # Domain mean daily rainfall & standardized anomaly
    domain_obs_mean = obs_rain.mean(axis=(1, 2))
    domain_clim_mean = clim_rain.mean(axis=(1, 2))
    diff = domain_obs_mean - domain_clim_mean
    std_diff = np.std(diff) if np.std(diff) > 1e-4 else 1.0
    rainfall_anomaly = diff / std_diff

    # 2. Load Reanalysis Circulation (MSLP, Winds)
    circ_file = raw_dir / "reanalysis" / "circulation_raw.nc"
    if not circ_file.exists():
        raise FileNotFoundError(f"Missing circulation raw file: {circ_file}")
    ds_circ = xr.open_dataset(circ_file)

    mslp_vals = ds_circ["mslp"].values  # (date, lat, lon)
    u850_vals = ds_circ["u850"].values  # (date, lat, lon)

    # Mean sea-level pressure departure from regional base (~1002.5 hPa)
    mslp_domain_mean = mslp_vals.mean(axis=(1, 2))
    mslp_anomaly = mslp_domain_mean - 1002.5

    # Trough position: latitude of minimum MSLP along the central meridian (closest to 80°E)
    lon_80_idx = np.argmin(np.abs(lons - 80.0))
    mslp_along_80 = mslp_vals[:, :, lon_80_idx]  # (date, lat)
    min_lat_indices = np.argmin(mslp_along_80, axis=1)
    trough_position_lat = lats[min_lat_indices]

    # Zonal shear: 850 hPa westerly wind speed in southern half (lat <= 21°N)
    south_lat_mask = (lats <= 21.0)
    zonal_shear_850 = u850_vals[:, south_lat_mask, :].mean(axis=(1, 2))

    # 3. Load Satellite Proxy (OLR)
    sat_file = raw_dir / "satellite_proxy" / "olr_proxy_raw.nc"
    if not sat_file.exists():
        raise FileNotFoundError(f"Missing satellite proxy file: {sat_file}")
    ds_sat = xr.open_dataset(sat_file)
    olr_vals = ds_sat["olr"].values  # (date, lat, lon)

    # OLR anomaly relative to 220 W/m² (negative means deep convection)
    olr_mean = olr_vals.mean(axis=(1, 2))
    olr_anomaly = olr_mean - 220.0

    # Satellite proxy: fraction of domain covered by convective high clouds (OLR <= 200 W/m²)
    satellite_proxy = (olr_vals <= 200.0).mean(axis=(1, 2))

    # 4. Orographic and Coastal Indices
    # Use ISRO Bhuvan CartoDEM topography if available, else fallback
    cartodem_file = processed_dir / "cartodem_grid.nc"
    if not cartodem_file.exists():
        cartodem_file = raw_dir / "topography" / "cartodem_raw.nc"

    lon_mesh, lat_mesh = np.meshgrid(lons, lats)
    if cartodem_file.exists():
        try:
            ds_dem = xr.open_dataset(cartodem_file)
            dem_elev = ds_dem["elevation_m"].interp(lat=lats, lon=lons, method="nearest").values
            orog_mask = dem_elev >= 500.0
            logger.info("Using ISRO Bhuvan CartoDEM for orographic terrain masking.")
        except Exception as e:
            logger.warning(f"Could not load CartoDEM ({e}), using default terrain mask.")
            orog_mask = (
                (((lat_mesh >= 18.0) & (lat_mesh <= 20.0) & (lon_mesh <= 75.5))) |
                (((lat_mesh >= 21.5) & (lat_mesh <= 22.8) & (lon_mesh >= 77.0) & (lon_mesh <= 81.0)))
            )
    else:
        orog_mask = (
            (((lat_mesh >= 18.0) & (lat_mesh <= 20.0) & (lon_mesh <= 75.5))) |
            (((lat_mesh >= 21.5) & (lat_mesh <= 22.8) & (lon_mesh >= 77.0) & (lon_mesh <= 81.0)))
        )

    if np.any(orog_mask):
        orog_rain_mean = obs_rain[:, orog_mask].mean(axis=1)
        orographic_index = np.where(domain_obs_mean > 0.1, orog_rain_mean / np.maximum(domain_obs_mean, 0.5), 1.0)
    else:
        orographic_index = np.ones(n_dates, dtype=float)

    # Coastal mask
    coastal_mask = (lon_mesh <= 74.5) | (lon_mesh >= 85.0)
    coastal_rain_mean = obs_rain[:, coastal_mask].mean(axis=1)
    coastal_convergence_index = np.where(domain_obs_mean > 0.1, coastal_rain_mean / np.maximum(domain_obs_mean, 0.5), 1.0)

    # 5. Synoptic Tracks (LPS & WD Flags)
    lps_file = raw_dir / "lps_wd_tracks" / "lps_tracks.csv"
    wd_file = raw_dir / "lps_wd_tracks" / "wd_tracks.csv"

    lps_dates = set()
    if lps_file.exists():
        lps_df = pd.read_csv(lps_file)
        if "date" in lps_df.columns:
            lps_dates = set(lps_df["date"].astype(str))

    wd_dates = set()
    if wd_file.exists():
        wd_df = pd.read_csv(wd_file)
        if "date" in wd_df.columns:
            wd_dates = set(wd_df["date"].astype(str))

    lps_flags = np.isin(dates, list(lps_dates)).astype(int)
    wd_flags = np.isin(dates, list(wd_dates)).astype(int)

    # Assemble features DataFrame
    df_features = pd.DataFrame({
        "date": dates,
        "mslp_anomaly": np.round(mslp_anomaly, 2),
        "olr_anomaly": np.round(olr_anomaly, 2),
        "satellite_proxy": np.round(satellite_proxy, 3),
        "rainfall_anomaly": np.round(rainfall_anomaly, 3),
        "lps_flag": lps_flags,
        "wd_flag": wd_flags,
        "trough_position_lat": np.round(trough_position_lat, 2),
        "zonal_shear_850": np.round(zonal_shear_850, 2),
        "orographic_index": np.round(orographic_index, 3),
        "coastal_convergence_index": np.round(coastal_convergence_index, 3),
    })

    return df_features


def run_feature_engineering(raw_dir: Path, processed_dir: Path) -> Path:
    """Run daily feature engineering and save features_daily.csv."""
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    df_features = compute_daily_features(raw_dir, processed_dir)
    out_file = processed_dir / "features_daily.csv"
    df_features.to_csv(out_file, index=False)
    logger.info(f"Saved {out_file} with {len(df_features)} rows and {len(df_features.columns)} columns.")
    return out_file
