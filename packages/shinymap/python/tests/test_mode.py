"""Tests for Mode classes and serialization.

These tests verify:
1. Mode class serialization (to_dict)
2. Mode normalization (string -> Mode class)
3. _serialize_aes function for IndexedAesthetic
4. Initial value extraction from modes
"""

import pytest

from shinymap import aes
from shinymap.mode import (
    Count,
    Cycle,
    Display,
    Multiple,
    Single,
    _serialize_aes,
    initial_value_from_mode,
    normalize_mode,
)


class TestModeToDict:
    """Test Mode.to_dict() serialization."""

    def test_single_default(self):
        """Single mode with defaults."""
        mode = Single()
        d = mode.to_dict()

        assert d["type"] == "single"
        assert d["allow_deselect"] is True
        assert "selected" not in d
        assert "aes_indexed" not in d

    def test_single_with_selection(self):
        """Single mode with initial selection."""
        mode = Single(selected="region1")
        d = mode.to_dict()

        assert d["type"] == "single"
        assert d["selected"] == "region1"

    def test_single_no_deselect(self):
        """Single mode with deselect disabled."""
        mode = Single(allow_deselect=False)
        d = mode.to_dict()

        assert d["allow_deselect"] is False

    def test_multiple_default(self):
        """Multiple mode with defaults."""
        mode = Multiple()
        d = mode.to_dict()

        assert d["type"] == "multiple"
        assert "selected" not in d
        assert "max_selection" not in d

    def test_multiple_with_selection(self):
        """Multiple mode with initial selection."""
        mode = Multiple(selected=["a", "b", "c"])
        d = mode.to_dict()

        assert d["selected"] == ["a", "b", "c"]

    def test_multiple_with_max(self):
        """Multiple mode with max selection limit."""
        mode = Multiple(max_selection=3)
        d = mode.to_dict()

        assert d["max_selection"] == 3

    def test_count_default(self):
        """Count mode with defaults."""
        mode = Count()
        d = mode.to_dict()

        assert d["type"] == "count"
        assert "values" not in d
        assert "max_count" not in d

    def test_count_with_values(self):
        """Count mode with initial values."""
        mode = Count(values={"a": 5, "b": 3})
        d = mode.to_dict()

        assert d["values"] == {"a": 5, "b": 3}

    def test_count_with_max(self):
        """Count mode with max count."""
        mode = Count(max_count=10)
        d = mode.to_dict()

        assert d["max_count"] == 10

    def test_cycle_basic(self):
        """Cycle mode with n states."""
        mode = Cycle(n=4)
        d = mode.to_dict()

        assert d["type"] == "cycle"
        assert d["n"] == 4
        assert "values" not in d

    def test_cycle_with_values(self):
        """Cycle mode with initial values."""
        mode = Cycle(n=3, values={"a": 1, "b": 2})
        d = mode.to_dict()

        assert d["n"] == 3
        assert d["values"] == {"a": 1, "b": 2}

    def test_cycle_n_must_be_at_least_2(self):
        """Cycle mode requires n >= 2."""
        with pytest.raises(ValueError):
            Cycle(n=1)

    def test_display_default(self):
        """Display mode with defaults."""
        mode = Display()
        d = mode.to_dict()

        assert d["type"] == "display"
        assert "aes_indexed" not in d

    def test_display_with_indexed_aes(self):
        """Display mode with IndexedAesthetic."""
        mode = Display(aes=aes.Indexed(fill_color=["#f3f4f6", "#22c55e", "#f59e0b", "#ef4444"]))
        d = mode.to_dict()

        assert d["type"] == "display"
        assert "aes_indexed" in d
        assert d["aes_indexed"]["fill_color"] == ["#f3f4f6", "#22c55e", "#f59e0b", "#ef4444"]

    def test_display_clickable_default(self):
        """Display mode clickable defaults to False."""
        mode = Display()
        d = mode.to_dict()

        assert d["type"] == "display"
        assert "clickable" not in d  # Not included when False

    def test_display_clickable_true(self):
        """Display mode with clickable=True."""
        mode = Display(clickable=True)
        d = mode.to_dict()

        assert d["type"] == "display"
        assert d["clickable"] is True

    def test_display_with_aes_and_clickable(self):
        """Display mode with both aes and clickable."""
        mode = Display(
            aes=aes.Indexed(fill_color=["#gray", "#green"]),
            clickable=True,
        )
        d = mode.to_dict()

        assert d["type"] == "display"
        assert d["clickable"] is True
        assert d["aes_indexed"]["fill_color"] == ["#gray", "#green"]

    def test_display_get_click_input_id_not_clickable(self):
        """get_click_input_id returns None when not clickable."""
        mode = Display()
        assert mode.get_click_input_id("my_map") is None

    def test_display_get_click_input_id_default(self):
        """get_click_input_id uses {id}_click by default."""
        mode = Display(clickable=True)
        assert mode.get_click_input_id("my_map") == "my_map_click"

    def test_display_get_click_input_id_custom(self):
        """get_click_input_id uses custom input_id if provided."""
        mode = Display(clickable=True, input_id="custom_input")
        assert mode.get_click_input_id("my_map") == "custom_input"

    def test_display_input_id_ignored_when_not_clickable(self):
        """input_id is ignored when clickable=False."""
        mode = Display(clickable=False, input_id="custom_input")
        assert mode.get_click_input_id("my_map") is None


