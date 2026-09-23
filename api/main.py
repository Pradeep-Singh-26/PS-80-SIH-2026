"""PS 26080 -- FastAPI Service.

Exposes regime classification, corrected forecasts, heavy-rain
probability, district/station products, verification summaries, alerts,
and a forecaster feedback endpoint.

Run:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

For dev with fixture data:
    CONFIG_PATH=config.test.yaml uvicorn api.main:app --reload
"""

import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    AlertRecord,
    DistrictRow,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    RegimeResponse,
    StationRow,
    VerificationSummary,
)
from api.data_loader import (
    load_alerts,
    load_district_table,
    load_fss_scores,
    load_regime_predictions,
    load_regime_summary,
    load_reliability_data,
    load_station_table,
    load_verification_summary,
    save_feedback,
    load_cartodem_info,
    _invalidate_cache,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PS 26080 -- Regime-Aware Rainfall Post-Processing API",
    description=(
        "API for the Regime-Aware AI Post-Processing system. "
        "Serves regime classification, corrected forecasts, heavy-rain "
        "probability, district/station products, verification, and alerts."
    ),
    version="0.1.0",
)

# Allow dashboard (Streamlit) to call the API from any origin during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        pipeline_stages={
            "aggregate": "available",
            "verify": "available",
            "alerts": "available",
        },
    )


@app.get("/api/v1/topography/cartodem", tags=["Topography"])
def get_cartodem_status():
    """Get ISRO Bhuvan CartoDEM integration status, token details, and terrain stats."""
    return load_cartodem_info()



# ---------------------------------------------------------------------------
# Regime
# ---------------------------------------------------------------------------

@app.get("/api/v1/regime/{date}", response_model=RegimeResponse, tags=["Regime"])
def get_regime(date: str):
    """Get regime classification for a specific date (YYYY-MM-DD)."""
    df = load_regime_predictions()
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
    row = df[df["date_str"] == date]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"No regime data for date {date}")
    r = row.iloc[0]
    return RegimeResponse(
        date=date,
        active_prob=r.get("active_prob", 0),
        break_prob=r.get("break_prob", 0),
        low_depression_prob=r.get("low_depression_prob", 0),
        western_disturbance_prob=r.get("western_disturbance_prob", 0),
        orographic_prob=r.get("orographic_prob", 0),
        coastal_prob=r.get("coastal_prob", 0),
        dominant_label=r.get("dominant_label", "unknown"),
        confidence=r.get("confidence", 0),
    )


@app.get("/api/v1/regime", response_model=List[RegimeResponse], tags=["Regime"])
def list_regimes(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """List regime classifications, optionally filtered by date range."""
    df = load_regime_predictions()
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    if start_date:
        df = df[df["date_str"] >= start_date]
    if end_date:
        df = df[df["date_str"] <= end_date]

    results = []
    for _, r in df.iterrows():
        results.append(RegimeResponse(
            date=r["date_str"],
            active_prob=r.get("active_prob", 0),
            break_prob=r.get("break_prob", 0),
            low_depression_prob=r.get("low_depression_prob", 0),
            western_disturbance_prob=r.get("western_disturbance_prob", 0),
            orographic_prob=r.get("orographic_prob", 0),
            coastal_prob=r.get("coastal_prob", 0),
            dominant_label=r.get("dominant_label", "unknown"),
            confidence=r.get("confidence", 0),
        ))
    return results


# ---------------------------------------------------------------------------
# District / Station products
# ---------------------------------------------------------------------------

@app.get("/api/v1/districts/{date}", response_model=List[DistrictRow], tags=["Products"])
def get_districts(date: str):
    """Get district-level products for a specific date."""
    df = load_district_table()
    if df.empty:
        raise HTTPException(status_code=404, detail="District table not generated yet")
    filtered = df[df["date"] == date]
    if filtered.empty:
        raise HTTPException(status_code=404, detail=f"No district data for date {date}")
    return filtered.to_dict(orient="records")


@app.get("/api/v1/districts", response_model=List[DistrictRow], tags=["Products"])
def list_districts(
    district_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """List all district-level products with optional filters."""
    df = load_district_table()
    if df.empty:
        return []
    if district_name:
        df = df[df["district_name"] == district_name]
    if start_date:
        df = df[df["date"] >= start_date]
    if end_date:
        df = df[df["date"] <= end_date]
    return df.to_dict(orient="records")


@app.get("/api/v1/stations/{date}", response_model=List[StationRow], tags=["Products"])
def get_stations(date: str):
    """Get station-level products for a specific date."""
    df = load_station_table()
    if df.empty:
        raise HTTPException(status_code=404, detail="Station table not generated yet")
    filtered = df[df["date"] == date]
    if filtered.empty:
        raise HTTPException(status_code=404, detail=f"No station data for date {date}")
    return filtered.to_dict(orient="records")


@app.get("/api/v1/stations", response_model=List[StationRow], tags=["Products"])
def list_stations(
    station_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """List all station-level products with optional filters."""
    df = load_station_table()
    if df.empty:
        return []
    if station_id:
        df = df[df["station_id"] == station_id]
    if start_date:
        df = df[df["date"] >= start_date]
    if end_date:
        df = df[df["date"] <= end_date]
    return df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

@app.get("/api/v1/verification/summary", response_model=List[dict], tags=["Verification"])
def get_verification_summary():
    """Get overall verification metrics (raw vs ensemble vs corrected)."""
    data = load_verification_summary()
    if not data:
        raise HTTPException(status_code=404, detail="Verification report not generated yet")
    return data


@app.get("/api/v1/verification/fss", response_model=List[dict], tags=["Verification"])
def get_fss_scores():
    """Get Fractions Skill Scores at multiple neighborhood scales."""
    data = load_fss_scores()
    if not data:
        raise HTTPException(status_code=404, detail="FSS scores not generated yet")
    return data


@app.get("/api/v1/verification/reliability", response_model=dict, tags=["Verification"])
def get_reliability():
    """Get reliability diagram data for probabilistic products."""
    data = load_reliability_data()
    if not data:
        raise HTTPException(status_code=404, detail="Reliability data not generated yet")
    return data


@app.get("/api/v1/verification/regime", response_model=List[dict], tags=["Verification"])
def get_regime_verification():
    """Get per-regime verification summary."""
    data = load_regime_summary()
    if not data:
        raise HTTPException(status_code=404, detail="Regime verification not generated yet")
    return data


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

@app.get("/api/v1/alerts", response_model=List[AlertRecord], tags=["Alerts"])
def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: WARNING, ALERT, CRITICAL"),
    district_name: Optional[str] = Query(None),
):
    """Get generated alerts, optionally filtered."""
    alerts = load_alerts()
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity.upper()]
    if district_name:
        alerts = [a for a in alerts if a.get("district_name") == district_name]
    return alerts


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

@app.post("/api/v1/feedback", response_model=FeedbackResponse, tags=["Feedback"])
def submit_feedback(feedback: FeedbackRequest):
    """Submit forecaster feedback (regime correction, rainfall correction, etc.).

    Feedback is stored using Track B's feedback schema so it can be
    consumed for retraining.
    """
    data = feedback.model_dump() if hasattr(feedback, "model_dump") else feedback.dict()
    feedback_id = save_feedback(data)
    return FeedbackResponse(
        status="accepted",
        feedback_id=feedback_id,
        message="Feedback recorded. Will be consumed by retraining pipeline.",
    )


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

@app.post("/api/v1/cache/invalidate", tags=["System"])
def invalidate_cache():
    """Invalidate in-memory data cache (call after a new pipeline run)."""
    _invalidate_cache()
    return {"status": "cache_cleared"}
