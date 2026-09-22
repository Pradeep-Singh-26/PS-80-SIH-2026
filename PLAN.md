# PS 26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

> **How to use this document (read this first, especially if you are an agent
> picking this up with no prior context):** This file is the single source of
> truth for what to build, in what order, and what "done" means for each
> piece. Do not start coding before Section 2 (scope) and Section 9 (data
> access) are resolved for the current environment — they gate everything
> else. Work top-to-bottom through Section 7 (task list); each task states
> its inputs, outputs, and acceptance criteria so it can be picked up,
> paused, or handed to a different agent without re-deriving context. If a
> decision point requires human input (e.g. no data access), stop and ask
> rather than guessing silently — flag it explicitly in your output.

## 0. One-paragraph summary

Build a prototype pipeline that (a) classifies the prevailing Indian monsoon
weather regime for a given date, (b) applies a regime-specific correction to
raw NWP rainfall forecasts for that date, (c) estimates probability of heavy/
very-heavy rainfall from the corrected forecast, (d) aggregates results to
Indian districts, and (e) verifies corrected vs. raw forecasts against
observations using standard forecast-verification metrics. This is a
proof-of-concept for a hackathon/PoC submission to MoES/NCMRWF, not an
operational system — scope is deliberately narrowed (see Section 2) to be
buildable and demoable with public data.

## 1. Problem framing

Raw NWP rainfall forecasts have systematic, regime-dependent biases (active
monsoon, break monsoon, low/depression, orographic, coastal, western
disturbance). A single global bias-correction model averages over these
regimes and underperforms in each. Solution shape:
**classify regime → route to regime-specific correction → produce
district/grid rainfall + heavy-rain probability + verification report.**

## 2. Scope — what to build now vs. defer

Treat this section as binding. If you are unsure whether something is in
scope, it is not — add it to "deferred" and move on.

### 2.1 IN SCOPE for this prototype
1. **Weather regime classifier** — 4-class (see Section 3), feature-based
   (not raw imagery/deep learning), trained on a limited domain and 1–2
   monsoon seasons.
2. **Regime-conditioned bias correction** — one correction step per regime
   class, applied to raw NWP grid rainfall (see Section 4 for method choice
   and the fallback if per-regime data is too sparse).
3. **Heavy rainfall probability** — probability of exceeding IMD's official
   heavy (≥64.5mm/24h) and very heavy (≥115.5mm/24h) thresholds, derived from
   the corrected forecast.
4. **District aggregation** — area-weighted mean of grid values within each
   district polygon, producing a table (and optionally a simple map).
5. **Verification report** — RMSE, ETS, CSI, POD, FAR for raw vs. corrected
   forecast against observations, broken out by regime and by rain
   threshold. FSS is optional/best-effort (see 2.2).
6. **Minimal output layer** — a static table + map image, or a simple
   Streamlit/HTML page. Not a hosted service.
7. **One reproducible end-to-end script/notebook chain** runnable on a
   packaged sample dataset.

### 2.2 DEFERRED / explicitly OUT OF SCOPE for this prototype
Do not build these unless the user explicitly asks to expand scope:
- Pan-India, multi-model/multi-NWP ensemble ingestion (start with one NWP
  source only).
- Real-time/operational data feed, automated ingestion, cron/scheduling.
- Deep learning on raw spatial fields (CNN/U-Net/ConvLSTM) for correction.
- Full multi-scale FSS / full spatial verification suite (implement a basic
  single-scale FSS only if time permits; otherwise omit and say so in the
  report).
- Sub-daily (3-hourly) or nowcasting-scale resolution — daily accumulated
  rainfall only.
- Regime detection from satellite/INSAT imagery — use reanalysis-derived
  circulation indices instead.
- Auth, API hosting, cloud deployment, scaling.
- Explainability dashboards, uncertainty quantification beyond the basic
  probability output.
- Multi-label/simultaneous regime overlap — assign a single dominant regime
  per date.

## 3. Weather regime classes (final label set — use exactly these 4)

