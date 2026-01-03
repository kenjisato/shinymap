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
from shinymap.mode import Single, Multiple, Cycle, Count, Display
from shinymap.outline import Outline
```

### Map Components

- `input_map(id, outline, mode, ...)` renders an interactive input.
  - Mode classes:
    - `Single()` or `mode="single"`: returns `str | None`
    - `Multiple()` or `mode="multiple"`: returns `list[str]`
    - `Cycle(n=4)`: cycles through n states, returns `dict[str, int]`
    - `Count()` or `Count(max=10)`: counting mode, returns `dict[str, int]`
  - Aesthetics via `aes` parameter:
    - `aes.ByState(base=..., hover=..., select=...)`: state-based styling
    - `aes.ByGroup(__all=..., region_id=...)`: per-region styling
    - `aes.Indexed(fill_color=[...])`: indexed colors for cycle/count modes
- `output_map("map", outline, ...)` adds a placeholder with static parameters.
  - `mode=Display()`: hover-only output map
  - `mode=Display(clickable=True)`: output map with click events
- `Map` provides a fluent API for building map payloads with method chaining.
- `render_map` decorator serializes a `Map` and mounts the React output map.
- `scale_sequential()` and `scale_qualitative()` generate fill color maps.

### Outline Utilities

The `shinymap.outline` subpackage provides tools for working with SVG geometry:

- **`Outline.from_svg(svg_path)`**: Extract geometry from SVG files (polymorphic elements)
- **`Outline.from_json(json_path)`**: Load geometry from shinymap JSON files
- **`outline.relabel({...})`**: Rename or merge regions
- **`outline.set_overlays([...])`**: Mark overlay regions
- **`outline.path_as_line("_dividers")`**: Mark regions as lines for stroke-only rendering
- **`outline.to_json(path)`**: Export to JSON file

**Polymorphic elements**: Circle, Rect, Ellipse, Path, Polygon, Line, Text

**Interactive converter app**:
```bash
uv run python -m shinymap.outline.converter -b
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
