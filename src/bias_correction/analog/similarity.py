"""Atmospheric & Synoptic Similarity Search Engine for Analog Forecasting (Track B - Task 4).

Finds historical analog days based on standardized Euclidean distance in multi-variable
synoptic/physical feature space, conditioned on weather regimes with strict leakage prevention.
"""

import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("analog_similarity")

ANALOG_FEATURE_COLS = [
    "mslp_anomaly",
    "olr_anomaly",
    "satellite_proxy",
    "rainfall_anomaly",
    "lps_flag",
    "wd_flag",
    "u850_anomaly",
    "v850_anomaly",
]

REGIME_PROB_COLS = [
    "active_prob",
    "break_prob",
    "low_depression_prob",
    "western_disturbance_prob",
    "orographic_prob",
    "coastal_prob",
]


class AnalogFeatureProcessor:
    """Builds and standardizes multi-variable synoptic feature vectors for analog search."""

    def __init__(self, include_regime_probs: bool = True):
        self.include_regime_probs = include_regime_probs
        self.feature_names: List[str] = []
        self.means: Dict[str, float] = {}
        self.stds: Dict[str, float] = {}
        self.is_fitted = False

    def fit(self, df_features: pd.DataFrame, df_regimes: Optional[pd.DataFrame] = None) -> "AnalogFeatureProcessor":
        """Fit standardization statistics (mean, std) on the historical candidate pool."""
        df_merged = self._merge_features(df_features, df_regimes)

        cols = [c for c in ANALOG_FEATURE_COLS if c in df_merged.columns]
        if self.include_regime_probs and df_regimes is not None:
            cols += [c for c in REGIME_PROB_COLS if c in df_merged.columns]

        self.feature_names = cols
        for col in self.feature_names:
            series = df_merged[col].dropna()
            self.means[col] = float(series.mean()) if len(series) > 0 else 0.0
            std_val = float(series.std()) if len(series) > 1 else 1.0
            self.stds[col] = std_val if std_val > 1e-6 else 1.0

        self.is_fitted = True
        return self

    def transform_vector(self, row_dict: Dict[str, float]) -> np.ndarray:
        """Extract and normalize a single day's feature vector."""
        if not self.is_fitted:
            # Fallback if called before fit
            return np.zeros(len(ANALOG_FEATURE_COLS), dtype=np.float32)

        vec = []
        for col in self.feature_names:
            raw_val = float(row_dict.get(col, self.means[col]))
            if np.isnan(raw_val):
                raw_val = self.means[col]
            norm_val = (raw_val - self.means[col]) / self.stds[col]
            vec.append(norm_val)

        return np.array(vec, dtype=np.float32)

    def _merge_features(self, df_features: pd.DataFrame, df_regimes: Optional[pd.DataFrame]) -> pd.DataFrame:
        df_f = df_features.copy()
        df_f["date_str"] = pd.to_datetime(df_f["date"]).dt.strftime("%Y-%m-%d")

        if df_regimes is not None:
            df_r = df_regimes.copy()
            df_r["date_str"] = pd.to_datetime(df_r["date"]).dt.strftime("%Y-%m-%d")
            return pd.merge(df_f, df_r, on="date_str", how="inner", suffixes=("", "_reg"))
        return df_f


