"""District-level aggregation.

Reads corrected gridded forecast, heavy-rain probability, and regime
predictions, then performs area-weighted zonal statistics over district
polygons to produce ``outputs/district_table.csv``.

All file paths come from ``src.config`` so swapping fixture data for real
Track A/B data is a config change, not a code change.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from src.config import get_config, get_path


# IMD rainfall categories (mm / 24h)
_THRESHOLDS = None


def _get_thresholds() -> dict:
    global _THRESHOLDS
    if _THRESHOLDS is None:
        cfg = get_config()
        _THRESHOLDS = cfg.get("thresholds", {})
    return _THRESHOLDS


def _classify_rainfall(mm: float) -> str:
    """Return IMD rainfall category string."""
    t = _get_thresholds()
    if mm >= t.get("extremely_heavy", 204.5):
        return "extremely_heavy"
    elif mm >= t.get("very_heavy", 115.5):
        return "very_heavy"
    elif mm >= t.get("heavy", 64.5):
        return "heavy"
    elif mm >= 15.6:
        return "moderate"
    elif mm >= 2.5:
        return "light"
    else:
        return "no_rain"


def _load_district_polygons() -> list[dict]:
    """Load district polygons from GeoJSON shapefile directory.

    Returns a list of dicts with keys: district_name, polygon (list of
    (lon, lat) coordinate rings).
    """
    shapefile_dir = get_path("data.district_shapefile")

    # Try GeoJSON first (fixture / lightweight format)
    geojson_path = shapefile_dir / "districts.geojson"
    if not geojson_path.exists():
        fallback_path = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "district_shapefile" / "districts.geojson"
        if fallback_path.exists():
            geojson_path = fallback_path

    if geojson_path.exists():
        with open(geojson_path, "r", encoding="utf-8") as f:
            gj = json.load(f)
        districts = []
        for feat in gj["features"]:
            districts.append(
                {
                    "district_name": feat["properties"]["district_name"],
                    "polygon": feat["geometry"]["coordinates"],
                }
            )
        return districts

    # Fallback: try geopandas for .shp files
    try:
        import geopandas as gpd

        shp_files = list(shapefile_dir.glob("*.shp"))
        if not shp_files:
            raise FileNotFoundError(f"No .shp files found in {shapefile_dir}")
        gdf = gpd.read_file(shp_files[0])
        districts = []
        for _, row in gdf.iterrows():
            name = row.get("district_name") or row.get("DISTRICT") or row.get("NAME")
            geom = row.geometry
            coords = (
                [list(geom.exterior.coords)]
                if geom.geom_type == "Polygon"
                else [list(p.exterior.coords) for p in geom.geoms]
            )
            districts.append({"district_name": name, "polygon": coords})
        return districts
    except ImportError:
        raise FileNotFoundError(
            f"No districts.geojson in {shapefile_dir} and geopandas not installed."
        )


def _point_in_polygon(lon: float, lat: float, polygon_coords: list) -> bool:
    """Ray-casting point-in-polygon test for a single ring."""
    ring = polygon_coords[0]  # outer ring
    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _grid_cells_in_district(
    lats: np.ndarray, lons: np.ndarray, polygon_coords: list
) -> list[tuple[int, int]]:
    """Return (lat_idx, lon_idx) pairs of grid cells whose center falls
    inside the district polygon."""
    cells = []
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            if _point_in_polygon(float(lon), float(lat), polygon_coords):
                cells.append((i, j))
    return cells


def aggregate_districts():
    """Main entry point: produce outputs/district_table.csv."""
    # Load inputs
    corrected_ds = xr.open_dataset(get_path("data.corrected_grid"))
    prob_ds = xr.open_dataset(get_path("data.heavy_rain_prob"))
    regime_df = pd.read_csv(get_path("data.regime_predictions"))
    method_df = pd.read_csv(get_path("data.correction_method_log"))

    districts = _load_district_polygons()

    corrected_var = "precip_mm_corrected"
    lats = corrected_ds.lat.values
    lons = corrected_ds.lon.values
    dates = pd.to_datetime(corrected_ds.date.values)

    # Merge regime + method info by date
    regime_df["date"] = pd.to_datetime(regime_df["date"])
    method_df["date"] = pd.to_datetime(method_df["date"])

    rows = []
    for district in districts:
        cells = _grid_cells_in_district(lats, lons, district["polygon"])
        if not cells:
            continue

        lat_idxs = [c[0] for c in cells]
        lon_idxs = [c[1] for c in cells]

        for t, date in enumerate(dates):
            # Area-weighted mean (uniform weights for regular grid)
            precip_vals = [
                float(corrected_ds[corrected_var].values[t, li, lj])
                for li, lj in zip(lat_idxs, lon_idxs)
            ]
            mean_precip = float(np.mean(precip_vals))

            # Probability (mean over district grid cells)
            p_heavy = float(np.mean([
                prob_ds["p_heavy"].values[t, li, lj]
                for li, lj in zip(lat_idxs, lon_idxs)
            ]))
            p_very_heavy = float(np.mean([
                prob_ds["p_very_heavy"].values[t, li, lj]
                for li, lj in zip(lat_idxs, lon_idxs)
            ]))
            unc_lower = float(np.mean([
                prob_ds["p_heavy_lower"].values[t, li, lj]
                for li, lj in zip(lat_idxs, lon_idxs)
            ]))
            unc_upper = float(np.mean([
                prob_ds["p_heavy_upper"].values[t, li, lj]
                for li, lj in zip(lat_idxs, lon_idxs)
            ]))

            # Regime info for this date
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

            # Correction method
            method_row = method_df[method_df["date"] == date]
            correction_method = (
                method_row["method_used"].iloc[0]
                if len(method_row) > 0
                else "unknown"
            )

            rows.append(
                {
                    "district_name": district["district_name"],
                    "date": date.strftime("%Y-%m-%d"),
                    "corrected_rainfall_mm": round(mean_precip, 2),
                    "rainfall_category": _classify_rainfall(mean_precip),
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
    out_path = get_path("outputs.district_table")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"    -> {out_path} ({len(df)} rows)")

    # Cleanup
    corrected_ds.close()
    prob_ds.close()
