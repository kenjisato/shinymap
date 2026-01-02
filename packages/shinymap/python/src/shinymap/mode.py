"""Mode classes for advanced input_map customization.

This module provides Mode classes for power users who need fine-grained control
over selection behavior and aesthetics. For most use cases, the simple string
modes ("single", "multiple") or sugar functions (input_radio_buttons,
input_checkbox_group) are recommended.

Two-Tier API:
    Tier 1 (Simple): mode="single", mode="multiple" (permanent, primary API)
    Tier 2 (Advanced): Mode classes for customization

Usage:
    >>> from shinymap import input_map, aes
    >>> from shinymap.mode import Single, Multiple, Cycle, Count
    >>>
    >>> # Multiple with selection limit
    >>> input_map("regions", outline, mode=Multiple(max_selection=3))
    >>>
    >>> # Cycle mode with custom palette (e.g., traffic light survey)
    >>> input_map(
    ...     "rating",
    ...     outline,
    ...     mode=Cycle(
    ...         n=4,
    ...         aes=aes.Indexed(
    ...             fill_color=["#e2e8f0", "#ef4444", "#eab308", "#22c55e"],
    ...         ),
    ...     ),
    ... )
    >>>
    >>> # Per-group palettes (e.g., color coordination quiz)
    >>> input_map(
    ...     "quiz",
    ...     outline,
    ...     mode=Cycle(
    ...         n=2,
    ...         aes=aes.ByGroup(
    ...             question_1=aes.Indexed(fill_color=["#bfdbfe", "#2563eb"]),
    ...             question_2=aes.Indexed(fill_color=["#bbf7d0", "#16a34a"]),
    ...         ),
    ...     ),
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .aes._core import ByGroup, IndexedAesthetic


@dataclass
class Single:
    """Single selection mode with customization options.

    Use when you need options beyond the simple mode="single" string:
    - Initial selection
    - Disable deselection
    - Custom two-state aesthetics

    Args:
        selected: Initially selected region ID.
        allow_deselect: If True (default), clicking selected region deselects it.
        aes: Two-state aesthetic [unselected, selected].
             Can be aes.Indexed (global) or aes.ByGroup wrapping aes.Indexed.

    Example:
        >>> from shinymap.mode import Single
        >>> from shinymap import aes
        >>>
        >>> # Pre-select a region
        >>> mode = Single(selected="region_a")
        >>>
        >>> # Disable deselection (must always have one selected)
        >>> mode = Single(allow_deselect=False)
        >>>
        >>> # Custom selection colors
        >>> mode = Single(
        ...     aes=aes.Indexed(
        ...         fill_color=["#e5e7eb", "#3b82f6"],  # gray -> blue
        ...     )
        ... )
    """

    selected: str | None = None
    allow_deselect: bool = True
    aes: IndexedAesthetic | ByGroup | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JavaScript (snake_case, JS converts to camelCase)."""
        result: dict[str, Any] = {
            "type": "single",
            "allow_deselect": self.allow_deselect,
        }
        if self.selected is not None:
            result["selected"] = self.selected
        if self.aes is not None:
            result["aes_indexed"] = _serialize_aes(self.aes)
        return result


@dataclass
class Multiple:
    """Multiple selection mode with customization options.

    Use when you need options beyond the simple mode="multiple" string:
    - Initial selections
    - Selection limit (max_selection)
    - Custom two-state aesthetics

    Args:
        selected: Initially selected region IDs.
        max_selection: Maximum number of selections allowed. None = unlimited.
        aes: Two-state aesthetic [unselected, selected].
             Can be aes.Indexed (global) or aes.ByGroup wrapping aes.Indexed.

    Example:
        >>> from shinymap.mode import Multiple
        >>> from shinymap import aes
        >>>
        >>> # Limit to 3 selections
        >>> mode = Multiple(max_selection=3)
        >>>
        >>> # Pre-select regions
        >>> mode = Multiple(selected=["region_a", "region_b"])
        >>>
        >>> # Custom selection colors with limit
        >>> mode = Multiple(
        ...     max_selection=5,
        ...     aes=aes.Indexed(
        ...         fill_color=["#e5e7eb", "#10b981"],  # gray -> green
        ...     )
        ... )
    """

    selected: list[str] | None = None
    max_selection: int | None = None
    aes: IndexedAesthetic | ByGroup | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JavaScript (snake_case, JS converts to camelCase)."""
        result: dict[str, Any] = {
            "type": "multiple",
        }
        if self.selected is not None:
            result["selected"] = self.selected
        if self.max_selection is not None:
            result["max_selection"] = self.max_selection
        if self.aes is not None:
            result["aes_indexed"] = _serialize_aes(self.aes)
        return result


@dataclass
class Cycle:
    """Cycle mode - finite state cycling (e.g., traffic light survey).

    Each click cycles through n states: 0 -> 1 -> 2 -> ... -> n-1 -> 0.
    Use with aes.Indexed to define visual appearance for each state.

    Args:
        n: Number of states (e.g., 4 for gray->red->yellow->green->gray).
        values: Initial state per region {id: state_index}. Default: all 0.
        aes: Indexed aesthetic with styles for each state.
             Can be aes.Indexed (global) or aes.ByGroup wrapping aes.Indexed.
             Index is computed as: count % n (wrapping).

    Example:
        >>> from shinymap.mode import Cycle
        >>> from shinymap import aes
        >>> from shinymap.palettes import HUE_CYCLE_4
        >>>
        >>> # Traffic light survey (4 states)
        >>> mode = Cycle(
        ...     n=4,
        ...     aes=aes.Indexed(fill_color=HUE_CYCLE_4),
        ... )
        >>>
        >>> # Per-group palettes (color coordination quiz)
        >>> mode = Cycle(
        ...     n=2,
        ...     aes=aes.ByGroup(
        ...         question_1=aes.Indexed(fill_color=["#bfdbfe", "#2563eb"]),
        ...         question_2=aes.Indexed(fill_color=["#bbf7d0", "#16a34a"]),
        ...     ),
        ... )
    """

    n: int
    values: dict[str, int] | None = None
    aes: IndexedAesthetic | ByGroup | None = None

    def __post_init__(self):
        if self.n < 2:
            raise ValueError("Cycle.n must be at least 2")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JavaScript (snake_case, JS converts to camelCase)."""
        result: dict[str, Any] = {
            "type": "cycle",
            "n": self.n,
        }
        if self.values is not None:
            result["values"] = self.values
        if self.aes is not None:
            result["aes_indexed"] = _serialize_aes(self.aes)
        return result


