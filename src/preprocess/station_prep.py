"""Station Observations Preprocessing Module (Track A - Task 2).

Standardizes station observations into the contract schema:
- data/processed/station_obs.csv (columns: station_id, date, precip_mm)
"""

import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


def run_station_prep(raw_dir: Path, processed_dir: Path) -> Path:
    """Read raw station observations, validate/clean, and save to contract schema."""
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_csv = raw_dir / "obs_station" / "station_obs_raw.csv"
    if not raw_csv.exists():
        raise FileNotFoundError(f"Missing raw station obs file: {raw_csv}")

    df = pd.read_csv(raw_csv)

    # Standardize column names
    col_map = {}
    for c in df.columns:
        if c.lower() in ["station_id", "station", "id", "st_id"]:
            col_map[c] = "station_id"
        elif c.lower() in ["date", "time", "day"]:
            col_map[c] = "date"
        elif c.lower() in ["precip_mm", "rainfall", "rainfall_mm", "rain_mm", "precip"]:
            col_map[c] = "precip_mm"

    df_clean = df.rename(columns=col_map)
    required_cols = ["station_id", "date", "precip_mm"]
    for rc in required_cols:
        if rc not in df_clean.columns:
            raise ValueError(f"Station data missing required column '{rc}'")

    df_out = df_clean[required_cols].copy()
    df_out["date"] = df_out["date"].astype(str)
    df_out["precip_mm"] = df_out["precip_mm"].fillna(0.0).round(2)

    out_csv = processed_dir / "station_obs.csv"
    df_out.to_csv(out_csv, index=False)
    logger.info(f"Saved {out_csv} with {len(df_out)} rows and columns {required_cols}")
    return out_csv
