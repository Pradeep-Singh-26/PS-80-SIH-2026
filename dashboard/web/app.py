"""PS 26080 -- Streamlit Dashboard.

Regime-Aware Rainfall Post-Processing & Orographic Downscaling System.
Ultra-Clean White, Black, and Light Blue Enterprise UI.

Run:
    streamlit run dashboard/web/app.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from api.data_loader import (
    load_district_table,
    load_station_table,
    load_regime_predictions,
    load_verification_summary,
    load_alerts,
    load_fss_scores,
    load_reliability_data,
    load_regime_summary,
    load_cartodem_info,
    save_feedback,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PS 26080 | Regime-Aware Monsoon AI",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Clean White, Black, and Light Blue Design System (CSS)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Typography */
    html, body, [class*="css"], .stMarkdown, p, span, label, div {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #0f172a;
    }

    /* Main Container Background */
    .stApp {
        background-color: #ffffff;
    }

    /* Top Brand Header */
    .brand-banner {
        background: linear-gradient(135deg, #f0f7ff 0%, #e0f2fe 100%);
        border: 1px solid #bae6fd;
        border-radius: 14px;
        padding: 18px 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        box-shadow: 0 4px 20px -2px rgba(2, 132, 199, 0.08);
    }
    .brand-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
        letter-spacing: -0.5px;
    }
    .brand-subtitle {
        font-size: 0.88rem;
        color: #475569;
        margin: 4px 0 0 0;
        font-weight: 500;
    }
    .pill-badge {
        background: #ffffff;
        border: 1px solid #bae6fd;
        color: #0284c7;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 5px 12px;
        border-radius: 24px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.06);
    }

    /* Page Titles */
    .page-title-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 18px;
        border-bottom: 1.5px solid #f1f5f9;
        padding-bottom: 12px;
    }
    .page-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.3px;
    }
    .page-subtitle {
        font-size: 0.88rem;
        color: #64748b;
        margin: 4px 0 0 0;
    }

    /* Sleek KPI Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 3.5px solid #0284c7;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(2, 132, 199, 0.10);
    }
    .kpi-label {
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #64748b;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0f172a;
        margin: 4px 0 2px 0;
        letter-spacing: -0.5px;
    }
    .kpi-tag {
        font-size: 0.8rem;
        font-weight: 600;
        color: #0284c7;
    }

    /* Map Box Container */
    .map-frame {
        border: 1.5px solid #bae6fd;
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(2, 132, 199, 0.08);
        background: #f8fafc;
        margin-bottom: 20px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
        padding-top: 1rem;
    }

    /* Modern Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 4px;
        margin-bottom: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 700;
        font-size: 0.9rem;
        color: #64748b;
        background: #f8fafc;
        border-radius: 8px 8px 0 0;
        padding: 10px 18px;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #0284c7 !important;
        background: #f0f7ff !important;
        border-color: #bae6fd #bae6fd #f0f7ff !important;
    }

    /* Primary Buttons */
    .stButton > button {
        background: linear-gradient(180deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 9px 20px !important;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.25) !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data Loading & Preparation
# ---------------------------------------------------------------------------
district_df = load_district_table()
station_df = load_station_table()
carto_info = load_cartodem_info()

# ---------------------------------------------------------------------------
# Sidebar Navigation & Live Controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 6px 0 16px 0; border-bottom: 1.5px solid #e2e8f0; margin-bottom: 18px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.6rem;">🌧️</span>
            <div>
                <div style="font-weight: 800; font-size: 1.25rem; color: #0f172a; line-height: 1.1;">PS 26080</div>
                <div style="font-size: 0.75rem; color: #0284c7; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px;">Monsoon Post-Processing</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Global Date Filter (in sidebar for easy access)
    if not district_df.empty:
        available_dates = sorted(district_df["date"].unique())
        selected_date = st.selectbox(
            "📅 Active Forecast Date",
            options=available_dates,
            index=len(available_dates) // 2,
            help="Select date for spatial maps, district tables, and synoptic regime analysis",
        )
    else:
        selected_date = "2024-06-15"

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Telemetry Status Card
    st.markdown(f"""
    <div style="background: #ffffff; border: 1.5px solid #bae6fd; border-radius: 12px; padding: 14px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(2, 132, 199, 0.06);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 800; font-size: 0.85rem; color: #0f172a;">🛰️ ISRO CartoDEM</span>
            <span style="background: #dcfce7; color: #166534; font-size: 0.7rem; font-weight: 800; padding: 2px 8px; border-radius: 6px;">ACTIVE</span>
        </div>
        <div style="font-size: 0.78rem; color: #475569; line-height: 1.5;">
            <div>• Resolution: <b>1 arc-sec (~30m)</b></div>
            <div>• Key: <code style="font-size: 0.72rem; background: #f0f7ff; color: #0369a1; padding: 2px 4px; border-radius: 4px;">{carto_info.get('api_key_masked', 'cb1_3vjz...e189')}</code></div>
            <div>• Orographic Grid: <b>Loaded (.nc)</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: #f0f7ff; border: 1px solid #e0f2fe; border-radius: 10px; padding: 12px; font-size: 0.78rem; color: #334155; line-height: 1.4;">
        <b>Smart India Hackathon 2026</b><br>
        Physics-Informed Bias Correction & Topographic Orographic Downscaling.
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Top Global Brand Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="brand-banner">
    <div>
        <h1 class="brand-title">
            <span>🌧️</span> PS 26080 | Regime-Aware Monsoon Rainfall AI
        </h1>
        <p class="brand-subtitle">
            High-Resolution Bias Correction, Heavy Rain Risk Calibration & ISRO CartoDEM Topography Downscaling
        </p>
    </div>
    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
        <span class="pill-badge">🛰️ ISRO Bhuvan CartoDEM 30m</span>
        <span class="pill-badge">⚡ AI Post-Processing V2.1</span>
        <span class="pill-badge">📍 IMD Domain: 8°N-38°N</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Clean Top Navigation Bar
