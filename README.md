# PS 26080 | Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![ISRO CartoDEM](https://img.shields.io/badge/ISRO_Bhuvan-CartoDEM_30m-orange.svg)](https://bhuvan.nrsc.gov.in)
[![Tests](https://img.shields.io/badge/Tests-62_Passed-brightgreen.svg)]()
[![Pipeline](https://img.shields.io/badge/Pipeline-8%2F8_Stages_OK-success.svg)]()

> **Smart India Hackathon 2026 (Problem Statement PS-80)**  
> Physics-informed AI post-processing, quantile mapping, and orographic downscaling using ISRO Bhuvan CartoDEM 1 arc-second (~30m) topography for operational numerical weather prediction (NWP) bias correction.

---

## 🏛️ System Architecture & Track Split

The platform is architected into three decoupled functional tracks adhering to strict data contracts:

* **Track A — Data Ingest & Synoptic Regime Intelligence (Pradeep)**
  - Multi-source NWP (GFS + ECMWF) and observational gridded ingestion (`0.25°` resolution).
  - ISRO Bhuvan CartoDEM Topography Ingestion (`30m` resolution, slope, aspect, curvature).
  - Multi-label Synoptic Regime Classifier (Active, Break, Low/Depression, Western Disturbance, Orographic, Coastal).
  - Per-prediction TreeSHAP synoptic feature attribution.

* **Track B — Physics-Informed Bias Correction & Heavy Rain Estimation (Baljeet)**
  - Dual-NWP ensemble blending.
  - Regime-conditioned Quantile Mapping (QM) + LightGBM error correction router.
  - Synoptic Analog Pattern Matching engine.
  - Calibrated Exceedance Probabilities for Heavy ($\ge 64.5\text{ mm}$) and Very Heavy ($\ge 115.6\text{ mm}$) rainfall with 90% uncertainty intervals.
  - MLOps drift monitoring, automated retraining queue, and model registry.

* **Track C — Spatial Aggregation, Alerts, API, Dashboard & Ops (Divyansh)**
  - District polygon zonal aggregation and point-station interpolation.
  - Rule-based multi-tier alert engine (Critical / Alert / Warning) with pluggable channels.
  - High-performance FastAPI REST backend with OpenAPI/Swagger docs.
  - Sleek Streamlit dashboard styled in modern White, Black, and Light Blue.
  - Master pipeline orchestrator (`run_pipeline.py`), Docker Compose, and automated test suite.

---

## ⚡ Quick Start Guide

### 1. Navigate to Project Directory
Make sure your working directory is the repository root:

```bash
cd PS-80-SIH-2026
```

### 2. Install Required Dependencies
Install all required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create or edit `.env` in the repository root:

```ini
# PS-80 SIH 2026 Environment Configuration
CARTODEM_API_KEY=cb1_3vjz_1_05a34b49c36bc7de09e7e189
BHUVAN_API_KEY=37b5638bbb8cef862115aa29b6b10b0145f35f2b
CONFIG_PATH=config.test.yaml
```

---

## 🚀 Running the Project

### Step 1: Run the End-to-End Orchestration Pipeline
Execute all 8 pipeline stages from raw data to final alerts:

```bash
python run_pipeline.py --config config.test.yaml
```

#### Pipeline Execution Status:
| Stage | Module | Track Owner | Status | Output Deliverable |
|---|---|---|:---:|---|
| **1. ingest** | `src.ingest` | Track A (Pradeep) | `[OK]` | `data/raw/` multi-source manifest & datasets |
| **2. preprocess** | `src.preprocess` | Track A (Pradeep) | `[OK]` | Regridded NWP, obs, climatology, daily features |
| **3. classifier** | `src.regime_classifier` | Track A (Pradeep) | `[OK]` | Multi-label regime model, EVAL.md, TreeSHAP |
| **4. correction** | `src.bias_correction` | Track B (Baljeet) | `[OK]` | Ensemble blend, QM/GBM corrected grid, analogs |
| **5. probability** | `src.heavy_rain_prob` | Track B (Baljeet) | `[OK]` | Calibrated probabilities & 90% UQ bounds |
| **6. aggregate** | `src.district_agg` | Track C (Divyansh) | `[OK]` | Zonal district table & AWS station summaries |
| **7. verify** | `src.verification` | Track C (Divyansh) | `[OK]` | Verification scorecards, FSS, reliability plots |
| **8. alerts** | `src.alerts` | Track C (Divyansh) | `[OK]` | Automated extreme weather disaster alerts |

*To run a single stage:*
```bash
python run_pipeline.py --stage aggregate --config config.test.yaml
```

---

### Step 2: Launch the Frontend Web Dashboard
Start the interactive Streamlit dashboard:

```bash
python -m streamlit run dashboard/web/app.py
```
👉 Open your browser at **`http://localhost:8501`**

#### Available Dashboard Views:
1. 🗺️ **District & Station Map**: Interactive Folium map with satellite/terrain/dark mode switcher, IMD intensity scale, district summaries, and 90% uncertainty intervals.
2. 🌀 **Regime Classification**: Active synoptic regime banner, confidence gauge, and TreeSHAP meteorological feature attribution.
3. 🛰️ **Topography & CartoDEM**: 1 arc-second (~30m) ISRO Bhuvan DEM elevation profiles & orographic lift factors.
4. 📊 **Verification & Skill**: Scorecards comparing AI Model vs Raw NWP (RMSE, Bias, MAE, CSI, ETS, FSS, Reliability).
5. 🚨 **Alerts Dashboard**: Multi-tier threshold warnings, severity counters, and DDMA action feeds.
6. ⚖️ **Raw vs Corrected**: Visual side-by-side error reduction benchmarks across monsoon regimes.
7. 📝 **Forecaster Feedback**: Operational human-in-the-loop annotations and active learning retraining queue.

---

### Step 3: Launch the FastAPI Backend
Run the high-performance REST API server:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive Swagger Docs: **`http://localhost:8000/docs`**
* ReDoc Specification: **`http://localhost:8000/redoc`**

#### Key API Endpoints:
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health and pipeline readiness status |
| `GET` | `/api/v1/topography/cartodem` | ISRO Bhuvan CartoDEM key status, resolution, and terrain stats |
| `GET` | `/api/v1/districts/{date}` | Zonal district forecasts, category, and probabilities for a date |
| `GET` | `/api/v1/districts` | Filterable district time series (`district_name`, `start_date`, `end_date`) |
| `GET` | `/api/v1/stations/{date}` | AWS station-level predictions with 90% confidence intervals |
| `GET` | `/api/v1/stations` | Filterable station records (`station_id`, `start_date`, `end_date`) |
| `GET` | `/api/v1/regime/{date}` | Active weather regime, probabilities, and confidence |
| `GET` | `/api/v1/regime` | Historical regime classifications with date range filtering |
| `GET` | `/api/v1/alerts` | Active extreme rainfall bulletins filtered by severity |
| `GET` | `/api/v1/verification/summary`| Overall verification metrics (Raw NWP vs Ensemble vs Corrected) |
| `GET` | `/api/v1/verification/fss` | Fractions Skill Score (FSS) at multiple spatial scales |
| `GET` | `/api/v1/verification/reliability`| Reliability diagram data (observed frequency vs forecast probability) |
| `GET` | `/api/v1/verification/regime` | Skill scores broken down by dominant synoptic regime |
| `POST`| `/api/v1/feedback` | Submit forecaster feedback for model active-learning retraining |

---

## 🐳 Docker Deployment

Deploy both API and Dashboard using Docker Compose:

```bash
cd infra/docker
docker-compose up --build -d
```
- Web Dashboard: `http://localhost:8501`
- REST API: `http://localhost:8000`

---

## 🧪 Running Automated Tests

Run the complete test suite (62 unit & integration tests):

```bash
python -m pytest -q
```

With coverage report:
```bash
python -m pytest --cov=src --cov=api
```

---

## 📚 Documentation Index

Comprehensive guides are available in the [`docs/`](docs/) directory:
* 🏛️ [System Architecture](docs/architecture.md) — Architectural overview, data contracts, and pipeline topology.
* 🔌 [API Reference](docs/api_reference.md) — Complete REST endpoint documentation and request/response schemas.
* 📖 [User Guide](docs/user_guide.md) — Operational workflows for forecasters and administrators.
* 🚀 [Deployment Guide](docs/DEPLOYMENT.md) — Cloud, Docker, and production deployment procedures.
* ⚙️ [Pipeline Execution Guide](docs/PIPELINE_GUIDE.md) — Deep-dive into all 8 pipeline stages and config customization.

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
├── docs/                   # Architecture, API, Deployment & User Documentation
├── infra/                  # Docker and CI/CD configuration
│   └── docker/
│       ├── Dockerfile
│       └── docker-compose.yml
├── outputs/                # Generated district tables, verification reports & alerts
├── src/                    # Core AI & Numerical Post-Processing Modules
│   ├── alerts/             # Rule engine and notification delivery
│   ├── bias_correction/    # Multi-NWP QM, ML GBM corrector, and analog search
│   ├── district_agg/       # Zonal district and station point aggregator
│   ├── explainability/     # TreeSHAP synoptic and correction attributions
│   ├── heavy_rain_prob/    # Calibrated exceedance probability and 90% UQ
│   ├── ingest/             # Multi-source NWP, reanalysis, and CartoDEM ingestion
│   ├── mlops/              # Drift monitoring, feedback loop, and model registry
│   ├── preprocess/         # Regridding, climatology, and regime ground-truth
│   ├── regime_classifier/  # Multi-label LGBM regime classifier and evaluator
│   └── verification/       # RMSE, ETS, CSI, FSS, and reliability metrics
├── tests/                  # Unit and integration test suites
│   ├── fixtures/           # Fixture generator & mock datasets
│   ├── integration/        # Full pipeline integration tests
│   └── unit/               # Module-level unit tests
├── config.yaml             # Production pipeline configuration
├── config.test.yaml        # Test/Fixture pipeline configuration
├── run_pipeline.py         # Master pipeline orchestrator
└── requirements.txt        # Python dependency manifest
```
