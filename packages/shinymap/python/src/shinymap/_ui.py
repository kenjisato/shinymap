from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping
from dataclasses import asdict, dataclass
from functools import wraps
from typing import TYPE_CHECKING, Any

from htmltools import HTMLDependency, Tag, TagList, css
from shiny import render, ui
from shiny.session import Session, require_active_session

from . import __version__

if TYPE_CHECKING:
    from .geometry import Geometry

GeometryMap = Mapping[str, str | list[str]]
TooltipMap = Mapping[str, str] | None
FillMap = str | Mapping[str, str] | None
CountMap = Mapping[str, int] | None
Selection = str | list[str] | None

# Module-level registry for static parameters from output_map()
_static_map_params: MutableMapping[str, Mapping[str, Any]] = {}


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


def _drop_nones(data: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def _normalize_geometry(geometry: GeometryMap) -> Mapping[str, str]:
    """Normalize geometry to flat string format for JavaScript.

    Accepts both formats:
    - Flat strings: {"id": "M 0 0 L 10 10"}
    - List format: {"id": ["M 0 0 L 10 10", "M 20 20 L 30 30"]}

    Returns flat strings joined with spaces.
    """
    return {
        region_id: " ".join(paths) if isinstance(paths, list) else paths
        for region_id, paths in geometry.items()
    }


def _normalize_fills(fills: FillMap, geometry: GeometryMap) -> Mapping[str, str] | None:
    """Normalize fills to a dict. If fills is a string, apply to all regions."""
    if fills is None:
        return None
    if isinstance(fills, str):
        return {region_id: fills for region_id in geometry.keys()}
    return fills


def _to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _camel_props(data: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Convert snake_case to camelCase (singular, consistent naming)."""
    mapping = {
        "max_selection": "maxSelection",
        "view_box": "viewBox",
        "default_aesthetic": "defaultAesthetic",
        "active_ids": "activeIds",
        "hover_highlight": "hoverHighlight",
        "selected_aesthetic": "selectedAesthetic",
        "fill_color": "fillColor",  # Singular, consistent with TS/JS
        "stroke_width": "strokeWidth",  # Singular, works for dict or scalar
        "stroke_color": "strokeColor",  # Singular
        "fill_opacity": "fillOpacity",  # Singular
        "fill_color_selected": "fillColorSelected",
        "fill_color_not_selected": "fillColorNotSelected",
        "count_palette": "countPalette",
        "overlay_geometry": "overlayGeometry",
        "overlay_aesthetic": "overlayAesthetic",
    }

    # Keys whose values are aesthetic dicts that need recursive conversion
    aesthetic_keys = {"default_aesthetic", "hover_highlight", "selected_aesthetic",
                      "overlay_aesthetic", "fill_color_selected", "fill_color_not_selected"}

    out: MutableMapping[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        camel_key = mapping.get(key)
        if camel_key:
            # Recursively convert aesthetic dicts
            if key in aesthetic_keys and isinstance(value, dict):
                out[camel_key] = {_to_camel(k): v for k, v in value.items()}
            else:
                out[camel_key] = value
        else:
            # Auto-convert any unmapped snake_case keys
            out[_to_camel(key)] = value
    return out


def input_map(
    id: str,
    geometry: "Geometry",
    *,
    tooltips: TooltipMap = None,
    fill_color: FillMap = None,
    mode: str | None = "multiple",
    value: CountMap = None,
    cycle: int | None = None,
    max_selection: int | None = None,
    view_box: tuple[float, float, float, float] | None = None,
    default_aesthetic: Mapping[str, Any] | None = None,
    hover_highlight: Mapping[str, Any] | None = None,
    selected_aesthetic: Mapping[str, Any] | None = None,
    overlay_aesthetic: Mapping[str, Any] | None = None,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
) -> TagList:
    """Create interactive map from Geometry object (OOP approach - recommended).

    For mode="single": returns a string (single selected region ID) or None
    For mode="multiple": returns a list of selected region IDs
    For mode="count": returns a dict mapping region IDs to counts

    The underlying value is always a count map (dict[str, int]), but Shiny
    automatically transforms it based on the mode using a value function.

    Args:
        id: Input ID for Shiny
        geometry: Geometry object
        mode: Interaction mode ("single", "multiple", "count")
        view_box: Override viewBox tuple. If None, uses geometry.viewbox()
        fill_color: Fill colors
        hover_highlight: Styling for hover state. Supported keys: fill_color, stroke_color, stroke_width.
            Note: Opacity changes (fill_opacity, stroke_opacity) have no visual effect because
            hover creates an overlay copy on top of the original region.
        selected_aesthetic: Styling for selected regions
        overlay_aesthetic: Styling for overlay regions (non-interactive paths like borders, dividers).
            Automatically extracts overlay regions from Geometry object if present.

    Example:
        from shinymap import input_map
        from shinymap.geometry import Geometry

        geo = Geometry.from_dict(data)
        input_map("my_map", geo, mode="multiple")
        input_map("my_map", geo, view_box=(10, 10, 80, 80))  # Zoom

    Aesthetic precedence (highest to lowest):
    1. Explicit parameters passed to this function
    2. Configured theme from configure_theme()
    3. System defaults from React components
    """
    # Get configured theme and apply defaults for parameters not explicitly provided
    from ._theme import get_theme_config

    theme_config = get_theme_config()

    if hover_highlight is None and "hover_highlight" in theme_config:
        hover_highlight = theme_config["hover_highlight"]
    if selected_aesthetic is None and "selected_aesthetic" in theme_config:
        selected_aesthetic = theme_config["selected_aesthetic"]
    if default_aesthetic is None and "default_aesthetic" in theme_config:
        default_aesthetic = theme_config["default_aesthetic"]
    if fill_color is None and "fill_color" in theme_config:
        fill_color = theme_config["fill_color"]

    if mode not in {None, "single", "multiple", "count"}:
        raise ValueError('mode must be one of "single", "multiple", "count", or None')

    # Validate hover_highlight - opacity changes don't work with overlay-based hover
    if hover_highlight is not None:
        import warnings
        invalid_keys = {"fill_opacity", "fillOpacity", "stroke_opacity", "strokeOpacity"}
        found_invalid = invalid_keys & set(hover_highlight.keys())
        if found_invalid:
            warnings.warn(
                f"hover_highlight contains opacity keys {found_invalid} which have no visual effect. "
                f"Hover creates an overlay copy, so opacity changes are not visible. "
                f"Use fill_color or stroke_color instead.",
                UserWarning,
                stacklevel=2,
            )

    # Extract viewBox
    vb_tuple = view_box if view_box else geometry.viewbox()

    # Extract main regions and overlay regions using Geometry methods
    main_regions = geometry.main_regions()
    overlay_regions_dict = geometry.overlay_regions()

    # Convert tuple viewBox to string for React (temporary)
    vb_str = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"

    # Mode presets mirror the React InputMap defaults.
    effective_cycle = cycle
    effective_max_selection = max_selection
    if mode == "single":
        effective_cycle = 2 if cycle is None else cycle
        effective_max_selection = 1 if max_selection is None else max_selection
    elif mode == "multiple":
        effective_cycle = 2 if cycle is None else cycle
        effective_max_selection = max_selection
    elif mode == "count":
        effective_cycle = cycle
        effective_max_selection = max_selection

    props = _camel_props(
        {
            "geometry": main_regions,
            "tooltips": tooltips,
            "fill_color": _normalize_fills(fill_color, main_regions),
            "mode": mode,
            "value": value,
            "cycle": effective_cycle,
            "max_selection": effective_max_selection,
            "view_box": vb_str,
            "default_aesthetic": default_aesthetic,
            "hover_highlight": hover_highlight,
            "selected_aesthetic": selected_aesthetic,
            "overlay_geometry": overlay_regions_dict if overlay_regions_dict else None,
            "overlay_aesthetic": overlay_aesthetic,
        }
    )

    # Store mode in data attribute for value transformation
    div = ui.div(
        id=id,
        class_=_class_names("shinymap-input", class_),
        style=css(**_merge_styles(width, height, style)),
        data_shinymap_input="1",
        data_shinymap_input_id=id,
        data_shinymap_input_mode=mode,  # Store mode for JS value transformation
        data_shinymap_props=json.dumps(props),
    )

    return TagList(_dependency(), div)


@dataclass
class MapPayload:
    geometry: GeometryMap | None = None  # Can be None if provided via output_map()
    tooltips: TooltipMap = None
    fill_color: str | Mapping[str, str] | None = None  # RENAMED from fills
    stroke_width: float | Mapping[str, float] | None = None  # NEW (dict support)
    stroke_color: str | Mapping[str, str] | None = None  # NEW
    fill_opacity: float | Mapping[str, float] | None = None  # NEW
    counts: CountMap = None
    active_ids: Selection = None
    view_box: str | None = None
    default_aesthetic: Mapping[str, Any] | None = None
    # Selection-specific aesthetics (RENAMED for consistency)
    fill_color_selected: Mapping[str, Any] | None = None  # RENAMED from selection_aesthetic
    fill_color_not_selected: Mapping[str, Any] | None = None  # RENAMED from not_selection_aesthetic
    # Overlay layer for non-interactive annotations (dividers, borders, grids)
    overlay_geometry: GeometryMap | None = None
    overlay_aesthetic: Mapping[str, Any] | None = None
    # Count palette (for later hover support)
    count_palette: list[str] | None = None

    def as_json(self) -> Mapping[str, Any]:
        data = asdict(self)
        # Normalize geometry from list format to flat strings for JavaScript
        if self.geometry is not None:
            data["geometry"] = _normalize_geometry(self.geometry)
        if self.overlay_geometry is not None:
            data["overlay_geometry"] = _normalize_geometry(self.overlay_geometry)
        # Normalize fill_color if it's a string (only if geometry is available)
        if isinstance(data.get("fill_color"), str) and self.geometry is not None:
            data["fill_color"] = _normalize_fills(data["fill_color"], self.geometry)
        return _camel_props(_drop_nones(data))


class MapBuilder:
    """Fluent builder for constructing map payloads with method chaining.

    Parameters can be provided here or via output_map(). When both are provided,
    builder parameters take precedence.

    Example (traditional):
        @render_map
        def my_map():
            return (
                Map(geometry, tooltips=tooltips, view_box=viewbox)
                .with_fill_color(my_fill_colors)
                .with_counts(my_counts)
            )

    Example (with static params in output_map()):
        # UI layer
        output_map("my_map", geometry=GEOMETRY, tooltips=TOOLTIPS, view_box=VIEWBOX)

        # Server layer
        @render_map
        def my_map():
            return Map().with_fill_color(my_fill_colors).with_counts(my_counts)
    """

    def __init__(
        self,
        regions: GeometryMap | None = None,
        *,
        tooltips: TooltipMap = None,
        view_box: tuple[float, float, float, float] | None = None,
        overlay_regions: GeometryMap | None = None,
        overlay_aesthetic: Mapping[str, Any] | None = None,
    ):
        """Internal constructor - use Map() function instead.

        Args:
            regions: Dict of main regions {regionId: [path1, ...]}
            tooltips: Optional region tooltips
            view_box: ViewBox as tuple (x, y, width, height)
            overlay_regions: Optional overlay dict
            overlay_aesthetic: Optional overlay styling
        """
        self._regions = regions
        self._tooltips = tooltips
        self._fill_color: str | Mapping[str, str] | None = None
        self._stroke_width: float | Mapping[str, float] | None = None
        self._stroke_color: str | Mapping[str, str] | None = None
        self._fill_opacity: float | Mapping[str, float] | None = None
        self._counts: CountMap = None
        self._active_ids: Selection = None
        self._view_box = view_box  # Always tuple or None
        self._default_aesthetic: Mapping[str, Any] | None = None
        self._overlay_regions = overlay_regions
        self._overlay_aesthetic = overlay_aesthetic

    def with_tooltips(self, tooltips: TooltipMap) -> MapBuilder:
        """Set region tooltips."""
        self._tooltips = tooltips
        return self

    def with_fill_color(
        self,
        fill_color: str | Mapping[str, str],
    ) -> "MapBuilder":
        """Set fill color (global string or per-region dict). Merges if called multiple times.

        Examples:
            .with_fill_color("red")  # All regions red
            .with_fill_color({"a": "red", "b": "blue"})  # Per-region
            .with_fill_color("#cccccc").with_fill_color({"selected": "yellow"})  # Base + override
        """
        if fill_color is None:
            return self

        # Normalize to dict (only if regions is available)
        if self._regions is not None:
            normalized = _normalize_fills(fill_color, self._regions)
        else:
            # If regions not yet available, store as-is (will normalize in _apply_static_params)
            normalized = fill_color if isinstance(fill_color, dict) else None

        # Merge with existing
        if self._fill_color is None:
            self._fill_color = normalized if normalized else fill_color
        else:
            if self._regions is not None:
                existing_normalized = _normalize_fills(self._fill_color, self._regions)
                if existing_normalized and normalized:
                    self._fill_color = {**existing_normalized, **normalized}
                elif normalized:
                    self._fill_color = normalized
            else:
                # Without regions, just use the new value
                self._fill_color = fill_color

        return self

    def with_counts(self, counts: CountMap) -> MapBuilder:
        """Set region count badges."""
        self._counts = counts
        return self

    def with_active(self, active_ids: Selection) -> MapBuilder:
        """Set active/highlighted region IDs."""
        self._active_ids = active_ids
        return self

    def with_view_box(self, view_box: str) -> MapBuilder:
        """Set the SVG viewBox."""
        self._view_box = view_box
        return self

    def with_stroke_width(
        self,
        stroke_width: float | Mapping[str, float],
    ) -> "MapBuilder":
        """Set stroke width (global float or per-region dict).

        Examples:
            .with_stroke_width(2.0)  # All regions
            .with_stroke_width({"a": 3.0, "b": 1.0})  # Per-region
        """
        if isinstance(stroke_width, dict):
            # Per-region dict
            self._stroke_width = stroke_width
        else:
            # Global: store in default_aesthetic
            if self._default_aesthetic is None:
                self._default_aesthetic = {}
            self._default_aesthetic = {**self._default_aesthetic, "strokeWidth": stroke_width}
        return self

    def with_stroke_color(
        self,
        stroke_color: str | Mapping[str, str],
    ) -> "MapBuilder":
        """Set stroke color (global string or per-region dict).

        Examples:
            .with_stroke_color("#1f2937")  # All regions
            .with_stroke_color({"a": "red", "b": "blue"})  # Per-region
        """
        if isinstance(stroke_color, str):
            # Global: store in default_aesthetic
            if self._default_aesthetic is None:
                self._default_aesthetic = {}
            self._default_aesthetic = {**self._default_aesthetic, "strokeColor": stroke_color}
        else:
            # Per-region dict
            self._stroke_color = stroke_color
        return self

    def with_fill_opacity(
        self,
        fill_opacity: float | Mapping[str, float],
    ) -> "MapBuilder":
        """Set fill opacity (global float or per-region dict).

        Examples:
            .with_fill_opacity(0.8)  # All regions
            .with_fill_opacity({"a": 0.9, "b": 0.5})  # Per-region
        """
        if isinstance(fill_opacity, dict):
            # Per-region dict
            self._fill_opacity = fill_opacity
        else:
            # Global: store in default_aesthetic
            if self._default_aesthetic is None:
                self._default_aesthetic = {}
            self._default_aesthetic = {**self._default_aesthetic, "fillOpacity": fill_opacity}
        return self

    def with_aesthetic(self, **kwargs: Any) -> MapBuilder:
        """Set default aesthetic properties (strokeWidth, fillOpacity, etc.)."""
        if self._default_aesthetic is None:
            self._default_aesthetic = {}
        self._default_aesthetic = {**self._default_aesthetic, **kwargs}
        return self

    def build(self) -> MapPayload:
        """Build and return the MapPayload."""
        # Convert tuple viewBox to string for serialization (temporary until React updated)
        view_box_str = None
        if self._view_box:
            view_box_str = f"{self._view_box[0]} {self._view_box[1]} {self._view_box[2]} {self._view_box[3]}"

        return MapPayload(
            geometry=self._regions,
            tooltips=self._tooltips,
            fill_color=self._fill_color,
            fill_opacity=self._fill_opacity,
            stroke_color=self._stroke_color,
            stroke_width=self._stroke_width,
            counts=self._counts,
            active_ids=self._active_ids,
            view_box=view_box_str,
            default_aesthetic=self._default_aesthetic,
            overlay_geometry=self._overlay_regions,
            overlay_aesthetic=self._overlay_aesthetic,
        )

    def as_json(self) -> Mapping[str, Any]:
        """Convert to JSON dict (for use with render_map)."""
        return self.build().as_json()


def Map(
    geometry: "Geometry | None" = None,
    *,
    view_box: tuple[float, float, float, float] | None = None,
    tooltips: dict[str, str] | None = None,
    fill_color: dict[str, str] | str | None = None,
    counts: dict[str, int] | None = None,
    active: list[str] | None = None,
) -> MapBuilder:
    """Create map from Geometry object.

    When used with output_map() that provides static geometry, you can call Map()
    without arguments. Otherwise, provide a Geometry object.

    Args:
        geometry: Geometry object with regions, viewBox, metadata. Optional when used with output_map()
        view_box: Override viewBox tuple (for zoom/pan). If None, uses geometry.viewbox()
        tooltips: Region tooltips
        fill_color: Fill colors (string for all, dict for per-region)
        counts: Count badges per region
        active: Active region IDs

    Example:
        # Standalone usage
        geo = Geometry.from_dict(data)
        Map(geo, fill_color=colors, counts=counts)

        # With output_map() providing static geometry
        output_map("my_map", GEOMETRY, tooltips=TOOLTIPS)
        @render_map
        def my_map():
            return Map().with_fill_color(colors)  # No geometry needed

    Returns:
        MapBuilder instance for method chaining
    """
    from .geometry import Geometry as GeometryClass

    if geometry is None:
        # No geometry provided - will be merged from output_map() static params
        builder = MapBuilder(
            None,  # Will be filled by _apply_static_params
            view_box=view_box,
            overlay_regions=None,
            tooltips=tooltips,
        )
    else:
        # Extract regions using Geometry methods
        main_regions = geometry.main_regions()
        overlay_regions_dict = geometry.overlay_regions()

        # Create MapBuilder with extracted data
        builder = MapBuilder(
            main_regions,
            view_box=view_box or geometry.viewbox(),
            overlay_regions=overlay_regions_dict if overlay_regions_dict else None,
            tooltips=tooltips,
        )

    # Apply optional styling
    if fill_color is not None:
        builder = builder.with_fill_color(fill_color)
    if counts is not None:
        builder = builder.with_counts(counts)
    if active is not None:
        builder = builder.with_active(active)

    return builder


class MapSelectionBuilder(MapBuilder):
    """Specialized builder for selection highlighting patterns.

    Parameters can be provided here or via output_map(). When both are provided,
    builder parameters take precedence.

    Example (traditional):
        MapSelection(geometry, selected="region1", tooltips=tooltips)
            .with_fill_color("#e2e8f0")
            .with_fill_color_selected("#fbbf24")

    Example (with static params in output_map()):
        # UI layer
        output_map("my_map", geometry=GEOMETRY, tooltips=TOOLTIPS, view_box=VIEWBOX)

        # Server layer
        @render_map
        def my_map():
            return MapSelection(selected=input.selected()).with_fill_color_selected("#fbbf24")
    """

    def __init__(
        self,
        geometry: GeometryMap | None = None,
        selected: Selection = None,
        *,
        tooltips: TooltipMap = None,
        view_box: tuple[float, float, float, float] | None = None,
        overlay_regions: GeometryMap | None = None,
        overlay_aesthetic: Mapping[str, Any] | None = None,
    ):
        super().__init__(geometry, tooltips=tooltips, view_box=view_box, overlay_regions=overlay_regions, overlay_aesthetic=overlay_aesthetic)
        self._selected = selected
        self._fill_color_selected: Mapping[str, Any] | None = None
        self._fill_color_not_selected: Mapping[str, Any] | None = None

    # Type overrides for method chaining
    def with_fill_color(self, fill_color: str | Mapping[str, str]) -> "MapSelectionBuilder":
        super().with_fill_color(fill_color)
        return self

    def with_fill_opacity(self, fill_opacity: float | Mapping[str, float]) -> "MapSelectionBuilder":
        super().with_fill_opacity(fill_opacity)
        return self

    def with_stroke_color(self, stroke_color: str | Mapping[str, str]) -> "MapSelectionBuilder":
        super().with_stroke_color(stroke_color)
        return self

    def with_stroke_width(self, stroke_width: float | Mapping[str, float]) -> "MapSelectionBuilder":
        super().with_stroke_width(stroke_width)
        return self

    def with_fill_color_selected(
        self,
        fill: str | Mapping[str, Any],
    ) -> "MapSelectionBuilder":
        """Set aesthetic for selected regions.

        Can be a color string or full aesthetic dict:
            .with_fill_color_selected("#fbbf24")
            .with_fill_color_selected({"fillColor": "#fbbf24", "strokeWidth": 2})
        """
        if isinstance(fill, str):
            self._fill_color_selected = {"fillColor": fill}
        else:
            self._fill_color_selected = fill
        return self

    def with_fill_color_not_selected(
        self,
        fill: str | Mapping[str, Any],
    ) -> "MapSelectionBuilder":
        """Set aesthetic for non-selected regions.

        Can be a color string or full aesthetic dict:
            .with_fill_color_not_selected("#e2e8f0")
            .with_fill_color_not_selected({"fillColor": "#e2e8f0", "fillOpacity": 0.5})
        """
        if isinstance(fill, str):
            self._fill_color_not_selected = {"fillColor": fill}
        else:
            self._fill_color_not_selected = fill
        return self

    def build(self) -> MapPayload:
        """Build payload with selection-specific aesthetics."""
        return MapPayload(
            geometry=self._regions,
            tooltips=self._tooltips,
            fill_color=self._fill_color,
            fill_opacity=self._fill_opacity,
            stroke_color=self._stroke_color,
            stroke_width=self._stroke_width,
            counts=self._counts,
            active_ids=self._selected,  # Mark selected regions as active
            view_box=self._view_box,
            default_aesthetic=self._default_aesthetic,
            fill_color_selected=self._fill_color_selected,
            fill_color_not_selected=self._fill_color_not_selected,
            overlay_geometry=self._overlay_regions,
            overlay_aesthetic=self._overlay_aesthetic,
        )


# Alias for shorter usage
def MapSelection(
    geometry: "Geometry | None" = None,
    selected: Selection = None,
    *,
    tooltips: dict[str, str] | None = None,
) -> MapSelectionBuilder:
    """Create selection-highlighting map from Geometry object.

    When used with output_map() that provides static geometry, you can call MapSelection()
    without geometry argument. Otherwise, provide a Geometry object.

    Args:
        geometry: Geometry object (optional when used with output_map())
        selected: Selected region ID(s)
        tooltips: Region tooltips

    Example with geometry:
        from shinymap import MapSelection
        from shinymap.geometry import Geometry

        geo = Geometry.from_dict(data)
        MapSelection(geo, selected="region1", tooltips=tooltips)
            .with_fill_color("#e2e8f0")
            .with_fill_color_selected("#fbbf24")

    Example with output_map() static params:
        # UI layer
        output_map("my_map", GEOMETRY, tooltips=TOOLTIPS)

        # Server layer
        @render_map
        def my_map():
            return MapSelection(selected=input.selected()).with_fill_color_selected("#fbbf24")

    Returns:
        MapSelectionBuilder instance for method chaining
    """
    from .geometry import Geometry as GeometryClass

    if geometry is None:
        # No geometry provided - will be merged from output_map() static params
        return MapSelectionBuilder(
            None,  # Will be filled by _apply_static_params
            selected=selected,
            tooltips=tooltips,
            view_box=None,
            overlay_regions=None,
        )
    else:
        # Extract regions using Geometry methods
        main_regions = geometry.main_regions()
        overlay_regions_dict = geometry.overlay_regions()

        # Create MapSelectionBuilder with extracted data
        return MapSelectionBuilder(
            main_regions,
            selected=selected,
            tooltips=tooltips,
            view_box=geometry.viewbox(),
            overlay_regions=overlay_regions_dict if overlay_regions_dict else None,
        )


class MapCountBuilder(MapBuilder):
    """Specialized builder for count-based coloring patterns.

    Parameters can be provided here or via output_map(). When both are provided,
    builder parameters take precedence.

    Example (traditional):
        MapCount(geometry, counts, tooltips=tooltips)
            .with_fill_color(["blue", "red", "green"])  # Palette for 0, 1, 2

    Example (with static params in output_map()):
        # UI layer
        output_map("my_map", geometry=GEOMETRY, tooltips=TOOLTIPS, view_box=VIEWBOX)

        # Server layer
        @render_map
        def my_map():
            return MapCount(counts=input.counts()).with_fill_color(palette)
    """

    def __init__(
        self,
        geometry: GeometryMap | None = None,
        counts: CountMap = None,
        *,
        tooltips: TooltipMap = None,
        view_box: tuple[float, float, float, float] | None = None,
        overlay_regions: GeometryMap | None = None,
        overlay_aesthetic: Mapping[str, Any] | None = None,
    ):
        super().__init__(geometry, tooltips=tooltips, view_box=view_box, overlay_regions=overlay_regions, overlay_aesthetic=overlay_aesthetic)
        self._counts = counts
        self._count_palette: list[str] | None = None

    # Override to accept palette list
    def with_fill_color(
        self,
        fill_color: str | list[str] | Mapping[str, str] | None,
    ) -> "MapCountBuilder":
        """Set fill colors (accepts palette list for count values).

        Can be:
        - String: Apply to all regions
        - List: Palette for count values [0, 1, 2, ...]
        - Dict: Explicit region → color mapping

        Examples:
            .with_fill_color(["blue", "red", "green"])  # count 0→blue, 1→red, 2→green
            .with_fill_color("#cccccc")  # all regions gray
            .with_fill_color({"a": "red"})  # explicit mapping
        """
        if fill_color is None:
            return self

        if isinstance(fill_color, list):
            # Palette mode: map count values to colors
            import warnings

            self._count_palette = fill_color

            # Only convert to fill map if geometry is available
            if self._regions is not None:
                # Convert to fill map
                count_fills = {}
                max_count = max(self._counts.values(), default=0) if self._counts else 0

                # Warn if palette is too small for count values
                if max_count >= len(fill_color):
                    warnings.warn(
                        f"Palette has {len(fill_color)} colors but max count is {max_count}. "
                        f"Colors will cycle (count {len(fill_color)} gets color[0], etc.).",
                        UserWarning,
                        stacklevel=2,
                    )

                for rid in self._regions.keys():
                    count = (self._counts or {}).get(rid, 0)
                    color_index = count % len(fill_color)  # Cycle if needed
                    count_fills[rid] = fill_color[color_index]
                # Store in base _fill_color
                if self._fill_color is None:
                    self._fill_color = count_fills
                else:
                    # Merge with existing fills
                    existing = _normalize_fills(self._fill_color, self._regions)
                    if existing:
                        self._fill_color = {**existing, **count_fills}
                    else:
                        self._fill_color = count_fills
            else:
                # Geometry not available yet - will be applied in _apply_static_params
                # Store the palette for later
                pass
        else:
            # String or dict - use parent method
            super().with_fill_color(fill_color)
        return self

    # Type overrides for other methods
    def with_fill_opacity(self, fill_opacity: float | Mapping[str, float]) -> "MapCountBuilder":
        super().with_fill_opacity(fill_opacity)
        return self

    def with_stroke_color(self, stroke_color: str | Mapping[str, str]) -> "MapCountBuilder":
        super().with_stroke_color(stroke_color)
        return self

    def with_stroke_width(self, stroke_width: float | Mapping[str, float]) -> "MapCountBuilder":
        super().with_stroke_width(stroke_width)
        return self

    def build(self) -> MapPayload:
        """Build payload with count information."""
        return MapPayload(
            geometry=self._regions,
            tooltips=self._tooltips,
            fill_color=self._fill_color,
            fill_opacity=self._fill_opacity,
            stroke_color=self._stroke_color,
            stroke_width=self._stroke_width,
            counts=self._counts,
            active_ids=self._active_ids,
            view_box=self._view_box,
            default_aesthetic=self._default_aesthetic,
            count_palette=self._count_palette,
            overlay_geometry=self._overlay_regions,
            overlay_aesthetic=self._overlay_aesthetic,
        )


# Alias for shorter usage
def MapCount(
    geometry: "Geometry | None" = None,
    counts: CountMap = None,
    *,
    tooltips: dict[str, str] | None = None,
) -> MapCountBuilder:
    """Create count-based coloring map from Geometry object.

    When used with output_map() that provides static geometry, you can call MapCount()
    without geometry argument. Otherwise, provide a Geometry object.

    Args:
        geometry: Geometry object (optional when used with output_map())
        counts: Count values per region
        tooltips: Region tooltips

    Example with geometry:
        from shinymap import MapCount
        from shinymap.geometry import Geometry

        geo = Geometry.from_dict(data)
        MapCount(geo, counts=counts, tooltips=tooltips)
            .with_fill_color(["blue", "red", "green"])  # Palette for 0, 1, 2

    Example with output_map() static params:
        # UI layer
        output_map("my_map", GEOMETRY, tooltips=TOOLTIPS)

        # Server layer
        @render_map
        def my_map():
            return MapCount(counts=input.counts()).with_fill_color(palette)

    Returns:
        MapCountBuilder instance for method chaining
    """
    from .geometry import Geometry as GeometryClass

    if geometry is None:
        # No geometry provided - will be merged from output_map() static params
        return MapCountBuilder(
            None,  # Will be filled by _apply_static_params
            counts=counts,
            tooltips=tooltips,
            view_box=None,
            overlay_regions=None,
        )
    else:
        # Extract regions using Geometry methods
        main_regions = geometry.main_regions()
        overlay_regions_dict = geometry.overlay_regions()

        # Create MapCountBuilder with extracted data
        return MapCountBuilder(
            main_regions,
            counts=counts,
            tooltips=tooltips,
            view_box=geometry.viewbox(),
            overlay_regions=overlay_regions_dict if overlay_regions_dict else None,
        )


def _render_map_ui(
    payload: MapPayload | MapBuilder,
    *,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
    click_input_id: str | None = None,
    _include_dependency: bool = True,
) -> Tag | TagList:
    """Internal: Render a map payload to HTML. Used by @render_map decorator."""
    if isinstance(payload, (Tag, TagList)):
        if _include_dependency:
            return TagList(_dependency(), payload)
        return payload

    payload_dict = payload.as_json()
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


def output_map(
    id: str,
    geometry: Geometry | None = None,
    *,
    tooltips: TooltipMap | None = None,
    view_box: tuple[float, float, float, float] | None = None,
    default_aesthetic: Mapping[str, Any] | None = None,
    overlay_geometry: GeometryMap | None = None,
    overlay_aesthetic: Mapping[str, Any] | None = None,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
) -> TagList:
    """UI placeholder for a ``@render_map`` output.

    Args:
        id: Output ID (must match @render_map function name)
        geometry: Geometry object
        tooltips: Optional static tooltips
        view_box: Optional viewBox tuple (x, y, width, height). If not provided, uses geometry.viewbox()
        default_aesthetic: Optional default styling for all regions (fillColor, strokeColor, strokeWidth, etc.)
        overlay_geometry: Optional static overlay geometry (non-interactive paths)
        overlay_aesthetic: Optional static overlay aesthetic styling
        width: Container width (CSS)
        height: Container height (CSS)
        class_: Additional CSS classes
        style: Additional inline styles

    Static parameters (geometry, tooltips, view_box, default_aesthetic, overlay_*) are merged with
    @render_map output. Builder parameters take precedence over static parameters.

    Aesthetic precedence (highest to lowest):
    1. Parameters from @render_map output (builder API)
    2. Explicit parameters passed to this function
    3. Configured theme from configure_theme()
    4. System defaults from React components

    Example:
        # UI layer - define static structure once
        output_map(
            "my_map",
            GEOMETRY,
            tooltips=TOOLTIPS,
            overlay_geometry=GEOMETRY.overlay_regions(),
            overlay_aesthetic=DIVIDER_STYLE,
        )

        # Server layer - focus on reactive data
        @render_map
        def my_map():
            return MapSelection(selected=input.selected()).with_fill_color_selected("#3b82f6")
    """
    # Get configured theme and apply defaults for parameters not explicitly provided
    from ._theme import get_theme_config

    theme_config = get_theme_config()

    if default_aesthetic is None and "default_aesthetic" in theme_config:
        default_aesthetic = theme_config["default_aesthetic"]
    if overlay_aesthetic is None and "overlay_aesthetic" in theme_config:
        overlay_aesthetic = theme_config["overlay_aesthetic"]

    # Process geometry if provided
    processed_geometry = None
    processed_view_box = None
    processed_overlay_geometry = overlay_geometry

    if geometry is not None:
        # Extract main regions from Geometry object
        processed_geometry = geometry.main_regions()

        # Use viewbox from Geometry if not explicitly provided
        if view_box is None:
            vb_tuple = geometry.viewbox()
        else:
            vb_tuple = view_box
        processed_view_box = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"

        # Extract overlay regions if not explicitly provided
        if overlay_geometry is None:
            overlay_regions = geometry.overlay_regions()
            if overlay_regions:
                processed_overlay_geometry = overlay_regions
    elif view_box is not None:
        # If geometry not provided but view_box is, process view_box
        processed_view_box = f"{view_box[0]} {view_box[1]} {view_box[2]} {view_box[3]}"

    # Store static params for retrieval in render_map
    static_params = {
        "geometry": processed_geometry,
        "tooltips": tooltips,
        "view_box": processed_view_box,
        "default_aesthetic": default_aesthetic,
        "overlay_geometry": processed_overlay_geometry,
        "overlay_aesthetic": overlay_aesthetic,
    }
    # Filter out None values
    static_params = {k: v for k, v in static_params.items() if v is not None}

    # Store in module-level registry (keyed by output ID)
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


def _apply_static_params(payload: MapPayload, output_id: str) -> MapPayload:
    """Apply static parameters from output_map() to payload.

    Builder parameters take precedence over static parameters.
    """
    static_params = _static_map_params.get(output_id)
    if not static_params:
        return payload

    # Merge geometry from static params if not provided by builder
    merged_geometry = payload.geometry if payload.geometry is not None else static_params.get("geometry")

    # Convert count_palette to fill_color if needed
    # This handles the case where MapCount() was called without geometry and used a palette
    merged_fill_color = payload.fill_color
    if payload.count_palette and merged_geometry and not payload.fill_color:
        import warnings
        # Convert palette to fill map using the merged geometry
        count_fills = {}
        max_count = max(payload.counts.values(), default=0) if payload.counts else 0
        palette = payload.count_palette

        # Warn if palette is too small for count values
        if max_count >= len(palette):
            warnings.warn(
                f"Palette has {len(palette)} colors but max count is {max_count}. "
                f"Colors will cycle (count {len(palette)} gets color[0], etc.).",
                UserWarning,
                stacklevel=2,
            )

        for rid in merged_geometry.keys():
            count = (payload.counts or {}).get(rid, 0)
            color_index = count % len(palette)  # Cycle if needed
            count_fills[rid] = palette[color_index]

        merged_fill_color = count_fills

    # Create new payload with static params as defaults
    # Builder values (if set) override static values
    return MapPayload(
        geometry=merged_geometry,
        tooltips=payload.tooltips if payload.tooltips is not None else static_params.get("tooltips"),
        fill_color=merged_fill_color,  # May be converted from palette
        stroke_width=payload.stroke_width,  # Always from builder
        stroke_color=payload.stroke_color,  # Always from builder
        fill_opacity=payload.fill_opacity,  # Always from builder
        counts=payload.counts,  # Always from builder
        active_ids=payload.active_ids,  # Always from builder
        view_box=payload.view_box if payload.view_box is not None else static_params.get("view_box"),
        default_aesthetic=payload.default_aesthetic if payload.default_aesthetic is not None else static_params.get("default_aesthetic"),
        fill_color_selected=payload.fill_color_selected,  # Always from builder
        fill_color_not_selected=payload.fill_color_not_selected,  # Always from builder
        count_palette=payload.count_palette,  # Keep for reference
        overlay_geometry=payload.overlay_geometry if payload.overlay_geometry is not None else static_params.get("overlay_geometry"),
        overlay_aesthetic=payload.overlay_aesthetic if payload.overlay_aesthetic is not None else static_params.get("overlay_aesthetic"),
    )


def render_map(fn=None):
    """Shiny render decorator that emits a :class:`MapBuilder` or :class:`MapPayload`.

    Merges static parameters from output_map() with builder output.
    Builder parameters take precedence over static parameters.
    """

    def decorator(func):
        @render.ui
        @wraps(func)
        def wrapper():
            val = func()

            # If val is a builder, build it to get payload
            if hasattr(val, "build"):
                payload = val.build()
            elif isinstance(val, MapPayload):
                payload = val
            else:
                # Pass through non-map values (e.g., Tag, TagList)
                return _render_map_ui(val, _include_dependency=False)

            # Apply static parameters from output_map()
            output_id = func.__name__
            payload = _apply_static_params(payload, output_id)

            return _render_map_ui(payload, _include_dependency=False)

        return wrapper

    if fn is None:
        return decorator

    return decorator(fn)


def update_map(
    id: str,
    *,
    # Aesthetics (both input_map and output_map)
    fill_color: str | Mapping[str, str] | None = None,
    stroke_width: float | Mapping[str, float] | None = None,
    stroke_color: str | Mapping[str, str] | None = None,
    fill_opacity: float | Mapping[str, float] | None = None,
    default_aesthetic: Mapping[str, Any] | None = None,
    hover_highlight: Mapping[str, Any] | None = None,
    # Input-specific parameters
    value: CountMap = None,  # Selection state (pass {} to clear all)
    selected_aesthetic: Mapping[str, Any] | None = None,
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
        default_aesthetic: Default aesthetic for all regions
        hover_highlight: Hover highlight aesthetic
        value: (input_map only) Selection state; pass {} to clear all selections
        selected_aesthetic: (input_map only) Aesthetic override for selected regions
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
    if default_aesthetic is not None:
        updates["default_aesthetic"] = default_aesthetic
    if selected_aesthetic is not None:
        updates["selected_aesthetic"] = selected_aesthetic
    if hover_highlight is not None:
        updates["hover_highlight"] = hover_highlight
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
