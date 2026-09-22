"""Station-level aggregation.

For each station, extracts the nearest grid-cell value from corrected
gridded forecast and probability products, then joins regime/method
metadata to produce ``outputs/station_table.csv``.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from src.config import get_path
from src.district_agg.district_aggregator import _classify_rainfall


def _load_station_metadata() -> list[dict]:
    """Load station metadata (station_id, lat, lon).

    Tries station_metadata.json in the shapefile dir, then falls back
    to the fixture location.
    """
    shapefile_dir = get_path("data.district_shapefile")
    meta_path = shapefile_dir.parent / "station_metadata.json"
    if not meta_path.exists():
        # Fixture location
        meta_path = shapefile_dir.parent / "station_metadata.json"
    if not meta_path.exists():
        # Try alongside fixtures
        meta_path = Path(get_path("data.regime_predictions")).parent / "station_metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(
            "station_metadata.json not found. Expected near the district shapefile dir."
        )
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _nearest_grid_idx(target: float, grid: np.ndarray) -> int:
    """Return index of nearest value in a sorted 1-D grid."""
    return int(np.argmin(np.abs(grid - target)))


def aggregate_stations():
    """Main entry point: produce outputs/station_table.csv."""
    corrected_ds = xr.open_dataset(get_path("data.corrected_grid"))
    prob_ds = xr.open_dataset(get_path("data.heavy_rain_prob"))
    regime_df = pd.read_csv(get_path("data.regime_predictions"))
    method_df = pd.read_csv(get_path("data.correction_method_log"))

    stations = _load_station_metadata()

    lats = corrected_ds.lat.values
    lons = corrected_ds.lon.values
    dates = pd.to_datetime(corrected_ds.date.values)

    regime_df["date"] = pd.to_datetime(regime_df["date"])
    method_df["date"] = pd.to_datetime(method_df["date"])

    rows = []
    for station in stations:
        lat_idx = _nearest_grid_idx(station["lat"], lats)
        lon_idx = _nearest_grid_idx(station["lon"], lons)

        for t, date in enumerate(dates):
            precip = float(corrected_ds["precip_mm_corrected"].values[t, lat_idx, lon_idx])
            p_heavy = float(prob_ds["p_heavy"].values[t, lat_idx, lon_idx])
            p_very_heavy = float(prob_ds["p_very_heavy"].values[t, lat_idx, lon_idx])
            unc_lower = float(prob_ds["p_heavy_lower"].values[t, lat_idx, lon_idx])
            unc_upper = float(prob_ds["p_heavy_upper"].values[t, lat_idx, lon_idx])

            regime_row = regime_df[regime_df["date"] == date]
            dominant_regime = (
                regime_row["dominant_label"].iloc[0]
                if len(regime_row) > 0
                else "unknown"
            )
            regime_confidence = (
                float(regime_row["confidence"].iloc[0])
                if len(regime_row) > 0
                else 0.0
            )

            method_row = method_df[method_df["date"] == date]
            correction_method = (
                method_row["method_used"].iloc[0]
                if len(method_row) > 0
                else "unknown"
            )

            rows.append(
                {
                    "station_id": station["station_id"],
                    "date": date.strftime("%Y-%m-%d"),
                    "lat": station["lat"],
                    "lon": station["lon"],
                    "corrected_rainfall_mm": round(precip, 2),
                    "rainfall_category": _classify_rainfall(precip),
                    "p_heavy": round(p_heavy, 4),
                    "p_very_heavy": round(p_very_heavy, 4),
                    "uncertainty_lower": round(unc_lower, 4),
                    "uncertainty_upper": round(unc_upper, 4),
                    "dominant_regime": dominant_regime,
                    "regime_confidence": round(regime_confidence, 4),
                    "correction_method": correction_method,
                }
            )

    df = pd.DataFrame(rows)
    out_path = get_path("outputs.station_table")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"    -> {out_path} ({len(df)} rows)")

    corrected_ds.close()
    prob_ds.close()
