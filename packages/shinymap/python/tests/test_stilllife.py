"""Tests for the StillLife class."""

import pytest

from shinymap import Map, PARENT, StillLife, Wash, aes
from shinymap.outline import Circle, Line, Outline, Path


class TestStillLifeInit:
    """Test StillLife initialization and validation."""

    @pytest.mark.unit
    def test_requires_builder_from_wash_build(self):
        """StillLife requires a MapBuilder created via WashResult.build()."""
        outline = Outline(regions={"a": [Circle(cx=50, cy=50, r=30)]}, metadata={})

        # Map() creates a MapBuilder without _outline and _resolved_aes
        builder = Map(outline)

        with pytest.raises(ValueError, match="lacks _outline"):
            StillLife(builder)

    @pytest.mark.unit
    def test_accepts_builder_from_wash_build(self):
        """StillLife accepts a MapBuilder created via WashResult.build()."""
        outline = Outline(regions={"a": [Circle(cx=50, cy=50, r=30)]}, metadata={})
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)
        pic = StillLife(builder)

        assert pic._outline is not None
        assert pic._resolved_aes is not None

    @pytest.mark.unit
    def test_value_override(self):
        """StillLife accepts value override."""
        outline = Outline(regions={"a": [Circle(cx=50, cy=50, r=30)]}, metadata={})
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline, value={"a": 1})
        pic = StillLife(builder, value={"a": 0})

        assert pic._value == {"a": 0}

    @pytest.mark.unit
    def test_uses_builder_value_by_default(self):
        """StillLife uses builder's value by default."""
        outline = Outline(regions={"a": [Circle(cx=50, cy=50, r=30)]}, metadata={})
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline, value={"a": 5})
        pic = StillLife(builder)

        assert pic._value == {"a": 5}

    @pytest.mark.unit
    def test_hovered_parameter(self):
        """StillLife accepts hovered parameter."""
        outline = Outline(regions={"a": [Circle(cx=50, cy=50, r=30)]}, metadata={})
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)
        pic = StillLife(builder, hovered="a")

        assert pic._hovered == "a"


