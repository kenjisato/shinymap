# Japan Prefecture Map Transformation Guide

## Overview

This script extracts prefecture paths from the Wikimedia Commons Japan SVG and transforms Okinawa (prefecture 47) for better visibility.

## What the Script Does

1. **Extracts paths**: Reads prefecture paths from Japan_template_large.svg
2. **Merges Hopporyodo**: Combines Northern Territories with Hokkaido (prefecture 01)
3. **Scales Okinawa**: Enlarges Okinawa by 1.4x around its center for better visibility
4. **Calculates viewBox**: Computes proper viewBox to fit all transformed prefectures
5. **Adds dividers**: Includes L-shaped divider line from original SVG

## Files

- **[transform_japan.py](transform_japan.py)**: Complete extraction and transformation script
- **[../Japan_template_large.svg](../Japan_template_large.svg)**: Original SVG from Wikimedia Commons
- **[../japan_prefectures.json](../japan_prefectures.json)**: Output JSON with transformed paths

## How to Run

```bash
cd packages/shinymap/python/examples
uv run python data/scripts/transform_japan.py
```

## Output Example

```
======================================================================
Japan Prefecture Map: Extract and Transform
======================================================================
Input:  .../Japan_template_large.svg
Output: .../japan_prefectures.json

STEP 1: Extracting paths from SVG...
  Extracted 47 prefectures

STEP 2: Scaling Okinawa (prefecture 47) by 1.4x...
  Original bounds: x=[141.0, 483.0], y=[314.0, 525.0]
  Center: (312.0, 419.5)
  Scale factor: 1.4x (around center)
  New bounds: x=[72.6, 551.4], y=[271.8, 567.2]

STEP 3: Calculating viewBox...
  ViewBox: 62.6 85.0 1323.4 1452.0

STEP 4: Adding L-shaped divider line...
  Divider: M 0 615 H 615 V 0

STEP 5: Saving to JSON...
  Saved to .../japan_prefectures.json

======================================================================
SUCCESS!
======================================================================
```

## Technical Details

### Dependencies

