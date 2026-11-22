# API Cookbook

Code patterns and examples for shinymap development.

## Core Concepts

### Unified Value Model

Internally uses `{region_id: int}` representation:
- `value = 0` or missing ’ not selected
- `value > 0` ’ selected

Python API transforms to ergonomic types:
- `mode="single"` ’ `str | None`
- `mode="multiple"` ’ `list[str]`
- `Count()` / `Cycle(n)` ’ `dict[str, int]`

### Late Serialization

Keep typed Python objects as long as possible. Serialize to dict/JSON only at the JavaScript boundary.

## Input Map Patterns

### Basic Input Map

```python
from shinymap import input_map
from shinymap.outline import Outline

outline = Outline.from_json("map.json")
input_map("region", outline, mode="single")
```

### With Custom Aesthetics (wash)

```python
from shinymap import wash, aes, PARENT

wc = wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#e2e8f0", stroke_color="#94a3b8"),
        select=aes.Shape(fill_color="#bfdbfe", stroke_color="#1e40af"),
        hover=aes.Shape(stroke_width=PARENT.stroke_width + 0.5),
    ),
    line=aes.Line(stroke_color="#94a3b8", stroke_width=0.5),
)

wc.input_map("region", outline, mode="single")
```

### Count Mode with Indexed Colors

```python
from shinymap.mode import Count
from shinymap.aes.color import SEQUENTIAL_ORANGE

wc.input_map(
    "counts",
    outline,
    mode=Count(aes=aes.Indexed(fill_color=["lightgray", *SEQUENTIAL_ORANGE])),
)
```

## Output Map Patterns

### Basic Output Map

```python
from shinymap import output_map, render_map, Map

output_map("my_map", outline)

@render_map
def my_map():
    return Map(outline).with_value(counts)
```

### Per-Region Colors

```python
from shinymap import Map, aes, render_map

@render_map
def categorical_map():
    region_aes = {
        region: aes.Shape(fill_color=COLORS[category])
        for region, category in categories.items()
    }
    return Map(outline, aes=aes.ByGroup(**region_aes))
```

### Display Mode (Clickable Output)

```python
from shinymap.mode import Display

output_map(
    "clickable_map",
    outline,
    mode=Display(clickable=True, input_id="clicked_region")
)

# In server:
@reactive.effect
@reactive.event(input.clicked_region)
def handle_click():
    region_id = input.clicked_region()
```

## Outline Manipulation

### Loading and Creating

```python
from shinymap.outline import Outline

# From JSON file
outline = Outline.from_json("map.json")

# From SVG file
outline = Outline.from_svg("map.svg", extract_viewbox=True)

# From dict
outline = Outline.from_dict({
    "a": "M 0 0 L 10 0 L 10 10 Z",
    "b": "M 20 0 L 30 0 L 30 10 Z",
})
```

### Layer Configuration

```python
# Fluent API
outline = (
    Outline.from_json("map.json")
    .move_layer("underlay", "_grid", "_background")
    .move_layer("overlay", "_border", "_dividers")
    .move_layer("hidden", "_construction_guides")
    .move_layer("main", "_region_to_restore")
)

# Query layers
outline.overlay_ids()    # Region IDs in overlay layer
outline.underlay_ids()   # Region IDs in underlay layer
outline.hidden_ids()     # Region IDs in hidden layer
```

### Relabeling/Merging Regions

```python
# Fluent API
outline = (
    Outline.from_svg("map.svg")
    .move_group("hokkaido", "path_1", "path_2", "path_3")  # Merge
    .move_group("tokyo", "path_4")                          # Rename
)

# Traditional API
outline = outline.relabel({
    "hokkaido": ["path_1", "path_2", "path_3"],
    "tokyo": "path_4",
})
```

## Color Scales

```python
from shinymap.aes.color import (
    scale_sequential, scale_diverging, scale_qualitative,
    SEQUENTIAL_BLUE, SEQUENTIAL_ORANGE, QUALITATIVE
)

# Sequential (count data)
fills = scale_sequential(counts, region_ids, palette=SEQUENTIAL_BLUE, max_count=10)

# Diverging (positive/negative)
fills = scale_diverging(
    values, region_ids,
    low_color="#ef4444", mid_color="#f3f4f6", high_color="#3b82f6"
)

# Qualitative (categories)
fills = scale_qualitative(categories, region_ids, palette=QUALITATIVE)
```

## Static Analysis with StillLife

```python
from shinymap import Wash, StillLife, aes, Outline

wc = Wash(shape=aes.ByState(
    base=aes.Shape(fill_color="#e2e8f0"),
    select=aes.Shape(fill_color="#3b82f6"),
))

outline = Outline.from_dict({"a": "M 0 0 L 10 0 L 10 10 Z"})
builder = wc.build(outline, value={"a": 1})

pic = StillLife(builder)
pic.aes("a")["fill_color"]  # Resolved aesthetic
pic.aes_table()              # All regions

# SVG export
pic.to_svg()                    # Returns string
pic.to_svg(output="map.svg")    # Writes file
```

## MapBuilder Methods

```python
Map(outline, tooltips=tooltips, value=value, aes=aes_config)

# Fluent API
Map(outline).with_value(value).with_aes(aes_config)
```

Available methods:
- `.with_value(dict)` - Set region values
- `.with_aes(ByGroup|ByState|Shape)` - Set aesthetics
- `.with_tooltips(dict)` - Set region tooltips
- `.with_view_box(tuple)` - Set SVG viewBox
- `.with_layers(dict)` - Set layer configuration
