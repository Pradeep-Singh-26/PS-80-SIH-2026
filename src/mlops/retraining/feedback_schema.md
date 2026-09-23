# Forecaster Feedback Contract & Schema Specification (Track B — Task 11)

> **Contract Owner**: Track B (Baljeet — MLOps & Retraining Pipeline)  
> **Contract Consumer**: Track C (Divyansh — Forecaster Dashboard UI & API)  
> **Storage Target**: `data/feedback/forecaster_feedback.csv`

---

## 1. Overview & Architectural Integration

This contract defines the standard format and validation rules for expert forecaster adjustments and qualitative assessments collected via the dashboard UI (Track C). 

```text
┌─────────────────────────────────────────────────────────────┐
│                 Track C — Forecaster UI                     │
│  (Expert reviews rainfall forecast, edits mm, clicks Save)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Forecaster Feedback Validation Engine              │
│       (src/mlops/retraining/feedback_validator.py)          │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Appends valid records)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           data/feedback/forecaster_feedback.csv             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           Track B — MLOps Retraining Pipeline (Step 8)      │
│   (Weighting historical data with forecaster corrections)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Field Schema Definitions

| Field Name | Type | Required / Optional | Constraints / Allowed Values | Description |
|---|---|---|---|---|
| `feedback_id` | String | **Required** | Non-empty, unique alphanumeric ID (e.g. `fb_20240623_001`) | Unique event identifier |
| `submitted_at` | String | **Required** | ISO 8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`) | Submission time |
| `forecaster_id` | String | **Required** | Non-empty string (e.g. `forecaster_imd_01`) | Anonymized expert ID |
| `forecast_date` | String | **Required** | `YYYY-MM-DD` | Date of the evaluated forecast |
| `district_name` | String | **Required** | Non-empty district string (e.g. `Ratnagiri`) | Target geographical district |
| `lat` | Float | Optional | Range: `[6.0, 38.0]` | Latitude coordinate |
| `lon` | Float | Optional | Range: `[68.0, 98.0]` | Longitude coordinate |
| `original_forecast_mm` | Float | **Required** | `>= 0.0` mm | Model/blended forecast amount |
| `forecaster_rainfall_mm` | Float | **Required** | `>= 0.0` mm | Forecaster adjusted rainfall amount |
| `p_heavy` | Float | Optional | `0.0 <= p <= 1.0` | Forecast probability for heavy rain |
| `p_very_heavy` | Float | Optional | `0.0 <= p <= 1.0` | Forecast probability for very heavy rain |
| `assessment` | String | **Required** | `underestimated`, `overestimated`, `accurate`, `missed_extreme`, `false_alarm` | Qualitative judgment |
| `correction_category` | String | **Required** | `orographic_enhancement`, `coastal_convergence`, `mesoscale_convective_system`, `synoptic_depression`, `dry_air_intrusion`, `nwp_phase_error`, `nwp_intensity_bias`, `general_adjustment` | Meteorological root-cause |
| `confidence` | Float | **Required** | `0.0 <= c <= 1.0` | Forecaster confidence in adjustment |
| `comment` | String | Optional | Free-text string | Contextual remarks |
| `model_version` | String | Optional | e.g. `v001`, `v002` | Version tag of active model used |
| `status` | String | Optional | `submitted`, `approved_for_retraining`, `rejected` (default: `submitted`) | Workflow lifecycle tag |

---

## 3. Strict Validation Constraints

1. **Non-Negative Rainfall**: Both `original_forecast_mm` and `forecaster_rainfall_mm` must be $\ge 0.0$.
2. **Bounded Probabilities**: Probabilities `p_heavy` and `p_very_heavy` must strictly lie within $[0.0, 1.0]$.
3. **Monotonicity**: If both probabilities are provided, $p_{\text{very\_heavy}} \le p_{\text{heavy}}$ must hold.
4. **Controlled Vocabulary**: `assessment` and `correction_category` must strictly match the permitted enumerations above.
5. **Traceability**: `model_version` must match the registered version format to ensure the active model that generated the forecast can be audited during retraining.

---

## 4. Storage & Append Specification

- Feedback records are persisted into `data/feedback/forecaster_feedback.csv`.
- If the file does not exist, it is initialized with the standard header.
- When new feedback is submitted via API/UI, it must pass `feedback_validator.validate_feedback_record(record)` before appending.