| Label | Meaning | Primary detection signal |
|---|---|---|
| `active` | Active monsoon: strong monsoon trough, above-normal rainfall over the monsoon core zone | Rainfall anomaly + MSLP trough position |
| `break` | Break monsoon: weak/displaced trough, suppressed rainfall over central India | Rainfall anomaly (negative) + trough displacement |
| `low_depression` | A monsoon low or depression is present | IMD best-track / low-pressure-system presence flag |
| `other` | Everything else, including orographic/coastal-enhanced and (if in the demo season) western-disturbance-influenced days | Fallback when none of the above triggers |

Rationale for collapsing to 4 classes (not 6): keeps per-class training data
large enough to be trainable within a 1–2 season dataset. If a future
iteration has more data, `other` can be split into `orographic_coastal` and
`western_disturbance` — treat that as a backlog item, not a blocker now.

## 4. Modeling approach

- **Regime classifier**: feature-based gradient boosting (XGBoost/LightGBM)
  over physically meaningful daily indices: monsoon trough latitude proxy,
  MSLP anomaly, OLR anomaly, regional rainfall anomaly, IMD low-pressure-
  system presence flag (binary). If labeled data is too scarce to train a
  model reliably, fall back to a rule-based decision tree using the same
  indices — document which path was used and why.
- **Bias correction**: per-regime quantile mapping (preferred, simplest,
  most defensible) using NWP rainfall + climatology as reference. **Fallback
  rule**: if any regime class has too few historical samples to fit a
  reliable per-regime quantile mapping (rule of thumb: fewer than ~30 grid-
  days), fall back to a single model with regime as a one-hot feature
  instead of a fully separate model per regime. Record which regimes used
  which path in the run's output metadata.
- **Heavy rainfall probability**: fit the regime-specific residual error
  distribution of the corrected forecast, compute P(rain > threshold) from
  it. If enough heavy-rain events exist in training data, a direct binary
  classifier per threshold is an acceptable alternative — pick whichever is
  simpler given the data actually available.
- **District aggregation**: area-weighted mean of grid cells intersecting
  each district polygon (standard GIS zonal statistics — no need for a
  custom method).

## 5. Data plan

| Need | Preferred source | Public fallback if preferred is inaccessible |
|---|---|---|
| Ground-truth rainfall | IMD gridded rainfall (0.25°, daily) | — (if entirely inaccessible, state this explicitly in README and consider ERA5 precipitation as a lower-quality substitute, clearly labeled as such) |
| Raw NWP forecast | NCMRWF/IMD operational NWP output | NOAA GFS forecast archive, or ECMWF open data, or ERA5/IMDAA reanalysis used as a "perfect prog" proxy |
| Regime-indicator fields (MSLP, OLR) | ERA5 reanalysis | NOAA interpolated OLR + NCEP reanalysis |
| Low-pressure-system/depression dates | IMD best-track archive | RSMC New Delhi best-track data (public) |
| District boundaries | Survey of India | data.gov.in open data portal, or a maintained public GIS admin-boundary repository |

**Domain and period**: restrict to one representative subregion (e.g. the
central India monsoon core zone) and 1–2 monsoon seasons, chosen once actual
data access is confirmed (see Section 9). This keeps the packaged sample
dataset small enough to ship with the prototype.

Any time a fallback/proxy source is used instead of the preferred one, this
must be stated explicitly in the README, not just in this plan.

## 6. Repository layout

Use this structure so any agent or contributor knows where things go. Create
folders as they're needed — don't pre-create empty ones.

```
PS 80/
├── PLAN.md                  # this file — always keep in sync with actual scope
├── README.md                # user-facing: how to run, data sources used, known limitations
├── data/
│   ├── raw/                 # untouched downloaded data (NWP, obs, reanalysis, shapefile)
│   └── processed/           # regridded/aligned/labeled data ready for modeling
├── src/
│   ├── ingest/               # scripts to pull/prepare each data source (Section 7, Task 1)
│   ├── preprocess/            # regridding, feature computation, regime labeling (Task 2)
│   ├── regime_classifier/     # training + inference (Task 3)
│   ├── bias_correction/       # per-regime correction models (Task 4)
│   ├── heavy_rain_prob/       # probability estimation (Task 5)
│   ├── district_agg/          # grid-to-district aggregation (Task 6)
│   └── verification/          # metric computation + report generation (Task 7)
├── notebooks/                # exploratory work; final pipeline must NOT depend on notebooks
├── outputs/
│   ├── district_table.csv    # Task 6 output
│   ├── verification_report/  # Task 7 output (tables + plots)
│   └── figures/
├── run_pipeline.py            # single entry point chaining all stages end-to-end
└── requirements.txt
```

