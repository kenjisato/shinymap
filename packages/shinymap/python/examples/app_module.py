"""Test Shiny module namespacing for input_map and output_map.

This example verifies that both input_map and output_map work correctly
when used inside Shiny modules (@module.ui / @module.server).

Related: GitHub issues #9 (input_map), #10 (output_map)
"""

from shiny import App, module, reactive, ui, render

from shinymap import Map, input_map, output_map, render_map
from shinymap.mode import Display, Single

from shared import DEMO_OUTLINE, TOOLTIPS


# Module with input_map (tests fix from #9)
@module.ui
def input_map_module_ui():
    return ui.card(
        ui.card_header("input_map (module)"),
        ui.p("Click to select a region."),
        input_map(
            "map",
            DEMO_OUTLINE,
            mode=Single(),
            tooltips=TOOLTIPS,
        ),
        ui.output_text_verbatim("selection_info"),
    )


@module.server
def input_map_module_server(input, output, session):
    @output
    @render.text
    def selection_info():
        val = input.map()
        if not val:
            return "No selection"
        #selected = [k for k, v in val.items() if v > 0]
        if val:
            return f"Selected: {val}"
        return "No selection"


# Module with output_map clickable (tests fix from #10)
@module.ui
def output_map_module_ui():
    return ui.card(
        ui.card_header("output_map clickable (module)"),
        ui.p("Click on a region to see if the click event is received."),
        output_map(
            "map",
            DEMO_OUTLINE,
            mode=Display(clickable=True),
            tooltips=TOOLTIPS,
        ),
        ui.output_text_verbatim("click_info"),
    )


@module.server
def output_map_module_server(input, output, session):
    click_count = reactive.value(0)
    last_clicked = reactive.value(None)

    @render_map
    def map():
        clicked = last_clicked()
        return Map(value={clicked: 1} if clicked else {})

    @reactive.effect
    @reactive.event(input.map_click)
    def _handle_click():
        clicked_id = input.map_click()
        click_count.set(click_count() + 1)
        last_clicked.set(clicked_id)

    @output
    @render.text
    def click_info():
        count = click_count()
        clicked = last_clicked()
        if count == 0:
            return "No clicks yet. Click on a region!"
        return f"Click #{count}: {clicked}"


# Main app UI with both module types
app_ui = ui.page_fixed(
    ui.h2("Shiny Module Namespacing Test"),
    ui.p(
        "This example tests that input_map and output_map work correctly "
        "when used inside Shiny modules. Each module instance should "
        "receive its own events independently."
    ),
    ui.layout_column_wrap(
        input_map_module_ui("input_mod"),
        input_map_module_ui("input_mod2"),
        output_map_module_ui("output_mod"),
        output_map_module_ui("output_mod2"),
        width=1 / 2,
    ),
)


def server(input, output, session):
    input_map_module_server("input_mod")
    input_map_module_server("input_mod2")
    output_map_module_server("output_mod")
    output_map_module_server("output_mod2")

app = App(app_ui, server)
