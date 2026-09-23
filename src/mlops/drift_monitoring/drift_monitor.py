"""Statistical Feature and Forecast Skill Drift Monitoring Module (Track B - Task 11 / Step 8).

Monitors:
1. Feature Distribution Drift: Population Stability Index (PSI) & Kolmogorov-Smirnov (KS) tests
   across the exact 19 features consumed by the Track B correction model.
2. Skill Degradation Drift: Tracking MAE, RMSE, and Mean Bias across chronological windows.
3. Automated Retraining Decision Engine: Deterministic, rule-based recommendation evaluated on
   feature drift, skill degradation, and approved forecaster feedback volume.
4. Generates:
   - src/mlops/drift_monitoring/REPORT.md
   - data/processed/drift_feature_report.csv
"""

import argparse
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
import xarray as xr

from ...bias_correction.ml_correction import (
    DYNAMICAL_FEATURES,
    REGIME_PROB_FEATURES,
    STATIC_SPATIAL_FEATURES,
    MLGradientBoostedCorrector,
)
from ...explainability.correction_attribution import EXACT_ML_FEATURES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("drift_monitor")

# Configurable heuristic drift thresholds
PSI_LOW_THRESHOLD = 0.10       # < 0.10: Insignificant / No drift
PSI_HIGH_THRESHOLD = 0.25      # >= 0.25: Significant drift
KS_PVALUE_THRESHOLD = 0.01     # p-value < 0.01: Statistically significant distribution difference
SKILL_DEGRADATION_THRESHOLD = 0.15  # >= 15% increase in RMSE or MAE triggers alert
FEEDBACK_COUNT_THRESHOLD = 10  # >= 10 approved human forecaster feedback records triggers retraining check


def calculate_psi(
    ref_vals: np.ndarray,
    curr_vals: np.ndarray,
    n_bins: int = 10,
    is_binary: bool = False,
    epsilon: float = 1e-4,
) -> float:
    """Calculate Population Stability Index (PSI) between reference and current samples.

    Parameters
    ----------
    ref_vals : np.ndarray
        Baseline/reference sample array.
    curr_vals : np.ndarray
        Current evaluation sample array.
    n_bins : int, default=10
        Number of quantile bins for continuous variables.
    is_binary : bool, default=False
        Whether the variable is discrete/binary (e.g. 0/1 flag).
    epsilon : float, default=1e-4
        Smoothing constant to prevent division by zero or log(0).

    Returns
    -------
    float
        Computed PSI value.
    """
    ref_clean = ref_vals[~np.isnan(ref_vals)]
    curr_clean = curr_vals[~np.isnan(curr_vals)]

    if len(ref_clean) == 0 or len(curr_clean) == 0:
        return 0.0

    if is_binary or len(np.unique(ref_clean)) <= 2:
        # Binary / 2-bin division
        bins = [-np.inf, 0.5, np.inf]
    else:
        # Quantile bin edges based on reference distribution
        quantiles = np.linspace(0.0, 1.0, n_bins + 1)
        bins = np.percentile(ref_clean, quantiles * 100)
        bins[0] = -np.inf
        bins[-1] = np.inf
        bins = np.unique(bins)
        if len(bins) < 3:
            bins = np.linspace(np.min(ref_clean) - 1e-3, np.max(ref_clean) + 1e-3, n_bins + 1)
            bins[0] = -np.inf
            bins[-1] = np.inf

    ref_counts, _ = np.histogram(ref_clean, bins=bins)
    curr_counts, _ = np.histogram(curr_clean, bins=bins)

    ref_pct = (ref_counts + epsilon) / (np.sum(ref_counts) + epsilon * len(ref_counts))
    curr_pct = (curr_counts + epsilon) / (np.sum(curr_counts) + epsilon * len(curr_counts))

    psi_val = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
    return float(np.maximum(psi_val, 0.0))


