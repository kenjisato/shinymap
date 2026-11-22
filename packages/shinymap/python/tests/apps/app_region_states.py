"""Per-region select and hover looks (region entry beats __all), for input and output maps."""

from shiny import App, ui

from shinymap import Map, aes, input_map, output_map, render_map
from shinymap.outline import Outline

OUTLINE = Outline.from_dict(
    {
        "a": "M0 0 L40 0 L40 40 L0 40 Z",
        "b": "M50 0 L90 0 L90 40 L50 40 Z",
        "_metadata": {"viewBox": "0 0 100 50"},
    }
)
A = aes.ByGroup(
    a=aes.ByState(
        base=aes.Shape(fill_color="#ffff00"),
        select=aes.Shape(fill_color="#ff0000"),
        hover=aes.Shape(stroke_color="#00aa00", stroke_width=5),
    ),
    b=aes.ByState(hover=None),
)

app_ui = ui.page_fluid(
    ui.div(input_map("i", OUTLINE, mode="multiple", aes=A, value={"a": 1}), style="width:400px"),
    ui.div(output_map("o", OUTLINE, aes=A), style="width:400px"),
)


def server(input, output, session):
    @render_map
    def o():
        return Map(value={"a": 1})


app = App(app_ui, server)
