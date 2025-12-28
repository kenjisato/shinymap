"""Demonstrates the difference between active (highlight) and user selection.

Key distinction:
- active: For programmatic highlighting based on computed logic
- User selection: Tracked via input_map → server, visualized with aes.select
"""

from shiny import App, render, ui

from shinymap import Map, input_map, output_map, render_map
from shinymap.aes.color import scale_sequential
from shinymap.mode import Count

from shared import DEMO_OUTLINE, TOOLTIPS


# Example 1: User selection tracking
_ui_user_selection = ui.card(
    ui.card_header("User Selection Tracking"),
    ui.p(
        "User selection from input_map is displayed in the output map. "
        "The 'active' parameter highlights the selected regions."
    ),
    ui.layout_columns(
        input_map("user_selected", DEMO_OUTLINE, tooltips=TOOLTIPS, mode="multiple"),
        output_map("user_selection_display", DEMO_OUTLINE, tooltips=TOOLTIPS),
    ),
    ui.output_text_verbatim("user_selection_text"),
)


def _server_user_selection(input, output, session):

    @render_map
    def user_selection_display():
        # Display user's selection with active highlighting
        selected = input.user_selected() or []
        return Map(active=list(selected))

    @render.text
    def user_selection_text():
        selected = input.user_selected()
        if selected:
            return f"User selected: {', '.join(selected)}"
        return "No regions selected by user"


# Example 2: Programmatic highlighting with computed styling
_ui_programmatic = ui.card(
    ui.card_header("Programmatic Highlighting with Computed Styling"),
    ui.p(
        "Highlight regions based on computed logic, not user selection. "
        "Here, we use thicker borders for regions with counts above a threshold."
    ),
    ui.layout_columns(
        input_map("region_counts", DEMO_OUTLINE, tooltips=TOOLTIPS, mode=Count(), value={}),
        output_map("programmatic_display", DEMO_OUTLINE, tooltips=TOOLTIPS),
    ),
    ui.output_text_verbatim("programmatic_text"),
)


def _server_programmatic(input, output, session):
    @render_map
    def programmatic_display():
        counts = input.region_counts() or {}

        # Compute which regions to highlight (count >= 3)
        high_value_regions = set(rid for rid, count in counts.items() if count >= 3)

        # Use sequential color scale
        fills = scale_sequential(counts, list(DEMO_OUTLINE.regions.keys()), max_count=10)

        # Create stroke width dict: thicker for high-value regions
        stroke_widths = {rid: 4.0 if rid in high_value_regions else 1.0
                        for rid in DEMO_OUTLINE.regions.keys()}

        return Map(
            value=counts,
            aes={"base": {"fillColor": fills, "strokeWidth": stroke_widths}}
        )

    @render.text
    def programmatic_text():
        counts = input.region_counts() or {}
        high_value = [rid for rid, count in counts.items() if count >= 3]
        if high_value:
            return f"Regions with count >= 3 (highlighted): {', '.join(high_value)}"
        return "No regions have count >= 3 yet"


# Example 3: Combined - User selection + Programmatic highlighting
_ui_combined = ui.card(
    ui.card_header("Combined: User Selection + Computed Highlighting"),
    ui.p(
        "User selection for primary highlight, with computed styling "
        "for regions that are 'neighbors' of selected regions (simulated)."
    ),
    ui.layout_columns(
        input_map("combined_selected", DEMO_OUTLINE, tooltips=TOOLTIPS, mode="single"),
        output_map("combined_display", DEMO_OUTLINE, tooltips=TOOLTIPS),
    ),
    ui.output_text_verbatim("combined_text"),
)


# Simulated neighbor relationships
NEIGHBORS = {
    "circle": ["square", "triangle"],
    "square": ["circle"],
    "triangle": ["circle"],
}


def _server_combined(input, output, session):
    @render_map
    def combined_display():
        selected = input.combined_selected()

        # Compute neighbors of selected region
        neighbors = NEIGHBORS.get(selected, []) if selected else []

        # Build fill color dict: neighbors get light blue, selected gets blue
        fill_colors = {}
        for rid in DEMO_OUTLINE.regions.keys():
            if rid == selected:
                fill_colors[rid] = "#3b82f6"  # Selected: blue
            elif rid in neighbors:
                fill_colors[rid] = "#93c5fd"  # Neighbors: light blue
            else:
                fill_colors[rid] = "#e2e8f0"  # Base: gray

        return Map(
            active=[selected] if selected else [],
            aes={"base": {"fillColor": fill_colors}}
        )

    @render.text
    def combined_text():
        selected = input.combined_selected()
        if selected:
            neighbors = NEIGHBORS.get(selected, [])
            return f"Selected: {selected}\nNeighbors (highlighted): {', '.join(neighbors) if neighbors else 'none'}"
        return "Select a region to see its neighbors highlighted"


# Put it all together
ui_active_vs_selected = ui.page_fluid(
    ui.h2("User Selection vs Programmatic Highlighting"),
    ui.markdown("""
**Key Distinction:**

- **`Map(active=[...])`**: Use to **highlight regions** based on computed logic or user selection.

- **Programmatic styling**: Use `aes={"base": {"fillColor": {...}, "strokeWidth": {...}}}`
  to apply **computed styles** based on data, thresholds, or relationships.

**When to use each:**
- User clicks -> show their selection? -> `Map(active=input.my_map())`
- Computing which regions to highlight based on data/logic? -> Use conditional styling with dicts
    """),
    _ui_user_selection,
    _ui_programmatic,
    _ui_combined,
    title="Active vs Selected",
)


def server_active_vs_selected(input, output, session):
    _server_user_selection(input, output, session)
    _server_programmatic(input, output, session)
    _server_combined(input, output, session)


app = App(ui_active_vs_selected, server_active_vs_selected)
