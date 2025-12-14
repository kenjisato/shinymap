from shared import DEMO_GEOMETRY, TOOLTIPS
from shiny import App, ui

from shinymap import MapCount, MapSelection, output_map, render_map


rids = list(DEMO_GEOMETRY.keys())

# Single Select -------------------

_ui_single = ui.card(
    ui.card_header("Single Select"), 
    ui.input_select(
        "single_select_input", 
        "Select a Region", 
        rids
    ),
    output_map("single_select_output"),
)

_ui_multiple = ui.card(
    ui.card_header("Multiple Select"), 
    ui.input_selectize(
        "multiple_select_input", 
        "Select Regions", 
        rids,
        multiple=True,
    ),
    output_map("multiple_select_output"),
)

def ui_input_numeric(rid):
    return ui.input_numeric(rid, rid.capitalize(), 0, min=0, max=10)

_ui_count = ui.card(
    ui.card_header("Alpha"), 
    ui.layout_column_wrap(
        *[ui_input_numeric(rid) for rid in rids],
        width=1/3,
    ),
    output_map("alpha_output"),
)



# Put them together ---------------
ui_output = ui.page_fixed(
    ui.h2("Output Maps"),
    ui.p("This demo showcases output maps."),
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
        return (
            MapSelection(DEMO_GEOMETRY, selected=selected, tooltips=TOOLTIPS)
            .with_fill_color("#e2e8f0")  # Base color for all regions
            .with_fill_color_selected("#fbbf24")  # Highlight selected region
        )

    @render_map
    def multiple_select_output():
        selected = input.multiple_select_input()
        return (
            MapSelection(DEMO_GEOMETRY, selected=selected, tooltips=TOOLTIPS)
            .with_fill_color("#e2e8f0")  # Base color for all regions
            .with_fill_color_selected("#fbbf24")  # Highlight selected regions
        )

    @render_map
    def alpha_output():
        counts = {rid: input[rid]() for rid in rids}
        return MapCount(DEMO_GEOMETRY, counts=counts, tooltips=TOOLTIPS).with_fill_color([
            "#eff6ff", "#bfdbfe", "#60a5fa", "#2563eb", "#1e40af",
            "#1e3a8a", "#172554", "#0f172a", "#020617", "#000000", "#000000"
        ])


app = App(ui_output, server_output)
