"""Demo comparing different APIs for building output maps."""

from shiny import App, ui

from shinymap import Map, MapPayload, input_map, output_map, render_map, scale_sequential

DEMO_GEOMETRY = {
    "circle": "M25,50 A20,20 0 1 1 24.999,50 Z",
    "square": "M10 10 H40 V40 H10 Z",
    "triangle": "M75 70 L90 40 L60 40 Z",
}

TOOLTIPS = {"circle": "Circle", "square": "Square", "triangle": "Triangle"}


app_ui = ui.page_fluid(
    ui.h2("Builder API Comparison Demo"),
    ui.p("Both output maps below show the same result, using different APIs."),
    input_map("clicks", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="count", value={}),
    ui.hr(),
    # Method chaining (Recommended)
    ui.h3("1. Method Chaining (Recommended)"),
    ui.p("Most intuitive for complex maps with many properties. Reads naturally and supports auto-completion."),
    ui.tags.pre(
        ui.tags.code(
            """@render_map
def builder_chain():
    counts = input.clicks()
    return (
        Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
        .with_fills(scale_sequential(counts, list(DEMO_GEOMETRY.keys())))
        .with_counts(counts)
        .with_stroke_width(2)
    )"""
        )
    ),
    output_map("builder_chain"),
    ui.hr(),
    # Dataclass
    ui.h3("2. Dataclass Constructor (Alternative)"),
    ui.p("Good for curried functions or when you prefer explicit parameter names."),
    ui.tags.pre(
        ui.tags.code(
            """@render_map
def dataclass_style():
    counts = input.clicks()
    return MapPayload(
        geometry=DEMO_GEOMETRY,
        tooltips=TOOLTIPS,
        fills=scale_sequential(counts, list(DEMO_GEOMETRY.keys())),
        counts=counts,
        default_aesthetic={"strokeWidth": 2}
    )"""
        )
    ),
    output_map("dataclass_style"),
)


def server(input, output, session):
    @render_map
    def builder_chain():
        # Method chaining (Recommended)
        counts = input.clicks() or {}
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_fills(scale_sequential(counts, list(DEMO_GEOMETRY.keys())))
            .with_counts(counts)
            .with_stroke_width(2)
        )

    @render_map
    def dataclass_style():
        # Dataclass constructor (Alternative)
        counts = input.clicks() or {}
        return MapPayload(
            geometry=DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            fills=scale_sequential(counts, list(DEMO_GEOMETRY.keys())),
            counts=counts,
            default_aesthetic={"strokeWidth": 2},
        )


app = App(app_ui, server)
