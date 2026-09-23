"""Master Bias Correction Orchestration Pipeline (Track B - Task 4).

Coordinates:
1. Multi-NWP ensemble input ingestion
2. Regime-conditioned Quantile Mapping calibration
3. Tabular ML Gradient Boosted Regression training
4. Dynamic regime-based routing & method choice logging
5. Generating corrected_grid.nc and correction_method_log.csv
"""

import argparse
import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import xarray as xr

from .ml_correction import MLGradientBoostedCorrector
from .quantile_mapping import RegimeConditionedQuantileMapper
from .router import RegimeBiasCorrectionRouter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bias_corrector")


def run_bias_correction_pipeline(
    ensemble_path: Path | str,
    obs_path: Path | str,
    climatology_path: Path | str,
    regime_preds_path: Path | str,
    features_daily_path: Path | str,
    output_grid_path: Path | str,
    output_log_path: Path | str,
    routing_strategy: str = "regime_conditioned",
    train_ratio: float = 0.75,
) -> Tuple[xr.Dataset, pd.DataFrame]:
    """Execute end-to-end regime-conditioned bias correction.

    Parameters
    ----------
    ensemble_path : Path | str
        Path to data/processed/ensemble_grid.nc.
    obs_path : Path | str
        Path to data/processed/obs_grid.nc.
    climatology_path : Path | str
        Path to data/processed/climatology.nc.
    regime_preds_path : Path | str
        Path to data/processed/regime_predictions.csv.
    features_daily_path : Path | str
        Path to data/processed/features_daily.csv.
    output_grid_path : Path | str
        Output destination for corrected_grid.nc.
    output_log_path : Path | str
        Output destination for correction_method_log.csv.
    routing_strategy : str, default='regime_conditioned'
        Routing policy: 'regime_conditioned', 'all_ml', or 'all_qm'.
    train_ratio : float, default=0.75
        Chronological training ratio for ML and calibration.

    Returns
    -------
    Tuple[xr.Dataset, pd.DataFrame]
        The corrected NetCDF dataset and the decision log DataFrame.
    """
    ensemble_path = Path(ensemble_path)
    obs_path = Path(obs_path)
    climatology_path = Path(climatology_path)
    regime_preds_path = Path(regime_preds_path)
    features_daily_path = Path(features_daily_path)
    output_grid_path = Path(output_grid_path)
    output_log_path = Path(output_log_path)

    # 1. Input existence validation
    for p, name in [
        (ensemble_path, "Ensemble Grid"),
        (obs_path, "Obs Grid"),
        (climatology_path, "Climatology"),
        (regime_preds_path, "Regime Predictions"),
        (features_daily_path, "Daily Features"),
    ]:
        if not p.exists():
            raise FileNotFoundError(f"Required input {name} not found at: {p}")

    logger.info(f"Loading inputs: ensemble={ensemble_path.name}, obs={obs_path.name}")
    ds_ens = xr.open_dataset(ensemble_path)
    ds_obs = xr.open_dataset(obs_path)
    ds_clim = xr.open_dataset(climatology_path)
    df_reg = pd.read_csv(regime_preds_path)
    df_feat = pd.read_csv(features_daily_path)

    dates = ds_ens["date"].values
    lats = ds_ens["lat"].values
    lons = ds_ens["lon"].values

    # Align dates with regime predictions
    df_reg_std = df_reg.copy()
    df_reg_std["date_str"] = pd.to_datetime(df_reg_std["date"]).dt.strftime("%Y-%m-%d")
    reg_lookup = df_reg_std.set_index("date_str")

    dominant_regimes = []
    confidences = []
    for d in dates:
        d_str = str(np.datetime_as_string(d, unit="D")) if np.issubdtype(d.dtype, np.datetime64) else str(d)[:10]
        if d_str in reg_lookup.index:
            row = reg_lookup.loc[d_str]
            dominant_regimes.append(str(row["dominant_label"]) if pd.notna(row["dominant_label"]) else "unknown")
            confidences.append(float(row["confidence"]) if pd.notna(row["confidence"]) else 0.5)
        else:
            dominant_regimes.append("unknown")
            confidences.append(0.5)

    dominant_regimes_arr = np.array(dominant_regimes)
    confidences_arr = np.array(confidences)

    # 2. Fit Quantile Mapping Models
    logger.info("Calibrating Regime-Conditioned Quantile Mapping models...")
    qm_router = RegimeConditionedQuantileMapper(min_samples_per_regime=10)
    qm_router.fit(
        ds_forecast=ds_ens,
        ds_obs=ds_obs,
        dates=dates,
        dominant_regimes=dominant_regimes_arr,
        var_fcst="precip_mm_ensemble",
        var_obs="precip_mm",
    )

    # 3. Fit ML Gradient Boosted Model
    logger.info("Training ML Gradient Boosted Bias Correction model...")
    ml_corrector = MLGradientBoostedCorrector(random_state=42)
    ml_corrector.fit(
        ds_ens=ds_ens,
        ds_obs=ds_obs,
        ds_clim=ds_clim,
        df_reg=df_reg,
        df_feat=df_feat,
        train_ratio=train_ratio,
    )

    # Generate full ML grid predictions
    ml_grid_preds = ml_corrector.predict_grid(
        ds_ens=ds_ens,
        ds_clim=ds_clim,
        df_reg=df_reg,
        df_feat=df_feat,
    )

    # 4. Route and Assemble Corrected Output
    logger.info("Routing daily forecast slices to selected correction methods...")
    router = RegimeBiasCorrectionRouter(routing_strategy=routing_strategy)
    ens_arr = ds_ens["precip_mm_ensemble"].values

    corrected_arr = np.full_like(ens_arr, np.nan, dtype=np.float32)
    decisions = []

    for t_idx, d in enumerate(dates):
        d_str = str(np.datetime_as_string(d, unit="D")) if np.issubdtype(d.dtype, np.datetime64) else str(d)[:10]
        reg = dominant_regimes_arr[t_idx]
        conf = confidences_arr[t_idx]
        fcst_slice = ens_arr[t_idx]

        category, reason = router.route_date(
            date_str=d_str,
            dominant_regime=reg,
            confidence=conf,
        )

        if category == "ml_gbm":
            corrected_slice = ml_grid_preds[t_idx]
            method_used = "ml_gbm"
        else:
            corrected_slice, method_used = qm_router.transform_slice(fcst_slice, reg)

        # Enforce non-negativity where not NaN
        valid_m = ~np.isnan(corrected_slice)
        corrected_slice[valid_m] = np.maximum(0.0, corrected_slice[valid_m])
        corrected_arr[t_idx] = corrected_slice

        decisions.append({
            "date": d_str,
            "regime": reg,
            "confidence": round(conf, 4),
            "method_used": method_used,
            "reason": reason,
        })

    df_log = router.generate_log_df(decisions)

    # 5. Build output xarray Dataset
    ds_corrected = xr.Dataset(
        data_vars={
            "precip_mm_corrected": (("date", "lat", "lon"), corrected_arr),
        },
        coords={
            "date": dates,
            "lat": lats,
            "lon": lons,
        },
        attrs={
            "title": "Regime-Conditioned Bias-Corrected Daily Precipitation Forecast",
            "method_architecture": "Regime-conditioned routing between Quantile Mapping and Gradient Boosting",
            "routing_strategy": routing_strategy,
            "input_source": str(ensemble_path),
            "units": "mm/day",
            "created_by": "Track B - Bias Correction Pipeline (Baljeet)",
        },
    )

    ds_corrected["precip_mm_corrected"].attrs = {
        "long_name": "Bias-corrected daily precipitation forecast",
        "units": "mm/day",
        "standard_name": "precipitation_flux",
    }

    # 6. Save outputs
    output_grid_path.parent.mkdir(parents=True, exist_ok=True)
    output_log_path.parent.mkdir(parents=True, exist_ok=True)

    encoding = {"precip_mm_corrected": {"zlib": True, "complevel": 4, "dtype": "float32"}}
    logger.info(f"Saving corrected grid to {output_grid_path}")
    ds_corrected.to_netcdf(output_grid_path, encoding=encoding)

    logger.info(f"Saving correction method log to {output_log_path}")
    df_log.to_csv(output_log_path, index=False)

    logger.info("Regime-conditioned bias correction completed successfully.")

    ds_ens.close()
    ds_obs.close()
    ds_clim.close()

    return ds_corrected, df_log


