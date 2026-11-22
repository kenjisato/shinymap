"""Input map next to a render.ui output, for the initial-value race test.

Clicking right after the page loads must not be undone by the bridge's
retry that sets the initial value (shinyBridge.ts mountInput).
"""

from shiny import App, render, ui

from shinymap import Outline, input_map

outline = Outline.from_dict(
    {
        "a": "M 0 0 L 40 0 L 40 40 L 0 40 Z",
        "b": "M 50 0 L 90 0 L 90 40 L 50 40 Z",
        "_metadata": {"viewBox": "0 0 100 50"},
    }
)

app_ui = ui.page_fluid(
    input_map("pick", outline, mode="single"),
    ui.output_ui("info"),
)


def server(input, output, session):
    @render.ui
    def info():
        picked = input.pick()
        return ui.p(f"picked: {picked}", id="picked")


app = App(app_ui, server)
