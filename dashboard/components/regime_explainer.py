"""Regime classification explainer panel for the dashboard."""

import streamlit as st
import pandas as pd


REGIME_LABELS = [
    "active", "break", "low_depression",
    "western_disturbance", "orographic", "coastal",
]

REGIME_DESCRIPTIONS = {
    "active": "Active monsoon: strong trough, above-normal core-zone rainfall.",
    "break": "Break monsoon: weak/displaced trough, suppressed central-India rainfall.",
    "low_depression": "Monsoon low/depression present in the region.",
    "western_disturbance": "Western disturbance-influenced rainfall (esp. NW India).",
    "orographic": "Terrain-driven rainfall enhancement (Western Ghats, NE hills).",
    "coastal": "Coastal convergence-driven rainfall.",
}

REGIME_COLORS = {
    "active": "#27ae60",
    "break": "#e74c3c",
    "low_depression": "#8e44ad",
    "western_disturbance": "#2980b9",
    "orographic": "#d35400",
    "coastal": "#16a085",
}


def render_regime_panel(regime_df: pd.DataFrame):
    """Render the regime classification panel.

    Args:
        regime_df: DataFrame with date + per-label probabilities +
                   dominant_label + confidence columns.
    """
    # Date selector
    regime_df = regime_df.sort_values("date")
    dates = regime_df["date"].dt.strftime("%Y-%m-%d").tolist()
    selected_date = st.selectbox("Select Date", dates, index=len(dates) // 2)

    row = regime_df[regime_df["date"].dt.strftime("%Y-%m-%d") == selected_date].iloc[0]

    # Header with dominant regime
    dominant = row.get("dominant_label", "unknown")
    confidence = row.get("confidence", 0)
    color = REGIME_COLORS.get(dominant, "#333")

    st.markdown(
        f'<div style="background: {color}; color: white; padding: 1rem; '
        f'border-radius: 10px; text-align: center; margin-bottom: 1rem;">'
        f'<h2 style="margin: 0;">{dominant.replace("_", " ").title()}</h2>'
        f'<p style="margin: 0.3rem 0 0 0;">Confidence: {confidence:.1%}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Description
    desc = REGIME_DESCRIPTIONS.get(dominant, "")
    if desc:
        st.info(desc)

    # Probability bars for all regimes
    st.subheader("All Regime Probabilities")
    prob_cols = [f"{r}_prob" for r in REGIME_LABELS]
    available_probs = {r: row.get(f"{r}_prob", 0) for r in REGIME_LABELS}

    for regime, prob in sorted(available_probs.items(), key=lambda x: -x[1]):
        col_label, col_bar = st.columns([1, 3])
        with col_label:
            st.markdown(f"**{regime.replace('_', ' ').title()}**")
        with col_bar:
            st.progress(min(float(prob), 1.0))
            st.caption(f"{prob:.1%}")

    # Time series of dominant regime
    st.subheader("Regime Timeline")
    timeline_data = regime_df[["date", "dominant_label", "confidence"]].copy()
    timeline_data["date"] = timeline_data["date"].dt.strftime("%Y-%m-%d")

    # Color-coded timeline
    st.dataframe(
        timeline_data.style.applymap(
            lambda v: f"background-color: {REGIME_COLORS.get(v, '#fff')}; color: white;"
            if v in REGIME_COLORS else "",
            subset=["dominant_label"],
        ),
        use_container_width=True,
        height=300,
    )

    # Regime distribution pie chart
    st.subheader("Regime Distribution (Period)")
    regime_counts = regime_df["dominant_label"].value_counts()
    st.bar_chart(regime_counts)
