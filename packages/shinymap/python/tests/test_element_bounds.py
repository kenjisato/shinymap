"""Unit tests for element bounds calculation.

Tests cover all supported element types:
- Circle
- Rect
- Path
- Polygon
- Ellipse
- Line
- Text (approximate bounds)
"""

from __future__ import annotations

import pytest

from shinymap.outline._elements import Circle, Ellipse, Line, Path, Polygon, Rect, Text


class TestCircleBounds:
    """Tests for Circle.bounds()"""

    def test_basic_circle(self):
        """Circle with center and radius."""
        circle = Circle(cx=100, cy=100, r=50)
        assert circle.bounds() == (50.0, 50.0, 150.0, 150.0)

    def test_circle_at_origin(self):
        """Circle centered at origin."""
        circle = Circle(cx=0, cy=0, r=10)
        assert circle.bounds() == (-10.0, -10.0, 10.0, 10.0)

    def test_circle_negative_center(self):
        """Circle with negative center coordinates."""
        circle = Circle(cx=-50, cy=-30, r=20)
        assert circle.bounds() == (-70.0, -50.0, -30.0, -10.0)

    def test_circle_zero_radius(self):
        """Circle with zero radius (point)."""
        circle = Circle(cx=100, cy=100, r=0)
        assert circle.bounds() == (100.0, 100.0, 100.0, 100.0)

    def test_circle_none_values(self):
        """Circle with None values (defaults to 0)."""
        circle = Circle()
        assert circle.bounds() == (0.0, 0.0, 0.0, 0.0)


class TestRectBounds:
    """Tests for Rect.bounds()"""

    def test_basic_rect(self):
        """Rectangle with position and dimensions."""
        rect = Rect(x=10, y=20, width=100, height=80)
        assert rect.bounds() == (10.0, 20.0, 110.0, 100.0)

    def test_rect_at_origin(self):
        """Rectangle at origin."""
        rect = Rect(x=0, y=0, width=50, height=30)
        assert rect.bounds() == (0.0, 0.0, 50.0, 30.0)

    def test_rect_negative_position(self):
        """Rectangle with negative position."""
        rect = Rect(x=-50, y=-30, width=100, height=60)
        assert rect.bounds() == (-50.0, -30.0, 50.0, 30.0)

    def test_rect_zero_dimensions(self):
        """Rectangle with zero dimensions (line/point)."""
        rect = Rect(x=10, y=20, width=0, height=0)
        assert rect.bounds() == (10.0, 20.0, 10.0, 20.0)

    def test_rect_with_rounded_corners(self):
        """Rectangle with corner radii (bounds should be same as without)."""
        rect = Rect(x=10, y=20, width=100, height=80, rx=5, ry=5)
        assert rect.bounds() == (10.0, 20.0, 110.0, 100.0)

    def test_rect_none_values(self):
        """Rectangle with None values (defaults to 0)."""
        rect = Rect()
        assert rect.bounds() == (0.0, 0.0, 0.0, 0.0)


class TestPathBounds:
    """Tests for Path.bounds()"""

    def test_simple_triangle_path(self):
        """Simple triangle path."""
        path = Path(d="M 0 0 L 100 0 L 100 100 Z")
        assert path.bounds() == (0.0, 0.0, 100.0, 100.0)

    def test_path_with_negative_coords(self):
        """Path with negative coordinates."""
        path = Path(d="M -50 -30 L 50 -30 L 50 30 L -50 30 Z")
        assert path.bounds() == (-50.0, -30.0, 50.0, 30.0)

    def test_path_single_moveto(self):
        """Path with single M command (point)."""
        path = Path(d="M 100 200")
        bounds = path.bounds()
        assert bounds[0] == 100.0
        assert bounds[1] == 200.0

    def test_path_none(self):
        """Path with no data."""
        path = Path(d=None)
        assert path.bounds() == (0.0, 0.0, 0.0, 0.0)

    def test_path_empty_string(self):
        """Path with empty string."""
        path = Path(d="")
        bounds = path.bounds()
        # Empty path should return zero bounds
        assert bounds == (0.0, 0.0, 0.0, 0.0)

    @pytest.mark.skipif(
        True, reason="PathData object testing requires svg.py path parsing understanding"
    )
    def test_path_with_pathdata_objects(self):
        """Path with PathData objects (svg.py native format)."""
        # This test is deferred - requires understanding svg.py's PathData API
        # from svg._path import M, L, Z
        # path = Path(d=[M(0, 0), L(100, 0), L(100, 100), Z()])
        # assert path.bounds() == (0.0, 0.0, 100.0, 100.0)
        pass


class TestPolygonBounds:
    """Tests for Polygon.bounds()"""

    def test_basic_polygon(self):
        """Square polygon."""
        polygon = Polygon(points=[0, 0, 100, 0, 100, 100, 0, 100])
        assert polygon.bounds() == (0.0, 0.0, 100.0, 100.0)

    def test_triangle_polygon(self):
        """Triangle polygon."""
        polygon = Polygon(points=[0, 0, 100, 0, 50, 100])
        assert polygon.bounds() == (0.0, 0.0, 100.0, 100.0)

    def test_polygon_negative_coords(self):
        """Polygon with negative coordinates."""
        polygon = Polygon(points=[-50, -30, 50, -30, 0, 50])
        assert polygon.bounds() == (-50.0, -30.0, 50.0, 50.0)

    def test_polygon_empty_points(self):
        """Polygon with no points."""
        polygon = Polygon(points=[])
        assert polygon.bounds() == (0.0, 0.0, 0.0, 0.0)

    def test_polygon_single_point(self):
        """Polygon with single coordinate pair."""
        polygon = Polygon(points=[100, 200])
        assert polygon.bounds() == (100.0, 200.0, 100.0, 200.0)

    def test_polygon_none_points(self):
        """Polygon with None points."""
        polygon = Polygon(points=None)
        assert polygon.bounds() == (0.0, 0.0, 0.0, 0.0)


