# API Reference

The PS-80 backend is a FastAPI REST service. By default, it runs on port `8000`.

Base URL: `http://localhost:8000/api/v1`

## System

### `GET /health`
Returns the system status and the availability of the Track C pipeline stages.

## Regime

### `GET /regime`
Returns a list of regime classifications for all available dates.
- **Query Params:** `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD)

### `GET /regime/{date}`
Returns the regime classification for a specific date.

## Products

### `GET /districts`
Returns aggregated district-level data.
- **Query Params:** `district_name`, `start_date`, `end_date`

### `GET /districts/{date}`
Returns all district data for a given date.

### `GET /stations`
Returns aggregated station-level data.
- **Query Params:** `station_id`, `start_date`, `end_date`

### `GET /stations/{date}`
Returns all station data for a given date.

## Verification

### `GET /verification/summary`
Returns the overall continuous and categorical metrics for raw vs. corrected forecasts.

### `GET /verification/fss`
Returns Fractions Skill Scores (FSS) at multiple spatial scales.

### `GET /verification/reliability`
Returns reliability diagram data (forecast probability vs. observed frequency).

### `GET /verification/regime`
Returns verification metrics broken down by the dominant weather regime.

## Alerts

### `GET /alerts`
Returns generated alerts.
- **Query Params:** `severity` (WARNING, ALERT, CRITICAL), `district_name`

## Feedback

### `POST /feedback`
Submit forecaster feedback for downstream model retraining.
- **Body Schema:**
```json
{
  "date": "2024-06-15",
  "feedback_type": "regime_correction",
  "original_value": "active",
  "corrected_value": "break",
  "comment": "Trough was further south than predicted.",
  "district_name": "Pune",
  "station_id": null,
  "forecaster_id": "F123"
}
```
