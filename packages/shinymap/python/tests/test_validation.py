"""Tests for aesthetic validation helpers."""

import warnings

from shinymap._validation import (
    _collect_element_types,
    validate_aesthetic_for_elements,
    validate_geometry_aesthetics,
)
from shinymap.geometry import Geometry


class TestCollectElementTypes:
    """Tests for _collect_element_types()."""

    def test_collect_from_geometry_object(self):
        """Collect element types from Geometry object."""
        geo = Geometry.from_dict(
            {
                "region1": [{"type": "path", "d": "M 0 0 L 10 10"}],
                "region2": [{"type": "circle", "cx": 5, "cy": 5, "r": 2}],
            }
        )
        types = _collect_element_types(geo)
        assert types == {"path", "circle"}

    def test_collect_from_dict(self):
        """Collect element types from raw dict."""
        data = {
            "region1": [{"type": "line", "x1": 0, "y1": 0, "x2": 10, "y2": 10}],
            "region2": [{"type": "rect", "x": 0, "y": 0, "width": 10, "height": 10}],
        }
        types = _collect_element_types(data)
        assert types == {"line", "rect"}

    def test_collect_specific_region(self):
        """Collect element types from specific region only."""
        data = {
            "lines": [{"type": "line", "x1": 0, "y1": 0, "x2": 10, "y2": 10}],
            "shapes": [{"type": "rect", "x": 0, "y": 0, "width": 10, "height": 10}],
        }
        types = _collect_element_types(data, "lines")
        assert types == {"line"}

    def test_collect_mixed_elements_in_region(self):
        """Collect multiple element types from single region."""
        data = {
            "mixed": [
                {"type": "path", "d": "M 0 0 L 10 10"},
                {"type": "circle", "cx": 5, "cy": 5, "r": 2},
            ],
        }
        types = _collect_element_types(data, "mixed")
        assert types == {"path", "circle"}

    def test_collect_skips_metadata(self):
        """Metadata keys starting with _ are skipped."""
        data = {
            "_metadata": {"viewBox": "0 0 100 100"},
            "region1": [{"type": "path", "d": "M 0 0 L 10 10"}],
        }
        types = _collect_element_types(data)
        assert types == {"path"}

    def test_collect_nonexistent_region(self):
        """Non-existent region returns empty set."""
        data = {"region1": [{"type": "path", "d": "M 0 0 L 10 10"}]}
        types = _collect_element_types(data, "nonexistent")
        assert types == set()

    def test_collect_normalizes_case(self):
        """Element types are normalized to lowercase."""
        data = {
            "region1": [
                {"type": "PATH", "d": "M 0 0 L 10 10"},
                {"type": "Circle", "cx": 5, "cy": 5, "r": 2},
            ],
        }
        types = _collect_element_types(data)
        assert types == {"path", "circle"}


class TestValidateAestheticForElements:
    """Tests for validate_aesthetic_for_elements()."""

    def test_no_warning_for_shape_with_fill(self):
        """No warning when fill is applied to shapes."""
        aesthetic = {"fill_color": "#fff", "stroke_color": "#000"}
        element_types = {"path", "rect"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_aesthetic_for_elements(aesthetic, element_types)
            assert len(w) == 0

    def test_warning_for_line_with_fill(self):
        """Warning when fill is applied to line-only region."""
        aesthetic = {"fill_color": "#fff"}
        element_types = {"line"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_aesthetic_for_elements(aesthetic, element_types)
            assert len(w) == 1
            assert "fill_color" in str(w[0].message)
            assert "Line elements" in str(w[0].message)

    def test_no_warning_for_line_with_stroke_only(self):
        """No warning when only stroke is applied to lines."""
        aesthetic = {"stroke_color": "#000", "stroke_width": 2}
        element_types = {"line"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_aesthetic_for_elements(aesthetic, element_types)
            assert len(w) == 0

    def test_no_warning_for_line_with_fill_none(self):
        """No warning when fill_color=None (transparent) on lines."""
        aesthetic = {"fill_color": None}
        element_types = {"line"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_aesthetic_for_elements(aesthetic, element_types)
            assert len(w) == 0

    def test_no_warning_for_mixed_elements(self):
        """No warning for mixed element types (some might use fill)."""
        aesthetic = {"fill_color": "#fff"}
        element_types = {"line", "path"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_aesthetic_for_elements(aesthetic, element_types)
            assert len(w) == 0

    def test_no_warning_for_text_with_stroke(self):
        """No warning for text with stroke (text outline is valid)."""
        aesthetic = {"stroke_color": "#000", "stroke_width": 1}
        element_types = {"text"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_aesthetic_for_elements(aesthetic, element_types)
            assert len(w) == 0

    def test_no_warning_for_none_aesthetic(self):
        """No warning when aesthetic is None."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_aesthetic_for_elements(None, {"line"})
            assert len(w) == 0

    def test_context_included_in_warning(self):
        """Context string is included in warning message."""
        aesthetic = {"fill_color": "#fff"}
        element_types = {"line"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_aesthetic_for_elements(aesthetic, element_types, context="region 'grid_lines'")
            assert len(w) == 1
            assert "region 'grid_lines'" in str(w[0].message)

    def test_camel_case_fill_keys(self):
        """Warning for camelCase fill keys (fillColor, fillOpacity)."""
        aesthetic = {"fillColor": "#fff", "fillOpacity": 0.5}
        element_types = {"line"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_aesthetic_for_elements(aesthetic, element_types)
            assert len(w) == 1
            assert "fillColor" in str(w[0].message) or "fillOpacity" in str(w[0].message)


class TestValidateGeometryAesthetics:
    """Tests for validate_geometry_aesthetics()."""

    def test_validates_default_aesthetic(self):
        """Validates default aesthetic against geometry."""
        geo = Geometry.from_dict(
            {
                "lines": [{"type": "line", "x1": 0, "y1": 0, "x2": 10, "y2": 10}],
            }
        )
        default_aes = {"fill_color": "#fff"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_geometry_aesthetics(geo, default_aesthetic=default_aes)
            assert len(w) == 1
            assert "lines" in str(w[0].message)

    def test_validates_group_aesthetics(self):
        """Validates per-group aesthetics."""
        geo = Geometry.from_dict(
            {
                "_metadata": {"groups": {"grid": ["grid_h", "grid_v"]}},
                "grid_h": [{"type": "line", "x1": 0, "y1": 50, "x2": 100, "y2": 50}],
                "grid_v": [{"type": "line", "x1": 50, "y1": 0, "x2": 50, "y2": 100}],
                "region1": [{"type": "path", "d": "M 0 0 L 10 10 Z"}],
            }
        )
        aes_group = {"grid": {"fill_color": "#fff", "stroke_color": "#ddd"}}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_geometry_aesthetics(geo, aes_group=aes_group)
            # Should warn for grid_h and grid_v
            assert len(w) == 2

    def test_no_warning_for_valid_aesthetics(self):
        """No warning when aesthetics are appropriate."""
        geo = Geometry.from_dict(
            {
                "_metadata": {"groups": {"grid": ["grid_h"]}},
                "grid_h": [{"type": "line", "x1": 0, "y1": 50, "x2": 100, "y2": 50}],
                "region1": [{"type": "path", "d": "M 0 0 L 10 10 Z"}],
            }
        )
        aes_group = {"grid": {"stroke_color": "#ddd", "stroke_width": 1}}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_geometry_aesthetics(geo, aes_group=aes_group)
            assert len(w) == 0
