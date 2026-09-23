"""Analog-Based Bias Correction Pipeline (Track B - Task 4).

Generates independent analog-based precipitation forecast corrections:
1. Indexes synoptic feature vectors and regimes across historical dates.
2. Identifies top-k atmospheric analog days with same-regime preference and zero-leakage constraints.
3. Transfers empirical forecast errors (Obs - Ensemble) weighted by inverse similarity distance.
4. Generates analog_correction.nc (precip_mm_analog_estimate) and analog_match_log.csv.
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xarray as xr

from .similarity import AnalogSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("analog_corrector")


class AnalogBiasCorrector:
    """Independent historical analog correction model."""

    def __init__(
        self,
        top_k: int = 5,
        min_same_regime: int = 2,
        mode: str = "leave_one_out",
    ):
        self.top_k = top_k
        self.search_engine = AnalogSearchEngine(
            top_k=top_k,
            min_same_regime=min_same_regime,
            mode=mode,
        )
        self.date_to_error: Dict[str, np.ndarray] = {}
        self.is_indexed = False

    def fit(
        self,
        ds_ensemble: xr.Dataset,
        ds_obs: xr.Dataset,
        df_features: pd.DataFrame,
        df_regimes: pd.DataFrame,
        var_ens: str = "precip_mm_ensemble",
        var_obs: str = "precip_mm",
    ) -> "AnalogBiasCorrector":
        """Index synoptic feature database and pre-calculate spatial historical error fields."""
        logger.info("Building analog synoptic feature search index...")
        self.search_engine.build_index(df_features, df_regimes)

        dates = ds_ensemble["date"].values
        ens_arr = ds_ensemble[var_ens].values
        obs_arr = ds_obs[var_obs].values

        self.date_to_error = {}
        for t_idx, d in enumerate(dates):
            d_str = str(np.datetime_as_string(d, unit="D")) if np.issubdtype(d.dtype, np.datetime64) else str(d)[:10]
            # Spatial forecast error: Obs - Forecast
            e_slice = obs_arr[t_idx] - ens_arr[t_idx]
            self.date_to_error[d_str] = e_slice.astype(np.float32)

        self.is_indexed = True
        logger.info(f"Pre-calculated spatial error maps for {len(self.date_to_error)} dates.")
        return self

    def predict_grid(
        self,
        ds_ensemble: xr.Dataset,
        df_features: pd.DataFrame,
        df_regimes: pd.DataFrame,
        var_ens: str = "precip_mm_ensemble",
    ) -> Tuple[np.ndarray, List[Dict]]:
        """Apply analog error transfer to produce corrected 3D precipitation grids and match logs."""
        if not self.is_indexed:
            raise RuntimeError("AnalogBiasCorrector must be fitted before predict_grid.")

        dates = ds_ensemble["date"].values
        lats = ds_ensemble["lat"].values
        lons = ds_ensemble["lon"].values
        ens_arr = ds_ensemble[var_ens].values

        df_f_indexed = df_features.copy()
        df_f_indexed["date_str"] = pd.to_datetime(df_f_indexed["date"]).dt.strftime("%Y-%m-%d")
        f_lookup = df_f_indexed.set_index("date_str")

        df_r_indexed = df_regimes.copy()
        df_r_indexed["date_str"] = pd.to_datetime(df_r_indexed["date"]).dt.strftime("%Y-%m-%d")
        r_lookup = df_r_indexed.set_index("date_str")

        n_dates = len(dates)
        n_lats = len(lats)
        n_lons = len(lons)

        out_arr = np.full((n_dates, n_lats, n_lons), np.nan, dtype=np.float32)
        match_logs = []

        for t_idx, d in enumerate(dates):
            d_str = str(np.datetime_as_string(d, unit="D")) if np.issubdtype(d.dtype, np.datetime64) else str(d)[:10]
            fcst_slice = ens_arr[t_idx]

            # Extract target features and regime
            f_row = f_lookup.loc[d_str].to_dict() if d_str in f_lookup.index else {}
            regime = str(r_lookup.loc[d_str].get("dominant_label", "unknown")) if d_str in r_lookup.index else "unknown"

            # Search top-k analogs
            match = self.search_engine.find_analogs(
                target_date=d_str,
                target_dict=f_row,
                target_regime=regime,
            )

            analog_dates = match["analog_dates"]
            weights = match["weights"]

            if len(analog_dates) == 0:
                # No analog available fallback
                logger.warning(f"No valid analogs found for {d_str}; using uncorrected forecast.")
                corrected_slice = fcst_slice.copy()
                mean_corr_term = 0.0
            else:
                # Compute weighted error transfer field
                estimated_error = np.zeros((n_lats, n_lons), dtype=np.float32)
                valid_weight_sum = 0.0

                for a_date, w in zip(analog_dates, weights):
                    if a_date in self.date_to_error:
                        err_map = self.date_to_error[a_date]
                        # Where error map is valid, add weighted contribution
                        err_valid = ~np.isnan(err_map)
                        estimated_error[err_valid] += w * err_map[err_valid]
                        valid_weight_sum += w

                if valid_weight_sum > 0:
                    estimated_error /= valid_weight_sum

                # Apply correction: Forecast + Estimated Error
                corrected_slice = fcst_slice + estimated_error
                mean_corr_term = float(np.nanmean(estimated_error))

            # Enforce physical non-negativity where valid
            valid_m = ~np.isnan(corrected_slice)
            corrected_slice[valid_m] = np.maximum(0.0, corrected_slice[valid_m])
            out_arr[t_idx] = corrected_slice

            match_logs.append({
                "date": d_str,
                "regime": regime,
                "analog_dates": ";".join(analog_dates),
                "analog_regimes": ";".join(match["analog_regimes"]),
                "distances": ";".join([str(x) for x in match["distances"]]),
                "weights": ";".join([str(x) for x in match["weights"]]),
                "mean_correction_mm": round(mean_corr_term, 4),
                "fallback_used": match["fallback_used"],
                "match_status": match["message"],
            })

        return out_arr, match_logs


def run_analog_correction_pipeline(
    ensemble_path: Path | str,
    obs_path: Path | str,
    features_daily_path: Path | str,
    regime_preds_path: Path | str,
    output_grid_path: Path | str,
    output_log_path: Path | str,
    top_k: int = 5,
    mode: str = "leave_one_out",
) -> Tuple[xr.Dataset, pd.DataFrame]:
    """Execute end-to-end analog-based correction pipeline."""
    ensemble_path = Path(ensemble_path)
    obs_path = Path(obs_path)
    features_daily_path = Path(features_daily_path)
    regime_preds_path = Path(regime_preds_path)
    output_grid_path = Path(output_grid_path)
    output_log_path = Path(output_log_path)

    for p, name in [
        (ensemble_path, "Ensemble Grid"),
        (obs_path, "Obs Grid"),
        (features_daily_path, "Daily Features"),
        (regime_preds_path, "Regime Predictions"),
    ]:
        if not p.exists():
            raise FileNotFoundError(f"Required input {name} not found at: {p}")

    logger.info(f"Loading datasets for Analog Correction: {ensemble_path.name}, {obs_path.name}")
    ds_ens = xr.open_dataset(ensemble_path)
    ds_obs = xr.open_dataset(obs_path)
    df_feat = pd.read_csv(features_daily_path)
    df_reg = pd.read_csv(regime_preds_path)

    corrector = AnalogBiasCorrector(top_k=top_k, mode=mode)
    corrector.fit(
        ds_ensemble=ds_ens,
        ds_obs=ds_obs,
        df_features=df_feat,
        df_regimes=df_reg,
    )

    logger.info("Computing analog corrections across all dates...")
    analog_arr, match_logs = corrector.predict_grid(
        ds_ensemble=ds_ens,
        df_features=df_feat,
        df_regimes=df_reg,
    )

    # Build output NetCDF dataset
    ds_analog = xr.Dataset(
        data_vars={
            "precip_mm_analog_estimate": (("date", "lat", "lon"), analog_arr),
        },
        coords={
            "date": ds_ens["date"].values,
            "lat": ds_ens["lat"].values,
            "lon": ds_ens["lon"].values,
        },
        attrs={
            "title": "Independent Analog-Based Precipitation Forecast Estimate",
            "method": "Multi-variable synoptic analog error transfer",
            "distance_metric": "Standardized Euclidean distance with regime conditioning",
            "top_k": int(top_k),
            "search_mode": mode,
            "leakage_prevention": "Target date strictly excluded from historical candidate pool",
            "units": "mm/day",
            "created_by": "Track B - Analog Bias Corrector (Baljeet)",
        },
    )

    ds_analog["precip_mm_analog_estimate"].attrs = {
        "long_name": "Analog-based empirical precipitation estimate",
        "units": "mm/day",
        "standard_name": "precipitation_flux",
    }

    output_grid_path.parent.mkdir(parents=True, exist_ok=True)
    output_log_path.parent.mkdir(parents=True, exist_ok=True)

    encoding = {"precip_mm_analog_estimate": {"zlib": True, "complevel": 4, "dtype": "float32"}}
    logger.info(f"Saving analog correction dataset to: {output_grid_path}")
    ds_analog.to_netcdf(output_grid_path, encoding=encoding)

    df_log = pd.DataFrame(match_logs)
    logger.info(f"Saving analog match diagnostics to: {output_log_path}")
    df_log.to_csv(output_log_path, index=False)

    ds_ens.close()
    ds_obs.close()

    logger.info("Analog-based correction pipeline completed successfully.")
    return ds_analog, df_log


def main():
    parser = argparse.ArgumentParser(description="Track B (Baljeet) - Analog-Based Correction Runner")
    parser.add_argument("--ensemble", type=str, default=None, help="Path to ensemble_grid.nc")
    parser.add_argument("--obs", type=str, default=None, help="Path to obs_grid.nc")
    parser.add_argument("--features", type=str, default=None, help="Path to features_daily.csv")
    parser.add_argument("--regime_preds", type=str, default=None, help="Path to regime_predictions.csv")
    parser.add_argument("--output_grid", type=str, default=None, help="Path for analog_correction.nc")
    parser.add_argument("--output_log", type=str, default=None, help="Path for analog_match_log.csv")
    parser.add_argument("--top_k", type=int, default=5, help="Number of analog days (default: 5)")
    parser.add_argument("--mode", type=str, default="leave_one_out", choices=["leave_one_out", "strict_chronological"])
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    processed_dir = project_root / "data" / "processed"

    ensemble_path = Path(args.ensemble) if args.ensemble else processed_dir / "ensemble_grid.nc"
    obs_path = Path(args.obs) if args.obs else processed_dir / "obs_grid.nc"
    features_path = Path(args.features) if args.features else processed_dir / "features_daily.csv"
    regime_preds_path = Path(args.regime_preds) if args.regime_preds else processed_dir / "regime_predictions.csv"
    output_grid = Path(args.output_grid) if args.output_grid else processed_dir / "analog_correction.nc"
    output_log = Path(args.output_log) if args.output_log else processed_dir / "analog_match_log.csv"

    run_analog_correction_pipeline(
        ensemble_path=ensemble_path,
        obs_path=obs_path,
        features_daily_path=features_path,
        regime_preds_path=regime_preds_path,
        output_grid_path=output_grid,
        output_log_path=output_log,
        top_k=args.top_k,
        mode=args.mode,
    )


if __name__ == "__main__":
    main()
