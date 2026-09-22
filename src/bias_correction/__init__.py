"""Track B (Baljeet): Regime-conditioned bias correction.

Tasks owned:
- Task 4: Per-regime quantile mapping (or regime-as-feature fallback).

Contracts consumed:
- data/processed/nwp_grid.nc
- data/processed/obs_grid.nc
- data/processed/climatology.nc
- data/processed/regime_predictions.csv (or ground truth regime labels)

Contracts produced:
- data/processed/corrected_grid.nc (dims: date, lat, lon; var: precip_mm_corrected)
"""
