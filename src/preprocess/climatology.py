"""Climatology Calculation Module (Track A - Task 2).

Computes daily smoothed precipitation climatology over the domain.
Produces:
- data/processed/climatology.nc with variable `precip_mm_clim`.
"""

import logging
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

logger = logging.getLogger(__name__)


def compute_climatology(obs_ds: xr.Dataset, window: int = 15) -> xr.Dataset:
    """Compute smoothed daily climatology from multi-year gridded observations.

    Parameters:
        obs_ds: Dataset with variable 'precip_mm' and coords (date, lat, lon).
        window: Centered rolling window in days for smoothing.

    Returns:
        Dataset with variable 'precip_mm_clim' aligned along (date, lat, lon).
    """
    precip = obs_ds["precip_mm"]
    dates = pd.to_datetime(obs_ds["date"].values)
    day_of_years = dates.dayofyear.values

    # Mean for each distinct day of year
    unique_doys = np.unique(day_of_years)
    doy_means = np.zeros((len(unique_doys), len(obs_ds["lat"]), len(obs_ds["lon"])), dtype=np.float32)

    for i, d in enumerate(unique_doys):
        mask = (day_of_years == d)
        doy_means[i] = precip.values[mask].mean(axis=0)

    # Apply circular/periodic rolling mean across the monsoon season days via SciPy
    from scipy.ndimage import uniform_filter1d
    smoothed_doy = uniform_filter1d(doy_means, size=window, axis=0, mode="wrap")

    # Map smoothed DOY back to each date in the dataset vectorially
    doy_to_idx = {d: i for i, d in enumerate(unique_doys)}
    doy_indices = np.array([doy_to_idx[d] for d in day_of_years], dtype=int)
    clim_by_date = smoothed_doy[doy_indices]

    clim_ds = xr.Dataset(
        data_vars={"precip_mm_clim": (("date", "lat", "lon"), clim_by_date.astype(np.float32))},
        coords={
            "date": obs_ds["date"].values,
            "lat": obs_ds["lat"].values,
            "lon": obs_ds["lon"].values,
        },
        attrs={
            "description": f"Daily smoothed {window}-day window rainfall climatology",
            "units": "mm/day",
        },
    )
    return clim_ds


def run_climatology(processed_dir: Path) -> Path:
    """Compute and save climatology.nc from processed obs_grid.nc."""
    processed_dir = Path(processed_dir)
    obs_file = processed_dir / "obs_grid.nc"
    if not obs_file.exists():
        raise FileNotFoundError(f"obs_grid.nc not found in {processed_dir}. Run regrid first.")

    obs_ds = xr.open_dataset(obs_file)
    clim_ds = compute_climatology(obs_ds)

    out_file = processed_dir / "climatology.nc"
    encoding = {"precip_mm_clim": {"zlib": True, "complevel": 4, "dtype": "float32"}}
    clim_ds.to_netcdf(out_file, encoding=encoding)
    logger.info(f"Saved {out_file} with variable 'precip_mm_clim'")
    return out_file
