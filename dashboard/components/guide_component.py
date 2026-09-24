"""Interactive User Guide & Navigation Component for RainCore Dashboard.

Provides:
- Comprehensive overview of the Monsoon AI Post-Processing & CartoDEM Downscaling Platform
- Interactive Quick Navigation cards with 1-click jump buttons to each system view
- Step-by-step daily operational forecaster workflow
- IMD Official Rainfall Threshold & Impact Matrix
- Key Meteorological and AI Terminology
- Contextual page-level navigation ribbons
"""

import streamlit as st


def render_page_help_banner(page_name: str, switch_fn=None):
    """Render a sleek contextual navigation ribbon at the top of any page."""
    help_text_map = {
        "🗺️ District & Station Map": (
            "Explore spatial rainfall fields downscaled via CartoDEM 30m. "
            "Use the map mode selector (top-right of map) to toggle between Satellite Imagery, Terrain, and Light Canvas. "
            "Filter minimum rainfall using the slider to isolate heavy precipitation zones."
        ),
        "🌀 Regime Classification": (
            "Inspect the physics-informed synoptic monsoon circulation patterns (Active, Break, Offshore Trough, Depression). "
            "Each regime uses dynamically calibrated bias correction models suited for its atmospheric flow structure."
        ),
        "🛰️ Topography & CartoDEM": (
            "High-resolution 1 arc-second (~30m) ISRO Bhuvan CartoDEM elevation derivatives. "
            "Inspect windward slope angles, aspect orientation, and valley confinement that induce orographic cloudbursts."
        ),
        "📊 Verification & Skill": (
            "Statistical verification benchmark against IMD observation grids. "
            "Evaluate Fractions Skill Score (FSS), Equitable Threat Score (ETS), and reliability curves proving AI superiority over raw NWP."
        ),
        "🚨 Alerts Dashboard": (
            "Automated multi-tier rainfall bulletins compliant with IMD & NDMA standards. "
            "Filter Critical (Red) and Alert (Orange) districts to generate flash flood advisories and civil protection actions."
        ),
        "⚖️ Raw vs Corrected": (
            "Direct delta comparison between raw Numerical Weather Prediction (ECMWF/GFS) and AI regime-corrected rainfall. "
            "Demonstrates systemic bias elimination and accurate peak rainfall capture over mountainous terrain."
        ),
        "📝 Forecaster Feedback": (
            "Human-in-the-loop operational feedback loop. IMD duty meteorologists log discrepancies or radar signatures "
            "which are automatically queued to retrain subsequent AI model checkpoints."
        ),
    }

    desc = help_text_map.get(page_name, "Select a system view to inspect downscaled monsoon forecasts.")

    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #f0f7ff 0%, #ffffff 100%); border-left: 4px solid #0284c7; border: 1px solid #bae6fd; border-left-width: 4px; border-radius: 8px; padding: 10px 16px; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1rem;">🧭</span>
                <span style="font-weight: 700; color: #0369a1; font-size: 0.84rem; text-transform: uppercase; letter-spacing: 0.5px;">Navigation Guidance:</span>
                <span style="color: #334155; font-size: 0.85rem;">{desc}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if switch_fn and st.button("📖 Full Guide", key=f"guide_btn_{page_name}"):
            switch_fn("📖 How to Use & Guide")