## 7. Task list (do in this order; each is independently checkable)

Each task specifies **Inputs → Outputs → Done when**. Do not mark a task
complete unless "Done when" is satisfied.

### Task 0 — Confirm data access and finalize domain/season
- **Inputs**: Section 5 data plan, Section 9 access questions.
- **Outputs**: a short `data/ACCESS_NOTES.md` stating exactly which sources
  are used (preferred or fallback) and the final chosen domain + season.
- **Done when**: every data need in Section 5 has a named, confirmed-
  accessible source, and the domain/season is fixed (not "TBD").
- **Blocking**: all later tasks depend on this. If access cannot be
  confirmed autonomously, stop and ask the user rather than guessing.

### Task 1 — Data ingestion
- **Inputs**: sources confirmed in Task 0.
- **Outputs**: raw files under `data/raw/` for NWP forecast, observed
  rainfall, MSLP/OLR reanalysis, low-pressure-system track records, district
  shapefile.
- **Done when**: all five raw datasets are present locally, covering the
  chosen domain and season, with a short manifest (source URL, download
  date, license) recorded per file.

### Task 2 — Preprocessing
- **Inputs**: `data/raw/*`.
- **Outputs**: `data/processed/` containing (a) NWP and obs regridded to a
  common grid, (b) a daily feature table of regime indicators, (c) a
  climatology reference for quantile mapping, (d) a per-date regime label
  (one of the 4 classes in Section 3) derived from the low-pressure-system
  track record and rainfall/MSLP anomaly rules.
- **Done when**: every date in the chosen season has a regime label and a
  complete feature row; no missing grid alignment between NWP and obs.

### Task 3 — Regime classifier
- **Inputs**: `data/processed/` feature table + labels from Task 2.
- **Outputs**: trained classifier (or documented rule-based fallback) under
  `src/regime_classifier/`, plus a held-out evaluation (accuracy/confusion
  matrix per class).
- **Done when**: the model produces a regime label + confidence for any date
  in the held-out period, and evaluation results are saved (not just
  printed).

### Task 4 — Regime-conditioned bias correction
- **Inputs**: Task 3 regime labels, `data/processed/` NWP + obs.
- **Outputs**: per-regime (or regime-as-feature fallback, per Section 4)
  correction model(s) under `src/bias_correction/`, and a corrected rainfall
  grid for the held-out period.
- **Done when**: corrected forecast exists for every held-out grid-day, and
  it is measurably closer to observations than the raw forecast on at least
  the primary metric (RMSE) — if it is not, that is itself a valid finding
  to report, not a reason to hide the result.

### Task 5 — Heavy rainfall probability
- **Inputs**: corrected forecast from Task 4, regime labels from Task 3.
- **Outputs**: per grid cell/day, P(rain ≥ 64.5mm) and P(rain ≥ 115.5mm),
  under `src/heavy_rain_prob/`.
- **Done when**: probabilities are produced for every held-out grid-day and
  are between 0 and 1 (sanity-checked), with a brief calibration check
  (e.g. reliability diagram or binned observed frequency vs. predicted
  probability).

### Task 6 — District aggregation
- **Inputs**: corrected forecast (Task 4), heavy-rain probability (Task 5),
  district shapefile (Task 1).
- **Outputs**: `outputs/district_table.csv` with columns: district name,
  date, corrected rainfall, rainfall category, P(heavy), P(very heavy).
  Optional: a simple choropleth map image in `outputs/figures/`.
- **Done when**: every district in the chosen domain has a row for every
  date in the held-out period, with no unmapped/missing districts.

### Task 7 — Verification report
- **Inputs**: raw NWP, corrected forecast (Task 4), observations, regime
  labels (Task 3).
- **Outputs**: `outputs/verification_report/` containing RMSE, ETS, CSI,
  POD, FAR computed for raw vs. corrected, split by regime and by rain
  threshold; FSS included only if implemented (state explicitly if omitted).
- **Done when**: the report shows a like-for-like raw-vs-corrected
  comparison per regime per metric, in a table any reader can interpret
  without reading the code.

