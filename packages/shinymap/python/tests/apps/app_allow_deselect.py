"""Single(allow_deselect=False): clicking the selected region keeps it selected (#27)."""

from shiny import App, render, ui

from shinymap import Outline, input_map
from shinymap.mode import Single

OUTLINE = Outline.from_dict(
    {
        "a": "M 0 0 L 40 0 L 40 40 L 0 40 Z",
        "b": "M 50 0 L 90 0 L 90 40 L 50 40 Z",
        "_metadata": {"viewBox": "0 0 100 50"},
    }
)

app_ui = ui.page_fluid(
    input_map("keep", OUTLINE, mode=Single(allow_deselect=False)),
    input_map("free", OUTLINE, mode=Single()),
    ui.output_text("values"),
)


def server(input, output, session):
    @render.text
    def values():
        return f"keep={input.keep()} free={input.free()}"


app = App(app_ui, server)
