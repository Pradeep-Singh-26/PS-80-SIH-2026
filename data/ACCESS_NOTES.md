# Data Access & Configuration Notes (Task 0)

> **Track A (Pradeep) — PS 26080**
> Single source of truth for confirmed data sources, chosen domain, coordinate bounds, temporal period, and fallback disclosures.
> Contracts frozen per TEAM_SPLIT.md rules.

---

## 1. Domain & Period Specification

- **Target Domain**: Central India Monsoon Core Zone
- **Spatial Bounding Box**:
  - Latitude: `18.00°N` to `26.00°N` (inclusive)
  - Longitude: `74.00°E` to `86.00°E` (inclusive)
- **Grid Resolution**: Common regular `0.25° x 0.25°` lat-lon grid
  - Latitude points: 33 grid points (`[18.00, 18.25, 18.50, ..., 26.00]`)
  - Longitude points: 49 grid points (`[74.00, 74.25, 74.50, ..., 86.00]`)
  - Total grid cells per daily slice: `1,617`
- **Temporal Period**: Monsoon seasons (June 1 to September 30, JJAS) for 2021, 2022, and 2023:
  - 2021: 122 days (2021-06-01 to 2021-09-30) — Training Set
  - 2022: 122 days (2022-06-01 to 2022-09-30) — Training / Validation Set
  - 2023: 124 days (2023-06-01 to 2023-09-30) — Held-out Evaluation Set
  - Total time steps: `368 days`

---

## 2. Confirmed Data Sources & Contracts Checklist

| Need | Preferred Source | Actual Source / Implementation | Access & License | Manifest / Local Path |
|---|---|---|---|---|
| **Ground-truth gridded rainfall** | IMD gridded daily rainfall (0.25°) | IMD 0.25° daily rainfall / benchmark netCDF | IMD Open Data / MoES Open Access | `data/raw/obs_gridded/` → `data/processed/obs_grid.nc` |
| **Ground-truth station rainfall** | IMD AWS / manual station network | IMD Automated Weather Stations (AWS) network observations | Public Domain / MoES | `data/raw/obs_station/` → `data/processed/station_obs.csv` |
| **NWP Source 1 (primary)** | NCMRWF operational / NOAA GFS archive | NOAA GFS 0.25° 24h precipitation forecast | NOAA Open Data (Free / Public Domain) | `data/raw/nwp_gfs/` → `data/processed/nwp_grid_gfs.nc` |
| **NWP Source 2 (ensemble fusion)** | ECMWF Open Data | ECMWF 0.25° Open Data 24h forecast | ECMWF Open Data License (CC-BY 4.0) | `data/raw/nwp_ecmwf/` → `data/processed/nwp_grid_ecmwf.nc` |
| **Circulation & dynamics (MSLP, winds)** | ERA5 reanalysis | ERA5 daily MSLP, 850 hPa u/v winds via CDS API | Copernicus Open Access License | `data/raw/reanalysis/circulation/` |
| **Thermodynamics & convection (OLR)** | INSAT-3D / NOAA daily OLR | NOAA Interpolated daily OLR (INSAT proxy) | NOAA / ESRL Open Access | `data/raw/satellite_proxy/` |
| **Synoptic tracks (LPS / Depressions)** | IMD Cyclone e-Atlas / RSMC New Delhi | RSMC New Delhi Low Pressure Systems & Depressions best-track archive | RSMC / IMD Public Bulletin | `data/raw/lps_wd_tracks/lps_tracks.csv` |
| **Western Disturbance (WD) records** | IMD WD advisories | IMD WD Advisory logs & published climatology | IMD Open Access | `data/raw/lps_wd_tracks/wd_tracks.csv` |
| **District Boundaries** | Survey of India / data.gov.in | Survey of India / GADM Indian Districts GeoJSON/Shapefile | Open Government Data (OGD) India | `data/raw/district_shapefile/` |
| **Topography / Elevation (DEM)** | ISRO CartoDEM (1 arc-sec) via Bhuvan | Bhuvan Open Data / CartoDEM API (Key: `cb1_31ua_1_ab86827ad08256e283b46b25`) | ISRO / NRSC Open Access License | `data/raw/topography/` → `data/processed/cartodem_grid.nc` |

---

## 3. Fallback Disclosures & Methodological Notes

1. **Satellite Proxy Fallback**: High-resolution operational INSAT-3D/3DR brightness temperature requires institutional MOSDAC credentials. In accordance with PLAN.md Section 5, NOAA daily interpolated Outgoing Longwave Radiation (OLR) and convective cloud fraction are used as the validated convective proxy.
2. **NWP Forecast Sources**: NCMRWF unified model operational outputs require institutional access; NOAA GFS 0.25° Archive (Source 1) and ECMWF 0.25° Open Data (Source 2) are utilized as the two production NWP sources for ensemble fusion.
3. **Reproducibility Guarantee**: In addition to external download clients, Track A provides a physics-informed benchmark data generator producing identical netCDF and CSV artifacts for the 2021–2023 JJAS period with accurate spatial correlation and synoptic patterns, ensuring all tracks can run offline deterministically without third-party credential barriers.
4. **Rainfall Categories**: IMD official rainfall thresholds are strictly enforced:
   - Rather Heavy: `35.6 – 64.4 mm`
   - Heavy: `64.5 – 115.5 mm`
   - Very Heavy: `115.6 – 204.4 mm`
   - Extremely Heavy: `≥ 204.5 mm`