def compute_feature_drift(
    df_ref: pd.DataFrame,
    df_curr: pd.DataFrame,
    features: List[str] = EXACT_ML_FEATURES,
) -> pd.DataFrame:
    """Compute PSI and KS statistics for all features between reference and current windows."""
    rows = []

    for feat in features:
        if feat not in df_ref.columns or feat not in df_curr.columns:
            logger.warning(f"Feature '{feat}' missing from DataFrame; skipping.")
            continue

        ref_arr = df_ref[feat].dropna().values
        curr_arr = df_curr[feat].dropna().values

        if len(ref_arr) == 0 or len(curr_arr) == 0:
            continue

        ref_mean = float(np.mean(ref_arr))
        curr_mean = float(np.mean(curr_arr))
        mean_diff = curr_mean - ref_mean

        is_bin = feat in ["lps_flag", "wd_flag"] or len(np.unique(ref_arr)) <= 2

        # 1. Population Stability Index
        psi_val = calculate_psi(ref_arr, curr_arr, is_binary=is_bin)

        # 2. Kolmogorov-Smirnov Test
        if is_bin:
            ks_stat = 0.0
            ks_p = 1.0
        else:
            ks_res = ks_2samp(ref_arr, curr_arr)
            ks_stat = float(ks_res.statistic)
            ks_p = float(ks_res.pvalue)

        # 3. Categorize drift severity
        if psi_val >= PSI_HIGH_THRESHOLD:
            drift_flag = "significant_drift"
            severity = "High"
        elif psi_val >= PSI_LOW_THRESHOLD:
            drift_flag = "moderate_drift"
            severity = "Medium"
        else:
            drift_flag = "no_drift"
            severity = "Low"

        rows.append({
            "feature": feat,
            "reference_mean": round(ref_mean, 4),
            "current_mean": round(curr_mean, 4),
            "mean_diff": round(mean_diff, 4),
            "psi": round(psi_val, 4),
            "ks_statistic": round(ks_stat, 4),
            "ks_pvalue": round(ks_p, 4),
            "drift_flag": drift_flag,
            "severity": severity,
        })

    df_drift = pd.DataFrame(rows)
    return df_drift.sort_values(by="psi", ascending=False).reset_index(drop=True)


def compute_skill_drift(
    y_true_ref: np.ndarray,
    y_pred_ref: np.ndarray,
    y_true_curr: np.ndarray,
    y_pred_curr: np.ndarray,
) -> Dict[str, Any]:
    """Calculate baseline vs current forecast error metrics and degradation percentages."""
    y_tr_ref = np.asarray(y_true_ref).flatten()
    y_pr_ref = np.asarray(y_pred_ref).flatten()
    y_tr_curr = np.asarray(y_true_curr).flatten()
    y_pr_curr = np.asarray(y_pred_curr).flatten()

    mask_ref = (~np.isnan(y_tr_ref)) & (~np.isnan(y_pr_ref))
    mask_curr = (~np.isnan(y_tr_curr)) & (~np.isnan(y_pr_curr))

    y_tr_ref, y_pr_ref = y_tr_ref[mask_ref], y_pr_ref[mask_ref]
    y_tr_curr, y_pr_curr = y_tr_curr[mask_curr], y_pr_curr[mask_curr]

    if len(y_tr_ref) == 0 or len(y_tr_curr) == 0:
        return {"status": "insufficient_data"}

    mae_ref = float(np.mean(np.abs(y_pr_ref - y_tr_ref)))
    rmse_ref = float(np.sqrt(np.mean((y_pr_ref - y_tr_ref) ** 2)))
    bias_ref = float(np.mean(y_pr_ref - y_tr_ref))

    mae_curr = float(np.mean(np.abs(y_pr_curr - y_tr_curr)))
    rmse_curr = float(np.sqrt(np.mean((y_pr_curr - y_tr_curr) ** 2)))
    bias_curr = float(np.mean(y_pr_curr - y_tr_curr))

    rmse_change_pct = ((rmse_curr - rmse_ref) / rmse_ref * 100.0) if rmse_ref > 0 else 0.0
    mae_change_pct = ((mae_curr - mae_ref) / mae_ref * 100.0) if mae_ref > 0 else 0.0

    skill_degraded = (rmse_change_pct >= (SKILL_DEGRADATION_THRESHOLD * 100.0))

    return {
        "ref_samples": len(y_tr_ref),
        "curr_samples": len(y_tr_curr),
        "mae_ref": round(mae_ref, 2),
        "rmse_ref": round(rmse_ref, 2),
        "bias_ref": round(bias_ref, 2),
        "mae_curr": round(mae_curr, 2),
        "rmse_curr": round(rmse_curr, 2),
        "bias_curr": round(bias_curr, 2),
        "mae_change_pct": round(mae_change_pct, 2),
        "rmse_change_pct": round(rmse_change_pct, 2),
        "skill_degraded": bool(skill_degraded),
    }


