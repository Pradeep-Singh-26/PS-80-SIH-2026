"""Track B (Baljeet): Regime-conditioned bias correction, ensemble fusion, and analog correction.

Tasks owned:
- Task 4: Multi-NWP ensemble blending, regime-conditioned bias correction (QM + ML + Router), and analog correction.

Contracts consumed:
- data/processed/ensemble_grid.nc (or nwp_grid_gfs.nc / nwp_grid_ecmwf.nc)
- data/processed/obs_grid.nc
- data/processed/climatology.nc
- data/processed/regime_predictions.csv
- data/processed/features_daily.csv

Contracts produced:
- data/processed/ensemble_grid.nc
- data/processed/corrected_grid.nc
- data/processed/correction_method_log.csv
- data/processed/analog_correction.nc
- data/processed/analog_match_log.csv
"""

from pathlib import Path
from .analog import AnalogBiasCorrector, AnalogSearchEngine, run_analog_correction_pipeline
from .bias_corrector import run_bias_correction_pipeline
from .ensemble.blender import run_ensemble_blending
from .ml_correction import MLGradientBoostedCorrector
from .quantile_mapping import EmpiricalQuantileMapper, RegimeConditionedQuantileMapper
from .router import RegimeBiasCorrectionRouter


def run():
    """Execute Track B ensemble blending, regime bias correction, and analog correction pipeline."""
    try:
        from src.config import get_path
        gfs_path = get_path("data.nwp_grid_gfs")
        ecmwf_path = get_path("data.nwp_grid_ecmwf")
        ensemble_path = get_path("data.ensemble_grid")
        obs_path = get_path("data.obs_grid")
        climatology_path = get_path("data.climatology")
        regime_preds_path = get_path("data.regime_predictions")
        features_daily_path = get_path("data.features_daily")
        corrected_grid_path = get_path("data.corrected_grid")
        correction_log_path = get_path("data.correction_method_log")
        analog_grid_path = get_path("data.analog_correction")
        analog_log_path = analog_grid_path.parent / "analog_match_log.csv"
    except Exception:
        project_root = Path(__file__).resolve().parent.parent.parent
        processed_dir = project_root / "data" / "processed"
        gfs_path = processed_dir / "nwp_grid_gfs.nc"
        ecmwf_path = processed_dir / "nwp_grid_ecmwf.nc"
        ensemble_path = processed_dir / "ensemble_grid.nc"
        obs_path = processed_dir / "obs_grid.nc"
        climatology_path = processed_dir / "climatology.nc"
        regime_preds_path = processed_dir / "regime_predictions.csv"
        features_daily_path = processed_dir / "features_daily.csv"
        corrected_grid_path = processed_dir / "corrected_grid.nc"
        correction_log_path = processed_dir / "correction_method_log.csv"
        analog_grid_path = processed_dir / "analog_correction.nc"
        analog_log_path = processed_dir / "analog_match_log.csv"

    # Step 1: Ensemble blending
    run_ensemble_blending(gfs_path=gfs_path, ecmwf_path=ecmwf_path, output_path=ensemble_path)

    # Step 2: Regime-conditioned bias correction
    run_bias_correction_pipeline(
        ensemble_path=ensemble_path,
        obs_path=obs_path,
        climatology_path=climatology_path,
        regime_preds_path=regime_preds_path,
        features_daily_path=features_daily_path,
        output_grid_path=corrected_grid_path,
        output_log_path=correction_log_path,
    )

    # Step 3: Analog correction
    run_analog_correction_pipeline(
        ensemble_path=ensemble_path,
        obs_path=obs_path,
        features_daily_path=features_daily_path,
        regime_preds_path=regime_preds_path,
        output_grid_path=analog_grid_path,
        output_log_path=analog_log_path,
    )


__all__ = [
    "run",
    "run_bias_correction_pipeline",
    "run_analog_correction_pipeline",
    "run_ensemble_blending",
    "EmpiricalQuantileMapper",
    "RegimeConditionedQuantileMapper",
    "MLGradientBoostedCorrector",
    "RegimeBiasCorrectionRouter",
    "AnalogBiasCorrector",
    "AnalogSearchEngine",
]