@dataclass
class Count:
    """Count mode - unbounded counting.

    Each click increments the count. Use with aes.Indexed to define
    visual appearance based on count (with clamping for index lookup).

    Args:
        values: Initial counts per region {id: count}. Default: all 0.
        max_count: Optional cap for aesthetic indexing (clamping).
                   If None, uses len(aes list) - 1 as the cap.
        aes: Indexed aesthetic for visual feedback.
             Can be aes.Indexed (global) or aes.ByGroup wrapping aes.Indexed.
             Index is computed as: min(count, len(list) - 1) (clamping).

    Example:
        >>> from shinymap.mode import Count
        >>> from shinymap import aes
        >>> from shinymap.utils import linspace
        >>>
        >>> # Heat map with opacity gradient
        >>> mode = Count(
        ...     aes=aes.Indexed(
        ...         fill_color="#f97316",
        ...         fill_opacity=linspace(0.0, 1.0, num=6),
        ...     ),
        ... )
        >>>
        >>> # Per-group palettes
        >>> mode = Count(
        ...     aes=aes.ByGroup(
        ...         group_a=aes.Indexed(
        ...             fill_color="#ef4444", fill_opacity=linspace(0.2, 1.0, num=5)
        ...         ),
        ...         group_b=aes.Indexed(
        ...             fill_color="#3b82f6", fill_opacity=linspace(0.2, 1.0, num=5)
        ...         ),
        ...     ),
        ... )
    """

    values: dict[str, int] | None = None
    max_count: int | None = None
    aes: IndexedAesthetic | ByGroup | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JavaScript (snake_case, JS converts to camelCase)."""
        result: dict[str, Any] = {
            "type": "count",
        }
        if self.values is not None:
            result["values"] = self.values
        if self.max_count is not None:
            result["max_count"] = self.max_count
        if self.aes is not None:
            result["aes_indexed"] = _serialize_aes(self.aes)
        return result


@dataclass
class Display:
    """Display-only mode for output_map.

    Regions respond to hover but not click by default. Value determines which
    indexed aesthetic to use, enabling declarative value-to-color mapping.

    This mode is specifically for output_map, allowing you to prepopulate
    the color scale in the UI declaration rather than computing it in
    the render function.

    Args:
        aes: Indexed aesthetic mapping values to colors.
             Can be aes.Indexed (global) or aes.ByGroup wrapping aes.Indexed.
             Index is computed as: min(value, len(list) - 1) (clamping).
        clickable: If True, clicking a region emits an input event with the
                   region ID. Use with @reactive.event to trigger actions
                   like showing modals. Default is False.
        input_id: Custom input ID for click events. If None (default),
                  uses "{output_map_id}_click". Only used when clickable=True.

    Example:
        >>> from shinymap.mode import Display
        >>> from shinymap import aes, output_map
        >>>
        >>> # Traffic light colors for status values
        >>> output_map(
        ...     "status_map",
        ...     outline,
        ...     mode=Display(aes=aes.Indexed(
        ...         fill_color=["#f3f4f6", "#22c55e", "#f59e0b", "#ef4444"]
        ...     ))
        ... )
        >>>
        >>> @render_map
        >>> def status_map():
        ...     # value 0=unknown, 1=good, 2=warning, 3=error
        ...     return Map(outline, value=status_values)
        >>>
        >>> # Clickable display map for triggering actions
        >>> output_map(
        ...     "clickable_map",
        ...     outline,
        ...     mode=Display(clickable=True)
        ... )
        >>>
        >>> @reactive.effect
        >>> @reactive.event(input.clickable_map_click)
        >>> def show_region_modal():
        ...     region_id = input.clickable_map_click()
        ...     # Show modal with region details
        >>>
        >>> # Custom input ID
        >>> output_map(
        ...     "my_map",
        ...     outline,
        ...     mode=Display(clickable=True, input_id="region_clicked")
        ... )
        >>> # Access via input.region_clicked()
    """

    aes: IndexedAesthetic | ByGroup | None = None
    clickable: bool = False
    input_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JavaScript (snake_case, JS converts to camelCase)."""
        result: dict[str, Any] = {
            "type": "display",
        }
        if self.aes is not None:
            result["aes_indexed"] = _serialize_aes(self.aes)
        if self.clickable:
            result["clickable"] = True
        # Note: input_id is handled by _output_map, not serialized to JS
        return result

    def get_click_input_id(self, output_id: str) -> str | None:
        """Get the click input ID for this mode.

        Args:
            output_id: The output map's ID

        Returns:
            The input ID for click events, or None if not clickable
        """
        if not self.clickable:
            return None
        return self.input_id if self.input_id else f"{output_id}_click"


