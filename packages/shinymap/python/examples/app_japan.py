"""Japanese Prefecture Map Demo

Demonstrates shinymap with Japanese prefecture boundaries.
Shows various interaction modes and data visualization patterns.
"""

from pathlib import Path
from shiny import App, render, ui, reactive

from shinymap import (
    Map,
    MapSelection,
    MapCount,
    input_map,
    output_map,
    render_map,
    scale_sequential,
    scale_qualitative,
    SEQUENTIAL_BLUE,
    QUALITATIVE,
)
from shinymap.geometry import load_geometry

from japan_prefectures import PREF_NAMES_JA, PREF_NAMES_ROMAJI

# Load geometry using the geometry package
GEOMETRY_PATH = Path(__file__).parent / "data" / "japan_prefectures.json"
GEOMETRY, DIVIDERS, VIEWBOX = load_geometry(
    GEOMETRY_PATH,
    overlay_keys=["_divider_lines"]
)

TOOLTIPS = {code: f"{name} ({PREF_NAMES_ROMAJI[code]})" for code, name in PREF_NAMES_JA.items()}

# Divider styling (no fill, gray stroke)
DIVIDER_STYLE = {"fillColor": "none", "strokeColor": "#999999", "strokeWidth": 2.0}


# Example 1: Simple selection (single mode)
_ui_single = ui.card(
    ui.card_header("Single Prefecture Selection"),
    ui.p("Click a prefecture to select it. Useful for drilling down into regional data."),
    ui.layout_columns(
        input_map(
            "selected_pref",
            GEOMETRY,
            tooltips=TOOLTIPS,
            mode="single",
            view_box=VIEWBOX,
            default_aesthetic={"fillColor": "#e5e7eb", "strokeColor": "#d1d5db", "strokeWidth": 1},
            hover_highlight={"stroke_color": "#374151", "stroke_width": 2},
        ),
        ui.div(
            ui.help_text("Selected prefecture:"),
            ui.output_text_verbatim("selected_pref_display", placeholder=True),
        ),
    ),
)


def _server_single(input, output, session):
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
        input_map(
            "multi_pref",
            GEOMETRY,
            tooltips=TOOLTIPS,
            mode="multiple",
            view_box=VIEWBOX,
            default_aesthetic={"fillColor": "#e5e7eb", "strokeColor": "#d1d5db", "strokeWidth": 1},
            hover_highlight={"stroke_color": "#374151", "stroke_width": 2},
        ),
        output_map(
            "multi_visual",
            geometry=GEOMETRY,
            tooltips=TOOLTIPS,
            view_box=VIEWBOX,
            overlay_geometry=DIVIDERS,
            overlay_aesthetic=DIVIDER_STYLE,
        ),
    ),
    ui.output_text_verbatim("multi_pref_display"),
)


def _server_multi(input, output, session):
    @render_map
    def multi_visual():
        selected = input.multi_pref()
        # Static params (geometry, tooltips, etc.) defined in output_map() above
        return (
            MapSelection(selected=selected)
            .with_fill_color("#e5e7eb")
            .with_fill_color_selected({"fillColor": "#3b82f6", "strokeColor": "#1e40af", "strokeWidth": 2})
            .with_stroke_color("transparent")
        )

    @render.text
    def multi_pref_display():
        selected = input.multi_pref()
        if selected:
            names = [f"{PREF_NAMES_JA[code]} ({PREF_NAMES_ROMAJI[code]})" for code in selected]
            return f"Selected {len(selected)} prefectures:\n" + "\n".join(f"  • {name}" for name in names)
        return "No prefectures selected"


# Example 3: Count mode with population simulation
_ui_count = ui.card(
    ui.card_header("Visit Counter (Count Mode)"),
    ui.p("Click prefectures to count visits. Color intensity increases with count."),
    ui.layout_columns(
        input_map(
            "visit_counts",
            GEOMETRY,
            tooltips=TOOLTIPS,
            mode="count",
            value={},
            view_box=VIEWBOX,
            default_aesthetic={"fillColor": "#e5e7eb", "strokeColor": "#d1d5db", "strokeWidth": 1},
            hover_highlight={"stroke_color": "#374151", "stroke_width": 2},
            overlay_geometry=DIVIDERS,
            overlay_aesthetic=DIVIDER_STYLE,
        ),
        output_map(
            "visit_visual",
            geometry=GEOMETRY,
            tooltips=TOOLTIPS,
            view_box=VIEWBOX,
            overlay_geometry=DIVIDERS,
            overlay_aesthetic=DIVIDER_STYLE,
        ),
    ),
    ui.div(
        ui.input_action_button("reset_counts", "Reset Counts"),
        ui.output_text_verbatim("visit_summary"),
    ),
)


