"""Verification skill charts and model comparison with clean White, Black, and Light Blue theme."""

import streamlit as st
import pandas as pd

from api.data_loader import (
    load_verification_summary,
    load_fss_scores,
    load_reliability_data,
    load_regime_summary,
)


def render_skill_view():
    """Render the verification, skill benchmark, and reliability view."""
    verification = load_verification_summary()
    if not verification:
        st.markdown("""
        <div style="background: #f0f7ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 2rem; text-align: center;">
            <span style="font-size: 2rem;">📊</span>
            <h4 style="color: #0369a1; margin: 0.5rem 0 0.2rem 0;">No Verification Summary Found</h4>
            <p style="color: #64748b; font-size: 0.9rem; margin: 0;">Run the verification pipeline to generate skill scores and benchmark comparisons.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    v_df = pd.DataFrame(verification)

    # Top Benchmark Scorecard Cards (Raw NWP vs AI Corrected)
    raw_row = v_df[v_df["source"].str.contains("raw", case=False, na=False)]
    corr_row = v_df[v_df["source"].str.contains("corrected|model|ai|post", case=False, na=False)]

    if not raw_row.empty and not corr_row.empty:
        raw_rmse = float(raw_row.iloc[0].get("rmse", 0.0))
        corr_rmse = float(corr_row.iloc[0].get("rmse", 0.0))
        raw_mae = float(raw_row.iloc[0].get("mae", 0.0))
        corr_mae = float(corr_row.iloc[0].get("mae", 0.0))
        raw_bias = float(raw_row.iloc[0].get("bias", 0.0))
        corr_bias = float(corr_row.iloc[0].get("bias", 0.0))

        rmse_delta = ((corr_rmse - raw_rmse) / raw_rmse) * 100 if raw_rmse > 0 else 0
        mae_delta = ((corr_mae - raw_mae) / raw_mae) * 100 if raw_mae > 0 else 0

        st.markdown("""
        <div style="font-weight: 700; color: #0f172a; font-size: 1.1rem; margin-bottom: 12px;">
            ⚡ AI Post-Processing Benchmark vs Raw NWP
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 3px solid #0284c7; border-radius: 10px; padding: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <div style="color: #64748b; font-size: 0.78rem; font-weight: 600; text-transform: uppercase;">RMSE Reduction</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #0284c7; margin: 4px 0;">{corr_rmse:.2f} <span style="font-size: 0.9rem; color: #64748b; font-weight: 500;">vs {raw_rmse:.2f} mm</span></div>
                <div style="color: #059669; font-size: 0.8rem; font-weight: 700;">📉 {rmse_delta:.1f}% error drop</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 3px solid #0ea5e9; border-radius: 10px; padding: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <div style="color: #64748b; font-size: 0.78rem; font-weight: 600; text-transform: uppercase;">MAE Improvement</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #0ea5e9; margin: 4px 0;">{corr_mae:.2f} <span style="font-size: 0.9rem; color: #64748b; font-weight: 500;">vs {raw_mae:.2f} mm</span></div>
                <div style="color: #059669; font-size: 0.8rem; font-weight: 700;">📉 {mae_delta:.1f}% error drop</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 3px solid #0369a1; border-radius: 10px; padding: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <div style="color: #64748b; font-size: 0.78rem; font-weight: 600; text-transform: uppercase;">Systematic Bias</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #0f172a; margin: 4px 0;">{corr_bias:+.2f} <span style="font-size: 0.9rem; color: #64748b; font-weight: 500;">vs {raw_bias:+.2f} mm</span></div>
                <div style="color: #0284c7; font-size: 0.8rem; font-weight: 700;">🎯 Near-zero calibration</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            n_pts = int(v_df.iloc[0].get("n_points", 0))
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 3px solid #38bdf8; border-radius: 10px; padding: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <div style="color: #64748b; font-size: 0.78rem; font-weight: 600; text-transform: uppercase;">Sample Size</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #0f172a; margin: 4px 0;">{n_pts:,}</div>
                <div style="color: #64748b; font-size: 0.8rem; font-weight: 500;">Grid-day paired observations</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Organized Verification Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overall Metrics",
        "🎯 Categorical Skill (POD/FAR/CSI)",
        "📐 Spatial Skill (FSS)",
        "📈 Reliability & Calibration",
        "🌀 Per-Regime Breakdown",
    ])

    with tab1:
        st.markdown("""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;">
            <div style="font-weight: 700; color: #0f172a; font-size: 0.92rem;">Continuous Verification Metrics Table</div>
        </div>
        """, unsafe_allow_html=True)

        key_cols = ["source", "n_points", "rmse", "bias", "mae"]
        available = [c for c in key_cols if c in v_df.columns]
        st.dataframe(v_df[available], use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if "rmse" in v_df.columns:
                st.markdown("<div style='font-weight: 600; font-size: 0.9rem; margin: 12px 0 6px 0;'>RMSE by Source (mm)</div>", unsafe_allow_html=True)
                st.bar_chart(v_df.set_index("source")["rmse"])
        with col_b:
            if "bias" in v_df.columns:
                st.markdown("<div style='font-weight: 600; font-size: 0.9rem; margin: 12px 0 6px 0;'>Bias by Source (mm)</div>", unsafe_allow_html=True)
                st.bar_chart(v_df.set_index("source")["bias"])

    with tab2:
        threshold_options = []
        for col in v_df.columns:
            if col.endswith("_pod"):
                t = col.replace("_pod", "")
                if t not in threshold_options:
                    threshold_options.append(t)

        if threshold_options:
            sel_col, _ = st.columns([1, 2])
            with sel_col:
                selected_threshold = st.selectbox("Select Rainfall Threshold", threshold_options)

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

                st.markdown(f"<div style='font-weight: 600; font-size: 0.9rem; margin: 10px 0 6px 0;'>Metrics for Threshold: <b>{selected_threshold}</b></div>", unsafe_allow_html=True)
                st.dataframe(cat_df.style.format("{:.3f}"), use_container_width=True)
                st.bar_chart(cat_df)
        else:
            st.info("No categorical threshold metrics found in verification report.")

    with tab3:
        fss_data = load_fss_scores()
        if fss_data:
            fss_df = pd.DataFrame(fss_data)
            sel_fss_col, _ = st.columns([1, 2])
            with sel_fss_col:
                fss_threshold = st.selectbox("Select FSS Intensity Threshold", fss_df["threshold"].unique(), key="fss_select")
            filtered_fss = fss_df[fss_df["threshold"] == fss_threshold]
            if not filtered_fss.empty:
                pivot = filtered_fss.pivot_table(index="neighborhood_radius", columns="source", values="fss")
                st.markdown(f"<div style='font-weight: 600; font-size: 0.9rem; margin: 10px 0 6px 0;'>FSS Curve vs Spatial Neighborhood Window (km)</div>", unsafe_allow_html=True)
                st.line_chart(pivot)
        else:
            st.info("FSS spatial evaluation data not available.")

    with tab4:
        reliability = load_reliability_data()
        if reliability:
            sel_rel_col, _ = st.columns([1, 2])
            with sel_rel_col:
                rel_threshold = st.selectbox("Select Probability Event Threshold", list(reliability.keys()), key="rel_select")
            rel = reliability[rel_threshold]
            rel_df = pd.DataFrame({
                "Forecast Probability": rel.get("forecast_frequency", []),
                "Observed Frequency": rel.get("observed_frequency", []),
                "Sample Count": rel.get("counts", []),
            }, index=[f"{c:.1f}" for c in rel.get("bin_centers", [])])

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("<div style='font-weight: 600; font-size: 0.9rem; margin: 10px 0 6px 0;'>Calibration / Reliability Curve</div>", unsafe_allow_html=True)
                st.line_chart(rel_df[["Forecast Probability", "Observed Frequency"]])
            with col_r2:
                st.markdown("<div style='font-weight: 600; font-size: 0.9rem; margin: 10px 0 6px 0;'>Forecast Frequency Distribution</div>", unsafe_allow_html=True)
                st.bar_chart(rel_df["Sample Count"])
        else:
            st.info("Reliability diagram data not available.")

    with tab5:
        regime_data = load_regime_summary()
        if regime_data:
            r_df = pd.DataFrame(regime_data)
            if "rmse" in r_df.columns and "regime" in r_df.columns:
                pivot = r_df.pivot_table(index="regime", columns="source", values="rmse")
                st.markdown("<div style='font-weight: 600; font-size: 0.9rem; margin: 10px 0 6px 0;'>Per-Regime RMSE Comparison (mm)</div>", unsafe_allow_html=True)
                st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)
                st.bar_chart(pivot)
        else:
            st.info("Per-regime breakdown data not available.")
