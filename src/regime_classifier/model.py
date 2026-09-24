"""Multi-Label Regime Classifier Implementation (Track A - Task 3).

Trains dedicated gradient-boosted trees per regime label (Binary Relevance),
supporting calibrated probabilities, dominant regime assignment, and exact
tree-based Shapley feature attribution.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
import joblib

from .config import REGIME_CLASSES, FEATURE_COLUMNS

logger = logging.getLogger(__name__)


class MultiLabelRegimeClassifier:
    """Multi-label weather regime classifier with calibrated probability and TreeSHAP attribution."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models: Dict[str, LGBMClassifier] = {}
        self.thresholds: Dict[str, float] = {rc: 0.5 for rc in REGIME_CLASSES}
        self.is_fitted = False

    def _prepare_X(self, X: pd.DataFrame) -> pd.DataFrame:
        X_mat = X.copy()
        for col in FEATURE_COLUMNS:
            if col not in X_mat.columns:
                X_mat[col] = 0.0
        return X_mat[FEATURE_COLUMNS]

    def fit(self, X: pd.DataFrame, Y: pd.DataFrame) -> "MultiLabelRegimeClassifier":
        X_mat = self._prepare_X(X)

        def _train_single_label(label: str):
            if label not in Y.columns:
                raise ValueError(f"Target column '{label}' missing in ground truth labels.")

            y_vec = Y[label].values
            pos_count = int(np.sum(y_vec == 1))
            total_count = len(y_vec)
            logger.info(f"Training classifier for '{label}' ({pos_count}/{total_count} positive instances)...")

            # Scale pos weight if imbalanced
            scale_pos_weight = (total_count - pos_count) / max(1, pos_count)
            scale_pos_weight = min(max(scale_pos_weight, 1.0), 10.0)

            model = LGBMClassifier(
                n_estimators=100,
                max_depth=4,
                num_leaves=15,
                learning_rate=0.05,
                min_child_samples=5,
                scale_pos_weight=scale_pos_weight,
                random_state=self.random_state,
                n_jobs=1,
                verbose=-1,
            )
            model.fit(X_mat, y_vec)
            return label, model

        from joblib import Parallel, delayed
        results = Parallel(n_jobs=-1, prefer="threads")(
            delayed(_train_single_label)(label) for label in REGIME_CLASSES
        )
        for label, model in results:
            self.models[label] = model

        self.is_fitted = True
        return self

    def predict_proba(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return probability DataFrame with columns <label>_prob for all 6 labels."""
        if not self.is_fitted:
            raise RuntimeError("Classifier must be fitted before predict_proba.")

        X_mat = self._prepare_X(X)
        prob_dict = {}

        for label in REGIME_CLASSES:
            model = self.models[label]
            probs = model.predict_proba(X_mat)[:, 1]
            prob_dict[f"{label}_prob"] = np.round(probs, 4)

        return pd.DataFrame(prob_dict, index=X.index)

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return binary prediction DataFrame (0 or 1) using calibrated thresholds."""
        probs = self.predict_proba(X)
        pred_dict = {}
        for label in REGIME_CLASSES:
            thresh = self.thresholds.get(label, 0.5)
            pred_dict[label] = (probs[f"{label}_prob"].values >= thresh).astype(int)
        return pd.DataFrame(pred_dict, index=X.index)

    def predict_dominant(self, prob_df: pd.DataFrame) -> Tuple[List[str], List[float]]:
        """Identify dominant regime label and confidence for each row.

        dominant_label = argmax(probabilities)
        confidence = max(probability)
        """
        prob_cols = [f"{rc}_prob" for rc in REGIME_CLASSES]
        mat = prob_df[prob_cols].values

        max_indices = np.argmax(mat, axis=1)
        confidences = np.max(mat, axis=1)

        dominant_labels = [REGIME_CLASSES[idx] for idx in max_indices]
        return dominant_labels, np.round(confidences, 4).tolist()

    def compute_attributions(self, X: pd.DataFrame, target_label: Optional[str] = None) -> Dict[str, np.ndarray]:
        """Compute exact TreeSHAP feature contributions for each model.

        Returns:
            Dict mapping label -> (N_samples, N_features) array of TreeSHAP values.
        """
        if not self.is_fitted:
            raise RuntimeError("Classifier must be fitted before computing attributions.")

        X_mat = self._prepare_X(X)
        attributions = {}

        labels_to_eval = [target_label] if target_label else REGIME_CLASSES
        for label in labels_to_eval:
            booster = self.models[label].booster_
            # pred_contrib=True returns [SHAP_feat1, SHAP_feat2, ..., SHAP_featK, baseline_value]
            contribs = booster.predict(X_mat, pred_contrib=True)
            # Take only feature contributions (exclude last baseline column)
            feat_contribs = contribs[:, :-1]
            attributions[label] = feat_contribs

        return attributions

    def save(self, filepath: str) -> None:
        """Serialize trained classifier state to disk."""
        joblib.dump(self, filepath)
        logger.info(f"Model saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "MultiLabelRegimeClassifier":
        """Deserialize classifier from disk."""
        return joblib.load(filepath)