def _server_count(input, output, session):
    @render_map
    def visit_visual():
        counts = input.visit_counts() or {}

        # Use sequential color scale for prefectures (or default gray if no counts)
        if counts:
            fills = scale_sequential(counts, list(GEOMETRY.keys()), palette=SEQUENTIAL_BLUE, max_count=10)
        else:
            fills = "#e5e7eb"

        # Static params (geometry, tooltips, etc.) defined in output_map() above
        return (
            Map()
            .with_fill_color(fills)
            .with_counts(counts)
            .with_stroke_color("transparent")
        )

    @render.text
    def visit_summary():
        counts = input.visit_counts() or {}
        if not counts:
            return "No visits yet. Click prefectures to start counting!"

        total = sum(counts.values())
        visited = len(counts)
        top_3 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]

        summary = f"Total visits: {total}\n"
        summary += f"Prefectures visited: {visited}/47\n\n"
        summary += "Top 3 most visited:\n"
        for code, count in top_3:
            summary += f"  {count}× {PREF_NAMES_JA[code]}\n"

        return summary

    @reactive.effect
    @reactive.event(input.reset_counts)
    def _():
        # Reset by sending empty dict - this updates the input value
        pass  # In real app, would use update function


# Example 4: Regional grouping
REGIONS = {
    "Hokkaido": ["01"],
    "Tohoku": ["02", "03", "04", "05", "06", "07"],
    "Kanto": ["08", "09", "10", "11", "12", "13", "14"],
    "Chubu": ["15", "16", "17", "18", "19", "20", "21", "22", "23"],
    "Kansai": ["24", "25", "26", "27", "28", "29", "30"],
    "Chugoku": ["31", "32", "33", "34", "35"],
    "Shikoku": ["36", "37", "38", "39"],
    "Kyushu": ["40", "41", "42", "43", "44", "45", "46", "47"],
}

REGION_COLORS = {
    "Hokkaido": "#ef4444",
    "Tohoku": "#f97316",
    "Kanto": "#f59e0b",
    "Chubu": "#84cc16",
    "Kansai": "#06b6d4",
    "Chugoku": "#3b82f6",
    "Shikoku": "#8b5cf6",
    "Kyushu": "#ec4899",
}

_ui_regions = ui.card(
    ui.card_header("Regional Grouping"),
    ui.p("Prefectures colored by traditional geographic regions of Japan."),
    output_map(
        "regions_map",
        geometry=GEOMETRY,
        tooltips=TOOLTIPS,
        view_box=VIEWBOX,
        overlay_geometry=DIVIDERS,
        overlay_aesthetic=DIVIDER_STYLE,
    ),
    ui.div(
        ui.help_text("Regions:"),
        ui.HTML(
            "<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin-top: 0.5rem;'>"
            + "".join(
                f"<div style='display: flex; align-items: center; gap: 0.5rem;'>"
                f"<div style='width: 1rem; height: 1rem; background-color: {color}; border-radius: 0.125rem;'></div>"
                f"<span style='font-size: 0.875rem;'>{region}</span>"
                f"</div>"
                for region, color in REGION_COLORS.items()
            )
            + "</div>"
        ),
    ),
)


def _server_regions(input, output, session):
    @render_map
    def regions_map():
        # Create color mapping for all prefectures
        fills = {}
        fill_opacities = {}

        for region, prefs in REGIONS.items():
            color = REGION_COLORS[region]
            for pref in prefs:
                fills[pref] = color
                fill_opacities[pref] = 0.8

        # Static params (geometry, tooltips, etc.) defined in output_map() above
        return (
            Map()
            .with_fill_color(fills)
            .with_stroke_color("#ffffff")
            .with_stroke_width(1.0)
            .with_fill_opacity(fill_opacities)
        )


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
