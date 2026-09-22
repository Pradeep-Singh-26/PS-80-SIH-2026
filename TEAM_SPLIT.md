# Team Split — PS 26080 (full-solution build)

Read alongside [PLAN.md](PLAN.md) (full task list, Tasks 0–12). This
document assigns those tasks to three people across the **expanded, full-
solution scope** (multi-source ingestion, multi-label regimes, ensemble
fusion, analog correction, uncertainty quantification, explainability, API,
dashboard, alerting, MLOps, testing/CI/Docker/docs) and defines **hard
boundaries** so all three can build in parallel without clashing.

Rule of thumb, unchanged from before: **you may only write files inside your
own folders.** Every cross-person dependency goes through a file on disk in
`data/processed/` or `outputs/`, in the exact schema below — never through a
shared in-memory object or a direct cross-track import. If something isn't
covered by a contract below, raise it and update this document rather than
guessing.

---

## Track A — Pradeep: Data, Ingestion & Regime Intelligence

**Owns PLAN.md Tasks**: 0, 1, 2, 3 (regime classifier + explainability of
the classifier only)
**Exclusive write access**: `data/`, `src/ingest/**`, `src/preprocess/`,
`src/regime_classifier/`, and the classifier's slice of
`src/explainability/` (attribution code specific to the regime model).

### Responsibilities
1. **Task 0** — confirm access for every source in PLAN.md Section 5;
   finalize domain/season(s) and the two NWP sources used for ensemble
   fusion; write `data/ACCESS_NOTES.md`.
2. **Task 1** — multi-source ingestion: both NWP sources, gridded + station
   observations, reanalysis (MSLP/OLR/winds), satellite proxy, radar (if
   available), IMD best-track (LPS + WD), district shapefile, station
   metadata. Structure ingestion so it's idempotent/re-runnable (schedulable
   later, even though it's run manually now).
3. **Task 2** — regridding, feature engineering (dynamical +
   thermodynamical + satellite-proxy features), climatology computation,
   and **multi-label** regime labeling for all 6 classes in PLAN.md
   Section 3.
4. **Task 3** — train/evaluate the **multi-label** regime classifier and
   its explainability (SHAP-style attribution per prediction).

### Must produce (contract — exact filenames/schemas other tracks rely on)
- `data/ACCESS_NOTES.md`
- `data/raw/` — all raw sources with per-file manifest (source, date,
  license); `data/raw/district_shapefile/` with `district_name` attribute.
- `data/processed/features_daily.csv` — one row per date: `date,
  mslp_anomaly, olr_anomaly, satellite_proxy, rainfall_anomaly, lps_flag,
  wd_flag, ...` (all model input features).
- `data/processed/nwp_grid_<source>.nc` — one per NWP source, dims
  `(date, lat, lon)`, variable `precip_mm`.
- `data/processed/obs_grid.nc` — same grid/dims, variable `precip_mm`.
- `data/processed/station_obs.csv` — columns: `station_id, date,
  precip_mm`.
- `data/processed/climatology.nc` — variable `precip_mm_clim`.
- `data/processed/regime_labels.csv` — columns: `date, active, break,
  low_depression, western_disturbance, orographic, coastal` (0/1 or
  probability per label — ground-truth labels used for training/eval).
- `data/processed/regime_predictions.csv` — columns: `date, <label>_prob`
  for each of the 6 labels, `dominant_label`, `confidence`.
- `src/regime_classifier/EVAL.md` — per-label precision/recall, confusion
  behavior, held-out evaluation.
- `src/regime_classifier/explanations/` — per-prediction attribution
  output, schema: `date, feature, attribution_value`.

### Explicitly NOT Pradeep's job
- Does not build bias correction, ensemble fusion, analog correction, heavy-
  rain probability/uncertainty, aggregation, verification, API, dashboard,
  alerts, or MLOps retraining/registry/drift code.
- Does not write to `src/bias_correction/`, `src/heavy_rain_prob/`,
  `src/uncertainty/`, `src/district_agg/`, `src/verification/`,
  `src/alerts/`, `src/mlops/`, `api/`, `dashboard/`.

---

## Track B — Baljeet: Correction, Probability, Uncertainty & MLOps

**Owns PLAN.md Tasks**: 4, 5, 11
**Exclusive write access**: `src/bias_correction/**`, `src/heavy_rain_prob/`,
`src/uncertainty/`, `src/mlops/**`, and the correction model's slice of
`src/explainability/` (attribution specific to correction models).

### Responsibilities
1. **Task 4** — multi-NWP ensemble fusion; regime-conditioned bias
   correction via both quantile mapping and ML correction (per-regime
   method choice logged); analog-based correction as an independent
   pathway.
2. **Task 5** — calibrated heavy/very-heavy rainfall probability with
   uncertainty bounds (ensemble spread or quantile regression), plus a
   reliability/calibration check.
3. **Task 11** — forecaster feedback capture format, drift monitoring on
   features/skill, retraining pipeline, model registry with versioning and
   rollback.

### Must consume only (from Track A — never modify these files)
- `data/processed/features_daily.csv`, `regime_predictions.csv`,
  `nwp_grid_<source>.nc`, `obs_grid.nc`, `climatology.nc`,
  `station_obs.csv`.

### Must produce (contract)
- `data/processed/ensemble_grid.nc` — fused NWP, dims `(date, lat, lon)`,
  variable `precip_mm_ensemble`.
