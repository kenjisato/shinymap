"""Comprehensive showcase of all input modes and their variations."""

from shiny import App, render, ui

from shinymap import input_map, output_map, render_map, scale_sequential, Map

from shared import DEMO_GEOMETRY, TOOLTIPS, code_sample


github_url = "https://github.com/kenjisato/shinymap/blob/main/packages/shinymap/python/examples/app_input_modes.py"
_ui_intro = ui.markdown(
f"""
This demo showcases input mode variations beyond basic single/multiple selection.
See [app_input_modes.py]({github_url}) for fundamental single and multiple selection examples.

""")

# Count Mode (Unlimited) --------
_ui_count_unlimited = ui.card(
    ui.card_header("Count Mode - Unlimited"),
    ui.p("Click shapes to increment counters. Keeps counting up indefinitely."),
    ui.layout_columns(
        ui.div(
            ui.h4("Code"),
            code_sample("""\
                # UI
                input_map(
                    "count_unlimited", 
                    DEMO_GEOMETRY, 
                    tooltips=TOOLTIPS, 
                    mode="count"
                )

                # SERVER   
                def server(input):
                    ...
                    # input.count_unlimited() 
                    # => { 'square': 1, 'circle': 2 } etc.
            """)
        ),
        ui.div(
            ui.h4("Input Map"),
            input_map(
                "count_unlimited", 
                DEMO_GEOMETRY, 
                tooltips=TOOLTIPS, 
                mode="count", 
            ),
        
        ),
        ui.div(
            ui.h4("Output Example"),
            ui.help_text("Click counts:"),
            ui.output_text_verbatim("count_unlimited_output", placeholder=True),
        ),
    ),
)


def _server_count_unlimited(input, output, session):
    @render.text
    def count_unlimited_output():
        value = input.count_unlimited() or {}
        counts_str = ", ".join([f"{id}: {count}" for id, count in value.items() if count > 0])
        return counts_str if counts_str else "No clicks yet"


# Count Mode with Hue Cycling --------
_ui_hue_cycle = ui.card(
    ui.card_header("Count Mode - Hue Cycling (cycle=4)"),
    ui.p(
        "Click shapes to cycle through colors: gray → red → yellow → green → gray. "
        "Perfect for color wheel quizzes or categorical cycling!"
    ),
    ui.layout_columns(
        ui.div(
            ui.h4("Code"),
            code_sample("""\
            # UI
            input_map(
                "count_cycle",
                 DEMO_GEOMETRY, 
                 tooltips=TOOLTIPS, 
                 mode="count", 
                 cycle=4
            )

            # SERVER
            def server(input):
                ...
                # input.count_cycle()
                # => { }      
            """)
        ),
        ui.div(
            ui.h4("Input Map"),
            # TODO: Clarify
            #  - How to change palette?
            #  - How to disable empty value? 
            input_map(
                "count_cycle",
                 DEMO_GEOMETRY, 
                 tooltips=TOOLTIPS, 
                 mode="count", 
                 cycle=4, 
            ),
        ),
        ui.div(
            ui.h4("Output Example"),
            ui.help_text("Current colors (0-3):"),
            ui.output_text_verbatim("count_cycle_output", placeholder=True),
        ),
    ),
)


def _server_hue_cycle(input, output, session):
    @render.text
    def count_cycle_output():
        value = input.count_cycle() or {}
        color_names = ["gray", "red", "yellow", "green"]
        counts_str = ", ".join(
            [f"{id}: {color_names[count % 4]}" for id, count in value.items() if count > 0]
        )
        return counts_str if counts_str else "No clicks yet"


# Multiple Selection with Limit --------
_ui_max_selection = ui.card(
    ui.card_header("Multiple Selection with Limit (max_selection=2)"),
    ui.p("Select up to 2 shapes. Further clicks are ignored until you deselect one."),
    ui.layout_columns(
        ui.div(
            ui.h4("Code"),
            code_sample("""\
                # UI
                input_map(
                    "limited", 
                    DEMO_GEOMETRY, 
                    tooltips=TOOLTIPS, 
                    mode="multiple", 
                    max_selection=2
                )

                # SERVER
                def server(input):
                    ...
                    # input.limited()
                    # => ['square', 'circle']      
                """)
        ),
        ui.div(
            ui.h4("Input Map"),
            input_map(
                "limited", 
                DEMO_GEOMETRY, 
                tooltips=TOOLTIPS, 
                mode="multiple", 
                max_selection=2
            ),
        ),
        ui.div(
            ui.h4("Output Example"),
            ui.help_text("Selected (max 2):"),
            ui.output_text_verbatim("limited_output", placeholder=True),
        ),
    ),
)


def _server_max_selection(input, output, session):
    @render.text
    def limited_output():
        selected = input.limited()  # Returns list of strings
        if selected:
            return f"Selected: {', '.join(selected)} ({len(selected)}/2)"
        return "None selected (0/2)"


# Put them together --------------
ui_input_modes = ui.page_fixed(
    ui.h2("Input Modes Demo"),
    _ui_intro,
    _ui_count_unlimited,
    _ui_hue_cycle,
    _ui_max_selection,
    title="Input Modes",
)


def server_input_modes(input, output, session):
    _server_count_unlimited(input, output, session)
    _server_hue_cycle(input, output, session)
    _server_max_selection(input, output, session)


app = App(ui_input_modes, server_input_modes)
