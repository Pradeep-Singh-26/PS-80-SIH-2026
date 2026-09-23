"""CLI entry point for Track A Regime Classifier & Explainability (Task 3).

Executes:
1. Model training on training years (2021-2022) -> regime_model.joblib
2. Held-out evaluation on test year (2023) -> src/regime_classifier/EVAL.md
3. Full dataset inference -> data/processed/regime_predictions.csv
4. Per-prediction TreeSHAP attribution -> src/regime_classifier/explanations/attributions.csv

Usage:
    python -m src.regime_classifier.run_classifier
"""

import argparse
import logging
from pathlib import Path

from .train import train_regime_classifier
from .evaluate import evaluate_classifier
from .predict import generate_regime_predictions
from ..explainability.regime_attribution import generate_regime_attributions

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_classifier")


def main():
    parser = argparse.ArgumentParser(description="Track A - Regime Classifier & Explainability Runner (Task 3)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    processed_dir = project_root / "data" / "processed"
    classifier_dir = project_root / "src" / "regime_classifier"
    model_path = classifier_dir / "regime_model.joblib"
    eval_md_path = classifier_dir / "EVAL.md"
    pred_csv_path = processed_dir / "regime_predictions.csv"
    explanations_dir = classifier_dir / "explanations"

    logger.info("Step 1/4: Training Multi-Label Weather Regime Classifier...")
    clf = train_regime_classifier(processed_dir, model_path)

    logger.info("Step 2/4: Evaluating on held-out test data (2023) and generating EVAL.md...")
    evaluate_classifier(clf, processed_dir, eval_md_path)

    logger.info("Step 3/4: Generating regime predictions for full dataset...")
    generate_regime_predictions(clf, processed_dir, pred_csv_path)

    logger.info("Step 4/4: Generating per-prediction TreeSHAP attributions...")
    generate_regime_attributions(clf, processed_dir, explanations_dir)

    logger.info("Task 3 Regime Classifier & Explainability: ALL DELIVERABLES GENERATED.")


if __name__ == "__main__":
    main()
