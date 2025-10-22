from __future__ import annotations
from html import escape
from typing import Iterable, List, Mapping

from ._geo import (
    MAP_HEIGHT,
    MAP_WIDTH,
    filter_regions,
    load_paths,
    okinawa_bbox,
    reposition_okinawa,
)

PREF_NAMES: Mapping[str, str] = {
    "01": "Hokkaido",
    "02": "Aomori",
    "03": "Iwate",
    "04": "Miyagi",
    "05": "Akita",
    "06": "Yamagata",
    "07": "Fukushima",
    "08": "Ibaraki",
    "09": "Tochigi",
    "10": "Gunma",
    "11": "Saitama",
    "12": "Chiba",
    "13": "Tokyo",
    "14": "Kanagawa",
    "15": "Niigata",
    "16": "Toyama",
    "17": "Ishikawa",
    "18": "Fukui",
    "19": "Yamanashi",
    "20": "Nagano",
    "21": "Gifu",
    "22": "Shizuoka",
    "23": "Aichi",
    "24": "Mie",
    "25": "Shiga",
    "26": "Kyoto",
    "27": "Osaka",
    "28": "Hyogo",
    "29": "Nara",
    "30": "Wakayama",
    "31": "Tottori",
    "32": "Shimane",
    "33": "Okayama",
    "34": "Hiroshima",
    "35": "Yamaguchi",
    "36": "Tokushima",
    "37": "Kagawa",
    "38": "Ehime",
    "39": "Kochi",
    "40": "Fukuoka",
    "41": "Saga",
    "42": "Nagasaki",
    "43": "Kumamoto",
    "44": "Oita",
    "45": "Miyazaki",
    "46": "Kagoshima",
    "47": "Okinawa",
}
from ._types import ColorbarStyle, MapConfig, MapData, MapTheme


def export_svg(
    data: MapData | None = None,
    config: MapConfig | None = None,
    width: float | None = MAP_WIDTH,
    height: float | None = MAP_HEIGHT,
) -> str:
    cfg = config or MapConfig()
    base_paths = load_paths()
    filtered = filter_regions(base_paths, cfg.regions)
    paths = reposition_okinawa(filtered, cfg.okinawa)

    theme = cfg.theme
    color_by = data.color_by_pref if data else {}
    tooltip_by = data.tooltip_by_pref if data else {}
    colorbar = data.colorbar if data else ColorbarStyle()

    map_bounds = _paths_bounds(paths)
    min_x, min_y, max_x, max_y = (map_bounds or (0.0, 0.0, MAP_WIDTH, MAP_HEIGHT))

    parts: List[str] = [""]
    if width is not None:
        parts.append(f' width="{_fmt(width)}"')
    if height is not None:
        parts.append(f' height="{_fmt(height)}"')
    parts.append(">")

    if cfg.draw_omission_line and cfg.okinawa != "original":
        orig_bbox = okinawa_bbox(filtered)
        new_bbox = okinawa_bbox(paths)
        mainland_bbox = _mainland_bounds(filtered)
        if orig_bbox and new_bbox and mainland_bbox:
            line_svg, line_bounds = _omission_line(orig_bbox, new_bbox, mainland_bbox, cfg.okinawa)
            parts.append(line_svg)
            if line_bounds:
                min_x = min(min_x, line_bounds[0])
                min_y = min(min_y, line_bounds[1])
                max_x = max(max_x, line_bounds[2])
                max_y = max(max_y, line_bounds[3])

    for code, d in paths.items():
        fill = escape(color_by.get(code, theme.fill_default))
        stroke = theme.border_color if theme.show_borders else "none"
        tip = tooltip_by.get(code) or _pref_label(code)
        title = f"<title>{escape(tip)}</title>" if tip else ""
        parts.append(
            f'<path id="pref-{code}" d="{d}" fill="{fill}" '
            f'stroke="{escape(stroke)}" stroke-width="1">{title}</path>'
        )

    if colorbar.visible:
        colors = _unique_colors(color_by.values())
        group, cb_bounds = _colorbar_group(colors, colorbar, theme, (min_x, min_y, max_x, max_y))
        if group:
            parts.append(group)
            if cb_bounds:
                min_x = min(min_x, cb_bounds[0])
                min_y = min(min_y, cb_bounds[1])
                max_x = max(max_x, cb_bounds[2])
                max_y = max(max_y, cb_bounds[3])

    parts[0] = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{_fmt(min_x)} {_fmt(min_y)} {_fmt(max_x - min_x or 1.0)} {_fmt(max_y - min_y or 1.0)}"'
    )

    parts.append("</svg>")
    return "".join(parts)


