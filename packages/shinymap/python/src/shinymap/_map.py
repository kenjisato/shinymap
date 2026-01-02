"""Map data model for shinymap.

This module provides the core Map/MapBuilder classes for constructing
map payloads that can be rendered by UI components.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from .aes._core import BaseAesthetic, ByGroup, ByState
from .types import CountMap, TooltipMap
from .uicore._util import _normalize_outline, _strip_none

if TYPE_CHECKING:
    from .geometry import Outline

# Type aliases
AesType = ByGroup | ByState | BaseAesthetic | Mapping[str, Mapping[str, Any] | None] | None


def _viewbox_to_str(view_box: tuple[float, float, float, float] | str | None) -> str | None:
    """Convert viewBox tuple to string format, or pass through string."""
    if view_box is None:
        return None
    if isinstance(view_box, str):
        return view_box
    return f"{view_box[0]} {view_box[1]} {view_box[2]} {view_box[3]}"


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
        self._view_box = view_box
        self._aes: AesType = None
        self._layers: Mapping[str, list[str] | None] | None = None

    def with_tooltips(self, tooltips: TooltipMap) -> MapBuilder:
        """Set region tooltips."""
        self._tooltips = tooltips
        return self

    def with_value(self, value: CountMap) -> MapBuilder:
        """Set region values (counts, selection state).

        Values determine both visual state and selection:
        - value = 0: not selected (base aesthetic)
        - value > 0: selected (select aesthetic applied)
        """
        self._value = value
        return self

    def with_view_box(self, view_box: tuple[float, float, float, float]) -> MapBuilder:
        """Set the SVG viewBox as tuple (x, y, width, height)."""
        self._view_box = view_box
        return self

    def with_aes(self, aes: AesType) -> MapBuilder:
        """Set aesthetic configuration.

        Args:
            aes: Aesthetic config (ByGroup, ByState, BaseAesthetic, or dict)
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
        """Convert to JSON dict for JavaScript consumption.

        Returns snake_case keys. JavaScript (shinymap-shiny.js) handles
        conversion to camelCase.
        """
        data: dict[str, Any] = {}

        if self._regions is not None:
            data["geometry"] = _normalize_outline(self._regions)
        if self._tooltips is not None:
            data["tooltips"] = self._tooltips
        if self._value is not None:
            data["value"] = self._value
        if self._view_box is not None:
            data["view_box"] = _viewbox_to_str(self._view_box)
        if self._aes is not None:
            # Use to_js_dict() for aes objects, pass through dicts
            if hasattr(self._aes, "to_js_dict"):
                data["aes"] = self._aes.to_js_dict()
            elif hasattr(self._aes, "to_dict"):
                data["aes"] = self._aes.to_dict()
            else:
                data["aes"] = self._aes
        if self._layers is not None:
            data["layers"] = self._layers
        if hasattr(self, "_geometry_metadata") and self._geometry_metadata is not None:
            data["geometry_metadata"] = self._geometry_metadata

        return _strip_none(data)


def Map(
    geometry: Outline | None = None,
    *,
    view_box: tuple[float, float, float, float] | None = None,
    tooltips: dict[str, str] | None = None,
    value: dict[str, int] | None = None,
    aes: AesType = None,
    layers: Mapping[str, list[str] | None] | None = None,
) -> MapBuilder:
    """Create map from Outline object.

    When used with output_map() that provides static geometry, you can call Map()
    without arguments. Otherwise, provide an Outline object.

    Args:
        geometry: Outline object with regions, viewBox, metadata.
            Optional when used with output_map()
        view_box: Override viewBox tuple (for zoom/pan).
            If None, uses geometry.viewbox()
        tooltips: Region tooltips
        value: Region values (counts, selection state).
            Values determine both visual state and selection:
            - value = 0: not selected (base aesthetic)
            - value > 0: selected (select aesthetic applied)
        aes: Aesthetic configuration (ByGroup, ByState, BaseAesthetic, or dict)
        layers: Layer configuration (nested dict: underlays, overlays, hidden)

    Example:
        # Standalone usage
        geo = Outline.from_dict(data)
        Map(geo, value={"a": 1, "b": 1, "c": 0})

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
        # Extract regions using Outline methods
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
    if aes is not None:
        builder = builder.with_aes(aes)
    if layers is not None:
        builder = builder.with_layers(layers)

    return builder
