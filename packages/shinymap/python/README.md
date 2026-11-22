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
from shinymap.aes.color import scale_sequential, scale_qualitative
from shinymap.mode import Single, Multiple, Cycle, Count, Display
from shinymap.outline import Outline
```

### Map Components

- `input_map(id, outline, mode, ...)` renders an interactive input.
  - Mode classes:
    - `Single()` or `mode="single"`: returns `str | None`
    - `Multiple()` or `mode="multiple"`: returns `list[str]`
    - `Cycle(n=4)`: cycles through n states, returns `dict[str, int]`
    - `Count()`: counting mode, returns `dict[str, int]` (`Count(max_count=10)` caps the indexed aesthetic, not the value)
  - Aesthetics via `aes` parameter:
    - `aes.ByState(base=..., hover=..., select=...)`: state-based styling
    - `aes.ByGroup(__all=..., region_id=...)`: per-region styling
    - `aes.Indexed(fill_color=[...])`: indexed colors for cycle/count modes
  - `raw=True` returns the `dict[str, int]` value in every mode
  - Works inside Shiny modules (ids are resolved through the module namespace)
- `output_map("map", outline, ...)` adds a placeholder with static parameters.
  - `mode=Display()`: hover-only output map
  - `mode=Display(clickable=True)`: output map with click events (`input_id=` to choose the input name)
- `Map` provides a fluent API for building map payloads with method chaining.
- `render_map` decorator serializes a `Map` and mounts the React output map.
- `scale_sequential()` and `scale_qualitative()` (in `shinymap.aes.color`) generate fill color maps.

### Outline Utilities

The `shinymap.outline` subpackage provides tools for working with SVG outlines:

- **`Outline.from_svg(svg_path)`**: Extract geometry from SVG files (polymorphic elements)
- **`Outline.from_json(json_path)`**: Load geometry from shinymap JSON files
- **`outline.relabel({...})`**: Rename or merge regions
- **`outline.set_overlays([...])`**: Mark overlay regions
- **`outline.move_layer("overlay", "a", "b")`**: Assign regions to `underlay` / `overlay` / `hidden` (or back to `main`)
- **`outline.move_group("group", "a", "b")`**: Merge regions into a group
- **`outline.path_as_line("_dividers")`**: Mark regions as lines for stroke-only rendering
- **`outline.to_json(path)`**: Export to JSON file

**SVG element classes** (`Circle`, `Rect`, `Ellipse`, `Path`, `Polygon`, `Line`, `Text`) live in `shinymap.svg`.

### Preparing SVG files (`shinymap.kit`)

```bash
# Interactive app: rename regions, set groups and layers, mark lines,
# then download the JSON and the Python code that reproduces it
uv run python -m shinymap.kit.sketch -f map.svg

# Reference SVG with region IDs overlaid
uv run python -m shinymap.kit.caption map.svg
```

## Minimal example

```python
from shiny import App, ui
from shinymap import Map, input_map, output_map, render_map, aes
from shinymap.mode import Count
from shinymap.outline import Outline

DEMO_OUTLINE = Outline.from_dict({
    "circle": [{"type": "circle", "cx": 25, "cy": 50, "r": 20}],
    "square": [{"type": "rect", "x": 10, "y": 10, "width": 30, "height": 30}],
    "triangle": [{"type": "path", "d": "M75 70 L90 40 L60 40 Z"}],
    "_metadata": {"viewBox": "0 0 100 100"},
})

TOOLTIPS = {"circle": "Circle", "square": "Square", "triangle": "Triangle"}


app_ui = ui.page_fluid(
    ui.h2("shinymap demo"),
    ui.layout_columns(
        input_map(
            "region",
            DEMO_OUTLINE,
            tooltips=TOOLTIPS,
            mode="single",  # Returns str | None
        ),
        output_map("summary", DEMO_OUTLINE, tooltips=TOOLTIPS),
    ),
    ui.br(),
    ui.h4("Counts"),
    ui.layout_columns(
        input_map(
            "clicks",
            DEMO_OUTLINE,
            tooltips=TOOLTIPS,
            mode=Count(),  # Returns dict[str, int]
        ),
        output_map("counts", DEMO_OUTLINE, tooltips=TOOLTIPS),
    ),
)


def server(input, output, session):
    @render_map
    def summary():
        selected = input.region()
        # Value dict: selected region has value=1
        value = {selected: 1} if selected else {}
        return Map().with_value(value)

    @render_map
    def counts():
        counts_data = input.clicks() or {}
        return Map().with_value(counts_data)


app = App(app_ui, server)
```
