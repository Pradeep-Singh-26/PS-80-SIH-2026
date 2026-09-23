"""Shared Explainability Utilities (Cross-Track Common Module).

Per TEAM_SPLIT.md Rule 3:
"If a shared utility is needed, it goes in src/explainability/common/ and either
party may add to it, but neither may modify the other's method-specific files there."
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def normalize_attributions(attributions: np.ndarray) -> np.ndarray:
    """Normalize feature attributions so absolute values sum to 1 per sample."""
    denom = np.sum(np.abs(attributions), axis=1, keepdims=True)
    denom = np.where(denom == 0, 1.0, denom)
    return attributions / denom


def format_attribution_dataframe(
    dates: List[str],
    feature_names: List[str],
    attribution_matrix: np.ndarray,
) -> pd.DataFrame:
    """Convert an (N_samples, N_features) attribution matrix to long format (date, feature, attribution_value).

    Schema:
        date, feature, attribution_value
    """
    n_samples, n_features = attribution_matrix.shape
    return pd.DataFrame({
        "date": np.repeat(dates, n_features),
        "feature": np.tile(feature_names, n_samples),
        "attribution_value": np.round(attribution_matrix.flatten(), 4),
    })


def extract_top_features_per_prediction(
    df_long: pd.DataFrame, top_k: int = 3
) -> pd.DataFrame:
    """Extract top-k most influential features (by absolute attribution) for each date."""
    df_sorted = df_long.reindex(
        df_long.attribution_value.abs().sort_values(ascending=False).index
    )
    return df_sorted.groupby("date").head(top_k).reset_index(drop=True)
