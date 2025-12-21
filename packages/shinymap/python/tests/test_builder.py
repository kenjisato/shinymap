"""Tests for the MapBuilder (Map) API."""

import pytest

from shinymap import Map, MapPayload
from shinymap.geometry import Geometry


@pytest.mark.unit
def test_map_builder_basic():
    """Test basic Map builder functionality."""
    geo = Geometry.from_dict(
        {"a": ["M0 0 L10 0 L10 10 L0 10 Z"], "b": ["M20 0 L30 0 L30 10 L20 10 Z"]}
    )

    map_obj = Map(geo)
    payload = map_obj.build()

    assert isinstance(payload, MapPayload)
    # Geometry is converted to dict format for payload
    assert "a" in payload.geometry
    assert "b" in payload.geometry
    assert payload.tooltips is None
    assert payload.fill_color is None


@pytest.mark.unit
def test_map_builder_with_tooltips():
    """Test Map builder with tooltips."""
    geo = Geometry.from_dict({"a": ["M0 0 L10 0 L10 10 L0 10 Z"]})
    tooltips = {"a": "Region A"}

    map_obj = Map(geo, tooltips=tooltips)
    payload = map_obj.build()

    assert payload.tooltips == tooltips


@pytest.mark.unit
def test_map_builder_method_chaining():
    """Test Map builder method chaining."""
    geo = Geometry.from_dict({"a": ["M0 0 L10 0 L10 10 L0 10 Z"]})
    fill_color = {"a": "#ff0000"}
    counts = {"a": 5}
    active_ids = ["a"]

    map_obj = (
        Map(geo)
        .with_fill_color(fill_color)
        .with_counts(counts)
        .with_active(active_ids)
        .with_stroke_width(2.0)
    )
    payload = map_obj.build()

    assert payload.fill_color == fill_color
    assert payload.counts == counts
    assert payload.active_ids == active_ids
    assert payload.default_aesthetic is not None
    assert payload.default_aesthetic.get("strokeWidth") == 2.0


@pytest.mark.unit
def test_map_builder_with_view_box():
    """Test Map builder with custom viewBox."""
    geo = Geometry.from_dict({"a": ["M0 0 L10 0 L10 10 L0 10 Z"]})
    view_box_tuple = (0.0, 0.0, 100.0, 100.0)
    expected_string = "0.0 0.0 100.0 100.0"

    map_obj = Map(geo).with_view_box(view_box_tuple)
    payload = map_obj.build()

    assert payload.view_box == expected_string


@pytest.mark.unit
def test_map_payload_creation():
    """Test direct MapPayload creation."""
    geometry = {"a": ["M0 0 L10 0 L10 10 L0 10 Z"]}
    tooltips = {"a": "Region A"}

    payload = MapPayload(geometry=geometry, tooltips=tooltips)

    assert payload.geometry == geometry
    assert payload.tooltips == tooltips
    assert payload.fill_color is None


@pytest.mark.unit
def test_fill_color_string_normalization():
    """Test that fill_color parameter accepts both string and dict."""
    geo = Geometry.from_dict({"a": ["M0 0"], "b": ["M10 10"], "c": ["M20 20"]})

    # Test with string fill_color - should normalize to dict
    map_obj = Map(geo).with_fill_color("red")
    payload = map_obj.build()
    json_output = payload.as_json()

    assert json_output["fillColor"] == {"a": "red", "b": "red", "c": "red"}

    # Test with dict fill_color - should pass through unchanged
    fill_color_dict = {"a": "blue", "b": "green", "c": "yellow"}
    map_obj2 = Map(geo).with_fill_color(fill_color_dict)
    payload2 = map_obj2.build()
    json_output2 = payload2.as_json()

    assert json_output2["fillColor"] == fill_color_dict


@pytest.mark.unit
def test_fill_color_merging():
    """Test that multiple with_fill_color() calls merge instead of replace."""
    geo = Geometry.from_dict({"a": ["M0 0"], "b": ["M10 10"], "c": ["M20 20"]})

    # Test base color + override pattern
    map_obj = (
        Map(geo)
        .with_fill_color("#cccccc")  # Base color for all regions
        .with_fill_color({"b": "yellow"})  # Override one region
    )
    payload = map_obj.build()
    json_output = payload.as_json()

    assert json_output["fillColor"] == {"a": "#cccccc", "b": "yellow", "c": "#cccccc"}

    # Test multiple overrides
    map_obj2 = (
        Map(geo)
        .with_fill_color("gray")
        .with_fill_color({"a": "red"})
        .with_fill_color({"b": "blue"})  # Multiple calls should all merge
    )
    payload2 = map_obj2.build()
    json_output2 = payload2.as_json()

    assert json_output2["fillColor"] == {"a": "red", "b": "blue", "c": "gray"}

    # Test that later values override earlier ones
    map_obj3 = Map(geo).with_fill_color({"a": "red"}).with_fill_color({"a": "blue"})
    payload3 = map_obj3.build()
    json_output3 = payload3.as_json()

    assert json_output3["fillColor"]["a"] == "blue"  # Latest value wins


