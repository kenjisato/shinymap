"""Extract and transform Japan prefecture map from Wikimedia Commons SVG.

This script:
1. Extracts prefecture paths from the SVG file
2. Merges Hopporyodo (Northern Territories) with Hokkaido
3. Scales Okinawa (prefecture 47) by 1.4x for better visibility
4. Calculates proper viewBox for the transformed map
5. Adds L-shaped divider lines

Source: https://commons.wikimedia.org/wiki/File:Japan_template_large.svg
License: CC BY-SA 3.0

Usage:
    cd packages/shinymap/python/examples
    uv run python data/scripts/transform_japan.py
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple

from svgpathtools import Path as SvgPath, parse_path

# Mapping from SVG IDs (Romaji names) to prefecture codes
ROMAJI_TO_CODE = {
    "Hokkaido": "01",
    "Aomori": "02",
    "Iwate": "03",
    "Miyagi": "04",
    "Akita": "05",
    "Yamagata": "06",
    "Fukushima": "07",
    "Ibaraki": "08",
    "Tochigi": "09",
    "Gumma": "10",  # Note: SVG uses "Gumma" not "Gunma"
    "Saitama": "11",
    "Chiba": "12",
    "Tokyo": "13",
    "Kanagawa": "14",
    "Nigata": "15",  # Note: SVG uses "Nigata" not "Niigata"
    "Toyama": "16",
    "Ishikawa": "17",
    "Fukui": "18",
    "Yamanashi": "19",
    "Nagano": "20",
    "Gifu": "21",
    "Shizuoka": "22",
    "Aichi": "23",
    "Mie": "24",
    "Shiga": "25",
    "Kyoto": "26",
    "Osaka": "27",
    "Hyogo": "28",
    "Nara": "29",
    "Wakayama": "30",
    "Tottori": "31",
    "Shimane": "32",
    "Okayama": "33",
    "Hiroshima": "34",
    "Yamaguchi": "35",
    "Tokushima": "36",
    "Kagawa": "37",
    "Ehime": "38",
    "Kochi": "39",
    "Fukuoka": "40",
    "Saga": "41",
    "Nagasaki": "42",
    "Kumamoto": "43",
    "Oita": "44",
    "Miyazaki": "45",
    "Kagoshima": "46",
    "Okinawa": "47",
}


def get_path_bounds(path_string: str) -> Tuple[float, float, float, float]:
    """Get bounding box of an SVG path (min_x, min_y, max_x, max_y).

    Uses svgpathtools to properly handle all SVG path commands including
    relative commands (lowercase l, m, h, v).
    """
    try:
        path = parse_path(path_string)
        if len(path) == 0:
            return (0, 0, 0, 0)

        # Get bounding box from path
        xmin, xmax, ymin, ymax = path.bbox()
        return (xmin, ymin, xmax, ymax)
    except Exception:
        return (0, 0, 0, 0)


def transform_path(path_string: str, dx: float = 0, dy: float = 0,
                   scale: float = 1.0, center_x: float = 0,
                   center_y: float = 0) -> str:
    """Transform an SVG path: scale around center, then translate.

    Args:
        path_string: SVG path d attribute string
        dx, dy: Translation offsets
        scale: Scale factor
        center_x, center_y: Center point for scaling

    Returns:
        Transformed SVG path string
    """
    try:
        path = parse_path(path_string)

        # Transform each segment
        transformed_segments = []
        for segment in path:
            # Get start and end points
            start = segment.start
            end = segment.end

            # Scale around center
            if scale != 1.0:
                start = complex(
                    center_x + (start.real - center_x) * scale,
                    center_y + (start.imag - center_y) * scale
                )
                end = complex(
                    center_x + (end.real - center_x) * scale,
                    center_y + (end.imag - center_y) * scale
                )

            # Translate
            start = complex(start.real + dx, start.imag + dy)
            end = complex(end.real + dx, end.imag + dy)

            # Create transformed segment (using same type as original)
            segment_type = type(segment)
            if hasattr(segment, 'control1'):  # CubicBezier
                control1 = segment.control1
                control2 = segment.control2
                if scale != 1.0:
                    control1 = complex(
                        center_x + (control1.real - center_x) * scale,
                        center_y + (control1.imag - center_y) * scale
                    )
                    control2 = complex(
                        center_x + (control2.real - center_x) * scale,
                        center_y + (control2.imag - center_y) * scale
                    )
                control1 = complex(control1.real + dx, control1.imag + dy)
                control2 = complex(control2.real + dx, control2.imag + dy)
                transformed_segments.append(segment_type(start, control1, control2, end))
            elif hasattr(segment, 'control'):  # QuadraticBezier
                control = segment.control
                if scale != 1.0:
                    control = complex(
                        center_x + (control.real - center_x) * scale,
                        center_y + (control.imag - center_y) * scale
                    )
                control = complex(control.real + dx, control.imag + dy)
                transformed_segments.append(segment_type(start, control, end))
            else:  # Line or Arc
                transformed_segments.append(segment_type(start, end))

        # Convert back to path string
        transformed_path = SvgPath(*transformed_segments)
        return transformed_path.d()
    except Exception as e:
        # If transformation fails, return original
        print(f"Warning: Failed to transform path: {e}")
        return path_string


def extract_paths(svg_path: Path) -> Dict[str, str]:
    """Extract prefecture paths from SVG file.

    Returns:
        Dictionary mapping prefecture codes to SVG path strings
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    geometry = {}
    hopporyodo_paths = []

    # Extract prefectures and special regions
    for group in root.iter():
        if group.tag.endswith('g'):
            group_id = group.get('id')

            # Handle prefectures
            if group_id in ROMAJI_TO_CODE:
                paths = []
                for path_elem in group.iter():
                    if path_elem.tag.endswith('path'):
                        path_d = path_elem.get('d')
                        if path_d:
                            paths.append(path_d.strip())

                if paths:
                    code = ROMAJI_TO_CODE[group_id]
                    geometry[code] = ' '.join(paths)

            # Handle Northern Territories (merge with Hokkaido)
            elif group_id == 'Hopporyodo':
                for path_elem in group.iter():
                    if path_elem.tag.endswith('path'):
                        path_d = path_elem.get('d')
                        if path_d:
                            hopporyodo_paths.append(path_d.strip())

    # Merge Hopporyodo paths with Hokkaido (01)
    if hopporyodo_paths and '01' in geometry:
        geometry['01'] = geometry['01'] + ' ' + ' '.join(hopporyodo_paths)

    return geometry


