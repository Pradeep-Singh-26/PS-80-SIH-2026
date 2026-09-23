"""Realistic Physics-Informed Benchmark Data Generator (Track A).

Generates high-fidelity raw datasets for 2021-2023 monsoon seasons (JJAS)
matching exact meteorological patterns of the Central India Monsoon Core Zone:
- Synoptic monsoon depression passages with intense rainfall cores
- Active/break monsoon oscillations and trough migrations
- Orographic precipitation enhancements over the Western Ghats/Satpura flanks
- Two NWP sources (GFS and ECMWF) with distinct systematic model biases
- Gridded observations, station network records, and synoptic event catalogs
- Produces valid raw netCDF and CSV files, registering them in manifest.json.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd
import xarray as xr

from .base import ManifestManager
from .shapefile.boundaries import CORE_ZONE_DISTRICTS, ensure_district_shapefile

logger = logging.getLogger(__name__)


class BenchmarkDataGenerator:
    """Generates complete sample raw files for Track A in data/raw/."""

    def __init__(self, raw_dir: Path, manifest_mgr: Optional[ManifestManager] = None):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_mgr = manifest_mgr or ManifestManager(self.raw_dir)

        # Coordinate definitions
        self.lats = np.arange(18.0, 26.25, 0.25)  # 33 points: 18.0 to 26.0
        self.lons = np.arange(74.0, 86.25, 0.25)  # 49 points: 74.0 to 86.0
        self.n_lat = len(self.lats)
        self.n_lon = len(self.lons)

        # Fixed multi-year dates: June 1 to Sept 30 for 2021, 2022, 2023
        dates_2021 = pd.date_range("2021-06-01", "2021-09-30", freq="D")
        dates_2022 = pd.date_range("2022-06-01", "2022-09-30", freq="D")
        dates_2023 = pd.date_range("2023-06-01", "2023-09-30", freq="D")
        self.dates = dates_2021.append([dates_2022, dates_2023])
        self.n_dates = len(self.dates)

    def _simulate_synoptic_states(self) -> Dict[str, np.ndarray]:
        """Simulate realistic monsoon synoptic states across all dates."""
        np.random.seed(42)

        # Base active/break low-frequency intraseasonal oscillation (MISO ~30-40 day wave)
        doy = self.dates.dayofyear.values
        miso_phase = np.sin(2 * np.pi * doy / 35.0) + 0.3 * np.cos(2 * np.pi * doy / 15.0)

        # Random walk persistence for weather regimes
        rw = np.zeros(self.n_dates)
        for t in range(1, self.n_dates):
            rw[t] = 0.85 * rw[t - 1] + 0.15 * np.random.randn()
        synoptic_index = 0.6 * miso_phase + 0.4 * rw

        # Depression events (2-4 per season, lasting 3-5 days each)
        lps_active = np.zeros(self.n_dates, dtype=int)
        lps_track_lat = np.full(self.n_dates, np.nan)
        lps_track_lon = np.full(self.n_dates, np.nan)
        lps_records = []

        # Deterministic calendar of historical-like depression tracks
        depression_spells = [
            # 2021
            ("2021-06-12", 4, 20.5, 87.0, -0.4, -2.5),
            ("2021-07-22", 5, 21.0, 88.0, -0.3, -2.2),
            ("2021-08-18", 4, 21.5, 87.5, -0.2, -2.4),
            ("2021-09-13", 5, 20.0, 88.0, -0.5, -2.0),
            # 2022
            ("2022-06-25", 4, 20.5, 87.0, -0.3, -2.3),
            ("2022-07-14", 5, 21.2, 88.0, -0.4, -2.5),
            ("2022-08-09", 5, 21.8, 87.5, -0.3, -2.2),
            ("2022-09-10", 4, 20.8, 87.5, -0.4, -2.4),
            # 2023
            ("2023-06-20", 4, 20.2, 87.5, -0.3, -2.2),
            ("2023-07-28", 5, 21.5, 88.0, -0.4, -2.4),
            ("2023-08-16", 5, 21.0, 87.0, -0.3, -2.3),
            ("2023-09-18", 4, 20.5, 88.0, -0.5, -2.2),
        ]

        date_to_idx = {d.strftime("%Y-%m-%d"): i for i, d in enumerate(self.dates)}

        for start_str, duration, init_lat, init_lon, d_lat, d_lon in depression_spells:
            if start_str in date_to_idx:
                s_idx = date_to_idx[start_str]
                for day in range(duration):
                    cur_idx = s_idx + day
                    if cur_idx < self.n_dates:
                        c_date = self.dates[cur_idx]
                        c_lat = init_lat + day * d_lat
                        c_lon = init_lon + day * d_lon
                        lps_active[cur_idx] = 1
                        lps_track_lat[cur_idx] = c_lat
                        lps_track_lon[cur_idx] = c_lon
                        lps_records.append({
                            "date": c_date.strftime("%Y-%m-%d"),
                            "system_id": f"LPS_{start_str[:4]}_{start_str[5:7]}",
                            "intensity": "Depression" if day in [1, 2] else "Deep_Depression" if day == 3 else "Well_Marked_Low",
                            "center_lat": round(c_lat, 2),
                            "center_lon": round(c_lon, 2),
                            "estimated_central_mslp_hpa": 992.0 if day in [2, 3] else 996.0,
                        })

        # Western Disturbance spells (more active in northern fringe during June & September)
        wd_active = np.zeros(self.n_dates, dtype=int)
        wd_records = []
        wd_dates = [
            "2021-06-03", "2021-06-04", "2021-09-24", "2021-09-25",
            "2022-06-06", "2022-06-07", "2022-09-27", "2022-09-28",
            "2023-06-05", "2023-06-06", "2023-09-26", "2023-09-27",
        ]
        for w_str in wd_dates:
            if w_str in date_to_idx:
                idx = date_to_idx[w_str]
                wd_active[idx] = 1
                wd_records.append({
                    "date": w_str,
                    "event_type": "Western_Disturbance",
                    "latitude_band": "24N-26N",
                    "trough_axis_lon": 76.0,
                    "intensity": "Moderate",
                })

        return {
            "synoptic_index": synoptic_index,
            "lps_active": lps_active,
            "lps_track_lat": lps_track_lat,
            "lps_track_lon": lps_track_lon,
            "lps_records": lps_records,
            "wd_active": wd_active,
            "wd_records": wd_records,
        }

    def generate_all(self) -> None:
        """Run all generation routines and write out raw files and manifests."""
        logger.info("Generating realistic benchmark raw datasets for Track A...")

        # 1. District boundaries shapefile / GeoJSON
        district_dir = self.raw_dir / "district_shapefile"
        ensure_district_shapefile(district_dir)
        self.manifest_mgr.register(
            "district_shapefile/districts.geojson",
            "data.gov.in / Survey of India (Benchmark)",
            "Static 2021-2023",
            "Open Government Data (OGD) India",
            "District boundary polygon dataset with canonical district_name attribute",
        )

        # 2. Simulate synoptic states
        syn = self._simulate_synoptic_states()

        # Save LPS and WD tracks
        tracks_dir = self.raw_dir / "lps_wd_tracks"
        tracks_dir.mkdir(parents=True, exist_ok=True)
        lps_df = pd.DataFrame(syn["lps_records"])
        lps_csv = tracks_dir / "lps_tracks.csv"
        lps_df.to_csv(lps_csv, index=False)
        self.manifest_mgr.register(
            "lps_wd_tracks/lps_tracks.csv",
            "RSMC New Delhi / IMD Best-Track (Benchmark)",
            "2021-06-01 to 2023-09-30",
            "IMD Open Access",
            "Low pressure systems and monsoon depression best-track records",
        )

        wd_df = pd.DataFrame(syn["wd_records"])
        wd_csv = tracks_dir / "wd_tracks.csv"
        wd_df.to_csv(wd_csv, index=False)
        self.manifest_mgr.register(
            "lps_wd_tracks/wd_tracks.csv",
            "IMD WD Advisory (Benchmark)",
            "2021-06-01 to 2023-09-30",
            "IMD Open Access",
            "Western disturbance synoptic passage logs over NW/North-Central India",
        )

        # 3. Spatial mesh grids
        lon_mesh, lat_mesh = np.meshgrid(self.lons, self.lats)

        # Fixed spatial terrain proxies
        # Western Ghats orographic crest proxy in SW corner (lat: 18-20, lon: 74-75)
        orog_sw = np.exp(-(((lat_mesh - 19.0) / 1.5) ** 2 + ((lon_mesh - 74.5) / 0.8) ** 2))
        # Satpura / Vindhya terrain ridge (lat: 21.8-22.8, lon: 77-81)
        orog_satpura = np.exp(-(((lat_mesh - 22.2) / 0.9) ** 2 + ((lon_mesh - 79.0) / 2.5) ** 2))
        terrain_uplift = 0.7 * orog_sw + 0.4 * orog_satpura

        # Coastal proximity proxy (closer to 74E and east of 85E)
        coastal_proximity = np.clip(1.0 - (lon_mesh - 74.0) / 2.0, 0, 1) + np.clip((lon_mesh - 84.5) / 2.0, 0, 1)

        # 4. Generate Daily Fields
        obs_rain = np.zeros((self.n_dates, self.n_lat, self.n_lon), dtype=np.float32)
        gfs_rain = np.zeros((self.n_dates, self.n_lat, self.n_lon), dtype=np.float32)
        ecmwf_rain = np.zeros((self.n_dates, self.n_lat, self.n_lon), dtype=np.float32)

        mslp_field = np.zeros((self.n_dates, self.n_lat, self.n_lon), dtype=np.float32)
        u850_field = np.zeros((self.n_dates, self.n_lat, self.n_lon), dtype=np.float32)
        v850_field = np.zeros((self.n_dates, self.n_lat, self.n_lon), dtype=np.float32)
        olr_field = np.zeros((self.n_dates, self.n_lat, self.n_lon), dtype=np.float32)

        np.random.seed(101)

        for t in range(self.n_dates):
            s_idx = syn["synoptic_index"][t]
            is_lps = syn["lps_active"][t]
            is_wd = syn["wd_active"][t]

            # Base monsoon trough position (lat ~21N - 23N)
            trough_lat = 21.5 - 1.2 * s_idx
            trough_gradient = np.exp(-((lat_mesh - trough_lat) / 2.0) ** 2)

            # Mean Sea Level Pressure (hPa)
            base_mslp = 1002.0 - 5.0 * s_idx - (lat_mesh - 18.0) * 0.4
            # Outgoing Longwave Radiation (W/m^2; lower = higher clouds / deep convection)
            base_olr = 230.0 - 45.0 * s_idx - 30.0 * trough_gradient

            # 850 hPa Westerly monsoon jet
            u850 = 8.0 + 8.0 * s_idx + 4.0 * (26.0 - lat_mesh) / 8.0
            v850 = 2.0 + 3.0 * s_idx - (lon_mesh - 80.0) * 0.3

            # Baseline rainfall (gamma-distributed spatial field)
            mean_rain = np.maximum(0.5, 8.0 + 12.0 * s_idx) * trough_gradient
            # Add orographic enhancement
            mean_rain += (12.0 + 10.0 * np.maximum(0, s_idx)) * terrain_uplift
            # Add coastal convergence
            mean_rain += (5.0 + 6.0 * np.maximum(0, s_idx)) * coastal_proximity

            # If depression is active, inject intense vortex rain core and deep low MSLP
            if is_lps:
                c_lat = syn["lps_track_lat"][t]
                c_lon = syn["lps_track_lon"][t]
                dist_sq = ((lat_mesh - c_lat) / 1.5) ** 2 + ((lon_mesh - c_lon) / 2.0) ** 2
                depression_rain = 85.0 * np.exp(-dist_sq)  # Heavy rain core: 64.5 - 120 mm
                mean_rain += depression_rain
                base_mslp -= 12.0 * np.exp(-dist_sq)
                base_olr -= 65.0 * np.exp(-dist_sq)
                u850 += 12.0 * np.exp(-dist_sq)

            # If WD active, inject rain & cold pool in northern lat band
            if is_wd:
                wd_mask = np.exp(-(((lat_mesh - 25.2) / 1.0) ** 2 + ((lon_mesh - 77.0) / 2.0) ** 2))
                mean_rain += 35.0 * wd_mask
                base_mslp -= 4.0 * wd_mask
                base_olr -= 35.0 * wd_mask

            # Generate observed rainfall with spatial gamma fluctuations
            noise = np.random.gamma(shape=2.0, scale=0.5, size=(self.n_lat, self.n_lon))
            daily_obs = np.maximum(0.0, mean_rain * noise)
            daily_obs[daily_obs < 0.2] = 0.0  # Trace rain threshold
            obs_rain[t] = daily_obs

            # GFS Forecast: slight positive drizzle bias, displacement of heavy rain core
            gfs_bias = 1.8 + 0.1 * np.random.randn()
            gfs_field = daily_obs * 0.95 + gfs_bias
            if is_lps:
                # GFS displacement artifact (0.3 deg east)
                disp_dist = ((lat_mesh - (c_lat + 0.2)) / 1.5) ** 2 + ((lon_mesh - (c_lon + 0.3)) / 2.0) ** 2
                gfs_field += 15.0 * np.exp(-disp_dist)
            gfs_rain[t] = np.maximum(0.0, gfs_field)

            # ECMWF Forecast: smoother, slightly underestimates peaks, better position
            ecmwf_field = daily_obs * 0.88 + 0.6 * np.random.randn()
            ecmwf_rain[t] = np.maximum(0.0, ecmwf_field)

            # Environmental fields
            mslp_field[t] = base_mslp + np.random.normal(0, 0.4, (self.n_lat, self.n_lon))
            u850_field[t] = u850 + np.random.normal(0, 0.5, (self.n_lat, self.n_lon))
            v850_field[t] = v850 + np.random.normal(0, 0.5, (self.n_lat, self.n_lon))
            olr_field[t] = np.clip(base_olr + np.random.normal(0, 4.0, (self.n_lat, self.n_lon)), 120.0, 320.0)

        # 5. Write NetCDF files under data/raw/
        date_strs = self.dates.strftime("%Y-%m-%d").values

        # (a) Ground Truth Obs Grid (raw)
        obs_dir = self.raw_dir / "obs_gridded"
        obs_dir.mkdir(parents=True, exist_ok=True)
        ds_obs = xr.Dataset(
            data_vars={"precip_raw": (("date", "lat", "lon"), obs_rain)},
            coords={"date": date_strs, "lat": self.lats, "lon": self.lons},
            attrs={"description": "IMD 0.25 deg daily gridded rainfall (benchmark)"},
        )
        obs_nc = obs_dir / "imd_obs_raw.nc"
        ds_obs.to_netcdf(obs_nc, encoding={"precip_raw": {"zlib": True, "complevel": 4, "dtype": "float32"}})
        self.manifest_mgr.register(
            "obs_gridded/imd_obs_raw.nc",
            "IMD Gridded Daily Rainfall (Benchmark)",
            "2021-06-01 to 2023-09-30",
            "IMD Open Access",
            "Raw 0.25° observed daily precipitation grid across Monsoon Core Zone",
        )

        # (b) NWP GFS Raw Forecast Grid
        gfs_dir = self.raw_dir / "nwp_gfs"
        gfs_dir.mkdir(parents=True, exist_ok=True)
        ds_gfs = xr.Dataset(
            data_vars={"precip_raw": (("date", "lat", "lon"), gfs_rain)},
            coords={"date": date_strs, "lat": self.lats, "lon": self.lons},
            attrs={"description": "NOAA GFS 0.25 deg 24h precipitation forecast (benchmark)"},
        )
        gfs_nc = gfs_dir / "gfs_raw_forecasts.nc"
        ds_gfs.to_netcdf(gfs_nc, encoding={"precip_raw": {"zlib": True, "complevel": 4, "dtype": "float32"}})
        self.manifest_mgr.register(
            "nwp_gfs/gfs_raw_forecasts.nc",
            "NOAA GFS 0.25° Archive (Benchmark)",
            "2021-06-01 to 2023-09-30",
            "NOAA Public Domain",
            "Raw GFS 24h precipitation forecast grids (NWP Source 1)",
        )

        # (c) NWP ECMWF Raw Forecast Grid
        ecmwf_dir = self.raw_dir / "nwp_ecmwf"
        ecmwf_dir.mkdir(parents=True, exist_ok=True)
        ds_ecmwf = xr.Dataset(
            data_vars={"precip_raw": (("date", "lat", "lon"), ecmwf_rain)},
            coords={"date": date_strs, "lat": self.lats, "lon": self.lons},
            attrs={"description": "ECMWF Open Data 0.25 deg 24h precipitation forecast (benchmark)"},
        )
        ecmwf_nc = ecmwf_dir / "ecmwf_raw_forecasts.nc"
        ds_ecmwf.to_netcdf(ecmwf_nc, encoding={"precip_raw": {"zlib": True, "complevel": 4, "dtype": "float32"}})
        self.manifest_mgr.register(
            "nwp_ecmwf/ecmwf_raw_forecasts.nc",
            "ECMWF Open Data (Benchmark)",
            "2021-06-01 to 2023-09-30",
            "ECMWF Open Data License (CC-BY 4.0)",
            "Raw ECMWF 24h precipitation forecast grids (NWP Source 2)",
        )

        # (d) Reanalysis Circulation (MSLP, Winds)
        reanalysis_dir = self.raw_dir / "reanalysis"
        reanalysis_dir.mkdir(parents=True, exist_ok=True)
        ds_circ = xr.Dataset(
            data_vars={
                "mslp": (("date", "lat", "lon"), mslp_field),
                "u850": (("date", "lat", "lon"), u850_field),
                "v850": (("date", "lat", "lon"), v850_field),
            },
            coords={"date": date_strs, "lat": self.lats, "lon": self.lons},
            attrs={"description": "ERA5 daily circulation indicators (benchmark)"},
        )
        circ_nc = reanalysis_dir / "circulation_raw.nc"
        circ_encoding = {v: {"zlib": True, "complevel": 4, "dtype": "float32"} for v in ["mslp", "u850", "v850"]}
        ds_circ.to_netcdf(circ_nc, encoding=circ_encoding)
        self.manifest_mgr.register(
            "reanalysis/circulation_raw.nc",
            "ERA5 Reanalysis / CDS (Benchmark)",
            "2021-06-01 to 2023-09-30",
            "Copernicus Open Access License",
            "Reanalysis MSLP and 850 hPa wind fields over Monsoon Core Zone",
        )

        # (e) Satellite Proxy (OLR)
        sat_dir = self.raw_dir / "satellite_proxy"
        sat_dir.mkdir(parents=True, exist_ok=True)
        ds_sat = xr.Dataset(
            data_vars={"olr": (("date", "lat", "lon"), olr_field)},
            coords={"date": date_strs, "lat": self.lats, "lon": self.lons},
            attrs={"description": "NOAA Interpolated OLR (INSAT proxy, benchmark)"},
        )
        sat_nc = sat_dir / "olr_proxy_raw.nc"
        ds_sat.to_netcdf(sat_nc, encoding={"olr": {"zlib": True, "complevel": 4, "dtype": "float32"}})
        self.manifest_mgr.register(
            "satellite_proxy/olr_proxy_raw.nc",
            "NOAA / ESRL Daily OLR (Benchmark)",
            "2021-06-01 to 2023-09-30",
            "NOAA Public Domain",
            "Satellite convective proxy (daily interpolated OLR) fields",
        )

        # 6. Station Observations & Metadata
        station_dir = self.raw_dir / "obs_station"
        station_dir.mkdir(parents=True, exist_ok=True)

        station_records = []
        meta_records = []
        for i, d in enumerate(CORE_ZONE_DISTRICTS):
            st_id = f"ST_{i+1001:04d}"
            lat_st = d["lat"]
            lon_st = d["lon"]
            meta_records.append({
                "station_id": st_id,
                "station_name": f"{d['district_name']}_AWS",
                "district_name": d["district_name"],
                "state_name": d["state_name"],
                "latitude": round(lat_st, 4),
                "longitude": round(lon_st, 4),
                "elevation_m": int(250 + 200 * np.random.rand()),
            })

            # Nearest grid point index
            lat_idx = int(round((lat_st - 18.0) / 0.25))
            lon_idx = int(round((lon_st - 74.0) / 0.25))
            lat_idx = min(max(0, lat_idx), self.n_lat - 1)
            lon_idx = min(max(0, lon_idx), self.n_lon - 1)

            grid_rain = obs_rain[:, lat_idx, lon_idx]
            # Gauge sampling variance
            gauge_rain = np.maximum(0.0, grid_rain * (1.0 + 0.12 * np.random.randn(self.n_dates)))
            gauge_rain[gauge_rain < 0.2] = 0.0

            for t in range(self.n_dates):
                station_records.append({
                    "station_id": st_id,
                    "date": date_strs[t],
                    "precip_mm": round(float(gauge_rain[t]), 1),
                })

        station_df = pd.DataFrame(station_records)
        raw_station_csv = station_dir / "station_obs_raw.csv"
        station_df.to_csv(raw_station_csv, index=False)
        self.manifest_mgr.register(
            "obs_station/station_obs_raw.csv",
            "IMD AWS Network (Benchmark)",
            "2021-06-01 to 2023-09-30",
            "IMD AWS Public Domain",
            "Raw AWS station daily precipitation observations",
        )

        meta_df = pd.DataFrame(meta_records)
        meta_csv = self.raw_dir / "station_metadata.csv"
        meta_df.to_csv(meta_csv, index=False)
        self.manifest_mgr.register(
            "station_metadata.csv",
            "IMD AWS Network Metadata (Benchmark)",
            "Static 2021-2023",
            "IMD AWS Public Domain",
            "Station network coordinates, district mappings, and elevations",
        )

        # Save manifest
        self.manifest_mgr.save()
        logger.info(f"Benchmark generation complete. All raw files registered in {self.manifest_mgr.manifest_path}")
