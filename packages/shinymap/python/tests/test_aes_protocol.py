"""Tests for aesthetic dict protocol (from_dict/to_dict).

These tests verify:
1. Round-trip conversion: obj.to_dict() -> from_dict(d) preserves data
2. Nested deserialization: Container types correctly deserialize nested dicts
3. Type key presence: All to_dict() outputs include 'type' key
4. Error handling: Missing/invalid type keys raise ValueError
"""

import pytest

from shinymap import aes
from shinymap.aes._core import (
    ByGroup,
    ByState,
    ByType,
    IndexedAesthetic,
    LineAesthetic,
    PathAesthetic,
    ShapeAesthetic,
    TextAesthetic,
    from_dict,
)
from shinymap.types import MISSING


class TestLeafAestheticRoundTrip:
    """Test round-trip conversion for leaf aesthetic types."""

    def test_shape_aesthetic_round_trip(self):
        """ShapeAesthetic should round-trip through dict."""
        original = ShapeAesthetic(
            fill_color="#3b82f6",
            fill_opacity=0.8,
            stroke_color="#1e40af",
            stroke_width=1.5,
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ShapeAesthetic)
        assert restored.fill_color == "#3b82f6"
        assert restored.fill_opacity == 0.8
        assert restored.stroke_color == "#1e40af"
        assert restored.stroke_width == 1.5

    def test_shape_aesthetic_with_none(self):
        """None values should be preserved in round-trip."""
        original = ShapeAesthetic(fill_color="#fff", stroke_color=None)
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ShapeAesthetic)
        assert restored.fill_color == "#fff"
        assert restored.stroke_color is None

    def test_shape_aesthetic_minimal(self):
        """Minimal ShapeAesthetic with only fill_color."""
        original = ShapeAesthetic(fill_color="#fff")
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ShapeAesthetic)
        assert restored.fill_color == "#fff"
        assert isinstance(restored.stroke_color, type(MISSING))

    @pytest.mark.filterwarnings("ignore:Unknown keys.*for Line.*fill_color")
    def test_line_aesthetic_round_trip(self):
        """LineAesthetic should round-trip through dict.

        Note: LineAesthetic.to_dict() includes fill_color=None to indicate
        stroke-only elements. This triggers a warning on from_dict() which
        is expected behavior.
        """
        original = LineAesthetic(
            stroke_color="#94a3b8",
            stroke_width=0.5,
            stroke_dasharray="5,5",
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, LineAesthetic)
        assert restored.stroke_color == "#94a3b8"
        assert restored.stroke_width == 0.5
        assert restored.stroke_dasharray == "5,5"

    def test_line_aesthetic_includes_fill_color_none(self):
        """LineAesthetic.to_dict() should include fill_color=None."""
        original = LineAesthetic(stroke_color="#000")
        d = original.to_dict()

        assert d["fill_color"] is None
        assert d["type"] == "line"

    def test_text_aesthetic_round_trip(self):
        """TextAesthetic should round-trip through dict."""
        original = TextAesthetic(
            fill_color="#0f172a",
            fill_opacity=1.0,
            stroke_color="#ffffff",
            stroke_width=0.5,
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, TextAesthetic)
        assert restored.fill_color == "#0f172a"
        assert restored.fill_opacity == 1.0
        assert restored.stroke_color == "#ffffff"
        assert restored.stroke_width == 0.5

    def test_path_aesthetic_round_trip(self):
        """PathAesthetic should round-trip through dict."""
        original = PathAesthetic(
            kind="line",
            fill_color=None,
            stroke_color="#000000",
            stroke_width=1.0,
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, PathAesthetic)
        assert restored.kind == "line"
        assert restored.fill_color is None
        assert restored.stroke_color == "#000000"
        assert restored.stroke_width == 1.0

    def test_indexed_aesthetic_round_trip(self):
        """IndexedAesthetic should round-trip through dict."""
        original = IndexedAesthetic(
            fill_color=["#e2e8f0", "#fbbf24", "#f97316", "#ef4444"],
            fill_opacity=[0.3, 0.5, 0.7, 1.0],
            stroke_width=1.0,
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, IndexedAesthetic)
        assert restored.fill_color == ["#e2e8f0", "#fbbf24", "#f97316", "#ef4444"]
        assert restored.fill_opacity == [0.3, 0.5, 0.7, 1.0]
        assert restored.stroke_width == 1.0


