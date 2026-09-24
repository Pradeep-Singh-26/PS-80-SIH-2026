"""Folium map component with multi-mode basemap switcher (Satellite, Terrain, Light Canvas, OSM, Dark)."""

import folium
from folium.plugins import Fullscreen
import pandas as pd


def _severity_color(rainfall_mm: float) -> str:
    """Map rainfall to modern vibrant colors that pop across all basemaps."""
    if rainfall_mm >= 204.5:
        return "#dc2626"  # Extremely heavy (Crimson)
    elif rainfall_mm >= 115.6:
        return "#ea580c"  # Very heavy (Orange Red)
    elif rainfall_mm >= 64.5:
        return "#f59e0b"  # Heavy (Amber)
    elif rainfall_mm >= 15.6:
        return "#0284c7"  # Moderate (Sky Blue)
    elif rainfall_mm > 0.1:
        return "#10b981"  # Light (Emerald)
    else:
        return "#94a3b8"  # Trace / Dry (Slate)


def create_station_map(station_df: pd.DataFrame, default_mode: str = "🛰️ Satellite Imagery") -> str:
    """Create an advanced meteorological map with selectable basemaps (Satellite, Topo, Light, OSM, Dark).

    Args:
        station_df: DataFrame with station observations.
        default_mode: Initial basemap mode ('☀️ Light Canvas', '🛰️ Satellite Imagery', '⛰️ Topography & Terrain', '🗺️ OpenStreetMap', '🌑 Dark Canvas')

    Returns:
        HTML representation of the Folium map.
    """
    if station_df.empty:
        return """
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 40px; text-align: center; color: #64748b;">
            <div style="font-size: 24px; margin-bottom: 8px;">📡</div>
            <div style="font-weight: 600;">No observation station records available for this date.</div>
        </div>
        """

    center_lat = float(station_df["lat"].mean())
    center_lon = float(station_df["lon"].mean())

    # Initialize Folium Map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles=None,
        control_scale=True,
    )

    # 1. Light Gray Canvas Layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
        name="☀️ Light Canvas",
        show=(default_mode == "☀️ Light Canvas"),
        overlay=False,
    ).add_to(m)

    # 2. High-Resolution Satellite Imagery Layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        name="🛰️ Satellite Imagery",
        show=(default_mode == "🛰️ Satellite Imagery"),
        overlay=False,
    ).add_to(m)

    # 3. Topography & Terrain Elevation Layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, USGS, FAO, NPS",
        name="⛰️ Topography & Terrain",
        show=(default_mode == "⛰️ Topography & Terrain"),
        overlay=False,
    ).add_to(m)

    # 4. Standard OpenStreetMap Layer
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺️ OpenStreetMap",
        show=(default_mode == "🗺️ OpenStreetMap"),
        overlay=False,
    ).add_to(m)

    # 5. Dark Canvas Layer (Night Mode)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
        name="🌑 Dark Canvas (Night)",
        show=(default_mode == "🌑 Dark Canvas (Night)"),
        overlay=False,
    ).add_to(m)

    # Hybrid Boundaries & Labels Overlay (available across all layers)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Boundaries &copy; Esri",
        name="🏷️ State Borders & Labels",
        show=True,
        overlay=True,
    ).add_to(m)

    # Add Layer Control to top-left so user can easily switch basemaps directly on the map
    folium.LayerControl(position="topleft", collapsed=False).add_to(m)

    # Fullscreen control on top-right
    Fullscreen(position="topright").add_to(m)

    for _, row in station_df.iterrows():
        rain = float(row.get("corrected_rainfall_mm", 0.0))
        color = _severity_color(rain)
        station_id = str(row.get("station_id", "Station"))
        category = str(row.get("rainfall_category", "N/A")).replace("_", " ").title()
        p_heavy = float(row.get("p_heavy", 0.0))
        p_very_heavy = float(row.get("p_very_heavy", 0.0))
        u_lower = float(row.get("uncertainty_lower", 0.0))
        u_upper = float(row.get("uncertainty_upper", 0.0))
        regime = str(row.get("dominant_regime", "N/A")).replace("_", " ").title()
        conf = float(row.get("regime_confidence", 0.0))
        method = str(row.get("correction_method", "AI Downscaled"))

        popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 12px; color: #0f172a; min-width: 240px; padding: 6px 4px;">
            <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #e0f2fe; padding-bottom: 6px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:{color};"></span>
                    <span style="font-weight: 800; font-size: 14px; color: #0f172a;">{station_id}</span>
                </div>
                <span style="background: #f0f7ff; color: #0284c7; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; border: 1px solid #bae6fd;">{category}</span>
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="color: #64748b; padding: 4px 0;">Corrected Rain:</td>
                    <td style="font-weight: 800; color: #0f172a; text-align: right; font-size: 13px;">{rain:.1f} mm</td>
                </tr>
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="color: #64748b; padding: 4px 0;">P(Heavy &ge;64.5mm):</td>
                    <td style="font-weight: 700; color: {'#dc2626' if p_heavy > 0.4 else '#0f172a'}; text-align: right;">{p_heavy:.1%}</td>
                </tr>
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="color: #64748b; padding: 4px 0;">P(Very Heavy &ge;115.6mm):</td>
                    <td style="font-weight: 700; color: {'#dc2626' if p_very_heavy > 0.3 else '#0f172a'}; text-align: right;">{p_very_heavy:.1%}</td>
                </tr>
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="color: #64748b; padding: 4px 0;">90% CI Uncertainty:</td>
                    <td style="font-family: monospace; font-size: 11px; color: #334155; text-align: right;">[{u_lower:.1f}, {u_upper:.1f}] mm</td>
                </tr>
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="color: #64748b; padding: 4px 0;">Active Regime:</td>
                    <td style="font-weight: 600; color: #0284c7; text-align: right;">{regime} ({conf:.0%})</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 4px 0;">Downscaling:</td>
                    <td style="font-size: 11px; color: #64748b; text-align: right;">{method}</td>
                </tr>
            </table>
        </div>
        """

        radius = max(7, min(20, 7 + (rain / 10)))

        # Outer high-contrast ring
        folium.CircleMarker(
            location=[float(row["lat"]), float(row["lon"])],
            radius=radius + 2.5,
            color="#ffffff",
            weight=2.5,
            fill=False,
        ).add_to(m)

        # Primary data marker
        folium.CircleMarker(
            location=[float(row["lat"]), float(row["lon"])],
            radius=radius,
            color="#0f172a",
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"<b>{station_id}</b>: {rain:.1f} mm ({category})",
        ).add_to(m)

    # Glassmorphic Legend
    legend_html = """
    <div style="position: fixed; bottom: 24px; right: 24px; z-index: 999;
                background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px);
                padding: 14px 18px; border-radius: 12px;
                border: 1px solid #bae6fd; box-shadow: 0 8px 24px rgba(2, 132, 199, 0.15);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 11px; color: #0f172a; line-height: 1.6;">
        <div style="font-weight: 800; color: #0284c7; font-size: 12px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 14px;">🌧️</span>
            <span>IMD Rainfall Intensity Scale</span>
        </div>
        <div style="display: grid; grid-template-columns: 14px 1fr; gap: 5px 10px; align-items: center;">
            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#dc2626; border:1px solid #7f1d1d;"></span>
            <span><b>Extremely Heavy</b> (&ge;204.5 mm)</span>
            
            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#ea580c; border:1px solid #9a3412;"></span>
            <span><b>Very Heavy</b> (115.6 - 204.4 mm)</span>
            
            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#f59e0b; border:1px solid #78350f;"></span>
            <span><b>Heavy</b> (64.5 - 115.5 mm)</span>
            
            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#0284c7; border:1px solid #0369a1;"></span>
            <span><b>Moderate</b> (15.6 - 64.4 mm)</span>
            
            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#10b981; border:1px solid #065f46;"></span>
            <span><b>Light / Trace</b> (0.1 - 15.5 mm)</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m._repr_html_()
