"""Tests for the MapBuilder (Map) API."""

import pytest

from shinymap import Map, MapPayload


@pytest.mark.unit
def test_map_builder_basic():
    """Test basic Map builder functionality."""
    geometry = {"a": "M0 0 L10 0 L10 10 L0 10 Z", "b": "M20 0 L30 0 L30 10 L20 10 Z"}

    map_obj = Map(geometry)
    payload = map_obj.build()

    assert isinstance(payload, MapPayload)
    assert payload.geometry == geometry
    assert payload.tooltips is None
    assert payload.fills is None


@pytest.mark.unit
def test_map_builder_with_tooltips():
    """Test Map builder with tooltips."""
    geometry = {"a": "M0 0 L10 0 L10 10 L0 10 Z"}
    tooltips = {"a": "Region A"}

    map_obj = Map(geometry, tooltips=tooltips)
    payload = map_obj.build()

    assert payload.tooltips == tooltips


@pytest.mark.unit
def test_map_builder_method_chaining():
    """Test Map builder method chaining."""
    geometry = {"a": "M0 0 L10 0 L10 10 L0 10 Z"}
    fills = {"a": "#ff0000"}
    counts = {"a": 5}
    active_ids = ["a"]

    map_obj = (
        Map(geometry)
        .with_fills(fills)
        .with_counts(counts)
        .with_active(active_ids)
        .with_stroke_width(2.0)
    )
    payload = map_obj.build()

    assert payload.fills == fills
    assert payload.counts == counts
    assert payload.active_ids == active_ids
    assert payload.default_aesthetic is not None
    assert payload.default_aesthetic.get("strokeWidth") == 2.0


@pytest.mark.unit
def test_map_builder_with_view_box():
    """Test Map builder with custom viewBox."""
    geometry = {"a": "M0 0 L10 0 L10 10 L0 10 Z"}
    view_box = "0 0 100 100"

    map_obj = Map(geometry).with_view_box(view_box)
    payload = map_obj.build()

    assert payload.view_box == view_box


@pytest.mark.unit
def test_map_payload_creation():
    """Test direct MapPayload creation."""
    geometry = {"a": "M0 0 L10 0 L10 10 L0 10 Z"}
    tooltips = {"a": "Region A"}

    payload = MapPayload(geometry=geometry, tooltips=tooltips)

    assert payload.geometry == geometry
    assert payload.tooltips == tooltips
    assert payload.fills is None