class TestNormalizeMode:
    """Test normalize_mode() function."""

    def test_single_string(self):
        """'single' string normalizes to Single()."""
        result = normalize_mode("single")
        assert isinstance(result, Single)

    def test_multiple_string(self):
        """'multiple' string normalizes to Multiple()."""
        result = normalize_mode("multiple")
        assert isinstance(result, Multiple)

    def test_mode_class_passthrough(self):
        """Mode class instances pass through unchanged."""
        mode = Count(max_count=5)
        result = normalize_mode(mode)
        assert result is mode

    def test_invalid_string_raises(self):
        """Invalid mode string raises ValueError."""
        with pytest.raises(ValueError):
            normalize_mode("invalid")  # type: ignore


class TestInitialValueFromMode:
    """Test initial_value_from_mode() function."""

    def test_single_with_selection(self):
        """Single mode with selection returns value dict."""
        mode = Single(selected="region1")
        result = initial_value_from_mode(mode)
        assert result == {"region1": 1}

    def test_single_without_selection(self):
        """Single mode without selection returns None."""
        mode = Single()
        result = initial_value_from_mode(mode)
        assert result is None

    def test_multiple_with_selection(self):
        """Multiple mode with selection returns value dict."""
        mode = Multiple(selected=["a", "b"])
        result = initial_value_from_mode(mode)
        assert result == {"a": 1, "b": 1}

    def test_multiple_without_selection(self):
        """Multiple mode without selection returns None."""
        mode = Multiple()
        result = initial_value_from_mode(mode)
        assert result is None

    def test_count_with_values(self):
        """Count mode with values returns them."""
        mode = Count(values={"a": 5, "b": 3})
        result = initial_value_from_mode(mode)
        assert result == {"a": 5, "b": 3}

    def test_cycle_with_values(self):
        """Cycle mode with values returns them."""
        mode = Cycle(n=4, values={"a": 2})
        result = initial_value_from_mode(mode)
        assert result == {"a": 2}


