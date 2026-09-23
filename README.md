# PS 26080 | Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![ISRO CartoDEM](https://img.shields.io/badge/ISRO_Bhuvan-CartoDEM_30m-orange.svg)](https://bhuvan.nrsc.gov.in)
[![Tests](https://img.shields.io/badge/Tests-60_Passed-brightgreen.svg)]()

> **Smart India Hackathon 2026 (Problem Statement PS-80)**  
> Physics-informed AI post-processing, quantile mapping, and orographic downscaling using ISRO Bhuvan CartoDEM 1 arc-second (~30m) topography for operational numerical weather prediction (NWP) bias correction.

---

## 🏛️ System Architecture & Track Split

The platform is architected into three decoupled functional tracks adhering to strict data contracts:

* **Track A — Data Ingest & Synoptic Regime Classifier**
  - IMD/ECMWF/GFS Gridded NWP Ingestion (`0.25°` resolution).
  - ISRO Bhuvan CartoDEM Topography Ingest (`30m` resolution, slope, aspect, curvature).
  - Multi-label Synoptic Regime Classifier (Active, Break, Low/Depression, Western Disturbance, Orographic, Coastal).

* **Track B — Physics-Informed Bias Correction & Heavy Rain Estimation**
  - Regime-conditioned Quantile Mapping & Gradient Boosted Error Correction.
  - Synoptic Analog Pattern Matching.
  - Calibrated Exceedance Probabilities for Heavy ($\ge 64.5\text{ mm}$) and Very Heavy ($\ge 115.5\text{ mm}$) rainfall with 90% uncertainty intervals.

* **Track C — Spatial Aggregation, Alerts, API & Dashboard Serving**
  - District polygon zonal aggregation and point-station interpolation.
  - Real-time automated disaster management alert engine (Critical / Alert / Warning).
  - High-performance FastAPI REST backend with automated OpenAPI documentation.
  - Modern, responsive Streamlit dashboard in a clean **White, Black, and Light Blue** theme.

---

## ⚡ Quick Start Guide

### 1. Open Terminal & Navigate to Project Directory
Make sure your working directory is the repository root (`PS-80-SIH-2026`):

```bash
cd "c:\Users\asus\Desktop\ps 80 2\PS-80-SIH-2026"
```

### 2. Install Required Dependencies
Install all required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

Ensure your `.env` contains your ISRO Bhuvan CartoDEM key:
```ini
CARTODEM_API_KEY=cb1_31ua...6b25
CONFIG_PATH=config.test.yaml
```

---

## 🚀 Running the Project

### Step 1: Generate Synthetic Fixture Data (Quick Test Mode)
To test the entire pipeline without needing live multi-gigabyte NWP GRIB files, generate test fixtures:

```bash
python tests/fixtures/generate_fixtures.py
```

### Step 2: Run the End-to-End Orchestration Pipeline
Execute all 12 pipeline tasks (Ingestion $\rightarrow$ Preprocessing $\rightarrow$ Regime Classification $\rightarrow$ Bias Correction $\rightarrow$ Probability Calibration $\rightarrow$ District Aggregation $\rightarrow$ Verification $\rightarrow$ Alerts):

```bash
python run_pipeline.py --config config.test.yaml
```

*To run a single stage:*
```bash
python run_pipeline.py --stage aggregate --config config.test.yaml
```

---

### Step 3: Launch the Frontend Web Dashboard
Start the interactive Streamlit dashboard (styled in a sleek White, Black, and Light Blue palette):

```bash
streamlit run dashboard/web/app.py
```
*Or using python module syntax:*
```bash
python -m streamlit run dashboard/web/app.py
```
👉 Open your browser at **`http://localhost:8501`**

#### Available Dashboard Views:
1. 🗺️ **District & Station Map**: Interactive Folium map, IMD intensity scale, district summaries, uncertainty bounds.
2. 🌀 **Regime Classification**: Active synoptic regime banner, confidence gauge, and meteorological diagnostics.
3. 🛰️ **Topography & CartoDEM**: 1 arc-second (~30m) ISRO Bhuvan DEM elevation profiles & orographic lift factors.
4. 📊 **Verification & Skill**: Scorecards comparing AI Model vs Raw NWP (RMSE, Bias, MAE, CSI, ETS, FSS, Reliability).
5. 🚨 **Alerts Dashboard**: Multi-tier threshold warnings, severity counters, and DDMA action feeds.
6. ⚖️ **Raw vs Corrected**: Visual side-by-side error reduction benchmarks across monsoon regimes.
7. 📝 **Forecaster Feedback**: Operational human-in-the-loop annotations and active learning retraining queue.

---

### Step 4: Launch the FastAPI Backend (Optional)
Run the REST API server:

```bash
uvicorn api.main:app --reload --port 8000
```
* Interactive Swagger Docs: **`http://localhost:8000/docs`**
* ReDoc Specification: **`http://localhost:8000/redoc`**

#### Key API Endpoints:
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health and telemetry status |
| `GET` | `/api/v1/districts` | Zonal district rainfall forecasts & $P(\text{Heavy})$ |
| `GET` | `/api/v1/stations` | Ground station predictions with 90% confidence intervals |
| `GET` | `/api/v1/regimes` | Active synoptic regime predictions & probabilities |
| `GET` | `/api/v1/alerts` | Active extreme rainfall warnings and bulletins |
| `GET` | `/api/v1/cartodem/status` | ISRO Bhuvan CartoDEM API and grid cache status |
| `POST`| `/api/v1/feedback` | Submit forecaster feedback for model retraining |

---

## 🧪 Running Automated Tests

Run the complete test suite (60 unit & integration tests):

```bash
python -m pytest
```

With coverage report:
```bash
python -m pytest --cov=src --cov=api
```

---

## 📁 Repository Directory Structure

```text
PS-80-SIH-2026/
├── .streamlit/             # Streamlit theme configuration (White, Black & Light Blue)
│   └── config.toml
├── api/                    # FastAPI REST API layer
│   ├── main.py
│   ├── schemas.py
│   └── data_loader.py
├── dashboard/              # Frontend UI Components & Pages
│   ├── web/
│   │   └── app.py          # Main Streamlit web application
│   └── components/
│       ├── alert_panel.py
│       ├── map_component.py
│       ├── regime_explainer.py
│       └── skill_charts.py
├── data/                   # Data directory (raw, processed, external)
├── docs/                   # Architecture, API & User Documentation
├── outputs/                # Generated district tables, verification reports & alerts
├── src/                    # Core AI & Numerical Post-Processing Modules
│   ├── alerts/
│   ├── bias_correction/
│   ├── district_agg/
│   ├── heavy_rain_prob/
│   ├── ingest/
│   ├── regime_classifier/
│   └── verification/
├── tests/                  # Unit and integration test suites
│   └── fixtures/           # Fixture generator & mock datasets
├── config.yaml             # Production pipeline configuration
├── config.test.yaml        # Test/Fixture pipeline configuration
├── run_pipeline.py         # Master pipeline orchestrator
└── requirements.txt        # Python dependency manifest
```
