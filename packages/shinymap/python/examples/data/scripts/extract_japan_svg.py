"""Extract prefecture paths from Wikimedia Commons Japan SVG.

Source: https://commons.wikimedia.org/wiki/File:Japan_template_large.svg
License: CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/)
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

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


def extract_paths(svg_path: Path) -> dict[str, str]:
    """Extract prefecture paths from SVG file.

    Prefectures are stored as <g> elements with id attributes.
    Each group may contain multiple <path> elements (for islands).
    We merge all paths within each group into a single path string.

    Northern Territories (Hopporyodo) are included with Hokkaido (01).
    AREA element (dividing lines) is stored with key _divider_lines.

    Args:
        svg_path: Path to the SVG file

    Returns:
        Dictionary mapping prefecture codes to SVG path strings,
        plus _divider_lines for the inverted-L dividers
    """
    # Parse SVG
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Extract paths from groups
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

    # Extract AREA (dividing lines) - direct path element
    for path_elem in root.iter():
        if path_elem.tag.endswith('path'):
            path_id = path_elem.get('id')
            if path_id == 'AREA':
                path_d = path_elem.get('d')
                if path_d:
                    geometry['_divider_lines'] = path_d.strip()

    return geometry


def main():
    """Extract paths and save to JSON."""
    svg_path = Path("/tmp/japan_template_large.svg")
    output_path = Path(__file__).parent / "data" / "japan_prefectures.json"

    print(f"Extracting paths from {svg_path}...")
    geometry = extract_paths(svg_path)

    print(f"Extracted {len(geometry)} prefectures")

    # Verify we got all 47 prefectures
    if len(geometry) != 47:
        missing = set(ROMAJI_TO_CODE.values()) - set(geometry.keys())
        print(f"WARNING: Missing prefectures: {missing}")

    # Create output with attribution header
    output_data = {
        "_metadata": {
            "source": "Wikimedia Commons - File:Japan_template_large.svg",
            "url": "https://commons.wikimedia.org/wiki/File:Japan_template_large.svg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
            "extracted": "2025-12-10",
            "note": "SVG path coordinates only. Prefecture codes 01-47 correspond to JIS X 0401 standard."
        },
        **geometry
    }

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
