from shiny import App, render, ui

from shinymap import aes, input_map

from shared import DEMO_GEOMETRY, code_sample

# Single Select Example ---------
_ui_single = ui.card(
    ui.card_header("Single Select"),
    ui.layout_columns(
        ui.div(
            ui.h4("Code"),
            code_sample("""\
                from shinymap import wash, aes

                # Create wash with default aesthetics
                wc = wash(
                    shape=aes.ByState(
                        base=aes.Shape(fill_color="#f0f9ff", stroke_color="#0369a1"),
                        select=aes.Shape(fill_color="#7dd3fc"),
                    ),
                )

                # UI
                wc.input_map("region_single", GEOMETRY, mode="single")

                # SERVER
                def server(input):
                    # input.region_single() returns str | None
                    ...
                """
            )
        ),
        ui.div(
            ui.h4("Input Map"),
            input_map(
                "region_single",
                DEMO_GEOMETRY,
                mode="single",
            ),
        ),
        ui.div(
            ui.h4("Output Example"),
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
        ui.div(
            ui.h4("Code"),
            code_sample("""\
                # UI (using same wc from above)
                wc.input_map("region_multi", GEOMETRY, mode="multiple")

                # SERVER
                def server(input):
                    # input.region_multi() returns list[str]
                    ...
                """
            )
        ),
        ui.div(
            ui.h4("Input Map"),
            input_map(
                "region_multi",
                DEMO_GEOMETRY,
                mode="multiple",
            ),
        ),
        ui.div(
            ui.h4("Output Example"),
            ui.help_text("Selected regions:"),
            ui.output_text_verbatim("multi_select", placeholder=True),
        ),
    ),
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
