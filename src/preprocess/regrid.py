"""Regridding and Spatial Alignment Module (Track A - Task 2).

Standardizes all NWP forecasts and observation grids to the common 0.25° grid
over the Central India Monsoon Core Zone (18°N–26°N, 74°E–86°E).
Produces:
- data/processed/nwp_grid_gfs.nc
- data/processed/nwp_grid_ecmwf.nc
- data/processed/obs_grid.nc
"""

import logging
from pathlib import Path
import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)

# Common 0.25 deg grid definition
TARGET_LATS = np.arange(18.0, 26.25, 0.25)
TARGET_LONS = np.arange(74.0, 86.25, 0.25)


def regrid_to_target(ds: xr.Dataset, var_in: str, var_out: str = "precip_mm") -> xr.Dataset:
    """Interpolate/align a dataset onto the target lat-lon grid and rename variable."""
    # Standardize coordinate names
    coord_map = {}
    for c in ds.coords:
        if c.lower() in ["latitude", "lat"]:
            coord_map[c] = "lat"
        elif c.lower() in ["longitude", "lon"]:
            coord_map[c] = "lon"
        elif c.lower() in ["time", "dates", "date"]:
            coord_map[c] = "date"

    ds_std = ds.rename(coord_map)

    # Convert date to string YYYY-MM-DD if datetime
    if np.issubdtype(ds_std["date"].dtype, np.datetime64):
        dates = [str(np.datetime_as_string(d, unit="D")) for d in ds_std["date"].values]
        ds_std = ds_std.assign_coords(date=dates)

    # Interpolate to target regular grid if needed
    if not (np.array_equal(ds_std["lat"].values, TARGET_LATS) and np.array_equal(ds_std["lon"].values, TARGET_LONS)):
        ds_interp = ds_std.interp(lat=TARGET_LATS, lon=TARGET_LONS, method="linear")
    else:
        ds_interp = ds_std

    # Extract variable and ensure correct name and float32 dtype
    precip_arr = np.maximum(0.0, ds_interp[var_in].values).astype(np.float32)

    ds_out = xr.Dataset(
        data_vars={var_out: (("date", "lat", "lon"), precip_arr)},
        coords={
            "date": ds_interp["date"].values,
            "lat": TARGET_LATS,
            "lon": TARGET_LONS,
        },
        attrs={
            "domain": "Central India Monsoon Core Zone",
            "resolution": "0.25x0.25 deg regular grid",
            "units": "mm/day",
        },
    )
    return ds_out


def run_regridding(raw_dir: Path, processed_dir: Path) -> None:
    """Run regridding for both NWP sources and gridded observations."""
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = Path(raw_dir)

    encoding = {"precip_mm": {"zlib": True, "complevel": 4, "dtype": "float32"}}

    # 1. GFS
    raw_gfs_nc = raw_dir / "nwp_gfs" / "gfs_raw_forecasts.nc"
    if not raw_gfs_nc.exists():
        raise FileNotFoundError(f"Missing raw GFS file: {raw_gfs_nc}")
    ds_gfs_raw = xr.open_dataset(raw_gfs_nc)
    ds_gfs_proc = regrid_to_target(ds_gfs_raw, var_in="precip_raw", var_out="precip_mm")
    out_gfs = processed_dir / "nwp_grid_gfs.nc"
    ds_gfs_proc.to_netcdf(out_gfs, encoding=encoding)
    logger.info(f"Saved {out_gfs} with sizes {dict(ds_gfs_proc.sizes)} and var 'precip_mm'")

    # 2. ECMWF
    raw_ecmwf_nc = raw_dir / "nwp_ecmwf" / "ecmwf_raw_forecasts.nc"
    if not raw_ecmwf_nc.exists():
        raise FileNotFoundError(f"Missing raw ECMWF file: {raw_ecmwf_nc}")
    ds_ecmwf_raw = xr.open_dataset(raw_ecmwf_nc)
    ds_ecmwf_proc = regrid_to_target(ds_ecmwf_raw, var_in="precip_raw", var_out="precip_mm")
    out_ecmwf = processed_dir / "nwp_grid_ecmwf.nc"
    ds_ecmwf_proc.to_netcdf(out_ecmwf, encoding=encoding)
    logger.info(f"Saved {out_ecmwf} with sizes {dict(ds_ecmwf_proc.sizes)} and var 'precip_mm'")

    # 3. Gridded Obs
    raw_obs_nc = raw_dir / "obs_gridded" / "imd_obs_raw.nc"
    if not raw_obs_nc.exists():
        raise FileNotFoundError(f"Missing raw Obs file: {raw_obs_nc}")
    ds_obs_raw = xr.open_dataset(raw_obs_nc)
    ds_obs_proc = regrid_to_target(ds_obs_raw, var_in="precip_raw", var_out="precip_mm")
    out_obs = processed_dir / "obs_grid.nc"
    ds_obs_proc.to_netcdf(out_obs, encoding=encoding)
    logger.info(f"Saved {out_obs} with sizes {dict(ds_obs_proc.sizes)} and var 'precip_mm'")
