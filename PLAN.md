# PS 26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

> **How to use this document (read this first, especially if you are an agent
> or teammate picking this up with no prior context):** This is the single
> source of truth for the full system design. It describes a complete,
> production-shaped solution to the problem statement — not a scoped-down
> demo. Section 2 fixes what is built now vs. genuinely future work (mostly
> things that require infrastructure/data this team doesn't control, e.g.
> live operational feeds from NCMRWF). Everything else described here is
> meant to be built. Section 7 breaks it into an ordered task list with
> explicit input/output contracts; [TEAM_SPLIT.md](TEAM_SPLIT.md) assigns
> those tasks to three people with strict, non-overlapping boundaries. No
> code has been written yet — this pass only establishes structure.

## 0. One-paragraph summary

Build a full regime-aware rainfall post-processing **system**: it ingests
multiple NWP forecast sources plus observations, satellite/radar and
reanalysis fields; classifies the prevailing monsoon weather regime (with
uncertainty and explainability); applies regime-conditioned, ensemble-aware
bias correction to raw rainfall forecasts; produces calibrated heavy/very-
heavy rainfall probabilities with uncertainty bounds; aggregates results to
district and station level; runs full skill verification (RMSE, ETS, CSI,
POD, FAR, FSS, reliability) split by regime; serves everything through an
API and an interactive dashboard; and includes a continuous-learning loop
(drift detection, retraining, forecaster feedback) and an alerting layer for
heavy-rainfall warnings. It is designed to be handed to NCMRWF as a
deployable system, not just a notebook.

## 1. Problem framing

Raw NWP rainfall forecasts have systematic, regime-dependent biases (active
monsoon, break monsoon, monsoon lows/depressions, orographic rainfall,
coastal rainfall, western disturbances). A single global bias-correction
method underperforms across regimes. This system: **detects the regime
(with confidence + explanation) → routes to a regime-specific, ensemble-
capable correction → produces calibrated probabilistic rainfall and heavy-
rain-probability products at grid/station/district level → verifies skill
per regime → serves the result via API/dashboard/alerts → continuously
improves via a feedback and retraining loop.**

## 2. Scope

### 2.1 IN SCOPE — build now (full solution, not a cut-down demo)

**Data & regimes**
1. Multi-source ingestion: NWP forecasts (support more than one model/
   source, e.g. GFS + ECMWF open data + NCMRWF/IMD output where available),
   observation grids/stations, reanalysis (MSLP, OLR, winds), satellite
   proxies (OLR/brightness temperature as INSAT proxy), radar/nowcast data
   where publicly available, and IMD low-pressure-system/depression best
   track records.
2. Automated ingestion pipeline scaffolding (schedulable, idempotent,
   re-runnable) — built to run on a schedule even though this team will run
   it manually/on-demand rather than against a live operational feed.
3. **6-class regime classifier**: `active`, `break`, `low_depression`,
   `western_disturbance`, `orographic`, `coastal` (see Section 3), with
   **multi-label support** (a day can carry more than one active regime,
   e.g. depression + coastal enhancement), confidence scores, and an
   explainability layer (feature attribution per prediction).
4. Regime detection from **multiple signal families**: dynamical (MSLP/
   trough), thermodynamical (OLR/convection proxy), and satellite proxy —
   fused rather than relying on one signal alone.

**Correction & products**
5. Regime-conditioned bias correction with **two interchangeable methods**:
   (a) per-regime quantile mapping (fast, interpretable baseline) and
   (b) per-regime/regime-feature ML correction (gradient boosting, with a
   documented upgrade path to a spatial deep model). Both are built; the
   system picks per-regime whichever has enough training data, and this
   choice is logged per run.
6. **Multi-model ensemble fusion**: when more than one NWP source is
   ingested, blend them (simple/weighted ensemble mean or ML-learned
   weights) before/alongside correction, rather than assuming a single NWP
   source.
7. **Analog-based correction** as a second, independent correction pathway:
   for a given regime + season, find historical analog days and use their
   empirical error distribution — used both as an alternative correction
   and as a sanity check/ensemble member against the ML correction.
8. Heavy/very-heavy rainfall probability, **calibrated** (reliability-
   checked) and **with uncertainty quantification** (ensemble spread or
   quantile regression, not a single point probability).
9. Grid, **station-level**, and **district-level** aggregated products (not
   grid/district only — stations included since IMD verifies at stations
   too).

**Verification**
10. Full verification suite: RMSE, ETS, CSI, POD, FAR, **and FSS at multiple
    neighborhood scales**, plus reliability diagrams and rank histograms for
    the probabilistic products — all split by regime, by threshold, and by
    lead time if multiple lead times are ingested.
