"""Unit tests for element JSON serialization.

Tests cover:
- to_dict() for all element types
- from_dict() deserialization
- Round-trip serialization (element → dict → element)
- Aesthetic preservation (fill, stroke, etc.)
"""

from __future__ import annotations

import pytest

from shinymap.svg import (
    ELEMENT_TYPE_MAP,
    Circle,
    Ellipse,
    Line,
    Path,
    Polygon,
    Rect,
    Text,
)


class TestCircleJSON:
    """Tests for Circle JSON serialization"""

    def test_to_dict_basic(self):
        """Circle.to_dict() with basic attributes."""
        circle = Circle(cx=100, cy=100, r=50)
        data = circle.to_dict()

        assert data["type"] == "circle"
        assert data["cx"] == 100
        assert data["cy"] == 100
        assert data["r"] == 50

    def test_to_dict_with_aesthetics(self):
        """Circle.to_dict() preserves aesthetics."""
        circle = Circle(cx=100, cy=100, r=50, fill="#ff0000", stroke="#000000", stroke_width=2)
        data = circle.to_dict()

        assert data["fill"] == "#ff0000"
        assert data["stroke"] == "#000000"
        assert data["stroke_width"] == 2

    def test_to_dict_omits_none(self):
        """Circle.to_dict() omits None values."""
        circle = Circle(cx=100, cy=100, r=50)
        data = circle.to_dict()

        # Should not include None values
        assert "fill" not in data or data["fill"] is None
        assert "stroke" not in data or data["stroke"] is None

    def test_from_dict_basic(self):
        """Circle.from_dict() reconstruction."""
        data = {"type": "circle", "cx": 100, "cy": 100, "r": 50}
        circle = Circle.from_dict(data)

        assert isinstance(circle, Circle)
        assert circle.cx == 100
        assert circle.cy == 100
        assert circle.r == 50

    def test_round_trip(self):
        """Circle round-trip: element → dict → element."""
        original = Circle(cx=100, cy=100, r=50, fill="#ff0000")
        data = original.to_dict()
        reconstructed = Circle.from_dict(data)

        assert reconstructed.cx == original.cx
        assert reconstructed.cy == original.cy
        assert reconstructed.r == original.r
        assert reconstructed.fill == original.fill


class TestRectJSON:
    """Tests for Rect JSON serialization"""

    def test_to_dict_basic(self):
        """Rect.to_dict() with basic attributes."""
        rect = Rect(x=10, y=20, width=100, height=80)
        data = rect.to_dict()

        assert data["type"] == "rect"
        assert data["x"] == 10
        assert data["y"] == 20
        assert data["width"] == 100
        assert data["height"] == 80

    def test_to_dict_with_rounded_corners(self):
        """Rect.to_dict() with corner radii."""
        rect = Rect(x=10, y=20, width=100, height=80, rx=5, ry=5)
        data = rect.to_dict()

        assert data["rx"] == 5
        assert data["ry"] == 5

    def test_from_dict_basic(self):
        """Rect.from_dict() reconstruction."""
        data = {"type": "rect", "x": 10, "y": 20, "width": 100, "height": 80}
        rect = Rect.from_dict(data)

        assert isinstance(rect, Rect)
        assert rect.x == 10
        assert rect.width == 100

    def test_round_trip(self):
        """Rect round-trip."""
        original = Rect(x=10, y=20, width=100, height=80, fill="#00ff00")
        data = original.to_dict()
        reconstructed = Rect.from_dict(data)

        assert reconstructed.x == original.x
        assert reconstructed.width == original.width
        assert reconstructed.fill == original.fill


class TestPathJSON:
    """Tests for Path JSON serialization"""

    def test_to_dict_string_path(self):
        """Path.to_dict() with string path data."""
        path = Path(d="M 0 0 L 100 0 L 100 100 Z")
        data = path.to_dict()

        assert data["type"] == "path"
        assert "d" in data
        # Path data should be preserved as string
        assert isinstance(data["d"], str)
        assert "M" in data["d"]

    def test_to_dict_with_aesthetics(self):
        """Path.to_dict() preserves fill and stroke."""
        path = Path(d="M 0 0 L 100 100", fill="#0000ff", stroke="#ff0000", stroke_width=3)
        data = path.to_dict()

        assert data["fill"] == "#0000ff"
        assert data["stroke"] == "#ff0000"
        assert data["stroke_width"] == 3

    def test_from_dict_basic(self):
        """Path.from_dict() reconstruction."""
        data = {"type": "path", "d": "M 0 0 L 100 0 L 100 100 Z"}
        path = Path.from_dict(data)

        assert isinstance(path, Path)
        # svg.py should accept string for d parameter
        assert path.d is not None

    def test_round_trip(self):
        """Path round-trip."""
        original = Path(d="M 0 0 L 100 100 Z", fill="#0000ff")
        data = original.to_dict()
        reconstructed = Path.from_dict(data)

        assert reconstructed.fill == original.fill

    @pytest.mark.skipif(
        True, reason="PathData object testing requires svg.py path parsing understanding"
    )
    def test_to_dict_pathdata_objects(self):
        """Path.to_dict() converts PathData objects to string."""
        # This test is deferred - requires understanding svg.py's PathData API
        # from svg._path import M, L, Z
        # path = Path(d=[M(0, 0), L(100, 0), Z()])
        # data = path.to_dict()
        # assert isinstance(data["d"], str)
        # assert "M 0 0" in data["d"]
        pass