The script uses [svgpathtools](https://github.com/mathandy/svgpathtools) to properly handle all SVG path commands including relative commands (lowercase l, m, h, v). This ensures accurate transformation of complex paths.

Install dependencies:
```bash
uv add --dev svgpathtools
```

### How It Works

1. **Path Extraction**: Uses `xml.etree.ElementTree` to parse SVG and extract `<path>` elements from prefecture `<g>` groups
2. **Hopporyodo Merging**: Collects paths from the "Hopporyodo" group and appends them to Hokkaido (code 01)
3. **Path Transformation**: Uses svgpathtools to:
   - Parse SVG path strings into segment objects
   - Transform each segment (scale around center, then translate)
   - Convert back to SVG path string
4. **Bounds Calculation**: Uses svgpathtools' `bbox()` method for accurate bounding box calculation

### Why svgpathtools?

SVG paths can use both absolute (uppercase) and relative (lowercase) commands:
- Absolute: `M 100 200 L 150 250` (coordinates are absolute positions)
- Relative: `m 100 200 l 50 50` (coordinates are offsets from current position)

The original SVG uses relative commands extensively. Custom regex parsing fails because it doesn't track the current position. svgpathtools handles this correctly by maintaining path state.

## Customization

### Adjust Okinawa Scale Factor

In [transform_japan.py:226](transform_japan.py#L226):

```python
scale_factor = 1.4  # Try 1.2, 1.5, 2.0, etc.
```

### Transform Different Prefectures

Modify the script to scale other prefectures. For example, to scale Kagoshima (46):

```python
# After Okinawa transformation
kagoshima_code = '46'
if kagoshima_code in geometry:
    bounds = get_path_bounds(geometry[kagoshima_code])
    center_x = (bounds[0] + bounds[2]) / 2
    center_y = (bounds[1] + bounds[3]) / 2
    geometry[kagoshima_code] = transform_path(
        geometry[kagoshima_code],
        dx=0, dy=0, scale=1.2,
        center_x=center_x, center_y=center_y
    )
```

### Adjust Divider Lines

The divider line is hardcoded from the original SVG in [transform_japan.py:285](transform_japan.py#L285):

```python
divider_line = "M 0 615 H 615 V 0"
```

To add custom dividers:

```python
# Add multiple divider lines
output_data["_divider_lines"] = [
    "M 0 615 H 615 V 0",  # Original L-shape
    "M 615 615 L 1200 615"  # Additional horizontal line
]
```

## Output Format

The generated JSON has this structure:

```json
{
  "_metadata": {
    "source": "Wikimedia Commons - File:Japan_template_large.svg",
    "url": "https://commons.wikimedia.org/wiki/File:Japan_template_large.svg",
    "license": "CC BY-SA 3.0",
    "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
    "extracted": "2025-12-18",
    "note": "SVG path coordinates only. Prefecture codes 01-47 correspond to JIS X 0401 standard.",
    "transformations": {
      "okinawa_scale": 1.4
    },
    "viewBox": "62.6 85.0 1323.4 1452.0",
    "overlays": ["_divider_lines"]
  },
  "01": "M 892 467 C ...",  // Hokkaido (with merged Hopporyodo)
  "02": "M 880 546 C ...",  // Aomori
  ...
  "47": "M 72.6 314 C ...",  // Okinawa (scaled)
  "_divider_lines": ["M 0 615 H 615 V 0"]
}
```

## Prefecture Code Reference

All 47 prefectures follow JIS X 0401 standard:

| Code | Prefecture | Notes |
|------|------------|-------|
| 01 | Hokkaido (北海道) | Includes merged Hopporyodo (Northern Territories) |
| 02-09 | Tohoku region | Aomori, Iwate, Miyagi, Akita, Yamagata, Fukushima, Ibaraki, Tochigi |
| 10 | Gunma (群馬県) | **Note**: SVG uses "Gumma" spelling |
| 11-14 | Kanto region | Saitama, Chiba, Tokyo, Kanagawa |
| 15 | Niigata (新潟県) | **Note**: SVG uses "Nigata" spelling |
| 16-30 | Chubu-Kansai | Toyama through Wakayama |
| 31-35 | Chugoku region | Tottori, Shimane, Okayama, Hiroshima, Yamaguchi |
| 36-39 | Shikoku region | Tokushima, Kagawa, Ehime, Kochi |
| 40-46 | Kyushu region | Fukuoka through Kagoshima |
| 47 | Okinawa (沖縄県) | **Scaled 1.4x** in transformed output |

## License

Source SVG: [Wikimedia Commons - Japan_template_large.svg](https://commons.wikimedia.org/wiki/File:Japan_template_large.svg)
License: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

The transformation script and this documentation are part of the shinymap project (MIT License).

## Troubleshooting

### Missing Prefectures

If the script reports missing prefectures, check the SVG file for:
- Non-standard romanization (Gumma vs Gunma, Nigata vs Niigata)
- Different group IDs in the SVG structure

### Transform Fails

If transformation produces corrupted paths:
- Ensure svgpathtools is installed: `uv sync`
- Check that the SVG file is valid and well-formed
- Verify the path string can be parsed: `parse_path(path_string)`

### ViewBox Too Large/Small

The viewBox is automatically calculated from bounds. To manually adjust:

```python
# In transform_japan.py, after calculating bounds
viewbox_padding = 20  # Increase for more padding
min_x -= viewbox_padding
min_y -= viewbox_padding
max_x += viewbox_padding
max_y += viewbox_padding
```

## Advanced Usage

### Extract Without Transformation

To extract paths without any transformation:

```python
from transform_japan import extract_paths
from pathlib import Path

geometry = extract_paths(Path("Japan_template_large.svg"))
# geometry now contains raw paths without Okinawa scaling
```

### Custom Transformation

Apply custom transformations to any prefecture:

```python
from transform_japan import transform_path, get_path_bounds

# Scale Tokyo 2x around its center
tokyo_path = geometry['13']
bounds = get_path_bounds(tokyo_path)
center_x = (bounds[0] + bounds[2]) / 2
center_y = (bounds[1] + bounds[3]) / 2

geometry['13'] = transform_path(
    tokyo_path,
    dx=0, dy=0,
    scale=2.0,
    center_x=center_x,
    center_y=center_y
)
```
