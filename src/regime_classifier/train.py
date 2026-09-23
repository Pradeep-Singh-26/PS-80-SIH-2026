"""Model Training Script for Regime Classifier (Track A - Task 3)."""

import logging
from pathlib import Path
import pandas as pd
from .config import TRAIN_YEARS
from .model import MultiLabelRegimeClassifier

logger = logging.getLogger(__name__)


def train_regime_classifier(processed_dir: Path, output_model_path: Path) -> MultiLabelRegimeClassifier:
    """Train multi-label regime classifier on training years and persist to disk."""
    features_file = processed_dir / "features_daily.csv"
    labels_file = processed_dir / "regime_labels.csv"

    if not features_file.exists() or not labels_file.exists():
        raise FileNotFoundError("Processed features_daily.csv or regime_labels.csv not found.")

    df_X = pd.read_csv(features_file)
    df_Y = pd.read_csv(labels_file)

    # Filter training years
    df_X["year"] = pd.to_datetime(df_X["date"]).dt.year
    train_mask = df_X["year"].isin(TRAIN_YEARS)

    X_train = df_X[train_mask].copy()
    Y_train = df_Y[train_mask].copy()

    logger.info(f"Training regime classifier on {len(X_train)} samples from years {TRAIN_YEARS}...")
    clf = MultiLabelRegimeClassifier()
    clf.fit(X_train, Y_train)

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    clf.save(str(output_model_path))
    return clf
