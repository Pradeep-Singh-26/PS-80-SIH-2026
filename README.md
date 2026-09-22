# PS 26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

A complete system (not a scoped-down demo) for MoES/NCMRWF problem statement
26080: multi-source ingestion, multi-label weather regime classification
with explainability, ensemble NWP fusion, regime-conditioned bias correction
(quantile mapping + ML + analog pathways), calibrated heavy-rain probability
with uncertainty, district/station products, full skill verification, an
API, a dashboard, an alerting layer, and an MLOps loop (feedback, drift
monitoring, retraining, model registry).

See [PLAN.md](PLAN.md) for the full architecture and task breakdown, and
[TEAM_SPLIT.md](TEAM_SPLIT.md) for how the three-person team divides the
work with strict, non-overlapping boundaries.

**Status: scaffolding only — no pipeline code has been written yet.**

## Setup (once implementation starts)

```
pip install -r requirements.txt
```

## Layout

See PLAN.md Section 6 for the full repository layout and PLAN.md Section 7
for the task list each folder corresponds to.

## Data sources actually used

To be filled in from `data/ACCESS_NOTES.md` once Task 0 is complete — this
section must list every place a fallback/proxy data source was used instead
of the primary one named in PLAN.md Section 5, and every place a method
defaulted (e.g. quantile mapping instead of ML correction) due to data
sparsity.

## Deferred scope

See PLAN.md Section 2.2 for what is explicitly out of reach for this build
(live operational data feeds, real SMS/push delivery, primary use of deep
spatial correction models, production cloud deployment, full nationwide
coverage) and why.
