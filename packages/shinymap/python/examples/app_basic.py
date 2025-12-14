from shiny import App, ui, render

from shinymap import Map, input_map, output_map, render_map, scale_qualitative

from shared import DEMO_GEOMETRY, TOOLTIPS, SHAPE_COLORS


# Single Select Example ---------
_ui_single = ui.card(
    ui.card_header("Single Select"),
    ui.layout_columns(
        input_map(
            "region_single",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="single",
            hover_highlight={"stroke_width": 1},
        ),
        ui.div(
            ui.help_text("Selected region: "),
            ui.output_text_verbatim("single_select", placeholder=True),
        ),
    ),
)

def _server_single(input, output, session):
    @render.text
    def single_select():
        return input.region_single()


# Multiple Select Example --------
_ui_multiple = ui.card(
    ui.card_header("Multiple Select"),
    ui.layout_columns(
        input_map(
            "region_multi",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="multiple",
            hover_highlight={"stroke_width": 1},
        ),
        ui.div(
            ui.help_text("Selected regions:"),
            ui.output_text_verbatim("multi_select", placeholder=True),
        )
    )
)

def _server_multiple(input, output, session):
    @render.text
    def multi_select():
        return input.region_multi()



# Put them together --------------
ui_basic = ui.page_fixed(
    _ui_single,
    _ui_multiple,
    title="Basic Examples",
)


def server_basic(input, output, session):
    _server_single(input, output, session)
    _server_multiple(input, output, session)



app = App(ui_basic, server_basic)
