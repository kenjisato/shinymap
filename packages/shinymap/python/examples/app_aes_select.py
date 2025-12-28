"""Test aes parameter with ByState for full aesthetic control."""

from shiny import App, ui, render

from shinymap import aes, input_map

from shared import DEMO_GEOMETRY, TOOLTIPS


app_ui = ui.page_fixed(
    ui.h1("Testing aes.ByState Parameter"),
    ui.p("Select regions to see custom aesthetic for selected state"),
    ui.card(
        ui.card_header("Input Map with aes.ByState"),
        ui.layout_columns(
            input_map(
                "test_selected",
                DEMO_GEOMETRY,
                tooltips=TOOLTIPS,
                mode="multiple",
                aes=aes.ByState(
                    # Base aesthetic (baseline)
                    base=aes.Shape(
                        fill_color="#e2e8f0",
                        stroke_color="#94a3b8",
                        stroke_width=1,
                        fill_opacity=0.8,
                    ),
                    # Hover aesthetic
                    hover=aes.Shape(
                        stroke_width=3,
                        stroke_color="#0284c7",
                    ),
                    # Selected aesthetic
                    select=aes.Shape(
                        fill_color="#fbbf24",
                        stroke_color="#f59e0b",
                        stroke_width=2,
                        fill_opacity=1.0,
                    ),
                ),
            ),
            ui.div(
                ui.help_text("Selected regions:"),
                ui.output_text_verbatim("selected_output", placeholder=True),
            ),
        ),
    ),
    title="Test aes.ByState",
)


def server(input, output, session):
    @render.text
    def selected_output():
        return str(input.test_selected())


app = App(app_ui, server)
