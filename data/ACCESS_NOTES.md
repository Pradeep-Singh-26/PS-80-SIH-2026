# Data Access & Configuration Notes (Task 0)

> This document records confirmed data access, chosen domain, and monsoon season.
> To be finalized by Track A (Pradeep) before modeling tracks begin.

## 1. Domain & Period
- **Domain**: Central India Monsoon Core Zone (Lat: 18°N - 26°N, Lon: 74°E - 86°E) *(subject to confirmation)*
- **Temporal Period**: Monsoon seasons (June 1 – September 30), representative seasons (e.g. 2021–2023)
- **Grid Resolution**: 0.25° x 0.25° common regular lat-lon grid

## 2. Data Sources Checklist

| Need | Preferred Source | Actual Source Used / Fallback | Access Status | Local Path / Manifest |
|---|---|---|---|---|
| Ground-truth rainfall | IMD gridded rainfall (0.25°, daily) | IMD gridded / ERA5 precip proxy | Pending download | `data/raw/obs/` |
| Raw NWP forecast | NCMRWF/IMD operational NWP | NOAA GFS archive / ECMWF open data / ERA5 perfect-prog | Pending download | `data/raw/nwp/` |
| Circulation indicators (MSLP, OLR) | ERA5 reanalysis | ERA5 via cdsapi / NOAA OLR | Confirmed accessible via cdsapi | `data/raw/reanalysis/` |
| Low-pressure systems / depressions | IMD best-track archive | RSMC New Delhi cyclone/depression track data | Publicly accessible | `data/raw/lps_tracks/` |
| District boundaries | Survey of India / data.gov.in | Public GIS boundary GeoJSON/Shapefile | Publicly accessible | `data/raw/district_shapefile/` |

## 3. Fallback Disclosures
*(Document every proxy or fallback source used instead of the preferred MoES/IMD/NCMRWF operational feed, as required by PLAN.md Section 5 and README.md)*
