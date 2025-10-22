from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any, Iterable, List, Literal, Mapping, Optional

from htmltools import HTML, Tag, tags

from ._color import map_colors
from ._svg import export_svg
from ._types import ColorbarStyle, MapConfig, MapData, MapTheme
from ._utils import column_values, is_dataframe, iter_codes, strings_from_column

try:  # pragma: no cover - optional dependency
    import cairosvg  # type: ignore
except ImportError:  # pragma: no cover
    cairosvg = None  # type: ignore


@dataclass
class MapImage:
    format: Literal["svg", "png"]
    data: str | bytes
    mime_type: str
    width: Optional[str] = None
    height: Optional[str] = None

    def as_ui(self) -> Tag | HTML:
        if self.format == "svg":
            return HTML(self.data)  # type: ignore[arg-type]
        encoded = base64.b64encode(self.data)  # type: ignore[arg-type]
        attrs: dict[str, str] = {}
        if self.width:
            attrs["width"] = self.width
        if self.height:
            attrs["height"] = self.height
        return tags.img(
            src=f"data:{self.mime_type};base64,{encoded.decode('ascii')}",
            **attrs,
        )

    def as_image(self) -> Mapping[str, object]:
        if self.format != "png":
            raise ValueError("Only PNG maps can be used with render.image")
        return {
            "src": io.BytesIO(self.data),  # type: ignore[arg-type]
            "content_type": self.mime_type,
            "width": self.width,
            "height": self.height,
        }

    def as_data_url(self) -> str:
        if self.format == "svg":
            return f"data:{self.mime_type};utf8,{self.data}"
        encoded = base64.b64encode(self.data)  # type: ignore[arg-type]
        return f"data:{self.mime_type};base64,{encoded.decode('ascii')}"


def map(
    data,
    *,
    color: str,
    tooltip: str | None = None,
    regions: Iterable[str] | None = None,
    okinawa: str = "original",
    draw_omission_line: bool = True,
    map_width: str | None = None,
    map_height: str | None = None,
    format: Literal["svg", "png"] = "svg",
    theme: MapTheme | None = None,
    colorbar: ColorbarStyle | None = None,
    png_scale: float = 1.0,
    palette: str | Iterable[str] | None = None,
) -> MapImage:
    if not is_dataframe(data):
        raise TypeError("map() expects a pandas or polars DataFrame-like object.")
    codes = list(iter_codes(data))
    if not codes:
        raise ValueError("map() requires at least one row with a pref_code value.")
    raw_color_values = column_values(data, color)
    if len(raw_color_values) != len(codes):
        raise ValueError("Color column length mismatch with pref_code column.")
    color_by = map_colors(codes, _resolve_color_values(raw_color_values, palette))
    tooltip_by = None
    if tooltip:
        tooltips = strings_from_column(data, tooltip)
        if len(tooltips) != len(codes):
            raise ValueError("Tooltip column length mismatch with pref_code column.")
        tooltip_by = dict(zip(codes, tooltips))

    cfg = MapConfig(
        regions=regions,
        okinawa=okinawa,
        draw_omission_line=draw_omission_line,
        theme=theme or MapTheme(),
        map_width=map_width,
        map_height=map_height,
    )
    map_data = MapData(
        color_by_pref=color_by,
        tooltip_by_pref=tooltip_by,
        colorbar=colorbar or ColorbarStyle(),
    )
    svg_width = _parse_dimension(map_width)
    svg_height = _parse_dimension(map_height)
    svg = export_svg(map_data, cfg, width=svg_width, height=svg_height)

    if format == "svg":
        return MapImage("svg", svg, "image/svg+xml", map_width, map_height)
    if format != "png":
        raise ValueError("format must be 'svg' or 'png'")
    if cairosvg is None:  # pragma: no cover - triggered when dependency missing
        raise RuntimeError(
            "PNG output requires the optional 'cairosvg' package. "
            "Install it with `pip install cairosvg`."
        )
    png_kwargs = {}
    if svg_width and svg_height:
        png_kwargs["output_width"] = svg_width * png_scale
        png_kwargs["output_height"] = svg_height * png_scale
    elif png_scale != 1.0:
        png_kwargs["scale"] = png_scale
    png_bytes = cairosvg.svg2png(bytestring=svg.encode("utf-8"), **png_kwargs)
    return MapImage("png", png_bytes, "image/png", map_width, map_height)


def _parse_dimension(value: str | None) -> Optional[float]:
    if value is None:
        return None
    stripped = value.strip()
    if stripped.endswith("px"):
        stripped = stripped[:-2]
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError as exc:
        raise ValueError(
            f"Unable to interpret dimension '{value}'. Use numeric pixels, e.g. '360' or '360px'."
        ) from exc