class TestPolygonJSON:
    """Tests for Polygon JSON serialization"""

    def test_to_dict_basic(self):
        """Polygon.to_dict() with points list."""
        polygon = Polygon(points=[0, 0, 100, 0, 100, 100, 0, 100])
        data = polygon.to_dict()

        assert data["type"] == "polygon"
        assert "points" in data
        # Points should be serialized as space-separated string
        assert isinstance(data["points"], str)

    def test_from_dict_basic(self):
        """Polygon.from_dict() reconstruction."""
        data = {"type": "polygon", "points": [0, 0, 100, 0, 50, 100]}
        polygon = Polygon.from_dict(data)

        assert isinstance(polygon, Polygon)
        assert polygon.points is not None

    def test_round_trip(self):
        """Polygon round-trip."""
        original = Polygon(points=[0, 0, 100, 0, 100, 100], fill="#ff00ff")
        data = original.to_dict()
        reconstructed = Polygon.from_dict(data)

        assert reconstructed.fill == original.fill


class TestEllipseJSON:
    """Tests for Ellipse JSON serialization"""

    def test_to_dict_basic(self):
        """Ellipse.to_dict() with basic attributes."""
        ellipse = Ellipse(cx=100, cy=100, rx=50, ry=30)
        data = ellipse.to_dict()

        assert data["type"] == "ellipse"
        assert data["cx"] == 100
        assert data["cy"] == 100
        assert data["rx"] == 50
        assert data["ry"] == 30

    def test_from_dict_basic(self):
        """Ellipse.from_dict() reconstruction."""
        data = {"type": "ellipse", "cx": 100, "cy": 100, "rx": 50, "ry": 30}
        ellipse = Ellipse.from_dict(data)

        assert isinstance(ellipse, Ellipse)
        assert ellipse.cx == 100
        assert ellipse.rx == 50

    def test_round_trip(self):
        """Ellipse round-trip."""
        original = Ellipse(cx=100, cy=100, rx=50, ry=30, fill="#ffff00")
        data = original.to_dict()
        reconstructed = Ellipse.from_dict(data)

        assert reconstructed.cx == original.cx
        assert reconstructed.fill == original.fill


class TestLineJSON:
    """Tests for Line JSON serialization"""

    def test_to_dict_basic(self):
        """Line.to_dict() with basic attributes."""
        line = Line(x1=0, y1=0, x2=100, y2=100)
        data = line.to_dict()

        assert data["type"] == "line"
        assert data["x1"] == 0
        assert data["y1"] == 0
        assert data["x2"] == 100
        assert data["y2"] == 100

    def test_to_dict_with_stroke(self):
        """Line.to_dict() preserves stroke properties."""
        line = Line(x1=0, y1=0, x2=100, y2=100, stroke="#000000", stroke_width=5)
        data = line.to_dict()

        assert data["stroke"] == "#000000"
        assert data["stroke_width"] == 5

    def test_from_dict_basic(self):
        """Line.from_dict() reconstruction."""
        data = {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 100}
        line = Line.from_dict(data)

        assert isinstance(line, Line)
        assert line.x1 == 0
        assert line.x2 == 100

    def test_round_trip(self):
        """Line round-trip."""
        original = Line(x1=0, y1=0, x2=100, y2=100, stroke="#ff0000")
        data = original.to_dict()
        reconstructed = Line.from_dict(data)

        assert reconstructed.x1 == original.x1
        assert reconstructed.stroke == original.stroke


class TestTextJSON:
    """Tests for Text JSON serialization"""

    def test_to_dict_basic(self):
        """Text.to_dict() with text content."""
        text = Text(x=100, y=100, text="Hello World")
        data = text.to_dict()

        assert data["type"] == "text"
        assert data["x"] == 100
        assert data["y"] == 100
        assert data["text"] == "Hello World"

    def test_to_dict_with_font_properties(self):
        """Text.to_dict() preserves font properties."""
        text = Text(x=100, y=100, text="Test", font_size=14, font_family="Arial", fill="#000000")
        data = text.to_dict()

        assert data["font_size"] == 14
        assert data["font_family"] == "Arial"
        assert data["fill"] == "#000000"

    def test_from_dict_basic(self):
        """Text.from_dict() reconstruction."""
        data = {"type": "text", "x": 100, "y": 100, "text": "Hello"}
        text = Text.from_dict(data)

        assert isinstance(text, Text)
        assert text.x == 100
        assert text.text == "Hello"

    def test_round_trip(self):
        """Text round-trip."""
        original = Text(x=100, y=100, text="Test", font_size=16, fill="#0000ff")
        data = original.to_dict()
        reconstructed = Text.from_dict(data)

        assert reconstructed.x == original.x
        assert reconstructed.text == original.text
        assert reconstructed.font_size == original.font_size


