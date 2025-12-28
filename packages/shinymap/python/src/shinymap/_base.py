"""Base/skeletal map functions that take aesthetic objects.

These functions are internal and should not be used directly.
Use Wash().input_map() or the public input_map() instead.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal

from htmltools import HTMLDependency, TagList, css
from shiny import render, ui

from . import __version__
from .aes._core import (
    BaseAesthetic,
    ByGroup,
    ByState,
    PathAesthetic,
)
from .mode import Count, Cycle, ModeType, Multiple, Single
from .types import MISSING, MissingType

if TYPE_CHECKING:
    from ._wash import WashConfig
    from .geometry import Outline

GeometryMap = Mapping[str, str | list[str] | dict[str, Any] | list[dict[str, Any]]]
TooltipMap = Mapping[str, str] | None
FillMap = str | Mapping[str, str] | None
CountMap = Mapping[str, int] | None


def _dependency() -> HTMLDependency:
    return HTMLDependency(
        name="shinymap",
        version=__version__,
        source={"package": "shinymap", "subdir": "www"},
        script=[{"src": "shinymap.global.js"}, {"src": "shinymap-shiny.js"}],
    )


def _merge_styles(
    width: str | None, height: str | None, style: MutableMapping[str, str] | None
) -> MutableMapping[str, str]:
    merged: MutableMapping[str, str] = {} if style is None else dict(style)
    if width is not None:
        merged.setdefault("width", width)
    if height is not None:
        merged.setdefault("height", height)
    return merged


def _class_names(base: str, extra: str | None) -> str:
    return f"{base} {extra}" if extra else base


def _to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _normalize_outline(outline: GeometryMap) -> Mapping[str, list[dict[str, Any]]]:
    """Normalize outline to Element list format for JavaScript."""

    def _to_camel_dict(d: dict[str, Any]) -> dict[str, Any]:
        return {_to_camel(k): v for k, v in d.items()}

    result: dict[str, list[dict[str, Any]]] = {}
    for region_id, value in outline.items():
        if isinstance(value, str):
            result[region_id] = [{"type": "path", "d": value}]
        elif isinstance(value, list):
            elements: list[dict[str, Any]] = []
            for item in value:
                if isinstance(item, str):
                    elements.append({"type": "path", "d": item})
                elif hasattr(item, "to_dict"):
                    elements.append(_to_camel_dict(item.to_dict()))
                elif isinstance(item, dict):
                    elements.append(_to_camel_dict(item))
            result[region_id] = elements
        elif hasattr(value, "to_dict"):
            result[region_id] = [_to_camel_dict(value.to_dict())]
        elif isinstance(value, dict):
            result[region_id] = [_to_camel_dict(value)]
    return result


def _normalize_fills(fills: FillMap, geometry: GeometryMap) -> Mapping[str, str] | None:
    """Normalize fills to a dict. If fills is a string, apply to all regions."""
    if fills is None:
        return None
    if isinstance(fills, str):
        return {region_id: fills for region_id in geometry.keys()}
    return fills


def _convert_aesthetic_dict(aes_dict: dict[str, Any]) -> dict[str, Any]:
    """Convert snake_case keys in an aesthetic dict to camelCase."""
    return {_to_camel(k): v for k, v in aes_dict.items()}


def _convert_nested_aes(aes: dict[str, Any]) -> dict[str, Any]:
    """Convert the nested aes structure with base/hover/select/notSelect/group."""
    result: dict[str, Any] = {}
    for key, value in aes.items():
        if key == "group" and isinstance(value, dict):
            # Group is a dict of group_name -> aesthetic dict
            result[key] = {
                group_name: _convert_aesthetic_dict(group_aes)
                if isinstance(group_aes, dict)
                else group_aes
                for group_name, group_aes in value.items()
            }
        elif isinstance(value, dict):
            # base, hover, select, notSelect are aesthetic dicts
            result[key] = _convert_aesthetic_dict(value)
        elif value is None:
            # Preserve None values (e.g., hover=None to disable)
            result[key] = None
        else:
            result[key] = value
    return result


def _camel_props(data: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Convert snake_case keys to camelCase and handle aesthetic dicts."""
    mapping = {
        "max_selection": "maxSelection",
        "view_box": "viewBox",
        "active_ids": "activeIds",
        "fill_color": "fillColor",
        "stroke_width": "strokeWidth",
        "stroke_color": "strokeColor",
        "fill_opacity": "fillOpacity",
        "count_palette": "countPalette",
        "overlay_geometry": "overlayGeometry",
        "overlay_aesthetic": "overlayAesthetic",
        "geometry_metadata": "geometryMetadata",
    }

    out: MutableMapping[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        if key == "aes" and isinstance(value, dict):
            # Handle nested aes structure
            out["aes"] = _convert_nested_aes(value)
        elif key == "layers" and isinstance(value, dict):
            # layers structure: {underlays: [...], overlays: [...], hidden: [...]}
            out["layers"] = value
        elif key == "overlay_aesthetic" and isinstance(value, dict):
            out["overlayAesthetic"] = _convert_aesthetic_dict(value)
        else:
            camel_key = mapping.get(key, _to_camel(key))
            out[camel_key] = value
    return out


def _merge_lines_as_path_into_aes(
    aes: ByGroup | ByState | BaseAesthetic | None | MissingType,
    lines_as_path: list[str],
) -> ByGroup | ByState | BaseAesthetic | None | MissingType:
    """Merge lines_as_path regions into aes as PathAesthetic(kind='line').

    For each region in lines_as_path, add a PathAesthetic(kind='line') entry
    to aes.group. User-provided aes takes priority over auto-generated entries.

    Args:
        aes: User-provided aesthetic configuration
        lines_as_path: List of region IDs that contain lines in path notation

    Returns:
        Modified aes with lines_as_path entries merged into group
    """
    if not lines_as_path:
        return aes

    # Build group entries for lines_as_path regions
    line_group_entries: dict[str, ByState | BaseAesthetic | None | MissingType] = {}
    for region_id in lines_as_path:
        line_group_entries[region_id] = PathAesthetic(kind="line")

    # Merge with existing aes
    if isinstance(aes, MissingType) or aes is None:
        # No user aes - create ByGroup with just the line entries
        return ByGroup(**line_group_entries)
    elif isinstance(aes, ByGroup):
        # Merge: user entries take priority
        merged_entries = dict(line_group_entries)
        for key in aes.keys():
            merged_entries[key] = aes[key]
        return ByGroup(**merged_entries)
    elif isinstance(aes, ByState):
        # User provided ByState for global config - wrap in ByGroup and add line entries
        # ByState applies to __all, line entries apply to specific regions
        bystate_entries: dict[str, ByState | BaseAesthetic | None | MissingType] = dict(
            line_group_entries
        )
        bystate_entries["__all"] = aes
        return ByGroup(**bystate_entries)
    elif isinstance(aes, BaseAesthetic):
        # User provided single aesthetic - wrap in ByGroup
        base_entries: dict[str, ByState | BaseAesthetic | None | MissingType] = dict(
            line_group_entries
        )
        base_entries["__all"] = aes
        return ByGroup(**base_entries)
    else:
        return aes


def _convert_aes_to_dict(
    aes: ByGroup | ByState | BaseAesthetic | None | MissingType,
    wash_config: WashConfig | None = None,
) -> dict[str, Any] | None:
    """Convert aesthetic objects to dict format for JavaScript.

    Args:
        aes: Aesthetic configuration (ByGroup, ByState, BaseAesthetic, or None)
        wash_config: Optional wash config for applying defaults

    Returns:
        Dict with keys: base, hover, select, group (ready for _camel_props)
    """
    # Import here to avoid circular dependency
    from ._wash import WashConfig, _convert_to_aes_dict

    # Create empty wash config if not provided
    if wash_config is None:
        wash_config = WashConfig(shape=MISSING, line=MISSING, text=MISSING)

    return _convert_to_aes_dict(wash_config, aes)


def base_input_map(
    id: str,
    geometry: Outline,
    mode: Literal["single", "multiple"] | ModeType,
    *,
    tooltips: TooltipMap = None,
    value: CountMap = None,
    view_box: tuple[float, float, float, float] | None = None,
    aes: ByGroup | ByState | BaseAesthetic | None | MissingType = MISSING,
    wash_config: WashConfig | None = None,
    layers: Mapping[str, list[str]] | None = None,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
) -> TagList:
    """Create an interactive map input component.

    This is the internal base function. Use Wash().input_map() or the
    public input_map() for the full API with aesthetic container support.

    Args:
        id: The input ID.
        geometry: Outline object containing regions and metadata.
        mode: Selection mode (required).
              - "single": Single selection (radio button behavior)
              - "multiple": Multiple selection (checkbox behavior)
              - Single(...): Single with customization
              - Multiple(...): Multiple with customization
              - Cycle(n, ...): Finite state cycling
              - Count(...): Unbounded counting
        tooltips: Tooltip text per region.
        value: Initial values per region {region_id: count}.
        view_box: SVG viewBox override (x, y, width, height).
        aes: Aesthetic configuration (ByGroup, ByState, or BaseAesthetic).
        wash_config: Optional wash config for resolving defaults.
        layers: Layer configuration dict with keys: underlays, overlays, hidden.
        width: CSS width (default: "100%").
        height: CSS height (default: "320px").
        class_: Additional CSS classes.
        style: Additional inline styles.

    Returns:
        TagList containing the input component.
    """
    # Normalize string modes to Mode class instances
    mode_obj: Single | Multiple | Cycle | Count
    if mode == "single":
        mode_obj = Single()
    elif mode == "multiple":
        mode_obj = Multiple()
    elif isinstance(mode, (Single, Multiple, Cycle, Count)):
        mode_obj = mode
    else:
        raise ValueError(
            'mode must be "single", "multiple", or a Mode class instance '
            "(Single, Multiple, Cycle, Count)"
        )

    # Geometry
    vb_tuple = view_box if view_box else geometry.viewbox()
    vb_str = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"
    all_regions = geometry.regions

    # Determine initial value from Mode class if not provided
    effective_value = value
    if effective_value is None:
        if isinstance(mode_obj, Single) and mode_obj.selected is not None:
            effective_value = {mode_obj.selected: 1}
        elif isinstance(mode_obj, Multiple) and mode_obj.selected is not None:
            effective_value = {s: 1 for s in mode_obj.selected}
        elif isinstance(mode_obj, (Cycle, Count)) and mode_obj.values is not None:
            effective_value = mode_obj.values

    # Geometry metadata
    geometry_metadata = None
    if geometry.metadata:
        geometry_metadata = {
            "viewBox": vb_str,
            "groups": geometry.metadata.get("groups"),
        }
        geometry_metadata = {k: v for k, v in geometry_metadata.items() if v is not None}
        if not geometry_metadata:
            geometry_metadata = None

    # Build mode config from Mode object
    mode_config = mode_obj.to_dict()

    # Build layers config (merge with geometry defaults)
    effective_layers = dict(layers) if layers else {}
    if "overlays" not in effective_layers:
        geo_overlays = geometry.overlays()
        if geo_overlays:
            effective_layers["overlays"] = geo_overlays

    # Merge lines_as_path from geometry into aes
    lines_as_path = geometry.metadata.get("lines_as_path", [])
    effective_aes = _merge_lines_as_path_into_aes(aes, lines_as_path)

    # Convert aes objects to dict format
    aes_dict = _convert_aes_to_dict(effective_aes, wash_config)

    # Build props with new nested structure
    props_dict: dict[str, Any] = {
        "geometry": _normalize_outline(all_regions),  # type: ignore[arg-type]
        "tooltips": tooltips,
        "view_box": vb_str,
        "geometry_metadata": geometry_metadata,
        "value": effective_value,
        "mode": mode_config,
        "aes": aes_dict,
        "layers": effective_layers if effective_layers else None,
    }

    props = _camel_props(props_dict)
    mode_type = mode_config["type"]

    div = ui.div(
        id=id,
        class_=_class_names("shinymap-input", class_),
        style=css(**_merge_styles(width, height, style)),
        data_shinymap_input="1",
        data_shinymap_input_id=id,
        data_shinymap_input_mode=mode_type,
        data_shinymap_props=json.dumps(props),
    )

    return TagList(_dependency(), div)


def base_output_map(
    id: str,
    geometry: Outline | None = None,
    *,
    tooltips: TooltipMap = None,
    view_box: tuple[float, float, float, float] | None = None,
    aes: ByGroup | ByState | BaseAesthetic | None | MissingType = MISSING,
    wash_config: WashConfig | None = None,
    layers: Mapping[str, list[str]] | None = None,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
) -> TagList:
    """Skeletal output_map UI placeholder.

    This is the internal base function. Use Wash().output_map() or the
    public output_map() for the full API with aesthetic container support.

    Args:
        id: Output ID for Shiny
        geometry: Outline object with regions
        tooltips: Region tooltips as {region_id: tooltip_text}
        view_box: Override viewBox tuple (x, y, width, height)
        aes: Aesthetic configuration (ByGroup, ByState, or BaseAesthetic).
        wash_config: Optional wash config for resolving defaults.
        layers: Layer configuration as nested dict:
            - underlays: Region IDs to render below main regions
            - overlays: Region IDs to render above main regions
            - hidden: Region IDs to hide
        width: Container width (CSS)
        height: Container height (CSS)
        class_: Additional CSS classes
        style: Additional inline styles
    """
    # Module-level registry for static parameters
    from .ui._ui import _static_map_params

    processed_geometry = None
    processed_view_box = None

    # Extract layers
    underlays = layers.get("underlays") if layers else None
    overlays = layers.get("overlays") if layers else None
    hidden = layers.get("hidden") if layers else None

    if geometry is not None:
        processed_geometry = geometry.regions

        if view_box is None:
            vb_tuple = geometry.viewbox()
        else:
            vb_tuple = view_box
        processed_view_box = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"

        # Use metadata overlays if not explicitly provided
        if overlays is None:
            overlays = geometry.overlays() or None

        # Merge lines_as_path from geometry into aes
        lines_as_path = geometry.metadata.get("lines_as_path", [])
        effective_aes = _merge_lines_as_path_into_aes(aes, lines_as_path)
    else:
        effective_aes = aes
        if view_box is not None:
            processed_view_box = f"{view_box[0]} {view_box[1]} {view_box[2]} {view_box[3]}"

    # Convert aes objects to dict format
    aes_dict = _convert_aes_to_dict(effective_aes, wash_config)

    geometry_metadata = None
    if geometry is not None and geometry.metadata:
        geometry_metadata = {
            "viewBox": processed_view_box,
            "groups": geometry.metadata.get("groups"),
        }
        geometry_metadata = {k: v for k, v in geometry_metadata.items() if v is not None}
        if not geometry_metadata:
            geometry_metadata = None

    static_params: dict[str, Any] = {
        "geometry": processed_geometry,
        "tooltips": tooltips,
        "view_box": processed_view_box,
        "aes": aes_dict,
        "layers": {  # Store as nested dict
            "underlays": underlays,
            "overlays": overlays,
            "hidden": hidden,
        },
        "geometry_metadata": geometry_metadata,
    }
    # Clean up None values in layers
    if static_params["layers"]:
        static_params["layers"] = {
            k: v for k, v in static_params["layers"].items() if v is not None
        }
        if not static_params["layers"]:
            static_params["layers"] = None

    static_params = {k: v for k, v in static_params.items() if v is not None}

    if static_params:
        _static_map_params[id] = static_params

    return TagList(
        _dependency(),
        ui.div(
            ui.output_ui(id),
            class_=_class_names("shinymap-output-container", class_),
            style=css(**_merge_styles(width, height, style)),
        ),
    )


def base_render_map(fn=None):
    """Base Shiny render decorator for map outputs."""
    # Import here to avoid circular dependency
    from ._map import MapBuilder
    from .ui._ui import _apply_static_params, _render_map_ui

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
                return _render_map_ui(val, _include_dependency=False)

            output_id = func.__name__
            builder = _apply_static_params(builder, output_id)

            return _render_map_ui(builder, _include_dependency=False)

        return wrapper

    if fn is None:
        return decorator

    return decorator(fn)


__all__ = ["base_input_map", "base_output_map", "base_render_map"]
