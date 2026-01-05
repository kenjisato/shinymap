"""Tests for the MapBuilder (Map) API."""

import pytest

from shinymap import Map
from shinymap.outline import Outline
from shinymap.types import MapBuilder


@pytest.mark.unit
def test_map_builder_basic():
    """Test basic Map builder functionality."""
    geo = Outline.from_dict(
        {"a": ["M0 0 L10 0 L10 10 L0 10 Z"], "b": ["M20 0 L30 0 L30 10 L20 10 Z"]}
    )

    builder = Map(geo)

    assert isinstance(builder, MapBuilder)
    # Access internal state
    assert builder._regions is not None
    assert "a" in builder._regions
    assert "b" in builder._regions
    assert builder._tooltips is None


@pytest.mark.unit
def test_map_builder_with_tooltips():
    """Test Map builder with tooltips."""
    geo = Outline.from_dict({"a": ["M0 0 L10 0 L10 10 L0 10 Z"]})
    tooltips = {"a": "Region A"}

    builder = Map(geo, tooltips=tooltips)

    assert builder._tooltips == tooltips


@pytest.mark.unit
def test_map_builder_method_chaining():
    """Test Map builder method chaining."""
    geo = Outline.from_dict({"a": ["M0 0 L10 0 L10 10 L0 10 Z"]})
    value = {"a": 5}

    builder = Map(geo).with_value(value)

    assert builder._value == value


@pytest.mark.unit
def test_map_builder_with_view_box():
    """Test Map builder with custom viewBox."""
    geo = Outline.from_dict({"a": ["M0 0 L10 0 L10 10 L0 10 Z"]})
    view_box_tuple = (0.0, 0.0, 100.0, 100.0)

    builder = Map(geo).with_view_box(view_box_tuple)
    json_output = builder.as_json()

    # as_json() returns snake_case; JS handles camelCase conversion
    assert json_output["view_box"] == "0.0 0.0 100.0 100.0"


@pytest.mark.unit
def test_map_builder_with_aes():
    """Test Map builder with aesthetic configuration."""
    geo = Outline.from_dict({"a": ["M0 0 L10 0 L10 10 L0 10 Z"]})

    aes_config = {
        "base": {"fillColor": "#e2e8f0"},
        "hover": {"strokeWidth": 2},
    }

    builder = Map(geo).with_aes(aes_config)
    json_output = builder.as_json()

    assert json_output["aes"]["base"]["fillColor"] == "#e2e8f0"
    assert json_output["aes"]["hover"]["strokeWidth"] == 2


@pytest.mark.unit
def test_map_builder_with_layers():
    """Test Map builder with layer configuration."""
    geo = Outline.from_dict({"a": ["M0 0"], "b": ["M10 10"], "overlay": ["M0 0 L10 10"]})

    layers_config = {
        "overlay": ["overlay"],
        "hidden": ["b"],
    }

    builder = Map(geo).with_layers(layers_config)
    json_output = builder.as_json()

    assert json_output["layers"]["overlay"] == ["overlay"]
    assert json_output["layers"]["hidden"] == ["b"]


@pytest.mark.unit
def test_map_as_json():
    """Test Map builder as_json() output."""
    geo = Outline.from_dict({"a": ["M0 0"], "b": ["M10 10"]})

    # Selection is now derived from value > 0 (no separate active param)
    builder = Map(geo, value={"a": 1, "b": 0})
    json_output = builder.as_json()

    # Check that regions is normalized
    assert "regions" in json_output
    # Check that value is included (value > 0 means selected)
    assert json_output["value"] == {"a": 1, "b": 0}


@pytest.mark.unit
def test_build_payload_with_static_outline():
    """Test that _build_payload uses static outline from output_map()."""
    from shinymap._map import MapBuilder
    from shinymap.outline import Outline
    from shinymap.uicore._render_map import _build_payload

    outline = Outline.from_dict({"a": ["M0 0"], "b": ["M10 10"]})
    tooltips = {"a": "Region A", "b": "Region B"}

    # Simulate static params from output_map()
    static_params = {
        "outline": outline,
        "tooltips": tooltips,
        "view_box": (0, 0, 100, 100),
    }

    # Create builder without geometry (simulating Map() with no args)
    builder = MapBuilder(None)

    # Build payload
    payload = _build_payload(builder, static_params)

    # Verify static params were used
    assert "regions" in payload
    assert "a" in payload["regions"]
    assert "b" in payload["regions"]
    assert payload["tooltips"] == tooltips
    assert payload["view_box"] == "0 0 100 100"


@pytest.mark.unit
def test_build_payload_builder_precedence():
    """Test that builder params take precedence over static params."""
    from shinymap._map import MapBuilder
    from shinymap.outline import Outline
    from shinymap.uicore._render_map import _build_payload

    static_outline = Outline.from_dict({"a": ["M0 0"], "b": ["M10 10"]})
    builder_regions = {"x": "M20 20", "y": "M30 30"}

    # Simulate static params from output_map()
    static_params = {
        "outline": static_outline,
        "view_box": (0, 0, 100, 100),
        "tooltips": {"a": "Static tooltip"},
    }

    # Create builder with geometry (should override static)
    builder = MapBuilder(builder_regions, tooltips={"x": "Builder tooltip"})

    # Build payload
    payload = _build_payload(builder, static_params)

    # Builder regions should win
    assert "x" in payload["regions"]
    assert "y" in payload["regions"]
    # Builder tooltips should win
    assert payload["tooltips"] == {"x": "Builder tooltip"}
    # Static view_box should be used (not set in builder)
    assert payload["view_box"] == "0 0 100 100"


class TestValueValidation:
    """Test value validation in Map()."""

    @pytest.mark.unit
    def test_valid_values_pass(self):
        """Valid non-negative integers pass validation."""
        geo = Outline.from_dict({"a": ["M0 0"], "b": ["M10 10"]})

        # Should not raise
        builder = Map(geo, value={"a": 0, "b": 1})
        assert builder._value == {"a": 0, "b": 1}

    @pytest.mark.unit
    def test_negative_value_raises(self):
        """Negative values raise ValueError."""
        geo = Outline.from_dict({"a": ["M0 0"]})

        with pytest.raises(ValueError, match=r"value\['a'\] must be non-negative"):
            Map(geo, value={"a": -1})

    @pytest.mark.unit
    def test_float_value_raises(self):
        """Float values raise ValueError."""
        geo = Outline.from_dict({"a": ["M0 0"]})

        with pytest.raises(ValueError, match=r"value\['a'\] must be an integer"):
            Map(geo, value={"a": 0.5})  # type: ignore

    @pytest.mark.unit
    def test_none_value_passes(self):
        """None value (no value specified) passes validation."""
        geo = Outline.from_dict({"a": ["M0 0"]})

        # Should not raise
        builder = Map(geo, value=None)
        assert builder._value is None
