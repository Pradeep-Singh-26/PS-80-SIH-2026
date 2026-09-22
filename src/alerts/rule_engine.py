"""Alert rule engine.

Reads district_table.csv, evaluates configurable rules from
alert_rules.yaml, generates alert records, logs them to
outputs/alerts_log/, and dispatches through pluggable delivery channels.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from src.config import get_path
from src.alerts.delivery import MockLogChannel


def _load_rules() -> list[dict]:
    """Load alert rules from YAML config."""
    rules_path = Path(__file__).parent / "alert_rules.yaml"
    with open(rules_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("rules", [])


def _evaluate_rule(rule: dict, row: pd.Series) -> bool:
    """Check if a district_table row triggers a rule's conditions."""
    conditions = rule.get("conditions", {})

    if "p_heavy_min" in conditions:
        if row.get("p_heavy", 0) < conditions["p_heavy_min"]:
            return False

    if "p_very_heavy_min" in conditions:
        if row.get("p_very_heavy", 0) < conditions["p_very_heavy_min"]:
            return False

    if "regime_confidence_min" in conditions:
        if row.get("regime_confidence", 0) < conditions["regime_confidence_min"]:
            return False

    if "corrected_rainfall_min_mm" in conditions:
        if row.get("corrected_rainfall_mm", 0) < conditions["corrected_rainfall_min_mm"]:
            return False

    return True


def _format_message(template: str, row: pd.Series) -> str:
    """Format an alert message template with row data."""
    try:
        return template.format(**row.to_dict())
    except (KeyError, ValueError):
        return template


def generate_alerts():
    """Main entry point: evaluate rules and log alerts."""
    district_table_path = get_path("outputs.district_table")
    if not district_table_path.exists():
        print("    [SKIP] district_table.csv not found -- run aggregation first.")
        return

    df = pd.read_csv(district_table_path)
    rules = _load_rules()

    alerts_dir = get_path("outputs.alerts_log")
    alerts_dir.mkdir(parents=True, exist_ok=True)

    channel = MockLogChannel()
    alerts = []

    for _, row in df.iterrows():
        for rule in rules:
            if _evaluate_rule(rule, row):
                message = _format_message(rule.get("message_template", ""), row)
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "rule_name": rule["name"],
                    "severity": rule.get("severity", "INFO"),
                    "district_name": row.get("district_name", "unknown"),
                    "date": row.get("date", "unknown"),
                    "p_heavy": round(float(row.get("p_heavy", 0)), 4),
                    "p_very_heavy": round(float(row.get("p_very_heavy", 0)), 4),
                    "corrected_rainfall_mm": round(float(row.get("corrected_rainfall_mm", 0)), 2),
                    "rainfall_category": row.get("rainfall_category", "unknown"),
                    "dominant_regime": row.get("dominant_regime", "unknown"),
                    "regime_confidence": round(float(row.get("regime_confidence", 0)), 4),
                    "message": message.strip(),
                }
                alerts.append(alert)
                channel.send(alert)

    # Write all alerts to a JSON log
    log_path = alerts_dir / "alerts.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2, default=str)

    # Also write a CSV summary
    if alerts:
        summary_df = pd.DataFrame(alerts)
        summary_df.to_csv(alerts_dir / "alerts_summary.csv", index=False)

    print(f"    -> {len(alerts)} alerts generated, logged to {alerts_dir}")
