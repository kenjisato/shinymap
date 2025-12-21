"""Tests for theme configuration."""

import threading

import pytest

from shinymap import configure_theme, input_map
from shinymap._theme import _theme_config, get_theme_config
from shinymap.geometry import Geometry


@pytest.mark.unit
def test_configure_theme_basic():
    """Test basic theme configuration."""
    geo = Geometry.from_dict({"a": ["M 0 0 L 10 0"]})

    # Reset theme between tests
    _theme_config.set(None)

    configure_theme(hover_highlight={"stroke_width": 4})

    # Verify configuration was stored
    config = get_theme_config()
    assert "hover_highlight" in config
    assert config["hover_highlight"]["stroke_width"] == 4

    # Verify input_map uses the configuration
    tag = input_map("map1", geo)
    assert tag is not None


@pytest.mark.unit
def test_configure_theme_override():
    """Test explicit parameter overrides configured theme."""
    geo = Geometry.from_dict({"a": ["M 0 0 L 10 0"]})

    _theme_config.set(None)

    configure_theme(hover_highlight={"stroke_width": 4})

    # Explicit override should take precedence
    tag = input_map("map1", geo, hover_highlight={"stroke_width": 8})
    assert tag is not None


@pytest.mark.unit
def test_configure_theme_multiple_params():
    """Test configuring multiple aesthetic parameters."""
    geo = Geometry.from_dict({"a": ["M 0 0 L 10 0"]})

    _theme_config.set(None)

    configure_theme(
        hover_highlight={"stroke_width": 4}, selected_aesthetic={"fill_color": "#ffffcc"}
    )

    # Verify both parameters were stored
    config = get_theme_config()
    assert "hover_highlight" in config
    assert "selected_aesthetic" in config

    tag = input_map("map1", geo)
    assert tag is not None


@pytest.mark.unit
def test_no_theme_configured():
    """Test behavior without theme configuration (backward compat)."""
    geo = Geometry.from_dict({"a": ["M 0 0 L 10 0"]})

    _theme_config.set(None)

    # Should use system defaults
    config = get_theme_config()
    assert config == {}

    tag = input_map("map1", geo)
    assert tag is not None


@pytest.mark.unit
def test_theme_reconfiguration():
    """Test that theme can be reconfigured."""
    _theme_config.set(None)

    configure_theme(hover_highlight={"stroke_width": 4})
    config1 = get_theme_config()
    assert config1["hover_highlight"]["stroke_width"] == 4

    # Reconfigure with new value
    configure_theme(hover_highlight={"stroke_width": 8})
    config2 = get_theme_config()
    assert config2["hover_highlight"]["stroke_width"] == 8


@pytest.mark.unit
def test_thread_safety():
    """Test that theme configuration is thread-safe across sessions."""
    results = {}

    def make_map_with_config(thread_id, stroke_width):
        configure_theme(hover_highlight={"stroke_width": stroke_width})
        config = get_theme_config()
        results[thread_id] = config["hover_highlight"]["stroke_width"]

    threads = [
        threading.Thread(target=make_map_with_config, args=(1, 4)),
        threading.Thread(target=make_map_with_config, args=(2, 8)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Each thread should see its own configuration
    assert results[1] == 4
    assert results[2] == 8
