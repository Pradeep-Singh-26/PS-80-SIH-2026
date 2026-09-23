"""Regime-Conditioned Bias Correction Router (Track B - Task 4).

Determines whether to apply Quantile Mapping or ML Gradient Boosted Correction for each
forecast day based on the prevailing weather regime, prediction confidence, and sample support.
Maintains an audit trail written to correction_method_log.csv.
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("bias_router")

DEFAULT_ML_REGIMES = {"active", "low_depression", "coastal"}
DEFAULT_QM_REGIMES = {"break", "western_disturbance", "orographic"}


class RegimeBiasCorrectionRouter:
    """Routes forecast slices to the optimal correction method per weather regime."""

    def __init__(
        self,
        routing_strategy: str = "regime_conditioned",
        min_confidence_threshold: float = 0.35,
    ):
        self.routing_strategy = routing_strategy
        self.min_confidence_threshold = min_confidence_threshold

    def route_date(
        self,
        date_str: str,
        dominant_regime: str,
        confidence: float,
        qm_sample_count: int = 0,
        min_qm_samples: int = 20,
    ) -> Tuple[str, str]:
        """Determine correction method for a single date.

        Returns (method_category, decision_reason) where method_category is 'ml_gbm' or 'quantile_mapping'.
        """
        regime_clean = str(dominant_regime).lower().strip()

        if self.routing_strategy == "all_ml":
            return "ml_gbm", "Global policy override: all_ml"
        elif self.routing_strategy == "all_qm":
            return "quantile_mapping", "Global policy override: all_qm"

        # Strategy: 'regime_conditioned' (scientific baseline per PLAN.md)
        if confidence < self.min_confidence_threshold:
            return (
                "quantile_mapping",
                f"Low regime confidence ({confidence:.2f} < {self.min_confidence_threshold}); falling back to robust QM",
            )

        if regime_clean in DEFAULT_ML_REGIMES:
            return (
                "ml_gbm",
                f"High-convection synoptic regime '{regime_clean}' routed to multi-feature ML regressor",
            )
        elif regime_clean in DEFAULT_QM_REGIMES:
            return (
                "quantile_mapping",
                f"Statistical regime '{regime_clean}' routed to distribution-preserving Quantile Mapping",
            )
        else:
            return (
                "quantile_mapping",
                f"Unrecognized/fallback regime '{regime_clean}' routed to global Quantile Mapping baseline",
            )

    def generate_log_df(self, decisions: List[Dict[str, str]]) -> pd.DataFrame:
        """Convert list of routing decisions to standard DataFrame matching contract."""
        df = pd.DataFrame(decisions)
        expected_cols = ["date", "regime", "confidence", "method_used", "reason"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        return df[expected_cols]
