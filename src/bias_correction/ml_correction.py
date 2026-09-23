"""ML Gradient Boosted Correction Module (Track B - Task 4).

Trains a gradient-boosted regressor to correct multi-NWP ensemble forecasts using
physical, dynamical, thermodynamical, climatological, and regime-probability features.
Uses strictly chronological train/validation splitting to avoid temporal data leakage.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xarray as xr
from sklearn.ensemble import HistGradientBoostingRegressor

logger = logging.getLogger("ml_correction")

# Exact feature list from contracted inputs
STATIC_SPATIAL_FEATURES = ["lat", "lon", "precip_clim"]
REGIME_PROB_FEATURES = [
    "active_prob",
    "break_prob",
    "low_depression_prob",
    "western_disturbance_prob",
    "orographic_prob",
    "coastal_prob",
    "confidence",
]
DYNAMICAL_FEATURES = [
    "mslp_anomaly",
    "olr_anomaly",
    "satellite_proxy",
    "rainfall_anomaly",
    "lps_flag",
    "wd_flag",
    "u850_anomaly",
    "v850_anomaly",
]


class MLGradientBoostedCorrector:
    """Gradient-boosted regression model for regime-aware forecast bias correction."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = HistGradientBoostingRegressor(
            loss="squared_error",
            max_iter=150,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            random_state=random_state,
        )
        self.feature_names: List[str] = []
        self.is_fitted = False
        self.train_metrics: Dict[str, float] = {}
        self.val_metrics: Dict[str, float] = {}

    def _build_tabular_features(
        self,
        ds_ens: xr.Dataset,
        ds_clim: xr.Dataset,
        df_reg: pd.DataFrame,
        df_feat: pd.DataFrame,
        ds_obs: Optional[xr.Dataset] = None,
        var_ens: str = "precip_mm_ensemble",
        var_obs: str = "precip_mm",
    ) -> Tuple[pd.DataFrame, Optional[np.ndarray], List[Tuple[str, float, float]]]:
        """Flatten 3D spatio-temporal grids into aligned 2D tabular features for ML."""
        dates = ds_ens["date"].values
        lats = ds_ens["lat"].values
        lons = ds_ens["lon"].values

        ens_arr = ds_ens[var_ens].values  # (date, lat, lon)
        clim_arr = ds_clim["precip_mm_clim"].values  # (lat, lon)
        obs_arr = ds_obs[var_obs].values if ds_obs is not None else None

        # Standardize date column in metadata dataframes to string YYYY-MM-DD
        df_reg_std = df_reg.copy()
        df_reg_std["date_str"] = pd.to_datetime(df_reg_std["date"]).dt.strftime("%Y-%m-%d")
        reg_indexed = df_reg_std.set_index("date_str")

        df_feat_std = df_feat.copy()
        df_feat_std["date_str"] = pd.to_datetime(df_feat_std["date"]).dt.strftime("%Y-%m-%d")
        feat_indexed = df_feat_std.set_index("date_str")

        rows = []
        targets = [] if obs_arr is not None else None
        index_tuples = []  # (date_str, lat, lon)

        for t_idx, d in enumerate(dates):
            d_str = str(np.datetime_as_string(d, unit="D")) if np.issubdtype(d.dtype, np.datetime64) else str(d)[:10]

            # Extract daily regime and dynamical features
            reg_row = reg_indexed.loc[d_str] if d_str in reg_indexed.index else pd.Series(dtype=float)
            feat_row = feat_indexed.loc[d_str] if d_str in feat_indexed.index else pd.Series(dtype=float)

            reg_dict = {
                col: float(reg_row[col]) if col in reg_row and pd.notna(reg_row[col]) else 0.0
                for col in REGIME_PROB_FEATURES
            }
            dyn_dict = {
                col: float(feat_row[col]) if col in feat_row and pd.notna(feat_row[col]) else 0.0
                for col in DYNAMICAL_FEATURES
            }

            for lat_idx, lat_val in enumerate(lats):
                for lon_idx, lon_val in enumerate(lons):
                    ens_val = ens_arr[t_idx, lat_idx, lon_idx]
                    clim_val = clim_arr[t_idx, lat_idx, lon_idx] if clim_arr.ndim == 3 else clim_arr[lat_idx, lon_idx]

                    row = {
                        "precip_ensemble": float(ens_val),
                        "lat": float(lat_val),
                        "lon": float(lon_val),
                        "precip_clim": float(clim_val),
                        **reg_dict,
                        **dyn_dict,
                    }
                    rows.append(row)
                    index_tuples.append((d_str, float(lat_val), float(lon_val)))

                    if obs_arr is not None:
                        targets.append(float(obs_arr[t_idx, lat_idx, lon_idx]))

        df_out = pd.DataFrame(rows)
        targets_arr = np.array(targets, dtype=np.float32) if targets is not None else None
        return df_out, targets_arr, index_tuples

    def fit(
        self,
        ds_ens: xr.Dataset,
        ds_obs: xr.Dataset,
        ds_clim: xr.Dataset,
        df_reg: pd.DataFrame,
        df_feat: pd.DataFrame,
        train_ratio: float = 0.75,
    ) -> "MLGradientBoostedCorrector":
        """Fit ML bias corrector using strictly chronological train/validation partition."""
        df_X, y, index_tuples = self._build_tabular_features(
            ds_ens=ds_ens,
            ds_clim=ds_clim,
            df_reg=df_reg,
            df_feat=df_feat,
            ds_obs=ds_obs,
        )

        self.feature_names = df_X.columns.tolist()

        # Valid mask (drop samples where ensemble or observation is NaN)
        valid_mask = (~df_X["precip_ensemble"].isna()) & (~np.isnan(y))
        df_X_valid = df_X[valid_mask].copy()
        y_valid = y[valid_mask]
        dates_valid = [t[0] for t, m in zip(index_tuples, valid_mask) if m]

        # Chronological split on unique dates
        unique_dates = sorted(list(set(dates_valid)))
        split_idx = max(1, int(len(unique_dates) * train_ratio))
        train_dates = set(unique_dates[:split_idx])
        val_dates = set(unique_dates[split_idx:])

        train_mask = np.array([d in train_dates for d in dates_valid])
        val_mask = np.array([d in val_dates for d in dates_valid])

        X_train, y_train = df_X_valid[train_mask], y_valid[train_mask]
        X_val, y_val = df_X_valid[val_mask], y_valid[val_mask]

        logger.info(
            f"Training ML Corrector: {len(X_train)} train samples ({len(train_dates)} days), "
            f"{len(X_val)} val samples ({len(val_dates)} days)."
        )

        self.model.fit(X_train, y_train)
        self.is_fitted = True

        # Compute train/val metrics
        train_preds = np.maximum(0.0, self.model.predict(X_train))
        self.train_metrics = {
            "mae": float(np.mean(np.abs(train_preds - y_train))),
            "rmse": float(np.sqrt(np.mean((train_preds - y_train) ** 2))),
            "bias": float(np.mean(train_preds - y_train)),
        }

        if len(X_val) > 0:
            val_preds = np.maximum(0.0, self.model.predict(X_val))
            self.val_metrics = {
                "mae": float(np.mean(np.abs(val_preds - y_val))),
                "rmse": float(np.sqrt(np.mean((val_preds - y_val) ** 2))),
                "bias": float(np.mean(val_preds - y_val)),
            }
            logger.info(
                f"ML Validation Metrics: MAE={self.val_metrics['mae']:.2f}, "
                f"RMSE={self.val_metrics['rmse']:.2f}, Bias={self.val_metrics['bias']:.2f}"
            )

        return self

    def predict_grid(
        self,
        ds_ens: xr.Dataset,
        ds_clim: xr.Dataset,
        df_reg: pd.DataFrame,
        df_feat: pd.DataFrame,
        var_ens: str = "precip_mm_ensemble",
    ) -> np.ndarray:
        """Generate 3D corrected grid array matching (date, lat, lon)."""
        if not self.is_fitted:
            raise RuntimeError("ML model must be fitted before predict_grid.")

        df_X, _, _ = self._build_tabular_features(
            ds_ens=ds_ens,
            ds_clim=ds_clim,
            df_reg=df_reg,
            df_feat=df_feat,
            ds_obs=None,
            var_ens=var_ens,
        )

        nan_mask = df_X["precip_ensemble"].isna()
        preds_flat = np.full(len(df_X), np.nan, dtype=np.float32)

        if not np.all(nan_mask):
            valid_preds = self.model.predict(df_X[~nan_mask])
            preds_flat[~nan_mask] = np.maximum(0.0, valid_preds)

        # Reshape to 3D (date, lat, lon)
        n_dates = len(ds_ens["date"])
        n_lats = len(ds_ens["lat"])
        n_lons = len(ds_ens["lon"])
        return preds_flat.reshape((n_dates, n_lats, n_lons)).astype(np.float32)