- `data/processed/corrected_grid.nc` — variable `precip_mm_corrected`, plus
  a companion `data/processed/correction_method_log.csv` (columns: `date,
  regime, method_used`).
- `data/processed/analog_correction.nc` — variable
  `precip_mm_analog_estimate`, independent of the ML correction above.
- `data/processed/heavy_rain_prob.nc` — variables `p_heavy`,
  `p_very_heavy`, `p_heavy_lower`, `p_heavy_upper`,
  `p_very_heavy_lower`, `p_very_heavy_upper`.
- `src/heavy_rain_prob/CALIBRATION.md` — reliability check results.
- `src/mlops/model_registry/` — versioned model artifacts + metadata
  (never referenced directly by other tracks except by version tag).
- `src/mlops/drift_monitoring/REPORT.md` — periodic drift status format
  (template, not necessarily live-scheduled).
- `src/mlops/retraining/feedback_schema.md` — the structured format Track C
  and any forecaster-facing UI must use to submit feedback (Track C writes
  feedback data using this schema; only Track B reads/consumes it for
  retraining).

### Explicitly NOT Baljeet's job
- Does not touch `data/raw/`, ingestion, feature engineering, or regime
  labeling (flag issues to Pradeep instead of recomputing).
- Does not do district/station aggregation, verification metrics, API,
  dashboard, or alert delivery.

---

## Track C — Divyansh: Aggregation, Verification, Serving, Alerts & Ops

**Owns PLAN.md Tasks**: 6, 7, 8, 9, 10, 12
**Exclusive write access**: `src/district_agg/`, `src/verification/`,
`src/alerts/`, `api/`, `dashboard/**`, `infra/**`, `monitoring/`,
`tests/**`, `docs/`, `outputs/**`, `run_pipeline.py`, `README.md`.

### Responsibilities
1. **Task 6** — district- and station-level aggregation from Track B's
   corrected/probability outputs + Track A's shapefile/station metadata.
2. **Task 7** — full verification suite (RMSE, ETS, CSI, POD, FAR,
   multi-scale FSS, reliability diagrams) comparing raw vs.
   ensemble-blended vs. corrected, split by regime/threshold.
3. **Task 8** — API service exposing all products.
4. **Task 9** — dashboard (map/table, regime explanation panel using Track
   A's/B's explanation outputs, skill view, climatology explorer,
   raw-vs-corrected comparison).
5. **Task 10** — alert rule engine + alert log + pluggable (mocked)
   delivery interface.
6. **Task 12** — tests (unit + integration), CI config, Docker setup,
   documentation, final README, and `run_pipeline.py` as the **only** file
   that chains all three tracks together end to end.

### Must consume only (never modify upstream files)
- From Track A: `regime_predictions.csv`, `obs_grid.nc`,
  `nwp_grid_<source>.nc`, `features_daily.csv`, `station_obs.csv`,
  `data/raw/district_shapefile/`, classifier explanations.
- From Track B: `ensemble_grid.nc`, `corrected_grid.nc`,
  `correction_method_log.csv`, `analog_correction.nc`,
  `heavy_rain_prob.nc`, correction explanations, model registry version
  tags (read-only, for display/provenance only).

### Must produce (contract)
- `outputs/district_table.csv` — `district_name, date,
  corrected_rainfall_mm, rainfall_category, p_heavy, p_very_heavy,
  uncertainty_lower, uncertainty_upper, dominant_regime,
  regime_confidence, correction_method`.
- `outputs/station_table.csv` — analogous, at station level.
- `outputs/verification_report/` — full metric suite, per regime/threshold.
- `outputs/alerts_log/` — generated alerts with timestamp, district,
  threshold crossed, confidence.
- `api/`, `dashboard/`, `infra/`, `tests/`, `docs/`, `run_pipeline.py`,
  `README.md`.
- Feedback data (if collected via dashboard) written using Track B's
  `feedback_schema.md` contract — Track C produces feedback records, Track
  B consumes them for retraining; Track C does not implement retraining
  itself.

### Explicitly NOT Divyansh's job
- Does not train or modify any model in Track A or B. If an upstream file
  doesn't match its documented schema, that's a bug report to the owning
  track, not something to patch downstream.
- Does not implement the actual retraining logic (only produces feedback
  data in the agreed schema for Track B to consume).

---

## Cross-cutting rules (applies to all three)

1. **No shared mutable files.** Only `PLAN.md` and `TEAM_SPLIT.md` may be
   edited by anyone, and only to record an agreed scope/contract change.
2. **Contracts freeze once Task 0 (Pradeep) is done.** A downstream schema
   change is proposed by editing this document and pinging the upstream
   owner — never by silently diverging.
3. **`src/explainability/` is split by ownership, not folder**: Pradeep
   owns classifier-attribution code, Baljeet owns correction-attribution
   code. If a shared utility is needed, it goes in
   `src/explainability/common/` and either party may add to it, but neither
   may modify the other's method-specific files there.
4. **`src/mlops/model_registry/` is Track B's**, but Track C's API/dashboard
   may *read* model version metadata from it for display purposes only —
   never write to it.
5. **Everyone works against the fixed sample dataset** defined by
   `data/ACCESS_NOTES.md` (Task 0) so all three tracks can develop/test
   independently before integration.
6. **Integration only happens in Divyansh's `run_pipeline.py`, `api/`, and
   `dashboard/`.** No one else writes a script importing across all three
   tracks.
7. If any PLAN.md task doesn't clearly map to one track, raise it — don't
   let two people build the same thing independently.