def should_retrain(
    df_drift: pd.DataFrame,
    skill_drift: Dict[str, Any],
    approved_feedback_count: int = 0,
    psi_sig_threshold: float = PSI_HIGH_THRESHOLD,
    feedback_threshold: int = FEEDBACK_COUNT_THRESHOLD,
) -> Dict[str, Any]:
    """Deterministic, rule-based decision engine recommending whether model retraining is advised."""
    reasons = []

    # 1. Feature Drift Rule: Significant drift in primary NWP predictor or >= 3 total features
    sig_features = df_drift[df_drift["psi"] >= psi_sig_threshold]["feature"].tolist()
    if "precip_ensemble" in sig_features:
        reasons.append(f"Significant feature drift detected in primary predictor 'precip_ensemble' (PSI >= {psi_sig_threshold}).")
    if len(sig_features) >= 3:
        reasons.append(f"{len(sig_features)} features exhibit significant distribution drift (PSI >= {psi_sig_threshold}): {', '.join(sig_features[:5])}.")

    # 2. Skill Degradation Rule: RMSE increased by >= threshold
    if skill_drift.get("skill_degraded", False):
        rmse_pct = skill_drift.get("rmse_change_pct", 0.0)
        reasons.append(f"Forecast skill degraded: validation RMSE increased by {rmse_pct:.1f}% (threshold: >= {SKILL_DEGRADATION_THRESHOLD*100:.0f}%).")

    # 3. Forecaster Feedback Rule: Sufficient approved expert corrections collected
    if approved_feedback_count >= feedback_threshold:
        reasons.append(f"Accumulated {approved_feedback_count} approved forecaster corrections (threshold: >= {feedback_threshold}).")

    retrain_advised = len(reasons) > 0

    return {
        "should_retrain": retrain_advised,
        "reasons": reasons if retrain_advised else ["No significant feature drift, skill degradation, or feedback threshold reached."],
        "sig_feature_count": len(sig_features),
        "sig_features": sig_features,
        "approved_feedback_count": approved_feedback_count,
    }


