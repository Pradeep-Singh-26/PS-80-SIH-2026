"""Configuration for Multi-Label Weather Regime Classifier (Track A - Task 3)."""

from typing import List

REGIME_CLASSES: List[str] = [
    "active",
    "break",
    "low_depression",
    "western_disturbance",
    "orographic",
    "coastal",
]

FEATURE_COLUMNS: List[str] = [
    "mslp_anomaly",
    "olr_anomaly",
    "satellite_proxy",
    "rainfall_anomaly",
    "lps_flag",
    "wd_flag",
    "trough_position_lat",
    "zonal_shear_850",
    "orographic_index",
    "coastal_convergence_index",
]

# Temporal train / held-out test split
TRAIN_YEARS = [2021, 2022]
TEST_YEARS = [2023]