11. Skill comparison report: raw NWP vs. corrected vs. (if multiple NWP
    ingested) ensemble-blended, so the report demonstrates the value added
    at each pipeline stage.

**Explainability & trust**
12. Per-prediction explainability for both the regime classifier and the
    correction model (e.g. SHAP-based feature attribution) — a forecaster
    should be able to see *why* the system picked a regime/correction, not
    just the number.
13. Confidence-aware presentation: every rainfall/probability output is
    shown with its regime confidence and correction-method provenance, not
    as a bare number.

**Serving & product layer**
14. **API service** exposing regime classification, corrected forecast,
    heavy-rain probability, and district/station products — so this can be
    integrated into other MoES/NCMRWF systems, not just viewed in a
    dashboard.
15. **Interactive dashboard**: district/station map + table, regime
    explanation panel, verification/skill view, historical regime
    climatology explorer, and a raw-vs-corrected comparison view.
16. **Alerting layer**: rule-based heavy/very-heavy rainfall alert
    generation (e.g. district crosses a threshold with high confidence) —
    logged to `outputs/alerts_log/`, with the delivery channel (SMS/email/
    push) stubbed as a pluggable interface rather than actually wired to a
    live telecom/SMS provider (see 2.2).

**Operations & continuous improvement**
17. **Human-in-the-loop feedback**: a forecaster can flag/correct a
    predicted regime or a rainfall product; flagged cases are logged in a
    structured format for retraining.
18. **Drift monitoring**: track input feature distributions and forecast
    skill over time; flag when retraining is warranted.
19. **Retraining pipeline + model registry**: versioned models, reproducible
    retraining, rollback capability.
20. **Testing**: unit tests for each pipeline stage's core logic, and an
    integration test that runs the full pipeline on a small fixture dataset.
21. **CI + containerization**: a CI pipeline definition (lint + tests) and a
    Docker setup so the system can be built and run consistently anywhere.
22. **Documentation**: architecture doc, API reference, and a forecaster-
    facing user guide.

### 2.2 Genuinely deferred (needs infrastructure/access this team cannot
     obtain on its own — not a scope-cutting choice)
- **Live production data feeds**: this system is built to be schedulable,
  but it will run against downloaded/batch data, not a real-time
  operational NCMRWF/IMD feed, since that requires institutional access
  this project doesn't have.
- **Real SMS/push notification delivery**: the alerting layer is built with
  a pluggable delivery interface; wiring it to an actual telecom/SMS
  gateway or NDMA integration is out of reach without institutional
  partnership, so it is stubbed/mocked and clearly documented as such.
- **Raw deep learning on full spatial fields** (CNN/U-Net/ConvLSTM/
  transformer-based spatial correction) as the *primary* correction method
  — the architecture leaves a clean extension point for this (see Section
  4), but building and tuning it from scratch is treated as a fast-follow,
  not a blocker for a complete first system, because it needs materially
  more data and compute than the rest of the pipeline.
- **Cloud production deployment / auth / multi-tenant scaling** — the
  system is containerized and API-first so it *can* be deployed, but
  standing up actual cloud infra, user auth, and horizontal scaling is an
  institutional/operational decision, not something this project decides
  unilaterally.
- **Nationwide, all-India, all-season coverage** at full station density in
  the first build — the architecture supports it (nothing is hard-coded to
  one region), but the first fully-verified build targets a defined
  domain/season set (fixed in Task 0) and expanding coverage is a
  data-acquisition exercise, not a redesign.

## 3. Weather regime classes (6-class, multi-label)

| Label | Meaning | Primary signal(s) |
|---|---|---|
| `active` | Active monsoon: strong trough, above-normal core-zone rainfall | Rainfall anomaly (+), MSLP trough position |
| `break` | Break monsoon: weak/displaced trough, suppressed central-India rainfall | Rainfall anomaly (−), trough displacement |
| `low_depression` | Monsoon low/depression present | IMD best-track presence flag |
| `western_disturbance` | WD-influenced rainfall (esp. NW India, outside/at monsoon margins) | WD-track presence, MSLP pattern over NW India |
| `orographic` | Terrain-driven enhancement (Western Ghats, NE hills) | Elevation-conditioned rainfall excess vs. surrounding grid |
| `coastal` | Coastal convergence-driven rainfall | Coastal proximity + convective indicators |

