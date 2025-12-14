# Japan Prefecture Map Transformation Guide

## Overview

This guide explains how to transform the Japan prefecture map to create a more compact, square-like layout by relocating Okinawa and Kagoshima's southern islands to the top-left corner.

## What the Transformation Does

1. **Relocates islands**: Moves Okinawa (prefecture 47) and Kagoshima's Amami islands (prefecture 46) to the top-left corner
2. **Scales islands**: Enlarges them by 1.3x for better visibility
3. **Adds dividers**: Draws separating lines to show the relocation
4. **Adjusts viewBox**: Makes the overall map more square (aspect ratio ~1.15:1 instead of elongated)

## Files

- **`transform_japan_map.py`**: The transformation script
- **`/tmp/japan_prefectures.json`**: Original map data
- **`/tmp/japan_prefectures_transformed.json`**: Transformed output

## How to Run

```bash
cd packages/shinymap/python/examples
uv run python transform_japan_map.py
```

## Output Example

```
Original island bounds: x=[22.5, 255.7], y=[504.4, 803.6]
Island center: (139.1, 654.0)

Transformation:
  Scale: 1.3x
  Translate: dx=-9.3, dy=-635.7

Transformed island bounds: x=[-21.7, 281.4], y=[-176.2, 212.8]

New ViewBox: "-31.7 -186.2 844.3 731.7"
Aspect ratio: 1.15:1
```

## Customizing the Transformation

### Adjust Scale Factor

In `transform_japan_map.py`, line ~116:

```python
scale_factor = 1.3  # Try 1.2, 1.5, 2.0, etc.
```

### Adjust Positioning

Change the target position (line ~119-120):

```python
padding = 20  # Increase for more spacing
target_x = padding
target_y = padding
```

### Move Different Prefectures

Change which prefectures to relocate (line ~98):

```python
# Add more prefecture codes as needed
islands_to_move = ['46', '47', '42']  # 42 = Nagasaki (has islands too)
```

### Adjust Divider Lines

The divider line is created around line 169:

```python
divider_y = max(all_y) + 15  # Adjust spacing
divider_line_horizontal = f"M{target_x} {divider_y} L{max(all_x)} {divider_y}"
```

You can add vertical lines too:

```python
# Add vertical divider
divider_x = max(all_x) + 15
divider_line_vertical = f"M{divider_x} {target_y} L{divider_x} {max(all_y)}"
transformed_geometry['_divider_2'] = divider_line_vertical
```

## Using the Transformed Map

### Step 1: Update `japan_prefectures.py`

Replace the geometry loading function:

```python
def load_geometry():
    """Load prefecture geometry from transformed JSON."""
    import json
    with open("/tmp/japan_prefectures_transformed.json", "r") as f:
        data = json.load(f)

    # Separate real prefectures from dividers
    geometry = {k: v for k, v in data.items() if not k.startswith('_')}
    dividers = {k: v for k, v in data.items() if k.startswith('_')}

    return geometry, dividers

# Update globals
JAPAN_GEOMETRY, JAPAN_DIVIDERS = None, None

def get_japan_geometry():
    """Get Japan prefecture geometry."""
    global JAPAN_GEOMETRY, JAPAN_DIVIDERS
    if JAPAN_GEOMETRY is None:
        JAPAN_GEOMETRY, JAPAN_DIVIDERS = load_geometry()
    return JAPAN_GEOMETRY

def get_japan_dividers():
    """Get divider lines."""
    global JAPAN_GEOMETRY, JAPAN_DIVIDERS
    if JAPAN_DIVIDERS is None:
        JAPAN_GEOMETRY, JAPAN_DIVIDERS = load_geometry()
    return JAPAN_DIVIDERS
```

### Step 2: Update `app_japan.py`

Update the viewBox:

```python
# ViewBox calculated from transformed prefecture boundaries
VIEWBOX = "-31.7 -186.2 844.3 731.7"
```

### Step 3: Display Dividers (Optional)

To show the divider lines in your map:

```python
from japan_prefectures import get_japan_dividers

# In your Map visualization:
@render_map
def regions_map():
    fills = {...}  # Your color mapping

    # Merge dividers into geometry for display
    geometry_with_dividers = {**GEOMETRY, **get_japan_dividers()}

    # Assign divider colors
    fills.update({k: "#999999" for k in get_japan_dividers().keys()})

    return (
        Map(geometry_with_dividers, tooltips=TOOLTIPS, view_box=VIEWBOX)
        .with_fill_color(fills)
        .with_stroke_color("#ffffff")
        .with_stroke_width(1.0)
    )
```

## Understanding the Transformation Algorithm

### 1. Parse SVG Paths

```python
def parse_path_commands(path: str) -> List[Tuple[str, List[float]]]:
    # Parses "M100 200 L150 250 Z" into
    # [('M', [100, 200]), ('L', [150, 250]), ('Z', [])]
```

### 2. Calculate Bounds

```python
def get_path_bounds(path: str) -> Tuple[float, float, float, float]:
    # Returns (min_x, min_y, max_x, max_y)
```

### 3. Transform Coordinates

```python
def transform_path(path, dx, dy, scale, center_x, center_y):
    # For each coordinate (x, y):
    # 1. Scale around center: x' = center_x + (x - center_x) * scale
    # 2. Translate: x'' = x' + dx
```

### 4. Rebuild Path String

```python
def build_path_string(commands):
    # Converts back to SVG path format
```

## Troubleshooting

### Islands appear in wrong location
- Check `target_x` and `target_y` values
- Verify `islands_to_move` contains correct prefecture codes

### Islands too small/large
- Adjust `scale_factor`

### Divider lines not showing
- Make sure divider keys (e.g., `_divider_1`) are included in geometry
- Check that dividers have a visible `strokeColor` and `strokeWidth`

### Aspect ratio still not square
- Increase scale factor for islands
- Adjust mainland bounds if needed

## Advanced: Creating Custom Inset Regions

To create multiple inset regions:

```python
# Define regions
insets = {
    'okinawa': {
        'prefectures': ['47'],
        'scale': 1.5,
        'target': (20, 20),
    },
    'northern_islands': {
        'prefectures': ['01'],  # Hokkaido northern tip
        'scale': 1.2,
        'target': (300, 20),
    },
}

# Transform each inset region separately
for name, config in insets.items():
    # ... transform logic ...
```

## Reference: Prefecture Codes

- 46: Kagoshima (鹿児島県) - includes Amami islands
- 47: Okinawa (沖縄県) - southernmost prefecture

## Further Customization

The script provides a foundation. You can extend it to:
- Add labels for inset regions
- Create hatching patterns for relocated areas
- Add zoom indicators
- Create multiple zoom levels
- Generate interactive overlays
