"""Showcase of clickable output_map."""

from shiny import App, ui, reactive

from shinymap import Map, output_map, render_map
from shinymap.mode import Display

from shared import DEMO_OUTLINE, TOOLTIPS, code_sample


rids = list(DEMO_OUTLINE.regions.keys())

# Default Id -------------------

_ui_default = ui.card(
    ui.card_header("Default Id"),
    ui.input_select(
        "clickable_default_in",
        "Select a Region",
        choices=rids
    ),
    ui.markdown("`mode=Display(clickable=True)` "),
    output_map(
        "clickable_default_out", 
        DEMO_OUTLINE, 
        mode=Display(clickable=True),
        tooltips=TOOLTIPS,
    ),
)

def _server_default(input):

    @render_map
    def clickable_default_out():
        selected = input.clickable_default_in()
        # value > 0 means selected (highlighted)
        return Map(value={selected: 1} if selected else {})
    
    @reactive.effect
    @reactive.event(input.clickable_default_out_click)
    def _():
        clicked_id = input.clickable_default_out_click()
        if clicked_id == input.clickable_default_in():
            msg = f"{clicked_id} is selected."
        else:
            msg = f"{clicked_id} is not selected." 

        m = ui.modal(
            ui.h4(clicked_id),
            ui.p(msg)
        )
        ui.modal_show(m)

# Custom ID ----------------------

_ui_custom_id = ui.card(
    ui.card_header("Custom Id"),
    ui.input_selectize(
        "clickable_custom_in",
        "Select a Region",
        choices=rids,
        multiple=True,
    ),
    ui.markdown("`mode=Display(clickable=True, input_id='clickable_id')` "),
    output_map(
        "clickable_custom_out", 
        DEMO_OUTLINE, 
        mode=Display(clickable=True, input_id="clickable_id"),
        tooltips=TOOLTIPS,
    ),
)

def _server_custom_id(input):

    @render_map
    def clickable_custom_out():
        selected = input.clickable_custom_in()
        val = {k: 1 for k in selected}
        return Map(value=val)
    
    @reactive.effect
    @reactive.event(input.clickable_id)
    def _():
        clicked_id = input.clickable_id()
        if clicked_id in input.clickable_custom_in():
            msg = f"{clicked_id} is selected."
        else:
            msg = f"{clicked_id} is not selected." 

        m = ui.modal(
            ui.h4(clicked_id),
            ui.p(msg)
        )
        ui.modal_show(m)

# Put them together ---------------

ui_output_clickable = ui.page_fixed(
    ui.h2("Clickable Output Maps"),
    ui.p("This demo showcases output maps that emit click event. "),
    code_sample("""\
        from shinymap import output_map
        from shinymap.mode import Display
                
        output_map(..., mode=Display(clickable=True, ...), ...)
    """),    
    ui.layout_column_wrap(
        _ui_default,
        _ui_custom_id,
        width=1/2,
    )
)

def server_output_clickable(input, output, session):

    _server_default(input)
    _server_custom_id(input)


app = App(ui_output_clickable, server_output_clickable)
