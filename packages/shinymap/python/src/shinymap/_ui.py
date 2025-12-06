from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from functools import wraps
from typing import Any, Mapping, MutableMapping

from htmltools import HTMLDependency, Tag, TagList, css
from shiny import render, ui

from . import __version__

GeometryMap = Mapping[str, str]
TooltipMap = Mapping[str, str] | None
FillMap = Mapping[str, str] | None
CountMap = Mapping[str, int] | None
Selection = str | list[str] | None


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


def _camel_props(data: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Convert select snake_case keys to camelCase for the JS component API."""
    mapping = {
        "max_selection": "maxSelection",
        "view_box": "viewBox",
        "default_aesthetic": "defaultAesthetic",
        "active_ids": "activeIds",
        "hover_highlight": "hoverHighlight",
    }
    out: MutableMapping[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        out[mapping.get(key, key)] = value
    return out


def input_map(
    id: str,
    geometry: GeometryMap,
    *,
    tooltips: TooltipMap = None,
    fills: FillMap = None,
    mode: str | None = "multiple",
    value: CountMap = None,
    cycle: int | None = None,
    max_selection: int | None = None,
    view_box: str | None = None,
    default_aesthetic: Mapping[str, Any] | None = None,
    hover_highlight: Mapping[str, Any] | None = None,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
) -> TagList:
    """Shiny input that emits region selections.

    For mode="single": returns a string (single selected region ID) or None
    For mode="multiple": returns a list of selected region IDs
    For mode="count": returns a dict mapping region IDs to counts

    The underlying value is always a count map (dict[str, int]), but Shiny
    automatically transforms it based on the mode using a value function.
    """
    if mode not in {None, "single", "multiple", "count"}:
        raise ValueError('mode must be one of "single", "multiple", "count", or None')

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
            "geometry": geometry,
            "tooltips": tooltips,
            "fills": fills,
            "mode": mode,
            "value": value,
            "cycle": effective_cycle,
            "max_selection": effective_max_selection,
            "view_box": view_box,
            "default_aesthetic": default_aesthetic,
            "hover_highlight": hover_highlight,
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
    geometry: GeometryMap
    tooltips: TooltipMap = None
    fills: FillMap = None
    counts: CountMap = None
    active_ids: Selection = None
    view_box: str | None = None
    default_aesthetic: Mapping[str, Any] | None = None

    def as_json(self) -> Mapping[str, Any]:
        return _camel_props(_drop_nones(asdict(self)))


class MapBuilder:
    """Fluent builder for constructing map payloads with method chaining.

    Example:
        @render_map
        def my_map():
            return (
                Map(geometry, tooltips=tooltips)
                .with_fills(my_fills)
                .with_counts(my_counts)
                .with_active(selected_ids)
            )
    """

    def __init__(
        self,
        geometry: GeometryMap,
        *,
        tooltips: TooltipMap = None,
        view_box: str | None = None,
    ):
        self._geometry = geometry
        self._tooltips = tooltips
        self._fills: FillMap = None
        self._counts: CountMap = None
        self._active_ids: Selection = None
        self._view_box = view_box
        self._default_aesthetic: Mapping[str, Any] | None = None

    def with_tooltips(self, tooltips: TooltipMap) -> "MapBuilder":
        """Set region tooltips."""
        self._tooltips = tooltips
        return self

    def with_fills(self, fills: FillMap) -> "MapBuilder":
        """Set region fill colors."""
        self._fills = fills
        return self

    def with_counts(self, counts: CountMap) -> "MapBuilder":
        """Set region count badges."""
        self._counts = counts
        return self

    def with_active(self, active_ids: Selection) -> "MapBuilder":
        """Set active/highlighted region IDs."""
        self._active_ids = active_ids
        return self

    def with_view_box(self, view_box: str) -> "MapBuilder":
        """Set the SVG viewBox."""
        self._view_box = view_box
        return self

    def with_stroke_width(self, width: float) -> "MapBuilder":
        """Set stroke width for all regions."""
        if self._default_aesthetic is None:
            self._default_aesthetic = {}
        self._default_aesthetic = {**self._default_aesthetic, "strokeWidth": width}
        return self

    def with_aesthetic(self, **kwargs: Any) -> "MapBuilder":
        """Set default aesthetic properties (strokeWidth, fillOpacity, etc.)."""
        if self._default_aesthetic is None:
            self._default_aesthetic = {}
        self._default_aesthetic = {**self._default_aesthetic, **kwargs}
        return self

    def build(self) -> MapPayload:
        """Build and return the MapPayload."""
        return MapPayload(
            geometry=self._geometry,
            tooltips=self._tooltips,
            fills=self._fills,
            counts=self._counts,
            active_ids=self._active_ids,
            view_box=self._view_box,
            default_aesthetic=self._default_aesthetic,
        )

    def as_json(self) -> Mapping[str, Any]:
        """Convert to JSON dict (for use with render_map)."""
        return self.build().as_json()


# Alias for more concise usage
Map = MapBuilder


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
    *,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
) -> TagList:
    """UI placeholder for a ``@render_map`` output."""
    return TagList(
        _dependency(),
        ui.div(
            ui.output_ui(id),
            class_=_class_names("shinymap-output-container", class_),
            style=css(**_merge_styles(width, height, style)),
        ),
    )


def render_map(fn=None):
    """Shiny render decorator that emits a :class:`MapBuilder` or :class:`MapPayload`."""

    def decorator(func):
        @render.ui
        @wraps(func)
        def wrapper():
            val = func()
            result = _render_map_ui(val, _include_dependency=False)
            print(f"[shinymap] render_map {func.__name__} type={type(val)} result={type(result)}")
            return result

        return wrapper

    if fn is None:
        return decorator

    return decorator(fn)
