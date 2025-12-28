"""Advanced patterns: helper functions, qualitative scaling, value transformations."""

from shiny import App, ui

from shinymap import Map, aes, input_map, output_map, render_map
from shinymap.color import scale_qualitative, scale_sequential
from shinymap.mode import Count

from shared import DEMO_GEOMETRY, SHAPE_COLORS, TOOLTIPS


# Helper functions --------
def selected_ids(counts: dict[str, int] | None) -> list[str]:
    """Return IDs of regions with count > 0."""
    return [id for id, count in (counts or {}).items() if count > 0]


def fills_for_qualitative(counts: dict[str, int] | None) -> dict[str, str]:
    """Active regions get their assigned color; inactive regions are neutral gray."""
    counts = counts or {}
    return scale_qualitative(
        categories={rid: rid if counts.get(rid, 0) > 0 else None for rid in DEMO_GEOMETRY.regions},
        region_ids=list(DEMO_GEOMETRY.regions.keys()),
        palette=[SHAPE_COLORS[rid] for rid in DEMO_GEOMETRY.regions],
    )


# Single Selection with Qualitative Colors --------
_ui_qualitative = ui.card(
    ui.card_header("Qualitative Scaling with Custom Palette"),
    ui.p(
        "Click to select a shape. Selected region gets its assigned color from QUALITATIVE palette, "
        "others remain gray. Demonstrates scale_qualitative with custom palette."
    ),
    ui.layout_columns(
        input_map(
            "region_single",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode="single",
            value={},
            aes=aes.ByState(hover=aes.Shape(stroke_width=1)),
        ),
        output_map("qualitative_output", DEMO_GEOMETRY, tooltips=TOOLTIPS),
    ),
)


def _server_qualitative(input, output, session):
    @render_map
    def qualitative_output():
        # Convert single selection (string | None) to count map for helper functions
        selected = input.region_single()
        counts = {selected: 1} if selected else {}
        fills = fills_for_qualitative(counts)

        return Map(
            value=counts,
            active=selected_ids(counts),
            aes={"base": {"fillColor": fills, "strokeWidth": 1.5}}
        )


# Count Mode with Helper Functions --------
_ui_count_helpers = ui.card(
    ui.card_header("Count Mode with Helper Functions"),
    ui.p(
        "Click to increment counts. Demonstrates using helper functions "
        "(selected_ids, scale_sequential) for common transformations."
    ),
    ui.layout_columns(
        input_map(
            "clicks",
            DEMO_GEOMETRY,
            tooltips=TOOLTIPS,
            mode=Count(),
            value={},
            aes=aes.ByState(hover=aes.Shape(stroke_width=2)),
        ),
        output_map("count_output", DEMO_GEOMETRY, tooltips=TOOLTIPS),
    ),
)


def _server_count_helpers(input, output, session):
    @render_map
    def count_output():
        counts = input.clicks() or {}
        fills = scale_sequential(counts, list(DEMO_GEOMETRY.regions.keys()), max_count=10)
        return Map(
            value=counts,
            aes={"base": {"fillColor": fills}}
        )


# Code Examples --------
_code_examples = ui.card(
    ui.card_header("Pattern: Helper Functions"),
    ui.p("Reusable helper functions for common transformations:"),
    ui.tags.pre(
        ui.tags.code(
            '''from shinymap.color import scale_qualitative

def selected_ids(counts: dict[str, int] | None) -> list[str]:
    """Return IDs of regions with count > 0."""
    return [id for id, count in (counts or {}).items() if count > 0]

def fills_for_qualitative(counts: dict[str, int] | None) -> dict[str, str]:
    """Active regions get their assigned color; inactive regions are neutral gray."""
    counts = counts or {}
    return scale_qualitative(
        categories={rid: rid if counts.get(rid, 0) > 0 else None for rid in DEMO_GEOMETRY.regions},
        region_ids=list(DEMO_GEOMETRY.regions.keys()),
        palette=[SHAPE_COLORS[rid] for rid in DEMO_GEOMETRY.regions],
    )

@render_map
def qualitative_output():
    selected = input.region_single()
    counts = {selected: 1} if selected else {}
    fills = fills_for_qualitative(counts)

    return Map(
        value=counts,
        active=selected_ids(counts),
        aes={"base": {"fillColor": fills}}
    )'''
        )
    ),
)


# Put them together --------------
ui_patterns = ui.page_fixed(
    ui.h2("Advanced Patterns Demo"),
    ui.p(
        "This demo showcases advanced patterns for working with shinymap: "
        "helper functions, qualitative scaling with custom palettes, and value transformations."
    ),
    _ui_qualitative,
    _ui_count_helpers,
    _code_examples,
    title="Advanced Patterns",
)


def server_patterns(input, output, session):
    _server_qualitative(input, output, session)
    _server_count_helpers(input, output, session)


app = App(ui_patterns, server_patterns)
