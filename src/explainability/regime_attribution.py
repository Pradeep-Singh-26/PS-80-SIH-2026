"""Regime Classifier Feature Attribution Module (Track A - Task 3).

Computes per-prediction feature attribution values using exact TreeSHAP,
saving output matching the contract schema in `src/regime_classifier/explanations/`.
Contract schema: date, feature, attribution_value
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import numpy as np
import pandas as pd

from ..regime_classifier.config import FEATURE_COLUMNS, REGIME_CLASSES
from ..regime_classifier.model import MultiLabelRegimeClassifier
from .common import format_attribution_dataframe

logger = logging.getLogger(__name__)


def generate_regime_attributions(
    clf: MultiLabelRegimeClassifier,
    processed_dir: Path,
    explanations_dir: Path,
) -> Path:
    """Compute per-prediction TreeSHAP attributions and save attributions.csv.

    Output Schema:
        date, feature, attribution_value
    """
    features_file = processed_dir / "features_daily.csv"
    pred_file = processed_dir / "regime_predictions.csv"

    if not features_file.exists():
        raise FileNotFoundError(f"Missing features file: {features_file}")
    if not pred_file.exists():
        raise FileNotFoundError(f"Missing predictions file: {pred_file}")

    df_X = pd.read_csv(features_file)
    df_pred = pd.read_csv(pred_file)

    dates = df_X["date"].tolist()
    dominant_regimes = df_pred["dominant_label"].tolist()

    # Compute raw TreeSHAP contributions for all regime models
    # contribs_dict[label] is (N_samples, N_features)
    contribs_dict = clf.compute_attributions(df_X)

    # For each sample, extract attribution vector corresponding to its dominant predicted regime
    n_samples = len(dates)
    n_features = len(FEATURE_COLUMNS)
    sample_attributions = np.zeros((n_samples, n_features), dtype=np.float32)

    for i in range(n_samples):
        dom_label = dominant_regimes[i]
        sample_attributions[i] = contribs_dict[dom_label][i]

    # Convert to standard contract long DataFrame
    df_long = format_attribution_dataframe(dates, FEATURE_COLUMNS, sample_attributions)

    explanations_dir = Path(explanations_dir)
    explanations_dir.mkdir(parents=True, exist_ok=True)
    out_csv = explanations_dir / "attributions.csv"
    df_long.to_csv(out_csv, index=False)
    logger.info(f"Saved {out_csv} with {len(df_long)} rows (schema: date, feature, attribution_value)")

    # Also save a wide summary with dominant feature per date for fast UI lookup (vectorized)
    top_feature_indices = np.argmax(np.abs(sample_attributions), axis=1)
    df_summary = pd.DataFrame({
        "date": dates,
        "top_feature": [FEATURE_COLUMNS[idx] for idx in top_feature_indices],
        "top_attribution": [round(float(sample_attributions[i, idx]), 4) for i, idx in enumerate(top_feature_indices)],
    })
    summary_csv = explanations_dir / "attribution_summary.csv"
    df_summary.to_csv(summary_csv, index=False)

    return out_csv
