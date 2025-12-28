# shinymap (Python)

Shiny for Python adapter for the core `shinymap` renderer. It bundles the prebuilt JS assets and exposes helpers to drop maps into Shiny apps without touching React.

## Installation

```bash
pip install shinymap
```

Or with uv:

```bash
uv add shinymap
```

## API

```python
from shinymap import Map, input_map, output_map, render_map, aes
from shinymap import scale_sequential, scale_qualitative
from shinymap.mode import Single, Multiple, Cycle, Count
from shinymap.geometry import Geometry
```

### Map Components

- `input_map(id, geometry, mode, ...)` renders an interactive input.
  - Mode classes (v0.2.0):
    - `Single()` or `mode="single"`: returns `str | None`
    - `Multiple()` or `mode="multiple"`: returns `list[str]`
    - `Cycle(n=4)`: cycles through n states, returns `dict[str, int]`
    - `Count()` or `Count(max=10)`: counting mode, returns `dict[str, int]`
  - Aesthetics via `aes` parameter:
    - `aes.ByState(base=..., hover=..., select=...)`: state-based styling
    - `aes.ByGroup(__all=..., region_id=...)`: per-region styling
    - `aes.Indexed(fill_color=[...])`: indexed colors for cycle/count modes
- `output_map("map", geometry, ...)` adds a placeholder with static parameters.
- `Map` provides a fluent API for building map payloads with method chaining.
- `render_map` decorator serializes a `Map` and mounts the React output map.
- `scale_sequential()` and `scale_qualitative()` generate fill color maps.

### Geometry Utilities

The `shinymap.geometry` subpackage provides tools for working with SVG geometry:

- **`Geometry.from_svg(svg_path)`**: Extract geometry from SVG files (v1.x polymorphic elements)
- **`Geometry.from_json(json_path)`**: Load geometry from shinymap JSON files
- **`geo.relabel({...})`**: Rename or merge regions
- **`geo.set_overlays([...])`**: Mark overlay regions
- **`geo.path_as_line("_dividers")`**: Mark regions as lines for stroke-only rendering
- **`geo.to_json(path)`**: Export to JSON file

**Polymorphic elements** (v0.2.0): Circle, Rect, Ellipse, Path, Polygon, Line, Text

**Interactive converter app**:
```bash
uv run python -m shinymap.geometry.converter -b
```

## Minimal example

```python
from shiny import App, ui
from shinymap import Map, input_map, output_map, render_map, scale_sequential, aes
from shinymap.mode import Count

DEMO_GEOMETRY = {
    "circle": ["M25,50 A20,20 0 1 1 24.999,50 Z"],
    "square": ["M10 10 H40 V40 H10 Z"],
    "triangle": ["M75 70 L90 40 L60 40 Z"],
}

TOOLTIPS = {"circle": "Circle", "square": "Square", "triangle": "Triangle"}


app_ui = ui.page_fluid(
    ui.h2("shinymap demo"),
    ui.layout_columns(
        input_map(
            "region",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="single",  # Returns str | None
        ),
        output_map("summary"),
    ),
    ui.br(),
    ui.h4("Counts"),
    ui.layout_columns(
        input_map(
            "clicks",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode=Count(),  # Returns dict[str, int]
        ),
        output_map("counts"),
    ),
)


def server(input, output, session):
    @render_map
    def summary():
        selected = input.region()
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_active(selected)
        )

    @render_map
    def counts():
        counts_data = input.clicks() or {}
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_fill_color(scale_sequential(counts_data, list(DEMO_GEOMETRY.keys()), max_count=10))
            .with_counts(counts_data)
        )


app = App(app_ui, server)
```