def _omission_line(
    _original_bbox: tuple[float, float, float, float],
    inset_bbox: tuple[float, float, float, float],
    mainland_bbox: tuple[float, float, float, float],
    placement: str,
) -> tuple[str, tuple[float, float, float, float]]:
    min_x, min_y, max_x, max_y = mainland_bbox
    mid_x, mid_y = (
        inset_bbox[2],
        inset_bbox[3],
    ) if placement == "topleft" else (
        inset_bbox[0],
        inset_bbox[1],
    )
    available_ne = min(max_x - mid_x, mid_y - min_y)
    available_sw = min(mid_x - min_x, max_y - mid_y)
    length = max(0.0, min(available_ne, available_sw))
    origin = (mid_x - length, mid_y + length)
    target = (mid_x + length, mid_y - length)
    bounds = (
        min(origin[0], target[0]),
        min(origin[1], target[1]),
        max(origin[0], target[0]),
        max(origin[1], target[1]),
    )
    return (
        f'<line x1="{_fmt(origin[0])}" y1="{_fmt(origin[1])}" '
        f'x2="{_fmt(target[0])}" y2="{_fmt(target[1])}" '
        f'stroke="#555" stroke-width="1.2" stroke-dasharray="6,4" />',
        bounds,
    )


def _mainland_bounds(paths: Mapping[str, str]) -> tuple[float, float, float, float] | None:
    xs: list[float] = []
    ys: list[float] = []
    for code, path in paths.items():
        if code == "47":
            continue
        _collect_points(path, xs, ys)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _paths_bounds(paths: Mapping[str, str]) -> tuple[float, float, float, float] | None:
    xs: list[float] = []
    ys: list[float] = []
    for path in paths.values():
        _collect_points(path, xs, ys)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _collect_points(path: str, xs: List[float], ys: List[float]) -> None:
    tokens = path.replace("M", " M ").replace("L", " L ").replace("Z", " Z ").split()
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in {"M", "L"}:
            xs.append(float(tokens[i + 1]))
            ys.append(float(tokens[i + 2]))
            i += 3
        else:
            i += 1


def _pref_label(code: str) -> str:
    return PREF_NAMES.get(code, code)


def _unique_colors(colors: Iterable[str]) -> List[str]:
    seen: dict[str, None] = {}
    for color in colors:
        if color not in seen:
            seen[color] = None
    return list(seen)


def _colorbar_group(
    colors: List[str],
    style: ColorbarStyle,
    theme: MapTheme,
    bounds: tuple[float, float, float, float],
) -> tuple[str | None, tuple[float, float, float, float] | None]:
    if not colors:
        return "", None
    swatch = 18.0
    padding = 12.0
    stroke = theme.border_color if theme.show_borders else "#333"
    text_color = theme.label_color
    min_x, min_y, max_x, max_y = bounds
    elems = [
        '<g id="jpmap-colorbar" font-family="sans-serif" font-size="12" '
        f'fill="{escape(text_color)}">'
    ]
    cb_min_x = min_x
    cb_min_y = min_y
    cb_max_x = max_x
    cb_max_y = max_y
    if style.position == "right":
        x = max_x + padding
        y = min_y + padding
        for idx, color in enumerate(colors):
            cy = y + idx * swatch
            elems.append(
                f'<rect x="{_fmt(x)}" y="{_fmt(cy)}" '
                f'width="{_fmt(swatch)}" height="{_fmt(swatch)}" '
                f'fill="{escape(color)}" stroke="{escape(stroke)}" '
                'stroke-width="0.6"/>'
            )
            cb_max_x = max(cb_max_x, x + swatch)
            cb_max_y = max(cb_max_y, cy + swatch)
        if style.label:
            label_x = x - 6
            label_y = y + (len(colors) * swatch) / 2
            elems.append(
                f'<text x="{_fmt(label_x)}" y="{_fmt(label_y)}" '
                'dominant-baseline="middle" text-anchor="end">'
                f"{escape(style.label)}</text>"
            )
            cb_min_x = min(cb_min_x, label_x)
            cb_min_y = min(cb_min_y, label_y)
    else:
        x = min_x + padding
        y = max_y + padding
        for idx, color in enumerate(colors):
            cx = x + idx * swatch
            elems.append(
                f'<rect x="{_fmt(cx)}" y="{_fmt(y)}" '
                f'width="{_fmt(swatch)}" height="{_fmt(swatch)}" '
                f'fill="{escape(color)}" stroke="{escape(stroke)}" '
                'stroke-width="0.6"/>'
            )
            cb_max_x = max(cb_max_x, cx + swatch)
            cb_max_y = max(cb_max_y, y + swatch)
        if style.label:
            label_x = x + (len(colors) * swatch) / 2
            label_y = y - 6
            elems.append(
                f'<text x="{_fmt(label_x)}" y="{_fmt(label_y)}" '
                'text-anchor="middle">'
                f"{escape(style.label)}</text>"
            )
            cb_max_y = max(cb_max_y, label_y)
    elems.append("</g>")
    return "".join(elems), (cb_min_x, cb_min_y, cb_max_x, cb_max_y)


def _fmt(value: float) -> str:
    text = f"{value:.2f}"
    text = text.rstrip("0").rstrip(".")
    return text or "0"
