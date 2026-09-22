"""Track C (Divyansh): District-level spatial aggregation.

Tasks owned:
- Task 6: Area-weighted mean aggregation of corrected rainfall and heavy rain probabilities to district boundaries.

Contracts consumed:
- data/processed/corrected_grid.nc
- data/processed/heavy_rain_prob.nc
- data/raw/district_shapefile/

Contracts produced:
- outputs/district_table.csv (district_name, date, corrected_rainfall_mm, rainfall_category, p_heavy, p_very_heavy)
"""
