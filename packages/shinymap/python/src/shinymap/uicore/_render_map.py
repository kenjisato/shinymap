"""Render map decorator for Shiny.

This module provides the @render_map decorator for creating reactive
map outputs.
"""

import json
from functools import wraps
from typing import Any

from htmltools import Tag, TagList, div
from shiny import render
from shiny.module import resolve_id

from ..aes._core import BaseAesthetic, ByGroup, ByState
from ..payload import build_aes_payload
from ..types import MapBuilder
from ._registry import _static_map_params
from ._util import _normalize_outline
from ._wash import element_kind


def _merge_bygroup(a: ByGroup, b: ByGroup) -> ByGroup:
    """Merge two ByGroup objects. Keys in b take precedence over a."""
    merged_groups = dict(a._groups)
    merged_groups.update(b._groups)
    return ByGroup(**merged_groups)


def _normalize_builder_aes(aes: Any, outline: Any, wash_config: Any) -> ByGroup | None:
    """Normalize the aes given to Map() into a ByGroup.

    ByState and single aesthetics apply to every region. They are resolved through
    the wash (the one output_map() used, else the default) so they also override
    the wash's type default (e.g. ``__shape``), which JS looks up before ``__all``.
    Only the entries the user affected are kept, so output_map()'s group and
    region entries survive the merge.
    Raw dicts are rejected: since 0.3 the payload is built from aes objects only.
    """
    if aes is None or isinstance(aes, ByGroup):
        return aes
    if isinstance(aes, (ByState, BaseAesthetic)):
        if outline is None:
            return ByGroup(__all=aes)
        if wash_config is None:
            from ..ui._ui import _default_wash

            wash_config = _default_wash.config
        resolved = wash_config.apply(aes, outline)
        keep = {"__all"}
        kind = element_kind(aes)
        if kind is not None:
            keep.add(f"__{kind}")
        return ByGroup(**{k: v for k, v in resolved.items() if k in keep})
    if isinstance(aes, dict):
        raise TypeError(
            "Map(aes=...) no longer accepts a dict. Use aes objects instead, e.g. "
            "aes.ByGroup(region_id=aes.Shape(fill_color='#f00')) or aes.Shape(...)."
        )
    raise TypeError(f"Unsupported aes type for Map(): {type(aes).__name__}")


def _build_payload(
    builder: MapBuilder,
    static_params: dict[str, Any],
) -> dict[str, Any]:
    """Build the final payload dict for JavaScript.

    Handles merging of builder params with static params from output_map(),
    and converts all objects to dicts.
    """
    # Get outline from static params or builder (builder._outline is set by Map())
    outline = static_params.get("outline") or builder._outline

    # Get view_box
    view_box = builder._view_box if builder._view_box is not None else static_params.get("view_box")
    if view_box is None and outline is not None:
        view_box = outline.viewbox()

    # Format view_box as string
    vb_str = None
    if view_box is not None:
        if isinstance(view_box, str):
            vb_str = view_box
        else:
            vb_str = f"{view_box[0]} {view_box[1]} {view_box[2]} {view_box[3]}"

    # Get regions
    regions = builder._regions
    if regions is None and outline is not None:
        regions = outline.regions

    # Merge aes: static from output_map, builder from Map()
    static_aes = static_params.get("resolved_aes")  # ByGroup object
    builder_aes = _normalize_builder_aes(builder._aes, outline, static_params.get("wash_config"))
    merged_aes: Any = None

    if static_aes is not None and builder_aes is not None:
        # Both exist: merge (builder keys take precedence)
        merged_aes = _merge_bygroup(static_aes, builder_aes)
    elif builder_aes is not None:
        merged_aes = builder_aes
    elif static_aes is not None:
        merged_aes = static_aes

    # Build aes payload dict
    aes_dict = None
    if merged_aes is not None and outline is not None:
        aes_dict = build_aes_payload(merged_aes, outline)
    elif merged_aes is not None:
        # No outline, use to_js_dict or to_dict
        if hasattr(merged_aes, "to_js_dict"):
            aes_dict = merged_aes.to_js_dict()
        elif hasattr(merged_aes, "to_dict"):
            aes_dict = merged_aes.to_dict()
        else:
            aes_dict = merged_aes

    # Get layers
    layers = builder._layers
    if layers is None and outline is not None:
        layers = outline.layers_dict()

    # Get outline metadata
    outline_metadata = None
    if hasattr(builder, "_outline_metadata") and builder._outline_metadata is not None:
        outline_metadata = builder._outline_metadata
    elif outline is not None:
        outline_metadata = outline.metadata_dict(
            view_box if not isinstance(view_box, str) else None
        )

    # Build payload
    payload: dict[str, Any] = {}

    if regions is not None:
        payload["regions"] = _normalize_outline(regions)
    if builder._tooltips is not None:
        payload["tooltips"] = builder._tooltips
    elif static_params.get("tooltips") is not None:
        payload["tooltips"] = static_params["tooltips"]
    if builder._value is not None:
        payload["value"] = builder._value
    if vb_str is not None:
        payload["view_box"] = vb_str
    if aes_dict is not None:
        payload["aes"] = aes_dict
    if layers is not None:
        payload["layers"] = layers
    if outline_metadata is not None:
        payload["outline_metadata"] = outline_metadata

    return payload


def _render_map_ui(
    payload_dict: dict[str, Any],
    click_input_id: str | None = None,
) -> Tag:
    """Internal: Render a payload dict to HTML.

    Used by @render_map decorator. This creates the inner content
    that goes inside the output_map container.

    Args:
        payload_dict: The payload dict to send to JavaScript
        click_input_id: Optional input ID for click events (from Display(clickable=True))

    Returns:
        Tag with map payload data attribute
    """
    # Build attributes dict
    attrs: dict[str, str] = {
        "class_": "shinymap-output",
        "data_shinymap_output": "1",
        "data_shinymap_payload": json.dumps(payload_dict),
        "style": "width: 100%; height: 100%;",
    }

    # Add click input ID if provided
    if click_input_id:
        attrs["data_shinymap_click_input_id"] = click_input_id

    return div(**attrs)


def _render_map(fn=None):
    """Base Shiny render decorator for map outputs."""
    from .._map import MapBuilder

    def decorator(func):
        @render.ui
        @wraps(func)
        def wrapper():
            val = func()

            # Pass through raw Tag/TagList
            if isinstance(val, (Tag, TagList)):
                return val

            # Ensure we have a MapBuilder
            if isinstance(val, MapBuilder):
                builder = val
            elif hasattr(val, "as_json"):
                # Duck typing: anything with as_json() works
                builder = val
            else:
                raise TypeError(f"Expected MapBuilder, got {type(val)}")

            output_id = resolve_id(func.__name__)
            static_params = _static_map_params.get(output_id, {})

            # Build payload with merged params
            payload_dict = _build_payload(builder, static_params)

            # Add mode to payload (convert to dict here)
            # Default to Display() if mode not in static_params (can happen when
            # output_map() is called without outline parameter)
            from ..mode import Display

            mode = static_params.get("mode") or Display()
            payload_dict["mode"] = mode.to_dict()

            # Get click_input_id from static params
            click_input_id = static_params.get("click_input_id")

            return _render_map_ui(payload_dict, click_input_id)

        return wrapper

    if fn is None:
        return decorator

    return decorator(fn)
