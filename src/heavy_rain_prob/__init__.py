"""Track B (Baljeet): Heavy rainfall probability estimation.

Tasks owned:
- Task 5: Probability estimation for IMD heavy (>=64.5mm) and very heavy (>=115.5mm) rainfall thresholds.

Contracts consumed:
- data/processed/corrected_grid.nc
- data/processed/regime_predictions.csv

Contracts produced:
- data/processed/heavy_rain_prob.nc (dims: date, lat, lon; vars: p_heavy, p_very_heavy)
"""
