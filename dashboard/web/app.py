"""PS 26080 -- Streamlit Dashboard.

Interactive dashboard for the Regime-Aware Rainfall Post-Processing system.
Consumes data from the FastAPI backend or directly from output files.

Run:
    streamlit run dashboard/web/app.py

For dev with fixture data:
    CONFIG_PATH=config.test.yaml streamlit run dashboard/web/app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

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
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PS 26080 | Regime-Aware Rainfall Post-Processing",
    page_icon=":cloud_with_rain:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a5276;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1.2rem;
        color: white;
        text-align: center;
    }
    .severity-CRITICAL { color: #e74c3c; font-weight: bold; }
    .severity-ALERT { color: #e67e22; font-weight: bold; }
    .severity-WARNING { color: #f39c12; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select View",
    [
        "District & Station Map",
        "Regime Classification",
        "Verification & Skill",
        "Alerts Dashboard",
        "Raw vs Corrected",
        "Feedback",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**PS 26080** | Regime-Aware AI\nPost-Processing of Monsoon\nRainfall Forecasts")


# ===========================================================================
# Page: District & Station Map
# ===========================================================================
if page == "District & Station Map":
    st.markdown('<p class="main-header">District & Station Products</p>', unsafe_allow_html=True)

    district_df = load_district_table()
    station_df = load_station_table()

    if district_df.empty:
        st.warning("District table not generated yet. Run the pipeline first.")
    else:
        # Date selector
        dates = sorted(district_df["date"].unique())
        selected_date = st.selectbox("Select Date", dates, index=len(dates) // 2)

        day_districts = district_df[district_df["date"] == selected_date]
        day_stations = station_df[station_df["date"] == selected_date] if not station_df.empty else pd.DataFrame()

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_rain = day_districts["corrected_rainfall_mm"].mean()
            st.metric("Avg Rainfall (mm)", f"{avg_rain:.1f}")
        with col2:
            max_rain = day_districts["corrected_rainfall_mm"].max()
            st.metric("Max Rainfall (mm)", f"{max_rain:.1f}")
        with col3:
            avg_p_heavy = day_districts["p_heavy"].mean()
            st.metric("Avg P(Heavy)", f"{avg_p_heavy:.1%}")
        with col4:
            dominant = day_districts["dominant_regime"].iloc[0] if len(day_districts) > 0 else "N/A"
            st.metric("Dominant Regime", dominant.replace("_", " ").title())

        # Map
        st.subheader("Station Map")
        if not day_stations.empty:
            from dashboard.components.map_component import create_station_map
            map_html = create_station_map(day_stations)
            st.components.v1.html(map_html, height=500)
        else:
            st.info("No station data for this date.")

        # District table
        st.subheader("District Table")
        st.dataframe(
            day_districts.style.background_gradient(
                subset=["corrected_rainfall_mm"], cmap="YlOrRd"
            ).background_gradient(
                subset=["p_heavy"], cmap="RdYlGn_r"
            ),
            use_container_width=True,
        )

        # Station table
        if not day_stations.empty:
            st.subheader("Station Table")
            st.dataframe(
                day_stations.style.background_gradient(
                    subset=["corrected_rainfall_mm"], cmap="YlOrRd"
                ),
                use_container_width=True,
            )


# ===========================================================================
# Page: Regime Classification
# ===========================================================================
elif page == "Regime Classification":
    st.markdown('<p class="main-header">Regime Classification</p>', unsafe_allow_html=True)

    regime_df = load_regime_predictions()
    if regime_df.empty:
        st.warning("Regime predictions not available yet.")
    else:
        regime_df["date"] = pd.to_datetime(regime_df["date"])

        from dashboard.components.regime_explainer import render_regime_panel
        render_regime_panel(regime_df)


# ===========================================================================
# Page: Verification & Skill
# ===========================================================================
elif page == "Verification & Skill":
    st.markdown('<p class="main-header">Verification & Skill Comparison</p>', unsafe_allow_html=True)

    from dashboard.components.skill_charts import render_skill_view
    render_skill_view()


# ===========================================================================
# Page: Alerts Dashboard
# ===========================================================================
elif page == "Alerts Dashboard":
    st.markdown('<p class="main-header">Rainfall Alerts</p>', unsafe_allow_html=True)

    from dashboard.components.alert_panel import render_alert_panel
    render_alert_panel()


# ===========================================================================
# Page: Raw vs Corrected
# ===========================================================================
elif page == "Raw vs Corrected":
    st.markdown('<p class="main-header">Raw NWP vs Corrected Comparison</p>', unsafe_allow_html=True)

    verification = load_verification_summary()
    if not verification:
        st.warning("Verification report not generated yet.")
    else:
        st.subheader("Overall Metrics Comparison")
        v_df = pd.DataFrame(verification)
        display_cols = ["source", "rmse", "bias", "mae", "n_points"]
        available_cols = [c for c in display_cols if c in v_df.columns]
        st.dataframe(v_df[available_cols], use_container_width=True)

        # Bar chart comparison
        if "rmse" in v_df.columns:
            st.subheader("RMSE Comparison")
            st.bar_chart(v_df.set_index("source")["rmse"])

        if "bias" in v_df.columns:
            st.subheader("Bias Comparison")
            st.bar_chart(v_df.set_index("source")["bias"])

        # Per-regime breakdown
        regime_data = load_regime_summary()
        if regime_data:
            st.subheader("Per-Regime RMSE")
            r_df = pd.DataFrame(regime_data)
            if "rmse" in r_df.columns and "regime" in r_df.columns:
                pivot = r_df.pivot_table(index="regime", columns="source", values="rmse")
                st.bar_chart(pivot)


# ===========================================================================
# Page: Feedback
# ===========================================================================
elif page == "Feedback":
    st.markdown('<p class="main-header">Forecaster Feedback</p>', unsafe_allow_html=True)
    st.markdown("Submit corrections or comments to improve future forecasts.")

    with st.form("feedback_form"):
        col1, col2 = st.columns(2)
        with col1:
            fb_date = st.date_input("Date")
            fb_type = st.selectbox(
                "Feedback Type",
                ["regime_correction", "rainfall_correction", "general"],
            )
            fb_district = st.text_input("District Name (optional)")
        with col2:
            fb_original = st.text_input("Original Value")
            fb_corrected = st.text_input("Corrected Value")
            fb_forecaster = st.text_input("Your ID (optional)")

        fb_comment = st.text_area("Comment")
        submitted = st.form_submit_button("Submit Feedback")

        if submitted:
            from api.data_loader import save_feedback
            feedback_id = save_feedback({
                "date": str(fb_date),
                "feedback_type": fb_type,
                "district_name": fb_district or None,
                "original_value": fb_original or None,
                "corrected_value": fb_corrected or None,
                "comment": fb_comment or None,
                "forecaster_id": fb_forecaster or None,
            })
            st.success(f"Feedback submitted! ID: {feedback_id}")