A day/grid-point may carry **more than one label** (e.g. `low_depression` +
`coastal`); the classifier outputs a probability per label, and the
correction stage uses the dominant (highest-probability) label to select its
primary regime-specific model, with the secondary label available as an
explanatory feature and for edge-case ensembling. This replaces the earlier
4-class, single-label prototype design.

## 4. Modeling approach

- **Regime classifier**: multi-label gradient boosting (XGBoost/LightGBM,
  one-vs-rest per label) over dynamical + thermodynamical + satellite-proxy
  features (Section 9.1 lists sources). Explainability via SHAP values per
  prediction. Extension point: a sequence model (e.g. temporal CNN/LSTM
  over the feature time series) is a documented future upgrade if the
  gradient-boosting baseline underperforms — not built in the first pass.
- **Bias correction**: two parallel, swappable methods per regime —
  (a) quantile mapping (baseline, always available, needs least data), and
  (b) gradient-boosted regression using NWP + auxiliary features (elevation,
  coast distance, climatology). Per-regime, the system picks whichever
  method has enough training samples (documented threshold, e.g. ~30
  grid-days minimum for a dedicated per-regime fit; below that, fall back to
  a single cross-regime model with regime as a feature). The chosen method
  per regime is recorded in run metadata for auditability. **Extension
  point**: a spatial deep-learning correction (CNN/U-Net) can be added later
  as a third method behind the same interface, once enough data is
  available (see Section 2.2).
- **Multi-model ensemble fusion**: if multiple NWP sources are ingested,
  blend before correction using either a simple weighted mean (weights from
  historical skill per source per regime) or a learned blending model — the
  interface supports both; start with the weighted mean as the default.
- **Analog-based correction**: for a target date's regime + season, retrieve
  the k most similar historical dates (by feature distance) within the same
  regime and use their empirical forecast-error distribution as an
  independent correction estimate — reported alongside the ML/quantile-
  mapping correction as a cross-check, and usable as an ensemble member.
- **Heavy rainfall probability + uncertainty**: fit regime-specific residual
  error distributions from the corrected forecast (for probability), and
  produce an uncertainty band via ensemble spread (across correction
  methods/analogs) or quantile regression — not a single deterministic
  probability number.
- **Aggregation**: area-weighted zonal statistics to district polygons;
  nearest-grid/interpolated values to station points.
- **Explainability**: SHAP (or equivalent) feature attribution stored
  alongside every regime prediction and correction decision, surfaced in
  the dashboard.

## 5. Data plan

| Need | Primary source | Fallback |
|---|---|---|
| Ground-truth rainfall (gridded) | IMD gridded rainfall (0.25°, daily) | ERA5 precipitation (clearly labeled as lower-quality substitute) |
| Ground-truth rainfall (station) | IMD station observations | Any publicly available station network for the domain |
| NWP forecast — source 1 | NCMRWF/IMD operational NWP output | NOAA GFS forecast archive |
| NWP forecast — source 2 (for ensemble fusion) | ECMWF open data | Any second public NWP archive |
| Regime-indicator fields (MSLP, OLR, winds) | ERA5 reanalysis | NOAA interpolated OLR + NCEP reanalysis |
| Satellite proxy | INSAT brightness temperature (if accessible) | NOAA interpolated OLR as convection proxy |
| Radar/nowcast (optional, for short lead times) | IMD radar mosaic (if accessible) | Omit lead times that need it; document as unavailable |
| Low-pressure-system/depression dates | IMD best-track archive | RSMC New Delhi best-track data (public) |
| Western disturbance dates | IMD WD advisories/climatology | Published WD climatology datasets |
| District boundaries | Survey of India | data.gov.in open data portal |
| Station metadata | IMD station list | Any public station metadata source |

**Domain and period**: fixed once in Task 0 (`data/ACCESS_NOTES.md`) —
architecture does not hard-code a region, so the domain can be widened later
without redesign, but the first fully verified build targets one domain and
1–3 monsoon seasons. Any fallback/proxy source used instead of the primary
one must be recorded explicitly in `README.md`.

## 6. Repository layout