class TestStillLifeAes:
    """Test StillLife.aes() method."""

    @pytest.mark.unit
    def test_base_aesthetic(self):
        """Test resolving base aesthetic for unselected region."""
        outline = Outline(
            regions={"a": [Path(d="M 0 0 L 10 0 L 10 10 L 0 10 Z")]},
            metadata={},
        )
        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(fill_color="#e2e8f0", stroke_width=1.0),
                select=aes.Shape(fill_color="#3b82f6"),
            )
        )

        builder = wc.build(outline, value={"a": 0})
        pic = StillLife(builder)

        resolved = pic.aes("a")

        assert resolved["fill_color"] == "#e2e8f0"
        assert resolved["stroke_width"] == 1.0

    @pytest.mark.unit
    def test_select_aesthetic(self):
        """Test resolving select aesthetic for selected region."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(fill_color="#e2e8f0", stroke_width=1.0),
                select=aes.Shape(fill_color="#3b82f6"),
            )
        )

        builder = wc.build(outline, value={"a": 1})
        pic = StillLife(builder)

        resolved = pic.aes("a")

        # fill_color should come from select aesthetic
        assert resolved["fill_color"] == "#3b82f6"
        # stroke_width should inherit from base
        assert resolved["stroke_width"] == 1.0

    @pytest.mark.unit
    def test_hover_aesthetic_from_constructor(self):
        """Test hover aesthetic applied via constructor."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(stroke_width=1.0),
                hover=aes.Shape(stroke_width=3.0),
            )
        )

        builder = wc.build(outline)
        pic = StillLife(builder, hovered="a")

        resolved = pic.aes("a")

        assert resolved["stroke_width"] == 3.0

    @pytest.mark.unit
    def test_hover_aesthetic_from_is_hovered_param(self):
        """Test hover aesthetic applied via is_hovered parameter."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(stroke_width=1.0),
                hover=aes.Shape(stroke_width=3.0),
            )
        )

        builder = wc.build(outline)
        pic = StillLife(builder)

        # Not hovered by default
        resolved_no_hover = pic.aes("a")
        assert resolved_no_hover["stroke_width"] == 1.0

        # Explicitly hovered
        resolved_hovered = pic.aes("a", is_hovered=True)
        assert resolved_hovered["stroke_width"] == 3.0

    @pytest.mark.unit
    def test_multiple_regions_with_different_states(self):
        """Test resolving aesthetics for multiple regions with different states."""
        outline = Outline(
            regions={
                "a": [Circle(cx=50, cy=50, r=30)],
                "b": [Circle(cx=150, cy=50, r=30)],
            },
            metadata={},
        )
        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(fill_color="#e2e8f0"),
                select=aes.Shape(fill_color="#3b82f6"),
            )
        )

        builder = wc.build(outline, value={"a": 1, "b": 0})
        pic = StillLife(builder)

        # a is selected
        assert pic.aes("a")["fill_color"] == "#3b82f6"
        # b is not selected
        assert pic.aes("b")["fill_color"] == "#e2e8f0"

    @pytest.mark.unit
    def test_line_element_type(self):
        """Test resolving aesthetics for line elements."""
        outline = Outline(
            regions={
                "_divider": [Line(x1=0, y1=50, x2=100, y2=50)],
            },
            metadata={},
        )
        wc = Wash(
            line=aes.ByState(
                base=aes.Line(stroke_color="#94a3b8", stroke_width=1.0),
                hover=aes.Line(stroke_width=2.0),
            )
        )

        builder = wc.build(outline)
        pic = StillLife(builder)

        resolved = pic.aes("_divider")

        assert resolved["stroke_color"] == "#94a3b8"
        assert resolved["stroke_width"] == 1.0

    @pytest.mark.unit
    def test_mixed_element_types(self):
        """Test resolving aesthetics for mixed shape and line elements."""
        outline = Outline(
            regions={
                "region_a": [Circle(cx=50, cy=50, r=30)],
                "_border": [Line(x1=0, y1=0, x2=100, y2=0)],
            },
            metadata={},
        )
        wc = Wash(
            shape=aes.Shape(fill_color="#e2e8f0", stroke_width=1.0),
            line=aes.Line(stroke_color="#94a3b8", stroke_width=0.5),
        )

        builder = wc.build(outline)
        pic = StillLife(builder)

        # Shape element should get shape aesthetics
        shape_aes = pic.aes("region_a")
        assert shape_aes["fill_color"] == "#e2e8f0"
        assert shape_aes["stroke_width"] == 1.0

        # Line element should get line aesthetics
        line_aes = pic.aes("_border")
        assert line_aes["stroke_color"] == "#94a3b8"
        assert line_aes["stroke_width"] == 0.5

    @pytest.mark.unit
    def test_relative_expr_resolution(self):
        """Test that PARENT expressions are resolved to concrete values."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(stroke_width=1.0),
                hover=aes.Shape(stroke_width=PARENT.stroke_width + 2),
            )
        )

        builder = wc.build(outline)
        pic = StillLife(builder, hovered="a")

        resolved = pic.aes("a")

        # PARENT.stroke_width + 2 should resolve to 1.0 + 2 = 3.0
        assert resolved["stroke_width"] == 3.0

    @pytest.mark.unit
    def test_relative_expr_with_select_and_hover(self):
        """Test PARENT resolution through select → hover chain."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(stroke_width=1.0),
                select=aes.Shape(stroke_width=2.0),
                hover=aes.Shape(stroke_width=PARENT.stroke_width * 1.5),
            )
        )

        builder = wc.build(outline, value={"a": 1})  # Selected
        pic = StillLife(builder, hovered="a")  # Also hovered

        resolved = pic.aes("a")

        # Chain: base(1.0) → select(2.0) → hover(PARENT * 1.5 = 3.0)
        assert resolved["stroke_width"] == 3.0

    # TODO: resolve_region() always returns ShapeAesthetic for all element types.
    #       Line elements get fill_color/fill_opacity which don't make sense.
    #       See: https://github.com/kenjisato/shinymap/issues/3
    @pytest.mark.unit
    @pytest.mark.xfail(reason="TODO: resolve_region returns ShapeAesthetic for all element types")
    def test_line_element_returns_line_aesthetic(self):
        """Line elements should return LineAesthetic, not ShapeAesthetic."""
        outline = Outline(
            regions={"_divider": [Line(x1=0, y1=50, x2=100, y2=50)]},
            metadata={},
        )
        wc = Wash(line=aes.Line(stroke_color="#94a3b8", stroke_width=1.0))

        builder = wc.build(outline)
        pic = StillLife(builder)

        resolved = pic.aes("_divider")

        # Line aesthetics should NOT have fill_color
        assert "fill_color" not in resolved


class TestStillLifeAesTable:
    """Test StillLife.aes_table() method."""

    @pytest.mark.unit
    def test_all_regions(self):
        """Test getting aesthetics for all regions."""
        outline = Outline(
            regions={
                "a": [Circle(cx=50, cy=50, r=20)],
                "b": [Circle(cx=100, cy=50, r=20)],
                "c": [Circle(cx=150, cy=50, r=20)],
            },
            metadata={},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)
        pic = StillLife(builder)

        table = pic.aes_table()

        assert len(table) == 3
        region_ids = {row["region_id"] for row in table}
        assert region_ids == {"a", "b", "c"}

    @pytest.mark.unit
    def test_specific_regions(self):
        """Test getting aesthetics for specific regions."""
        outline = Outline(
            regions={
                "a": [Circle(cx=50, cy=50, r=20)],
                "b": [Circle(cx=100, cy=50, r=20)],
                "c": [Circle(cx=150, cy=50, r=20)],
            },
            metadata={},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)
        pic = StillLife(builder)

        table = pic.aes_table(region_ids=["a", "c"])

        assert len(table) == 2
        region_ids = {row["region_id"] for row in table}
        assert region_ids == {"a", "c"}

    @pytest.mark.unit
    def test_table_includes_all_properties(self):
        """Test that table rows include all aesthetic properties."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0", stroke_width=1.0))

        builder = wc.build(outline)
        pic = StillLife(builder)

        table = pic.aes_table()

        assert len(table) == 1
        row = table[0]
        assert "region_id" in row
        assert "fill_color" in row
        assert "stroke_width" in row

    @pytest.mark.unit
    def test_table_with_mixed_element_types(self):
        """Test aes_table with mixed shape and line elements."""
        outline = Outline(
            regions={
                "region": [Circle(cx=50, cy=50, r=30)],
                "_line": [Line(x1=0, y1=0, x2=100, y2=0)],
            },
            metadata={},
        )
        wc = Wash(
            shape=aes.Shape(fill_color="#e2e8f0"),
            line=aes.Line(stroke_color="#94a3b8"),
        )

        builder = wc.build(outline)
        pic = StillLife(builder)

        table = pic.aes_table()

        assert len(table) == 2
        # Find each row
        region_row = next(r for r in table if r["region_id"] == "region")
        line_row = next(r for r in table if r["region_id"] == "_line")

        assert region_row["fill_color"] == "#e2e8f0"
        assert line_row["stroke_color"] == "#94a3b8"


