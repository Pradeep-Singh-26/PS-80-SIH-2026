"""Forecaster Feedback Validation and Storage Module (Track B - Task 11).

Validates human forecaster feedback records submitted from Track C UI / API
against the agreed schema before appending to data/feedback/forecaster_feedback.csv.
"""

from datetime import datetime
import logging
from pathlib import Path
import re
from typing import Any, Dict, Optional, Tuple

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("feedback_validator")

ALLOWED_ASSESSMENTS = {
    "underestimated",
    "overestimated",
    "accurate",
    "missed_extreme",
    "false_alarm",
}

ALLOWED_CORRECTION_CATEGORIES = {
    "orographic_enhancement",
    "coastal_convergence",
    "mesoscale_convective_system",
    "synoptic_depression",
    "dry_air_intrusion",
    "nwp_phase_error",
    "nwp_intensity_bias",
    "general_adjustment",
}

ALLOWED_STATUSES = {
    "submitted",
    "approved_for_retraining",
    "rejected",
}

FEEDBACK_COLUMNS = [
    "feedback_id",
    "submitted_at",
    "forecaster_id",
    "forecast_date",
    "district_name",
    "lat",
    "lon",
    "original_forecast_mm",
    "forecaster_rainfall_mm",
    "p_heavy",
    "p_very_heavy",
    "assessment",
    "correction_category",
    "confidence",
    "comment",
    "model_version",
    "status",
]


def validate_feedback_record(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a single forecaster feedback dictionary against contract schema.

    Returns (is_valid, error_message).
    """
    if not isinstance(record, dict):
        return False, "Record must be a dictionary."

    # 1. Required string fields
    for field in ["feedback_id", "submitted_at", "forecaster_id", "forecast_date", "district_name"]:
        val = record.get(field)
        if not val or not str(val).strip():
            return False, f"Missing required field '{field}'."

    # 2. Date format validation
    date_str = str(record["forecast_date"]).strip()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False, f"Invalid forecast_date '{date_str}'. Expected format YYYY-MM-DD."

    # 3. Non-negative rainfall amounts
    for rf_field in ["original_forecast_mm", "forecaster_rainfall_mm"]:
        if rf_field not in record or record[rf_field] is None:
            return False, f"Missing required rainfall field '{rf_field}'."
        try:
            rf_val = float(record[rf_field])
            if rf_val < 0.0:
                return False, f"Rainfall amount '{rf_field}' cannot be negative ({rf_val} mm)."
        except (ValueError, TypeError):
            return False, f"Invalid numeric value for '{rf_field}'."

    # 4. Probability bounds & cross-threshold monotonicity
    p_h = record.get("p_heavy")
    p_vh = record.get("p_very_heavy")

    if p_h is not None and not pd.isna(p_h):
        try:
            p_h_val = float(p_h)
            if not (0.0 <= p_h_val <= 1.0):
                return False, f"p_heavy must be in [0.0, 1.0], got {p_h_val}."
        except (ValueError, TypeError):
            return False, "Invalid float value for p_heavy."

    if p_vh is not None and not pd.isna(p_vh):
        try:
            p_vh_val = float(p_vh)
            if not (0.0 <= p_vh_val <= 1.0):
                return False, f"p_very_heavy must be in [0.0, 1.0], got {p_vh_val}."
        except (ValueError, TypeError):
            return False, "Invalid float value for p_very_heavy."

    if p_h is not None and p_vh is not None and not pd.isna(p_h) and not pd.isna(p_vh):
        if float(p_vh) > float(p_h) + 1e-6:
            return False, f"Monotonicity violation: p_very_heavy ({p_vh}) > p_heavy ({p_h})."

    # 5. Assessment and correction category vocabulary
    assessment = str(record.get("assessment", "")).lower().strip()
    if assessment not in ALLOWED_ASSESSMENTS:
        return False, f"Invalid assessment '{assessment}'. Allowed: {sorted(ALLOWED_ASSESSMENTS)}."

    category = str(record.get("correction_category", "")).lower().strip()
    if category not in ALLOWED_CORRECTION_CATEGORIES:
        return False, f"Invalid correction_category '{category}'. Allowed: {sorted(ALLOWED_CORRECTION_CATEGORIES)}."

    # 6. Confidence range
    conf = record.get("confidence")
    if conf is None or pd.isna(conf):
        return False, "Missing required field 'confidence'."
    try:
        conf_val = float(conf)
        if not (0.0 <= conf_val <= 1.0):
            return False, f"confidence must be in [0.0, 1.0], got {conf_val}."
    except (ValueError, TypeError):
        return False, "Invalid float value for confidence."

    # 7. Model version format
    mod_ver = record.get("model_version")
    if mod_ver is not None and not pd.isna(mod_ver) and str(mod_ver).strip():
        if not re.match(r"^v\d{3,}$", str(mod_ver).strip()):
            return False, f"Invalid model_version '{mod_ver}'. Expected format 'v001', 'v002'."

    # 8. Status check
    status = str(record.get("status", "submitted")).lower().strip()
    if status not in ALLOWED_STATUSES:
        return False, f"Invalid status '{status}'. Allowed: {sorted(ALLOWED_STATUSES)}."

    return True, None


def append_feedback_record(
    record: Dict[str, Any],
    feedback_csv_path: Path | str = "data/feedback/forecaster_feedback.csv",
) -> Path:
    """Validate and append a forecaster feedback record to disk."""
    is_valid, err_msg = validate_feedback_record(record)
    if not is_valid:
        raise ValueError(f"Feedback record validation failed: {err_msg}")

    feedback_csv_path = Path(feedback_csv_path)
    feedback_csv_path.parent.mkdir(parents=True, exist_ok=True)

    clean_record = {
        col: record.get(col, None) for col in FEEDBACK_COLUMNS
    }
    # Standardize status default
    if not clean_record.get("status"):
        clean_record["status"] = "submitted"

    df_new = pd.DataFrame([clean_record])

    if not feedback_csv_path.exists() or feedback_csv_path.stat().st_size == 0:
        df_new.to_csv(feedback_csv_path, index=False)
    else:
        df_new.to_csv(feedback_csv_path, mode="a", header=False, index=False)

    logger.info(f"Appended feedback record '{record['feedback_id']}' to {feedback_csv_path}")
    return feedback_csv_path
