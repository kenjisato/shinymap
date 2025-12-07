from shiny import App, ui

from shinymap import (
    QUALITATIVE,
    Map,
    input_map,
    output_map,
    render_map,
    scale_qualitative,
    scale_sequential,
)

DEMO_GEOMETRY = {
    "circle": "M25,50 A20,20 0 1 1 24.999,50 Z",
    "square": "M10 10 H40 V40 H10 Z",
    "triangle": "M75 70 L90 40 L60 40 Z",
}

TOOLTIPS = {"circle": "Circle", "square": "Square", "triangle": "Triangle"}

# Assign each shape a distinct color from the qualitative palette
SHAPE_COLORS = {"circle": QUALITATIVE[0], "square": QUALITATIVE[1], "triangle": QUALITATIVE[2]}


def selected_ids(counts: dict[str, int] | None) -> list[str]:
    """Return IDs of regions with count > 0."""
    return [id for id, count in (counts or {}).items() if count > 0]


def fills_for_summary(counts: dict[str, int] | None) -> dict[str, str]:
    """Active regions get their assigned color; inactive regions are neutral gray."""
    counts = counts or {}
    return scale_qualitative(
        categories={rid: rid if counts.get(rid, 0) > 0 else None for rid in DEMO_GEOMETRY},
        region_ids=list(DEMO_GEOMETRY.keys()),
        palette=[SHAPE_COLORS[rid] for rid in DEMO_GEOMETRY],
    )


app_ui = ui.page_fluid(
    ui.h2("shinymap demo"),
    ui.layout_columns(
        input_map(
            "region",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="single",
            value={},
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
            value={},
            hover_highlight={"stroke_width": 2, "fill_opacity": -0.3},
        ),
        output_map("counts"),
    ),
)


def server(input, output, session):
    @render_map
    def summary():
        # Fluent builder API (Option B) - method chaining
        # input.region() returns a single selected ID (string) or None for mode="single"
        # But we need a count map for the helper functions, so we'll convert it
        selected = input.region()
        counts = {selected: 1} if selected else {}
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_fills(fills_for_summary(counts))
            .with_counts(counts)
            .with_active(selected_ids(counts))
            .with_stroke_width(1.5)
        )

    @render_map
    def counts():
        # Simple function-based API (Option A) - good for single-line returns
        counts_data = input.clicks() or {}
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_fills(scale_sequential(counts_data, list(DEMO_GEOMETRY.keys()), max_count=10))
            .with_counts(counts_data)
        )


app = App(app_ui, server)