def main():
    """Extract paths from SVG and transform Japan map."""
    # Paths
    script_dir = Path(__file__).parent
    svg_path = script_dir.parent / "Japan_template_large.svg"
    output_path = script_dir.parent / "japan_prefectures.json"

    print("=" * 70)
    print("Japan Prefecture Map: Extract and Transform")
    print("=" * 70)
    print(f"Input:  {svg_path}")
    print(f"Output: {output_path}")
    print()

    # Step 1: Extract paths from SVG
    print("STEP 1: Extracting paths from SVG...")
    geometry = extract_paths(svg_path)
    print(f"  Extracted {len(geometry)} prefectures")

    # Verify all 47 prefectures
    if len(geometry) != 47:
        missing = set(ROMAJI_TO_CODE.values()) - set(geometry.keys())
        print(f"  WARNING: Missing prefectures: {missing}")
    print()

    # Step 2: Scale Okinawa (in place - it's already in top-left)
    print("STEP 2: Scaling Okinawa (prefecture 47) by 1.4x...")
    okinawa_code = '47'
    scale_factor = 1.4

    if okinawa_code in geometry:
        # Get Okinawa bounds and center
        okinawa_bounds = get_path_bounds(geometry[okinawa_code])
        oki_min_x, oki_min_y, oki_max_x, oki_max_y = okinawa_bounds
        oki_center_x = (oki_min_x + oki_max_x) / 2
        oki_center_y = (oki_min_y + oki_max_y) / 2

        print(f"  Original bounds: x=[{oki_min_x:.1f}, {oki_max_x:.1f}], y=[{oki_min_y:.1f}, {oki_max_y:.1f}]")
        print(f"  Center: ({oki_center_x:.1f}, {oki_center_y:.1f})")
        print(f"  Scale factor: {scale_factor}x (around center)")

        # Scale Okinawa around its center (no translation)
        geometry[okinawa_code] = transform_path(
            geometry[okinawa_code], dx=0, dy=0, scale=scale_factor,
            center_x=oki_center_x, center_y=oki_center_y
        )

        # Get new bounds
        new_bounds = get_path_bounds(geometry[okinawa_code])
        print(f"  New bounds: x=[{new_bounds[0]:.1f}, {new_bounds[2]:.1f}], y=[{new_bounds[1]:.1f}, {new_bounds[3]:.1f}]")
    print()

    # Step 3: Calculate viewBox
    print("STEP 3: Calculating viewBox...")
    all_bounds = [get_path_bounds(p) for p in geometry.values()]
    all_x = [b[0] for b in all_bounds] + [b[2] for b in all_bounds]
    all_y = [b[1] for b in all_bounds] + [b[3] for b in all_bounds]

    min_x, min_y = min(all_x), min(all_y)
    max_x, max_y = max(all_x), max(all_y)

    viewbox_padding = 10
    viewbox_str = f"{min_x - viewbox_padding:.1f} {min_y - viewbox_padding:.1f} {max_x - min_x + 2*viewbox_padding:.1f} {max_y - min_y + 2*viewbox_padding:.1f}"
    print(f"  ViewBox: {viewbox_str}")
    print()

    # Step 4: Add L-shaped divider
    print("STEP 4: Adding L-shaped divider line...")
    divider_line = "M 0 615 H 615 V 0"
    print(f"  Divider: {divider_line}")
    print()

    # Step 5: Save to JSON
    print("STEP 5: Saving to JSON...")
    output_data = {
        "_metadata": {
            "source": "Wikimedia Commons - File:Japan_template_large.svg",
            "url": "https://commons.wikimedia.org/wiki/File:Japan_template_large.svg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
            "extracted": "2025-12-18",
            "note": "SVG path coordinates only. Prefecture codes 01-47 correspond to JIS X 0401 standard.",
            "transformations": {
                "okinawa_scale": scale_factor,
            },
            "viewBox": viewbox_str,
            "overlay": ["_divider_lines"]
        },
        **geometry,
        "_divider_lines": [divider_line]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"  Saved to {output_path}")
    print()
    print("=" * 70)
    print("SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    main()
