"""Shiny UI components for shinymap with library defaults.

This module provides pre-configured UI functions using sensible library defaults.
For custom aesthetics, use the `uicore.Wash` factory directly.

Usage:
    from shinymap.ui import input_map, output_map, update_map
    from shinymap import render_map  # decorator, at top-level

    # UI layer
    input_map("region", geometry, mode="single")
    output_map("my_map", geometry)

    # Server layer
    @render_map
    def my_map():
        return Map().with_value(counts)

    # Update existing map
    update_map("my_map", aes=aes.ByGroup(region1=aes.Shape(fill_color="#ff0000")))
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from htmltools import TagList

from .. import aes
from ..relative import PARENT
from ..uicore import Wash, update_map

if TYPE_CHECKING:
    from ..geometry import Outline

# =============================================================================
# Default wash with sensible library defaults
# =============================================================================

# Create default Wash instance with library defaults for base, select, hover.
# These defaults are applied when using the library-supplied input_map/output_map.
# Users who create their own Wash() must define all aesthetics themselves.
#
# Design notes:
# - TypeScript has two sets of defaults:
#   1. DEFAULT_AESTHETIC_VALUES: reserved/subtle for user-defined wash layers
#   2. LIBRARY_AESTHETIC_DEFAULTS: complete defaults for React developers
# - Library defaults here provide a complete, polished out-of-box experience
# - No hardcoded fallbacks in shinymap-shiny.js - everything flows from Python
_default_wash = Wash(
    shape=aes.ByState(
        base=aes.Shape(
            fill_color="#e2e8f0",  # slate-200: neutral base
            stroke_color="#94a3b8",  # slate-400: subtle border
            stroke_width=0.5,
        ),
        select=aes.Shape(
            fill_color="#bfdbfe",  # blue-200: selected highlight
            stroke_color="#1e40af",  # blue-800: strong border
            stroke_width=1,
        ),
        hover=aes.Shape(
            stroke_color="#475569",  # slate-600: darker border on hover
            stroke_width=PARENT.stroke_width + 0.5,
        ),
    ),
    line=aes.Line(
        stroke_color="#94a3b8",  # slate-400
        stroke_width=0.5,
    ),
    text=aes.Text(
        fill_color="#1e293b",  # slate-800
    ),
)

# Public API functions use the default wash
input_map = _default_wash.input_map
output_map = _default_wash.output_map
render_map = _default_wash.render_map


# =============================================================================
# Sugar functions: Shiny-aligned naming for common use cases
# =============================================================================


def input_radio_buttons(
    id: str,
    geometry: Outline,
    *,
    tooltips: dict[str, str] | None = None,
    selected: str | None = None,
    view_box: tuple[float, float, float, float] | None = None,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
) -> TagList:
    """Visual radio buttons using map regions.

    Single-selection mode: clicking a region selects it, clicking another
    deselects the previous one. Returns `str | None` (selected region ID).

    This is a sugar function for `input_map(..., mode="single")`.

    Args:
        id: Input ID for Shiny
        geometry: Outline object with regions
        tooltips: Region tooltips as {region_id: tooltip_text}
        selected: Initially selected region ID
        view_box: Override viewBox tuple
        width: Container width (CSS)
        height: Container height (CSS)
        class_: Additional CSS classes
        style: Additional inline styles

    Returns:
        TagList with the map component

    Example:
        >>> from shinymap import input_radio_buttons
        >>> from shinymap.geometry import Outline
        >>>
        >>> geo = Outline.from_dict(data)
        >>> input_radio_buttons("region", geo)
    """
    value = {selected: 1} if selected else None
    return input_map(
        id,
        geometry,
        "single",
        tooltips=tooltips,
        value=value,
        view_box=view_box,
        width=width,
        height=height,
        class_=class_,
        style=style,
    )


def input_checkbox_group(
    id: str,
    geometry: Outline,
    *,
    tooltips: dict[str, str] | None = None,
    selected: list[str] | None = None,
    view_box: tuple[float, float, float, float] | None = None,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
) -> TagList:
    """Visual checkbox group using map regions.

    Multiple-selection mode: clicking toggles selection state.
    Returns `list[str]` (list of selected region IDs).

    This is a sugar function for `input_map(..., mode="multiple")`.

    Args:
        id: Input ID for Shiny
        geometry: Outline object with regions
        tooltips: Region tooltips as {region_id: tooltip_text}
        selected: Initially selected region IDs
        view_box: Override viewBox tuple
        width: Container width (CSS)
        height: Container height (CSS)
        class_: Additional CSS classes
        style: Additional inline styles

    Returns:
        TagList with the map component

    Example:
        >>> from shinymap import input_checkbox_group
        >>> from shinymap.geometry import Outline
        >>>
        >>> geo = Outline.from_dict(data)
        >>> input_checkbox_group("regions", geo, selected=["a", "b"])
    """
    value = {rid: 1 for rid in selected} if selected else None
    return input_map(
        id,
        geometry,
        "multiple",
        tooltips=tooltips,
        value=value,
        view_box=view_box,
        width=width,
        height=height,
        class_=class_,
        style=style,
    )


# Re-export update_map for convenience
__all__ = [
    "input_map",
    "output_map",
    "render_map",
    "update_map",
    "input_radio_buttons",
    "input_checkbox_group",
]
