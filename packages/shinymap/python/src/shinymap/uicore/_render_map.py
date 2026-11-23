"""Render map decorator for Shiny.

This module provides the @render_map decorator for creating reactive
map outputs.
"""

import json
from collections.abc import Mapping
from functools import wraps
from typing import Any

from htmltools import Tag, TagList, div
from shiny import render
from shiny.module import resolve_id

from ..payload import build_aes_payload
from ..types import MapBuilder
from ._registry import _static_map_params
from ._util import _normalize_outline
from ._wash import layer_user_aes


def _resolve_map_aes(builder_aes: Any, static_params: Mapping[str, Any], outline: Any) -> Any:
    """Resolve ``Map(aes=...)`` as ``@render_map`` shows it.

    ``Map(aes=...)`` is layered over ``output_map(aes=...)`` and the result is
    resolved once through the output's wash (the default wash without one), so
    user entries always outrank the wash's defaults. Shared with ``StillLife`` so
    a static picture matches the rendered map.
    """
    if builder_aes is None and static_params.get("resolved_aes") is not None:
        return static_params["resolved_aes"]
    combined = layer_user_aes(static_params.get("user_aes"), builder_aes)
    wash_config = static_params.get("wash_config")
    if wash_config is None:
        from ..ui._ui import default_wash

        wash_config = default_wash.config
    return wash_config.apply(combined, outline)


def _resolve_map_geometry(builder: MapBuilder, static_params: Mapping[str, Any]) -> tuple[Any, Any]:
    """The outline (with its layers) and viewBox ``@render_map`` draws.

    The outline is the one given to ``Map()``, else ``output_map()``'s (builder
    parameters take precedence, as for tooltips and the viewBox). Layers are
    merged key by key: the outline's own, then ``output_map(layers=...)``, then
    ``Map(layers=...)``. The viewBox is ``Map()``'s, else ``output_map()``'s, else
    the outline's.
    Shared with ``StillLife`` so a static picture matches the rendered map.
    """
    outline = builder._outline or static_params.get("outline")
    if outline is not None:
        if builder._outline is not None:
            # output_map()'s own outline already has its layers merged in
            outline = outline.merge_layers(static_params.get("layers"))
        if builder._layers is not None:
            layers = {k: v for k, v in builder._layers.items() if v is not None}
            outline = outline.merge_layers(layers)
    view_box = builder._view_box if builder._view_box is not None else static_params.get("view_box")
    if view_box is None and outline is not None:
        view_box = outline.viewbox()
    return outline, view_box


def _build_payload(
    builder: MapBuilder,
    static_params: dict[str, Any],
) -> dict[str, Any]:
    """Build the final payload dict for JavaScript.

    Handles merging of builder params with static params from output_map(),
    and converts all objects to dicts.
    """
    outline, view_box = _resolve_map_geometry(builder, static_params)

    # Format view_box as string
    vb_str = None
    if view_box is not None:
        if isinstance(view_box, str):
            vb_str = view_box
        else:
            vb_str = f"{view_box[0]} {view_box[1]} {view_box[2]} {view_box[3]}"

    # All regions of the outline: layers say which are overlay, underlay, etc.
    # (Map(outline) keeps only main regions in _regions, so overlays went missing)
    # A MapBuilder made from raw regions (no outline) keeps its own regions.
    regions: Any = None
    if builder._outline is None and builder._regions is not None:
        regions = builder._regions
    elif outline is not None:
        regions = outline.regions

    # Merge aes (see _resolve_map_aes); without an outline it cannot be resolved yet
    merged_aes: Any = None
    if outline is not None:
        merged_aes = _resolve_map_aes(builder._aes, static_params, outline)
    elif builder._aes is not None:
        merged_aes = layer_user_aes(static_params.get("user_aes"), builder._aes)

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

    layers = outline.layers_dict() if outline is not None else builder._layers

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
