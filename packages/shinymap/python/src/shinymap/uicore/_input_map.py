"""Input map component for Shiny.

This module provides the internal _input_map function that creates
interactive map input components.
"""

import json
from collections.abc import MutableMapping

from htmltools import TagList, css, div

from ..aes._core import ByGroup
from ..geometry._core import Outline
from ..mode import ModeType, initial_value_from_mode, normalize_mode
from ..payload import build_aes_payload
from ..types import CountMap, TooltipMap
from ._util import (
    _class_names,
    _dependency,
    _merge_styles,
    _normalize_outline,
    _strip_none,
    _validate_value,
)


def _input_map(
    id: str,
    outline: Outline,
    mode: ModeType,
    resolved_aes: ByGroup,
    tooltips: TooltipMap,
    value: CountMap,
    view_box: tuple[float, float, float, float] | None,
    layers: dict[str, list[str]] | None,
    raw: bool,
    width: str | None,
    height: str | None,
    class_: str | None,
    style: MutableMapping[str, str] | None,
) -> TagList:
    """Create an interactive map input component.

    This is the internal base function. Use Wash().input_map() or the
    public input_map() for the full API.

    Args:
        id: The input ID.
        outline: Outline object containing regions and metadata.
        mode: Selection mode.
        resolved_aes: Pre-resolved ByGroup aesthetic (from WashConfig.apply).
        tooltips: Tooltip text per region.
        value: Initial values per region {region_id: count}.
        view_box: SVG viewBox override (x, y, width, height).
        layers: Layer configuration dict with keys: underlays, overlays, hidden.
        raw: If True, return raw dict[str, int] value instead of transformed types.
        width: CSS width.
        height: CSS height.
        class_: Additional CSS classes.
        style: Additional inline styles.

    Returns:
        TagList containing the input component.
    """
    # Validate initial value (must be non-negative integers)
    _validate_value(value, "value")

    # Merge layers into outline metadata
    outline = outline.merge_layers(layers)

    # Normalize mode and extract initial value
    mode_obj = normalize_mode(mode)
    effective_value = value if value is not None else initial_value_from_mode(mode_obj)

    # Geometry
    vb_tuple = view_box if view_box else outline.viewbox()
    vb_str = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"

    # Build aes payload from pre-resolved ByGroup
    aes_dict = build_aes_payload(resolved_aes, outline)

    # Build props (JS will convert snake_case to camelCase)
    props = _strip_none(
        {
            "geometry": _normalize_outline(outline.regions),
            "tooltips": tooltips,
            "view_box": vb_str,
            "geometry_metadata": outline.metadata_dict(vb_tuple),
            "value": effective_value,
            "mode": mode_obj.to_dict(),
            "aes": aes_dict,
            "layers": outline.overlays() or None,
            "raw": raw if raw else None,  # Only include if True
        }
    )

    container = div(
        id=id,
        class_=_class_names("shinymap-input", class_),
        style=css(**_merge_styles(width, height, style)),
        data_shinymap_input="1",
        data_shinymap_input_id=id,
        data_shinymap_input_mode=props["mode"]["type"],
        data_shinymap_props=json.dumps(props),
    )

    return TagList(_dependency(), container)
