from shiny import App, reactive, ui

from shinymap import MapPayload, input_map, output_map, render_map

DEMO_GEOMETRY = {
    "circle": "M50,10 A40,40 0 1 1 49.999,10 Z",
    "square": "M10 10 H90 V90 H10 Z",
    "triangle": "M50 10 L90 90 H10 Z",
}

TOOLTIPS = {"circle": "Circle", "square": "Square", "triangle": "Triangle"}
FILLS = {"circle": "#93c5fd", "square": "#bbf7d0", "triangle": "#fbcfe8"}


app_ui = ui.page_fluid(
    ui.h2("shinymap demo"),
    ui.layout_columns(
        input_map("region", DEMO_GEOMETRY, tooltips=TOOLTIPS, highlight_fill="#2563eb"),
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
            highlight_fill="#f97316",
            hover_fill="#fb923c",
        ),
        output_map("counts"),
    ),
)


def server(input, output, session):
    @reactive.Calc
    def count_ceiling():
        counts = input.clicks() or {}
        return max(counts.values(), default=0) or 1

    @output
    @render_map
    def summary():
        active = input.region()
        return MapPayload(
            geometry=DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            fills=FILLS,
            active_ids=active,
        )

    @output
    @render_map
    def counts():
        return MapPayload(
            geometry=DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            fills=FILLS,
            counts=input.clicks(),
            max_count=count_ceiling(),
        )


app = App(app_ui, server)
