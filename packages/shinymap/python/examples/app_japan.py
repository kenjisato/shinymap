"""Japanese Prefecture Map Demo

Demonstrates shinymap with Japanese prefecture boundaries.
Shows various interaction modes and data visualization patterns.
"""

import random
from pathlib import Path
from pprint import pformat

from shiny import App, render, ui, reactive

from shinymap import (
    Map,
    aes,
    update_map,
    Wash,
)
from shinymap.mode import Count
from shinymap.outline import Outline
from shinymap.aes.color import SEQUENTIAL_ORANGE

from japan_prefectures import PREF_NAMES_JA, PREF_NAMES_ROMAJI
from shared import code_sample

# Load outline using the Outline class
OUTLINE_PATH = Path(__file__).parent / "data" / "japan_prefectures.json"
OUTLINE = Outline.from_json(OUTLINE_PATH).path_as_line("_divider_lines")

TOOLTIPS = {code: f"{name} ({PREF_NAMES_ROMAJI[code]})" for code, name in PREF_NAMES_JA.items()}

# Create Wash with theme aesthetics
# Note: stroke_width is in viewBox units (viewBox is ~1400x1450)
wc = Wash(
    shape=aes.ByState(
        base=aes.Shape(
            fill_color="#ddd",
            stroke_color="#fff",
            stroke_width=0.3,
        ),
        select=aes.Shape(
            fill_color="darkseagreen",
        ),
        hover=aes.Shape(
            fill_color="#ffff66",
            stroke_color="#d1d5db",
            stroke_width=0.6,
        ),
    ),
    # Line defaults: applied to aes.Path(kind="line", ...) elements
    line=aes.Line(
        stroke_color="#999",
        stroke_width=1.5,
    ),
)

# Example 1: Simple selection (single mode)
_ui_single = ui.card(
    ui.card_header("Single Prefecture Selection"),
    ui.p("Click a prefecture to select it. Useful for drilling down into regional data."),
    ui.layout_columns(
        ui.TagList(
            ui.h4("Code"),
            code_sample(
                """\
                # UI
                input_map(
                    "selected_pref",
                    OUTLINE,
                    tooltips=TOOLTIPS,
                    mode="single",
                )

                # SERVER
                def server(input):
                    ...
                    # input.selected_pref()
                    # => Returns OUTLINE's key: 01, 02, ...
                """
            )
        ),
        ui.TagList(
            ui.h4("Input Map"),
            wc.input_map(
                "selected_pref",
                OUTLINE,
                tooltips=TOOLTIPS,
                mode="single",
            ),
        ),
        ui.TagList(
            ui.h4("Output Example"),
            ui.div(
                ui.help_text("Selected ID"),
                ui.output_text_verbatim("selected_pref_raw", placeholder=True),
            ),
            ui.div(
                ui.help_text("Selected prefecture:"),
                ui.output_text_verbatim("selected_pref_display", placeholder=True),
            )
        ),
    ),
)


def _server_single(input, output, session):
    @render.text
    def selected_pref_raw():
        value = input.selected_pref()
        return  value if value is not None else "None"
    
    @render.text
    def selected_pref_display():
        code = input.selected_pref()
        if code:
            return f"{PREF_NAMES_JA[code]} ({PREF_NAMES_ROMAJI[code]})"
        return "None"


# Example 2: Multiple selection with visualization
_ui_multi = ui.card(
    ui.card_header("Multiple Prefecture Selection"),
    ui.p("Select multiple prefectures to compare. Click again to deselect."),
    ui.layout_columns(
        ui.TagList(
            ui.h4("Code"),
            code_sample(
                """\
                # UI
                input_map(
                    "multi_pref",
                    OUTLINE,
                    tooltips=TOOLTIPS,
                    mode="multiple",
                ),

                # SERVER
                def server(input):
                    ...
                    # input.multi_pref()
                    # => Returns a tuple of OUTLINE's keys
                """
            )
        ),
        ui.TagList(
            ui.h4("Input Map"),
            wc.input_map(
                "multi_pref",
                OUTLINE,
                tooltips=TOOLTIPS,
                mode="multiple"
            ),
        ),
        ui.TagList(
            ui.h4("Output Example"),
            ui.layout_columns(
                ui.div(
                    ui.help_text("Selected IDs:"),
                    ui.output_text_verbatim("multi_pref_raw", placeholder=True),
                ),
                ui.div(
                    ui.help_text("Selected Prefectures:"),
                    ui.output_text_verbatim("multi_pref_display", placeholder=True),
                )
            )
            
        )
    ),
)


