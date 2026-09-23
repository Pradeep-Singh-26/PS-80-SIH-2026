# MLOps Drift Monitoring & Model Health Report (Task 11)

> **Track B (Baljeet) — PS 26080**  
> **Status**: `⚠️ RETRAINING RECOMMENDED`  
> **Evaluated Windows**: Chronological Reference vs Current Windows (Zero Lookahead)  
> **Data Status**: `SYNTHETIC FIXTURE / DEMO VALIDATION`

---

## 1. Monitoring Window Specifications

- **Reference Window**: `2024-06-01` to `2024-06-22` (1056 grid samples)
- **Current Evaluation Window**: `2024-06-23` to `2024-06-30` (384 grid samples)
- **Features Monitored**: Exact 19 input features consumed by Track B ML Bias Corrector.

---

## 2. Statistical Feature Drift Summary

| Metric | Threshold Rule | Description |
|---|---|---|
| **Low / No Drift** | `PSI < 0.10` | Distributions are statistically consistent |
| **Moderate Drift** | `0.10 <= PSI < 0.25` | Minor distribution shift; continue monitoring |
| **Significant Drift** | `PSI >= 0.25` | Substantial distribution shift; potential retraining trigger |

### Feature Summary
- **High Severity Drift Features (`PSI >= 0.25`)**: `13` (break_prob, western_disturbance_prob, v850_anomaly, coastal_prob, orographic_prob, low_depression_prob, olr_anomaly, confidence, rainfall_anomaly, active_prob, satellite_proxy, u850_anomaly, mslp_anomaly)
- **Medium Severity Drift Features (`0.10 <= PSI < 0.25`)**: `0` (None)

### Detailed Feature Drift Table
| Feature | Reference Mean | Current Mean | Mean Diff | PSI | KS Stat | KS p-value | Severity |
|---|---|---|---|---|---|---|---|
| `break_prob` | `0.1347` | `0.0598` | `-0.075` | **`8.9678`** | `0.4773` | `0.0` | `High` |
| `western_disturbance_prob` | `0.1487` | `0.2328` | `0.0841` | **`8.4673`** | `0.5568` | `0.0` | `High` |
| `v850_anomaly` | `-0.2764` | `3.2525` | `3.5289` | **`8.2628`** | `0.5682` | `0.0` | `High` |
| `coastal_prob` | `0.2005` | `0.1842` | `-0.0164` | **`7.6683`** | `0.2045` | `0.0` | `High` |
| `orographic_prob` | `0.211` | `0.1817` | `-0.0293` | **`7.5768`** | `0.2273` | `0.0` | `High` |
| `low_depression_prob` | `0.1496` | `0.1457` | `-0.0039` | **`7.023`** | `0.2273` | `0.0` | `High` |
| `olr_anomaly` | `5.0941` | `-1.515` | `-6.6091` | **`7.023`** | `0.2727` | `0.0` | `High` |
| `confidence` | `0.4024` | `0.3366` | `-0.0658` | **`6.3688`** | `0.4318` | `0.0` | `High` |
| `rainfall_anomaly` | `-0.1564` | `-0.155` | `0.0014` | **`6.2773`** | `0.1705` | `0.0` | `High` |
| `active_prob` | `0.1554` | `0.1959` | `0.0404` | **`5.632`** | `0.3864` | `0.0` | `High` |
| `satellite_proxy` | `227.48` | `223.71` | `-3.77` | **`5.632`** | `0.25` | `0.0` | `High` |
| `u850_anomaly` | `-1.6927` | `-0.1125` | `1.5802` | **`5.632`** | `0.3523` | `0.0` | `High` |
| `mslp_anomaly` | `-0.4168` | `0.09` | `0.5068` | **`3.605`** | `0.1818` | `0.0` | `High` |
| `wd_flag` | `0.1364` | `0.25` | `0.1136` | **`0.0849`** | `0.0` | `1.0` | `Low` |
| `precip_ensemble` | `45.6073` | `45.2026` | `-0.4047` | **`0.0222`** | `0.0365` | `0.8344` | `Low` |
| `lps_flag` | `0.2273` | `0.25` | `0.0227` | **`0.0028`** | `0.0` | `1.0` | `Low` |
| `precip_clim` | `16.5181` | `16.5181` | `0.0` | **`0.0`** | `0.0` | `1.0` | `Low` |
| `lon` | `77.5` | `77.5` | `0.0` | **`0.0`** | `0.0` | `1.0` | `Low` |
| `lat` | `20.5` | `20.5` | `0.0` | **`0.0`** | `0.0` | `1.0` | `Low` |

---

## 3. Forecast Skill Degradation Summary

| Metric | Reference Period | Current Period | Change (%) | Status |
|---|---|---|---|---|
| **MAE** | `7.96 mm` | `19.46 mm` | `144.51%` | ⚠️ Degraded |
| **RMSE** | `10.57 mm` | `25.45 mm` | `140.87%` | ⚠️ Degraded |
| **Mean Bias** | `-0.0 mm` | `-1.51 mm` | — | ✅ Stable |

---

## 4. Retraining Decision & Action Items

- **Should Retrain**: **`True`**
- **Approved Feedback Records Available**: `0`
- **Trigger Reasons**:
  - 13 features exhibit significant distribution drift (PSI >= 0.25): break_prob, western_disturbance_prob, v850_anomaly, coastal_prob, orographic_prob.
  - Forecast skill degraded: validation RMSE increased by 140.9% (threshold: >= 15%).

---

## 5. Engineering Limitations & Disclosures

> [!IMPORTANT]
> **Operational Context**:
> These drift diagnostics are computed on synthetic fixture data for pipeline validation. Configurable heuristic thresholds (`PSI >= 0.25`, `RMSE degradation >= 15%`) will be tuned against multi-year operational monsoon distributions when Track A real data is ingested.
