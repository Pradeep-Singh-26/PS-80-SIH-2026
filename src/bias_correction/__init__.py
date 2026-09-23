"""Track B (Baljeet): Regime-conditioned bias correction and ensemble fusion.

Tasks owned:
- Task 4: Multi-NWP ensemble blending and regime-conditioned bias correction (QM + ML + Router).

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
"""

from .bias_corrector import run_bias_correction_pipeline
from .ml_correction import MLGradientBoostedCorrector
from .quantile_mapping import EmpiricalQuantileMapper, RegimeConditionedQuantileMapper
from .router import RegimeBiasCorrectionRouter

__all__ = [
    "run_bias_correction_pipeline",
    "EmpiricalQuantileMapper",
    "RegimeConditionedQuantileMapper",
    "MLGradientBoostedCorrector",
    "RegimeBiasCorrectionRouter",
]
