"""Demo of PARENT-relative aesthetics."""

from shiny import ui, App

from shinymap import aes, input_map, PARENT

from shared import DEMO_GEOMETRY

ui_relative = ui.page_fixed(
    ui.card(
        ui.card_header("Relative Aesthetics with PARENT"),
        ui.p(
            "Demonstrates PARENT-relative aesthetics. "
            "Select state adds 3 to the base stroke width."
        ),
        input_map(
            "base",
            DEMO_GEOMETRY,
            mode="multiple",
            aes=aes.ByState(
                base=aes.Shape(stroke_width=1),
                select=aes.Shape(stroke_width=PARENT.stroke_width + 3),
                hover=aes.Shape(stroke_width=PARENT.stroke_width + 3),
            ),
        ),
    )
)

def server_relative(input):
    pass

app = App(ui_relative, server_relative)