def _resolve_color_values(values: Iterable[Any], palette: str | Iterable[str] | None) -> List[str]:
    normalized: List[str] = []
    hex_values: List[str] = []
    all_hex = True
    for value in values:
        text = "" if value is None else str(value)
        normalized.append(text)
        if _is_hex_color(text):
            hex_values.append(text)
        else:
            all_hex = False
    if all_hex:
        return hex_values

    numeric_values: List[float] = []
    numeric = True
    for value in values:
        if value is None or (isinstance(value, str) and not value.strip()):
            numeric = False
            break
        try:
            numeric_values.append(float(value))
        except (TypeError, ValueError):
            numeric = False
            break

    if numeric and numeric_values:
        palette_colors = _resolve_palette(palette, default="viridis")
        min_val = min(numeric_values)
        max_val = max(numeric_values)
        return [
            _interpolate_palette(palette_colors, v, min_val, max_val)
            for v in numeric_values
        ]

    palette_colors = _resolve_palette(palette, default="tab10")
    unique_values: dict[str, str] = {}
    mapped: List[str] = []
    palette_list = list(palette_colors)
    if not palette_list:
        raise ValueError("Palette sequence must contain at least one color.")
    for value in normalized:
        key = value or "(missing)"
        if key not in unique_values:
            color = palette_list[len(unique_values) % len(palette_list)]
            unique_values[key] = color
        mapped.append(unique_values[key])
    return mapped


def _is_hex_color(value: str) -> bool:
    text = value.strip()
    if len(text) not in (4, 7) or not text.startswith("#"):
        return False
    hex_digits = text[1:]
    if len(hex_digits) == 3:
        hex_digits = "".join(ch * 2 for ch in hex_digits)
    try:
        int(hex_digits, 16)
    except ValueError:
        return False
    return True


def _resolve_palette(
    palette: str | Iterable[str] | None,
    *,
    default: str,
) -> List[str]:
    if palette is None:
        palette = default
    if isinstance(palette, str):
        key = palette.lower()
        if key in _BUILTIN_PALETTES:
            return list(_BUILTIN_PALETTES[key])
        raise ValueError(
            f"Unknown palette '{palette}'. Available palettes: {', '.join(sorted(_BUILTIN_PALETTES))}"
        )
    colors = [color for color in palette if _is_hex_color(color)]
    if not colors:
        raise ValueError("Palette sequence must contain hex colors like '#3366cc'.")
    return colors


def _interpolate_palette(colors: List[str], value: float, min_value: float, max_value: float) -> str:
    if not colors:
        raise ValueError("Palette must contain at least one color.")
    if min_value == max_value:
        return colors[len(colors) // 2]
    normalized = (value - min_value) / (max_value - min_value)
    normalized = max(0.0, min(1.0, normalized))
    if len(colors) == 1:
        return colors[0]
    scaled = normalized * (len(colors) - 1)
    lower_index = int(scaled)
    upper_index = min(lower_index + 1, len(colors) - 1)
    fraction = scaled - lower_index
    if fraction <= 1e-9 or lower_index == upper_index:
        return colors[lower_index]
    lower_rgb = _hex_to_rgb(colors[lower_index])
    upper_rgb = _hex_to_rgb(colors[upper_index])
    blended = tuple(
        int(round((1 - fraction) * low + fraction * high))
        for low, high in zip(lower_rgb, upper_rgb)
    )
    return _rgb_to_hex(blended)


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    text = color.lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    return tuple(int(text[i : i + 2], 16) for i in range(0, 6, 2))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02x}" for channel in rgb)


_BUILTIN_PALETTES: Mapping[str, List[str]] = {
    "viridis": [
        "#fde725",
        "#5ec962",
        "#21918c",
        "#3b528b",
        "#440154",
    ],
    "magma": [
        "#fcfdbf",
        "#fe9929",
        "#d92b4c",
        "#7c1d6f",
        "#0d0887",
    ],
    "plasma": [
        "#f0f921",
        "#f1605d",
        "#b12a90",
        "#5c01a6",
    ],
    "cividis": [
        "#ffe255",
        "#e1b34c",
        "#a88050",
        "#714c5e",
        "#2c2a4a",
    ],
    "tab10": [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ],
    "pastel": [
        "#aec7e8",
        "#ffbb78",
        "#98df8a",
        "#ff9896",
        "#c5b0d5",
        "#c49c94",
        "#f7b6d2",
        "#c7c7c7",
        "#dbdb8d",
        "#9edae5",
    ],
}
