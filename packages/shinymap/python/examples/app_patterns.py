"""Advanced patterns: helper functions, qualitative scaling, value transformations."""

from shiny import App, ui

from shinymap import (
    QUALITATIVE,
    Map,
    input_map,
    output_map,
    render_map,
    scale_qualitative,
    scale_sequential,
)

from shared import DEMO_GEOMETRY, SHAPE_COLORS, TOOLTIPS


# Helper functions --------
def selected_ids(counts: dict[str, int] | None) -> list[str]:
    """Return IDs of regions with count > 0."""
    return [id for id, count in (counts or {}).items() if count > 0]


def fills_for_qualitative(counts: dict[str, int] | None) -> dict[str, str]:
    """Active regions get their assigned color; inactive regions are neutral gray."""
    counts = counts or {}
    return scale_qualitative(
        categories={rid: rid if counts.get(rid, 0) > 0 else None for rid in DEMO_GEOMETRY},
        region_ids=list(DEMO_GEOMETRY.keys()),
        palette=[SHAPE_COLORS[rid] for rid in DEMO_GEOMETRY],
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
            hover_highlight={"stroke_width": 1},
        ),
        output_map("qualitative_output"),
    ),
)


def _server_qualitative(input, output, session):
    @render_map
    def qualitative_output():
        # Convert single selection (string | None) to count map for helper functions
        selected = input.region_single()
        counts = {selected: 1} if selected else {}

        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_fill_color(fills_for_qualitative(counts))
            .with_counts(counts)
            .with_active(selected_ids(counts))
            .with_stroke_width(1.5)
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
            mode="count",
            value={},
            hover_highlight={"stroke_width": 2, "fill_opacity": -0.3},
        ),
        output_map("count_output"),
    ),
)


def _server_count_helpers(input, output, session):
    @render_map
    def count_output():
        counts = input.clicks() or {}
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_fill_color(scale_sequential(counts, list(DEMO_GEOMETRY.keys()), max_count=10))
            .with_counts(counts)
        )


# Code Examples --------
_code_examples = ui.card(
    ui.card_header("Pattern: Helper Functions"),
    ui.p("Reusable helper functions for common transformations:"),
    ui.tags.pre(
        ui.tags.code(
            '''def selected_ids(counts: dict[str, int] | None) -> list[str]:
    """Return IDs of regions with count > 0."""
    return [id for id, count in (counts or {}).items() if count > 0]

def fills_for_qualitative(counts: dict[str, int] | None) -> dict[str, str]:
    """Active regions get their assigned color; inactive regions are neutral gray."""
    counts = counts or {}
    return scale_qualitative(
        categories={rid: rid if counts.get(rid, 0) > 0 else None for rid in DEMO_GEOMETRY},
        region_ids=list(DEMO_GEOMETRY.keys()),
        palette=[SHAPE_COLORS[rid] for rid in DEMO_GEOMETRY],
    )

@render_map
def qualitative_output():
    # Convert single selection to count map for reusability
    selected = input.region_single()
    counts = {selected: 1} if selected else {}

    return (
        Map(DEMO_GEOMETRY)
        .with_fill_color(fills_for_qualitative(counts))
        .with_active(selected_ids(counts))
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
