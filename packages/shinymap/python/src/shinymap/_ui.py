from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, MutableMapping, Sequence

from htmltools import Tag, TagList, css, html_dependency
from shiny import render, ui

from . import __version__

GeometryMap = Mapping[str, str]
TooltipMap = Mapping[str, str] | None
FillMap = Mapping[str, str] | None
CountMap = Mapping[str, int] | None
Selection = str | Sequence[str] | None


def _dependency() -> Tag:
    return html_dependency(
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


def input_map(
    id: str,
    geometry: GeometryMap,
    *,
    tooltips: TooltipMap = None,
    mode: str = "single",
    value: Any | None = None,
    max_count: int | None = None,
    view_box: str | None = None,
    default_fill: str | None = None,
    stroke: str | None = None,
    highlight_fill: str | None = None,
    hover_fill: str | None = None,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
) -> TagList:
    """Shiny input that emits region selections or counts.

    Depending on ``mode`` the Shiny input value will be one of:

    - ``"single"`` (default): ``str | None`` of the active region.
    - ``"multiple"``: ``list[str]`` of selected regions.
    - ``"count"``: ``dict[str, int]`` with click counters.
    """
    if mode not in {"single", "multiple", "count"}:
        raise ValueError('mode must be one of "single", "multiple", or "count"')

    props = _drop_nones(
        {
            "geometry": geometry,
            "tooltips": tooltips,
            "mode": mode,
            "value": value,
            "maxCount": max_count,
            "viewBox": view_box,
            "defaultFill": default_fill,
            "stroke": stroke,
            "highlightFill": highlight_fill,
            "hoverFill": hover_fill,
        }
    )

    data = {
        "shinymap-input": "1",
        "shinymap-input-id": id,
        "shinymap-props": json.dumps(props),
    }

    return TagList(
        _dependency(),
        ui.div(
            id=id,
            class_=_class_names("shinymap-input", class_),
            style=css(**_merge_styles(width, height, style)),
            data=data,
        ),
    )


@dataclass
class MapPayload:
    geometry: GeometryMap
    tooltips: TooltipMap = None
    fills: FillMap = None
    counts: CountMap = None
    max_count: int | None = None
    active_ids: Selection = None
    view_box: str | None = None
    default_fill: str | None = None
    stroke: str | None = None

    def as_json(self) -> Mapping[str, Any]:
        return _drop_nones(asdict(self))


def map(
    payload: MapPayload | Mapping[str, Any],
    *,
    width: str | None = "100%",
    height: str | None = "320px",
    class_: str | None = None,
    style: MutableMapping[str, str] | None = None,
    click_input_id: str | None = None,
) -> TagList:
    """Render a read-only map. Intended for use inside a ``@render_map`` output."""
    payload_dict = payload.as_json() if isinstance(payload, MapPayload) else _drop_nones(dict(payload))
    data = {
        "shinymap-output": "1",
        "shinymap-payload": json.dumps(payload_dict),
    }
    if click_input_id:
        data["shinymap-click-input-id"] = click_input_id

    return TagList(
        _dependency(),
        ui.div(
            class_=_class_names("shinymap-output", class_),
            style=css(**_merge_styles(width, height, style)),
            data=data,
        ),
    )


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
            class_=_class_names("shinymap-output-container", class_),
            style=css(**_merge_styles(width, height, style)),
            children=[ui.output_ui(id)],
        ),
    )


def render_map(fn=None):
    """Shiny render decorator that emits a :class:`MapPayload` or compatible mapping."""

    def decorator(func):
        @render.ui
        def wrapper():
            return map(func())

        return wrapper

    if fn is None:
        return decorator

    return decorator(fn)