class TestStillLifeToSvg:
    """Test StillLife.to_svg() method."""

    @pytest.mark.unit
    def test_to_svg_not_implemented(self):
        """to_svg() raises NotImplementedError (Phase 2)."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)
        pic = StillLife(builder)

        with pytest.raises(NotImplementedError, match="Phase 2"):
            pic.to_svg()


class TestWashResultBuild:
    """Test WashResult.build() method."""

    @pytest.mark.unit
    def test_build_basic(self):
        """Test basic WashResult.build() usage."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)

        assert builder._outline is not None
        assert builder._resolved_aes is not None

    @pytest.mark.unit
    def test_build_with_value(self):
        """Test WashResult.build() with value."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline, value={"a": 5})

        assert builder._value == {"a": 5}

    @pytest.mark.unit
    def test_build_with_tooltips(self):
        """Test WashResult.build() with tooltips."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline, tooltips={"a": "Region A"})

        assert builder._tooltips == {"a": "Region A"}

    @pytest.mark.unit
    def test_build_with_layers(self):
        """Test WashResult.build() with layers."""
        outline = Outline(
            regions={
                "a": [Circle(cx=50, cy=50, r=30)],
                "_border": [Line(x1=0, y1=0, x2=100, y2=0)],
            },
            metadata={},
        )
        wc = Wash(
            shape=aes.Shape(fill_color="#e2e8f0"),
            line=aes.Line(stroke_color="#94a3b8"),
        )

        builder = wc.build(outline, layers={"overlays": ["_border"]})

        # Layers should be merged into outline
        assert "_border" in builder._outline.overlays()

    @pytest.mark.unit
    def test_build_resolves_aes(self):
        """Test that WashResult.build() resolves aesthetics."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={},
        )
        wc = Wash(shape=aes.Shape(fill_color="#custom"))

        builder = wc.build(outline)

        # _resolved_aes should be a ByGroup with __all entry
        assert builder._resolved_aes is not None
        all_entry = builder._resolved_aes.get("__all")
        assert all_entry is not None
        assert all_entry.base.fill_color == "#custom"

    @pytest.mark.unit
    def test_build_with_line_elements(self):
        """Test WashResult.build() with line elements."""
        outline = Outline(
            regions={"_divider": [Line(x1=0, y1=50, x2=100, y2=50)]},
            metadata={},
        )
        wc = Wash(line=aes.Line(stroke_color="#94a3b8", stroke_width=0.5))

        builder = wc.build(outline)

        assert builder._resolved_aes is not None
        line_entry = builder._resolved_aes.get("__line")
        assert line_entry is not None
        assert line_entry.base.stroke_color == "#94a3b8"
