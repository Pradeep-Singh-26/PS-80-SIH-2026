"""Regime classification explainer component with clean White, Black, and Light Blue theme."""

import streamlit as st
import pandas as pd


REGIME_META = {
    "active": {
        "title": "Active Monsoon",
        "badge": "Active Trough",
        "color": "#0284c7",
        "bg": "#f0f9ff",
        "border": "#bae6fd",
        "desc": "Monsoon trough is near normal or south of normal position with strong low-level westerly winds over Arabian Sea, leading to widespread heavy rainfall over Central India and West Coast.",
        "wind": "Westerly / SW 30-45 kts",
        "moisture": "High (>55 kg/m² TPW)",
        "trough": "South of Normal Position",
        "impact": "Widespread Moderate to Heavy Rain",
    },
    "break": {
        "title": "Break Monsoon",
        "badge": "Suppressed Core",
        "color": "#64748b",
        "bg": "#f8fafc",
        "border": "#cbd5e1",
        "desc": "Monsoon trough shifted towards the foothills of the Himalayas. Rainfall is significantly suppressed over Central India while shifting heavily towards Himalayan foothills and SE peninsula.",
        "wind": "Weak Westerlies 10-20 kts",
        "moisture": "Moderate (35-45 kg/m² TPW)",
        "trough": "Shifted to Himalayan Foothills",
        "impact": "Floods in Foothills, Dry Core Zone",
    },
    "low_depression": {
        "title": "Monsoon Low / Depression",
        "badge": "Synoptic Vortex",
        "color": "#0369a1",
        "bg": "#e0f2fe",
        "border": "#7dd3fc",
        "desc": "Cyclonic circulation / low pressure system formed over Bay of Bengal / Arabian Sea and tracking inland along the monsoon trough, producing localized intense rainfall bands.",
        "wind": "Cyclonic Inflow >40 kts",
        "moisture": "Extreme (>65 kg/m² TPW)",
        "trough": "Embedded in Trough Zone",
        "impact": "Intense Rainbands & Local Inundation",
    },
    "western_disturbance": {
        "title": "Western Disturbance",
        "badge": "Mid-latitude Wave",
        "color": "#0f766e",
        "bg": "#f0fdfa",
        "border": "#99f6e4",
        "desc": "Upper-tropospheric westerly trough interacting with monsoon moisture over North & Northwest India, triggering orographic precipitation and cloudburst risks.",
        "wind": "Upper Westerly Jet Interacting",
        "moisture": "Moderate-High localized",
        "trough": "Northwest Axis Incursion",
        "impact": "Orographic Flash Floods in North",
    },
    "orographic": {
        "title": "Orographic Enhancement",
        "badge": "Terrain Uplift",
        "color": "#0284c7",
        "bg": "#f0f9ff",
        "border": "#38bdf8",
        "desc": "Steep topographic barriers (Western Ghats, Meghalaya Khasi-Jaintia Hills, Himalayan ridge) forcing strong moisture uplift and extreme rainfall on windward slopes.",
        "wind": "Cross-Barrier Flow >25 kts",
        "moisture": "Very High on Windward Slopes",
        "trough": "Synoptic Windward Forcing",
        "impact": "Extreme Orographic Rain (>200mm)",
    },
    "coastal": {
        "title": "Coastal Convergence",
        "badge": "Sea-Breeze / Shear",
        "color": "#0284c7",
        "bg": "#f0f9ff",
        "border": "#bae6fd",
        "desc": "Frictional convergence of low-level winds at the coastal boundary, giving rise to nocturnal and early morning convective showers along the coastline.",
        "wind": "Shore-perpendicular convergence",
        "moisture": "High marine boundary layer",
        "trough": "Coastal shear zone",
        "impact": "Coastal localized squalls",
    },
}


