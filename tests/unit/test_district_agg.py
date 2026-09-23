"""Unit tests for district & station aggregation."""

import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# Use test config
os.environ["CONFIG_PATH"] = str(ROOT / "config.test.yaml")


class TestDistrictAggregator:
    """Tests for src/district_agg/district_aggregator.py."""

    def test_classify_rainfall_categories(self):
        from src.district_agg.district_aggregator import _classify_rainfall

        assert _classify_rainfall(0) == "no_rain"
        assert _classify_rainfall(2.4) == "no_rain"
        assert _classify_rainfall(5) == "light"
        assert _classify_rainfall(20) == "moderate"
        assert _classify_rainfall(65) == "heavy"
        assert _classify_rainfall(120) == "very_heavy"
        assert _classify_rainfall(210) == "extremely_heavy"

    def test_point_in_polygon(self):
        from src.district_agg.district_aggregator import _point_in_polygon

        # Simple square polygon: (0,0) to (10,10)
        polygon = [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]

        assert _point_in_polygon(5, 5, polygon) is True
        assert _point_in_polygon(0.5, 0.5, polygon) is True
        assert _point_in_polygon(15, 5, polygon) is False
        assert _point_in_polygon(-1, 5, polygon) is False

    def test_aggregate_districts_produces_output(self):
        from src.district_agg.district_aggregator import aggregate_districts
        from src.config import get_path

        aggregate_districts()

        out_path = get_path("outputs.district_table")
        assert out_path.exists(), f"district_table.csv not created at {out_path}"

        df = pd.read_csv(out_path)
        assert len(df) > 0, "district_table.csv is empty"

        # Check required columns
        required_cols = [
            "district_name", "date", "corrected_rainfall_mm",
            "rainfall_category", "p_heavy", "p_very_heavy",
            "uncertainty_lower", "uncertainty_upper",
            "dominant_regime", "regime_confidence", "correction_method",
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_district_rainfall_non_negative(self):
        from src.district_agg.district_aggregator import aggregate_districts
        from src.config import get_path

        aggregate_districts()
        df = pd.read_csv(get_path("outputs.district_table"))
        assert (df["corrected_rainfall_mm"] >= 0).all(), "Negative rainfall values found"


class TestStationAggregator:
    """Tests for src/district_agg/station_aggregator.py."""

    def test_nearest_grid_idx(self):
        from src.district_agg.station_aggregator import _nearest_grid_idx

        grid = np.array([18.0, 19.0, 20.0, 21.0, 22.0])
        assert _nearest_grid_idx(18.5, grid) == 0 or _nearest_grid_idx(18.5, grid) == 1
        assert _nearest_grid_idx(22.0, grid) == 4
        assert _nearest_grid_idx(17.0, grid) == 0

    def test_aggregate_stations_produces_output(self):
        from src.district_agg.station_aggregator import aggregate_stations
        from src.config import get_path

        aggregate_stations()

        out_path = get_path("outputs.station_table")
        assert out_path.exists()

        df = pd.read_csv(out_path)
        assert len(df) > 0
        assert "station_id" in df.columns
        assert "corrected_rainfall_mm" in df.columns
