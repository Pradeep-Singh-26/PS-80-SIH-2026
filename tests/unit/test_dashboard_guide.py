"""Unit tests for dashboard guide component and navigation options."""

import pytest
from dashboard.components.guide_component import render_guide_view, render_page_help_banner
from dashboard.web.app import NAV_OPTIONS


def test_nav_options_has_guide_first():
    """Ensure the user guide is the very first option on the left of the navigation bar."""
    assert len(NAV_OPTIONS) >= 7
    assert NAV_OPTIONS[0] == "📖 How to Use & Guide"
    assert "🗺️ District & Station Map" in NAV_OPTIONS
    assert "🌀 Regime Classification" in NAV_OPTIONS
    assert "🛰️ Topography & CartoDEM" in NAV_OPTIONS
    assert "📊 Verification & Skill" in NAV_OPTIONS
    assert "🚨 Alerts Dashboard" in NAV_OPTIONS


def test_render_page_help_banner_callable():
    """Verify page help banner helper is callable with valid view name."""
    called = []

    def mock_switch(target):
        called.append(target)

    # Calling with known page
    render_page_help_banner("🗺️ District & Station Map", mock_switch)
    # Calling with unknown fallback
    render_page_help_banner("Unknown Page", mock_switch)


def test_render_guide_view_callable():
    """Verify render_guide_view can be called with a switch function without crashing."""
    switched_to = []

    def mock_switch(target):
        switched_to.append(target)

    render_guide_view(mock_switch)
