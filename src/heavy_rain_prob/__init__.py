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

from pathlib import Path


def run():
    """Execute Track B probability estimation, UQ, and calibration verification pipeline."""
    project_root = Path(__file__).resolve().parent.parent.parent
    processed_dir = project_root / "data" / "processed"
    corrected_path = processed_dir / "corrected_grid.nc"
    obs_path = processed_dir / "obs_grid.nc"
    regime_preds_path = processed_dir / "regime_predictions.csv"
    heavy_prob_path = processed_dir / "heavy_rain_prob.nc"
    calib_md_path = project_root / "src" / "heavy_rain_prob" / "CALIBRATION.md"

    # Step 1: Probability estimation + UQ
    run_heavy_rain_prob_pipeline(
        corrected_path=corrected_path,
        obs_path=obs_path,
        regime_preds_path=regime_preds_path,
        output_nc_path=heavy_prob_path,
        output_report_path=calib_md_path,
    )

    # Step 2: Calibration & Reliability verification
    run_probabilistic_verification(
        heavy_prob_path=heavy_prob_path,
        obs_path=obs_path,
        output_report_path=calib_md_path,
        output_dir_processed=processed_dir,
    )


__all__ = [
    "run",
    "HeavyRainProbabilityEstimator",
    "run_heavy_rain_prob_pipeline",
    "generate_calibration_report",
    "compute_reliability_table",
    "plot_reliability_curve",
    "run_probabilistic_verification",
    "HEAVY_THRESHOLD",
    "VERY_HEAVY_THRESHOLD",
]

