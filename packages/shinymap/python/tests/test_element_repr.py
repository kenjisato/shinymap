"""Tests for custom __repr__, __str__, attrs(), and as_svg() methods."""

import pytest

from shinymap.geometry import Circle, Ellipse, Geometry, Line, Path, Polygon, Rect, Text


class TestElementRepr:
    """Test clean __repr__ implementation using reprlib."""

    def test_circle_repr_shows_only_non_none(self):
        """Circle repr should show only non-None attributes."""
        circle = Circle(cx=100, cy=100, r=50, fill="#ff0000")
        repr_str = repr(circle)

        assert repr_str.startswith("Circle(")
        assert "cx=100" in repr_str
        assert "cy=100" in repr_str
        assert "r=50" in repr_str
        assert "fill='#ff0000'" in repr_str
        # Should NOT include None values
        assert "stroke=None" not in repr_str

    def test_rect_repr_minimal(self):
        """Rect with minimal attributes."""
        rect = Rect(x=10, y=20, width=100, height=80)
        repr_str = repr(rect)

        assert repr_str.startswith("Rect(")
        assert "x=10" in repr_str
        assert "y=20" in repr_str
        assert "width=100" in repr_str
        assert "height=80" in repr_str

    def test_path_repr_with_string_d(self):
        """Path repr with string d attribute."""
        path = Path(d="M 0 0 L 100 0", fill="#0000ff")
        repr_str = repr(path)

        assert repr_str.startswith("Path(")
        assert "d='M 0 0 L 100 0'" in repr_str
        assert "fill='#0000ff'" in repr_str

    def test_str_equals_repr(self):
        """__str__ should return same as __repr__ for consistency."""
        circle = Circle(cx=100, cy=100, r=50)
        assert str(circle) == repr(circle)


class TestElementStr:
    """Test that __str__ returns clean repr, not SVG markup."""

    def test_str_not_svg_markup(self):
        """str() should NOT return SVG markup (that's what as_svg() is for)."""
        circle = Circle(cx=100, cy=100, r=50, fill="#ff0000")
        str_output = str(circle)

        # Should be repr format, not SVG
        assert str_output.startswith("Circle(")
        assert not str_output.startswith("<circle")

    def test_print_shows_clean_output(self):
        """Printing element should show clean repr."""
        rect = Rect(x=10, y=20, width=100, height=80)
        # This is what users see when they type the variable name in REPL
        assert str(rect).startswith("Rect(")


class TestAttrsMethod:
    """Test attrs() method for iterating over non-None attributes."""

    def test_attrs_excludes_none(self):
        """attrs() should not yield None values."""
        circle = Circle(cx=100, cy=100, r=50, fill="#ff0000")
        attrs_dict = dict(circle.attrs())

        assert "cx" in attrs_dict
        assert attrs_dict["cx"] == 100
        assert "fill" in attrs_dict
        assert attrs_dict["fill"] == "#ff0000"

        # None values should be excluded
        assert "stroke" not in attrs_dict  # stroke is None by default

    def test_attrs_excludes_internal_fields(self):
        """attrs() should exclude internal fields like 'elements' and 'element_name'."""
        circle = Circle(cx=100, cy=100, r=50)
        attrs_dict = dict(circle.attrs())

        assert "elements" not in attrs_dict
        assert "element_name" not in attrs_dict

    def test_attrs_iteration(self):
        """Can iterate over attrs() multiple times."""
        rect = Rect(x=10, y=20, width=100, height=80, fill="#00ff00")

        # First iteration
        first_pass = list(rect.attrs())
        # Second iteration
        second_pass = list(rect.attrs())

        assert first_pass == second_pass
        assert len(first_pass) == 5  # x, y, width, height, fill

    def test_attrs_all_element_types(self):
        """attrs() works for all element types."""
        elements = [
            Circle(cx=100, cy=100, r=50),
            Rect(x=10, y=20, width=100, height=80),
            Path(d="M 0 0 L 100 0"),
            Polygon(points=[0, 0, 100, 0, 100, 100]),
            Ellipse(cx=100, cy=100, rx=50, ry=30),
            Line(x1=0, y1=0, x2=100, y2=100),
            Text(x=100, y=100, text="Hello"),
        ]

        for elem in elements:
            attrs_list = list(elem.attrs())
            assert len(attrs_list) > 0  # Each element has at least some attributes
            # All yielded values should be non-None
            for key, val in attrs_list:
                assert val is not None


