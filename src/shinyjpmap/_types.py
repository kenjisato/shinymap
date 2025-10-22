from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Literal, Mapping, Optional

RegionKey = Literal[
    "Hokkaido", "Tohoku", "Kanto", "Chubu", "Kinki", "Chugoku",
    "Shikoku", "Kyushu", "Okinawa",
]

OkinawaPlacement = Literal["original", "topleft", "bottomright"]

@dataclass
class ColorbarStyle:
    visible: bool = True
    position: Literal["right", "bottom"] = "right"
    label: str = ""

@dataclass
class MapTheme:
    fill_default: str = "#ffffff"
    border_color: str = "#000000"
    show_borders: bool = True
    label_color: str = "#000000"

@dataclass
class MapConfig:
    regions: Optional[Iterable[RegionKey]] = None
    okinawa: OkinawaPlacement = "original"
    draw_omission_line: bool = True
    theme: MapTheme = field(default_factory=MapTheme)
    map_width: Optional[str] = None
    map_height: Optional[str] = None

DataFrameLike = object  # pandas or polars; duck-typed

@dataclass
class AestheticSpec:
    color: str
    tooltip: Optional[str] = None

@dataclass
class MapData:
    # key: JIS prefecture code (string like "01".."47")
    color_by_pref: Mapping[str, str]
    tooltip_by_pref: Mapping[str, str] | None = None
    colorbar: ColorbarStyle = field(default_factory=ColorbarStyle)
