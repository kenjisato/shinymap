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


# Opacity (Darken) ---------

_ui_darken = ui.card(
    ui.card_header("Fill Opacity - Darken"),
    ui.p("Reduces fill opacity by 0.3 on hover (darkening effect)."),
    input_map(
        "darken",
        DEMO_GEOMETRY,
        mode="multiple",
        default_aesthetic={"fillColor": "black", "fillOpacity": 0.2},
        hover_highlight={"fill_opacity": 0.3},
    ),
)

# Opacity (Brighten) ---------

_ui_brighten = ui.card(
    ui.card_header("Fill Opacity - Brighten"),
    ui.p("Increases fill opacity by 0.2 on hover (brightening effect)."),
    ui.div(
        input_map(
            "brighten",
            DEMO_GEOMETRY,
            mode="multiple",
            default_aesthetic={"fillColor": "slategray"},
            hover_highlight={"fill_opacity": -0.2},
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
        "Hover over the shapes to see the visual feedback."
    ),
    ui.layout_column_wrap(
        _ui_default,
        _ui_stroke_width, 
        _ui_darken,
        _ui_brighten,
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
