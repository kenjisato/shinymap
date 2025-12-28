"""Showcase of output_map with dynamic data from server."""

from shared import DEMO_OUTLINE, TOOLTIPS
from shiny import App, ui

from shinymap import Map, output_map, render_map
from shinymap.aes.color import scale_sequential, SEQUENTIAL_BLUE


rids = list(DEMO_OUTLINE.regions.keys())

# Single Select -------------------

_ui_single = ui.card(
    ui.card_header("Single Select"),
    ui.input_select(
        "single_select_input",
        "Select a Region",
        rids
    ),
    output_map("single_select_output", DEMO_OUTLINE, tooltips=TOOLTIPS),
)

_ui_multiple = ui.card(
    ui.card_header("Multiple Select"),
    ui.input_selectize(
        "multiple_select_input",
        "Select Regions",
        rids,
        multiple=True,
    ),
    output_map("multiple_select_output", DEMO_OUTLINE, tooltips=TOOLTIPS),
)

def ui_input_numeric(rid):
    return ui.input_numeric(rid, rid.capitalize(), 0, min=0, max=10)

_ui_count = ui.card(
    ui.card_header("Value-based Coloring"),
    ui.layout_column_wrap(
        *[ui_input_numeric(rid) for rid in rids],
        width=1/3,
    ),
    output_map("alpha_output", DEMO_OUTLINE, tooltips=TOOLTIPS),
)



# Put them together ---------------
ui_output = ui.page_fixed(
    ui.h2("Output Maps"),
    ui.p("This demo showcases output maps with dynamic data."),
    ui.layout_column_wrap(
        _ui_single,
        _ui_multiple,
        _ui_count,
        width=1/2,
    )
)

def server_output(input, output, session):
    @render_map
    def single_select_output():
        selected = input.single_select_input()
        return Map(active=[selected] if selected else [])

    @render_map
    def multiple_select_output():
        selected = input.multiple_select_input() or []
        return Map(active=list(selected))

    @render_map
    def alpha_output():
        counts = {rid: input[rid]() or 0 for rid in rids}
        # Use scale_sequential to generate fill colors based on counts
        fills = scale_sequential(counts, rids, palette=SEQUENTIAL_BLUE, max_count=10)
        return Map(value=counts, aes={"base": {"fill_color": fills}})


app = App(ui_output, server_output)
