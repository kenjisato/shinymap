from shiny import App, ui

from shinymap import input_map

DEMO_GEOMETRY = {
    "circle": "M25,50 A20,20 0 1 1 24.999,50 Z",
    "square": "M10 10 H40 V40 H10 Z",
    "triangle": "M75 70 L90 40 L60 40 Z",
}

TOOLTIPS = {"circle": "Circle", "square": "Square", "triangle": "Triangle"}


app_ui = ui.page_fluid(
    ui.h2("Hover Highlight Demo"),
    ui.p(
        "This demo showcases different hover_highlight configurations. "
        "Hover over the shapes to see the visual feedback."
    ),
    ui.h3("1. Stroke Width Only"),
    ui.p("Increases stroke width by 2 on hover (subtle border thickening)."),
    ui.div(
        input_map(
            "stroke_only",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="multiple",
            value={},
            hover_highlight={"stroke_width": 2},
        ),
        style="max-width: 400px; margin-bottom: 2rem;",
    ),
    ui.h3("2. Fill Opacity - Darken"),
    ui.p("Reduces fill opacity by 0.3 on hover (darkening effect)."),
    ui.div(
        input_map(
            "darken",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="multiple",
            value={},
            hover_highlight={"fill_opacity": -0.3},
        ),
        style="max-width: 400px; margin-bottom: 2rem;",
    ),
    ui.h3("3. Fill Opacity - Brighten"),
    ui.p("Increases fill opacity by 0.2 on hover (brightening effect)."),
    ui.div(
        input_map(
            "brighten",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="multiple",
            value={},
            hover_highlight={"fill_opacity": 0.2},
        ),
        style="max-width: 400px; margin-bottom: 2rem;",
    ),
    ui.h3("4. Stroke Color Change"),
    ui.p("Changes stroke color to red on hover."),
    ui.div(
        input_map(
            "stroke_color",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="multiple",
            value={},
            hover_highlight={"stroke_color": "#ef4444", "stroke_width": 2},
        ),
        style="max-width: 400px; margin-bottom: 2rem;",
    ),
    ui.h3("5. Fill Color Change"),
    ui.p("Changes fill color to yellow on hover."),
    ui.div(
        input_map(
            "fill_color",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="multiple",
            value={},
            hover_highlight={"fill_color": "#fef08a"},
        ),
        style="max-width: 400px; margin-bottom: 2rem;",
    ),
    ui.h3("6. Combined Effects"),
    ui.p("Combines multiple effects: thicker stroke, darker fill, and color change."),
    ui.div(
        input_map(
            "combined",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="multiple",
            value={},
            hover_highlight={
                "stroke_width": 3,
                "fill_opacity": -0.2,
                "stroke_color": "#3b82f6",
            },
        ),
        style="max-width: 400px; margin-bottom: 2rem;",
    ),
    ui.h3("7. No Hover Highlight (Default)"),
    ui.p("Default behavior with no hover_highlight parameter (stroke width +1)."),
    ui.div(
        input_map(
            "default",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="multiple",
            value={},
        ),
        style="max-width: 400px; margin-bottom: 2rem;",
    ),
)


def server(input, output, session):
    pass


app = App(app_ui, server)