class AnalogSearchEngine:
    """Finds top-k historical analog days matching a target synoptic profile and weather regime."""

    def __init__(
        self,
        top_k: int = 5,
        regime_penalty: float = 2.0,
        min_same_regime: int = 2,
        mode: str = "leave_one_out",
    ):
        self.top_k = top_k
        self.regime_penalty = regime_penalty
        self.min_same_regime = min_same_regime
        self.mode = mode  # 'leave_one_out' or 'strict_chronological'
        self.processor = AnalogFeatureProcessor()
        self.historical_pool: List[Dict] = []
        self.is_indexed = False

    def build_index(
        self,
        df_features: pd.DataFrame,
        df_regimes: pd.DataFrame,
    ) -> "AnalogSearchEngine":
        """Index all available historical candidate days with their standardized features."""
        self.processor.fit(df_features, df_regimes)

        df_merged = self.processor._merge_features(df_features, df_regimes)
        self.historical_pool = []

        for _, row in df_merged.iterrows():
            d_str = row["date_str"]
            regime = str(row.get("dominant_label", "unknown")).lower().strip()
            row_dict = row.to_dict()
            norm_vec = self.processor.transform_vector(row_dict)

            self.historical_pool.append({
                "date": d_str,
                "regime": regime,
                "vector": norm_vec,
                "raw_dict": row_dict,
            })

        self.is_indexed = True
        logger.info(f"Indexed {len(self.historical_pool)} historical analog candidate days.")
        return self

    def find_analogs(
        self,
        target_date: str,
        target_dict: Dict[str, float],
        target_regime: str,
    ) -> Dict:
        """Find the top-k nearest historical analogs for a target date with leakage prevention."""
        target_date_str = pd.to_datetime(target_date).strftime("%Y-%m-%d")
        target_regime_clean = str(target_regime).lower().strip()
        target_vec = self.processor.transform_vector(target_dict)

        fallback_used = False
        fallback_reason = "normal_match"

        # 1. Candidate selection with strict leakage prevention
        candidates = []
        for item in self.historical_pool:
            cand_date = item["date"]
            # Strict rule: NEVER allow target date to be its own analog
            if cand_date == target_date_str:
                continue

            # In strict chronological mode, only allow dates before target date
            if self.mode == "strict_chronological" and cand_date >= target_date_str:
                continue

            candidates.append(item)

        if len(candidates) == 0:
            if self.mode == "strict_chronological":
                return {
                    "analog_dates": [],
                    "analog_regimes": [],
                    "distances": [],
                    "weights": [],
                    "fallback_used": True,
                    "message": "no_prior_history_no_correction",
                }
            else:
                # In leave_one_out mode, fallback to all non-target dates
                fallback_used = True
                fallback_reason = "no_prior_history_fallback_to_leave_one_out"
                candidates = [c for c in self.historical_pool if c["date"] != target_date_str]

        if len(candidates) == 0:
            # Empty candidate database entirely
            return {
                "analog_dates": [],
                "analog_regimes": [],
                "distances": [],
                "weights": [],
                "fallback_used": True,
                "message": "no_candidates_available",
            }

        # 2. Check same-regime candidate availability
        same_regime_candidates = [c for c in candidates if c["regime"] == target_regime_clean]

        if len(same_regime_candidates) >= self.min_same_regime:
            active_pool = same_regime_candidates
        else:
            active_pool = candidates
            fallback_used = True
            fallback_reason = f"insufficient_same_regime_samples_{len(same_regime_candidates)}<min_{self.min_same_regime}"

        # 3. Compute Standardized Euclidean Distances
        cand_results = []
        for cand in active_pool:
            diff = target_vec - cand["vector"]
            base_dist = float(np.sqrt(np.sum(diff ** 2)))

            # Apply regime penalty if candidate regime does not match target
            if cand["regime"] != target_regime_clean:
                effective_dist = base_dist + self.regime_penalty
            else:
                effective_dist = base_dist

            cand_results.append({
                "date": cand["date"],
                "regime": cand["regime"],
                "distance": effective_dist,
            })

        # Sort by distance ascending
        cand_results.sort(key=lambda x: x["distance"])
        k = min(self.top_k, len(cand_results))
        top_matches = cand_results[:k]

        # 4. Compute Inverse Distance Weights
        distances = [m["distance"] for m in top_matches]
        epsilon = 1e-4
        inv_dists = [1.0 / (d + epsilon) for d in distances]
        sum_inv = sum(inv_dists)
        weights = [float(iv / sum_inv) for iv in inv_dists] if sum_inv > 0 else [1.0 / k] * k

        return {
            "analog_dates": [m["date"] for m in top_matches],
            "analog_regimes": [m["regime"] for m in top_matches],
            "distances": [round(float(d), 4) for d in distances],
            "weights": [round(float(w), 4) for w in weights],
            "fallback_used": fallback_used,
            "message": fallback_reason if fallback_used else "matched_same_regime",
        }
