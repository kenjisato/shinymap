from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, Any

from htmltools import Tag, TagList, css
from shiny import ui
from shiny.session import Session, require_active_session

from ._base import (
    CountMap,
    TooltipMap,
    _camel_props,
    _class_names,
    _dependency,
    _merge_styles,
    _normalize_geometry,
)

if TYPE_CHECKING:
    from .geometry import Geometry

Selection = str | list[str] | None

# Module-level registry for static parameters from output_map()
_static_map_params: MutableMapping[str, Mapping[str, Any]] = {}


def _viewbox_to_str(view_box: tuple[float, float, float, float] | str | None) -> str | None:
    """Convert viewBox tuple to string format, or pass through string."""
    if view_box is None:
        return None
    if isinstance(view_box, str):
        return view_box
    return f"{view_box[0]} {view_box[1]} {view_box[2]} {view_box[3]}"


# Public input_map uses wash() with sensible defaults
# Defined at module level after all helper definitions
# See end of file for: input_map = _default_wash.input_map


class MapBuilder:
    """Fluent builder for constructing map payloads with method chaining.

    Parameters can be provided here or via output_map(). When both are provided,
    builder parameters take precedence.

    Example (traditional):
        @render_map
        def my_map():
            return (
                Map(geometry, tooltips=tooltips, view_box=viewbox)
                .with_value(my_counts)
                .with_active(active_ids)
            )

    Example (with static params in output_map()):
        # UI layer
        output_map("my_map", geometry=GEOMETRY, tooltips=TOOLTIPS, view_box=VIEWBOX)

        # Server layer
        @render_map
        def my_map():
            return Map().with_value(my_counts)
    """

    def __init__(
        self,
        regions: Mapping[str, Any] | None = None,
        *,
        tooltips: TooltipMap = None,
        view_box: tuple[float, float, float, float] | None = None,
    ):
        """Internal constructor - use Map() function instead.

        Args:
            regions: Dict of main regions {regionId: [element1, ...]}
            tooltips: Optional region tooltips
            view_box: ViewBox as tuple (x, y, width, height)
        """
        self._regions: Mapping[str, Any] | None = regions
        self._tooltips = tooltips
        self._value: CountMap = None
        self._active_ids: Selection = None
        self._view_box = view_box
        self._aes: Mapping[str, Mapping[str, Any] | None] | None = None
        self._layers: Mapping[str, list[str] | None] | None = None

    def with_tooltips(self, tooltips: TooltipMap) -> MapBuilder:
        """Set region tooltips."""
        self._tooltips = tooltips
        return self

    def with_value(self, value: CountMap) -> MapBuilder:
        """Set region values (counts, selection state)."""
        self._value = value
        return self

    def with_active(self, active_ids: Selection) -> MapBuilder:
        """Set active/highlighted region IDs."""
        self._active_ids = active_ids
        return self

    def with_view_box(self, view_box: tuple[float, float, float, float]) -> MapBuilder:
        """Set the SVG viewBox as tuple (x, y, width, height)."""
        self._view_box = view_box
        return self

    def with_aes(self, aes: Mapping[str, Mapping[str, Any] | None]) -> MapBuilder:
        """Set aesthetic configuration.

        Args:
            aes: Nested dict with keys like 'base', 'hover', 'group'
        """
        self._aes = aes
        return self

    def with_layers(self, layers: Mapping[str, list[str] | None]) -> MapBuilder:
        """Set layer configuration.

        Args:
            layers: Nested dict with keys 'underlays', 'overlays', 'hidden'
        """
        self._layers = layers
        return self

    def with_geometry_metadata(self, metadata: Mapping[str, Any]) -> MapBuilder:
        """Set geometry metadata (viewBox, groups)."""
        self._geometry_metadata = metadata
        return self

    def as_json(self) -> Mapping[str, Any]:
        """Convert to JSON dict for JavaScript consumption."""
        data: dict[str, Any] = {}

        if self._regions is not None:
            data["geometry"] = _normalize_geometry(self._regions)
        if self._tooltips is not None:
            data["tooltips"] = self._tooltips
        if self._value is not None:
            data["value"] = self._value
        if self._active_ids is not None:
            data["active_ids"] = self._active_ids
        if self._view_box is not None:
            data["view_box"] = _viewbox_to_str(self._view_box)
        if self._aes is not None:
            data["aes"] = self._aes
        if self._layers is not None:
            data["layers"] = self._layers
        if hasattr(self, "_geometry_metadata") and self._geometry_metadata is not None:
            data["geometry_metadata"] = self._geometry_metadata

        return _camel_props(data)


