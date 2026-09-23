# Model Evaluation Report — Multi-Label Regime Classifier (Track A)

> **Generated**: 2026-09-23 15:28:16 UTC  
> **Held-out Test Period**: Monsoon Season 2023 (June 1 – September 30, 122 days)  
> **Model Framework**: Multi-Output / Binary Relevance LightGBM Gradient Boosted Trees  

## 1. Executive Summary & Overall Skill

| Metric | Value | Interpretation |
|---|---|---|
| **Macro F1-Score** | **0.969** | Unweighted average skill across all 6 regime classes |
| **Micro F1-Score** | **0.978** | Global aggregate precision-recall harmonic mean |
| **Exact Match Ratio (Subset Accuracy)** | **0.918** | Fraction of days where all 6 labels matched ground truth perfectly |
| **Hamming Loss** | **0.0137** | Fraction of incorrect individual label predictions (lower is better) |
| **Mean Dominant Confidence** | **0.988** | Average confidence score on primary regime assignment |

## 2. Per-Regime Performance on Held-Out Test Set (2023)

| Weather Regime | Test Support (Days) | Precision | Recall | F1-Score | ROC-AUC |
|---|---|---|---|---|---|
| `active` | 6 | 0.75 | 1.0 | **0.857** | 1.0 |
| `break` | 25 | 1.0 | 1.0 | **1.0** | 1.0 |
| `low_depression` | 18 | 1.0 | 1.0 | **1.0** | 1.0 |
| `western_disturbance` | 4 | 1.0 | 1.0 | **1.0** | 1.0 |
| `orographic` | 79 | 0.987 | 0.987 | **0.987** | 0.99 |
| `coastal` | 94 | 0.949 | 0.989 | **0.969** | 0.97 |

## 3. Confusion Behavior & Contingency Tables

| Regime | True Positive (TP) | False Positive (FP) | False Negative (FN) | True Negative (TN) |
|---|---|---|---|---|
| `active` | 6 | 2 | 0 | 114 |
| `break` | 25 | 0 | 0 | 97 |
| `low_depression` | 18 | 0 | 0 | 104 |
| `western_disturbance` | 4 | 0 | 0 | 118 |
| `orographic` | 78 | 1 | 1 | 42 |
| `coastal` | 93 | 5 | 1 | 23 |

## 4. Key Meteorological Observations & Validation Insights

1. **Active vs. Break Monsoon Discrimination**:
   - The model cleanly separates active and break spells with high precision, driven by `rainfall_anomaly`, `mslp_anomaly`, and `trough_position_lat`.
   - Zero false-positive crossovers between active and break monsoon regimes.

2. **Synoptic Depression Detection** (`low_depression`):
   - High recall on low pressure systems and depressions due to strong physical coupling with `lps_flag` and deep MSLP / OLR vortex anomalies.

3. **Western Disturbance (WD) Identification**:
   - Accurately captures transition-month (early June and late September) mid-latitude interactions in the northern tier of the domain.

4. **Orographic & Coastal Multi-Label Co-occurrence**:
   - Co-occurs naturally with active monsoon and depression passages, validating the multi-label framing over a restrictive single-label setup.

5. **Downstream Pipeline Contract Guarantee**:
   - Generates calibrated probabilities `[0, 1]` for all 6 labels in `data/processed/regime_predictions.csv` alongside `dominant_label` and `confidence` for Track B (Baljeet) and Track C (Divyansh).