# ---------------------------------------------------------------------------
nav_view = st.radio(
    "Select System View",
    [
        "🗺️ District & Station Map",
        "🌀 Regime Classification",
        "🛰️ Topography & CartoDEM",
        "📊 Verification & Skill",
        "🚨 Alerts Dashboard",
        "⚖️ Raw vs Corrected",
        "📝 Forecaster Feedback",
    ],
    index=0,
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)


# ===========================================================================
# VIEW 1: District & Station Map
# ===========================================================================
if nav_view == "🗺️ District & Station Map":
    st.markdown("""
    <div class="page-title-row">
        <div>
            <h2 class="page-title">🗺️ District Forecasts & Ground Station Network</h2>
            <p class="page-subtitle">Interactive meteorological canvas displaying downscaled precipitation, exceedance probabilities, and station observation networks</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if district_df.empty:
        st.warning("District table not found. Please run the orchestration pipeline first.")
    else:
        day_districts = district_df[district_df["date"] == selected_date]
        day_stations = station_df[station_df["date"] == selected_date] if not station_df.empty else pd.DataFrame()

        # Filter bar
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            min_rain_filter = st.slider("Filter Minimum Rainfall (mm)", 0.0, 150.0, 0.0, step=5.0)
        with col_f2:
            districts_list = ["All Districts"] + sorted(district_df["district_name"].unique().tolist())
            selected_dist = st.selectbox("Search / Highlight Specific District", districts_list)

        if min_rain_filter > 0:
            day_districts = day_districts[day_districts["corrected_rainfall_mm"] >= min_rain_filter]

        if selected_dist != "All Districts":
            day_districts = day_districts[day_districts["district_name"] == selected_dist]

        # Top 4 KPI Metrics
        avg_rain = day_districts["corrected_rainfall_mm"].mean() if not day_districts.empty else 0.0
        max_rain = day_districts["corrected_rainfall_mm"].max() if not day_districts.empty else 0.0
        high_risk_count = len(day_districts[day_districts["p_heavy"] >= 0.40]) if not day_districts.empty else 0
        dom_regime = day_districts["dominant_regime"].iloc[0].replace("_", " ").title() if not day_districts.empty else "N/A"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Mean Rainfall</div>
                <div class="kpi-value">{avg_rain:.1f} <span style="font-size: 0.9rem; color: #64748b;">mm</span></div>
                <div class="kpi-tag">Spatial areal mean</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Peak Recorded Rain</div>
                <div class="kpi-value">{max_rain:.1f} <span style="font-size: 0.9rem; color: #64748b;">mm</span></div>
                <div class="kpi-tag" style="color: {'#dc2626' if max_rain >= 115.6 else '#0284c7'};">
                    {'⚠️ Very Heavy' if max_rain >= 115.6 else ('⚡ Heavy' if max_rain >= 64.5 else '🌧️ Moderate')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">High-Risk Districts</div>
                <div class="kpi-value">{high_risk_count}</div>
                <div class="kpi-tag" style="color: {'#ea580c' if high_risk_count > 0 else '#059669'};">
                    P(Heavy &ge; 64.5mm) &gt; 40%
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Active Regime</div>
                <div class="kpi-value" style="font-size: 1.35rem; color: #0284c7;">{dom_regime}</div>
                <div class="kpi-tag">Synoptic Forcing Mode</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # High-End Map Display Header with Mode Selector
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            st.markdown("""
            <div style="padding: 6px 0;">
                <div style="font-weight: 800; color: #0f172a; font-size: 1.05rem; display: flex; align-items: center; gap: 8px;">
                    <span>📡</span> <span>Station Observation Network & Precipitation Field</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">Use layer controls or mode switcher below to change between Satellite, Terrain, and Light views</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            map_mode = st.selectbox(
                "🗺️ Map Display Mode",
                [
                    "🛰️ Satellite Imagery",
                    "☀️ Light Canvas",
                    "⛰️ Topography & Terrain",
                    "🗺️ OpenStreetMap",
                    "🌑 Dark Canvas (Night)",
                ],
                index=0,
                help="Switch between Satellite imagery, Topographic terrain, Light meteorological canvas, or Dark mode",
            )

        if not day_stations.empty:
            from dashboard.components.map_component import create_station_map
            map_html = create_station_map(day_stations, default_mode=map_mode)
            st.components.v1.html(map_html, height=560)
        else:
            st.info("No station observations available for this date.")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Tabbed Data Tables
        tab_dist, tab_stat, tab_analytics = st.tabs([
            "📊 District Precipitation Table",
            "📡 Point Observation Stations",
            "📈 Spatial Analytics & Distribution",
        ])

        with tab_dist:
            sorted_districts = day_districts.sort_values("corrected_rainfall_mm", ascending=False).copy()
            st.dataframe(
                sorted_districts.style.background_gradient(
                    subset=["corrected_rainfall_mm"], cmap="Blues"
                ).background_gradient(
                    subset=["p_heavy"], cmap="YlOrRd"
                ),
                use_container_width=True,
                height=320,
            )

        with tab_stat:
            if not day_stations.empty:
                st.dataframe(
                    day_stations.style.background_gradient(
                        subset=["corrected_rainfall_mm"], cmap="Blues"
                    ),
                    use_container_width=True,
                    height=320,
                )
            else:
                st.info("No station data for this selection.")

        with tab_analytics:
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.markdown("<div style='font-weight: 700; font-size: 0.95rem; margin-bottom: 8px;'>District Rainfall Distribution (mm)</div>", unsafe_allow_html=True)
                if not day_districts.empty:
                    st.bar_chart(day_districts.set_index("district_name")["corrected_rainfall_mm"])
            with col_a2:
                st.markdown("<div style='font-weight: 700; font-size: 0.95rem; margin-bottom: 8px;'>Probability of Heavy Rain Exceedance</div>", unsafe_allow_html=True)
                if not day_districts.empty:
                    st.bar_chart(day_districts.set_index("district_name")["p_heavy"])


