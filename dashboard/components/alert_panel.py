"""Alert panel component for the dashboard with clean White, Black, and Light Blue aesthetic."""

import streamlit as st
import pandas as pd

from api.data_loader import load_alerts


def render_alert_panel():
    """Render the rainfall alerts and warnings dashboard panel."""
    alerts = load_alerts()

    if not alerts:
        st.markdown("""
        <div style="background: #f0f7ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 2rem; text-align: center;">
            <span style="font-size: 2rem;">🛡️</span>
            <h4 style="color: #0369a1; margin: 0.5rem 0 0.2rem 0;">No Active Rainfall Alerts</h4>
            <p style="color: #64748b; font-size: 0.9rem; margin: 0;">Run the pipeline with alert rules to generate real-time district advisories.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    alerts_df = pd.DataFrame(alerts)

    total_alerts = len(alerts_df)
    critical_count = len(alerts_df[alerts_df["severity"] == "CRITICAL"])
    alert_count = len(alerts_df[alerts_df["severity"] == "ALERT"])
    warning_count = len(alerts_df[alerts_df["severity"] == "WARNING"])
    info_count = len(alerts_df[alerts_df["severity"] == "INFO"])

    # Summary KPI row in modern white/black/light-blue styled cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 3px solid #0284c7; border-radius: 10px; padding: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
            <div style="color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Total Alerts Logged</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #0f172a; margin-top: 0.2rem;">{total_alerts}</div>
            <div style="color: #0284c7; font-size: 0.75rem; font-weight: 500; margin-top: 0.2rem;">Across monitored districts</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #fee2e2; border-top: 3px solid #dc2626; border-radius: 10px; padding: 1rem; box-shadow: 0 2px 8px rgba(220,38,38,0.05);">
            <div style="color: #991b1b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Critical / Red Level</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #dc2626; margin-top: 0.2rem;">{critical_count}</div>
            <div style="color: #ef4444; font-size: 0.75rem; font-weight: 500; margin-top: 0.2rem;">Immediate action needed</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #ffedd5; border-top: 3px solid #ea580c; border-radius: 10px; padding: 1rem; box-shadow: 0 2px 8px rgba(234,88,12,0.05);">
            <div style="color: #9a3412; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Alert / Orange Level</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #ea580c; margin-top: 0.2rem;">{alert_count}</div>
            <div style="color: #f97316; font-size: 0.75rem; font-weight: 500; margin-top: 0.2rem;">Be prepared for heavy rain</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #fef3c7; border-top: 3px solid #eab308; border-radius: 10px; padding: 1rem; box-shadow: 0 2px 8px rgba(234,179,8,0.05);">
            <div style="color: #854d0e; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Warning / Yellow Level</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #ca8a04; margin-top: 0.2rem;">{warning_count}</div>
            <div style="color: #eab308; font-size: 0.75rem; font-weight: 500; margin-top: 0.2rem;">Monitor conditions closely</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Filter Bar container
    with st.container():
        st.markdown("""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px;">
            <div style="font-weight: 700; color: #0f172a; font-size: 0.9rem; margin-bottom: 6px;">🔍 Filter Advisories</div>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            all_sevs = ["CRITICAL", "ALERT", "WARNING", "INFO"]
            available_sevs = [s for s in all_sevs if s in alerts_df["severity"].unique()] or all_sevs
            severity_filter = st.multiselect(
                "Filter by Severity",
                options=available_sevs,
                default=available_sevs,
                help="Select severity levels to show",
            )
        with col2:
            district_options = sorted(alerts_df["district_name"].dropna().unique())
            district_filter = st.multiselect(
                "Filter by District",
                options=district_options,
                default=district_options,
                help="Select districts to monitor",
            )

    filtered = alerts_df[
        (alerts_df["severity"].isin(severity_filter))
        & (alerts_df["district_name"].isin(district_filter))
    ]

    st.markdown(f"<div style='font-weight: 700; font-size: 1.1rem; color: #0f172a; margin: 16px 0 10px 0;'>Active Advisories & Bulletins ({len(filtered)} items)</div>", unsafe_allow_html=True)

    if filtered.empty:
        st.info("No alerts match the selected filter criteria.")
    else:
        for _, alert in filtered.iterrows():
            sev = str(alert.get("severity", "INFO")).upper()
            district = alert.get("district_name", "Unknown District")
            date_str = alert.get("date", "N/A")
            msg = alert.get("message", "Precipitation warning issued.")
            rule = alert.get("rule_name", "standard_threshold")

            # Clean styling per severity with white cards & light tints
            if sev == "CRITICAL":
                border_color = "#f87171"
                bg_color = "#fef2f2"
                badge_bg = "#dc2626"
                badge_color = "#ffffff"
                icon = "🚨"
            elif sev == "ALERT":
                border_color = "#fdba74"
                bg_color = "#fff7ed"
                badge_bg = "#ea580c"
                badge_color = "#ffffff"
                icon = "⚠️"
            elif sev == "WARNING":
                border_color = "#fde047"
                bg_color = "#fefce8"
                badge_bg = "#eab308"
                badge_color = "#0f172a"
                icon = "⚡"
            else:
                border_color = "#bae6fd"
                bg_color = "#f0f9ff"
                badge_bg = "#0284c7"
                badge_color = "#ffffff"
                icon = "ℹ️"

            st.markdown(f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 1.1rem;">{icon}</span>
                        <span style="font-weight: 700; font-size: 1.05rem; color: #0f172a;">{district}</span>
                        <span style="background: {badge_bg}; color: {badge_color}; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px; letter-spacing: 0.5px;">{sev}</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.8rem; font-family: monospace;">📅 {date_str}</div>
                </div>
                <div style="color: #1e293b; font-size: 0.92rem; line-height: 1.5; margin-bottom: 6px;">
                    {msg}
                </div>
                <div style="display: flex; gap: 16px; font-size: 0.78rem; color: #64748b; border-top: 1px dashed {border_color}; padding-top: 6px; margin-top: 6px;">
                    <span>Rule Trigger: <b>{rule}</b></span>
                    <span>Action: <b>Notify District Disaster Management Authority (DDMA)</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Secondary Analytics Row
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin-bottom: 8px;">
            <div style="font-weight: 700; color: #0f172a; font-size: 0.95rem; margin-bottom: 10px;">📊 Alert Distribution by District</div>
        </div>
        """, unsafe_allow_html=True)
        if not filtered.empty:
            summary = filtered.groupby(["district_name", "severity"]).size().unstack(fill_value=0)
            st.dataframe(summary, use_container_width=True)

    with col_b:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin-bottom: 8px;">
            <div style="font-weight: 700; color: #0f172a; font-size: 0.95rem; margin-bottom: 10px;">📅 Alerts Timeline (Event Frequency)</div>
        </div>
        """, unsafe_allow_html=True)
        if not filtered.empty:
            date_counts = filtered.groupby("date").size()
            st.bar_chart(date_counts)
