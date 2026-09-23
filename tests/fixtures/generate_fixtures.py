"""Generate synthetic fixture data matching all contracted schemas.

Run:
    python tests/fixtures/generate_fixtures.py

Produces small NetCDF + CSV files in tests/fixtures/ for offline
development and testing.  These fixtures match the schemas defined in
TEAM_SPLIT.md so Track C modules work without real Track A/B data.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Try to import optional heavy deps; degrade gracefully for minimal envs
# ---------------------------------------------------------------------------
try:
    import xarray as xr

    HAS_XARRAY = True
except ImportError:
    HAS_XARRAY = False

FIXTURE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = FIXTURE_DIR / "outputs"

# -- Synthetic domain (small grid over central India) ----------------------
LATS = np.arange(18.0, 24.0, 1.0)  # 6 points
LONS = np.arange(74.0, 82.0, 1.0)  # 8 points
DATES = pd.date_range("2024-06-01", "2024-06-30", freq="D")  # 30 days, JJAS season

REGIMES = [
    "active",
    "break",
    "low_depression",
    "western_disturbance",
    "orographic",
    "coastal",
]

# Dummy station list (5 stations roughly in central/western India)
STATIONS = [
    {"station_id": "PUNE", "lat": 18.52, "lon": 73.85},
    {"station_id": "MUMBAI", "lat": 19.07, "lon": 72.87},
    {"station_id": "NAGPUR", "lat": 21.14, "lon": 79.08},
    {"station_id": "BHOPAL", "lat": 23.25, "lon": 77.41},
    {"station_id": "INDORE", "lat": 22.71, "lon": 75.85},
]

np.random.seed(42)


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def _make_precip_grid(
    scale: float = 20.0, offset: float = 5.0
) -> "xr.Dataset | None":
    """Return an xarray Dataset with dims (date, lat, lon) and var precip_mm."""
    if not HAS_XARRAY:
        return None
    data = np.maximum(
        0, np.random.gamma(2, scale, size=(len(DATES), len(LATS), len(LONS))) + offset
    )
    ds = xr.Dataset(
        {"precip_mm": (["date", "lat", "lon"], data.astype(np.float32))},
        coords={"date": DATES, "lat": LATS, "lon": LONS},
    )
    return ds


def generate_nwp_grids():
    """nwp_grid_gfs.nc and nwp_grid_ecmwf.nc -- two NWP forecast sources."""
    for src in ("gfs", "ecmwf"):
        ds = _make_precip_grid(scale=22.0 if src == "gfs" else 18.0)
        if ds is not None:
            path = FIXTURE_DIR / f"nwp_grid_{src}.nc"
            ds.to_netcdf(path)
            print(f"  [OK] {path.name}")


def generate_obs_grid():
    """obs_grid.nc -- gridded observations."""
    ds = _make_precip_grid(scale=15.0, offset=8.0)
    if ds is not None:
        path = FIXTURE_DIR / "obs_grid.nc"
        ds.to_netcdf(path)
        print(f"  [OK] {path.name}")


def generate_climatology():
    """climatology.nc -- long-term mean precipitation per grid cell."""
    if not HAS_XARRAY:
        return
    clim = np.random.uniform(5, 25, size=(len(LATS), len(LONS))).astype(np.float32)
    ds = xr.Dataset(
        {"precip_mm_clim": (["lat", "lon"], clim)},
        coords={"lat": LATS, "lon": LONS},
    )
    path = FIXTURE_DIR / "climatology.nc"
    ds.to_netcdf(path)
    print(f"  [OK] {path.name}")


def generate_ensemble_grid():
    """ensemble_grid.nc -- fused NWP (Track B output)."""
    ds = _make_precip_grid(scale=19.0, offset=6.0)
    if ds is not None:
        ds = ds.rename({"precip_mm": "precip_mm_ensemble"})
        path = FIXTURE_DIR / "ensemble_grid.nc"
        ds.to_netcdf(path)
        print(f"  [OK] {path.name}")


def generate_corrected_grid():
    """corrected_grid.nc -- bias-corrected precipitation (Track B output)."""
    ds = _make_precip_grid(scale=16.0, offset=7.0)
    if ds is not None:
        ds = ds.rename({"precip_mm": "precip_mm_corrected"})
        path = FIXTURE_DIR / "corrected_grid.nc"
        ds.to_netcdf(path)
        print(f"  [OK] {path.name}")


def generate_analog_correction():
    """analog_correction.nc -- analog-based estimate (Track B output)."""
    ds = _make_precip_grid(scale=17.0, offset=6.5)
    if ds is not None:
        ds = ds.rename({"precip_mm": "precip_mm_analog_estimate"})
        path = FIXTURE_DIR / "analog_correction.nc"
        ds.to_netcdf(path)
        print(f"  [OK] {path.name}")


def generate_heavy_rain_prob():
    """heavy_rain_prob.nc -- probability + uncertainty (Track B output)."""
    if not HAS_XARRAY:
        return
    shape = (len(DATES), len(LATS), len(LONS))
    p_heavy = np.random.beta(2, 5, size=shape).astype(np.float32)
    p_very_heavy = (p_heavy * np.random.uniform(0.1, 0.5, size=shape)).astype(
        np.float32
    )
    spread = np.random.uniform(0.02, 0.10, size=shape).astype(np.float32)

    ds = xr.Dataset(
        {
            "p_heavy": (["date", "lat", "lon"], p_heavy),
            "p_very_heavy": (["date", "lat", "lon"], p_very_heavy),
            "p_heavy_lower": (["date", "lat", "lon"], np.clip(p_heavy - spread, 0, 1)),
            "p_heavy_upper": (["date", "lat", "lon"], np.clip(p_heavy + spread, 0, 1)),
            "p_very_heavy_lower": (
                ["date", "lat", "lon"],
                np.clip(p_very_heavy - spread * 0.5, 0, 1),
            ),
            "p_very_heavy_upper": (
                ["date", "lat", "lon"],
                np.clip(p_very_heavy + spread * 0.5, 0, 1),
            ),
        },
        coords={"date": DATES, "lat": LATS, "lon": LONS},
    )
    path = FIXTURE_DIR / "heavy_rain_prob.nc"
    ds.to_netcdf(path)
    print(f"  [OK] {path.name}")


# -- CSV fixtures ----------------------------------------------------------


def generate_features_daily():
    """features_daily.csv -- regime-indicator features (Track A output)."""
    rows = []
    for d in DATES:
        rows.append(
            {
                "date": d.strftime("%Y-%m-%d"),
                "mslp_anomaly": round(np.random.normal(0, 3), 2),
                "olr_anomaly": round(np.random.normal(0, 15), 2),
                "satellite_proxy": round(np.random.uniform(180, 280), 2),
                "rainfall_anomaly": round(np.random.normal(0, 10), 2),
                "lps_flag": int(np.random.choice([0, 1], p=[0.8, 0.2])),
                "wd_flag": int(np.random.choice([0, 1], p=[0.9, 0.1])),
                "u850_anomaly": round(np.random.normal(0, 4), 2),
                "v850_anomaly": round(np.random.normal(0, 3), 2),
            }
        )
    df = pd.DataFrame(rows)
    path = FIXTURE_DIR / "features_daily.csv"
    df.to_csv(path, index=False)
    print(f"  [OK] {path.name}")


def generate_regime_labels():
    """regime_labels.csv -- ground-truth multi-label regime labels."""
    rows = []
    for d in DATES:
        row = {"date": d.strftime("%Y-%m-%d")}
        for reg in REGIMES:
            row[reg] = int(np.random.choice([0, 1], p=[0.7, 0.3]))
        # Ensure at least one label is active
        if sum(row[r] for r in REGIMES) == 0:
            row[np.random.choice(REGIMES)] = 1
        rows.append(row)
    df = pd.DataFrame(rows)
    path = FIXTURE_DIR / "regime_labels.csv"
    df.to_csv(path, index=False)
    print(f"  [OK] {path.name}")


def generate_regime_predictions():
    """regime_predictions.csv -- classifier output (Track A output)."""
    rows = []
    for d in DATES:
        row = {"date": d.strftime("%Y-%m-%d")}
        probs = np.random.dirichlet(np.ones(len(REGIMES)))
        for reg, p in zip(REGIMES, probs):
            row[f"{reg}_prob"] = round(float(p), 4)
        dominant = REGIMES[int(np.argmax(probs))]
        row["dominant_label"] = dominant
        row["confidence"] = round(float(np.max(probs)), 4)
        rows.append(row)
    df = pd.DataFrame(rows)
    path = FIXTURE_DIR / "regime_predictions.csv"
    df.to_csv(path, index=False)
    print(f"  [OK] {path.name}")


def generate_station_obs():
    """station_obs.csv -- station-level observations (Track A output)."""
    rows = []
    for d in DATES:
        for st in STATIONS:
            rows.append(
                {
                    "station_id": st["station_id"],
                    "date": d.strftime("%Y-%m-%d"),
                    "precip_mm": round(
                        max(0, np.random.gamma(2, 12) + 3), 1
                    ),
                }
            )
    df = pd.DataFrame(rows)
    path = FIXTURE_DIR / "station_obs.csv"
    df.to_csv(path, index=False)
    print(f"  [OK] {path.name}")


def generate_correction_method_log():
    """correction_method_log.csv -- which correction method was used per
    date/regime (Track B output)."""
    rows = []
    methods = ["quantile_mapping", "ml_gbm"]
    for d in DATES:
        rows.append(
            {
                "date": d.strftime("%Y-%m-%d"),
                "regime": np.random.choice(REGIMES),
                "method_used": np.random.choice(methods),
            }
        )
    df = pd.DataFrame(rows)
    path = FIXTURE_DIR / "correction_method_log.csv"
    df.to_csv(path, index=False)
    print(f"  [OK] {path.name}")


def generate_district_shapefile():
    """Create a simple GeoJSON with 5 dummy districts (no geopandas needed)."""
    districts = [
        {
            "name": "Pune",
            "coords": [[[73.5, 18.0], [74.5, 18.0], [74.5, 19.0], [73.5, 19.0], [73.5, 18.0]]],
        },
        {
            "name": "Mumbai Suburban",
            "coords": [[[72.5, 19.0], [73.5, 19.0], [73.5, 20.0], [72.5, 20.0], [72.5, 19.0]]],
        },
        {
            "name": "Nagpur",
            "coords": [[[78.5, 20.5], [79.5, 20.5], [79.5, 21.5], [78.5, 21.5], [78.5, 20.5]]],
        },
        {
            "name": "Bhopal",
            "coords": [[[77.0, 23.0], [78.0, 23.0], [78.0, 24.0], [77.0, 24.0], [77.0, 23.0]]],
        },
        {
            "name": "Indore",
            "coords": [[[75.5, 22.5], [76.5, 22.5], [76.5, 23.5], [75.5, 23.5], [75.5, 22.5]]],
        },
    ]
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"district_name": d["name"]},
                "geometry": {"type": "Polygon", "coordinates": d["coords"]},
            }
            for d in districts
        ],
    }
    shapefile_dir = FIXTURE_DIR / "district_shapefile"
    shapefile_dir.mkdir(parents=True, exist_ok=True)
    path = shapefile_dir / "districts.geojson"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2)
    print(f"  [OK] {path.name}")


def generate_station_metadata():
    """Station metadata JSON for aggregation."""
    path = FIXTURE_DIR / "station_metadata.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(STATIONS, f, indent=2)
    print(f"  [OK] {path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print(f"Generating fixtures in {FIXTURE_DIR} ...")
    print()

    # Ensure output dirs exist
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "verification_report").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "alerts_log").mkdir(parents=True, exist_ok=True)

    # CSV fixtures (always work)
    generate_features_daily()
    generate_regime_labels()
    generate_regime_predictions()
    generate_station_obs()
    generate_correction_method_log()
    generate_district_shapefile()
    generate_station_metadata()

    # NetCDF fixtures (need xarray + netCDF4)
    if HAS_XARRAY:
        generate_nwp_grids()
        generate_obs_grid()
        generate_climatology()
        generate_ensemble_grid()
        generate_corrected_grid()
        generate_analog_correction()
        generate_heavy_rain_prob()
    else:
        print(
            "\n  [WARN] xarray not installed -- skipping NetCDF fixtures."
            "\n         Install with: pip install xarray netCDF4"
        )

    print()
    print("[DONE] All fixtures generated.")


if __name__ == "__main__":
    main()
