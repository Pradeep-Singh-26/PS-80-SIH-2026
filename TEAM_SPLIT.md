# Team Split — PS 26080

Read this alongside [PLAN.md](PLAN.md), which defines the full task list
(Tasks 0–9). This document assigns those tasks to three people and defines
**hard boundaries** so work can proceed in parallel without merge conflicts,
duplicated logic, or one person blocking another.

Rule of thumb: **you may only write files inside your own `src/<your_folders>/`
directories.** Every cross-person dependency goes through a file on disk in
`data/processed/` or `outputs/`, in the exact schema defined below — never
through a shared in-memory object, a shared config someone else also edits,
or a direct function import across tracks. If you need something from
another track that isn't in its contract below, that's a signal to raise it
and update this document — not to quietly reach into their folder.

---

## Track A — Pradeep: Data & Regime Labeling

**Owns**: PLAN.md Tasks 0, 1, 2
**Folders (exclusive write access)**: `data/`, `src/ingest/`, `src/preprocess/`

### Responsibilities
1. Confirm data access and finalize domain/season (Task 0) — write
   `data/ACCESS_NOTES.md`.
2. Download/prepare all raw data into `data/raw/` (Task 1): NWP forecast,
   observed rainfall, MSLP/OLR reanalysis, low-pressure-system track
   records, district shapefile. Include a manifest (source, download date,
   license) for each.
3. Regrid NWP+obs to a common grid, compute daily regime-indicator
   features, build climatology reference, and produce the per-date regime
   label (Task 2).

### Must produce (the contract — exact filenames/columns other tracks rely on)
- `data/processed/features_daily.csv` — one row per date, columns:
  `date, mslp_anomaly, olr_anomaly, rainfall_anomaly, lps_flag, regime_label`
  where `regime_label` ∈ {`active`, `break`, `low_depression`, `other`}.
- `data/processed/nwp_grid.nc` — raw NWP rainfall, regridded, dims
  `(date, lat, lon)`, variable name `precip_mm`.
- `data/processed/obs_grid.nc` — observed rainfall, same grid/dims/variable
  name as above, variable name `precip_mm`.
- `data/processed/climatology.nc` — same grid, variable `precip_mm_clim`,
  used as the quantile-mapping reference.
- `data/raw/district_shapefile/` — district polygons, any standard
  shapefile/GeoPackage, with a `district_name` attribute field.

### Explicitly NOT Pradeep's job
- Does not train any model (classifier, correction, or probability) — only
  produces the labeled/processed data those models consume.
- Does not touch `src/regime_classifier/`, `src/bias_correction/`,
  `src/heavy_rain_prob/`, `src/district_agg/`, `src/verification/`.

---

## Track B — Baljeet: Modeling (Classifier, Correction, Probability)

**Owns**: PLAN.md Tasks 3, 4, 5
**Folders (exclusive write access)**: `src/regime_classifier/`,
`src/bias_correction/`, `src/heavy_rain_prob/`

### Responsibilities
1. Train/evaluate the regime classifier (Task 3) using Pradeep's
   `features_daily.csv` as the only input — do not recompute features.
2. Build regime-conditioned bias correction (Task 4) using Pradeep's
   `nwp_grid.nc`, `obs_grid.nc`, `climatology.nc`, and the classifier's
   regime labels.
3. Estimate heavy-rain probability (Task 5) from the corrected forecast.

### Must consume only (never modify upstream files)
- `data/processed/features_daily.csv`
- `data/processed/nwp_grid.nc`, `obs_grid.nc`, `climatology.nc`

### Must produce (the contract)
- `data/processed/regime_predictions.csv` — columns: `date, regime_pred,
  regime_confidence` (held-out period).
- `data/processed/corrected_grid.nc` — dims `(date, lat, lon)`, variable
  `precip_mm_corrected`.
- `data/processed/heavy_rain_prob.nc` — dims `(date, lat, lon)`, variables
  `p_heavy` (≥64.5mm) and `p_very_heavy` (≥115.5mm).
- `src/regime_classifier/EVAL.md` — held-out accuracy/confusion matrix.

### Explicitly NOT Baljeet's job
- Does not touch `data/raw/`, `data/ingest/`, `data/preprocess/`, or
  regenerate features — if a feature is missing or wrong, flag it to
  Pradeep rather than recomputing it independently.
- Does not do district aggregation, verification metrics, or the
  presentation layer.

---

## Track C — Divyansh: Aggregation, Verification, Presentation, Integration

**Owns**: PLAN.md Tasks 6, 7, 8, 9
**Folders (exclusive write access)**: `src/district_agg/`,
`src/verification/`, `outputs/`, `run_pipeline.py`, `README.md`

### Responsibilities
1. Aggregate corrected forecast + heavy-rain probability to district level
   (Task 6) using Baljeet's outputs + Pradeep's district shapefile.
2. Compute verification metrics — RMSE, ETS, CSI, POD, FAR (FSS if time
   permits) — comparing raw vs. corrected forecast against obs, split by
   regime (Task 7).
3. Build the minimal presentation layer — static HTML or Streamlit page
   (Task 8).
4. Write `run_pipeline.py` that chains Tasks 1–8 end-to-end, and the final
   `README.md` (Task 9) — this is the only file allowed to reference/import
   code from all three tracks.

### Must consume only (never modify upstream files)
- `data/processed/corrected_grid.nc`, `heavy_rain_prob.nc`,
  `regime_predictions.csv` (from Baljeet)
- `data/processed/obs_grid.nc`, `nwp_grid.nc`, `features_daily.csv`
  (from Pradeep, for ground truth and regime split in verification)
- `data/raw/district_shapefile/` (from Pradeep)

### Must produce (the contract)
- `outputs/district_table.csv` — columns: `district_name, date,
  corrected_rainfall_mm, rainfall_category, p_heavy, p_very_heavy`.
- `outputs/verification_report/` — metric tables (RMSE, ETS, CSI, POD, FAR,
  FSS-if-implemented) for raw vs. corrected, split by regime.
- `outputs/figures/` — any supporting plots/maps.
- `run_pipeline.py`, `README.md`.

### Explicitly NOT Divyansh's job
- Does not train or modify any model in Track B, does not touch data
  ingestion/preprocessing in Track A. If an upstream file doesn't match its
  documented schema, that's a bug report to the owning track, not something
  to patch downstream.

---

## Cross-cutting rules (applies to all three)

1. **No shared mutable files.** Only `PLAN.md` and `TEAM_SPLIT.md` may be
   edited by anyone, and only to reflect an agreed scope/contract change —
   not silently.
2. **Contracts are frozen once Task 0 (Pradeep) is done.** If a downstream
   person needs a schema change (e.g. an extra column), they propose it by
   editing this document and pinging the upstream owner — they do not just
   start producing a divergent file.
3. **Everyone works against the packaged sample dataset** referenced in
   `data/ACCESS_NOTES.md` (produced by Pradeep in Task 0) so all three
   tracks can develop and test independently before integration.
4. **Integration only happens in Divyansh's `run_pipeline.py`.** No one
   else should write a script that imports across all three tracks.
5. If any task from PLAN.md doesn't clearly fall into one track, raise it —
   don't let two people build it independently.
