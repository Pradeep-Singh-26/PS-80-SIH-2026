"""Uncertainty Quantification Module for Rainfall Forecasts (Track B - Task 5).

Estimates probabilistic residual error distributions and uncertainty bounds (lower/upper credible intervals)
conditioned on weather regimes, enforcing mathematical probability constraints (0 <= lower <= central <= upper <= 1).
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import scipy.stats as stats

logger = logging.getLogger("uncertainty_estimator")


class ResidualUncertaintyEstimator:
    """Calibrates historical forecast residual distributions and computes probability bounds."""

    def __init__(
        self,
        min_samples_per_regime: int = 15,
        alpha_interval: float = 0.80,  # 80% credible interval [10th percentile, 90th percentile]
        n_bootstrap: int = 200,
        random_state: int = 42,
    ):
        self.min_samples_per_regime = min_samples_per_regime
        self.alpha_interval = alpha_interval
        self.n_bootstrap = n_bootstrap
        self.rng = np.random.default_rng(random_state)

        self.global_residuals: np.ndarray = np.array([])
        self.regime_residuals: Dict[str, np.ndarray] = {}
        self.is_calibrated = False

    def calibrate(
        self,
        y_fcst_train: np.ndarray,
        y_obs_train: np.ndarray,
        regimes_train: np.ndarray,
    ) -> "ResidualUncertaintyEstimator":
        """Fit empirical residual distributions on the historical calibration partition."""
        f_flat = np.asarray(y_fcst_train).flatten()
        o_flat = np.asarray(y_obs_train).flatten()

        valid_mask = (~np.isnan(f_flat)) & (~np.isnan(o_flat))
        residuals_all = (o_flat - f_flat)[valid_mask]

        if len(residuals_all) == 0:
            logger.warning("Empty calibration partition provided. Using default zero-mean unit residual.")
            self.global_residuals = np.array([0.0], dtype=np.float32)
        else:
            self.global_residuals = residuals_all.astype(np.float32)

        # Fit per-regime residual pools
        unique_regimes = np.unique([str(r).lower().strip() for r in regimes_train if pd_not_na(r)])
        reg_flat = np.repeat(regimes_train, y_fcst_train.shape[1] * y_fcst_train.shape[2]) if y_fcst_train.ndim == 3 else np.asarray(regimes_train).flatten()

        for reg in unique_regimes:
            reg_mask = (reg_flat == reg) & valid_mask
            res_reg = (o_flat - f_flat)[reg_mask]
            if len(res_reg) >= self.min_samples_per_regime:
                self.regime_residuals[reg] = res_reg.astype(np.float32)
                logger.info(f"Calibrated residual pool for regime '{reg}' ({len(res_reg)} points).")
            else:
                logger.info(
                    f"Regime '{reg}' has {len(res_reg)} calibration residuals (< {self.min_samples_per_regime}); "
                    "using global residual pool."
                )

        self.is_calibrated = True
        return self

    def estimate_exceedance_probability(
        self,
        y_hat: np.ndarray,
        threshold: float,
        regime: Optional[str] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute exceedance probability P(R >= threshold) and lower/upper uncertainty bounds.

        P(R >= threshold) = P(y_hat + e >= threshold) = P(e >= threshold - y_hat)

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray]
            (p_central, p_lower, p_upper)
        """
        if not self.is_calibrated:
            raise RuntimeError("ResidualUncertaintyEstimator must be calibrated before probability estimation.")

        y_arr = np.asarray(y_hat, dtype=np.float32)
        nan_mask = np.isnan(y_arr)

        reg_clean = str(regime).lower().strip() if regime is not None else ""
        res_pool = self.regime_residuals.get(reg_clean, self.global_residuals)

        if len(res_pool) == 0:
            res_pool = np.array([0.0], dtype=np.float32)

        # Required residual for exceedance: e >= threshold - y_hat
        # For each valid grid point, compute fraction of calibration residuals satisfying this
        valid_y = y_arr[~nan_mask]

        if len(valid_y) == 0:
            empty = np.full_like(y_arr, np.nan, dtype=np.float32)
            return empty, empty.copy(), empty.copy()

        # Delta needed to cross threshold
        delta_needed = threshold - valid_y  # 1D array of shape (N_valid,)

        # Point probability: empirical CDF exceedance P(e >= delta)
        # Using searchsorted on sorted residuals for fast vectorized evaluation
        sorted_res = np.sort(res_pool)
        n_res = len(sorted_res)

        # Indices where sorted_res >= delta
        idx = np.searchsorted(sorted_res, delta_needed, side="left")
        p_central_valid = ((n_res - idx) / n_res).astype(np.float32)

        # Smooth using kernel / logistic boundary to prevent discrete step artifacts
        # when sample size is moderate
        res_std = float(np.std(sorted_res)) if len(sorted_res) > 1 else 10.0
        res_std = max(res_std, 1.0)
        p_parametric = 1.0 - stats.norm.cdf(delta_needed, loc=float(np.mean(sorted_res)), scale=res_std)
        # Blend empirical with parametric for smooth calibration
        weight_emp = min(1.0, len(res_pool) / 100.0)
        p_central_valid = (weight_emp * p_central_valid + (1.0 - weight_emp) * p_parametric).astype(np.float32)

        # Uncertainty intervals via bootstrap resampling of residual pool
        # Pre-generate bootstrap quantile estimates
        boot_p = np.zeros((self.n_bootstrap, len(valid_y)), dtype=np.float32)
        for b in range(self.n_bootstrap):
            res_boot = self.rng.choice(sorted_res, size=n_res, replace=True)
            res_boot.sort()
            idx_b = np.searchsorted(res_boot, delta_needed, side="left")
            boot_p[b] = (n_res - idx_b) / n_res

        lower_pct = 100.0 * (1.0 - self.alpha_interval) / 2.0  # 10th percentile
        upper_pct = 100.0 * (1.0 + self.alpha_interval) / 2.0  # 90th percentile

        p_lower_valid = np.percentile(boot_p, lower_pct, axis=0).astype(np.float32)
        p_upper_valid = np.percentile(boot_p, upper_pct, axis=0).astype(np.float32)

        # Enforce mathematical constraints: 0 <= lower <= central <= upper <= 1
        p_lower_valid = np.clip(p_lower_valid, 0.0, 1.0)
        p_central_valid = np.clip(p_central_valid, 0.0, 1.0)
        p_upper_valid = np.clip(p_upper_valid, 0.0, 1.0)

        p_lower_valid = np.minimum(p_lower_valid, p_central_valid)
        p_upper_valid = np.maximum(p_upper_valid, p_central_valid)

        # Reconstruct output arrays
        p_central = np.full_like(y_arr, np.nan, dtype=np.float32)
        p_lower = np.full_like(y_arr, np.nan, dtype=np.float32)
        p_upper = np.full_like(y_arr, np.nan, dtype=np.float32)

        p_central[~nan_mask] = p_central_valid
        p_lower[~nan_mask] = p_lower_valid
        p_upper[~nan_mask] = p_upper_valid

        return p_central, p_lower, p_upper


def pd_not_na(val) -> bool:
    if val is None:
        return False
    if isinstance(val, float) and np.isnan(val):
        return False
    if str(val).strip() == "" or str(val).lower() == "nan":
        return False
    return True
