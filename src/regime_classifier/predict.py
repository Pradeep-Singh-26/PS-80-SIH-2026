"""Inference and Regime Predictions Generator (Track A - Task 3).

Applies the trained multi-label classifier to features_daily.csv to produce:
- data/processed/regime_predictions.csv
  Columns: date, active_prob, break_prob, low_depression_prob,
           western_disturbance_prob, orographic_prob, coastal_prob,
           dominant_label, confidence
"""

import logging
from pathlib import Path
import pandas as pd
from .config import REGIME_CLASSES
from .model import MultiLabelRegimeClassifier

logger = logging.getLogger(__name__)


def generate_regime_predictions(
    clf: MultiLabelRegimeClassifier,
    processed_dir: Path,
    out_csv: Path,
) -> Path:
    """Generate and write regime_predictions.csv matching contract schema."""
    features_file = processed_dir / "features_daily.csv"
    if not features_file.exists():
        raise FileNotFoundError(f"Missing features file: {features_file}")

    df_X = pd.read_csv(features_file)
    dates = df_X["date"].values

    # Predict probabilities for all 6 regime labels
    prob_df = clf.predict_proba(df_X)

    # Determine dominant regime label and confidence
    dominant_labels, confidences = clf.predict_dominant(prob_df)

    # Construct final contract DataFrame
    res_df = pd.DataFrame({"date": dates})
    for label in REGIME_CLASSES:
        res_df[f"{label}_prob"] = prob_df[f"{label}_prob"].values
    res_df["dominant_label"] = dominant_labels
    res_df["confidence"] = confidences

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(out_csv, index=False)
    logger.info(f"Saved {out_csv} with {len(res_df)} rows and columns: {list(res_df.columns)}")
    return out_csv
