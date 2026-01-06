"""Test app that triggers the render_map mode default bug.

This app uses output_map() WITHOUT the outline parameter, which means
mode is not stored in static_params. When render_map tries to call
mode.to_dict() on None, it raises AttributeError.

The fix: _render_map.py defaults mode to Display() when not in static_params.
"""

from shiny import App, ui

from shinymap import Map, Outline, output_map, render_map

outline = Outline.from_dict({
    "region_a": "M 0 0 L 50 0 L 50 50 L 0 50 Z",
})

app_ui = ui.page_fluid(
    # output_map WITHOUT outline - mode is not registered in static_params
    output_map("test_map"),
)


def server(input, output, session):
    @render_map
    def test_map():
        # Outline provided here instead of in output_map
        return Map(outline)


app = App(app_ui, server)
