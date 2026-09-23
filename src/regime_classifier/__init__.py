"""Track B (Baljeet): Weather regime classification model training and inference.

Tasks owned:
- Task 3: Train/evaluate 4-class regime classifier (active, break, low_depression, other).

Contracts consumed:
- data/processed/features_daily.csv

Contracts produced:
- data/processed/regime_predictions.csv (date, regime_pred, regime_confidence)
- src/regime_classifier/EVAL.md (held-out accuracy/confusion matrix)
"""
