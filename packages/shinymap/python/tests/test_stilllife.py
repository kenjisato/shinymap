"""Tests for the StillLife class."""

import pytest

from shinymap import PARENT, Map, StillLife, Wash, aes
from shinymap.outline import Outline
from shinymap.svg import Circle, Line, Path


class TestStillLifeInit:
    """Test StillLife initialization and validation."""

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
    def test_to_svg_returns_string(self):
        """to_svg() returns SVG string."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "0 0 100 100"},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)
        pic = StillLife(builder)

        svg_str = pic.to_svg()

        assert svg_str is not None
        assert "<svg" in svg_str
        assert "<circle" in svg_str

    @pytest.mark.unit
    def test_to_svg_applies_fill_color(self):
        """to_svg() applies resolved fill color."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "0 0 100 100"},
        )
        wc = Wash(shape=aes.Shape(fill_color="#3b82f6"))

        builder = wc.build(outline)
        pic = StillLife(builder)

        svg_str = pic.to_svg()

        assert 'fill="#3b82f6"' in svg_str

    @pytest.mark.unit
    def test_to_svg_applies_stroke(self):
        """to_svg() applies resolved stroke properties."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "0 0 100 100"},
        )
        wc = Wash(shape=aes.Shape(stroke_color="#000000", stroke_width=2.0))

        builder = wc.build(outline)
        pic = StillLife(builder)

        svg_str = pic.to_svg()

        assert 'stroke="#000000"' in svg_str
        assert 'stroke-width="2.0"' in svg_str

    @pytest.mark.unit
    def test_to_svg_selected_region(self):
        """to_svg() applies select aesthetic for selected regions."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "0 0 100 100"},
        )
        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(fill_color="#e2e8f0"),
                select=aes.Shape(fill_color="#3b82f6"),
            )
        )

        builder = wc.build(outline, value={"a": 1})
        pic = StillLife(builder)

        svg_str = pic.to_svg()

        # Selected region should have select fill color
        assert 'fill="#3b82f6"' in svg_str

    @pytest.mark.unit
    def test_to_svg_hovered_region(self):
        """to_svg() applies hover aesthetic for hovered region."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "0 0 100 100"},
        )
        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(stroke_width=1.0),
                hover=aes.Shape(stroke_width=3.0),
            )
        )

        builder = wc.build(outline)
        pic = StillLife(builder, hovered="a")

        svg_str = pic.to_svg()

        # Hovered region should have hover stroke width
        assert 'stroke-width="3.0"' in svg_str

    @pytest.mark.unit
    def test_to_svg_hidden_region(self):
        """to_svg() excludes hidden regions."""
        outline = Outline(
            regions={
                "visible": [Circle(cx=50, cy=50, r=30)],
                "_hidden": [Circle(cx=150, cy=50, r=30)],
            },
            metadata={"viewBox": "0 0 200 100", "hidden": ["_hidden"]},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)
        pic = StillLife(builder)

        svg_str = pic.to_svg()

        # Only one circle should be present (hidden one excluded)
        assert svg_str.count("<circle") == 1
        assert 'cx="50"' in svg_str  # visible circle
        assert 'cx="150"' not in svg_str  # hidden circle not present

    @pytest.mark.unit
    def test_to_svg_with_path_string(self):
        """to_svg() handles v0.x string path format."""
        outline = Outline.from_dict(
            {
                "a": "M 0 0 L 100 0 L 100 100 L 0 100 Z",
                "_metadata": {"viewBox": "0 0 100 100"},
            }
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)
        pic = StillLife(builder)

        svg_str = pic.to_svg()

        assert "<path" in svg_str
        assert 'fill="#e2e8f0"' in svg_str

    @pytest.mark.unit
    def test_to_svg_writes_to_file(self, tmp_path):
        """to_svg() writes to file when output is provided."""
        outline = Outline(
            regions={"a": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "0 0 100 100"},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

        builder = wc.build(outline)
        pic = StillLife(builder)

        output_file = tmp_path / "test.svg"
        result = pic.to_svg(output=output_file)

        assert result is None
        assert output_file.exists()
        content = output_file.read_text()
        assert "<svg" in content

    @pytest.mark.unit
    def test_to_svg_layer_order(self):
        """to_svg() renders layers in correct order."""
        outline = Outline(
            regions={
                "_bg": [Circle(cx=50, cy=50, r=40)],
                "region": [Circle(cx=50, cy=50, r=30)],
                "_border": [Line(x1=0, y1=0, x2=100, y2=0)],
            },
            metadata={
                "viewBox": "0 0 100 100",
                "underlay": ["_bg"],
                "overlay": ["_border"],
            },
        )
        wc = Wash(
            shape=aes.Shape(fill_color="#e2e8f0"),
            line=aes.Line(stroke_color="#000000"),
        )

        builder = wc.build(outline)
        pic = StillLife(builder)

        svg_str = pic.to_svg()

        # Check all elements are present
        assert svg_str.count("<circle") == 2
        assert "<line" in svg_str

        # Check order: underlay (r=40) < base (r=30) < overlay (line)
        bg_pos = svg_str.index('r="40"')
        region_pos = svg_str.index('r="30"')
        border_pos = svg_str.index("<line")

        assert bg_pos < region_pos < border_pos


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

        builder = wc.build(outline, layers={"overlay": ["_border"]})

        # Layers should be merged into outline
        assert "_border" in builder._outline.overlay_ids()

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


class TestStillLifeIndexed:
    """Cycle/Count/Display with aes.Indexed, mirroring the JS components."""

    PALETTE = ["#000000", "#111111", "#222222"]

    def _outline(self, groups=None):
        meta = {"viewBox": "0 0 100 100"}
        if groups:
            meta["groups"] = groups
        return Outline.from_dict(
            {"a": "M0 0 L10 0 L10 10 Z", "b": "M20 0 L30 0 L30 10 Z", "_metadata": meta}
        )

    @pytest.mark.unit
    def test_cycle_wraps_index(self):
        from shinymap.mode import Cycle

        wc = Wash(shape=aes.Shape(fill_color="#ffffff"))
        mode = Cycle(n=3, aes=aes.Indexed(fill_color=self.PALETTE))
        pic = StillLife(wc.build(self._outline(), mode=mode, value={"a": 4}))

        assert pic.aes("a")["fill_color"] == self.PALETTE[4 % 3]
        assert pic.aes("b")["fill_color"] == self.PALETTE[0]

    @pytest.mark.unit
    def test_count_clamps_to_last_color(self):
        from shinymap.mode import Count

        wc = Wash(shape=aes.Shape(fill_color="#ffffff"))
        mode = Count(aes=aes.Indexed(fill_color=self.PALETTE))
        pic = StillLife(wc.build(self._outline(), mode=mode, value={"a": 10, "b": 1}))

        assert pic.aes("a")["fill_color"] == self.PALETTE[-1]
        assert pic.aes("b")["fill_color"] == self.PALETTE[1]

    @pytest.mark.unit
    def test_indexed_by_group_applies_to_members_only(self):
        from shinymap.mode import Count

        wc = Wash(shape=aes.Shape(fill_color="#ffffff"))
        mode = Count(aes=aes.ByGroup(g=aes.Indexed(fill_color=self.PALETTE)))
        outline = self._outline(groups={"g": ["a"]})
        pic = StillLife(wc.build(outline, mode=mode, value={"a": 2, "b": 2}))

        assert pic.aes("a")["fill_color"] == self.PALETTE[2]
        # Like the JS components: an indexed mode never shows the select look
        assert pic.aes("b")["fill_color"] == "#ffffff"

    @pytest.mark.unit
    def test_indexed_by_group_non_members_get_no_select_look(self):
        from shinymap.mode import Count

        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(fill_color="#ffffff"), select=aes.Shape(fill_color="#ff0000")
            )
        )
        mode = Count(aes=aes.ByGroup(g=aes.Indexed(fill_color=self.PALETTE)))
        outline = self._outline(groups={"g": ["a"]})
        pic = StillLife(wc.build(outline, mode=mode, value={"a": 1, "b": 1}))

        assert pic.aes("b")["fill_color"] == "#ffffff"
        assert "#ff0000" not in pic.to_svg()

    @pytest.mark.unit
    def test_indexed_skips_selection_overlay(self):
        from shinymap.mode import Count

        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(fill_color="#ffffff"), select=aes.Shape(fill_color="#ff0000")
            )
        )
        mode = Count(aes=aes.Indexed(fill_color=self.PALETTE))
        svg_str = StillLife(wc.build(self._outline(), mode=mode, value={"a": 1})).to_svg()

        assert svg_str.count("<path") == 2  # base layer only, no selection copy
        assert "#ff0000" not in svg_str

    @pytest.mark.unit
    def test_hover_keeps_indexed_fill(self):
        from shinymap.mode import Cycle

        wc = Wash(
            shape=aes.ByState(
                base=aes.Shape(fill_color="#ffffff", stroke_width=1),
                hover=aes.Shape(stroke_width=3),
            )
        )
        mode = Cycle(n=3, aes=aes.Indexed(fill_color=self.PALETTE))
        pic = StillLife(wc.build(self._outline(), mode=mode, value={"a": 2}), hovered="a")

        hovered = pic.aes("a")
        assert hovered["fill_color"] == self.PALETTE[2]
        assert hovered["stroke_width"] == 3

    @pytest.mark.unit
    def test_string_mode_is_accepted(self):
        wc = Wash(shape=aes.Shape(fill_color="#ffffff"))
        pic = StillLife(wc.build(self._outline(), mode="single", value={"a": 1}))

        assert pic.aes("b")["fill_color"] == "#ffffff"


class TestStillLifeAnnotation:
    @pytest.mark.unit
    def test_annotation_drawn_last_and_not_in_base(self):
        outline = Outline(
            regions={
                "region": [Circle(cx=50, cy=50, r=30)],
                "label": [Circle(cx=50, cy=50, r=5)],
            },
            metadata={"viewBox": "0 0 100 100", "annotation": ["label"]},
        )
        wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))
        svg_str = StillLife(wc.build(outline), hovered="region").to_svg()

        assert svg_str.count('r="5"') == 1
        # The annotation comes after the hover copy of "region"
        assert svg_str.rindex('r="30"') < svg_str.index('r="5"')


class TestStillLifeCountMaxCount:
    @pytest.mark.unit
    def test_max_count_caps_the_index(self):
        from shinymap.mode import Count

        palette = ["#000000", "#111111", "#222222", "#333333"]
        outline = Outline.from_dict(
            {"a": "M0 0 L10 0 L10 10 Z", "_metadata": {"viewBox": "0 0 10 10"}}
        )
        wc = Wash(shape=aes.Shape(fill_color="#ffffff"))
        mode = Count(max_count=1, aes=aes.Indexed(fill_color=palette))
        pic = StillLife(wc.build(outline, mode=mode, value={"a": 5}))

        assert pic.aes("a")["fill_color"] == palette[1]


class TestStillLifeFromMap:
    """StillLife(Map(...)) draws what @render_map would show."""

    OUTLINE = Outline.from_dict({"a": "M0 0 L10 0 L10 10 Z", "b": "M20 0 L30 0 L30 10 Z"})

    @pytest.fixture(autouse=True)
    def _clean_registry(self):
        from shinymap.uicore._registry import _static_map_params

        yield
        for key in [k for k in _static_map_params if k.startswith("_still_")]:
            del _static_map_params[key]

    @pytest.mark.unit
    def test_map_defaults_to_default_wash(self):
        from shinymap import default_wash

        pic = StillLife(Map(self.OUTLINE, value={"a": 1}))
        expected = StillLife(default_wash.build(self.OUTLINE, value={"a": 1}))
        assert pic.aes("a") == expected.aes("a")
        assert pic.aes("b") == expected.aes("b")

    @pytest.mark.unit
    def test_map_fill_color(self):
        pic = StillLife(Map(self.OUTLINE, fill_color={"a": "#ff0000"}))
        assert pic.aes("a")["fill_color"] == "#ff0000"
        assert pic.aes("b")["fill_color"] != "#ff0000"

    @pytest.mark.unit
    def test_wash(self):
        wc = Wash(shape=aes.Shape(fill_color="#123456"))
        pic = StillLife(Map(self.OUTLINE), wash=wc)
        assert pic.aes("a")["fill_color"] == "#123456"

    @pytest.mark.unit
    def test_map_id_layers_map_over_output_map(self):
        from shinymap import output_map

        output_map("_still_a", self.OUTLINE, aes=aes.ByGroup(a=aes.Shape(stroke_width=3)))
        pic = StillLife(Map(fill_color={"a": "#ff0000"}), map_id="_still_a")
        assert pic.aes("a")["fill_color"] == "#ff0000"
        assert pic.aes("a")["stroke_width"] == 3  # kept from output_map's aes

    @pytest.mark.unit
    def test_map_id_matches_render_map_payload(self):
        from shinymap.uicore._registry import _static_map_params
        from shinymap.uicore._render_map import _build_payload

        wc = Wash(shape=aes.ByState(base=aes.Shape(fill_color="#eeeeee", stroke_width=1)))
        wc.output_map("_still_b", self.OUTLINE, aes=aes.ByGroup(b=aes.Shape(stroke_width=4)))
        builder = Map(fill_color={"a": "#ff0000"})
        payload = _build_payload(builder, _static_map_params["_still_b"])["aes"]
        pic = StillLife(builder, map_id="_still_b")
        for rid in ("a", "b"):
            base = payload.get(rid, payload["__shape"])["base"]
            for key, val in base.items():
                assert pic.aes(rid)[key] == val, (rid, key)

    @pytest.mark.unit
    def test_map_id_takes_wash_without_outline(self):
        wc = Wash(shape=aes.Shape(fill_color="#123456"))
        wc.output_map("_still_c")
        pic = StillLife(Map(self.OUTLINE), map_id="_still_c")
        assert pic.aes("a")["fill_color"] == "#123456"

    @pytest.mark.unit
    def test_map_id_takes_mode(self):
        from shinymap import output_map
        from shinymap.mode import Display

        mode = Display(aes=aes.Indexed(fill_color=["#000000", "#111111", "#222222"]))
        output_map("_still_d", self.OUTLINE, mode=mode)
        pic = StillLife(Map(value={"a": 2}), map_id="_still_d")
        assert pic.aes("a")["fill_color"] == "#222222"

    @pytest.mark.unit
    def test_errors(self):
        wc = Wash(shape=aes.Shape(fill_color="#123456"))
        with pytest.raises(ValueError, match="either"):
            StillLife(Map(self.OUTLINE), wash=wc, map_id="x")
        with pytest.raises(ValueError, match="_still_missing"):
            StillLife(Map(self.OUTLINE), map_id="_still_missing")
        with pytest.raises(ValueError, match="outline"):
            StillLife(Map())
        with pytest.raises(ValueError, match="build"):
            StillLife(wc.build(self.OUTLINE), wash=wc)


class TestStillLifeGeometryMatchesRenderMap:
    """StillLife(Map(...), map_id=) uses the regions, layers and viewBox @render_map sends."""

    OUTLINE = Outline.from_dict(
        {
            "a": "M0 0 L10 0 L10 10 Z",
            "b": "M20 0 L30 0 L30 10 Z",
            "border": "M0 0 L30 0",
            "_metadata": {"overlay": ["border"]},
        }
    )

    @pytest.fixture(autouse=True)
    def _clean_registry(self):
        from shinymap.uicore._registry import _static_map_params

        yield
        for key in [k for k in _static_map_params if k.startswith("_geom_")]:
            del _static_map_params[key]

    def _both(self, builder, map_id, **om_kwargs):
        from shinymap import output_map
        from shinymap.uicore._registry import _static_map_params
        from shinymap.uicore._render_map import _build_payload

        output_map(map_id, **om_kwargs)
        payload = _build_payload(builder, _static_map_params[map_id])
        return payload, StillLife(builder, map_id=map_id)

    @staticmethod
    def _svg_viewbox(pic):
        import re

        return re.search(r'viewBox="([^"]+)"', pic.to_svg()).group(1)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "make_builder, om_kwargs",
        [
            (lambda o: Map(), {"outline": "O", "view_box": (2, 3, 4, 5)}),
            (lambda o: Map(o), {}),
            (lambda o: Map(o), {"outline": "O", "layers": {"hidden": ["b"]}}),
            (lambda o: Map(o, layers={"hidden": ["b"]}), {"outline": "O"}),
            (lambda o: Map(o, view_box=(0, 0, 5, 5)), {"outline": "O", "view_box": (2, 3, 4, 5)}),
        ],
        ids=["om_view_box", "map_outline", "om_layers", "map_layers", "map_view_box"],
    )
    def test_same_regions_layers_viewbox(self, make_builder, om_kwargs, request):
        kwargs = {k: (self.OUTLINE if v == "O" else v) for k, v in om_kwargs.items()}
        map_id = "_geom_" + request.node.callspec.id
        payload, pic = self._both(make_builder(self.OUTLINE), map_id, **kwargs)

        assert sorted(pic._outline.regions) == sorted(payload["regions"])
        assert pic._outline.layers_dict() == payload["layers"]
        assert self._svg_viewbox(pic) == payload["view_box"]