```
PS 80/
├── PLAN.md
├── TEAM_SPLIT.md
├── README.md
├── requirements.txt
├── run_pipeline.py                    # end-to-end batch pipeline entry point
├── data/
│   ├── raw/                           # untouched downloads (NWP x2, obs, reanalysis, satellite, best-track, shapefile, stations)
│   │   └── district_shapefile/
│   ├── processed/                     # regridded/aligned/labeled/feature data
│   └── external/                      # reference tables (thresholds, station metadata, analog index)
├── src/
│   ├── ingest/
│   │   ├── nwp_sources/               # one module per NWP source
│   │   ├── observations/              # gridded + station obs
│   │   ├── satellite_radar/           # satellite proxy + radar (if available)
│   │   └── realtime_feed/             # schedulable ingestion scaffolding (batch-run in practice)
│   ├── preprocess/                    # regridding, feature engineering, regime labeling, climatology
│   ├── regime_classifier/             # multi-label classifier + explainability
│   ├── bias_correction/
│   │   ├── ensemble/                  # multi-NWP fusion
│   │   └── analog/                    # analog-based correction
│   ├── heavy_rain_prob/               # calibrated probability + uncertainty
│   ├── uncertainty/                   # shared UQ utilities (ensemble spread, quantile regression)
│   ├── explainability/                # SHAP/attribution utilities shared by classifier + correction
│   ├── mlops/
│   │   ├── retraining/                # retraining pipeline
│   │   ├── model_registry/            # versioned model storage/metadata
│   │   └── drift_monitoring/          # feature/skill drift checks
│   ├── district_agg/                  # district + station aggregation
│   ├── verification/                  # RMSE/ETS/CSI/POD/FAR/FSS/reliability, per-regime reports
│   └── alerts/                        # threshold-based alert generation + pluggable delivery interface
├── api/                                # API service exposing all products
├── dashboard/
│   ├── web/                            # dashboard app
│   └── components/                     # shared UI pieces (map, table, regime explainer, skill view)
├── infra/
│   ├── docker/                         # containerization
│   └── ci/                             # CI pipeline definitions
├── monitoring/                         # operational logging/metrics for the running system
├── tests/
│   ├── unit/
│   └── integration/
├── docs/                                # architecture doc, API reference, forecaster user guide
├── notebooks/                           # exploratory only — pipeline must not depend on these
└── outputs/
    ├── figures/
    ├── verification_report/
    └── alerts_log/
```

## 7. Task list

Same input/output contract discipline as before: every task states
**Inputs → Outputs → Done when**. Full assignment to people is in
[TEAM_SPLIT.md](TEAM_SPLIT.md); this list is the technical breakdown.

### Task 0 — Confirm data access & finalize domain/season/sources
- **Outputs**: `data/ACCESS_NOTES.md` naming every source actually used
  (primary or fallback, per Section 5), the two NWP sources chosen for
  ensemble fusion, and the fixed domain/season(s).
- **Done when**: no data need in Section 5 is unresolved.

