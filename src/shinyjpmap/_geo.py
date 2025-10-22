from __future__ import annotations
import json
from importlib import resources
from typing import Dict, Iterable, Iterator, Mapping, Optional, Tuple

DATA_PACKAGE = "shinyjpmap.data"
DATA_FILE = "pref_paths.json"

MAP_WIDTH = 960.0
MAP_HEIGHT = 948.14

_INSET_BASE_SCALE = 0.42
_INSET_SCALE_BOOST = 1.5

# Lazy-loaded minimal SVG path data. Replace with real data in production.
# Keys are JIS codes "01".."47"; values are 'd' path strings.
_SVG_PATHS: Dict[str, str] | None = None


def load_paths() -> Dict[str, str]:
    global _SVG_PATHS
    if _SVG_PATHS is not None:
        return _SVG_PATHS
    with resources.files(DATA_PACKAGE).joinpath(DATA_FILE).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    _SVG_PATHS = {k: data[k] for k in sorted(data)}
    return _SVG_PATHS


def reposition_okinawa(
    paths: Dict[str, str],
    placement: str,
) -> Dict[str, str]:
    normalized = placement
    if normalized not in {"original", "topleft", "bottomright"}:
        raise ValueError(f"Unknown Okinawa placement '{placement}'")
    if normalized == "original":
        return paths
    if "47" not in paths:
        return paths
    ok_path = paths["47"]
    bbox = _path_bbox(ok_path)
    scale = _INSET_BASE_SCALE * _INSET_SCALE_BOOST
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    mainland = _mainland_bbox(paths)
    if mainland is None:
        mainland = (0.0, 0.0, MAP_WIDTH, MAP_HEIGHT)
    min_x, min_y, max_x, max_y = mainland
    scaled_width = width * scale
    scaled_height = height * scale
    if normalized == "topleft":
        origin_x = min_x
        origin_y = min_y
    else:  # bottomright
        origin_x = max_x - scaled_width
        origin_y = max_y - scaled_height
    origin_x = max(0.0, min(origin_x, MAP_WIDTH - scaled_width))
    origin_y = max(0.0, min(origin_y, MAP_HEIGHT - scaled_height))
    transformed = _transform_path(ok_path, scale, origin_x, origin_y, bbox)
    new_paths = dict(paths)
    new_paths["47"] = transformed
    return new_paths


REGIONS: Dict[str, Tuple[str, ...]] = {
    "Hokkaido": ("01",),
    "Tohoku": ("02", "03", "04", "05", "06", "07"),
    "Kanto": ("08", "09", "10", "11", "12", "13", "14"),
    "Chubu": ("15", "16", "17", "18", "19", "20", "21", "22", "23"),
    "Kinki": ("24", "25", "26", "27", "28", "29", "30"),
    "Chugoku": ("31", "32", "33", "34", "35"),
    "Shikoku": ("36", "37", "38", "39"),
    "Kyushu": ("40", "41", "42", "43", "44", "45", "46"),
    "Okinawa": ("47",),
}


def filter_regions(paths: Dict[str, str], regions: Iterable[str] | None) -> Dict[str, str]:
    if not regions:
        return paths
    allow = set()
    for r in regions:
        allow.update(REGIONS.get(r, ()))
    return {k: v for k, v in paths.items() if k in allow}


def _iter_path_coords(path: str) -> Iterator[Tuple[float, float]]:
    tokens = path.replace("M", " M ").replace("L", " L ").replace("Z", " Z ").split()
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in {"M", "L"}:
            yield float(tokens[i + 1]), float(tokens[i + 2])
            i += 3
        else:
            i += 1


def _path_bbox(path: str) -> Tuple[float, float, float, float]:
    xs = []
    ys = []
    for x, y in _iter_path_coords(path):
        xs.append(x)
        ys.append(y)
    if not xs:
        raise ValueError("Empty path data")
    return min(xs), min(ys), max(xs), max(ys)


def _mainland_bbox(paths: Mapping[str, str]) -> Optional[Tuple[float, float, float, float]]:
    xs: list[float] = []
    ys: list[float] = []
    for code, path in paths.items():
        if code == "47":
            continue
        for x, y in _iter_path_coords(path):
            xs.append(x)
            ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _format_number(value: float) -> str:
    text = f"{value:.2f}"
    text = text.rstrip("0").rstrip(".")
    return text or "0"


def _transform_path(
    path: str,
    scale: float,
    origin_x: float,
    origin_y: float,
    bbox: Tuple[float, float, float, float],
) -> str:
    min_x, min_y, _, _ = bbox
    dx = origin_x - min_x * scale
    dy = origin_y - min_y * scale
    tokens = path.replace("M", " M ").replace("L", " L ").replace("Z", " Z ").split()
    result: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in {"M", "L"}:
            x = float(tokens[i + 1]) * scale + dx
            y = float(tokens[i + 2]) * scale + dy
            result.append(f"{token}{_format_number(x)} {_format_number(y)}")
            i += 3
        elif token == "Z":
            result.append("Z")
            i += 1
        else:
            i += 1
    return "".join(result)


def okinawa_bbox(paths: Mapping[str, str]) -> Optional[Tuple[float, float, float, float]]:
    path = paths.get("47")
    if not path:
        return None
    return _path_bbox(path)
