"""Track A (Pradeep): Weather regime classification model training, inference, and explainability.

Tasks owned:
- Task 3: Train/evaluate multi-label regime classifier (active, break, low_depression, western_disturbance, orographic, coastal).

Contracts consumed:
- data/processed/features_daily.csv
- data/processed/regime_labels.csv

Contracts produced:
- data/processed/regime_predictions.csv (date, active_prob, ..., dominant_label, confidence)
- src/regime_classifier/EVAL.md (held-out accuracy/confusion matrix)
- src/regime_classifier/explanations/attributions.csv (TreeSHAP attributions)
"""

import logging
from pathlib import Path

from .train import train_regime_classifier
from .evaluate import evaluate_classifier
from .predict import generate_regime_predictions
from .model import MultiLabelRegimeClassifier
from ..explainability.regime_attribution import generate_regime_attributions

logger = logging.getLogger(__name__)


def run() -> None:
    """Execute Track A Regime Classifier & Explainability pipeline stage."""
    project_root = Path(__file__).resolve().parent.parent.parent
    try:
        from src.config import get_path
        regime_preds_path = get_path("data.regime_predictions")
        processed_dir = regime_preds_path.parent
    except Exception:
        processed_dir = project_root / "data" / "processed"
        regime_preds_path = processed_dir / "regime_predictions.csv"

    classifier_dir = project_root / "src" / "regime_classifier"
    model_path = classifier_dir / "regime_model.joblib"
    eval_md_path = classifier_dir / "EVAL.md"
    explanations_dir = classifier_dir / "explanations"

    logger.info("Step 1/4: Training Multi-Label Weather Regime Classifier...")
    clf = train_regime_classifier(processed_dir, model_path)

    logger.info("Step 2/4: Evaluating on held-out test data and generating EVAL.md...")
    evaluate_classifier(clf, processed_dir, eval_md_path)

    logger.info("Step 3/4: Generating regime predictions for full dataset...")
    generate_regime_predictions(clf, processed_dir, regime_preds_path)

    logger.info("Step 4/4: Generating per-prediction TreeSHAP attributions...")
    generate_regime_attributions(clf, processed_dir, explanations_dir)

    logger.info("Task 3 Regime Classifier & Explainability: ALL DELIVERABLES GENERATED.")


__all__ = [
    "run",
    "train_regime_classifier",
    "evaluate_classifier",
    "generate_regime_predictions",
    "MultiLabelRegimeClassifier",
]