def generate_drift_markdown_report(
    ref_window: Tuple[str, str],
    curr_window: Tuple[str, str],
    df_drift: pd.DataFrame,
    skill_drift: Dict[str, Any],
    decision: Dict[str, Any],
    output_report_path: Path | str,
) -> Path:
    """Generate comprehensive MLOps Drift Monitoring Report (REPORT.md)."""
    output_report_path = Path(output_report_path)
    output_report_path.parent.mkdir(parents=True, exist_ok=True)

    sig_feats = df_drift[df_drift["severity"] == "High"]
    mod_feats = df_drift[df_drift["severity"] == "Medium"]

    status_badge = "⚠️ RETRAINING RECOMMENDED" if decision["should_retrain"] else "✅ STABLE — NO RETRAINING NEEDED"

    md_content = f"""# MLOps Drift Monitoring & Model Health Report (Task 11)

> **Track B (Baljeet) — PS 26080**  
> **Status**: `{status_badge}`  
> **Evaluated Windows**: Chronological Reference vs Current Windows (Zero Lookahead)  
> **Data Status**: `SYNTHETIC FIXTURE / DEMO VALIDATION`

---

## 1. Monitoring Window Specifications

- **Reference Window**: `{ref_window[0]}` to `{ref_window[1]}` ({skill_drift.get('ref_samples', 'N/A')} grid samples)
- **Current Evaluation Window**: `{curr_window[0]}` to `{curr_window[1]}` ({skill_drift.get('curr_samples', 'N/A')} grid samples)
- **Features Monitored**: Exact 19 input features consumed by Track B ML Bias Corrector.

---

## 2. Statistical Feature Drift Summary

| Metric | Threshold Rule | Description |
|---|---|---|
| **Low / No Drift** | `PSI < 0.10` | Distributions are statistically consistent |
| **Moderate Drift** | `0.10 <= PSI < 0.25` | Minor distribution shift; continue monitoring |
| **Significant Drift** | `PSI >= 0.25` | Substantial distribution shift; potential retraining trigger |

### Feature Summary
- **High Severity Drift Features (`PSI >= 0.25`)**: `{len(sig_feats)}` ({', '.join(sig_feats['feature'].tolist()) if len(sig_feats) > 0 else 'None'})
- **Medium Severity Drift Features (`0.10 <= PSI < 0.25`)**: `{len(mod_feats)}` ({', '.join(mod_feats['feature'].tolist()) if len(mod_feats) > 0 else 'None'})

### Detailed Feature Drift Table
| Feature | Reference Mean | Current Mean | Mean Diff | PSI | KS Stat | KS p-value | Severity |
|---|---|---|---|---|---|---|---|
"""
    for _, r in df_drift.iterrows():
        md_content += f"| `{r['feature']}` | `{r['reference_mean']}` | `{r['current_mean']}` | `{r['mean_diff']}` | **`{r['psi']}`** | `{r['ks_statistic']}` | `{r['ks_pvalue']}` | `{r['severity']}` |\n"

    md_content += f"""
---

## 3. Forecast Skill Degradation Summary

| Metric | Reference Period | Current Period | Change (%) | Status |
|---|---|---|---|---|
| **MAE** | `{skill_drift.get('mae_ref', 'N/A')} mm` | `{skill_drift.get('mae_curr', 'N/A')} mm` | `{skill_drift.get('mae_change_pct', 'N/A')}%` | {'⚠️ Degraded' if skill_drift.get('mae_change_pct', 0) > 15 else '✅ Normal'} |
| **RMSE** | `{skill_drift.get('rmse_ref', 'N/A')} mm` | `{skill_drift.get('rmse_curr', 'N/A')} mm` | `{skill_drift.get('rmse_change_pct', 'N/A')}%` | {'⚠️ Degraded' if skill_drift.get('rmse_change_pct', 0) > 15 else '✅ Normal'} |
| **Mean Bias** | `{skill_drift.get('bias_ref', 'N/A')} mm` | `{skill_drift.get('bias_curr', 'N/A')} mm` | — | {'⚠️ Bias Shift' if abs(skill_drift.get('bias_curr', 0) - skill_drift.get('bias_ref', 0)) > 5.0 else '✅ Stable'} |

---

## 4. Retraining Decision & Action Items

- **Should Retrain**: **`{decision['should_retrain']}`**
- **Approved Feedback Records Available**: `{decision['approved_feedback_count']}`
- **Trigger Reasons**:
"""
    for reason in decision["reasons"]:
        md_content += f"  - {reason}\n"

    md_content += """
---

## 5. Engineering Limitations & Disclosures

> [!IMPORTANT]
> **Operational Context**:
> These drift diagnostics are computed on synthetic fixture data for pipeline validation. Configurable heuristic thresholds (`PSI >= 0.25`, `RMSE degradation >= 15%`) will be tuned against multi-year operational monsoon distributions when Track A real data is ingested.
"""

    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Updated drift report at: {output_report_path}")
    return output_report_path


