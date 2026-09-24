# PS-80 Forecaster & Operator User Guide

This user guide walks meteorologists, duty officers, and system operators through daily execution, dashboard exploration, and alert management for the **Regime-Aware Rainfall Post-Processing Platform**.

---

## 1. Quick Setup & Environment

Ensure you have Python 3.10+ installed. From the repository root, install required packages:

```bash
pip install -r requirements.txt
```

Create your `.env` configuration file in the project root:

```ini
# PS-80 SIH 2026 Environment Configuration
CARTODEM_API_KEY=cb1_3vjz_1_05a34b49c36bc7de09e7e189
BHUVAN_API_KEY=37b5638bbb8cef862115aa29b6b10b0145f35f2b
CONFIG_PATH=config.test.yaml
```

---

## 2. Running the Post-Processing Pipeline

The master orchestrator [`run_pipeline.py`](../run_pipeline.py) chains all 8 operational tasks sequentially:

```bash
# Execute complete end-to-end pipeline
python run_pipeline.py --config config.test.yaml
```

### Stage Summary Table
| Stage | Function | Description |
|---|---|---|
| **1. ingest** | `src.ingest.run()` | Verifies/downloads multi-NWP and CartoDEM datasets. |
| **2. preprocess** | `src.preprocess.run()` | Aligns grids to 0.25°, computes climatology & 10 synoptic features. |
| **3. classifier** | `src.regime_classifier.run()` | Classifies synoptic regimes & generates TreeSHAP feature attributions. |
| **4. correction** | `src.bias_correction.run()` | Runs dual-NWP blending, QM/GBM error correction, and synoptic analogs. |
| **5. probability** | `src.heavy_rain_prob.run()` | Calibrates exceedance probabilities & calculates 90% UQ intervals. |
| **6. aggregate** | `src.district_agg.run()` | Performs district polygon zonal averaging & AWS station interpolation. |
| **7. verify** | `src.verification.run()` | Generates RMSE, ETS, CSI, FSS, and reliability scorecards. |
| **8. alerts** | `src.alerts.run()` | Dispatches multi-tier extreme rainfall bulletins based on rules. |

*To run or re-run an individual stage (e.g. alerts):*
```bash
python run_pipeline.py --stage alerts --config config.test.yaml
```

---

## 3. Launching the Visual Dashboard

Start the interactive Streamlit dashboard:

```bash
python -m streamlit run dashboard/web/app.py
```
Open **`http://localhost:8501`** in any web browser.

### Key Dashboard Tabs:
1. 🗺️ **District & Station Map**:
   - High-contrast Folium map with instant basemap switcher (**Satellite Imagery**, **Topography & Terrain**, **Light Canvas**, **OpenStreetMap**, **Dark Canvas**).
   - Click any station marker or district to view rainfall intensity, $P(\text{Heavy} \ge 64.5\text{mm})$, $P(\text{Very Heavy} \ge 115.6\text{mm})$, and $[10\%, 90\%]$ uncertainty intervals.
2. 🌀 **Weather Regime Diagnostics**:
   - Real-time classification banner showing dominant regime (Active, Break, Low/Depression, Western Disturbance, Orographic, Coastal).
   - Confidence meter and local TreeSHAP attribution chart indicating which atmospheric anomalies influenced the model.
3. 🛰️ **ISRO Bhuvan CartoDEM**:
   - 1 arc-second (~30m) elevation raster inspection, terrain slope, aspect, and orographic lift enhancement factors.
4. 📊 **Verification & Skill**:
   - Interactive scorecards displaying RMSE reduction, CSI / ETS gains, and multi-scale Fractions Skill Scores (FSS).
5. 🚨 **Alerts Bulletin**:
   - Live district emergency advisory feed categorizing threats into **CRITICAL** (red), **ALERT** (orange), and **WARNING** (amber).
6. 📝 **Forecaster Feedback**:
   - Active-learning interface allowing duty officers to flag false alarms or submit regime re-classifications directly to the MLOps retraining backlog.

---

## 4. Launching the Backend REST API

Start the FastAPI microservice for programmatic access and institutional integration:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: **`http://localhost:8000/docs`**
- ReDoc Technical Reference: **`http://localhost:8000/redoc`**

---

## 5. Customizing Alert Thresholds & Rules

Alert rules are defined declaratively in [`src/alerts/alert_rules.yaml`](../src/alerts/alert_rules.yaml). You can customize triggering conditions without editing code:

```yaml
rules:
  - name: very_heavy_rain_alert
    conditions:
      p_very_heavy_min: 0.40
      regime_confidence_min: 0.00
    severity: ALERT
    message_template: >
      ALERT: {district_name} has {p_very_heavy:.0%} probability of very
      heavy rainfall (>= 115.6mm) on {date}. Regime: {dominant_regime}.
```

After modifying rules, re-run `python run_pipeline.py --stage alerts` to refresh the alert logs.

---

## 6. Running Automated Tests

Validate system integrity with the automated test suite:

```bash
python -m pytest -q
```
Expected output: **62 passed in ~8s (100% passing)**.