def _serialize_aes(aes: Any) -> dict[str, Any]:
    """Serialize aes.Indexed or aes.ByGroup to dict for JavaScript.

    For IndexedAesthetic (global), produces the data directly:
        {fill_color: [...], ...}

    For ByGroup wrapping IndexedAesthetic (per-group), produces:
        {type: "byGroup", groups: {group_name: {fill_color: [...], ...}, ...}}

    JS distinguishes: if aesIndexed has a "type" key, it's ByGroup. Otherwise direct data.
    """
    from .aes._core import ByGroup, IndexedAesthetic

    def _indexed_to_data(indexed: IndexedAesthetic) -> dict[str, Any]:
        """Extract just the aesthetic values (no type key) for JS IndexedAestheticData."""
        d = indexed.to_dict()
        d.pop("type", None)  # Remove the "type" key - JS doesn't need it
        return d

    if isinstance(aes, IndexedAesthetic):
        # Direct IndexedAestheticData (no wrapper)
        return _indexed_to_data(aes)
    elif isinstance(aes, ByGroup):
        # ByGroup wrapping IndexedAesthetic
        groups = {}
        for key, value in aes.items():
            if isinstance(value, IndexedAesthetic):
                groups[key] = _indexed_to_data(value)
            elif hasattr(value, "to_dict"):
                groups[key] = value.to_dict()
        return {"type": "byGroup", "groups": groups}
    elif hasattr(aes, "to_dict"):
        return aes.to_dict()  # type: ignore[no-any-return]
    else:
        return aes  # type: ignore[no-any-return]


# Type alias for mode parameter (input_map modes)
ModeType = Literal["single", "multiple"] | Single | Multiple | Cycle | Count

# Type alias for output_map mode parameter (includes Display)
OutputModeType = Display | None


def normalize_mode(mode: ModeType) -> Single | Multiple | Cycle | Count:
    """Normalize mode parameter to Mode class instance.

    Converts string modes ("single", "multiple") to their class equivalents.

    Args:
        mode: Mode string or Mode class instance

    Returns:
        Mode class instance (Single, Multiple, Cycle, or Count)

    Raises:
        ValueError: If mode is not a valid string or Mode class instance

    Example:
        >>> normalize_mode("single")
        Single(selected=None, allow_deselect=True, aes=None)
        >>> normalize_mode(Multiple(max_selection=3))
        Multiple(selected=None, max_selection=3, aes=None)
    """
    if mode == "single":
        return Single()
    elif mode == "multiple":
        return Multiple()
    elif isinstance(mode, (Single, Multiple, Cycle, Count)):
        return mode
    else:
        raise ValueError(
            'mode must be "single", "multiple", or a Mode class instance '
            "(Single, Multiple, Cycle, Count)"
        )


def initial_value_from_mode(
    mode: Single | Multiple | Cycle | Count,
) -> dict[str, int] | None:
    """Extract initial value from Mode class instance.

    Gets the initial selection/value state from the mode configuration.

    Args:
        mode: Mode class instance

    Returns:
        Initial value dict {region_id: count}, or None if no initial value

    Example:
        >>> initial_value_from_mode(Single(selected="region1"))
        {'region1': 1}
        >>> initial_value_from_mode(Multiple(selected=["a", "b"]))
        {'a': 1, 'b': 1}
        >>> initial_value_from_mode(Count(values={"r1": 3}))
        {'r1': 3}
    """
    if isinstance(mode, Single) and mode.selected is not None:
        return {mode.selected: 1}
    elif isinstance(mode, Multiple) and mode.selected is not None:
        return {s: 1 for s in mode.selected}
    elif isinstance(mode, (Cycle, Count)) and mode.values is not None:
        return mode.values
    return None


__all__ = [
    "Single",
    "Multiple",
    "Cycle",
    "Count",
    "Display",
    "ModeType",
    "OutputModeType",
    "normalize_mode",
    "initial_value_from_mode",
]