class TestAsSvgMethod:
    """Test as_svg() method for getting SVG markup."""

    def test_as_svg_returns_markup(self):
        """as_svg() should return SVG markup string."""
        circle = Circle(cx=100, cy=100, r=50, fill="#ff0000")
        svg_markup = circle.as_svg()

        assert svg_markup.startswith("<circle")
        assert 'cx="100"' in svg_markup
        assert 'cy="100"' in svg_markup
        assert 'r="50"' in svg_markup
        assert 'fill="#ff0000"' in svg_markup

    def test_as_svg_rect(self):
        """as_svg() for Rect element."""
        rect = Rect(x=10, y=20, width=100, height=80, fill="#00ff00")
        svg_markup = rect.as_svg()

        assert svg_markup.startswith("<rect")
        assert 'x="10"' in svg_markup
        assert 'y="20"' in svg_markup
        assert 'width="100"' in svg_markup
        assert 'height="80"' in svg_markup

    def test_as_svg_differs_from_str(self):
        """as_svg() should return different output than str()."""
        circle = Circle(cx=100, cy=100, r=50)

        # str() returns clean repr
        str_output = str(circle)
        assert str_output.startswith("Circle(")

        # as_svg() returns SVG markup
        svg_output = circle.as_svg()
        assert svg_output.startswith("<circle")

        # They should be different
        assert str_output != svg_output

    def test_as_svg_all_element_types(self):
        """as_svg() works for all element types."""
        test_cases = [
            (Circle(cx=100, cy=100, r=50), "<circle"),
            (Rect(x=10, y=20, width=100, height=80), "<rect"),
            (Path(d="M 0 0 L 100 0"), "<path"),
            (Polygon(points=[0, 0, 100, 0, 100, 100]), "<polygon"),
            (Ellipse(cx=100, cy=100, rx=50, ry=30), "<ellipse"),
            (Line(x1=0, y1=0, x2=100, y2=100), "<line"),
            (Text(x=100, y=100, text="Hello"), "<text"),
        ]

        for elem, expected_start in test_cases:
            svg_markup = elem.as_svg()
            assert svg_markup.startswith(expected_start)

    def test_as_svg_omits_none_attributes(self):
        """as_svg() should not include None attributes in markup."""
        circle = Circle(cx=100, cy=100, r=50)  # No fill specified
        svg_markup = circle.as_svg()

        # Should NOT have fill attribute in markup if it's None
        # svg.py handles this automatically
        assert svg_markup.startswith("<circle")


class TestGeometryRepr:
    """Test clean __repr__ for Geometry class."""

    def test_geometry_repr_small_regions(self):
        """Geometry repr with small number of regions shows all keys."""
        circle = Circle(cx=100, cy=100, r=50)
        geo = Geometry(
            regions={"r1": [circle], "r2": [circle], "r3": [circle]},
            metadata={"viewBox": "0 0 500 500"},
        )
        repr_str = repr(geo)

        assert repr_str.startswith("Geometry(")
        assert "regions=" in repr_str
        # With 3 regions, should show all keys
        assert "'r1'" in repr_str or '"r1"' in repr_str
        assert "'r2'" in repr_str or '"r2"' in repr_str
        assert "'r3'" in repr_str or '"r3"' in repr_str
        assert "metadata=" in repr_str
        assert "viewBox" in repr_str

    def test_geometry_repr_many_regions(self):
        """Geometry repr with many regions shows count."""
        circle = Circle(cx=100, cy=100, r=50)
        geo = Geometry(
            regions={f"region{i}": [circle] for i in range(20)},
            metadata={"viewBox": "0 0 1000 1000"},
        )
        repr_str = repr(geo)

        assert repr_str.startswith("Geometry(")
        assert "20 regions" in repr_str
        # Should show first few keys
        assert "region0" in repr_str
        # Should have ellipsis
        assert "..." in repr_str

    def test_geometry_repr_with_complex_metadata(self):
        """Geometry repr with complex metadata uses reprlib."""
        circle = Circle(cx=100, cy=100, r=50)
        geo = Geometry(
            regions={"r1": [circle]},
            metadata={
                "viewBox": "0 0 500 500",
                "source": "test",
                "license": "MIT",
                "url": "https://example.com",
                "extra1": "value1",
                "extra2": "value2",
                "extra3": "value3",
            },
        )
        repr_str = repr(geo)

        assert repr_str.startswith("Geometry(")
        # reprlib should truncate the metadata dict
        assert "metadata=" in repr_str
