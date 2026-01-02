"""Render map decorator for Shiny.

This module provides the @render_map decorator for creating reactive
map outputs.
"""

import json
from functools import wraps

from htmltools import Tag, TagList, div
from shiny import render

from ..types import MapBuilder
from ._registry import _static_map_params


def _apply_static_params(builder: MapBuilder, output_id: str) -> MapBuilder:
    """Apply static parameters from output_map() to builder.

    Builder parameters take precedence over static parameters.
    Static params use v0.3 aes payload format (flat with _metadata).
    """
    from .._map import MapBuilder

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

    # Merge aes: builder aes overrides static
    # v0.3 format: flat dict with region/group keys, each containing {base, select, hover}
    static_aes = static_params.get("aes")
    if builder._aes is not None:
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


def _render_map_ui(builder: MapBuilder, click_input_id: str | None = None) -> Tag | TagList:
    """Internal: Render a map builder to HTML.

    Used by @render_map decorator. This creates the inner content
    that goes inside the output_map container.

    Args:
        builder: MapBuilder with data to render
        click_input_id: Optional input ID for click events (from Display(clickable=True))

    Returns:
        Tag with map payload data attribute
    """
    if isinstance(builder, (Tag, TagList)):
        return builder

    payload_dict = builder.as_json()

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

            # Ensure we have a MapBuilder
            if isinstance(val, MapBuilder):
                builder = val
            elif hasattr(val, "as_json"):
                # Duck typing: anything with as_json() works
                builder = val
            else:
                # Pass through raw Tag/TagList
                return _render_map_ui(val)

            output_id = func.__name__
            builder = _apply_static_params(builder, output_id)

            # Get click_input_id from static params if set
            static_params = _static_map_params.get(output_id, {})
            click_input_id = static_params.get("click_input_id")

            return _render_map_ui(builder, click_input_id)

        return wrapper

    if fn is None:
        return decorator

    return decorator(fn)
