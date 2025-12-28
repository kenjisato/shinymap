"""Test update_map() function for partial updates."""

from shiny import App, ui, reactive, render

from shinymap import aes, input_map, update_map
from shinymap.color import QUALITATIVE

from shared import DEMO_GEOMETRY, TOOLTIPS


app_ui = ui.page_fixed(
    ui.h1("Testing update_map() Function"),
    ui.p("Click buttons to update map aesthetics without re-rendering"),
    ui.card(
        ui.card_header("Dynamic Updates"),
        ui.layout_columns(
            input_map(
                "test_update",
                DEMO_GEOMETRY,
                tooltips=TOOLTIPS,
                mode="multiple",
                aes=aes.ByState(
                    base=aes.Shape(
                        fill_color="#e2e8f0",
                        stroke_color="#94a3b8",
                        stroke_width=1,
                    )
                ),
            ),
            ui.div(
                ui.h4("Update Controls"),
                ui.input_action_button("update_colors", "Update Fill Colors", class_="btn-primary"),
                ui.input_action_button("update_selected", "Update Selected Aesthetic", class_="btn-success"),
                ui.input_action_button("update_stroke", "Update Stroke Width", class_="btn-warning"),
                ui.input_action_button("clear_selection", "Clear Selection", class_="btn-warning"),
                ui.input_action_button("reset", "Reset All", class_="btn-secondary"),
                ui.hr(),
                ui.help_text("Selected regions:"),
                ui.output_text_verbatim("selected_output", placeholder=True),
            ),
        ),
    ),
    title="Test update_map()",
)


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.update_colors)
    def _():
        # Update fill colors for each region
        update_map(
            "test_update",
            fill_color={
                "circle": QUALITATIVE[0],
                "square": QUALITATIVE[1],
                "triangle": QUALITATIVE[2],
            },
        )

    @reactive.effect
    @reactive.event(input.update_selected)
    def _():
        # Update selected aesthetic
        update_map(
            "test_update",
            aes_select={
                "fill_color": "#fbbf24",
                "stroke_color": "#f59e0b",
                "stroke_width": 3,
                "fill_opacity": 1.0,
            },
        )

    @reactive.effect
    @reactive.event(input.update_stroke)
    def _():
        # Update stroke width for all regions
        update_map(
            "test_update",
            stroke_width={"circle": 3.0, "square": 2.0, "triangle": 1.0},
        )

    @reactive.effect
    @reactive.event(input.clear_selection)
    def _():
        # Clear all selections (common "Reset" pattern for input_map)
        update_map("test_update", value={})

    @reactive.effect
    @reactive.event(input.reset)
    def _():
        # Reset aesthetics and selection to default
        update_map(
            "test_update",
            fill_color="#e2e8f0",
            stroke_width=1,
            value={},
            aes_select={
                "fill_color": "#cbd5e1",
                "stroke_width": 1,
            },
        )

    @output
    @render.text
    def selected_output():
        return str(input.test_update())


app = App(app_ui, server)
