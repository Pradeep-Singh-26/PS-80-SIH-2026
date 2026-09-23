"""Verification skill charts for the dashboard."""

import streamlit as st
import pandas as pd

from api.data_loader import (
    load_verification_summary,
    load_fss_scores,
    load_reliability_data,
    load_regime_summary,
)


def render_skill_view():
    """Render the full verification / skill comparison view."""
    verification = load_verification_summary()
    if not verification:
        st.warning("Verification report not generated yet. Run the pipeline first.")
        return

    v_df = pd.DataFrame(verification)

    # ------------------------------------------------------------------
    # Overall metrics table
    # ------------------------------------------------------------------
    st.subheader("Overall Metrics (all dates, all grid cells)")

    # Pick key columns
    key_cols = ["source", "n_points", "rmse", "bias", "mae"]
    available = [c for c in key_cols if c in v_df.columns]

    st.dataframe(
        v_df[available].style.format(
            {c: "{:.2f}" for c in available if c not in ["source", "n_points"]}
        ).highlight_min(subset=["rmse"], color="#d4edda")
        if "rmse" in available else v_df[available],
        use_container_width=True,
    )

    # ------------------------------------------------------------------
    # RMSE / Bias bar charts
    # ------------------------------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        if "rmse" in v_df.columns:
            st.subheader("RMSE by Source")
            chart_df = v_df.set_index("source")[["rmse"]]
            st.bar_chart(chart_df)

    with col2:
        if "bias" in v_df.columns:
            st.subheader("Bias by Source")
            chart_df = v_df.set_index("source")[["bias"]]
            st.bar_chart(chart_df)

    # ------------------------------------------------------------------
    # Categorical metrics per threshold
    # ------------------------------------------------------------------
    st.subheader("Categorical Metrics by Threshold")
    threshold_options = []
    for col in v_df.columns:
        if col.endswith("_pod"):
            t = col.replace("_pod", "")
            if t not in threshold_options:
                threshold_options.append(t)

    if threshold_options:
        selected_threshold = st.selectbox("Threshold", threshold_options)
        cat_cols = [
            f"{selected_threshold}_pod",
            f"{selected_threshold}_far",
            f"{selected_threshold}_csi",
            f"{selected_threshold}_ets",
        ]
        cat_available = [c for c in cat_cols if c in v_df.columns]
        if cat_available:
            cat_df = v_df[["source"] + cat_available].set_index("source")
            cat_df.columns = [c.split("_", 1)[1].upper() for c in cat_df.columns]
            st.dataframe(cat_df.style.format("{:.3f}"), use_container_width=True)
            st.bar_chart(cat_df)

    # ------------------------------------------------------------------
    # FSS scores
    # ------------------------------------------------------------------
    fss_data = load_fss_scores()
    if fss_data:
        st.subheader("Fractions Skill Score (FSS) by Neighborhood Scale")
        fss_df = pd.DataFrame(fss_data)

        fss_threshold = st.selectbox(
            "FSS Threshold",
            fss_df["threshold"].unique(),
            key="fss_threshold",
        )
        filtered_fss = fss_df[fss_df["threshold"] == fss_threshold]

        if not filtered_fss.empty:
            pivot = filtered_fss.pivot_table(
                index="neighborhood_radius", columns="source", values="fss"
            )
            st.line_chart(pivot)

    # ------------------------------------------------------------------
    # Reliability diagram data
    # ------------------------------------------------------------------
    reliability = load_reliability_data()
    if reliability:
        st.subheader("Reliability Diagram Data")
        rel_threshold = st.selectbox(
            "Probability Threshold",
            list(reliability.keys()),
            key="rel_threshold",
        )
        rel = reliability[rel_threshold]
        rel_df = pd.DataFrame({
            "Forecast Probability": rel["forecast_frequency"],
            "Observed Frequency": rel["observed_frequency"],
            "Sample Count": rel["counts"],
        }, index=[f"{c:.1f}" for c in rel["bin_centers"]])

        col1, col2 = st.columns(2)
        with col1:
            st.line_chart(rel_df[["Forecast Probability", "Observed Frequency"]])
        with col2:
            st.bar_chart(rel_df["Sample Count"])

    # ------------------------------------------------------------------
    # Per-regime breakdown
    # ------------------------------------------------------------------
    regime_data = load_regime_summary()
    if regime_data:
        st.subheader("Per-Regime Verification")
        r_df = pd.DataFrame(regime_data)
        if "rmse" in r_df.columns and "regime" in r_df.columns:
            pivot = r_df.pivot_table(index="regime", columns="source", values="rmse")
            st.bar_chart(pivot)