class TestTypeKeyPresence:
    """Test that all to_dict() outputs include 'type' key."""

    def test_shape_has_type_key(self):
        assert ShapeAesthetic(fill_color="#fff").to_dict()["type"] == "shape"

    def test_line_has_type_key(self):
        assert LineAesthetic(stroke_color="#000").to_dict()["type"] == "line"

    def test_text_has_type_key(self):
        assert TextAesthetic(fill_color="#000").to_dict()["type"] == "text"

    def test_path_has_type_key(self):
        assert PathAesthetic(fill_color="#000").to_dict()["type"] == "path"

    def test_indexed_has_type_key(self):
        assert IndexedAesthetic(fill_color="#000").to_dict()["type"] == "indexed"

    def test_bystate_has_type_key(self):
        aes = ByState(base=ShapeAesthetic(fill_color="#fff"))
        assert aes.to_dict()["type"] == "bystate"

    def test_bytype_has_type_key(self):
        aes = ByType(shape=ShapeAesthetic(fill_color="#fff"))
        assert aes.to_dict()["type"] == "bytype"

    def test_bygroup_has_type_key(self):
        aes = ByGroup(region_a=ShapeAesthetic(fill_color="#fff"))
        assert aes.to_dict()["type"] == "bygroup"


class TestContainerRoundTrip:
    """Test round-trip conversion for container types."""

    def test_bystate_round_trip(self):
        """ByState should round-trip through dict."""
        original = ByState(
            base=ShapeAesthetic(fill_color="#e2e8f0"),
            select=ShapeAesthetic(fill_color="#3b82f6"),
            hover=ShapeAesthetic(stroke_width=2.0),
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ByState)
        assert isinstance(restored.base, ShapeAesthetic)
        assert restored.base.fill_color == "#e2e8f0"
        assert isinstance(restored.select, ShapeAesthetic)
        assert restored.select.fill_color == "#3b82f6"
        assert isinstance(restored.hover, ShapeAesthetic)
        assert restored.hover.stroke_width == 2.0

    def test_bystate_with_none(self):
        """ByState with None values should round-trip."""
        original = ByState(
            base=ShapeAesthetic(fill_color="#fff"),
            hover=None,  # Explicitly disabled
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ByState)
        assert isinstance(restored.base, ShapeAesthetic)
        assert restored.hover is None

    @pytest.mark.filterwarnings("ignore:Unknown keys.*for Line.*fill_color")
    def test_bystate_partial(self):
        """ByState with only base should round-trip.

        Uses LineAesthetic to test different leaf type handling.
        """
        original = ByState(base=LineAesthetic(stroke_color="#000"))
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ByState)
        assert isinstance(restored.base, LineAesthetic)
        assert isinstance(restored.select, type(MISSING))
        assert isinstance(restored.hover, type(MISSING))

    @pytest.mark.filterwarnings("ignore:Unknown keys.*for Line.*fill_color")
    def test_bytype_round_trip(self):
        """ByType should round-trip through dict."""
        original = ByType(
            shape=ShapeAesthetic(fill_color="#f0f9ff"),
            line=LineAesthetic(stroke_color="#0369a1"),
            text=TextAesthetic(fill_color="#0c4a6e"),
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ByType)
        assert isinstance(restored.shape, ShapeAesthetic)
        assert restored.shape.fill_color == "#f0f9ff"
        assert isinstance(restored.line, LineAesthetic)
        assert restored.line.stroke_color == "#0369a1"
        assert isinstance(restored.text, TextAesthetic)
        assert restored.text.fill_color == "#0c4a6e"

    def test_bytype_with_bystate(self):
        """ByType with ByState values should round-trip."""
        original = ByType(
            shape=ByState(
                base=ShapeAesthetic(fill_color="#f0f9ff"),
                hover=ShapeAesthetic(stroke_width=2.0),
            ),
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ByType)
        assert isinstance(restored.shape, ByState)
        assert isinstance(restored.shape.base, ShapeAesthetic)
        assert restored.shape.base.fill_color == "#f0f9ff"

    def test_bygroup_round_trip(self):
        """ByGroup should round-trip through dict."""
        original = ByGroup(
            __all=ShapeAesthetic(fill_color="#e5e7eb"),
            coastal=ShapeAesthetic(fill_color="#3b82f6"),
            mountain=ShapeAesthetic(fill_color="#10b981"),
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ByGroup)
        assert isinstance(restored["__all"], ShapeAesthetic)
        assert restored["__all"].fill_color == "#e5e7eb"
        assert isinstance(restored["coastal"], ShapeAesthetic)
        assert restored["coastal"].fill_color == "#3b82f6"
        assert isinstance(restored["mountain"], ShapeAesthetic)
        assert restored["mountain"].fill_color == "#10b981"

    def test_bygroup_with_bystate(self):
        """ByGroup with ByState values should round-trip."""
        original = ByGroup(
            __all=ByState(
                base=ShapeAesthetic(fill_color="#e5e7eb"),
                hover=ShapeAesthetic(stroke_width=1.5),
            ),
            coastal=ShapeAesthetic(fill_color="#3b82f6"),
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ByGroup)
        assert isinstance(restored["__all"], ByState)
        assert isinstance(restored["__all"].base, ShapeAesthetic)
        assert restored["__all"].base.fill_color == "#e5e7eb"
        assert isinstance(restored["coastal"], ShapeAesthetic)

    def test_bygroup_with_none(self):
        """ByGroup with None values should round-trip."""
        original = ByGroup(
            __all=ShapeAesthetic(fill_color="#e5e7eb"),
            disabled_region=None,
        )
        d = original.to_dict()
        restored = from_dict(d)

        assert isinstance(restored, ByGroup)
        assert restored["disabled_region"] is None