class TestSerializeAes:
    """Test _serialize_aes() function for Mode.aes serialization."""

    def test_indexed_aesthetic_direct(self):
        """IndexedAesthetic serializes to direct data (no wrapper)."""
        indexed = aes.Indexed(
            fill_color=["#gray", "#blue", "#green"],
            fill_opacity=[0.3, 0.6, 1.0],
        )
        result = _serialize_aes(indexed)

        # Should NOT have "type" key - direct data for JS
        assert "type" not in result
        # Should have the aesthetic values
        assert result["fill_color"] == ["#gray", "#blue", "#green"]
        assert result["fill_opacity"] == [0.3, 0.6, 1.0]

    def test_indexed_aesthetic_single_value(self):
        """IndexedAesthetic with single values works."""
        indexed = aes.Indexed(fill_color="#orange", fill_opacity=0.5)
        result = _serialize_aes(indexed)

        assert result["fill_color"] == "#orange"
        assert result["fill_opacity"] == 0.5

    def test_bygroup_wrapping_indexed(self):
        """ByGroup wrapping IndexedAesthetic produces byGroup format."""
        by_group = aes.ByGroup(
            group_a=aes.Indexed(fill_color=["#red", "#blue"]),
            group_b=aes.Indexed(fill_color=["#green", "#yellow"]),
        )
        result = _serialize_aes(by_group)

        # Should have type: byGroup
        assert result["type"] == "byGroup"
        assert "groups" in result

        # Each group should have direct data (no nested type)
        assert "type" not in result["groups"]["group_a"]
        assert result["groups"]["group_a"]["fill_color"] == ["#red", "#blue"]
        assert result["groups"]["group_b"]["fill_color"] == ["#green", "#yellow"]


class TestModeWithAes:
    """Test Mode classes with aes parameter."""

    def test_count_with_indexed_aes(self):
        """Count mode with IndexedAesthetic serializes correctly."""
        mode = Count(
            aes=aes.Indexed(
                fill_color=["#e5e7eb", "#fca5a5", "#f87171", "#ef4444", "#dc2626"],
            )
        )
        d = mode.to_dict()

        assert d["type"] == "count"
        assert "aes_indexed" in d
        # aes_indexed should be direct data (no type wrapper)
        assert "type" not in d["aes_indexed"]
        assert d["aes_indexed"]["fill_color"] == [
            "#e5e7eb",
            "#fca5a5",
            "#f87171",
            "#ef4444",
            "#dc2626",
        ]

    def test_cycle_with_indexed_aes(self):
        """Cycle mode with IndexedAesthetic serializes correctly."""
        mode = Cycle(
            n=4,
            aes=aes.Indexed(fill_color=["#gray", "#red", "#yellow", "#green"]),
        )
        d = mode.to_dict()

        assert d["type"] == "cycle"
        assert d["n"] == 4
        assert "aes_indexed" in d
        assert d["aes_indexed"]["fill_color"] == ["#gray", "#red", "#yellow", "#green"]

    def test_single_with_indexed_aes(self):
        """Single mode with IndexedAesthetic serializes correctly."""
        mode = Single(
            aes=aes.Indexed(fill_color=["#e5e7eb", "#3b82f6"]),
        )
        d = mode.to_dict()

        assert d["type"] == "single"
        assert "aes_indexed" in d
        assert d["aes_indexed"]["fill_color"] == ["#e5e7eb", "#3b82f6"]

    def test_multiple_with_bygroup_indexed(self):
        """Multiple mode with ByGroup(IndexedAesthetic) serializes correctly."""
        mode = Multiple(
            aes=aes.ByGroup(
                coastal=aes.Indexed(fill_color=["#bfdbfe", "#2563eb"]),
                inland=aes.Indexed(fill_color=["#bbf7d0", "#16a34a"]),
            )
        )
        d = mode.to_dict()

        assert d["type"] == "multiple"
        assert "aes_indexed" in d
        assert d["aes_indexed"]["type"] == "byGroup"
        assert d["aes_indexed"]["groups"]["coastal"]["fill_color"] == ["#bfdbfe", "#2563eb"]
        assert d["aes_indexed"]["groups"]["inland"]["fill_color"] == ["#bbf7d0", "#16a34a"]


# Mark all tests as unit tests
pytestmark = pytest.mark.unit
