"""Verification comparator.

Runs all metrics across raw NWP, ensemble-blended, and corrected forecasts
vs. observations, split by regime and threshold. Produces the full
verification report under ``outputs/verification_report/``.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from src.config import get_config, get_path
from src.verification.metrics import (
    rmse,
    bias,
    mae,
    contingency_table,
    pod,
    far,
    csi,
    ets,
    frequency_bias,
    fss,
    reliability_data,
)


# Neighborhood radii for FSS (in grid cells)
FSS_RADII = [1, 2, 3, 5]


def _load_datasets() -> dict:
    """Load all gridded datasets needed for verification."""
    datasets = {}

    # Raw NWP (use GFS as primary)
    try:
        datasets["raw_nwp"] = xr.open_dataset(get_path("data.nwp_grid_gfs"))
    except FileNotFoundError:
        datasets["raw_nwp"] = None

    # Ensemble-blended
    try:
        datasets["ensemble"] = xr.open_dataset(get_path("data.ensemble_grid"))
    except FileNotFoundError:
        datasets["ensemble"] = None

    # Corrected
    datasets["corrected"] = xr.open_dataset(get_path("data.corrected_grid"))

    # Observations
    datasets["obs"] = xr.open_dataset(get_path("data.obs_grid"))

    # Heavy rain probability (for reliability)
    try:
        datasets["prob"] = xr.open_dataset(get_path("data.heavy_rain_prob"))
    except FileNotFoundError:
        datasets["prob"] = None

    return datasets


def _extract_precip(ds: xr.Dataset) -> np.ndarray:
    """Extract precipitation array from dataset, handling different var names."""
    for var in ["precip_mm", "precip_mm_corrected", "precip_mm_ensemble"]:
        if var in ds.data_vars:
            return ds[var].values
    raise KeyError(f"No precipitation variable found in dataset. Vars: {list(ds.data_vars)}")


def _compute_metrics_for_pair(
    obs_vals: np.ndarray,
    fcst_vals: np.ndarray,
    thresholds: dict,
    label: str,
) -> dict:
    """Compute all metrics for one obs-forecast pair.

    Args:
        obs_vals: flattened observation array.
        fcst_vals: flattened forecast array.
        thresholds: dict of threshold_name -> mm value.
        label: identifier for this comparison (e.g. "raw_nwp", "corrected").

    Returns:
        Dict of computed metrics.
    """
    result = {
        "source": label,
        "n_points": int(len(obs_vals)),
        "rmse": rmse(obs_vals, fcst_vals),
        "bias": bias(obs_vals, fcst_vals),
        "mae": mae(obs_vals, fcst_vals),
    }

    # Categorical metrics per threshold
    for tname, tval in thresholds.items():
        ct = contingency_table(obs_vals, fcst_vals, tval)
        result[f"{tname}_pod"] = pod(ct)
        result[f"{tname}_far"] = far(ct)
        result[f"{tname}_csi"] = csi(ct)
        result[f"{tname}_ets"] = ets(ct)
        result[f"{tname}_freq_bias"] = frequency_bias(ct)
        result[f"{tname}_hits"] = ct["hits"]
        result[f"{tname}_misses"] = ct["misses"]
        result[f"{tname}_false_alarms"] = ct["false_alarms"]

    return result


def run_comparison():
    """Main entry point: produce outputs/verification_report/."""
    cfg = get_config()
    thresholds = cfg.get("thresholds", {"heavy": 64.5, "very_heavy": 115.5, "extremely_heavy": 204.5})

    datasets = _load_datasets()
    obs_data = _extract_precip(datasets["obs"])
    regime_df = pd.read_csv(get_path("data.regime_predictions"))
    regime_df["date"] = pd.to_datetime(regime_df["date"])

    dates = pd.to_datetime(datasets["obs"].date.values)

    # Pairs to compare
    pairs = []
    if datasets["raw_nwp"] is not None:
        pairs.append(("raw_nwp", _extract_precip(datasets["raw_nwp"])))
    if datasets["ensemble"] is not None:
        pairs.append(("ensemble", _extract_precip(datasets["ensemble"])))
    pairs.append(("corrected", _extract_precip(datasets["corrected"])))

    report_dir = get_path("outputs.verification_report")
    report_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Overall metrics (all dates, all grid cells)
    # ------------------------------------------------------------------
    overall_results = []
    for label, fcst_data in pairs:
        obs_flat = obs_data.flatten()
        fcst_flat = fcst_data.flatten()
        metrics = _compute_metrics_for_pair(obs_flat, fcst_flat, thresholds, label)
        overall_results.append(metrics)

    overall_df = pd.DataFrame(overall_results)
    overall_df.to_csv(report_dir / "overall_metrics.csv", index=False)
    print(f"    -> overall_metrics.csv")

    # ------------------------------------------------------------------
    # 2. Per-regime metrics
    # ------------------------------------------------------------------
    regime_results = []
    for label, fcst_data in pairs:
        for t_idx, date in enumerate(dates):
            rrow = regime_df[regime_df["date"] == date]
            if len(rrow) == 0:
                continue
            regime = rrow["dominant_label"].iloc[0]

            obs_slice = obs_data[t_idx].flatten()
            fcst_slice = fcst_data[t_idx].flatten()
            metrics = _compute_metrics_for_pair(obs_slice, fcst_slice, thresholds, label)
            metrics["date"] = date.strftime("%Y-%m-%d")
            metrics["regime"] = regime
            regime_results.append(metrics)

    regime_df_out = pd.DataFrame(regime_results)
    regime_df_out.to_csv(report_dir / "per_regime_metrics.csv", index=False)
    print(f"    -> per_regime_metrics.csv")

    # Aggregate per regime
    if len(regime_df_out) > 0:
        regime_summary = regime_df_out.groupby(["source", "regime"]).mean(numeric_only=True).reset_index()
        regime_summary.to_csv(report_dir / "regime_summary.csv", index=False)
        print(f"    -> regime_summary.csv")

    # ------------------------------------------------------------------
    # 3. FSS at multiple scales (for the latest time step)
    # ------------------------------------------------------------------
    fss_results = []
    last_t = len(dates) - 1
    obs_2d = obs_data[last_t]
    for label, fcst_data in pairs:
        fcst_2d = fcst_data[last_t]
        for tname, tval in thresholds.items():
            for radius in FSS_RADII:
                score = fss(obs_2d, fcst_2d, tval, radius)
                fss_results.append({
                    "source": label,
                    "threshold": tname,
                    "threshold_mm": tval,
                    "neighborhood_radius": radius,
                    "fss": round(score, 4),
                })

    fss_df = pd.DataFrame(fss_results)
    fss_df.to_csv(report_dir / "fss_scores.csv", index=False)
    print(f"    -> fss_scores.csv")

    # ------------------------------------------------------------------
    # 4. Reliability diagram data (if probability dataset available)
    # ------------------------------------------------------------------
    if datasets["prob"] is not None:
        prob_ds = datasets["prob"]
        rel_results = {}
        for tname, tval in thresholds.items():
            prob_var = f"p_{tname}" if f"p_{tname}" in prob_ds.data_vars else None
            if prob_var is None:
                continue
            obs_flat = obs_data.flatten()
            prob_flat = prob_ds[prob_var].values.flatten()
            rel = reliability_data(obs_flat, prob_flat, tval)
            rel_results[tname] = rel

        with open(report_dir / "reliability_data.json", "w") as f:
            json.dump(rel_results, f, indent=2)
        print(f"    -> reliability_data.json")

    # ------------------------------------------------------------------
    # 5. Summary report (Markdown)
    # ------------------------------------------------------------------
    _write_summary_report(report_dir, overall_df, thresholds)

    # Cleanup
    for ds in datasets.values():
        if ds is not None:
            ds.close()


def _write_summary_report(report_dir: Path, overall_df: pd.DataFrame, thresholds: dict):
    """Write a human-readable Markdown summary."""
    lines = [
        "# Verification Report",
        "",
        "## Overall Metrics (all dates, all grid cells)",
        "",
    ]

    for _, row in overall_df.iterrows():
        lines.append(f"### {row['source']}")
        lines.append(f"- **RMSE**: {row['rmse']:.2f} mm")
        lines.append(f"- **Bias**: {row['bias']:.2f} mm")
        lines.append(f"- **MAE**: {row['mae']:.2f} mm")
        lines.append(f"- **N points**: {int(row['n_points'])}")
        lines.append("")

        for tname in thresholds:
            lines.append(f"#### Threshold: {tname} (>= {thresholds[tname]} mm)")
            lines.append(f"- POD: {row.get(f'{tname}_pod', 'N/A'):.3f}" if not np.isnan(row.get(f'{tname}_pod', np.nan)) else f"- POD: N/A")
            lines.append(f"- FAR: {row.get(f'{tname}_far', 'N/A'):.3f}" if not np.isnan(row.get(f'{tname}_far', np.nan)) else f"- FAR: N/A")
            lines.append(f"- CSI: {row.get(f'{tname}_csi', 'N/A'):.3f}" if not np.isnan(row.get(f'{tname}_csi', np.nan)) else f"- CSI: N/A")
            lines.append(f"- ETS: {row.get(f'{tname}_ets', 'N/A'):.3f}" if not np.isnan(row.get(f'{tname}_ets', np.nan)) else f"- ETS: N/A")
            lines.append("")

    lines.append("---")
    lines.append("*Generated by src/verification/comparator.py*")

    with open(report_dir / "REPORT.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"    -> REPORT.md")
