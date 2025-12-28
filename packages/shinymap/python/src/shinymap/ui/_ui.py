from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, Any

from htmltools import Tag, TagList, css
from shiny import ui
from shiny.session import Session, require_active_session

from .._base import (
    CountMap,
    TooltipMap,
    _camel_props,
    _class_names,
    _convert_aes_to_dict,
    _dependency,
    _merge_styles,
)
from .._map import MapBuilder
from ..aes._core import BaseAesthetic, ByGroup, ByState

if TYPE_CHECKING:
    from ..geometry import Outline

Selection = str | list[str] | None
AesType = ByGroup | ByState | BaseAesthetic | Mapping[str, Mapping[str, Any] | None] | None

# Module-level registry for static parameters from output_map()
_static_map_params: MutableMapping[str, Mapping[str, Any]] = {}


# Public input_map uses Wash() with sensible defaults
# Defined at module level after all helper definitions
# See end of file for: input_map = _default_wash.input_map


def _render_map_ui(
    builder: MapBuilder,
    *,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
    click_input_id: str | None = None,
    _include_dependency: bool = True,
) -> Tag | TagList:
    """Internal: Render a map builder to HTML. Used by @render_map decorator."""
    if isinstance(builder, (Tag, TagList)):
        if _include_dependency:
            return TagList(_dependency(), builder)
        return builder

    payload_dict = builder.as_json()
    div = ui.div(
        class_=_class_names("shinymap-output", class_),
        style=css(**_merge_styles(width, height, style)),
        data_shinymap_output="1",
        data_shinymap_payload=json.dumps(payload_dict),
        data_shinymap_click_input_id=click_input_id if click_input_id else None,
    )

    if _include_dependency:
        return TagList(_dependency(), div)
    return div


# Public output_map uses Wash() with sensible defaults
# Defined at module level after all helper definitions
# See end of file for: output_map = _default_wash.output_map


def _apply_static_params(builder: MapBuilder, output_id: str) -> MapBuilder:
    """Apply static parameters from output_map() to builder.

    Builder parameters take precedence over static parameters.
    """
    static_params = _static_map_params.get(output_id)
    if not static_params:
        return builder

    # Create new builder with merged parameters
    # Builder values (if set) override static values
    regions = builder._regions if builder._regions is not None else static_params.get("geometry")
    tooltips = builder._tooltips if builder._tooltips is not None else static_params.get("tooltips")
    view_box = builder._view_box if builder._view_box is not None else static_params.get("view_box")
    merged = MapBuilder(regions=regions, tooltips=tooltips, view_box=view_box)

    # Copy over builder-set values
    if builder._value is not None:
        merged._value = builder._value
    if builder._active_ids is not None:
        merged._active_ids = builder._active_ids

    # Merge aes: builder values override static, but preserve lines_as_path from static
    static_aes = static_params.get("aes")
    if builder._aes is not None and static_aes is not None:
        # Need to merge: static aes contains lines_as_path entries, builder aes is user-provided
        # Convert builder aes to dict and merge with static
        builder_aes_dict = (
            _convert_aes_to_dict(builder._aes)
            if isinstance(builder._aes, (ByGroup, ByState, BaseAesthetic))
            else builder._aes
        )
        # Deep merge: static group entries are base, builder entries override
        merged_aes: dict[str, Any] = dict(static_aes) if static_aes else {}
        if builder_aes_dict:
            for key, value in builder_aes_dict.items():
                if key == "group" and isinstance(value, dict):
                    # Merge group entries: builder overrides static
                    if "group" not in merged_aes:
                        merged_aes["group"] = {}
                    merged_aes["group"] = {**merged_aes.get("group", {}), **value}
                else:
                    merged_aes[key] = value
        merged._aes = merged_aes
    elif builder._aes is not None:
        merged._aes = builder._aes
    elif static_aes is not None:
        merged._aes = static_aes

    # Merge layers: builder values override static
    static_layers = static_params.get("layers")
    if builder._layers is not None:
        merged._layers = builder._layers
    elif static_layers is not None:
        merged._layers = static_layers

    # Geometry metadata
    static_metadata = static_params.get("geometry_metadata")
    if hasattr(builder, "_geometry_metadata") and builder._geometry_metadata is not None:
        merged._geometry_metadata = builder._geometry_metadata
    elif static_metadata is not None:
        merged._geometry_metadata = static_metadata

    return merged


# Public render_map uses Wash() with sensible defaults
# Defined at module level after all helper definitions
# See end of file for: render_map = _default_wash.render_map


def update_map(
    id: str,
    *,
    aes: AesType = None,
    value: CountMap = None,
    tooltips: TooltipMap = None,
    session: Session | None = None,
) -> None:
    """Update an input_map or output_map without full re-render.

    For input_map: Updates aesthetics and selection state.
    For output_map: Updates aesthetics only (use @render_map for data changes).

    Args:
        id: The map element ID
        aes: Aesthetic configuration (ByGroup, ByState, or BaseAesthetic)
        value: (input_map only) Selection state; pass {} to clear all selections
        tooltips: Region tooltips
        session: A Session instance. If not provided, it is inferred via get_current_session()

    Example:
        from shinymap import aes
        from shinymap.ui import update_map

        # Update aesthetics with ByGroup (per-region colors)
        update_map("my_map", aes=aes.ByGroup(
            region1=aes.Shape(fill_color="#ff0000"),
            region2=aes.Shape(fill_color="#00ff00"),
        ))

        # Update with ByState (base/select/hover)
        update_map("my_map", aes=aes.ByState(
            base=aes.Shape(fill_color="#e2e8f0"),
            select=aes.Shape(fill_color="#bfdbfe"),
        ))

        # Clear all selections (input_map only)
        update_map("my_map", value={})

        # Set specific selections (input_map only)
        update_map("my_map", value={"region1": 1, "region2": 1})

    Note:
        - Uses shallow merge semantics: new properties override existing ones
        - Properties not specified are left unchanged
        - For output_map data updates, use @render_map re-execution instead
    """
    session = require_active_session(session)

    # Build update payload
    updates: dict[str, Any] = {}

    if aes is not None:
        if isinstance(aes, (ByGroup, ByState, BaseAesthetic)):
            updates["aes"] = _convert_aes_to_dict(aes)
        else:
            updates["aes"] = aes
    if value is not None:
        updates["value"] = value
    if tooltips is not None:
        updates["tooltips"] = tooltips

    if not updates:
        return  # Nothing to update

    # Convert to camelCase for JavaScript
    camel_updates = _camel_props(updates)

    # Send custom message to JavaScript
    msg = {"id": id, "updates": camel_updates}
    session._send_message_sync({"custom": {"shinymap-update": msg}})


# =============================================================================
# Default wash with sensible library defaults
# Import at module end to avoid circular dependency (_wash imports _base)
# =============================================================================

from .. import aes  # noqa: E402
from .._wash import Wash  # noqa: E402
from ..relative import PARENT  # noqa: E402

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
