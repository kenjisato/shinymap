from shiny import App, ui

from shinymap import input_map

from shared import DEMO_GEOMETRY, TOOLTIPS

# Default -----

_ui_default = ui.card(
    ui.card_header("Default"),
    ui.p("Increases stroke width by 1 on hover."),
    ui.div(
        input_map(
            "stroke_only",
            DEMO_GEOMETRY,
            mode="multiple",
        ),
    ),
)

# Stroke Width -----

_ui_stroke_width = ui.card(
    ui.card_header("Stroke Width Only"),
    ui.p("Increases stroke width by 3 on hover."),
    ui.div(
        input_map(
            "stroke_only",
            DEMO_GEOMETRY,
            mode="multiple",
            hover_highlight={"stroke_width": 3},
        ),
    ),
)


# Stroke and Fill ---------

_ui_stroke_and_fill = ui.card(
    ui.card_header("Stroke and Fill Combined"),
    ui.p("Changes both stroke width and fill color on hover."),
    input_map(
        "stroke_and_fill",
        DEMO_GEOMETRY,
        mode="multiple",
        hover_highlight={"stroke_width": 2, "fill_color": "#bfdbfe"},
    ),
)

# Subtle Highlight ---------

_ui_subtle = ui.card(
    ui.card_header("Subtle Highlight"),
    ui.p("Minimal visual feedback with thin colored border."),
    ui.div(
        input_map(
            "subtle",
            DEMO_GEOMETRY,
            mode="multiple",
            hover_highlight={"stroke_color": "#60a5fa", "stroke_width": 1},
        ),
    ),
)

# Stroke Color ---------------

_ui_stroke_color = ui.card(
    ui.card_header("Stroke Color Change"),
    ui.p("Changes stroke color to red on hover."),
    input_map(
        "stroke_color",
        DEMO_GEOMETRY,
        tooltips=TOOLTIPS,
        mode="multiple",
        hover_highlight={"stroke_color": "#ef4444", "stroke_width": 2},
    ),
)

# Fill Color

_ui_fill_color = ui.card(
    ui.card_header("Fill Color Change"),
    ui.p("Changes fill color to yellow on hover."),
    input_map(
        "fill_color",
        DEMO_GEOMETRY,
        mode="multiple",
        hover_highlight={"fill_color": "#fef08a"},
    ),
)

# Combined 

_ui_combined = ui.card(
    ui.card_header("Combined Effects"),
    ui.p("Combines multiple effects: thicker stroke, and color change."),
    input_map(
        "combined",
        DEMO_GEOMETRY,
        mode="multiple",
        hover_highlight={
            "stroke_width": 3,
            "fill_color": "#fef08a",
            "stroke_color": "#3b82f6",
        },
    ),
)

ui_hover = ui.page_fixed(
    ui.h2("Hover Highlight Demo"),
    ui.p(
        "This demo showcases different hover_highlight configurations. "
        "Hover over the shapes to see the visual feedback. "
        "Note: Opacity changes don't work because hover creates an overlay copy."
    ),
    ui.layout_column_wrap(
        _ui_default,
        _ui_stroke_width,
        _ui_stroke_and_fill,
        _ui_subtle,
        _ui_stroke_color,
        _ui_fill_color,
        _ui_combined,
        width=1/2,
    ),
)

# Put them together ------
def server_hover(input, output, session):
    pass

app = App(ui_hover, server_hover)
