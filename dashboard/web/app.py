"""RainCore -- Streamlit Dashboard.

Regime-Aware Rainfall Post-Processing & Orographic Downscaling System.
High-Resolution Weather Intelligence Platform.

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
    _invalidate_cache,
)
from dashboard.components.guide_component import render_guide_view, render_page_help_banner

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RainCore | Monsoon Intelligence & Orographic AI",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design System & Modern Top Navbar CSS
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

    /* =======================================================================
       RAINCORE PROPER TOP NAVBAR
       Sleek enterprise navigation bar placed at the top of the portal
       ======================================================================= */
    .raincore-navbar {
        background: linear-gradient(135deg, #f0f7ff 0%, #e0f2fe 100%);
        border: 1.5px solid #bae6fd;
        border-radius: 14px;
        padding: 14px 20px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        box-shadow: 0 4px 16px rgba(2, 132, 199, 0.07);
    }
    .raincore-brand-group {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .raincore-brand-icon {
        font-size: 2rem;
        line-height: 1;
    }
    .raincore-brand-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }
    .raincore-brand-subtitle {
        font-size: 0.82rem;
        color: #475569;
        margin: 2px 0 0 0;
        font-weight: 500;
    }
    .raincore-badge {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 6px;
        letter-spacing: 0.4px;
        display: inline-block;
        margin-left: 6px;
    }
    .pill-badge {
        background: #ffffff;
        border: 1px solid #bae6fd;
        color: #0284c7;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.05);
    }

    /* Segmented Control Navbar Container */
    div[data-testid="stSegmentedControl"] {
        background: #f8fafc !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 5px !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 16px !important;
    }
    div[data-testid="stSegmentedControl"] button {
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        padding: 9px 16px !important;
        color: #334155 !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stSegmentedControl"] button:hover {
        background: #ffffff !important;
        color: #0284c7 !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 3px 10px rgba(2, 132, 199, 0.3) !important;
    }

    /* Page Titles */
    .page-title-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
        border-bottom: 1.5px solid #f1f5f9;
        padding-bottom: 10px;
        flex-wrap: wrap;
        gap: 8px;
    }
    .page-title {
        font-size: 1.38rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.3px;
    }
    .page-subtitle {
        font-size: 0.86rem;
        color: #64748b;
        margin: 4px 0 0 0;
    }

    /* Active Filter Status Banner */
    .filter-status-banner {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 8px 14px;
        margin-bottom: 14px;
    }
    .filter-chip {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 3px 9px;
        font-size: 0.78rem;
        color: #0f172a;
        display: inline-flex;
        align-items: center;
        gap: 4px;
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

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1.5px solid #e2e8f0;
        padding-top: 0.8rem;
    }

    /* Sidebar Brand Card */
    .sidebar-brand-card {
        background: #ffffff;
        border: 1.5px solid #bae6fd;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.06);
    }
    .sidebar-brand-title {
        font-weight: 800;
        font-size: 1.35rem;
        color: #0f172a;
        margin: 4px 0 0 0;
        line-height: 1.1;
    }
    .sidebar-brand-subtitle {
        font-size: 0.76rem;
        color: #0284c7;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .sidebar-badge-row {
        display: flex;
        gap: 6px;
        margin-top: 8px;
        flex-wrap: wrap;
    }
    .sidebar-mini-badge {
        font-size: 0.7rem;
        font-weight: 700;
        background: #f0f7ff;
        color: #0369a1;
        border: 1px solid #bae6fd;
        border-radius: 4px;
        padding: 2px 6px;
    }

    /* Live Pulsing Dot */
    @keyframes pulse-emerald {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
        70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .pulse-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        animation: pulse-emerald 2s infinite;
        vertical-align: middle;
        margin-right: 4px;
    }
    .live-status-pill {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
        font-size: 0.7rem;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
    }

    /* Telemetry Card */
    .telemetry-card {
        background: #ffffff;
        border: 1.5px solid #bae6fd;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.05);
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
        padding: 8px 16px !important;
        font-size: 0.88rem !important;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.20) !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.30) !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Navigation Setup
# ---------------------------------------------------------------------------
NAV_OPTIONS = [
    "📖 How to Use & Guide",   # <-- Far-left option!
    "🗺️ District & Station Map",
    "🌀 Regime Classification",
    "🛰️ Topography & CartoDEM",
    "📊 Verification & Skill",
    "🚨 Alerts Dashboard",
    "⚖️ Raw vs Corrected",
    "📝 Forecaster Feedback",
]

# Track active navigation tab
if "raincore_active_tab" not in st.session_state:
    st.session_state["raincore_active_tab"] = "🗺️ District & Station Map"


def switch_to_view(view_name: str):
    """Programmatically switch system view and rerun."""
    if view_name in NAV_OPTIONS:
        st.session_state["raincore_active_tab"] = view_name
        st.session_state["raincore_segmented_nav"] = view_name
        st.rerun()


# ---------------------------------------------------------------------------
# Data Loading & Preparation
# ---------------------------------------------------------------------------
district_df = load_district_table()
station_df = load_station_table()
carto_info = load_cartodem_info()
alerts_list = load_alerts()


# ---------------------------------------------------------------------------
# Dedicated Sidebar Controls
# (All controls and parameters live exclusively on the sidebar)
# ---------------------------------------------------------------------------
with st.sidebar:
    # 1. RainCore Brand Card
    st.markdown("""
    <div class="sidebar-brand-card">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 1.7rem;">🌧️</span>
            <span class="live-status-pill"><span class="pulse-dot"></span> OPERATIONAL</span>
        </div>
        <div class="sidebar-brand-title">RainCore</div>
        <div class="sidebar-brand-subtitle">Regime-Aware Monsoon AI</div>
        <div class="sidebar-badge-row">
            <span class="sidebar-mini-badge">ISRO CartoDEM 30m</span>
            <span class="sidebar-mini-badge">MoES / IMD</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Collapsible Quick Guide in Sidebar
    with st.expander("🧭 Quick Guide & Workflow", expanded=False):
        st.markdown("""
        <div style="font-size: 0.8rem; color: #334155; line-height: 1.5;">
            <div style="font-weight: 800; color: #0284c7; margin-bottom: 6px;">⚡ Operational Protocol:</div>
            <div><b>1. Set Date:</b> Pick target forecast date below.</div>
            <div><b>2. Check Regime:</b> Inspect active synoptic circulation.</div>
            <div><b>3. Examine Map:</b> Spot high P(Heavy) exceedance districts.</div>
            <div><b>4. Review Alerts:</b> Generate civil defense bulletins.</div>
            <div style="border-top: 1px solid #e2e8f0; margin: 8px 0; padding-top: 6px;">
                <div style="font-weight: 800; color: #0284c7; margin-bottom: 4px;">🌧️ IMD Rainfall Scale:</div>
                <div><span style="color: #166534; font-weight: 700;">🟢 Light:</span> &lt; 15.6 mm</div>
                <div><span style="color: #0284c7; font-weight: 700;">🔵 Moderate:</span> 15.6 - 64.4 mm</div>
                <div><span style="color: #ea580c; font-weight: 700;">🟠 Heavy:</span> 64.5 - 115.5 mm</div>
                <div><span style="color: #dc2626; font-weight: 700;">🔴 Very Heavy:</span> &ge; 115.6 mm</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📖 Open Full Guide", key="sidebar_full_guide_btn", use_container_width=True):
            switch_to_view("📖 How to Use & Guide")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 3. Forecast Control Options (Sidebar exclusive)
    st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;'>Forecast Parameters</div>", unsafe_allow_html=True)

    # Date selector
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

    # Minimum rainfall filter slider
    sidebar_min_rain = st.slider(
        "💧 Min Rainfall Filter (mm)",
        min_value=0.0,
        max_value=150.0,
        value=0.0,
        step=5.0,
        help="Filter districts and map records by minimum downscaled rainfall",
    )

    # Quick District Search
    if not district_df.empty:
        all_districts = ["All Districts"] + sorted(district_df["district_name"].unique().tolist())
        sidebar_district = st.selectbox(
            "🔍 District Scope & Search",
            options=all_districts,
            index=0,
            help="Highlight or filter down to a specific district",
        )
    else:
        sidebar_district = "All Districts"

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. Live Telemetry & Feed Status Card
    critical_alerts_count = sum(1 for a in alerts_list if a.get("severity") == "CRITICAL")
    warning_alerts_count = sum(1 for a in alerts_list if a.get("severity") in ("ALERT", "WARNING"))

    st.markdown(f"""
    <div class="telemetry-card">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 800; font-size: 0.85rem; color: #0f172a;">📡 Telemetry & Feeds</span>
            <span style="background: #e0f2fe; color: #0369a1; font-size: 0.7rem; font-weight: 800; padding: 2px 6px; border-radius: 4px;">SYNCED</span>
        </div>
        <div style="font-size: 0.78rem; color: #475569; line-height: 1.55;">
            <div>• <b>ISRO CartoDEM:</b> <span style="color: #059669; font-weight: 700;">1 arc-sec (~30m)</span></div>
            <div>• <b>Observation Net:</b> {len(station_df) if not station_df.empty else 150} Stations</div>
            <div>• <b>IMD Domain:</b> 8°N-38°N (0.25° grid)</div>
            <div>• <b>Active Alerts:</b> <span style="color: {'#dc2626' if critical_alerts_count > 0 else '#059669'}; font-weight: 700;">{critical_alerts_count} Critical</span> | {warning_alerts_count} Warning</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 5. Forecaster Action Tools
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("🔄 Refresh Cache", use_container_width=True, help="Invalidate data loader cache and reload"):
            _invalidate_cache()
            st.cache_data.clear()
            st.rerun()
    with col_sb2:
        if st.button("✍️ Add Feedback", use_container_width=True, help="Jump to forecaster feedback form"):
            switch_to_view("📝 Forecaster Feedback")

    # Export active forecast CSV
    if not district_df.empty:
        day_export = district_df[district_df["date"] == selected_date]
        if not day_export.empty:
            csv_str = day_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Day Forecast (CSV)",
                data=csv_str,
                file_name=f"raincore_forecast_{selected_date}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 0.72rem; color: #94a3b8; text-align: center; line-height: 1.3;">
        MoES &bull; IMD &bull; ISRO Bhuvan Open Data<br>
        Physics-Informed Orographic Post-Processing V2.1
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Top Global Brand Header & Navigation Bar
# ---------------------------------------------------------------------------
st.markdown("""
<div class="raincore-navbar">
    <div class="raincore-brand-group">
        <span class="raincore-brand-icon">🌧️</span>
        <div>
            <div style="display: flex; align-items: center;">
                <h1 class="raincore-brand-title">RainCore</h1>
                <span class="raincore-badge">MONSOON AI</span>
            </div>
            <p class="raincore-brand-subtitle">
                Physics-Informed Bias Correction &bull; Heavy Rain Risk Calibration &bull; ISRO CartoDEM Topography Downscaling
            </p>
        </div>
    </div>
    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
        <span class="pill-badge" style="background: #f0fdf4; border-color: #bbf7d0; color: #166534;">
            <span class="pulse-dot"></span> LIVE FORECASTS
        </span>
        <span class="pill-badge">🛰️ ISRO CartoDEM 30m</span>
        <span class="pill-badge">📍 IMD Domain: 8°N-38°N</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Clean, Visible, Well-Placed Segmented Navigation Bar
# ("📖 How to Use & Guide" is on the far left!)
# ---------------------------------------------------------------------------
selected_nav = st.segmented_control(
    "RainCore Navigation",
    NAV_OPTIONS,
    default=st.session_state.get("raincore_active_tab", "🗺️ District & Station Map"),
    key="raincore_segmented_nav",
    label_visibility="collapsed",
    width="stretch",
)

if not selected_nav:
    nav_view = st.session_state.get("raincore_active_tab", "🗺️ District & Station Map")
else:
    nav_view = selected_nav
    st.session_state["raincore_active_tab"] = nav_view

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)


# ===========================================================================
# VIEW 0: How to Use & System Guide (Far Left Navigation Option)
# ===========================================================================
if nav_view == "📖 How to Use & Guide":
    render_guide_view(switch_to_view)


# ===========================================================================
# VIEW 1: District & Station Map
# ===========================================================================
elif nav_view == "🗺️ District & Station Map":
    render_page_help_banner(nav_view, switch_to_view)

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
        day_districts = district_df[district_df["date"] == selected_date].copy()
        day_stations = station_df[station_df["date"] == selected_date].copy() if not station_df.empty else pd.DataFrame()

        # Apply sidebar controls directly (no duplicate controls on dashboard)
        effective_min_rain = sidebar_min_rain
        if effective_min_rain > 0:
            day_districts = day_districts[day_districts["corrected_rainfall_mm"] >= effective_min_rain]

        if sidebar_district != "All Districts":
            day_districts = day_districts[day_districts["district_name"] == sidebar_district]

        # Active parameters indicator ribbon
        st.markdown(f"""
        <div class="filter-status-banner">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <span style="font-weight: 700; color: #0369a1; font-size: 0.82rem; text-transform: uppercase;">Active Scope:</span>
                    <span class="filter-chip">📅 Date: <b>{selected_date}</b></span>
                    <span class="filter-chip">💧 Min Rain: <b>&ge; {sidebar_min_rain:.1f} mm</b></span>
                    <span class="filter-chip">📍 District: <b>{sidebar_district}</b></span>
                    <span class="filter-chip">📊 Displayed: <b>{len(day_districts)} districts</b></span>
                </div>
                <div style="font-size: 0.78rem; color: #64748b;">
                    ⚙️ <i>Filter parameters managed via left sidebar</i>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Top 4 KPI Metrics
        avg_rain = day_districts["corrected_rainfall_mm"].mean() if not day_districts.empty else 0.0
        max_rain = day_districts["corrected_rainfall_mm"].max() if not day_districts.empty else 0.0
        high_risk_count = len(day_districts[day_districts["p_heavy"] >= 0.40]) if not day_districts.empty else 0
        dom_regime = day_districts["dominant_regime"].iloc[0].replace("_", " ").title() if not day_districts.empty else "Active Monsoon"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Mean Rainfall</div>
                <div class="kpi-value">{avg_rain:.1f} <span style="font-size: 0.9rem; color: #64748b;">mm</span></div>
                <div class="kpi-tag">Spatial areal mean ({len(day_districts)} districts)</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Peak Recorded Rain</div>
                <div class="kpi-value">{max_rain:.1f} <span style="font-size: 0.9rem; color: #64748b;">mm</span></div>
                <div class="kpi-tag" style="color: {'#dc2626' if max_rain >= 115.6 else ('#ea580c' if max_rain >= 64.5 else '#0284c7')};">
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

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Map Display Header with Mode Selector
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
    render_page_help_banner(nav_view, switch_to_view)

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
    render_page_help_banner(nav_view, switch_to_view)

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
    render_page_help_banner(nav_view, switch_to_view)

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
    render_page_help_banner(nav_view, switch_to_view)

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
    render_page_help_banner(nav_view, switch_to_view)

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
    render_page_help_banner(nav_view, switch_to_view)

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
