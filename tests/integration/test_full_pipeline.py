"""Integration test: full pipeline on fixture data.

Verifies that running the complete Track C pipeline on fixture data
produces all expected output files with correct schemas.
"""

import json
import os
import sys
from pathlib import Path

import pytest
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
os.environ["CONFIG_PATH"] = str(ROOT / "config.test.yaml")

from src.config import get_path


class TestFullPipeline:
    """Run all Track C stages and verify outputs."""

    @pytest.fixture(autouse=True, scope="class")
    def run_pipeline(self):
        """Run all Track C stages once before all tests in this class."""
        from src.district_agg import run as run_aggregate
        from src.verification import run as run_verify
        from src.alerts import run as run_alerts

        run_aggregate()
        run_verify()
        run_alerts()

    # ------------------------------------------------------------------
    # District aggregation
    # ------------------------------------------------------------------
    def test_district_table_exists(self):
        assert get_path("outputs.district_table").exists()

    def test_district_table_schema(self):
        df = pd.read_csv(get_path("outputs.district_table"))
        required = [
            "district_name", "date", "corrected_rainfall_mm",
            "rainfall_category", "p_heavy", "p_very_heavy",
            "uncertainty_lower", "uncertainty_upper",
            "dominant_regime", "regime_confidence", "correction_method",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_district_table_not_empty(self):
        df = pd.read_csv(get_path("outputs.district_table"))
        assert len(df) > 0

    # ------------------------------------------------------------------
    # Station aggregation
    # ------------------------------------------------------------------
    def test_station_table_exists(self):
        assert get_path("outputs.station_table").exists()

    def test_station_table_has_stations(self):
        df = pd.read_csv(get_path("outputs.station_table"))
        assert "station_id" in df.columns
        assert len(df["station_id"].unique()) > 0

    # ------------------------------------------------------------------
    # Verification report
    # ------------------------------------------------------------------
    def test_verification_overall_exists(self):
        report_dir = get_path("outputs.verification_report")
        assert (report_dir / "overall_metrics.csv").exists()

    def test_verification_regime_exists(self):
        report_dir = get_path("outputs.verification_report")
        assert (report_dir / "per_regime_metrics.csv").exists()

    def test_verification_fss_exists(self):
        report_dir = get_path("outputs.verification_report")
        assert (report_dir / "fss_scores.csv").exists()

    def test_verification_reliability_exists(self):
        report_dir = get_path("outputs.verification_report")
        assert (report_dir / "reliability_data.json").exists()

    def test_verification_report_md_exists(self):
        report_dir = get_path("outputs.verification_report")
        assert (report_dir / "REPORT.md").exists()

    def test_verification_has_multiple_sources(self):
        df = pd.read_csv(get_path("outputs.verification_report") / "overall_metrics.csv")
        assert len(df["source"].unique()) >= 2  # at least raw_nwp + corrected

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------
    def test_alerts_json_exists(self):
        alerts_path = get_path("outputs.alerts_log") / "alerts.json"
        assert alerts_path.exists()

    def test_alerts_valid_json(self):
        alerts_path = get_path("outputs.alerts_log") / "alerts.json"
        with open(alerts_path) as f:
            alerts = json.load(f)
        assert isinstance(alerts, list)

    def test_alerts_have_required_fields(self):
        alerts_path = get_path("outputs.alerts_log") / "alerts.json"
        with open(alerts_path) as f:
            alerts = json.load(f)
        if alerts:
            required = ["severity", "district_name", "date", "message"]
            for field in required:
                assert field in alerts[0], f"Alert missing field: {field}"