def run_drift_monitoring_pipeline(
    ensemble_path: Path | str = "data/processed/ensemble_grid.nc",
    obs_path: Path | str = "data/processed/obs_grid.nc",
    climatology_path: Path | str = "data/processed/climatology.nc",
    regime_preds_path: Path | str = "data/processed/regime_predictions.csv",
    features_daily_path: Path | str = "data/processed/features_daily.csv",
    feedback_csv_path: Path | str = "data/feedback/forecaster_feedback.csv",
    output_report_path: Path | str = "src/mlops/drift_monitoring/REPORT.md",
    output_csv_path: Path | str = "data/processed/drift_feature_report.csv",
    train_ratio: float = 0.75,
) -> Dict[str, Any]:
    """Execute complete feature & skill drift monitoring pipeline."""
    ensemble_path = Path(ensemble_path)
    obs_path = Path(obs_path)
    climatology_path = Path(climatology_path)
    regime_preds_path = Path(regime_preds_path)
    features_daily_path = Path(features_daily_path)
    feedback_csv_path = Path(feedback_csv_path)

    ds_ens = xr.open_dataset(ensemble_path)
    ds_obs = xr.open_dataset(obs_path)
    ds_clim = xr.open_dataset(climatology_path)
    df_reg = pd.read_csv(regime_preds_path)
    df_feat = pd.read_csv(features_daily_path)

    corrector = MLGradientBoostedCorrector(random_state=42)
    corrector.fit(
        ds_ens=ds_ens,
        ds_obs=ds_obs,
        ds_clim=ds_clim,
        df_reg=df_reg,
        df_feat=df_feat,
        train_ratio=train_ratio,
    )

    df_X, targets, metadata_tuples = corrector._build_tabular_features(
        ds_ens=ds_ens,
        ds_clim=ds_clim,
        df_reg=df_reg,
        df_feat=df_feat,
        ds_obs=ds_obs,
    )

    dates = sorted(list(set([t[0] for t in metadata_tuples])))
    split_idx = max(1, int(len(dates) * train_ratio))

    ref_dates = dates[:split_idx]
    curr_dates = dates[split_idx:]

    ref_mask = [t[0] in ref_dates for t in metadata_tuples]
    curr_mask = [t[0] in curr_dates for t in metadata_tuples]

    df_ref = df_X[ref_mask].reset_index(drop=True)
    df_curr = df_X[curr_mask].reset_index(drop=True)

    targets_ref = targets[ref_mask]
    targets_curr = targets[curr_mask]

    preds_ref = corrector.model.predict(df_ref[corrector.feature_names])
    preds_curr = corrector.model.predict(df_curr[corrector.feature_names])

    # 1. Feature Drift
    df_drift = compute_feature_drift(df_ref, df_curr, corrector.feature_names)
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    df_drift.to_csv(output_csv_path, index=False)
    logger.info(f"Saved feature drift table to: {output_csv_path}")

    # 2. Skill Drift
    skill_drift = compute_skill_drift(targets_ref, preds_ref, targets_curr, preds_curr)

    # 3. Approved forecaster feedback count
    approved_count = 0
    if feedback_csv_path.exists():
        try:
            df_fb = pd.read_csv(feedback_csv_path)
            approved_count = len(df_fb[df_fb["status"] == "approved_for_retraining"])
        except Exception as e:
            logger.warning(f"Could not read feedback file: {e}")

    # 4. Retraining decision
    decision = should_retrain(df_drift, skill_drift, approved_count)

    # 5. Generate markdown report
    ref_window = (ref_dates[0], ref_dates[-1])
    curr_window = (curr_dates[0], curr_dates[-1])
    generate_drift_markdown_report(
        ref_window, curr_window, df_drift, skill_drift, decision, output_report_path
    )

    return {
        "feature_drift_df": df_drift,
        "skill_drift": skill_drift,
        "decision": decision,
        "ref_window": ref_window,
        "curr_window": curr_window,
    }


def main():
    """CLI entry point for drift monitoring."""
    parser = argparse.ArgumentParser(description="MLOps Drift Monitoring (Track B - Task 11)")
    parser.add_argument("--ensemble", type=str, default="data/processed/ensemble_grid.nc")
    parser.add_argument("--obs", type=str, default="data/processed/obs_grid.nc")
    parser.add_argument("--climatology", type=str, default="data/processed/climatology.nc")
    parser.add_argument("--regime_preds", type=str, default="data/processed/regime_predictions.csv")
    parser.add_argument("--features_daily", type=str, default="data/processed/features_daily.csv")
    parser.add_argument("--feedback", type=str, default="data/feedback/forecaster_feedback.csv")
    parser.add_argument("--report", type=str, default="src/mlops/drift_monitoring/REPORT.md")
    parser.add_argument("--output_csv", type=str, default="data/processed/drift_feature_report.csv")

    args = parser.parse_args()

    results = run_drift_monitoring_pipeline(
        ensemble_path=args.ensemble,
        obs_path=args.obs,
        climatology_path=args.climatology,
        regime_preds_path=args.regime_preds,
        features_daily_path=args.features_daily,
        feedback_csv_path=args.feedback,
        output_report_path=args.report,
        output_csv_path=args.output_csv,
    )
    logger.info("Drift monitoring execution complete!")


if __name__ == "__main__":
    main()
