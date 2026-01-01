"""Output map component for Shiny.

This module provides the internal _output_map function that creates
output map containers.
"""

from collections.abc import MutableMapping
from typing import Any

from htmltools import TagList, css, div
from shiny import ui

from ..aes._core import ByGroup
from ..geometry._core import Outline
from ..payload import build_aes_payload
from ..types import TooltipMap
from ._registry import _static_map_params
from ._util import (
    _class_names,
    _dependency,
    _merge_styles,
    _strip_none,
)


def _output_map(
    id: str,
    outline: Outline | None,
    resolved_aes: ByGroup,
    tooltips: TooltipMap,
    view_box: tuple[float, float, float, float] | None,
    layers: dict[str, list[str]] | None,
    width: str | None,
    height: str | None,
    class_: str | None,
    style: MutableMapping[str, str] | None,
) -> TagList:
    """Create an output map container.

    This is the internal base function. Use Wash().output_map() or the
    public output_map() for the full API.

    Args:
        id: Output ID for Shiny.
        outline: Outline object with regions (can be None if provided via @render_map).
        resolved_aes: Pre-resolved ByGroup aesthetic (from WashConfig.apply).
        tooltips: Region tooltips as {region_id: tooltip_text}.
        view_box: Override viewBox tuple (x, y, width, height).
        layers: Layer configuration dict with keys: underlays, overlays, hidden.
        width: Container width (CSS).
        height: Container height (CSS).
        class_: Additional CSS classes.
        style: Additional inline styles.

    Returns:
        TagList with the output container.
    """
    static_params: dict[str, Any] = {}

    if outline is not None:
        # Merge layers into outline metadata
        outline = outline.merge_layers(layers)

        # Geometry
        vb_tuple = view_box if view_box else outline.viewbox()
        vb_str = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"

        # Build aes payload from pre-resolved ByGroup
        aes_dict = build_aes_payload(resolved_aes, outline)

        # Store static params (JS will convert snake_case to camelCase)
        static_params = _strip_none(
            {
                "geometry": outline.regions,
                "tooltips": tooltips,
                "view_box": vb_str,
                "aes": aes_dict,
                "layers": outline.overlays() or None,
                "geometry_metadata": outline.metadata_dict(vb_tuple),
            }
        )
    elif view_box is not None:
        # No outline but view_box provided
        vb_str = f"{view_box[0]} {view_box[1]} {view_box[2]} {view_box[3]}"
        static_params = _strip_none(
            {
                "tooltips": tooltips,
                "view_box": vb_str,
            }
        )

    if static_params:
        _static_map_params[id] = static_params

    return TagList(
        _dependency(),
        div(
            ui.output_ui(id),
            class_=_class_names("shinymap-output-container", class_),
            style=css(**_merge_styles(width, height, style)),
        ),
    )
