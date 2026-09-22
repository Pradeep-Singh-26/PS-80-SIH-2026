"""Alert panel component for the dashboard."""

import streamlit as st
import pandas as pd

from api.data_loader import load_alerts


SEVERITY_ICONS = {
    "CRITICAL": "!!",
    "ALERT": "!",
    "WARNING": "~",
    "INFO": "i",
}


def render_alert_panel():
    """Render the alerts dashboard panel."""
    alerts = load_alerts()

    if not alerts:
        st.info("No alerts generated. Run the pipeline with alert rules to see results.")
        return

    alerts_df = pd.DataFrame(alerts)

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Alerts", len(alerts_df))
    with col2:
        critical = len(alerts_df[alerts_df["severity"] == "CRITICAL"])
        st.metric("Critical", critical)
    with col3:
        alert_count = len(alerts_df[alerts_df["severity"] == "ALERT"])
        st.metric("Alert", alert_count)
    with col4:
        warning = len(alerts_df[alerts_df["severity"] == "WARNING"])
        st.metric("Warning", warning)

    # Filters
    st.subheader("Filter Alerts")
    col1, col2 = st.columns(2)
    with col1:
        severity_filter = st.multiselect(
            "Severity",
            ["CRITICAL", "ALERT", "WARNING"],
            default=["CRITICAL", "ALERT", "WARNING"],
        )
    with col2:
        district_options = sorted(alerts_df["district_name"].unique())
        district_filter = st.multiselect(
            "District",
            district_options,
            default=district_options,
        )

    filtered = alerts_df[
        (alerts_df["severity"].isin(severity_filter))
        & (alerts_df["district_name"].isin(district_filter))
    ]

    # Alert list
    st.subheader(f"Alerts ({len(filtered)} shown)")
    for _, alert in filtered.iterrows():
        severity = alert.get("severity", "INFO")
        if severity == "CRITICAL":
            st.error(
                f"**[{severity}]** {alert.get('district_name', '?')} | "
                f"{alert.get('date', '?')}\n\n{alert.get('message', '')}"
            )
        elif severity == "ALERT":
            st.warning(
                f"**[{severity}]** {alert.get('district_name', '?')} | "
                f"{alert.get('date', '?')}\n\n{alert.get('message', '')}"
            )
        else:
            st.info(
                f"**[{severity}]** {alert.get('district_name', '?')} | "
                f"{alert.get('date', '?')}\n\n{alert.get('message', '')}"
            )

    # Summary table
    st.subheader("Alert Summary by District")
    if not filtered.empty:
        summary = filtered.groupby(["district_name", "severity"]).size().unstack(fill_value=0)
        st.dataframe(summary, use_container_width=True)

    # Alerts by date
    st.subheader("Alerts by Date")
    if not filtered.empty:
        date_counts = filtered.groupby("date").size()
        st.bar_chart(date_counts)
