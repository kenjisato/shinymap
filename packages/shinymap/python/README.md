# shinymap (Python)

Shiny for Python adapter for the core `shinymap` renderer. It bundles the prebuilt JS assets and exposes helpers to drop maps into Shiny apps without touching React.

## API

```python
from shinymap import MapPayload, input_map, output_map, render_map
```

- `input_map(id, geometry, mode="single"|"multiple"|"count", ...)` renders an interactive input that emits a Shiny input value (`str | None`, `list[str]`, or `dict[str, int]` depending on mode).
- `output_map("map")` adds a placeholder in your UI; pair it with a `@render_map` output in the server.
- `MapPayload` models the data you can send to an output map: geometry, tooltips, fills, counts, active ids, etc.
- `render_map` is a convenience decorator that serializes a `MapPayload` (or dict) and mounts the React output map.

## Minimal example

```python
from shiny import App, reactive, ui
from shinymap import MapPayload, input_map, output_map, render_map

DEMO_GEOMETRY = {
    "circle": "M50,10 A40,40 0 1 1 49.999,10 Z",
    "square": "M10 10 H90 V90 H10 Z",
    "triangle": "M50 10 L90 90 H10 Z",
}

app_ui = ui.page_fluid(
    ui.h2("Shinymap demo"),
    ui.layout_columns(
        input_map("region", DEMO_GEOMETRY, tooltips={"circle": "Circle"}, highlight_fill="#2563eb"),
        output_map("summary"),
    ),
)


def server(input, output, session):
    @output
    @render_map
    def summary():
        active = input.region()
        fills = {"circle": "#93c5fd", "square": "#bbf7d0", "triangle": "#fbcfe8"}
        return MapPayload(geometry=DEMO_GEOMETRY, fills=fills, active_ids=active)


app = App(app_ui, server)
```
