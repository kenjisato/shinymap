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
    >>> input_map("regions", geometry, mode=Multiple(max_selection=3))
    >>>
    >>> # Cycle mode with custom palette (e.g., traffic light survey)
    >>> input_map(
    ...     "rating",
    ...     geometry,
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
    ...     geometry,
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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._aesthetics import ByGroup, IndexedAesthetic


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
        """Serialize for JavaScript."""
        result: dict[str, Any] = {
            "type": "single",
            "allowDeselect": self.allow_deselect,
        }
        if self.selected is not None:
            result["selected"] = self.selected
        if self.aes is not None:
            result["aesIndexed"] = _serialize_aes(self.aes)
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
        """Serialize for JavaScript."""
        result: dict[str, Any] = {
            "type": "multiple",
        }
        if self.selected is not None:
            result["selected"] = self.selected
        if self.max_selection is not None:
            result["maxSelection"] = self.max_selection
        if self.aes is not None:
            result["aesIndexed"] = _serialize_aes(self.aes)
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
        """Serialize for JavaScript."""
        result: dict[str, Any] = {
            "type": "cycle",
            "n": self.n,
        }
        if self.values is not None:
            result["values"] = self.values
        if self.aes is not None:
            result["aesIndexed"] = _serialize_aes(self.aes)
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
        ...         group_a=aes.Indexed(fill_color="#ef4444", fill_opacity=linspace(0.2, 1.0, num=5)),
        ...         group_b=aes.Indexed(fill_color="#3b82f6", fill_opacity=linspace(0.2, 1.0, num=5)),
        ...     ),
        ... )
    """

    values: dict[str, int] | None = None
    max_count: int | None = None
    aes: IndexedAesthetic | ByGroup | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JavaScript."""
        result: dict[str, Any] = {
            "type": "count",
        }
        if self.values is not None:
            result["values"] = self.values
        if self.max_count is not None:
            result["maxCount"] = self.max_count
        if self.aes is not None:
            result["aesIndexed"] = _serialize_aes(self.aes)
        return result


def _serialize_aes(aes: Any) -> dict[str, Any]:
    """Serialize aes.Indexed or aes.ByGroup to dict for JavaScript."""
    from ._aesthetics import ByGroup, IndexedAesthetic

    if isinstance(aes, IndexedAesthetic):
        return {"type": "indexed", "value": aes.to_dict()}
    elif isinstance(aes, ByGroup):
        # ByGroup wrapping IndexedAesthetic
        groups = {}
        for key, value in aes.items():
            if isinstance(value, IndexedAesthetic):
                groups[key] = value.to_dict()
            elif hasattr(value, "to_dict"):
                groups[key] = value.to_dict()
        return {"type": "byGroup", "groups": groups}
    elif hasattr(aes, "to_dict"):
        return aes.to_dict()
    else:
        return aes


# Type alias for mode parameter
ModeType = str | Single | Multiple | Cycle | Count

__all__ = ["Single", "Multiple", "Cycle", "Count", "ModeType"]
