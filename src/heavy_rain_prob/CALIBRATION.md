# Heavy Rainfall Probability Calibration & Reliability Verification Report (Task 5)

> **Track B (Baljeet) — PS 26080**  
> **Status**: `SYNTHETIC FIXTURE / DEMO VALIDATION`  
> Evaluated strictly on **held-out chronological validation data** (Zero temporal lookahead / Zero train contamination).

---

## 1. Protocol & Partition Specifications

- **Evaluation Principle**: Evaluated strictly on held-out validation days not seen during calibration.
- **Calibration Partition (75%)**: `2024-06-01` to `2024-06-22` (22 days, 1056 grid points).
- **Held-Out Validation Partition (25%)**: `2024-06-23` to `2024-06-30` (8 days, 384 grid points).
- **Heavy Rain Threshold**: `≥ 64.5 mm/24h` (Official IMD standard).
- **Very Heavy Rain Threshold**: `≥ 115.6 mm/24h` (Official IMD standard).

---

## 2. Held-Out Validation Probabilistic Skill Metrics

| Metric | Heavy Rainfall (`≥ 64.5 mm`) | Very Heavy Rainfall (`≥ 115.6 mm`) | Description |
|---|---|---|---|
| **Observed Events (Validation)** | `45` / 384 | `6` / 384 | Observed threshold exceedance counts |
| **Validation Base Rate** | `11.72%` | `1.56%` | Empirical event frequency in test sample |
| **Calibration Climatology (p_ref)** | `10.70%` | `0.76%` | Prior reference frequency from train split |
| **Brier Score (BS)** | **`0.1560`** | **`0.0200`** | Mean squared probability error (0.0 = perfect) |
| **Reference Brier Score (BS_ref)** | `0.1036` | `0.0154` | Climatology benchmark Brier Score |
| **Brier Skill Score (BSS)** | **`-0.5062`** | **`-0.2934`** | Skill improvement over climatology (> 0 is skill) |
| **Expected Calibration Error (ECE)** | **`0.1184`** | **`0.0195`** | Weighted average reliability deviation |
| **ROC-AUC (Discrimination)** | **`0.5405`** | **`0.5049`** | Area under ROC curve |

---

## 3. Reliability Bin Distribution (Held-Out Data)

### A. Heavy Rainfall (`p_heavy`, threshold ≥ 64.5 mm)
| Bin Range | Mean Forecast Prob | Observed Frequency | Count (Points) | Share (%) |
|---|---|---|---|---|
| `[0.0, 0.1)` | `0.0516` | `0.1010` | `198` | `51.6%` |
| `[0.1, 0.2)` | `0.1398` | `0.1348` | `89` | `23.2%` |
| `[0.2, 0.3)` | `0.2376` | `0.1200` | `25` | `6.5%` |
| `[0.3, 0.4)` | `0.3544` | `0.1250` | `24` | `6.2%` |
| `[0.4, 0.5)` | `0.4478` | `0.3333` | `9` | `2.3%` |
| `[0.5, 0.6)` | `0.5267` | `0.2500` | `8` | `2.1%` |
| `[0.6, 0.7)` | `0.6488` | `0.0000` | `6` | `1.6%` |
| `[0.7, 0.8)` | `0.7413` | `0.0000` | `7` | `1.8%` |
| `[0.8, 0.9)` | `0.8367` | `0.0000` | `5` | `1.3%` |
| `[0.9, 1.0]` | `0.9462` | `0.1538` | `13` | `3.4%` |

### B. Very Heavy Rainfall (`p_very_heavy`, threshold ≥ 115.6 mm)
| Bin Range | Mean Forecast Prob | Observed Frequency | Count (Points) | Share (%) |
|---|---|---|---|---|
| `[0.0, 0.1)` | `0.0083` | `0.0163` | `367` | `95.6%` |
| `[0.1, 0.2)` | `0.1507` | `0.0000` | `6` | `1.6%` |
| `[0.2, 0.3)` | `0.2351` | `0.0000` | `7` | `1.8%` |
| `[0.3, 0.4)` | `0.3472` | `0.0000` | `1` | `0.3%` |
| `[0.4, 0.5)` | `0.4292` | `0.0000` | `1` | `0.3%` |
| `[0.5, 0.6)` | `0.5139` | `0.0000` | `1` | `0.3%` |
| `[0.6, 0.7)` | `0.6500` | `nan` | `0` | `0.0%` |
| `[0.7, 0.8)` | `0.7042` | `0.0000` | `1` | `0.3%` |
| `[0.8, 0.9)` | `0.8500` | `nan` | `0` | `0.0%` |
| `[0.9, 1.0]` | `0.9500` | `nan` | `0` | `0.0%` |

---

## 4. Mathematical & Sanity Guarantees Verified

1. **Probability Range**: `0.0 <= p <= 1.0` strictly satisfied for 100% of grid points.
2. **Cross-Threshold Monotonicity**: `p_very_heavy <= p_heavy` for 100% of spatial coordinates.
3. **Credible Interval Ordering**: `lower <= central <= upper` universally verified.
4. **Binary Target Conformance**: Observed targets are strictly binary in (0, 1).
5. **Zero Data Leakage**: No validation dates or observations were used to construct calibration distributions.

---

## 5. Important Disclosures & Limitations

> [!IMPORTANT]
> **Operational Context Disclosure**:
> These fixture-derived metrics are engineering validation results and must not be presented as operational forecast skill.
> In this 30-day synthetic monsoon test fixture, the 8-day validation window contains 6 very heavy events, which limits statistical power for extreme tails. The code is production-ready to ingest full 2021–2023 JJAS multi-season operational datasets once Track A data ingestion is active.
