"""Track B (Baljeet): Heavy rainfall probability estimation and calibration verification.

Tasks owned:
- Task 5: Calibrated probability estimation and UQ for IMD Heavy (>=64.5mm) and Very Heavy (>=115.6mm) thresholds.

Contracts consumed:
- data/processed/corrected_grid.nc
- data/processed/obs_grid.nc
- data/processed/regime_predictions.csv

Contracts produced:
- data/processed/heavy_rain_prob.nc
- data/processed/reliability_heavy.csv
- data/processed/reliability_very_heavy.csv
- src/heavy_rain_prob/CALIBRATION.md
- src/heavy_rain_prob/reliability_heavy.png
- src/heavy_rain_prob/reliability_very_heavy.png
"""

from .probability_estimator import (
    HEAVY_THRESHOLD,
    VERY_HEAVY_THRESHOLD,
    HeavyRainProbabilityEstimator,
    generate_calibration_report,
    run_heavy_rain_prob_pipeline,
)
from .reliability import (
    compute_reliability_table,
    plot_reliability_curve,
    run_probabilistic_verification,
)

__all__ = [
    "HeavyRainProbabilityEstimator",
    "run_heavy_rain_prob_pipeline",
    "generate_calibration_report",
    "compute_reliability_table",
    "plot_reliability_curve",
    "run_probabilistic_verification",
    "HEAVY_THRESHOLD",
    "VERY_HEAVY_THRESHOLD",
]
