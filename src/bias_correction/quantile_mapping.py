"""Quantile Mapping Module for Precipitation Bias Correction (Track B - Task 4).

Implements empirical quantile mapping (QM) at both global and weather-regime-conditioned levels.
Preserves non-negativity, robustly handles missing/NaN data, and provides reliable fallbacks
when sample sizes per regime are limited.
"""

import logging
from typing import Dict, Optional, Tuple
import numpy as np
import xarray as xr

logger = logging.getLogger("quantile_mapping")


class EmpiricalQuantileMapper:
    """Non-parametric empirical quantile mapper for 1D/grid precipitation distributions."""

    def __init__(self, num_quantiles: int = 100, min_samples: int = 5):
        self.num_quantiles = num_quantiles
        self.min_samples = min_samples
        self.q_levels = np.linspace(0.0, 100.0, num_quantiles)
        self.f_quantiles: Optional[np.ndarray] = None
        self.o_quantiles: Optional[np.ndarray] = None
        self.is_fitted = False

    def fit(self, forecast: np.ndarray, observed: np.ndarray) -> "EmpiricalQuantileMapper":
        """Fit empirical quantile-quantile transfer function from historical forecast & obs."""
        f_flat = np.asarray(forecast).flatten()
        o_flat = np.asarray(observed).flatten()

        valid_mask = (~np.isnan(f_flat)) & (~np.isnan(o_flat))
        f_valid = f_flat[valid_mask]
        o_valid = o_flat[valid_mask]

        if len(f_valid) < self.min_samples:
            logger.warning(
                f"Insufficient valid samples ({len(f_valid)} < {self.min_samples}) for QM fit. "
                "Defaulting to identity transfer."
            )
            self.f_quantiles = np.linspace(0.0, 100.0, self.num_quantiles)
            self.o_quantiles = np.linspace(0.0, 100.0, self.num_quantiles)
            self.is_fitted = True
            return self

        # Calculate empirical percentiles
        self.f_quantiles = np.percentile(f_valid, self.q_levels)
        self.o_quantiles = np.percentile(o_valid, self.q_levels)

        # Ensure monotonicity for stable interpolation
        self.f_quantiles = np.maximum.accumulate(self.f_quantiles)
        self.o_quantiles = np.maximum.accumulate(self.o_quantiles)

        self.is_fitted = True
        return self

    def transform(self, forecast: np.ndarray) -> np.ndarray:
        """Apply quantile mapping to correct forecast precipitation values."""
        if not self.is_fitted or self.f_quantiles is None or self.o_quantiles is None:
            raise RuntimeError("Quantile mapper must be fitted before transform.")

        f_arr = np.asarray(forecast, dtype=np.float32)
        nan_mask = np.isnan(f_arr)

        if np.all(nan_mask):
            return f_arr.copy()

        # Perform 1D quantile interpolation on valid values
        valid_vals = f_arr[~nan_mask]

        # Interpolate within the empirical quantile range
        corrected_valid = np.interp(
            valid_vals,
            self.f_quantiles,
            self.o_quantiles,
            left=float(self.o_quantiles[0]),
            right=float(self.o_quantiles[-1]),
        )

        # For extreme values beyond the 100th percentile, preserve the difference / additive tail
        f_max = self.f_quantiles[-1]
        o_max = self.o_quantiles[-1]
        high_tail_mask = valid_vals > f_max
        if np.any(high_tail_mask):
            corrected_valid[high_tail_mask] = o_max + np.maximum(0.0, valid_vals[high_tail_mask] - f_max)

        # Enforce physical non-negativity
        corrected_valid = np.maximum(0.0, corrected_valid)

        out = np.full_like(f_arr, np.nan, dtype=np.float32)
        out[~nan_mask] = corrected_valid
        return out


class RegimeConditionedQuantileMapper:
    """Regime-aware quantile mapping router with per-regime models and global fallback."""

    def __init__(self, num_quantiles: int = 100, min_samples_per_regime: int = 20):
        self.num_quantiles = num_quantiles
        self.min_samples_per_regime = min_samples_per_regime
        self.global_mapper = EmpiricalQuantileMapper(num_quantiles=num_quantiles)
        self.regime_mappers: Dict[str, EmpiricalQuantileMapper] = {}
        self.regime_sample_counts: Dict[str, int] = {}
        self.is_fitted = False

    def fit(
        self,
        ds_forecast: xr.Dataset,
        ds_obs: xr.Dataset,
        dates: np.ndarray,
        dominant_regimes: np.ndarray,
        var_fcst: str = "precip_mm_ensemble",
        var_obs: str = "precip_mm",
    ) -> "RegimeConditionedQuantileMapper":
        """Fit quantile mapping transfer functions per weather regime."""
        f_vals = ds_forecast[var_fcst].values
        o_vals = ds_obs[var_obs].values

        # 1. Fit global mapper on all available data
        self.global_mapper.fit(f_vals, o_vals)

        # 2. Fit per-regime mappers where sample counts suffice
        unique_regimes = np.unique([str(r) for r in dominant_regimes if pd_not_na(r)])

        for regime in unique_regimes:
            date_mask = np.array([str(r) == regime for r in dominant_regimes])
            f_regime = f_vals[date_mask]
            o_regime = o_vals[date_mask]

            num_valid = np.sum((~np.isnan(f_regime)) & (~np.isnan(o_regime)))
            self.regime_sample_counts[regime] = int(num_valid)

            if num_valid >= self.min_samples_per_regime:
                mapper = EmpiricalQuantileMapper(num_quantiles=self.num_quantiles)
                mapper.fit(f_regime, o_regime)
                self.regime_mappers[regime] = mapper
                logger.info(f"Fitted dedicated QM for regime '{regime}' ({num_valid} valid grid-days).")
            else:
                logger.info(
                    f"Regime '{regime}' has {num_valid} valid grid-days (< {self.min_samples_per_regime}); "
                    "will use global QM fallback."
                )

        self.is_fitted = True
        return self

    def transform_slice(
        self,
        forecast_slice: np.ndarray,
        regime: str,
    ) -> Tuple[np.ndarray, str]:
        """Correct a 2D spatial slice given the prevailing regime.

        Returns (corrected_array, method_used_string).
        """
        if not self.is_fitted:
            raise RuntimeError("RegimeConditionedQuantileMapper must be fitted before transform.")

        if regime in self.regime_mappers:
            corrected = self.regime_mappers[regime].transform(forecast_slice)
            method = f"quantile_mapping_regime_{regime}"
        else:
            corrected = self.global_mapper.transform(forecast_slice)
            method = "quantile_mapping_global_fallback"

        return corrected, method


def pd_not_na(val) -> bool:
    """Helper to check for non-NA/None/empty strings."""
    if val is None:
        return False
    if isinstance(val, float) and np.isnan(val):
        return False
    if str(val).strip() == "" or str(val).lower() == "nan":
        return False
    return True
