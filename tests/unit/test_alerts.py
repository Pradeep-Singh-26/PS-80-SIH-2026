"""Unit tests for alerting module."""

import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
os.environ["CONFIG_PATH"] = str(ROOT / "config.test.yaml")


class TestAlertRuleEngine:
    def test_evaluate_rule_triggers(self):
        from src.alerts.rule_engine import _evaluate_rule

        rule = {
            "name": "test_rule",
            "conditions": {"p_heavy_min": 0.5, "regime_confidence_min": 0.3},
        }
        row = pd.Series({"p_heavy": 0.7, "regime_confidence": 0.5})
        assert _evaluate_rule(rule, row) is True

    def test_evaluate_rule_does_not_trigger(self):
        from src.alerts.rule_engine import _evaluate_rule

        rule = {
            "name": "test_rule",
            "conditions": {"p_heavy_min": 0.8},
        }
        row = pd.Series({"p_heavy": 0.3})
        assert _evaluate_rule(rule, row) is False

    def test_evaluate_rule_rainfall_threshold(self):
        from src.alerts.rule_engine import _evaluate_rule

        rule = {
            "name": "rainfall_rule",
            "conditions": {"corrected_rainfall_min_mm": 64.5},
        }
        row_above = pd.Series({"corrected_rainfall_mm": 70.0})
        row_below = pd.Series({"corrected_rainfall_mm": 30.0})
        assert _evaluate_rule(rule, row_above) is True
        assert _evaluate_rule(rule, row_below) is False

    def test_load_rules(self):
        from src.alerts.rule_engine import _load_rules

        rules = _load_rules()
        assert len(rules) >= 1
        assert all("name" in r for r in rules)
        assert all("conditions" in r for r in rules)

    def test_generate_alerts_produces_output(self):
        """Requires aggregation to have run first (fixture outputs exist)."""
        from src.config import get_path

        alerts_path = get_path("outputs.alerts_log") / "alerts.json"
        if not alerts_path.exists():
            # Run aggregation + alerts first
            from src.district_agg.district_aggregator import aggregate_districts
            from src.alerts.rule_engine import generate_alerts
            aggregate_districts()
            generate_alerts()

        assert alerts_path.exists()
        with open(alerts_path) as f:
            alerts = json.load(f)
        assert isinstance(alerts, list)


class TestDeliveryChannels:
    def test_mock_log_channel(self):
        from src.alerts.delivery import MockLogChannel

        channel = MockLogChannel()
        assert channel.channel_name() == "mock_log"
        result = channel.send({"severity": "WARNING", "message": "test"})
        assert result is True

    def test_mock_sms_channel(self):
        from src.alerts.delivery import MockSMSChannel

        channel = MockSMSChannel()
        assert channel.channel_name() == "mock_sms"
        result = channel.send({"district_name": "Pune", "message": "test alert"})
        assert result is True

    def test_mock_email_channel(self):
        from src.alerts.delivery import MockEmailChannel

        channel = MockEmailChannel()
        assert channel.channel_name() == "mock_email"
        result = channel.send({"severity": "CRITICAL", "message": "test"})
        assert result is True