def _server_multi(input, output, session):

    @render.text
    def multi_pref_raw():
        return pformat(input.multi_pref(), width=15)
    
    @render.text
    def multi_pref_display():
        pref_names = [PREF_NAMES_JA[p] for p in input.multi_pref()]
        return "\n".join(pref_names)


# Example 3: Count mode with population simulation
_ui_count = ui.card(
    ui.card_header("Visit Counter (Count Mode)"),
    ui.p("Click prefectures to count visits. Color intensity increases with count."),
    ui.layout_columns(
        ui.TagList(
            ui.h4("Code"),
            code_sample("""\
                # UI
                input_map(
                    "visit_counts",
                    OUTLINE,
                    tooltips=TOOLTIPS,
                    mode="count",
                ),

                # SERVER
                def server(input):
                    ...
                    # input.visit_counts()
                    # => Returns dict { id: count } 
            """)
        ),
        ui.TagList(
            ui.h4("Input Map"),
            wc.input_map(
                "visit_counts",
                OUTLINE,
                tooltips=TOOLTIPS,
                mode=Count(aes=aes.Indexed(fill_color=["lightgray", *SEQUENTIAL_ORANGE])),
            ),
        ),
        ui.TagList(
            ui.h4("Output Example"),
            ui.input_action_button("reset_counts", "Reset Counts"),
            ui.layout_columns(
                ui.output_text_verbatim("count_raw"),
                ui.output_text_verbatim("count_by_name", placeholder=True)
            )
        ),
    ),
)


def _server_count(input, output, session):
    
    @render.text
    def count_raw():
        return pformat(input.visit_counts(), width=15)
    
    @render.text
    def count_by_name():
        _counts = input.visit_counts()
        _count_table = [f"{PREF_NAMES_JA[k]}: {v}" for k, v in _counts.items()]
        return "\n".join(_count_table)

    @reactive.effect
    @reactive.event(input.reset_counts)
    def _():
        update_map("visit_counts", value={})


# Example 4: Categorical Mapping

_ui_regions = ui.card(
    ui.card_header("Categorical Mapping"),
    ui.p("Prefectures colored by cateogory."),
    ui.layout_columns(
        ui.TagList(
            ui.h4("Code"),
            code_sample("""\
                # UI
                output_map(
                    "categorical_map",
                    OUTLINE,
                    tooltips=TOOLTIPS,
                ),

                # SERVER
                @render_map
                def categorical_map():
                    # pref_categories() => { '01': 'green', '02': 'red', ... }
                    # COLORS => { 'green': "#84cc16", 'red': "#ef4444", ... }
                    region_aes = {
                        region: aes.Shape(fill_color=COLORS[group])
                        for region, group in pref_categories().items()
                    }
                    return Map(aes=aes.ByGroup(**region_aes))
                """)
        ),
        ui.TagList(
            ui.h4("Input Example"),
            ui.input_action_button("shuffle_value", "Shuffle Values"),
            ui.output_text_verbatim("pref_to_category", placeholder=True)
        ),
        ui.TagList(
            ui.h4("Output Map"),
            wc.output_map(
                "categorical_map",
                OUTLINE,
                tooltips=TOOLTIPS,
            ),
        ),
    ),    
    ui.div(
        
    ),
)


def _server_regions(input, output, session):

    COLORS = {
        "red": "#ef4444",
        "orange": "#f59e0b",
        "green": "#84cc16",
        "blue": "#3b82f6",
        "purple": "#8b5cf6",
    }

    pref_categories = reactive.value()

    @reactive.effect
    @reactive.event(input.shuffle_value)
    def _reset_values():
        _colors = list(COLORS.keys())
        pref_categories.set(
            {k: v for k, v in zip(OUTLINE.regions.keys(), random.choices(_colors, k=47))}
        )

    @render.text
    def pref_to_category():
        return pformat(pref_categories(), width=30)

    @wc.render_map
    def categorical_map():
        # Create per-region aesthetics using ByGroup
        # Static params (geometry, tooltips, etc.) defined in output_map() above
        region_aes = {
            region: aes.Shape(fill_color=COLORS[group])
            for region, group in pref_categories().items()
        }
        return Map(aes=aes.ByGroup(**region_aes))


# Combine all examples
app_ui = ui.page_fluid(
    ui.h2("🗾 Japanese Prefecture Map Demo"),
    ui.p(
        "Interactive demonstrations of shinymap with Japanese prefecture boundaries. "
        "Explore different interaction modes and visualization patterns."
    ),
    _ui_single,
    _ui_multi,
    _ui_count,
    _ui_regions,
    title="Japan Prefecture Map Demo",
)


def server(input, output, session):
    _server_single(input, output, session)
    _server_multi(input, output, session)
    _server_count(input, output, session)
    _server_regions(input, output, session)


app = App(app_ui, server)
