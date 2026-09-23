"""Pydantic response/request models for the API.

Defines all schemas used by the API endpoints so responses are
validated and self-documenting via OpenAPI/Swagger.
"""

from datetime import date as DateType
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Regime
# ---------------------------------------------------------------------------

class RegimeResponse(BaseModel):
    """Regime classification for a single date."""
    date: str
    active_prob: float = Field(..., ge=0, le=1)
    break_prob: float = Field(..., ge=0, le=1)
    low_depression_prob: float = Field(..., ge=0, le=1)
    western_disturbance_prob: float = Field(..., ge=0, le=1)
    orographic_prob: float = Field(..., ge=0, le=1)
    coastal_prob: float = Field(..., ge=0, le=1)
    dominant_label: str
    confidence: float = Field(..., ge=0, le=1)


# ---------------------------------------------------------------------------
# District / Station tables
# ---------------------------------------------------------------------------

class DistrictRow(BaseModel):
    """Single row of the district aggregation table."""
    district_name: str
    date: str
    corrected_rainfall_mm: float
    rainfall_category: str
    p_heavy: float
    p_very_heavy: float
    uncertainty_lower: float
    uncertainty_upper: float
    dominant_regime: str
    regime_confidence: float
    correction_method: str


class StationRow(BaseModel):
    """Single row of the station aggregation table."""
    station_id: str
    date: str
    lat: float
    lon: float
    corrected_rainfall_mm: float
    rainfall_category: str
    p_heavy: float
    p_very_heavy: float
    uncertainty_lower: float
    uncertainty_upper: float
    dominant_regime: str
    regime_confidence: float
    correction_method: str


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

class VerificationSummary(BaseModel):
    """Summary metrics for a single forecast source."""
    source: str
    n_points: int
    rmse: float
    bias: float
    mae: float
    heavy_pod: Optional[float] = None
    heavy_far: Optional[float] = None
    heavy_csi: Optional[float] = None
    heavy_ets: Optional[float] = None
    very_heavy_pod: Optional[float] = None
    very_heavy_far: Optional[float] = None
    very_heavy_csi: Optional[float] = None
    very_heavy_ets: Optional[float] = None


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class AlertRecord(BaseModel):
    """Single alert record."""
    timestamp: str
    rule_name: str
    severity: str
    district_name: str
    date: str
    p_heavy: float
    p_very_heavy: float
    corrected_rainfall_mm: float
    rainfall_category: str
    dominant_regime: str
    regime_confidence: float
    message: str


# ---------------------------------------------------------------------------
# Feedback (writes using Track B's feedback_schema)
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    """Forecaster feedback submission."""
    date: str
    district_name: Optional[str] = None
    station_id: Optional[str] = None
    feedback_type: str = Field(
        ...,
        description="One of: regime_correction, rainfall_correction, general"
    )
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    comment: Optional[str] = None
    forecaster_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    status: str
    feedback_id: str
    message: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """API health check response."""
    status: str
    version: str
    pipeline_stages: dict