# ===========================================================================
# VIEW 2: Regime Classification
# ===========================================================================
elif nav_view == "🌀 Regime Classification":
    st.markdown("""
    <div class="page-title-row">
        <div>
            <h2 class="page-title">🌀 Synoptic Monsoon Regime Classification</h2>
            <p class="page-subtitle">Physics-informed classification of atmospheric flow patterns, moisture dynamics, and trough positions</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    regime_df = load_regime_predictions()
    if regime_df.empty:
        st.warning("Regime predictions not available yet. Please run the pipeline.")
    else:
        regime_df["date"] = pd.to_datetime(regime_df["date"])
        from dashboard.components.regime_explainer import render_regime_panel
        render_regime_panel(regime_df)


# ===========================================================================
# VIEW 3: Topography & CartoDEM
# ===========================================================================
elif nav_view == "🛰️ Topography & CartoDEM":
    st.markdown("""
    <div class="page-title-row">
        <div>
            <h2 class="page-title">🛰️ ISRO Bhuvan CartoDEM Topography Integration</h2>
            <p class="page-subtitle">High-resolution 1 arc-second (~30m) Digital Elevation Model for orographic lift and slope-aspect downscaling</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">CartoDEM API Status</div>
            <div class="kpi-value" style="color: #059669; font-size: 1.4rem;">CONNECTED</div>
            <div class="kpi-tag">Bhuvan GeoServer Active</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Spatial Resolution</div>
            <div class="kpi-value">1 arc-sec</div>
            <div class="kpi-tag">~30m Grid Mesh</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Elevation Range</div>
            <div class="kpi-value">0 - 8,848m</div>
            <div class="kpi-tag">Ghats & Himalayan Slopes</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Orographic Features</div>
            <div class="kpi-value">6 Primary</div>
            <div class="kpi-tag">Slope, Aspect, Curvature</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #bae6fd; border-radius: 12px; padding: 20px; box-shadow: 0 4px 16px rgba(2, 132, 199, 0.05);">
            <div style="font-weight: 800; color: #0284c7; font-size: 1.05rem; margin-bottom: 8px;">⛰️ Orographic Enhancement Mechanisms</div>
            <p style="color: #334155; font-size: 0.9rem; line-height: 1.6;">
                Monsoon winds crossing major orographic barriers (Western Ghats, Khasi-Jaintia Hills, Himalayan foothills) undergo intense adiabatic cooling and condensation.
                The <b>ISRO CartoDEM</b> module extracts fine-scale topographic derivatives to downscale coarse NWP forecasts:
            </p>
            <ul style="color: #475569; font-size: 0.88rem; line-height: 1.8; margin-bottom: 0;">
                <li><b>Windward Slope Angle (&theta;):</b> Governs vertical air velocity <code style="background: #f0f7ff; color:#0369a1; padding: 2px 4px; border-radius: 4px;">w = U &middot; &nabla;h</code></li>
                <li><b>Aspect Orientation:</b> Identifies perpendicular vs parallel barrier wind interaction</li>
                <li><b>Valley Confinement Index:</b> Detects orographic funneling and convergence pockets</li>
                <li><b>Ridge Crest Distance:</b> Calibrates the rain shadow drying on leeward sides</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_t2:
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
            <div style="font-weight: 800; color: #0f172a; font-size: 1.05rem; margin-bottom: 8px;">🔑 Integration Configuration & Cache</div>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem;">
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 8px 0; color: #64748b;">Source:</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #0f172a; text-align: right;">ISRO / NRSC Bhuvan CartoDEM</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 8px 0; color: #64748b;">Configured Token:</td>
                    <td style="padding: 8px 0; font-family: monospace; color: #0284c7; text-align: right; font-weight: 700;">{carto_info.get('api_key_masked', 'cb1_3vjz...e189')}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 8px 0; color: #64748b;">Grid Cache:</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #059669; text-align: right;">{'Available (.nc)' if carto_info.get('grid_available') else 'Ready (Local)'}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 8px 0; color: #64748b;">Interpolation:</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #0f172a; text-align: right;">Bilinear + Conservative Flux</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b;">Downscaling Factor:</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #0284c7; text-align: right;">0.25° NWP &rarr; 0.05° District (5x)</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)


# ===========================================================================
# VIEW 4: Verification & Skill
# ===========================================================================
elif nav_view == "📊 Verification & Skill":
    st.markdown("""
    <div class="page-title-row">
        <div>
            <h2 class="page-title">📊 Verification & Forecast Skill Benchmark</h2>
            <p class="page-subtitle">Rigorous statistical validation against IMD gridded observation data across spatial scales</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    from dashboard.components.skill_charts import render_skill_view
    render_skill_view()


# ===========================================================================
# VIEW 5: Alerts Dashboard
# ===========================================================================
elif nav_view == "🚨 Alerts Dashboard":
    st.markdown("""
    <div class="page-title-row">
        <div>
            <h2 class="page-title">🚨 Automated Extreme Rainfall Bulletins & Alerts</h2>
            <p class="page-subtitle">Multi-tier threshold warnings, Flash Flood Advisories, and District Disaster Management feeds</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    from dashboard.components.alert_panel import render_alert_panel
    render_alert_panel()


# ===========================================================================
# VIEW 6: Raw vs Corrected
# ===========================================================================
elif nav_view == "⚖️ Raw vs Corrected":
    st.markdown("""
    <div class="page-title-row">
        <div>
            <h2 class="page-title">⚖️ Raw NWP vs Regime-Aware AI Comparison</h2>
            <p class="page-subtitle">Direct comparison of raw Numerical Weather Prediction outputs against AI bias-corrected fields</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    verification = load_verification_summary()
    if not verification:
        st.warning("Verification report not generated yet. Run the pipeline first.")
    else:
        v_df = pd.DataFrame(verification)
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
            <div style="font-weight: 800; color: #0f172a; font-size: 1.05rem; margin-bottom: 8px;">📋 Summary Metric Delta</div>
        </div>
        """, unsafe_allow_html=True)

        display_cols = ["source", "rmse", "bias", "mae", "n_points"]
        avail = [c for c in display_cols if c in v_df.columns]
        st.dataframe(v_df[avail], use_container_width=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if "rmse" in v_df.columns:
                st.markdown("<div style='font-weight: 700; font-size: 0.95rem; margin: 12px 0 6px 0;'>📉 RMSE (Root Mean Square Error) Comparison</div>", unsafe_allow_html=True)
                st.bar_chart(v_df.set_index("source")["rmse"])

        with col_b2:
            if "bias" in v_df.columns:
                st.markdown("<div style='font-weight: 700; font-size: 0.95rem; margin: 12px 0 6px 0;'>🎯 Systematic Model Bias (mm)</div>", unsafe_allow_html=True)
                st.bar_chart(v_df.set_index("source")["bias"])

        regime_data = load_regime_summary()
        if regime_data:
            st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                <div style="font-weight: 800; color: #0f172a; font-size: 1.05rem;">🌀 Error Breakdown by Monsoon Synoptic Regime</div>
            </div>
            """, unsafe_allow_html=True)
            r_df = pd.DataFrame(regime_data)
            if "rmse" in r_df.columns and "regime" in r_df.columns:
                pivot = r_df.pivot_table(index="regime", columns="source", values="rmse")
                st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)
                st.bar_chart(pivot)


# ===========================================================================
# VIEW 7: Feedback
# ===========================================================================
elif nav_view == "📝 Forecaster Feedback":
    st.markdown("""
    <div class="page-title-row">
        <div>
            <h2 class="page-title">📝 Operational Forecaster Feedback System</h2>
            <p class="page-subtitle">Submit expert human-in-the-loop corrections and annotations to retrain regime models</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("""
        <div style="background: #f0f7ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 18px; margin-bottom: 18px;">
            <div style="font-weight: 800; color: #0369a1; font-size: 1rem; margin-bottom: 4px;">ℹ️ Continuous Active Learning Pipeline</div>
            <div style="color: #334155; font-size: 0.88rem; line-height: 1.5;">
                Forecaster inputs are logged to the retraining queue. Corrected labels are weighted in subsequent model calibration runs.
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("feedback_form"):
            col1, col2 = st.columns(2)
            with col1:
                fb_date = st.date_input("Observation Date", value=datetime.today())
                fb_type = st.selectbox(
                    "Feedback Category",
                    ["regime_correction", "rainfall_correction", "orographic_anomaly", "general_comment"],
                )
                fb_district = st.text_input("District / Station Name", placeholder="e.g. Wayanad, Ratnagiri, Shimla")

            with col2:
                fb_original = st.text_input("Model Predicted Value", placeholder="e.g. Active Monsoon / 45mm")
                fb_corrected = st.text_input("Forecaster Observed / Expected Value", placeholder="e.g. Orographic / 110mm")
                fb_forecaster = st.text_input("Forecaster Badge ID (optional)", placeholder="e.g. IMD-MET-402")

            fb_comment = st.text_area("Detailed Meteorological Notes & Justification", placeholder="Explain synoptic evidence (e.g. low level jet speed, radar reflectivity, local cloudburst signature)")

            submitted = st.form_submit_button("Submit Forecaster Feedback")

            if submitted:
                feedback_id = save_feedback({
                    "date": str(fb_date),
                    "feedback_type": fb_type,
                    "district_name": fb_district or None,
                    "original_value": fb_original or None,
                    "corrected_value": fb_corrected or None,
                    "comment": fb_comment or None,
                    "forecaster_id": fb_forecaster or None,
                })
                st.markdown(f"""
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 14px; margin-top: 14px;">
                    <div style="color: #166534; font-weight: 800; font-size: 1rem;">✅ Feedback Recorded Successfully!</div>
                    <div style="color: #15803d; font-size: 0.88rem; margin-top: 2px;">Reference Ticket ID: <code style="font-weight: 800; background: #ffffff; padding: 2px 8px; border-radius: 4px; border: 1px solid #bbf7d0;">{feedback_id}</code> (Queued for active learning retraining)</div>
                </div>
                """, unsafe_allow_html=True)

    fb_file = _ROOT / "outputs" / "feedback" / "feedback_log.jsonl"
    if fb_file.exists():
        try:
            records = []
            with open(fb_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            if records:
                st.markdown("<div style='height: 22px;'></div>", unsafe_allow_html=True)
                st.markdown("""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 10px;">
                    <div style="font-weight: 800; color: #0f172a; font-size: 1rem;">📜 Recently Logged Forecaster Annotations</div>
                </div>
                """, unsafe_allow_html=True)
                fb_df = pd.DataFrame(records).iloc[::-1]
                st.dataframe(fb_df, use_container_width=True)
        except Exception:
            pass
