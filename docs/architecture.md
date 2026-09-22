# Architecture Overview (Track C)

This document describes the architecture of the Track C post-processing layer, which is responsible for aggregation, verification, alerting, and serving the outputs of the PS-80 AI Rainfall system.

## High-Level Flow

1. **Upstream Processing (Tracks A & B):**
   - Track A produces `regime_predictions.csv` (weather regime classifications).
   - Track B produces `corrected_grid.nc` (AI-corrected rainfall) and `heavy_rain_prob.nc` (probabilistic heavy rain forecasts).

2. **Configuration (`src/config.py` & `config.yaml`):**
   - All file paths are strictly decoupled via YAML config.
   - Modules request data paths from the config system.
   - For testing, `config.test.yaml` points to synthetic fixture data.

3. **Aggregation (`src/district_agg/`):**
   - **District:** Area-weighted zonal statistics over district polygons.
   - **Station:** Nearest-grid extraction for key points.
   - Merges rainfall, probabilities, regime, and uncertainties into uniform CSV tables.

4. **Verification (`src/verification/`):**
   - Pure numpy metric implementations.
   - Computes RMSE, ETS, CSI, POD, FAR, FSS (multi-scale), and reliability diagrams.
   - Segregates performance metrics by dominant weather regime.

5. **Alerting (`src/alerts/`):**
   - Rule-based engine configured via `alert_rules.yaml`.
   - Pluggable delivery interface (`AlertChannel`) to allow mocking (Log/SMS/Email) until real institutional gateways are available.

6. **API (`api/main.py`):**
   - FastAPI-based REST service.
   - Reads final outputs from disk (via config paths) and serves them as JSON.
   - Implements an endpoint to collect forecaster feedback, saving it for Track B retraining.

7. **Dashboard (`dashboard/web/app.py`):**
   - Streamlit interface consuming API outputs (or local files).
   - Provides visualization for maps, regime analysis, skill verification, and alerts.

## Boundaries and Contracts
Track C does **not** perform ML inference. It relies completely on the data schemas agreed upon with Tracks A and B (defined in `PLAN.md` and mocked in `tests/fixtures/generate_fixtures.py`).