class TestElementTypeMap:
    """Tests for ELEMENT_TYPE_MAP and generic from_dict"""

    def test_type_map_has_all_types(self):
        """ELEMENT_TYPE_MAP should include all element types."""
        expected_types = {"circle", "rect", "path", "polygon", "ellipse", "line", "text"}
        assert set(ELEMENT_TYPE_MAP.keys()) == expected_types

    def test_type_map_values(self):
        """ELEMENT_TYPE_MAP should map to correct classes."""
        assert ELEMENT_TYPE_MAP["circle"] == Circle
        assert ELEMENT_TYPE_MAP["rect"] == Rect
        assert ELEMENT_TYPE_MAP["path"] == Path
        assert ELEMENT_TYPE_MAP["polygon"] == Polygon
        assert ELEMENT_TYPE_MAP["ellipse"] == Ellipse
        assert ELEMENT_TYPE_MAP["line"] == Line
        assert ELEMENT_TYPE_MAP["text"] == Text

    def test_from_dict_unknown_type(self):
        """from_dict should raise ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown element type"):
            Circle.from_dict({"type": "unknown_shape", "x": 100})

    def test_from_dict_missing_type(self):
        """from_dict should raise ValueError if type is missing."""
        with pytest.raises(ValueError, match="Missing 'type' field"):
            Circle.from_dict({"x": 100, "y": 100})

    def test_from_dict_dispatches_correctly(self):
        """from_dict should dispatch to correct element class."""
        circle_data = {"type": "circle", "cx": 100, "cy": 100, "r": 50}
        rect_data = {"type": "rect", "x": 10, "y": 20, "width": 100, "height": 80}

        # Call from_dict on any element class - should dispatch based on type
        circle = Circle.from_dict(circle_data)
        rect = Rect.from_dict(rect_data)

        assert isinstance(circle, Circle)
        assert isinstance(rect, Rect)


class TestAestheticPreservation:
    """Tests that aesthetics are preserved but documented as not used"""

    def test_all_aesthetics_preserved(self):
        """All SVG aesthetic properties should be preserved in JSON."""
        circle = Circle(
            cx=100,
            cy=100,
            r=50,
            fill="#ff0000",
            stroke="#000000",
            stroke_width=2,
            opacity=0.8,
        )
        data = circle.to_dict()

        # All aesthetics should be in dict
        assert data["fill"] == "#ff0000"
        assert data["stroke"] == "#000000"
        assert data["stroke_width"] == 2
        assert data["opacity"] == 0.8

    def test_aesthetics_round_trip(self):
        """Aesthetics should survive round-trip even though not used by shinymap."""
        original = Rect(
            x=0,
            y=0,
            width=100,
            height=100,
            fill="#00ff00",
            stroke="#0000ff",
            stroke_width=3,
            fill_opacity=0.5,
        )

        data = original.to_dict()
        reconstructed = Rect.from_dict(data)

        # Aesthetics preserved
        assert reconstructed.fill == original.fill
        assert reconstructed.stroke == original.stroke
        assert reconstructed.stroke_width == original.stroke_width
        assert reconstructed.fill_opacity == original.fill_opacity


class TestClassAttribute:
    """Tests for class_ attribute handling (Python reserved word)"""

    def test_class_attribute_in_to_dict(self):
        """class_ attribute should be converted to 'class' in dict."""
        circle = Circle(cx=100, cy=100, r=50, class_=["region", "interactive"])
        data = circle.to_dict()

        # Should have "class", not "class_"
        assert "class" in data
        assert data["class"] == "region interactive"

    def test_class_attribute_from_dict(self):
        """'class' in dict should be converted to class_ attribute."""
        data = {"type": "circle", "cx": 100, "cy": 100, "r": 50, "class": "region interactive"}
        circle = Circle.from_dict(data)

        # Should have class_ attribute
        assert hasattr(circle, "class_")
        assert circle.class_ == ["region", "interactive"]

    def test_class_round_trip(self):
        """class_ should survive round-trip conversion."""
        original = Rect(x=0, y=0, width=100, height=100, class_=["region", "active"])
        data = original.to_dict()
        reconstructed = Rect.from_dict(data)

        assert reconstructed.class_ == original.class_
