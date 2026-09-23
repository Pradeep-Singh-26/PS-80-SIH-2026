"""Track A (Pradeep): Weather regime classification model training and inference.

Tasks owned:
- Task 3: Train/evaluate 6-class multi-label regime classifier and explainability.

Contracts consumed:
- data/processed/features_daily.csv
- data/processed/regime_labels.csv

Contracts produced:
- data/processed/regime_predictions.csv (date, <label>_prob, dominant_label, confidence)
- src/regime_classifier/EVAL.md (held-out evaluation)
- src/regime_classifier/explanations/attributions.csv
"""

from pathlib import Path
from .train import train_regime_classifier
from .evaluate import evaluate_classifier
from .predict import generate_regime_predictions
from ..explainability.regime_attribution import generate_regime_attributions


def run():
    """Execute Track A multi-label regime classifier and explainability pipeline."""
    project_root = Path(__file__).resolve().parent.parent.parent
    processed_dir = project_root / "data" / "processed"
    classifier_dir = project_root / "src" / "regime_classifier"
    model_path = classifier_dir / "regime_model.joblib"
    eval_md_path = classifier_dir / "EVAL.md"
    pred_csv_path = processed_dir / "regime_predictions.csv"
    explanations_dir = classifier_dir / "explanations"

    clf = train_regime_classifier(processed_dir, model_path)
    evaluate_classifier(clf, processed_dir, eval_md_path)
    generate_regime_predictions(clf, processed_dir, pred_csv_path)
    generate_regime_attributions(clf, processed_dir, explanations_dir)


__all__ = [
    "run",
    "train_regime_classifier",
    "evaluate_classifier",
    "generate_regime_predictions",
    "generate_regime_attributions",
]

