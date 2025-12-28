"""Comprehensive showcase of all input modes and their variations."""

from shiny import App, render, ui

from shinymap import aes, input_map
from shinymap.mode import Count, Cycle, Multiple

from shared import DEMO_OUTLINE, TOOLTIPS, code_sample

# Traffic light colors for 4-state cycle
CYCLE_COLORS = ["#e2e8f0", "#fecaca", "#fef08a", "#bbf7d0"]  # gray, red, yellow, green


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
                from shinymap.mode import Count

                # UI
                input_map(
                    "count_unlimited",
                    DEMO_OUTLINE,
                    tooltips=TOOLTIPS,
                    mode=Count()
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
                DEMO_OUTLINE,
                tooltips=TOOLTIPS,
                mode=Count(aes=aes.Indexed(fill_color=CYCLE_COLORS)),
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


# Cycle Mode (Finite States) --------
_ui_hue_cycle = ui.card(
    ui.card_header("Cycle Mode (n=4)"),
    ui.p(
        "Click shapes to cycle through states: 0 → 1 → 2 → 3 → 0. "
        "Perfect for surveys or categorical selection!"
    ),
    ui.layout_columns(
        ui.div(
            ui.h4("Code"),
            code_sample("""\
            from shinymap.mode import Cycle

            # UI
            input_map(
                "count_cycle",
                DEMO_OUTLINE,
                tooltips=TOOLTIPS,
                mode=Cycle(n=4)
            )

            # SERVER
            def server(input):
                ...
                # input.count_cycle()
                # => { 'circle': 2 } (state 2)
            """)
        ),
        ui.div(
            ui.h4("Input Map"),
            input_map(
                "count_cycle",
                DEMO_OUTLINE,
                tooltips=TOOLTIPS,
                mode=Cycle(n=4, aes=aes.Indexed(fill_color=CYCLE_COLORS)),
            ),
        ),
        ui.div(
            ui.h4("Output Example"),
            ui.help_text("Current states (0-3):"),
            ui.output_text_verbatim("count_cycle_output", placeholder=True),
        ),
    ),
)


def _server_hue_cycle(input, output, session):
    @render.text
    def count_cycle_output():
        value = input.count_cycle() or {}
        state_names = ["state 0", "state 1", "state 2", "state 3"]
        counts_str = ", ".join(
            [f"{id}: {state_names[val]}" for id, val in value.items() if val > 0]
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
                from shinymap.mode import Multiple

                # UI
                input_map(
                    "limited",
                    DEMO_OUTLINE,
                    tooltips=TOOLTIPS,
                    mode=Multiple(max_selection=2)
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
                DEMO_OUTLINE,
                tooltips=TOOLTIPS,
                mode=Multiple(max_selection=2),
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