def render_regime_panel(regime_df: pd.DataFrame):
    """Render the regime classification panel with modern white/black/light-blue layout.

    Args:
        regime_df: DataFrame with date + per-label probabilities +
                   dominant_label + confidence columns.
    """
    if regime_df.empty:
        st.info("No regime predictions available.")
        return

    regime_df = regime_df.sort_values("date")
    dates = regime_df["date"].dt.strftime("%Y-%m-%d").tolist()

    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_date = st.selectbox("Select Forecast Date", dates, index=len(dates) // 2)

    row = regime_df[regime_df["date"].dt.strftime("%Y-%m-%d") == selected_date].iloc[0]

    dominant = str(row.get("dominant_label", "active")).lower()
    confidence = float(row.get("confidence", 0.0))
    meta = REGIME_META.get(dominant, REGIME_META["active"])

    # Hero Banner Card
    st.markdown(f"""
    <div style="background: {meta['bg']}; border: 1.5px solid {meta['border']}; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.06);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; border-bottom: 1px solid {meta['border']}; padding-bottom: 12px; margin-bottom: 14px;">
            <div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.6rem; font-weight: 800; color: #0f172a;">{meta['title']}</span>
                    <span style="background: #ffffff; color: {meta['color']}; border: 1px solid {meta['border']}; font-size: 0.75rem; font-weight: 700; padding: 3px 10px; border-radius: 20px;">{meta['badge']}</span>
                </div>
                <div style="color: #475569; font-size: 0.88rem; margin-top: 4px;">📅 Forecast Date: <b>{selected_date}</b> | Synoptic Scale Mode</div>
            </div>
            <div style="text-align: right; background: #ffffff; border: 1px solid {meta['border']}; border-radius: 10px; padding: 8px 16px;">
                <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Confidence Score</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {meta['color']};">{confidence:.1%}</div>
            </div>
        </div>
        <div style="color: #1e293b; font-size: 0.95rem; line-height: 1.6; margin-bottom: 16px;">
            {meta['desc']}
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; background: #ffffff; border: 1px solid {meta['border']}; border-radius: 8px; padding: 12px;">
            <div>
                <span style="color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">💨 Wind Circulation</span>
                <div style="color: #0f172a; font-weight: 600; font-size: 0.88rem; margin-top: 2px;">{meta['wind']}</div>
            </div>
            <div>
                <span style="color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">💧 Moisture Flux (TPW)</span>
                <div style="color: #0f172a; font-weight: 600; font-size: 0.88rem; margin-top: 2px;">{meta['moisture']}</div>
            </div>
            <div>
                <span style="color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">🧭 Trough Orientation</span>
                <div style="color: #0f172a; font-weight: 600; font-size: 0.88rem; margin-top: 2px;">{meta['trough']}</div>
            </div>
            <div>
                <span style="color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">⚡ Expected Impact</span>
                <div style="color: #0f172a; font-weight: 600; font-size: 0.88rem; margin-top: 2px;">{meta['impact']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2-Column Split: Regime Probabilities & Historical Distribution
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-weight: 700; color: #0f172a; font-size: 1rem; margin-bottom: 4px;">📈 Multi-Regime Probability Distribution</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 14px;">Softmax ensemble probabilities for each meteorological pattern</div>
        </div>
        """, unsafe_allow_html=True)

        regime_keys = list(REGIME_META.keys())
        prob_dict = {}
        for r in regime_keys:
            prob_dict[r] = float(row.get(f"{r}_prob", 0.0))

        # Sort descending
        sorted_probs = sorted(prob_dict.items(), key=lambda x: -x[1])
        for r_key, p_val in sorted_probs:
            r_info = REGIME_META.get(r_key, {})
            is_active = (r_key == dominant)
            bar_bg = "#0284c7" if is_active else "#94a3b8"
            card_border = "#38bdf8" if is_active else "#f1f5f9"
            card_bg = "#f0f9ff" if is_active else "#ffffff"

            st.markdown(f"""
            <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: {'700' if is_active else '500'}; color: #0f172a; font-size: 0.9rem;">
                        {'⭐ ' if is_active else ''}{r_info.get('title', r_key)}
                    </span>
                    <span style="font-weight: 700; color: {'#0284c7' if is_active else '#475569'}; font-size: 0.9rem;">{p_val:.1%}</span>
                </div>
                <div style="background: #e2e8f0; border-radius: 6px; height: 8px; overflow: hidden; width: 100%;">
                    <div style="background: {bar_bg}; width: {min(100, max(2, int(p_val * 100)))}%; height: 100%; border-radius: 6px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-weight: 700; color: #0f172a; font-size: 1rem; margin-bottom: 4px;">📊 Seasonal Regime Frequency</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 14px;">Occurrence count of synoptic regimes across the dataset</div>
        </div>
        """, unsafe_allow_html=True)

        counts = regime_df["dominant_label"].value_counts().rename(index=lambda x: x.replace("_", " ").title())
        st.bar_chart(counts)

    # Timeline section
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
        <div style="font-weight: 700; color: #0f172a; font-size: 1rem; margin-bottom: 4px;">📅 Synoptic Regime Timeline (Full Season)</div>
        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 12px;">Track synoptic transitions and model confidence over time</div>
    </div>
    """, unsafe_allow_html=True)

    timeline_data = regime_df[["date", "dominant_label", "confidence"]].copy()
    timeline_data["date"] = timeline_data["date"].dt.strftime("%Y-%m-%d")
    timeline_data["dominant_label"] = timeline_data["dominant_label"].str.replace("_", " ").str.title()
    timeline_data["confidence"] = timeline_data["confidence"].apply(lambda x: f"{x:.1%}")

    st.dataframe(timeline_data, use_container_width=True, height=260)