### Task 1 — Multi-source ingestion
- **Outputs**: raw files under `data/raw/` for both NWP sources, gridded +
  station obs, reanalysis, satellite proxy, best-track (LPS + WD), district
  shapefile, station metadata — each with a manifest (source, date,
  license). Ingestion code structured so re-running it is idempotent
  (safe to schedule later even though it's run manually now).

### Task 2 — Preprocessing & multi-label regime labeling
- **Outputs**: `data/processed/features_daily.csv` (dynamical +
  thermodynamical + satellite-proxy features), `nwp_grid_<source>.nc` for
  each NWP source, `obs_grid.nc`, `climatology.nc`, `station_obs.csv`, and
  multi-label regime labels per date (`regime_labels.csv`: one row per
  date, one probability/flag column per of the 6 classes).

### Task 3 — Regime classifier (multi-label) + explainability
- **Outputs**: trained multi-label classifier, per-prediction SHAP
  attribution, `regime_predictions.csv` (per-label probabilities +
  confidence), `EVAL.md` (per-label precision/recall/confusion behavior).

### Task 4 — Ensemble fusion + regime-conditioned bias correction
- **Outputs**: `ensemble_grid.nc` (fused NWP), `corrected_grid.nc`
  (post-correction), method-choice log per regime (quantile mapping vs. ML),
  `analog_correction.nc` (independent analog-based estimate) — all keyed by
  date/lat/lon.

### Task 5 — Heavy rain probability + uncertainty quantification
- **Outputs**: `heavy_rain_prob.nc` with `p_heavy`, `p_very_heavy`, and
  uncertainty bounds (e.g. `p_heavy_lower`, `p_heavy_upper`), plus a
  calibration/reliability check artifact.

### Task 6 — District & station aggregation
- **Outputs**: `outputs/district_table.csv` and `outputs/station_table.csv`
  with rainfall, category, probability + uncertainty, regime label(s) and
  confidence.

### Task 7 — Full verification suite
- **Outputs**: `outputs/verification_report/` with RMSE, ETS, CSI, POD, FAR,
  multi-scale FSS, reliability diagrams — for raw vs. ensemble-blended vs.
  corrected, split by regime and threshold.

### Task 8 — API service
- **Outputs**: `api/` exposing endpoints for regime classification,
  corrected forecast, heavy-rain probability, district/station products,
  and verification summaries.

### Task 9 — Dashboard
- **Outputs**: `dashboard/` app consuming the API: map/table view, regime
  explanation panel, skill/verification view, historical regime climatology
  explorer, raw-vs-corrected comparison.

### Task 10 — Alerting layer
- **Outputs**: `src/alerts/` rule engine (threshold + confidence-based
  alert generation), `outputs/alerts_log/`, and a pluggable delivery
  interface (mocked channel implementation — see Section 2.2).

### Task 11 — MLOps: feedback, drift monitoring, retraining, registry
- **Outputs**: forecaster feedback capture format, drift-monitoring checks
  on features/skill, a retraining pipeline that produces a new versioned
  model in the model registry, rollback capability.

### Task 12 — Testing, CI, containerization, documentation
- **Outputs**: `tests/unit/`, `tests/integration/` (full pipeline on a
  fixture dataset), `infra/ci/` pipeline definition, `infra/docker/`
  container setup, `docs/` (architecture, API reference, user guide),
  final `README.md`, `run_pipeline.py` tying the batch path together end to
  end.

## 8. Deliverables checklist (Expected Outcome + innovations)

- [ ] Multi-label weather regime classifier with explainability (Task 3)
- [ ] Multi-model ensemble fusion (Task 4)
- [ ] Regime-conditioned bias correction, ML + quantile-mapping + analog
      pathways (Task 4)
- [ ] Calibrated heavy-rain probability with uncertainty bounds (Task 5)
- [ ] District- and station-level rainfall products (Task 6)
- [ ] Full verification suite incl. multi-scale FSS and reliability (Task 7)
- [ ] API service (Task 8)
- [ ] Interactive dashboard with regime explanation and climatology explorer
      (Task 9)
- [ ] Heavy-rain alerting layer (Task 10)
- [ ] Feedback + drift monitoring + retraining/model registry (Task 11)
- [ ] Tests, CI, Docker, full documentation (Task 12)

## 9. Research / reference sources needed

### 9.1 Domain background
- IMD/IITM active-break monsoon criteria (Rajeevan et al.; IITM monsoon
  monographs).
- IMD cyclone/depression e-atlas and best-track documentation.
- Western disturbance climatology and detection literature.
- Orographic (Western Ghats/NE hills) and coastal convergence rainfall
  mechanism literature.
- NCMRWF public technical reports on rainfall forecast bias/post-processing.

### 9.2 Datasets
- IMD gridded rainfall (0.25° daily) — access/registration/license.
- NCMRWF/IMD NWP archives, plus a second NWP source (ECMWF open data or
  NOAA GFS) for ensemble fusion.
- IMD/RSMC New Delhi best-track archive (LPS + depressions).
- IMD WD advisories / published WD climatology.
- ERA5/NOAA OLR reanalysis; INSAT brightness temperature if accessible.
- IMD radar mosaic availability (for optional short-lead-time products).
- District boundary shapefile + IMD station metadata.
- IMD's official rainfall category thresholds (heavy ≥64.5mm, very heavy
  ≥115.5mm, extremely heavy ≥204.5mm per 24h) — used verbatim, not invented.

### 9.3 Methods
- Standard verification formulas: RMSE, ETS, CSI, POD, FAR, FSS (multi-
  scale), reliability diagrams — WMO/WWRP guidance, Jolliffe & Stephenson.
- Quantile mapping and statistical precipitation bias-correction literature.
- Analog forecasting / analog-based post-processing literature.
- Regime-dependent/regime-conditioned post-processing precedent (search:
  "weather regime conditioned bias correction," "analog-based post-
  processing," "regime-dependent MOS precipitation").
- Multi-model ensemble blending/weighting methods for precipitation.
- Explainable ML for weather/climate applications (SHAP for tree models).
- Quantile regression / ensemble-spread approaches for forecast uncertainty.

### 9.4 Access/licensing checks (Task 0)
- Confirm institutional vs. open access for every IMD dataset; record every
  fallback substitution explicitly in README.md.

## 10. Definition of done

The system is complete when every item in Section 8 is checked, the batch
pipeline (`run_pipeline.py`) reproduces all outputs from the fixed sample
dataset in one command, the API and dashboard both run locally against that
output, `tests/` pass in CI, and `README.md`/`docs/` fully disclose every
fallback data source, every place a method defaulted (e.g. quantile mapping
instead of ML correction) due to data sparsity, and every deferred item from
Section 2.2.
