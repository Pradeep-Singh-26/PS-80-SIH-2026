"""Multi-NWP Ensemble Blending Module (Track B - Task 4).

Fuses multi-source NWP rainfall forecasts (e.g., GFS and ECMWF) into a unified
ensemble precipitation grid (precip_mm_ensemble).

Contract inputs:
- data/processed/nwp_grid_gfs.nc (dims: date, lat, lon; var: precip_mm)
- data/processed/nwp_grid_ecmwf.nc (dims: date, lat, lon; var: precip_mm)

Contract output:
- data/processed/ensemble_grid.nc (dims: date, lat, lon; var: precip_mm_ensemble)
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import xarray as xr

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ensemble_blender")


def validate_inputs(
    ds_gfs: xr.Dataset,
    ds_ecmwf: xr.Dataset,
    var_name: str = "precip_mm",
) -> None:
    """Validate that input datasets conform to expected contracts.

    Parameters
    ----------
    ds_gfs : xr.Dataset
        GFS NWP dataset.
    ds_ecmwf : xr.Dataset
        ECMWF NWP dataset.
    var_name : str
        Required precipitation variable name.

    Raises
    ------
    ValueError
        If variables, dimensions, or coordinates are incompatible or missing.
    """
    # 1. Variable check
    if var_name not in ds_gfs.data_vars:
        raise ValueError(
            f"GFS dataset missing required variable '{var_name}'. "
            f"Available variables: {list(ds_gfs.data_vars)}"
        )
    if var_name not in ds_ecmwf.data_vars:
        raise ValueError(
            f"ECMWF dataset missing required variable '{var_name}'. "
            f"Available variables: {list(ds_ecmwf.data_vars)}"
        )

    # 2. Dimensions check
    expected_dims = ("date", "lat", "lon")
    for dim in expected_dims:
        if dim not in ds_gfs.dims:
            raise ValueError(f"GFS dataset missing required dimension '{dim}'. Dims: {list(ds_gfs.dims)}")
        if dim not in ds_ecmwf.dims:
            raise ValueError(f"ECMWF dataset missing required dimension '{dim}'. Dims: {list(ds_ecmwf.dims)}")

    # 3. Coordinate shape check
    if ds_gfs.sizes != ds_ecmwf.sizes:
        raise ValueError(
            f"Dimension size mismatch between GFS {dict(ds_gfs.sizes)} and ECMWF {dict(ds_ecmwf.sizes)}"
        )

    # 4. Coordinate alignment check
    for coord in ("lat", "lon"):
        if not np.allclose(ds_gfs[coord].values, ds_ecmwf[coord].values, atol=1e-4):
            raise ValueError(f"Coordinate mismatch on '{coord}' between GFS and ECMWF grids.")

    # 5. Date coordinate alignment
    gfs_dates = ds_gfs["date"].values
    ecmwf_dates = ds_ecmwf["date"].values
    if len(gfs_dates) != len(ecmwf_dates) or not np.array_equal(gfs_dates, ecmwf_dates):
        raise ValueError("Time/date coordinate mismatch between GFS and ECMWF datasets.")

    logger.info("Input validation passed: GFS and ECMWF datasets are structurally aligned.")


def blend_forecasts(
    ds_gfs: xr.Dataset,
    ds_ecmwf: xr.Dataset,
    w_gfs: float = 0.5,
    w_ecmwf: float = 0.5,
    var_name: str = "precip_mm",
) -> xr.Dataset:
    """Fuse GFS and ECMWF forecast grids using scientific weighted blending.

    Handles missing data without silently treating missing values as zero:
    - Where both models have valid forecasts: weighted blend (w_gfs * GFS + w_ecmwf * ECMWF).
    - Where only one model is valid: fall back to the available model value.
    - Where both are NaN: preserve NaN.
    - Non-negativity is strictly enforced for physical realism.

    Parameters
    ----------
    ds_gfs : xr.Dataset
        Input GFS dataset.
    ds_ecmwf : xr.Dataset
        Input ECMWF dataset.
    w_gfs : float, default=0.5
        Blending weight for GFS.
    w_ecmwf : float, default=0.5
        Blending weight for ECMWF.
    var_name : str, default='precip_mm'
        Variable name for precipitation in input datasets.

    Returns
    -------
    xr.Dataset
        Fused ensemble dataset containing 'precip_mm_ensemble'.
    """
    validate_inputs(ds_gfs, ds_ecmwf, var_name=var_name)

    if w_gfs < 0 or w_ecmwf < 0:
        raise ValueError(f"Weights must be non-negative. Got w_gfs={w_gfs}, w_ecmwf={w_ecmwf}")

    total_weight = w_gfs + w_ecmwf
    if total_weight <= 0:
        raise ValueError("Sum of weights must be greater than zero.")

    # Normalize weights
    norm_w_gfs = float(w_gfs / total_weight)
    norm_w_ecmwf = float(w_ecmwf / total_weight)

    gfs_data = ds_gfs[var_name].values.astype(np.float32)
    ecmwf_data = ds_ecmwf[var_name].values.astype(np.float32)

    gfs_valid = ~np.isnan(gfs_data)
    ecmwf_valid = ~np.isnan(ecmwf_data)

    both_valid = gfs_valid & ecmwf_valid
    only_gfs = gfs_valid & (~ecmwf_valid)
    only_ecmwf = (~gfs_valid) & ecmwf_valid

    # Pre-allocate output array with NaNs
    blended = np.full_like(gfs_data, np.nan, dtype=np.float32)

    # Blend where both valid
    blended[both_valid] = (norm_w_gfs * gfs_data[both_valid]) + (norm_w_ecmwf * ecmwf_data[both_valid])

    # Single-model fallbacks
    blended[only_gfs] = gfs_data[only_gfs]
    blended[only_ecmwf] = ecmwf_data[only_ecmwf]

    # Enforce physical non-negativity where not NaN
    valid_mask = ~np.isnan(blended)
    blended[valid_mask] = np.maximum(0.0, blended[valid_mask])

    # Build output xarray Dataset
    coords = {
        "date": ds_gfs["date"].values,
        "lat": ds_gfs["lat"].values,
        "lon": ds_gfs["lon"].values,
    }

    ds_ensemble = xr.Dataset(
        data_vars={
            "precip_mm_ensemble": (("date", "lat", "lon"), blended),
        },
        coords=coords,
        attrs={
            "title": "Multi-NWP Blended Ensemble Precipitation Forecast",
            "method": "weighted_linear_blend",
            "gfs_weight": norm_w_gfs,
            "ecmwf_weight": norm_w_ecmwf,
            "units": "mm/day",
            "source_models": "GFS, ECMWF",
            "missing_data_policy": "Single-model fallback when one source is NaN; preserve NaN when both missing",
            "created_by": "Track B - Ensemble Blender (Baljeet)",
        },
    )

    # Add variable-level metadata
    ds_ensemble["precip_mm_ensemble"].attrs = {
        "long_name": "Multi-model ensemble daily precipitation forecast",
        "units": "mm/day",
        "standard_name": "precipitation_flux",
    }

    return ds_ensemble


def run_ensemble_blending(
    gfs_path: Path | str,
    ecmwf_path: Path | str,
    output_path: Path | str,
    w_gfs: float = 0.5,
    w_ecmwf: float = 0.5,
    var_name: str = "precip_mm",
) -> xr.Dataset:
    """Load NWP inputs, perform ensemble blending, and save NetCDF output.

    Parameters
    ----------
    gfs_path : Path | str
        Path to GFS NetCDF file.
    ecmwf_path : Path | str
        Path to ECMWF NetCDF file.
    output_path : Path | str
        Destination path for ensemble_grid.nc.
    w_gfs : float, default=0.5
        Weight for GFS.
    w_ecmwf : float, default=0.5
        Weight for ECMWF.
    var_name : str, default='precip_mm'
        Variable name in input files.

    Returns
    -------
    xr.Dataset
        The generated ensemble dataset.
    """
    gfs_path = Path(gfs_path)
    ecmwf_path = Path(ecmwf_path)
    output_path = Path(output_path)

    if not gfs_path.exists():
        raise FileNotFoundError(f"GFS NetCDF input not found at: {gfs_path}")
    if not ecmwf_path.exists():
        raise FileNotFoundError(f"ECMWF NetCDF input not found at: {ecmwf_path}")

    logger.info(f"Loading GFS forecast from: {gfs_path}")
    ds_gfs = xr.open_dataset(gfs_path)

    logger.info(f"Loading ECMWF forecast from: {ecmwf_path}")
    ds_ecmwf = xr.open_dataset(ecmwf_path)

    logger.info(f"Blending NWP models with weights: GFS={w_gfs}, ECMWF={w_ecmwf}...")
    ds_ensemble = blend_forecasts(
        ds_gfs=ds_gfs,
        ds_ecmwf=ds_ecmwf,
        w_gfs=w_gfs,
        w_ecmwf=w_ecmwf,
        var_name=var_name,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoding = {"precip_mm_ensemble": {"zlib": True, "complevel": 4, "dtype": "float32"}}

    logger.info(f"Saving fused ensemble dataset to: {output_path}")
    ds_ensemble.to_netcdf(output_path, encoding=encoding)
    logger.info(f"Successfully created {output_path} with sizes {dict(ds_ensemble.sizes)}")

    # Close input datasets
    ds_gfs.close()
    ds_ecmwf.close()

    return ds_ensemble


def main():
    parser = argparse.ArgumentParser(description="Track B (Baljeet) - Multi-NWP Ensemble Blender")
    parser.add_argument(
        "--gfs",
        type=str,
        default=None,
        help="Path to GFS NetCDF file (default: data/processed/nwp_grid_gfs.nc)",
    )
    parser.add_argument(
        "--ecmwf",
        type=str,
        default=None,
        help="Path to ECMWF NetCDF file (default: data/processed/nwp_grid_ecmwf.nc)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for output ensemble grid (default: data/processed/ensemble_grid.nc)",
    )
    parser.add_argument(
        "--w_gfs",
        type=float,
        default=0.5,
        help="Blending weight for GFS (default: 0.5)",
    )
    parser.add_argument(
        "--w_ecmwf",
        type=float,
        default=0.5,
        help="Blending weight for ECMWF (default: 0.5)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent.parent

    gfs_path = Path(args.gfs) if args.gfs else project_root / "data" / "processed" / "nwp_grid_gfs.nc"
    ecmwf_path = Path(args.ecmwf) if args.ecmwf else project_root / "data" / "processed" / "nwp_grid_ecmwf.nc"
    output_path = Path(args.output) if args.output else project_root / "data" / "processed" / "ensemble_grid.nc"

    run_ensemble_blending(
        gfs_path=gfs_path,
        ecmwf_path=ecmwf_path,
        output_path=output_path,
        w_gfs=args.w_gfs,
        w_ecmwf=args.w_ecmwf,
    )


if __name__ == "__main__":
    main()