def main():
    parser = argparse.ArgumentParser(description="Track B (Baljeet) - Regime-Conditioned Bias Correction Runner")
    parser.add_argument("--ensemble", type=str, default=None, help="Path to ensemble_grid.nc")
    parser.add_argument("--obs", type=str, default=None, help="Path to obs_grid.nc")
    parser.add_argument("--clim", type=str, default=None, help="Path to climatology.nc")
    parser.add_argument("--regime_preds", type=str, default=None, help="Path to regime_predictions.csv")
    parser.add_argument("--features", type=str, default=None, help="Path to features_daily.csv")
    parser.add_argument("--output_grid", type=str, default=None, help="Path for corrected_grid.nc")
    parser.add_argument("--output_log", type=str, default=None, help="Path for correction_method_log.csv")
    parser.add_argument("--strategy", type=str, default="regime_conditioned", choices=["regime_conditioned", "all_ml", "all_qm"])
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    processed_dir = project_root / "data" / "processed"

    ensemble_path = Path(args.ensemble) if args.ensemble else processed_dir / "ensemble_grid.nc"
    obs_path = Path(args.obs) if args.obs else processed_dir / "obs_grid.nc"
    clim_path = Path(args.clim) if args.clim else processed_dir / "climatology.nc"
    regime_preds_path = Path(args.regime_preds) if args.regime_preds else processed_dir / "regime_predictions.csv"
    features_path = Path(args.features) if args.features else processed_dir / "features_daily.csv"
    output_grid = Path(args.output_grid) if args.output_grid else processed_dir / "corrected_grid.nc"
    output_log = Path(args.output_log) if args.output_log else processed_dir / "correction_method_log.csv"

    run_bias_correction_pipeline(
        ensemble_path=ensemble_path,
        obs_path=obs_path,
        climatology_path=clim_path,
        regime_preds_path=regime_preds_path,
        features_daily_path=features_path,
        output_grid_path=output_grid,
        output_log_path=output_log,
        routing_strategy=args.strategy,
    )


if __name__ == "__main__":
    main()
