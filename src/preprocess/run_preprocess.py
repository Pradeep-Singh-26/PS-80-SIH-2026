"""CLI entry point for Track A Preprocessing & Feature Engineering (Task 2).

Executes:
1. Regridding -> nwp_grid_gfs.nc, nwp_grid_ecmwf.nc, obs_grid.nc
2. Climatology -> climatology.nc
3. Station preprocessing -> station_obs.csv
4. Feature engineering -> features_daily.csv
5. Regime labeling -> regime_labels.csv

Usage:
    python -m src.preprocess.run_preprocess
"""

import argparse
import logging
from pathlib import Path

from .regrid import run_regridding
from .climatology import run_climatology
from .station_prep import run_station_prep
from .feature_engineering import run_feature_engineering
from .regime_labeling import run_regime_labeling

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_preprocess")


def main():
    parser = argparse.ArgumentParser(description="Track A - Preprocessing & Regime Labeling Runner (Task 2)")
    _ = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"

    logger.info("Step 1/5: Running regridding for NWP and Observations...")
    run_regridding(raw_dir, processed_dir)

    logger.info("Step 2/5: Computing daily climatology...")
    run_climatology(processed_dir)

    logger.info("Step 3/5: Standardizing station observations...")
    run_station_prep(raw_dir, processed_dir)

    logger.info("Step 4/5: Engineering daily dynamical & thermodynamical features...")
    run_feature_engineering(raw_dir, processed_dir)

    logger.info("Step 5/5: Generating multi-label ground-truth weather regimes...")
    run_regime_labeling(processed_dir)

    logger.info("Task 2 Preprocessing: ALL PROCESSED DATASETS GENERATED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