def render_guide_view(switch_fn):
    """Render the comprehensive interactive platform guide and navigation center."""
    st.markdown("""
    <div class="page-title-row">
        <div>
            <h2 class="page-title">📖 System Tour, Navigation & Operational Guide</h2>
            <p class="page-subtitle">Complete walkthrough of the Regime-Aware AI Post-Processing & ISRO CartoDEM Downscaling System</p>
        </div>
        <div>
            <span class="pill-badge" style="background: #f0fdf4; border-color: #bbf7d0; color: #166534;">
                ● OPERATIONAL METEOROLOGY PORTAL
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Welcome Hero Banner
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #0f172a 100%); border-radius: 14px; padding: 24px 28px; color: #ffffff; margin-bottom: 24px; box-shadow: 0 8px 30px rgba(2, 132, 199, 0.18);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
            <div style="max-width: 780px;">
                <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 4px 12px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px;">
                    <span>🌧️</span> RainCore &bull; Monsoon Intelligence & Downscaling Platform
                </div>
                <h1 style="color: #ffffff; font-size: 1.65rem; font-weight: 800; margin: 0 0 10px 0; line-height: 1.25;">
                    Welcome to RainCore — Regime-Aware Monsoon Intelligence
                </h1>
                <p style="color: #e0f2fe; font-size: 0.92rem; line-height: 1.6; margin: 0;">
                    Raw numerical weather models (GFS / ECMWF) suffer from significant spatial displacement and orographic underestimation over India's complex terrain. 
                    This portal integrates <b>synoptic circulation regime classification</b> with <b>ISRO Bhuvan 1 arc-second (~30m) CartoDEM digital elevation models</b> to deliver high-resolution bias-corrected rainfall forecasts, heavy rain exceedance probabilities, and automated disaster management alerts.
                </p>
            </div>
            <div style="background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255,255,255,0.25); border-radius: 12px; padding: 14px 18px; text-align: center; min-width: 170px;">
                <div style="font-size: 0.76rem; color: #bae6fd; font-weight: 600; text-transform: uppercase;">Domain Coverage</div>
                <div style="font-size: 1.45rem; font-weight: 800; color: #ffffff; margin: 2px 0;">8°N - 38°N</div>
                <div style="font-size: 0.75rem; color: #e0f2fe;">68°E - 98°E (Pan-India)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Interactive Navigation Matrix
    st.markdown("""
    <div style="margin-bottom: 12px;">
        <h3 style="font-size: 1.15rem; font-weight: 800; color: #0f172a; margin: 0 0 4px 0;">
            🧭 System Navigation Center (7 Core Operational Modules)
        </h3>
        <p style="font-size: 0.86rem; color: #64748b; margin: 0;">
            Click on any module card below or use the navigation bar to jump directly into that operational view.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Navigation Cards Grid (Row 1)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="kpi-card" style="height: 100%; min-height: 200px; display: flex; flex-direction: column; justify-content: space-between; border-top: 3.5px solid #0284c7;">
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 1.4rem;">🗺️</span>
                    <span style="font-size: 0.7rem; font-weight: 700; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 6px;">CORE VIEW</span>
                </div>
                <div style="font-weight: 800; font-size: 1.05rem; color: #0f172a;">District & Station Map</div>
                <p style="font-size: 0.82rem; color: #475569; margin: 8px 0; line-height: 1.5;">
                    Interactive GIS canvas with 5 basemap layers (Satellite, Topo, Light, OSM, Dark). Displays downscaled precipitation, station telemetry, and P(Heavy) exceedance risk.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Open District & Station Map", key="jump_map"):
            switch_fn("🗺️ District & Station Map")

    with c2:
        st.markdown("""
        <div class="kpi-card" style="height: 100%; min-height: 200px; display: flex; flex-direction: column; justify-content: space-between; border-top: 3.5px solid #8b5cf6;">
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 1.4rem;">🌀</span>
                    <span style="font-size: 0.7rem; font-weight: 700; background: #ede9fe; color: #6d28d9; padding: 2px 8px; border-radius: 6px;">PHYSICS AI</span>
                </div>
                <div style="font-weight: 800; font-size: 1.05rem; color: #0f172a;">Regime Classification</div>
                <p style="font-size: 0.82rem; color: #475569; margin: 8px 0; line-height: 1.5;">
                    Identifies prevailing atmospheric synoptic state: Active, Break, Offshore Trough, or Depression. Drives regime-specific bias weights for accurate local physics.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🌀 Open Regime Classification", key="jump_regime"):
            switch_fn("🌀 Regime Classification")

    with c3:
        st.markdown("""
        <div class="kpi-card" style="height: 100%; min-height: 200px; display: flex; flex-direction: column; justify-content: space-between; border-top: 3.5px solid #059669;">
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 1.4rem;">🛰️</span>
                    <span style="font-size: 0.7rem; font-weight: 700; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 6px;">ISRO CARTODEM</span>
                </div>
                <div style="font-weight: 800; font-size: 1.05rem; color: #0f172a;">Topography & CartoDEM</div>
                <p style="font-size: 0.82rem; color: #475569; margin: 8px 0; line-height: 1.5;">
                    1 arc-sec (~30m) Bhuvan Digital Elevation Model derivatives: windward slope, aspect orientation, and valley confinement explaining Ghats and Himalayan cloudbursts.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🛰️ Open Topography & CartoDEM", key="jump_carto"):
            switch_fn("🛰️ Topography & CartoDEM")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Navigation Cards Grid (Row 2)
    c4, c5, c6, c7 = st.columns(4)
    with c4:
        st.markdown("""
        <div class="kpi-card" style="height: 100%; min-height: 185px; display: flex; flex-direction: column; justify-content: space-between; border-top: 3.5px solid #2563eb;">
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-size: 1.3rem;">📊</span>
                    <span style="font-size: 0.68rem; font-weight: 700; background: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 4px;">SKILL</span>
                </div>
                <div style="font-weight: 800; font-size: 0.96rem; color: #0f172a;">Verification & Skill</div>
                <p style="font-size: 0.78rem; color: #475569; margin: 6px 0; line-height: 1.45;">
                    Validation against IMD observations. Fractions Skill Score (FSS), Equitable Threat Score (ETS), and reliability curves.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📊 Open Verification", key="jump_skill"):
            switch_fn("📊 Verification & Skill")

    with c5:
        st.markdown("""
        <div class="kpi-card" style="height: 100%; min-height: 185px; display: flex; flex-direction: column; justify-content: space-between; border-top: 3.5px solid #dc2626;">
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-size: 1.3rem;">🚨</span>
                    <span style="font-size: 0.68rem; font-weight: 700; background: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px;">WARNINGS</span>
                </div>
                <div style="font-weight: 800; font-size: 0.96rem; color: #0f172a;">Alerts Dashboard</div>
                <p style="font-size: 0.78rem; color: #475569; margin: 6px 0; line-height: 1.45;">
                    Automated multi-tier alert bulletins, Flash Flood advisories, and CAP-compatible feeds for disaster response.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚨 Open Alerts", key="jump_alerts"):
            switch_fn("🚨 Alerts Dashboard")

    with c6:
        st.markdown("""
        <div class="kpi-card" style="height: 100%; min-height: 185px; display: flex; flex-direction: column; justify-content: space-between; border-top: 3.5px solid #d97706;">
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-size: 1.3rem;">⚖️</span>
                    <span style="font-size: 0.68rem; font-weight: 700; background: #fef3c7; color: #92400e; padding: 2px 6px; border-radius: 4px;">DELTA</span>
                </div>
                <div style="font-weight: 800; font-size: 0.96rem; color: #0f172a;">Raw vs Corrected</div>
                <p style="font-size: 0.78rem; color: #475569; margin: 6px 0; line-height: 1.45;">
                    Direct comparison of raw NWP vs AI post-processed fields showing systematic bias removal and error drops.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚖️ Open Comparison", key="jump_comp"):
            switch_fn("⚖️ Raw vs Corrected")

    with c7:
        st.markdown("""
        <div class="kpi-card" style="height: 100%; min-height: 185px; display: flex; flex-direction: column; justify-content: space-between; border-top: 3.5px solid #0891b2;">
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-size: 1.3rem;">📝</span>
                    <span style="font-size: 0.68rem; font-weight: 700; background: #cffafe; color: #155e75; padding: 2px 6px; border-radius: 4px;">ACTIVE LEARNING</span>
                </div>
                <div style="font-weight: 800; font-size: 0.96rem; color: #0f172a;">Forecaster Feedback</div>
                <p style="font-size: 0.78rem; color: #475569; margin: 6px 0; line-height: 1.45;">
                    Human-in-the-loop operational feedback form for meteorologists to log corrections and retrain AI models.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📝 Open Feedback", key="jump_fb"):
            switch_fn("📝 Forecaster Feedback")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # 3. Recommended Operational Workflow ("How to Use the Website Step-by-Step")
    st.markdown("""
    <div style="background: #ffffff; border: 1.5px solid #bae6fd; border-radius: 14px; padding: 22px 24px; box-shadow: 0 4px 16px rgba(2, 132, 199, 0.06); margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
            <span style="font-size: 1.4rem;">📋</span>
            <div>
                <div style="font-weight: 800; font-size: 1.15rem; color: #0f172a;">How to Use the Website: Daily Forecaster Workflow</div>
                <div style="font-size: 0.84rem; color: #64748b;">Follow this recommended 5-step operational protocol to generate timely and accurate monsoon forecasts</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="background: #0284c7; color: white; font-weight: 800; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">1</div>
                    <div style="font-weight: 700; color: #0f172a; font-size: 0.92rem;">Select Forecast Date & Scope</div>
                </div>
                <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
                    In the left sidebar, choose the active forecast or observation date. You can also preset a minimum rainfall filter to suppress trace amounts and focus on heavy rainfall regions.
                </div>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="background: #0284c7; color: white; font-weight: 800; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">2</div>
                    <div style="font-weight: 700; color: #0f172a; font-size: 0.92rem;">Check the Synoptic Regime</div>
                </div>
                <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
                    Verify today's circulation mode in the sidebar or under <b>Regime Classification</b>. Knowing whether the system is in an Active, Break, or Trough phase establishes the atmospheric moisture context.
                </div>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="background: #0284c7; color: white; font-weight: 800; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">3</div>
                    <div style="font-weight: 700; color: #0f172a; font-size: 0.92rem;">Analyze District & Station Maps</div>
                </div>
                <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
                    Inspect the interactive map. Switch to <b>Satellite</b> or <b>Terrain</b> view. Check point station markers for telemetry and look for districts highlighted with high heavy rain probability P(Heavy) &gt; 40%.
                </div>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="background: #0284c7; color: white; font-weight: 800; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">4</div>
                    <div style="font-weight: 700; color: #0f172a; font-size: 0.92rem;">Inspect Topography & Warnings</div>
                </div>
                <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
                    Under <b>Topography & CartoDEM</b>, evaluate windward slope enhancement. Cross-check the <b>Alerts Dashboard</b> to review Red/Orange warning bulletins and export disaster management notices.
                </div>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="background: #0284c7; color: white; font-weight: 800; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">5</div>
                    <div style="font-weight: 700; color: #0f172a; font-size: 0.92rem;">Log Ground Truth Feedback</div>
                </div>
                <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
                    If Doppler radar or ground automatic weather stations indicate localized departures, submit a quick entry under <b>Forecaster Feedback</b> to continuously refine the AI models.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. IMD Rainfall Scale Reference & Impact Table
    col_t1, col_t2 = st.columns([3, 2])
    with col_t1:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.03);">
            <div style="font-weight: 800; font-size: 1rem; color: #0f172a; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <span>🌧️</span> <span>IMD Official Rainfall Classification & Color Scheme</span>
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.84rem;">
                <thead>
                    <tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0; text-align: left;">
                        <th style="padding: 8px 10px; color: #64748b;">Category</th>
                        <th style="padding: 8px 10px; color: #64748b;">24h Rainfall</th>
                        <th style="padding: 8px 10px; color: #64748b;">Color Code</th>
                        <th style="padding: 8px 10px; color: #64748b;">Typical Operational Impact</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 10px; font-weight: 700;">Light Rain</td>
                        <td style="padding: 8px 10px;">2.5 - 15.5 mm</td>
                        <td style="padding: 8px 10px;"><span style="background: #dcfce7; color: #166534; font-weight: 700; padding: 2px 8px; border-radius: 4px;">🟢 Green</span></td>
                        <td style="padding: 8px 10px; color: #64748b;">Normal agricultural activity</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 10px; font-weight: 700;">Moderate Rain</td>
                        <td style="padding: 8px 10px;">15.6 - 64.4 mm</td>
                        <td style="padding: 8px 10px;"><span style="background: #e0f2fe; color: #0369a1; font-weight: 700; padding: 2px 8px; border-radius: 4px;">🔵 Light Blue</span></td>
                        <td style="padding: 8px 10px; color: #64748b;">Minor urban waterlogging</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 10px; font-weight: 700;">Heavy Rain</td>
                        <td style="padding: 8px 10px;">64.5 - 115.5 mm</td>
                        <td style="padding: 8px 10px;"><span style="background: #ffedd5; color: #c2410c; font-weight: 700; padding: 2px 8px; border-radius: 4px;">🟠 Orange (Alert)</span></td>
                        <td style="padding: 8px 10px; color: #64748b;">Localized flash floods, traffic disruption</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 10px; font-weight: 700;">Very Heavy Rain</td>
                        <td style="padding: 8px 10px;">115.6 - 204.4 mm</td>
                        <td style="padding: 8px 10px;"><span style="background: #fee2e2; color: #b91c1c; font-weight: 700; padding: 2px 8px; border-radius: 4px;">🔴 Red (Critical)</span></td>
                        <td style="padding: 8px 10px; color: #64748b;">Severe flooding, slope failure in hills</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 10px; font-weight: 700;">Extremely Heavy</td>
                        <td style="padding: 8px 10px;">&ge; 204.5 mm</td>
                        <td style="padding: 8px 10px;"><span style="background: #f3e8ff; color: #6b21a8; font-weight: 700; padding: 2px 8px; border-radius: 4px;">🟣 Purple (Severe)</span></td>
                        <td style="padding: 8px 10px; color: #64748b;">Catastrophic flooding; civil evacuation</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col_t2:
        st.markdown("""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; height: 100%;">
            <div style="font-weight: 800; font-size: 1rem; color: #0f172a; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <span>💡</span> <span>Key Concept Cheat Sheet</span>
            </div>
            <div style="font-size: 0.83rem; color: #334155; line-height: 1.6;">
                <div style="margin-bottom: 10px;">
                    <b style="color: #0284c7;">P(Heavy):</b> Exceedance probability that 24h rainfall will cross 64.5mm. Values &gt; 40% warrant immediate Orange alert status.
                </div>
                <div style="margin-bottom: 10px;">
                    <b style="color: #0284c7;">FSS (Fractions Skill Score):</b> Spatial neighborhood metric (0 to 1). Unlike rigid point RMSE, FSS rewards forecasts that capture rain bands even with slight spatial displacement.
                </div>
                <div style="margin-bottom: 10px;">
                    <b style="color: #0284c7;">CartoDEM Orographic Forcing:</b> Fine-scale 30m terrain mesh that extracts vertical air speed <code style="font-size: 0.76rem; background: #e0f2fe; color: #0369a1; padding: 2px 4px; border-radius: 4px;">w = U · ∇h</code>, overcoming raw NWP grid coarseness.
                </div>
                <div>
                    <b style="color: #0284c7;">Synoptic Regimes:</b> The four macro states (Active, Break, Trough, Depression) that dictate whether monsoon rain is uniform, orographic, or convective.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 5. Quick Jump Bottom Action Bar
    st.markdown("""
    <div style="text-align: center; padding: 14px 18px; background: #f0f7ff; border: 1px dashed #bae6fd; border-radius: 12px; margin-bottom: 12px;">
        <span style="font-weight: 700; color: #0369a1; font-size: 0.95rem;">Ready to begin forecast analysis? Jump straight into:</span>
    </div>
    """, unsafe_allow_html=True)

    c_b1, c_b2, c_b3 = st.columns(3)
    with c_b1:
        if st.button("🗺️ Explore Spatial Map & Stations", key="guide_bottom_map"):
            switch_fn("🗺️ District & Station Map")
    with c_b2:
        if st.button("🌀 Check Active Monsoon Regime", key="guide_bottom_regime"):
            switch_fn("🌀 Regime Classification")
    with c_b3:
        if st.button("🚨 Review Extreme Rainfall Alerts", key="guide_bottom_alerts"):
            switch_fn("🚨 Alerts Dashboard")
