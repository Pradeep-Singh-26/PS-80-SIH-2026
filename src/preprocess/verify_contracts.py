"""Automated Contract Verification Suite for Track A (Pradeep).

Validates all deliverables against the exact contract specifications
in TEAM_SPLIT.md and PLAN.md.
"""

import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_contracts")


def verify_track_a_contracts(workspace_root: Path) -> bool:
    """Check all deliverables produced by Track A against strict contract schemas."""
    workspace_root = Path(workspace_root)
    all_passed = True

    def check(condition: bool, msg: str) -> None:
        nonlocal all_passed
        if condition:
            logger.info(f"[PASS] {msg}")
        else:
            logger.error(f"[FAIL] {msg}")
            all_passed = False

    logger.info("=== Starting Track A Contract Verification ===")

    # 1. Task 0: data/ACCESS_NOTES.md
    access_notes = workspace_root / "data" / "ACCESS_NOTES.md"
    check(access_notes.exists() and access_notes.stat().st_size > 500, "data/ACCESS_NOTES.md exists and is populated")

    # 2. Task 1: data/raw/ manifest and district shapefile
    raw_dir = workspace_root / "data" / "raw"
    manifest_path = raw_dir / "manifest.json"
    check(manifest_path.exists(), "data/raw/manifest.json exists")
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        check(len(manifest) >= 8, f"manifest.json contains {len(manifest)} registered sources (>=8 expected)")

    district_geojson = raw_dir / "district_shapefile" / "districts.geojson"
    check(district_geojson.exists(), "data/raw/district_shapefile/districts.geojson exists")
    if district_geojson.exists():
        with open(district_geojson, "r", encoding="utf-8") as f:
            gj = json.load(f)
        has_dn = all("district_name" in feat.get("properties", {}) for feat in gj.get("features", []))
        check(has_dn and len(gj.get("features", [])) > 0, "district_shapefile contains 'district_name' attribute")

    # 3. Task 2: data/processed/features_daily.csv
    features_csv = workspace_root / "data" / "processed" / "features_daily.csv"
    check(features_csv.exists(), "data/processed/features_daily.csv exists")
    if features_csv.exists():
        df_feat = pd.read_csv(features_csv)
        req_cols = ["date", "mslp_anomaly", "olr_anomaly", "satellite_proxy", "rainfall_anomaly", "lps_flag", "wd_flag"]
        check(all(c in df_feat.columns for c in req_cols), f"features_daily.csv has required base columns {req_cols}")
        check(len(df_feat) >= 365, f"features_daily.csv has {len(df_feat)} daily rows (>=365 expected)")
        check(df_feat[req_cols].isna().sum().sum() == 0, "features_daily.csv contains zero NaNs")

    # 4. Task 2: data/processed/nwp_grid_<source>.nc (GFS and ECMWF)
    for src in ["gfs", "ecmwf"]:
        nwp_file = workspace_root / "data" / "processed" / f"nwp_grid_{src}.nc"
        check(nwp_file.exists(), f"data/processed/nwp_grid_{src}.nc exists")
        if nwp_file.exists():
            ds = xr.open_dataset(nwp_file)
            check("precip_mm" in ds.data_vars, f"nwp_grid_{src}.nc has variable 'precip_mm'")
            dims = set(ds.sizes.keys())
            check(dims == {"date", "lat", "lon"}, f"nwp_grid_{src}.nc has exact dims (date, lat, lon), got {dims}")

    # 5. Task 2: data/processed/obs_grid.nc
    obs_file = workspace_root / "data" / "processed" / "obs_grid.nc"
    check(obs_file.exists(), "data/processed/obs_grid.nc exists")
    if obs_file.exists():
        ds = xr.open_dataset(obs_file)
        check("precip_mm" in ds.data_vars, "obs_grid.nc has variable 'precip_mm'")
        dims = set(ds.sizes.keys())
        check(dims == {"date", "lat", "lon"}, f"obs_grid.nc has exact dims (date, lat, lon), got {dims}")

    # 6. Task 2: data/processed/station_obs.csv
    st_file = workspace_root / "data" / "processed" / "station_obs.csv"
    check(st_file.exists(), "data/processed/station_obs.csv exists")
    if st_file.exists():
        df_st = pd.read_csv(st_file)
        st_cols = list(df_st.columns)
        check(st_cols == ["station_id", "date", "precip_mm"], f"station_obs.csv has exact columns ['station_id', 'date', 'precip_mm'], got {st_cols}")
        check(len(df_st) > 1000, f"station_obs.csv has {len(df_st)} rows (>1000 expected)")

    # 7. Task 2: data/processed/climatology.nc
    clim_file = workspace_root / "data" / "processed" / "climatology.nc"
    check(clim_file.exists(), "data/processed/climatology.nc exists")
    if clim_file.exists():
        ds = xr.open_dataset(clim_file)
        check("precip_mm_clim" in ds.data_vars, "climatology.nc has variable 'precip_mm_clim'")

    # 8. Task 2: data/processed/regime_labels.csv
    labels_file = workspace_root / "data" / "processed" / "regime_labels.csv"
    check(labels_file.exists(), "data/processed/regime_labels.csv exists")
    if labels_file.exists():
        df_lbl = pd.read_csv(labels_file)
        req_lbl_cols = ["date", "active", "break", "low_depression", "western_disturbance", "orographic", "coastal"]
        check(list(df_lbl.columns) == req_lbl_cols, f"regime_labels.csv has exact columns {req_lbl_cols}")
        check(len(df_lbl) >= 365, f"regime_labels.csv has {len(df_lbl)} rows")

    # 9. Task 3: data/processed/regime_predictions.csv
    pred_file = workspace_root / "data" / "processed" / "regime_predictions.csv"
    check(pred_file.exists(), "data/processed/regime_predictions.csv exists")
    if pred_file.exists():
        df_pred = pd.read_csv(pred_file)
        pred_cols = ["date", "active_prob", "break_prob", "low_depression_prob", "western_disturbance_prob", "orographic_prob", "coastal_prob", "dominant_label", "confidence"]
        check(list(df_pred.columns) == pred_cols, f"regime_predictions.csv has exact columns {pred_cols}")
        probs = df_pred[["active_prob", "break_prob", "low_depression_prob", "western_disturbance_prob", "orographic_prob", "coastal_prob"]].values
        check(np.all((probs >= 0.0) & (probs <= 1.0)), "regime probabilities are bounded in [0, 1]")
        check(np.all((df_pred["confidence"].values >= 0.0) & (df_pred["confidence"].values <= 1.0)), "confidence scores are bounded in [0, 1]")

    # 10. Task 3: src/regime_classifier/EVAL.md
    eval_file = workspace_root / "src" / "regime_classifier" / "EVAL.md"
    check(eval_file.exists() and eval_file.stat().st_size > 500, "src/regime_classifier/EVAL.md exists and is populated")

    # 11. Task 3: src/regime_classifier/explanations/attributions.csv
    attr_file = workspace_root / "src" / "regime_classifier" / "explanations" / "attributions.csv"
    check(attr_file.exists(), "src/regime_classifier/explanations/attributions.csv exists")
    if attr_file.exists():
        df_attr = pd.read_csv(attr_file)
        check(list(df_attr.columns) == ["date", "feature", "attribution_value"], f"attributions.csv has exact schema ['date', 'feature', 'attribution_value'], got {list(df_attr.columns)}")
        check(len(df_attr) >= 3000, f"attributions.csv has {len(df_attr)} records (>=3000 expected)")

    # 12. Cross-track boundary compliance
    forbidden_modified = []
    forbidden_prefixes = [
        "src/bias_correction",
        "src/heavy_rain_prob",
        "src/uncertainty",
        "src/district_agg",
        "src/verification",
        "src/alerts",
        "src/mlops",
        "api",
        "dashboard",
    ]
    for pref in forbidden_prefixes:
        p = workspace_root / pref
        if p.exists():
            for f in p.rglob("*"):
                if f.is_file() and f.name not in [".gitkeep", "__init__.py"]:
                    forbidden_modified.append(str(f.relative_to(workspace_root)))

    check(len(forbidden_modified) == 0, f"Zero files touched in forbidden directories (found: {forbidden_modified})")

    logger.info(f"=== Verification Complete. Overall Status: {'SUCCESS' if all_passed else 'FAILURE'} ===")
    return all_passed


if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parent.parent.parent
    success = verify_track_a_contracts(root)
    sys.exit(0 if success else 1)
