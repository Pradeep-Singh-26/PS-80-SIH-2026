"""Track C (Divyansh): Forecast verification and report generation.

Tasks owned:
- Task 7: Compute verification metrics (RMSE, ETS, CSI, POD, FAR, FSS if feasible) comparing raw vs. corrected forecast against observations, split by regime.

Contracts consumed:
- data/processed/corrected_grid.nc
- data/processed/nwp_grid.nc
- data/processed/obs_grid.nc
- data/processed/features_daily.csv (or regime_predictions.csv)

Contracts produced:
- outputs/verification_report/ (metric tables, comparisons, summary plots)
- outputs/figures/
"""
