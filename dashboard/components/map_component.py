"""Folium map component for station/district visualization."""

import folium
import pandas as pd


def _severity_color(rainfall_mm: float) -> str:
    """Map rainfall to a color for map markers."""
    if rainfall_mm >= 204.5:
        return "darkred"
    elif rainfall_mm >= 115.5:
        return "red"
    elif rainfall_mm >= 64.5:
        return "orange"
    elif rainfall_mm >= 15.6:
        return "blue"
    else:
        return "green"


def create_station_map(station_df: pd.DataFrame) -> str:
    """Create a Folium map with station markers.

    Args:
        station_df: DataFrame with columns lat, lon, station_id,
                    corrected_rainfall_mm, rainfall_category, p_heavy, etc.

    Returns:
        HTML string of the rendered Folium map.
    """
    # Center on mean lat/lon
    center_lat = station_df["lat"].mean()
    center_lon = station_df["lon"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles="CartoDB positron",
    )

    for _, row in station_df.iterrows():
        color = _severity_color(row.get("corrected_rainfall_mm", 0))

        popup_html = f"""
        <div style="font-family: Arial; font-size: 13px; min-width: 200px;">
            <b>{row.get('station_id', 'Unknown')}</b><br>
            <hr style="margin: 4px 0;">
            <b>Rainfall:</b> {row.get('corrected_rainfall_mm', 0):.1f} mm
            ({row.get('rainfall_category', 'N/A')})<br>
            <b>P(Heavy):</b> {row.get('p_heavy', 0):.1%}<br>
            <b>P(Very Heavy):</b> {row.get('p_very_heavy', 0):.1%}<br>
            <b>Uncertainty:</b> [{row.get('uncertainty_lower', 0):.2f},
            {row.get('uncertainty_upper', 0):.2f}]<br>
            <b>Regime:</b> {row.get('dominant_regime', 'N/A')}
            (conf: {row.get('regime_confidence', 0):.1%})<br>
            <b>Method:</b> {row.get('correction_method', 'N/A')}
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8 + row.get("corrected_rainfall_mm", 0) / 15,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row.get('station_id', '')}: {row.get('corrected_rainfall_mm', 0):.1f}mm",
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 10px; border-radius: 8px;
                border: 2px solid #ccc; font-size: 12px;">
        <b>Rainfall Category</b><br>
        <i style="color:darkred;">&#9679;</i> Extremely Heavy (>=204.5mm)<br>
        <i style="color:red;">&#9679;</i> Very Heavy (>=115.5mm)<br>
        <i style="color:orange;">&#9679;</i> Heavy (>=64.5mm)<br>
        <i style="color:blue;">&#9679;</i> Moderate (>=15.6mm)<br>
        <i style="color:green;">&#9679;</i> Light / No Rain<br>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m._repr_html_()