@pytest.mark.unit
def test_map_selection_basic():
    """Test MapSelection basic usage."""
    from shinymap import MapSelection

    geo = Geometry.from_dict({"a": ["M0 0"], "b": ["M10 10"], "c": ["M20 20"]})

    map_obj = (
        MapSelection(geo, selected="b")
        .with_fill_color("#e2e8f0")
        .with_fill_color_selected("#fbbf24")
    )
    payload = map_obj.build()
    json_output = payload.as_json()

    assert json_output["fillColor"] == {"a": "#e2e8f0", "b": "#e2e8f0", "c": "#e2e8f0"}
    assert json_output["activeIds"] == "b"
    assert json_output["fillColorSelected"] == {"fillColor": "#fbbf24"}


@pytest.mark.unit
def test_map_selection_full_aesthetic():
    """Test MapSelection with full aesthetic dict."""
    from shinymap import MapSelection

    geo = Geometry.from_dict({"a": ["M0 0"], "b": ["M10 10"]})

    map_obj = MapSelection(geo, selected="a").with_fill_color_selected(
        {"fillColor": "#fbbf24", "strokeWidth": 2, "strokeColor": "#f59e0b"}
    )
    payload = map_obj.build()
    json_output = payload.as_json()

    assert json_output["fillColorSelected"]["fillColor"] == "#fbbf24"
    assert json_output["fillColorSelected"]["strokeWidth"] == 2


@pytest.mark.unit
def test_map_count_palette():
    """Test MapCount with color palette."""
    from shinymap import MapCount

    geo = Geometry.from_dict({"a": ["M0 0"], "b": ["M10 10"], "c": ["M20 20"]})
    counts = {"a": 0, "b": 1, "c": 2}

    map_obj = MapCount(geo, counts).with_fill_color(["blue", "red", "green"])
    payload = map_obj.build()
    json_output = payload.as_json()

    assert json_output["fillColor"]["a"] == "blue"  # count 0
    assert json_output["fillColor"]["b"] == "red"  # count 1
    assert json_output["fillColor"]["c"] == "green"  # count 2
    assert json_output["counts"] == counts
    assert json_output["countPalette"] == ["blue", "red", "green"]


@pytest.mark.unit
def test_map_count_palette_cycling():
    """Test MapCount palette cycling for counts > palette length."""
    import warnings

    from shinymap import MapCount

    geo = Geometry.from_dict({"a": ["M0 0"], "b": ["M10 10"], "c": ["M20 20"]})
    counts = {"a": 0, "b": 3, "c": 6}  # 3 and 6 cycle back

    # Should issue a warning about cycling
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        map_obj = MapCount(geo, counts).with_fill_color(["blue", "red", "green"])
        assert len(w) == 1
        assert "Colors will cycle" in str(w[0].message)

    payload = map_obj.build()
    json_output = payload.as_json()

    assert json_output["fillColor"]["a"] == "blue"  # 0 % 3 = 0
    assert json_output["fillColor"]["b"] == "blue"  # 3 % 3 = 0
    assert json_output["fillColor"]["c"] == "blue"  # 6 % 3 = 0


@pytest.mark.unit
def test_static_params_merging():
    """Test that _apply_static_params merges static params from output_map()."""
    from shinymap._ui import _apply_static_params, _static_map_params

    geometry = {"a": "M0 0", "b": "M10 10"}
    tooltips = {"a": "Region A", "b": "Region B"}
    viewbox = "0 0 100 100"
    overlay_geom = {"line": "M0 0 L100 100"}
    overlay_style = {"strokeColor": "#999"}

    # Simulate output_map() storing static params
    _static_map_params["test_map"] = {
        "geometry": geometry,
        "tooltips": tooltips,
        "view_box": viewbox,
        "overlay_geometry": overlay_geom,
        "overlay_aesthetic": overlay_style,
    }

    # Create payload without static params
    from shinymap import MapPayload

    payload = MapPayload(
        fill_color={"a": "red", "b": "blue"},  # Dynamic data
    )

    # Apply static params
    merged = _apply_static_params(payload, "test_map")

    # Verify static params were applied
    assert merged.geometry == geometry
    assert merged.tooltips == tooltips
    assert merged.view_box == viewbox
    assert merged.overlay_geometry == overlay_geom
    assert merged.overlay_aesthetic == overlay_style
    # Verify dynamic data preserved
    assert merged.fill_color == {"a": "red", "b": "blue"}

    # Cleanup
    del _static_map_params["test_map"]


@pytest.mark.unit
def test_static_params_builder_precedence():
    """Test that builder params take precedence over static params."""
    from shinymap import MapPayload
    from shinymap._ui import _apply_static_params, _static_map_params

    static_geometry = {"a": "M0 0", "b": "M10 10"}
    builder_geometry = {"x": "M20 20", "y": "M30 30"}

    # Simulate output_map() storing static params
    _static_map_params["test_map2"] = {
        "geometry": static_geometry,
        "view_box": "0 0 100 100",
    }

    # Create payload with builder params (should override static)
    payload = MapPayload(
        geometry=builder_geometry,  # Builder provides geometry
        # view_box not provided - should use static
    )

    # Apply static params
    merged = _apply_static_params(payload, "test_map2")

    # Builder geometry should win
    assert merged.geometry == builder_geometry
    # Static view_box should be used
    assert merged.view_box == "0 0 100 100"

    # Cleanup
    del _static_map_params["test_map2"]
