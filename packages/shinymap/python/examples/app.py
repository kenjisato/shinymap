from shiny import App, ui, render, reactive, Session

from shinymap import Map, input_map, output_map, render_map
from shinymap.aes.color import QUALITATIVE, scale_qualitative
from shiny_querynav import querynav

from shared import DEMO_OUTLINE, TOOLTIPS, SHAPE_COLORS
from app_basic import ui_basic, server_basic
from app_hover import ui_hover, server_hover
from app_input_modes import ui_input_modes, server_input_modes
from app_output import ui_output, server_output
from app_patterns import ui_patterns, server_patterns
from app_active_vs_selected import ui_active_vs_selected, server_active_vs_selected

def app_ui(request):
    _ui = ui.page_fluid(
        querynav.dependency(),
        ui.h1("ShinyMap"),
        ui.navset_pill_list(
            ui.nav_panel("Basic Inputs", ui_basic, value="basic"),
            ui.nav_panel("Input Modes", ui_input_modes, value="input_modes"),
            ui.nav_panel("Hover Effects", ui_hover, value="hover"),
            ui.nav_panel("Output Maps", ui_output, value="output"),
            ui.nav_panel("Advanced Patterns", ui_patterns, value="patterns"),
            ui.nav_panel("Active vs Selected", ui_active_vs_selected, value="active"),

            well=False,
            widths=(2, 10),
            id="page"
        ),
    )
    return _ui

def server(input, output, session: Session):
    querynav.sync("page", home_value="basic")

    server_basic(input, output, session)
    server_input_modes(input, output, session)
    server_hover(input, output, session)
    server_output(input, output, session)
    server_patterns(input, output, session)
    server_active_vs_selected(input, output, session)

app = App(app_ui, server)