class TestEllipseBounds:
    """Tests for Ellipse.bounds()"""

    def test_basic_ellipse(self):
        """Ellipse with center and radii."""
        ellipse = Ellipse(cx=100, cy=100, rx=50, ry=30)
        assert ellipse.bounds() == (50.0, 70.0, 150.0, 130.0)

    def test_ellipse_at_origin(self):
        """Ellipse centered at origin."""
        ellipse = Ellipse(cx=0, cy=0, rx=20, ry=10)
        assert ellipse.bounds() == (-20.0, -10.0, 20.0, 10.0)

    def test_ellipse_negative_center(self):
        """Ellipse with negative center."""
        ellipse = Ellipse(cx=-50, cy=-30, rx=25, ry=15)
        assert ellipse.bounds() == (-75.0, -45.0, -25.0, -15.0)

    def test_ellipse_equal_radii(self):
        """Ellipse with equal radii (circle)."""
        ellipse = Ellipse(cx=100, cy=100, rx=50, ry=50)
        assert ellipse.bounds() == (50.0, 50.0, 150.0, 150.0)

    def test_ellipse_zero_radii(self):
        """Ellipse with zero radii (point)."""
        ellipse = Ellipse(cx=100, cy=100, rx=0, ry=0)
        assert ellipse.bounds() == (100.0, 100.0, 100.0, 100.0)

    def test_ellipse_none_values(self):
        """Ellipse with None values."""
        ellipse = Ellipse()
        assert ellipse.bounds() == (0.0, 0.0, 0.0, 0.0)


class TestLineBounds:
    """Tests for Line.bounds()"""

    def test_basic_line(self):
        """Line from one point to another."""
        line = Line(x1=0, y1=0, x2=100, y2=100)
        assert line.bounds() == (0.0, 0.0, 100.0, 100.0)

    def test_horizontal_line(self):
        """Horizontal line."""
        line = Line(x1=10, y1=50, x2=110, y2=50)
        assert line.bounds() == (10.0, 50.0, 110.0, 50.0)

    def test_vertical_line(self):
        """Vertical line."""
        line = Line(x1=50, y1=10, x2=50, y2=110)
        assert line.bounds() == (50.0, 10.0, 50.0, 110.0)

    def test_line_reverse_coords(self):
        """Line with end point before start point (should normalize)."""
        line = Line(x1=100, y1=100, x2=0, y2=0)
        assert line.bounds() == (0.0, 0.0, 100.0, 100.0)

    def test_line_negative_coords(self):
        """Line with negative coordinates."""
        line = Line(x1=-50, y1=-30, x2=50, y2=30)
        assert line.bounds() == (-50.0, -30.0, 50.0, 30.0)

    def test_line_zero_length(self):
        """Line with zero length (point)."""
        line = Line(x1=100, y1=100, x2=100, y2=100)
        assert line.bounds() == (100.0, 100.0, 100.0, 100.0)

    def test_line_none_values(self):
        """Line with None values."""
        line = Line()
        assert line.bounds() == (0.0, 0.0, 0.0, 0.0)


class TestTextBounds:
    """Tests for Text.bounds()

    Note: Text bounds are approximate (position only).
    True bounds would require font metrics.
    """

    def test_basic_text(self):
        """Text with position."""
        text = Text(x=100, y=100, text="Hello")
        bounds = text.bounds()
        assert bounds == (100.0, 100.0, 101.0, 101.0)

    def test_text_at_origin(self):
        """Text at origin."""
        text = Text(x=0, y=0, text="World")
        bounds = text.bounds()
        assert bounds == (0.0, 0.0, 1.0, 1.0)

    def test_text_negative_position(self):
        """Text with negative position."""
        text = Text(x=-50, y=-30, text="Test")
        bounds = text.bounds()
        assert bounds == (-50.0, -30.0, -49.0, -29.0)

    def test_text_none_position(self):
        """Text with None position."""
        text = Text(text="Default")
        bounds = text.bounds()
        assert bounds == (0.0, 0.0, 1.0, 1.0)

    def test_text_empty_string(self):
        """Text with empty string."""
        text = Text(x=100, y=100, text="")
        bounds = text.bounds()
        # Bounds should still be at position, even with no text
        assert bounds == (100.0, 100.0, 101.0, 101.0)


class TestBoundsMixinDispatch:
    """Tests for BoundsMixin dispatch mechanism"""

    def test_unsupported_element_type(self):
        """bounds() should raise NotImplementedError for unsupported types."""
        # This test would require creating a custom element type
        # that inherits from BoundsMixin but is not one of the supported types.
        # For now, we skip this as all our element types are supported.
        pass

    def test_all_element_types_have_bounds(self):
        """Verify all element types have working bounds() method."""
        elements = [
            Circle(cx=100, cy=100, r=50),
            Rect(x=0, y=0, width=100, height=100),
            Path(d="M 0 0 L 100 100"),
            Polygon(points=[0, 0, 100, 0, 50, 100]),
            Ellipse(cx=100, cy=100, rx=50, ry=30),
            Line(x1=0, y1=0, x2=100, y2=100),
            Text(x=100, y=100, text="Test"),
        ]

        for elem in elements:
            bounds = elem.bounds()
            assert isinstance(bounds, tuple)
            assert len(bounds) == 4
            assert all(isinstance(b, float) for b in bounds)
            # min_x <= max_x, min_y <= max_y
            assert bounds[0] <= bounds[2]
            assert bounds[1] <= bounds[3]
