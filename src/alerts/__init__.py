"""Alerting module.

Rule-based heavy/very-heavy rainfall alert generation with pluggable
delivery interface (mocked channels for now, per PLAN.md Section 2.2).
"""


def run():
    """Run alert generation."""
    from src.alerts.rule_engine import generate_alerts

    print("  Running alert generation ...")
    generate_alerts()
