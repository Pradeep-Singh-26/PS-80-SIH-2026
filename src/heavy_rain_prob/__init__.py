"""Track B (Baljeet): Heavy rainfall probability estimation and calibration.

Tasks owned:
- Task 5: Calibrated probability estimation and UQ for IMD Heavy (>=64.5mm) and Very Heavy (>=115.6mm) thresholds.

Contracts consumed:
- data/processed/corrected_grid.nc
- data/processed/obs_grid.nc
- data/processed/regime_predictions.csv

Contracts produced:
- data/processed/heavy_rain_prob.nc
- src/heavy_rain_prob/CALIBRATION.md
"""

from .probability_estimator import (
    HEAVY_THRESHOLD,
    VERY_HEAVY_THRESHOLD,
    HeavyRainProbabilityEstimator,
    generate_calibration_report,
    run_heavy_rain_prob_pipeline,
)

__all__ = [
    "HeavyRainProbabilityEstimator",
    "run_heavy_rain_prob_pipeline",
    "generate_calibration_report",
    "HEAVY_THRESHOLD",
    "VERY_HEAVY_THRESHOLD",
]
