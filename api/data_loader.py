"""Config-driven data loader for the API layer.

Reads contracted output files from disk using paths from src.config.
Each loader returns pandas DataFrames or dicts -- the API layer converts
them to Pydantic models.

This is the ONLY place the API touches the filesystem. When Track A/B
update config.yaml with real paths, the API automatically picks them up.
"""

import json

import pandas as pd

from src.config import get_path


# ---------------------------------------------------------------------------
# Caches (simple in-memory; fine for single-process API)
# ---------------------------------------------------------------------------
_cache: dict = {}


def _invalidate_cache():
    """Clear all cached data (call after new pipeline run)."""
    _cache.clear()


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_regime_predictions() -> pd.DataFrame:
    """Load regime_predictions.csv."""
    key = "regime_predictions"
    if key not in _cache:
        path = get_path("data.regime_predictions")
        _cache[key] = pd.read_csv(path, parse_dates=["date"])
    return _cache[key]


def load_district_table() -> pd.DataFrame:
    """Load outputs/district_table.csv."""
    key = "district_table"
    if key not in _cache:
        path = get_path("outputs.district_table")
        if not path.exists():
            return pd.DataFrame()
        _cache[key] = pd.read_csv(path)
    return _cache[key]


def load_station_table() -> pd.DataFrame:
    """Load outputs/station_table.csv."""
    key = "station_table"
    if key not in _cache:
        path = get_path("outputs.station_table")
        if not path.exists():
            return pd.DataFrame()
        _cache[key] = pd.read_csv(path)
    return _cache[key]


def load_verification_summary() -> list[dict]:
    """Load overall_metrics.csv from verification report."""
    key = "verification_summary"
    if key not in _cache:
        report_dir = get_path("outputs.verification_report")
        overall_path = report_dir / "overall_metrics.csv"
        if not overall_path.exists():
            return []
        df = pd.read_csv(overall_path)
        _cache[key] = df.to_dict(orient="records")
    return _cache[key]


def load_alerts() -> list[dict]:
    """Load alerts from outputs/alerts_log/alerts.json."""
    key = "alerts"
    if key not in _cache:
        alerts_dir = get_path("outputs.alerts_log")
        alerts_path = alerts_dir / "alerts.json"
        if not alerts_path.exists():
            return []
        with open(alerts_path, "r", encoding="utf-8") as f:
            _cache[key] = json.load(f)
    return _cache[key]


def load_fss_scores() -> list[dict]:
    """Load FSS scores from verification report."""
    key = "fss_scores"
    if key not in _cache:
        report_dir = get_path("outputs.verification_report")
        fss_path = report_dir / "fss_scores.csv"
        if not fss_path.exists():
            return []
        df = pd.read_csv(fss_path)
        _cache[key] = df.to_dict(orient="records")
    return _cache[key]


def load_reliability_data() -> dict:
    """Load reliability diagram data from verification report."""
    key = "reliability_data"
    if key not in _cache:
        report_dir = get_path("outputs.verification_report")
        rel_path = report_dir / "reliability_data.json"
        if not rel_path.exists():
            return {}
        with open(rel_path, "r", encoding="utf-8") as f:
            _cache[key] = json.load(f)
    return _cache[key]


def load_regime_summary() -> list[dict]:
    """Load per-regime verification summary."""
    key = "regime_summary"
    if key not in _cache:
        report_dir = get_path("outputs.verification_report")
        path = report_dir / "regime_summary.csv"
        if not path.exists():
            return []
        df = pd.read_csv(path)
        _cache[key] = df.to_dict(orient="records")
    return _cache[key]


def save_feedback(feedback: dict) -> str:
    """Save forecaster feedback to a JSONL file.

    Writes using Track B's feedback schema so Track B can consume it
    for retraining.

    Returns:
        A generated feedback_id string.
    """
    import uuid
    from datetime import datetime

    feedback_dir = get_path("outputs.alerts_log").parent / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)

    feedback_id = str(uuid.uuid4())[:8]
    record = {
        "feedback_id": feedback_id,
        "submitted_at": datetime.now().isoformat(),
        **feedback,
    }

    feedback_file = feedback_dir / "feedback_log.jsonl"
    with open(feedback_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")

    return feedback_id