def Map(
    geometry: Geometry | None = None,
    *,
    view_box: tuple[float, float, float, float] | None = None,
    tooltips: dict[str, str] | None = None,
    value: dict[str, int] | None = None,
    active: list[str] | None = None,
    aes: Mapping[str, Mapping[str, Any] | None] | None = None,
    layers: Mapping[str, list[str] | None] | None = None,
) -> MapBuilder:
    """Create map from Geometry object.

    When used with output_map() that provides static geometry, you can call Map()
    without arguments. Otherwise, provide a Geometry object.

    Args:
        geometry: Geometry object with regions, viewBox, metadata.
            Optional when used with output_map()
        view_box: Override viewBox tuple (for zoom/pan).
            If None, uses geometry.viewbox()
        tooltips: Region tooltips
        value: Region values (counts, selection state)
        active: Active region IDs
        aes: Aesthetic configuration (nested dict: base, hover, group)
        layers: Layer configuration (nested dict: underlays, overlays, hidden)

    Example:
        # Standalone usage
        geo = Geometry.from_dict(data)
        Map(geo, value=counts, active=["a", "b"])

        # With output_map() providing static geometry
        output_map("my_map", GEOMETRY, tooltips=TOOLTIPS)
        @render_map
        def my_map():
            return Map().with_value(counts)

    Returns:
        MapBuilder instance for method chaining
    """

    if geometry is None:
        # No geometry provided - will be merged from output_map() static params
        builder = MapBuilder(
            None,  # Will be filled by _apply_static_params
            view_box=view_box,
            tooltips=tooltips,
        )
    else:
        # Extract regions using Geometry methods
        main_regions = geometry.main_regions()

        # Create MapBuilder with extracted data
        builder = MapBuilder(
            main_regions,
            view_box=view_box or geometry.viewbox(),
            tooltips=tooltips,
        )

    # Apply optional parameters
    if value is not None:
        builder = builder.with_value(value)
    if active is not None:
        builder = builder.with_active(active)
    if aes is not None:
        builder = builder.with_aes(aes)
    if layers is not None:
        builder = builder.with_layers(layers)

    return builder


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


# Public output_map uses wash() with sensible defaults
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

    # Merge aes: builder values override static
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


# Public render_map uses wash() with sensible defaults
# Defined at module level after all helper definitions
# See end of file for: render_map = _default_wash.render_map


def update_map(
    id: str,
    *,
    # Aesthetics (both input_map and output_map)
    fill_color: str | Mapping[str, str] | None = None,
    stroke_width: float | Mapping[str, float] | None = None,
    stroke_color: str | Mapping[str, str] | None = None,
    fill_opacity: float | Mapping[str, float] | None = None,
    aes_base: Mapping[str, Any] | None = None,
    aes_hover: Mapping[str, Any] | None = None,
    # Input-specific parameters
    value: CountMap = None,  # Selection state (pass {} to clear all)
    aes_select: Mapping[str, Any] | None = None,
    cycle: int | None = None,
    max_selection: int | None = None,
    # Common
    tooltips: TooltipMap = None,
    session: Session | None = None,
) -> None:
    """Update an input_map or output_map without full re-render.

    For input_map: Updates aesthetics, selection state, and input behavior parameters.
    For output_map: Updates aesthetics only (use @render_map for data changes).

    Args:
        id: The map element ID
        fill_color: Fill color (string for all regions, dict for per-region)
        stroke_width: Stroke width (number for all, dict for per-region)
        stroke_color: Stroke color (string for all, dict for per-region)
        fill_opacity: Fill opacity (number for all, dict for per-region)
        aes_base: Base aesthetic for all regions
        aes_hover: Hover aesthetic
        value: (input_map only) Selection state; pass {} to clear all selections
        aes_select: (input_map only) Aesthetic override for selected regions
        cycle: (input_map only) Cycle count for click behavior
        max_selection: (input_map only) Maximum number of selectable regions
        tooltips: Region tooltips
        session: A Session instance. If not provided, it is inferred via get_current_session()

    Example:
        # Update aesthetics (works for both input_map and output_map)
        update_map("my_map", fill_color=new_colors, stroke_width=2.0)

        # Clear all selections (input_map only)
        update_map("my_map", value={})

        # Set specific selections (input_map only)
        update_map("my_map", value={"region1": 1, "region2": 1})

        # Change input behavior (input_map only)
        update_map("my_map", max_selection=3, cycle=5)

    Note:
        - Uses shallow merge semantics: new properties override existing ones
        - Properties not specified are left unchanged
        - For output_map data updates, use @render_map re-execution instead
    """
    session = require_active_session(session)

    # Build update payload
    updates: dict[str, Any] = {}

    if fill_color is not None:
        updates["fill_color"] = fill_color
    if stroke_width is not None:
        updates["stroke_width"] = stroke_width
    if stroke_color is not None:
        updates["stroke_color"] = stroke_color
    if fill_opacity is not None:
        updates["fill_opacity"] = fill_opacity
    if aes_base is not None:
        updates["aes_base"] = aes_base
    if aes_select is not None:
        updates["aes_select"] = aes_select
    if aes_hover is not None:
        updates["aes_hover"] = aes_hover
    if value is not None:
        updates["value"] = value
    if cycle is not None:
        updates["cycle"] = cycle
    if max_selection is not None:
        updates["max_selection"] = max_selection
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

from . import aes  # noqa: E402
from ._wash import wash  # noqa: E402
from .relative import PARENT  # noqa: E402

# Create default wash instance with library defaults for base, select, hover.
# These defaults are applied when using the library-supplied input_map/output_map.
# Users who create their own wash() must define all aesthetics themselves.
#
# Design notes:
# - TypeScript has two sets of defaults:
#   1. DEFAULT_AESTHETIC_VALUES: reserved/subtle for user-defined wash layers
#   2. LIBRARY_AESTHETIC_DEFAULTS: complete defaults for React developers
# - Library defaults here provide a complete, polished out-of-box experience
# - No hardcoded fallbacks in shinymap-shiny.js - everything flows from Python
_default_wash = wash(
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
    geometry: Geometry,
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
        geometry: Geometry object with regions
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
        >>> from shinymap.geometry import Geometry
        >>>
        >>> geo = Geometry.from_dict(data)
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
    geometry: Geometry,
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
        geometry: Geometry object with regions
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
        >>> from shinymap.geometry import Geometry
        >>>
        >>> geo = Geometry.from_dict(data)
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