class TestNestedDeserialization:
    """Test deeply nested deserialization."""

    def test_deeply_nested_structure(self):
        """Complex nested structure should deserialize correctly."""
        d = {
            "type": "bygroup",
            "__all": {
                "type": "bystate",
                "base": {"type": "shape", "fill_color": "#e2e8f0"},
                "select": {"type": "shape", "fill_color": "#3b82f6"},
                "hover": {"type": "shape", "stroke_width": 2.0},
            },
            "coastal": {"type": "shape", "fill_color": "#0ea5e9"},
            "mountain": {
                "type": "bystate",
                "base": {"type": "shape", "fill_color": "#10b981"},
            },
        }
        restored = from_dict(d)

        assert isinstance(restored, ByGroup)
        assert isinstance(restored["__all"], ByState)
        assert isinstance(restored["__all"].base, ShapeAesthetic)
        assert restored["__all"].base.fill_color == "#e2e8f0"
        assert isinstance(restored["coastal"], ShapeAesthetic)
        assert restored["coastal"].fill_color == "#0ea5e9"
        assert isinstance(restored["mountain"], ByState)


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_missing_type_key_raises(self):
        """Dict without 'type' key should raise ValueError."""
        with pytest.raises(ValueError, match="must have 'type' key"):
            from_dict({"fill_color": "#fff"})

    def test_unknown_type_raises(self):
        """Dict with unknown 'type' should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown aesthetic type"):
            from_dict({"type": "unknown", "fill_color": "#fff"})

    def test_bystate_with_container_type_raises(self):
        """ByState nested values must be leaf types."""
        with pytest.raises(ValueError, match="Expected leaf aesthetic type"):
            from_dict(
                {
                    "type": "bystate",
                    "base": {"type": "bygroup", "region_a": {"type": "shape"}},
                }
            )


class TestFromDictDirectly:
    """Test using from_dict directly with dict literals."""

    def test_shape_from_dict(self):
        """Create ShapeAesthetic from dict."""
        result = from_dict(
            {
                "type": "shape",
                "fill_color": "#3b82f6",
                "stroke_width": 1.0,
            }
        )
        assert isinstance(result, ShapeAesthetic)
        assert result.fill_color == "#3b82f6"
        assert result.stroke_width == 1.0

    def test_bystate_from_dict(self):
        """Create ByState from dict."""
        result = from_dict(
            {
                "type": "bystate",
                "base": {"type": "shape", "fill_color": "#fff"},
                "hover": {"type": "shape", "stroke_width": 2.0},
            }
        )
        assert isinstance(result, ByState)
        assert isinstance(result.base, ShapeAesthetic)
        assert result.base.fill_color == "#fff"

    def test_bygroup_from_dict(self):
        """Create ByGroup from dict."""
        result = from_dict(
            {
                "type": "bygroup",
                "__all": {"type": "shape", "fill_color": "#e2e8f0"},
                "region_a": {"type": "shape", "fill_color": "#3b82f6"},
            }
        )
        assert isinstance(result, ByGroup)
        assert result["__all"].fill_color == "#e2e8f0"
        assert result["region_a"].fill_color == "#3b82f6"


class TestResolve:
    """Test aesthetic resolution methods."""

    def test_resolve_inherits_missing(self):
        """MISSING values should inherit from parent."""
        parent = ShapeAesthetic(
            fill_color="#fff",
            fill_opacity=0.8,
            stroke_color="#000",
            stroke_width=1.0,
        )
        child = ShapeAesthetic(fill_color="#3b82f6")  # Only fill_color set

        resolved = child.resolve(parent)

        assert resolved.fill_color == "#3b82f6"  # Child value
        assert resolved.fill_opacity == 0.8  # Inherited from parent
        assert resolved.stroke_color == "#000"  # Inherited from parent
        assert resolved.stroke_width == 1.0  # Inherited from parent

    def test_resolve_preserves_none(self):
        """None values should override parent (not inherit)."""
        parent = ShapeAesthetic(fill_color="#fff", stroke_color="#000")
        child = ShapeAesthetic(stroke_color=None)  # Explicit None

        resolved = child.resolve(parent)

        assert resolved.fill_color == "#fff"  # Inherited
        assert resolved.stroke_color is None  # Child's explicit None

    def test_resolve_relative_expr(self):
        """RelativeExpr should resolve against parent value."""
        from shinymap.relative import PARENT

        parent = ShapeAesthetic(stroke_width=1.0)
        child = ShapeAesthetic(stroke_width=PARENT.stroke_width + 2)

        resolved = child.resolve(parent)

        assert resolved.stroke_width == 3.0  # 1.0 + 2

    def test_resolve_relative_expr_multiply(self):
        """RelativeExpr multiplication should work."""
        from shinymap.relative import PARENT

        parent = ShapeAesthetic(stroke_width=2.0)
        child = ShapeAesthetic(stroke_width=PARENT.stroke_width * 1.5)

        resolved = child.resolve(parent)

        assert resolved.stroke_width == 3.0  # 2.0 * 1.5

    def test_resolve_returns_same_type(self):
        """Resolve should return same type as self."""
        parent = LineAesthetic(stroke_color="#000", stroke_width=1.0)
        child = LineAesthetic(stroke_width=2.0)

        resolved = child.resolve(parent)

        assert isinstance(resolved, LineAesthetic)
        assert resolved.stroke_color == "#000"
        assert resolved.stroke_width == 2.0


class TestWashConfigApply:
    """Test WashConfig.apply() method.

    WashConfig.apply() now returns a ByGroup. Access __all entry to get
    the default ByState for all regions.
    """

    def test_apply_single_aesthetic(self):
        """Single aesthetic applies as base, inherits from wash."""
        from shinymap.outline import Outline
        from shinymap.uicore import Wash

        wc = Wash(shape=ShapeAesthetic(fill_color="#e5e7eb", stroke_width=1.0))
        geo = Outline.from_dict({"a": ["M0 0 L10 0 L10 10 Z"]})
        resolved = wc.config.apply(ShapeAesthetic(fill_color="#3b82f6"), geo)

        # Access __all for default ByState
        all_state = resolved["__all"]
        assert all_state.base.fill_color == "#3b82f6"  # User override
        assert all_state.base.stroke_width == 1.0  # Inherited from wash

    def test_apply_bystate_with_all_layers(self):
        """ByState with all layers applies correctly."""
        from shinymap.outline import Outline
        from shinymap.uicore import Wash

        wc = Wash(shape=ShapeAesthetic(fill_color="#e5e7eb", stroke_width=1.0))
        geo = Outline.from_dict({"a": ["M0 0 L10 0 L10 10 Z"]})
        resolved = wc.config.apply(
            ByState(
                base=ShapeAesthetic(fill_color="#3b82f6"),
                select=ShapeAesthetic(fill_color="#1e40af"),
                hover=ShapeAesthetic(stroke_width=2.0),
            ),
            geo,
        )

        all_state = resolved["__all"]
        assert all_state.base.fill_color == "#3b82f6"
        assert all_state.select.fill_color == "#1e40af"
        assert all_state.hover.stroke_width == 2.0

    def test_apply_preserves_relative_expr(self):
        """RelativeExpr in hover is preserved (NOT resolved - JS does that)."""
        from shinymap.outline import Outline
        from shinymap.relative import PARENT, RelativeExpr
        from shinymap.uicore import Wash

        wc = Wash(
            shape=aes.ByState(
                base=ShapeAesthetic(fill_color="#e5e7eb", stroke_width=1.0),
                hover=ShapeAesthetic(stroke_width=PARENT.stroke_width + 1),
            )
        )
        geo = Outline.from_dict({"a": ["M0 0 L10 0 L10 10 Z"]})
        resolved = wc.config.apply(ShapeAesthetic(stroke_width=2.0), geo)

        all_state = resolved["__all"]
        assert all_state.base.stroke_width == 2.0
        # RelativeExpr should be preserved, not resolved
        assert isinstance(all_state.hover.stroke_width, RelativeExpr)

    def test_apply_with_missing(self):
        """MISSING aes returns wash defaults."""
        from shinymap.outline import Outline
        from shinymap.types import MISSING
        from shinymap.uicore import Wash

        wc = Wash(shape=ShapeAesthetic(fill_color="#e5e7eb", stroke_width=1.0))
        geo = Outline.from_dict({"a": ["M0 0 L10 0 L10 10 Z"]})
        resolved = wc.config.apply(MISSING, geo)

        all_state = resolved["__all"]
        assert all_state.base.fill_color == "#e5e7eb"
        assert all_state.base.stroke_width == 1.0

    def test_apply_with_none(self):
        """None aes passes through defaults."""
        from shinymap.outline import Outline
        from shinymap.uicore import Wash

        wc = Wash(shape=ShapeAesthetic(fill_color="#e5e7eb", stroke_width=1.0))
        geo = Outline.from_dict({"a": ["M0 0 L10 0 L10 10 Z"]})
        resolved = wc.config.apply(None, geo)

        all_state = resolved["__all"]
        assert all_state.base.fill_color == "#e5e7eb"


class TestByStateResolveForRegion:
    """Test ByState.resolve_for_region() method."""

    def test_resolve_base_only(self):
        """With no selection/hover, only base layer applies."""
        default = ShapeAesthetic(fill_color="#e5e7eb", stroke_width=1.0)
        states = ByState(base=ShapeAesthetic(fill_color="#3b82f6"))

        resolved = states.resolve_for_region(default)

        assert resolved.fill_color == "#3b82f6"  # From base
        assert resolved.stroke_width == 1.0  # Inherited from default

    def test_resolve_with_selection(self):
        """Selection layer should apply when is_selected=True."""
        default = ShapeAesthetic(fill_color="#e5e7eb", stroke_width=1.0)
        states = ByState(
            base=ShapeAesthetic(fill_color="#3b82f6"),
            select=ShapeAesthetic(fill_color="#1e40af"),
        )

        resolved = states.resolve_for_region(default, is_selected=True)

        assert resolved.fill_color == "#1e40af"  # From select
        assert resolved.stroke_width == 1.0  # Inherited through chain

    def test_resolve_with_hover(self):
        """Hover layer should apply when is_hovered=True."""
        from shinymap.relative import PARENT

        default = ShapeAesthetic(fill_color="#e5e7eb", stroke_width=1.0)
        states = ByState(
            base=ShapeAesthetic(fill_color="#3b82f6"),
            hover=ShapeAesthetic(stroke_width=PARENT.stroke_width + 1),
        )

        resolved = states.resolve_for_region(default, is_hovered=True)

        assert resolved.fill_color == "#3b82f6"  # From base
        assert resolved.stroke_width == 2.0  # 1.0 + 1 from hover

    def test_resolve_full_chain(self):
        """Full chain: default → base → select → hover."""
        from shinymap.relative import PARENT

        default = ShapeAesthetic(
            fill_color="#e5e7eb",
            fill_opacity=1.0,
            stroke_width=1.0,
        )
        states = ByState(
            base=ShapeAesthetic(fill_color="#3b82f6"),
            select=ShapeAesthetic(fill_color="#1e40af", stroke_width=2.0),
            hover=ShapeAesthetic(stroke_width=PARENT.stroke_width + 0.5),
        )

        resolved = states.resolve_for_region(default, is_selected=True, is_hovered=True)

        assert resolved.fill_color == "#1e40af"  # From select
        assert resolved.fill_opacity == 1.0  # From default
        assert resolved.stroke_width == 2.5  # 2.0 (select) + 0.5 (hover)

    def test_resolve_missing_base(self):
        """MISSING base should use default as-is."""
        default = ShapeAesthetic(fill_color="#e5e7eb", stroke_width=1.0)
        states = ByState(hover=ShapeAesthetic(stroke_width=2.0))

        resolved = states.resolve_for_region(default, is_hovered=True)

        assert resolved.fill_color == "#e5e7eb"  # Default unchanged
        assert resolved.stroke_width == 2.0  # From hover

    def test_resolve_none_select_skips_layer(self):
        """None select should be skipped (no effect)."""
        default = ShapeAesthetic(fill_color="#e5e7eb")
        states = ByState(
            base=ShapeAesthetic(fill_color="#3b82f6"),
            select=None,  # Explicitly disabled
        )

        resolved = states.resolve_for_region(default, is_selected=True)

        # Select is None, so it doesn't apply
        assert resolved.fill_color == "#3b82f6"  # From base only
