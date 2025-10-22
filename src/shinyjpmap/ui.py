from __future__ import annotations

import json
from typing import Optional

from htmltools import HTMLDependency, TagList, css, div
from shiny import ui

from ._types import MapConfig, MapTheme

try:  # pragma: no cover - fallback for older Python
    from importlib.metadata import PackageNotFoundError, version as pkg_version
except ImportError:  # pragma: no cover
    from importlib_metadata import PackageNotFoundError, version as pkg_version  # type: ignore[assignment]


def input_map(
    id: str,
    *,
    regions: Optional[list[str]] = None,
    okinawa: str = "original",
    draw_omission_line: bool = True,
    label_color: str = "#000000",
    border_color: str = "#000000",
    show_borders: bool = True,
    width: str | None = None,
    height: str | None = "420px",
    map_width: str | None = None,
    map_height: str | None = None,
):
    if width is None and map_width is not None:
        width = map_width
    if height is None and map_height is not None:
        height = map_height
    cfg = MapConfig(
        regions=regions,
        okinawa=okinawa,
        draw_omission_line=draw_omission_line,
        theme=MapTheme(
            label_color=label_color,
            border_color=border_color,
            show_borders=show_borders,
        ),
        map_width=map_width,
        map_height=map_height,
    )
    tag = div(
        div(id=id, class_="jpmap-input"),
        class_="jpmap",
        style=css(width=width, height=height),
        data_jpmap_config=_config_to_json(cfg),
    )
    return TagList(_dependency(), tag)


def output_map(
    id: str,
    *,
    width: str | None = None,
    height: str | None = "420px",
    map_width: str | None = None,
    map_height: str | None = None,
):
    if width is None and map_width is not None:
        width = map_width
    if height is None and map_height is not None:
        height = map_height
    tag = ui.output_ui(id, width=width, height=height)
    return TagList(_dependency(), tag)


def _config_to_json(cfg: MapConfig) -> str:
    data = {
        "regions": list(cfg.regions) if cfg.regions else None,
        "okinawa": cfg.okinawa,
        "draw_omission_line": cfg.draw_omission_line,
        "size": {
            "width": cfg.map_width,
            "height": cfg.map_height,
        },
        "theme": {
            "fill_default": cfg.theme.fill_default,
            "border_color": cfg.theme.border_color,
            "show_borders": cfg.theme.show_borders,
            "label_color": cfg.theme.label_color,
        },
    }
    return json.dumps(data)


_DEP_CACHE: HTMLDependency | None = None


def _dependency() -> HTMLDependency:
    global _DEP_CACHE
    if _DEP_CACHE is None:
        try:
            version = pkg_version("shinyjpmap")
        except PackageNotFoundError:
            version = "0.0.0"
        _DEP_CACHE = HTMLDependency(
            name="shinyjpmap",
            version=version,
            source={"package": "shinyjpmap", "subdir": "www"},
            script={"src": "bridge.js", "type": "module"},
        )
    return _DEP_CACHE


def dependency() -> HTMLDependency:
    return _dependency()
