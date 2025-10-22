#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


Point = Tuple[float, float]
Ring = List[Point]
Polygon = List[Ring]
MultiPolygon = List[Polygon]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert prefecture GeoJSON to compact SVG path data."
    )
    parser.add_argument("geojson", type=Path, help="Input GeoJSON file path")
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("src/shinyjpmap/data/pref_paths.json"),
        help="Output JSON path mapping",
    )
    parser.add_argument(
        "--out-ts",
        type=Path,
        default=Path("www/src/pref_paths.ts"),
        help="Optional TypeScript module output",
    )
    parser.add_argument(
        "--width",
        type=float,
        default=960.0,
        help="Target SVG width used for scaling",
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        default=0.6,
        help="Simplification tolerance in SVG units",
    )
    parser.add_argument(
        "--min-area",
        type=float,
        default=0.0,
        help="Drop polygon components smaller than this area (in scaled SVG units²)",
    )
    return parser.parse_args()


def project(lon: float, lat: float, cos_lat: float) -> Point:
    return lon * cos_lat, lat


def iter_coords(feature: dict) -> Iterable[Tuple[float, float]]:
    geom = feature["geometry"]
    coords = geom["coordinates"]
    if geom["type"] == "Polygon":
        coords = [coords]
    for rings in coords:
        for ring in rings:
            for lon, lat in ring:
                yield lon, lat


def load_polygons(feature: dict, cos_lat: float) -> MultiPolygon:
    geom = feature["geometry"]
    coords = geom["coordinates"]
    if geom["type"] == "Polygon":
        coords = [coords]
    multipolygon: MultiPolygon = []
    for rings in coords:
        polygon: Polygon = []
        for ring in rings:
            pts: Ring = []
            for lon, lat in ring:
                pts.append(project(lon, lat, cos_lat))
            polygon.append(pts)
        multipolygon.append(polygon)
    return multipolygon


def flatten_points(multipolygon: Sequence[Polygon]) -> Iterable[Point]:
    for polygon in multipolygon:
        for ring in polygon:
            for pt in ring:
                yield pt


def perpendicular_distance(pt: Point, start: Point, end: Point) -> float:
    (x, y), (x1, y1), (x2, y2) = pt, start, end
    if x1 == x2 and y1 == y2:
        return math.hypot(x - x1, y - y1)
    num = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1)
    den = math.hypot(y2 - y1, x2 - x1)
    return num / den


def simplify(points: Sequence[Point], epsilon: float) -> Ring:
    if len(points) <= 2:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack: List[Tuple[int, int]] = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        max_dist = -1.0
        max_idx = None
        for idx in range(start + 1, end):
            dist = perpendicular_distance(points[idx], points[start], points[end])
            if dist > max_dist:
                max_dist = dist
                max_idx = idx
        if max_idx is not None and max_dist > epsilon:
            keep[max_idx] = True
            stack.append((start, max_idx))
            stack.append((max_idx, end))
    return [pt for pt, flag in zip(points, keep) if flag]


def round_number(value: float) -> str:
    text = f"{value:.2f}"
    text = text.rstrip("0").rstrip(".")
    return text or "0"


def rings_to_path(
    polygon: Polygon,
    scale: float,
    min_x: float,
    max_y: float,
    epsilon: float,
) -> tuple[str, float]:
    commands: list[str] = []
    area = 0.0
    for ring in polygon:
        if not ring:
            continue
        if ring[0] == ring[-1]:
            ring = ring[:-1]
        scaled = [
            ((x - min_x) * scale, (max_y - y) * scale)
            for x, y in ring
        ]
        if not scaled:
            continue
        if area == 0.0:
            area = max(area, _ring_area(scaled))
        simplified = simplify(scaled, epsilon)
        if len(simplified) < 3:
            continue
        x0, y0 = simplified[0]
        commands.append(f"M{round_number(x0)} {round_number(y0)}")
        for x, y in simplified[1:]:
            commands.append(f"L{round_number(x)} {round_number(y)}")
        commands.append("Z")
    return "".join(commands), area


def _ring_area(points: Sequence[Point]) -> float:
    if len(points) < 3:
        return 0.0
    total = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def build_paths(
    features: Sequence[dict],
    width: float,
    epsilon: float,
    min_area: float,
) -> tuple[dict[str, str], float]:
    lat_values = [lat for feat in features for _, lat in iter_coords(feat)]
    if not lat_values:
        raise ValueError("GeoJSON contains no coordinates")
    avg_lat = sum(lat_values) / len(lat_values)
    cos_lat = math.cos(math.radians(avg_lat))
    projected = [load_polygons(feat, cos_lat) for feat in features]
    xs: List[float] = []
    ys: List[float] = []
    for multipolygon in projected:
        for x, y in flatten_points(multipolygon):
            xs.append(x)
            ys.append(y)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x or 1.0
    scale = width / span_x
    height = (max_y - min_y) * scale
    paths: dict[str, str] = {}
    for idx, multipolygon in enumerate(projected, start=1):
        code = f"{idx:02d}"
        parts: list[str] = []
        for polygon in multipolygon:
            part, area = rings_to_path(polygon, scale, min_x, max_y, epsilon)
            if min_area and area and area < min_area:
                continue
            if part:
                parts.append(part)
        if not parts:
            continue
        paths[code] = "".join(parts)
    return paths, height


def write_ts(paths: dict[str, str], width: float, height: float, out_path: Path) -> None:
    lines = [
        "// Auto-generated by scripts/geojson_to_svg_paths.py",
        "/* eslint-disable */",
        "export const PREF_GEOMETRY = {",
        f"  width: {round(width, 2)},",
        f"  height: {round(height, 2)},",
        "  paths: {",
    ]
    for code, path in paths.items():
        lines.append(f'    "{code}": "{path}",')
    lines.append("  },")
    lines.append("} as const;")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    with args.geojson.open() as fh:
        data = json.load(fh)
    features: Sequence[dict] = data["features"]
    paths, height = build_paths(features, args.width, args.epsilon, args.min_area)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w", encoding="utf-8") as fh:
        json.dump(paths, fh, separators=(",", ":"))
    if args.out_ts:
        write_ts(paths, args.width, height, args.out_ts)
    print(f"wrote {len(paths)} paths -> {args.out_json}")
    print(f"viewBox: 0 0 {round(args.width, 2)} {round(height, 2)}")


if __name__ == "__main__":
    main()