### Task 8 — Presentation layer
- **Inputs**: `outputs/district_table.csv`, `outputs/verification_report/`.
- **Outputs**: a single static HTML page or simple Streamlit app showing the
  district table/map and a summary of verification results.
- **Done when**: it runs locally with one command and requires no manual
  data wrangling.

### Task 9 — End-to-end integration
- **Inputs**: Tasks 1–8.
- **Outputs**: `run_pipeline.py` that runs Tasks 1–8 in sequence on the
  packaged sample dataset, plus `README.md` documenting how to run it, what
  data sources were actually used (vs. the preferred ones in Section 5), and
  known limitations.
- **Done when**: a fresh clone can run `run_pipeline.py` and reproduce
  `outputs/` from the packaged sample data alone.

## 8. Deliverables checklist (maps directly to the problem statement's
   "Expected Outcome")

- [ ] Weather regime classifier (Task 3)
- [ ] Bias-corrected rainfall forecast (Task 4)
- [ ] Heavy rainfall probability (Task 5)
- [ ] District-level rainfall product (Task 6)
- [ ] Verification report: RMSE, ETS, CSI, POD, FAR, FSS-if-feasible (Task 7)
- [ ] End-to-end reproducible pipeline (Task 9)
- [ ] README with data-source and limitation disclosures (Task 9)

## 9. Research / reference sources needed

Use this section to fill knowledge gaps before/while doing Tasks 0–7.
Grouped by what each is needed for.

### 9.1 Domain background (regime definitions, physical indices)
- IMD/IITM literature on active vs. break monsoon definitions (e.g. Rajeevan
  et al. active-break criteria; IITM monsoon monograph series) — needed for
  Task 2 labeling rules.
- IMD cyclone/depression e-atlas and best-track documentation — needed for
  Task 2 `low_depression` labeling.
- Literature on western disturbance climatology — only needed if that
  regime stays in scope for the chosen season (currently folded into
  `other`, see Section 3).
- Reference material on orographic (Western Ghats/NE hills) and coastal
  convergence rainfall mechanisms — supports the `other` class definition
  and README justification.
- NCMRWF's own public technical reports on rainfall forecast bias/post-
  processing, if available — helps align terminology with the sponsoring
  department's expectations.

### 9.2 Datasets (see also Section 5 table)
- IMD gridded rainfall data — portal, registration requirements, license.
- NCMRWF/IMD NWP output archives — what's public vs. what needs a data-
  sharing request.
- IMD/RSMC New Delhi best-track archive — for depression date labeling.
- ERA5 / NOAA OLR reanalysis — for MSLP/OLR indicator features.
- District boundary shapefile — source and currency check (district
  reorganizations may have occurred since the shapefile was published).
- IMD's official rainfall category thresholds (light/moderate/heavy≥64.5mm/
  very heavy≥115.5mm/extremely heavy≥204.5mm per 24h) — must match exactly
  in Task 5, not use an invented cutoff.

### 9.3 Methods (verification metrics, bias-correction techniques)
- Standard formulas for RMSE, ETS, CSI, POD, FAR, FSS — e.g. WMO/WWRP
  forecast verification guidance, Jolliffe & Stephenson's "Forecast
  Verification" — needed for Task 7 to match community-standard
  definitions.
- Literature on quantile mapping and other statistical precipitation bias-
  correction methods — needed to justify the Task 4 method choice.
- Prior work on regime-dependent/regime-conditioned post-processing of
  precipitation forecasts (search: "weather regime conditioned bias
  correction," "analog-based post-processing," "regime-dependent MOS
  precipitation") — establishes precedent for the overall approach, useful
  for the README/report's justification section.

### 9.4 Access/licensing checks (resolve as part of Task 0)
- Determine which IMD datasets require institutional login/paid access vs.
  open access. If the "preferred" source in Section 5 is inaccessible, use
  the listed fallback and state the substitution explicitly in README.md —
  never silently swap a data source without recording it.

## 10. Definition of done for the whole prototype

The prototype is complete when: Section 8's checklist is fully checked,
`run_pipeline.py` reproduces all outputs from packaged sample data in one
command, and `README.md` accurately discloses every place a fallback/proxy
data source or simplifying assumption was used instead of the ideal one.
