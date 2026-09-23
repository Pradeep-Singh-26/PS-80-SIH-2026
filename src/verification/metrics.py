"""Core verification metrics.

Implements all metrics required by PLAN.md Task 7:
  - Continuous: RMSE
  - Categorical: ETS, CSI, POD, FAR (contingency-table based)
  - Spatial: FSS (Fractions Skill Score) at multiple neighborhood scales
  - Probabilistic: reliability diagram data

All functions operate on numpy arrays for maximum reusability.
"""

import numpy as np
from typing import Tuple


# ---------------------------------------------------------------------------
# Contingency table helpers
# ---------------------------------------------------------------------------

def contingency_table(
    obs: np.ndarray, fcst: np.ndarray, threshold: float
) -> dict:
    """Compute contingency table counts for a binary event (>= threshold).

    Returns dict with keys: hits, misses, false_alarms, correct_negatives, total.
    """
    obs_binary = (obs >= threshold).astype(int)
    fcst_binary = (fcst >= threshold).astype(int)

    hits = int(np.sum((obs_binary == 1) & (fcst_binary == 1)))
    misses = int(np.sum((obs_binary == 1) & (fcst_binary == 0)))
    false_alarms = int(np.sum((obs_binary == 0) & (fcst_binary == 1)))
    correct_negatives = int(np.sum((obs_binary == 0) & (fcst_binary == 0)))

    return {
        "hits": hits,
        "misses": misses,
        "false_alarms": false_alarms,
        "correct_negatives": correct_negatives,
        "total": hits + misses + false_alarms + correct_negatives,
    }


# ---------------------------------------------------------------------------
# Continuous metrics
# ---------------------------------------------------------------------------

def rmse(obs: np.ndarray, fcst: np.ndarray) -> float:
    """Root Mean Square Error."""
    return float(np.sqrt(np.mean((fcst - obs) ** 2)))


def bias(obs: np.ndarray, fcst: np.ndarray) -> float:
    """Mean bias (fcst - obs)."""
    return float(np.mean(fcst - obs))


def mae(obs: np.ndarray, fcst: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(np.mean(np.abs(fcst - obs)))


# ---------------------------------------------------------------------------
# Categorical metrics (from contingency table)
# ---------------------------------------------------------------------------

def pod(ct: dict) -> float:
    """Probability of Detection (Hit Rate).

    POD = hits / (hits + misses)
    """
    denom = ct["hits"] + ct["misses"]
    return ct["hits"] / denom if denom > 0 else np.nan


def far(ct: dict) -> float:
    """False Alarm Ratio.

    FAR = false_alarms / (hits + false_alarms)
    """
    denom = ct["hits"] + ct["false_alarms"]
    return ct["false_alarms"] / denom if denom > 0 else np.nan


def csi(ct: dict) -> float:
    """Critical Success Index (Threat Score).

    CSI = hits / (hits + misses + false_alarms)
    """
    denom = ct["hits"] + ct["misses"] + ct["false_alarms"]
    return ct["hits"] / denom if denom > 0 else np.nan


def ets(ct: dict) -> float:
    """Equitable Threat Score (Gilbert Skill Score).

    ETS = (hits - hits_random) / (hits + misses + false_alarms - hits_random)
    where hits_random = (hits + misses)(hits + false_alarms) / total
    """
    total = ct["total"]
    if total == 0:
        return np.nan
    hits_random = (ct["hits"] + ct["misses"]) * (ct["hits"] + ct["false_alarms"]) / total
    denom = ct["hits"] + ct["misses"] + ct["false_alarms"] - hits_random
    if denom == 0:
        return np.nan
    return (ct["hits"] - hits_random) / denom


def frequency_bias(ct: dict) -> float:
    """Frequency Bias Index.

    FBI = (hits + false_alarms) / (hits + misses)
    """
    denom = ct["hits"] + ct["misses"]
    return (ct["hits"] + ct["false_alarms"]) / denom if denom > 0 else np.nan


# ---------------------------------------------------------------------------
# Spatial metric: Fractions Skill Score (FSS)
# ---------------------------------------------------------------------------

def _fractional_coverage(binary_field: np.ndarray, radius: int) -> np.ndarray:
    """Compute fractional coverage using a square neighborhood of given radius.

    Uses a simple box filter (uniform kernel) via cumulative sums for
    efficiency.
    """
    ny, nx = binary_field.shape
    # Pad to handle edges
    padded = np.pad(binary_field.astype(float), radius, mode="constant", constant_values=0)
    # Cumulative sum approach for box filter
    cum = np.cumsum(np.cumsum(padded, axis=0), axis=1)

    # Box sum using inclusion-exclusion
    y1, y2 = 0, 2 * radius
    x1, x2 = 0, 2 * radius
    box_sum = (
        cum[y2:y2 + ny, x2:x2 + nx]
        - cum[y1:y1 + ny, x2:x2 + nx]
        - cum[y2:y2 + ny, x1:x1 + nx]
        + cum[y1:y1 + ny, x1:x1 + nx]
    )
    box_size = (2 * radius + 1) ** 2
    return box_sum / box_size


def fss(
    obs_2d: np.ndarray,
    fcst_2d: np.ndarray,
    threshold: float,
    neighborhood_radius: int,
) -> float:
    """Fractions Skill Score for a 2-D field.

    Args:
        obs_2d: 2-D observed field (lat, lon).
        fcst_2d: 2-D forecast field (lat, lon).
        threshold: rainfall threshold for binary conversion.
        neighborhood_radius: radius in grid cells for the box filter.

    Returns:
        FSS value in [0, 1]. 1 = perfect, 0 = no skill.
    """
    obs_bin = (obs_2d >= threshold).astype(float)
    fcst_bin = (fcst_2d >= threshold).astype(float)

    obs_frac = _fractional_coverage(obs_bin, neighborhood_radius)
    fcst_frac = _fractional_coverage(fcst_bin, neighborhood_radius)

    mse = float(np.mean((fcst_frac - obs_frac) ** 2))
    mse_ref = float(np.mean(fcst_frac ** 2) + np.mean(obs_frac ** 2))

    if mse_ref == 0:
        return 1.0  # both fields are zero everywhere
    return 1.0 - mse / mse_ref


# ---------------------------------------------------------------------------
# Probabilistic: reliability diagram data
# ---------------------------------------------------------------------------

def reliability_data(
    obs: np.ndarray,
    prob: np.ndarray,
    threshold: float,
    n_bins: int = 10,
) -> dict:
    """Compute reliability diagram data.

    Args:
        obs: observed values (continuous).
        prob: forecast probabilities of exceeding threshold.
        threshold: the rainfall threshold the probability refers to.
        n_bins: number of probability bins.

    Returns:
        Dict with: bin_centers, observed_frequency, forecast_frequency, counts.
    """
    obs_binary = (obs >= threshold).astype(float)
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    observed_freq = np.zeros(n_bins)
    forecast_freq = np.zeros(n_bins)
    counts = np.zeros(n_bins, dtype=int)

    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            mask = (prob >= lo) & (prob <= hi)
        else:
            mask = (prob >= lo) & (prob < hi)
        n = int(np.sum(mask))
        counts[i] = n
        if n > 0:
            observed_freq[i] = float(np.mean(obs_binary[mask]))
            forecast_freq[i] = float(np.mean(prob[mask]))

    return {
        "bin_centers": bin_centers.tolist(),
        "observed_frequency": observed_freq.tolist(),
        "forecast_frequency": forecast_freq.tolist(),
        "counts": counts.tolist(),
    }
