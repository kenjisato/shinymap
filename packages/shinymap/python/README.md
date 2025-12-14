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
from shinymap import Map, MapPayload, input_map, output_map, render_map
from shinymap import scale_sequential, scale_qualitative, SEQUENTIAL, QUALITATIVE
from shinymap.geometry import load_geometry, convert, from_svg, from_json
```

### Map Components

- `input_map(id, geometry, mode="single"|"multiple"|"count", cycle=None, max_selection=None, hover_highlight=None, ...)` renders an interactive input.
  - For `mode="single"`: returns a single selected region ID (string) or None
  - For `mode="multiple"`: returns a list of selected region IDs
  - For `mode="count"`: returns a dict mapping region IDs to counts
  - `hover_highlight` accepts a dict with keys: `stroke_width`, `fill_opacity`, `stroke_color`, `fill_color` for customizing hover effects
    - Hover effects are rendered as an overlay layer on top to ensure full border visibility
    - Default hover highlight: `{"stroke_width": 2, "stroke_color": "#1e40af"}` (blue-800)
- `output_map("map")` adds a placeholder in your UI; pair it with a `@render_map` output in the server.
- `Map` (alias for `MapBuilder`) provides a fluent API for building map payloads with method chaining.
- `MapPayload` models the data you can send to an output map: geometry, tooltips, fills, counts, active ids, default aesthetics, etc.
- `render_map` is a convenience decorator that serializes a `Map`/`MapPayload` (or dict) and mounts the React output map.
- `scale_sequential(counts, region_ids, max_count=None)` and `scale_qualitative(categories, region_ids, palette=None)` are helper functions for generating fill color maps.

### Geometry Utilities

The `shinymap.geometry` subpackage provides tools for converting SVG files to shinymap's JSON format:

- **`load_geometry(json_path, overlay_keys=None)`**: Load geometry from shinymap JSON files. Returns `(geometry, overlay_geometry, viewbox)` tuple.
- **`from_svg(svg_path, output_path=None)`**: Extract intermediate JSON from SVG file with auto-generated path IDs.
- **`from_json(intermediate_json, output_path=None, relabel=None, ...)`**: Transform intermediate JSON by renaming/merging paths.
- **`convert(input_path, output_path=None, relabel=None, ...)`**: One-shot SVG to JSON conversion.
- **`infer_relabel(initial_file, final_json)`**: Infer relabel mapping from existing transformations.

**Interactive converter app**:
```bash
uv run python -m shinymap.geometry.converter -b
```

See [geometry package documentation](src/shinymap/geometry/__init__.py) for detailed workflow examples.

**Geometry format**: Shinymap uses a list-based path format where each region maps to a **list** of SVG path strings:
```python
geometry = {
    "circle": ["M25,50 A20,20 0 1 1 24.999,50 Z"],  # Single-element list
    "hokkaido": ["M 0 0...", "M 200 0..."],         # Multi-element list (merged paths)
}
```

## Minimal example

```python
from shiny import App, ui
from shinymap import Map, input_map, output_map, render_map, scale_sequential

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
            mode="single",
            hover_highlight={"stroke_width": 1},
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
            mode="count",
            hover_highlight={"stroke_width": 2, "fill_opacity": -0.3},
        ),
        output_map("counts"),
    ),
)


def server(input, output, session):
    @render_map
    def summary():
        # mode="single" returns a single ID (string) or None
        selected = input.region()
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_active(selected)
            .with_stroke_width(1.5)
        )

    @render_map
    def counts():
        # mode="count" returns a dict mapping region IDs to counts
        counts_data = input.clicks() or {}
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_fills(scale_sequential(counts_data, list(DEMO_GEOMETRY.keys()), max_count=10))
            .with_counts(counts_data)
        )


app = App(app_ui, server)
```
