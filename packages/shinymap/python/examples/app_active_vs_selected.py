"""Demonstrates the difference between with_active() and MapSelection's selected parameter.

Key distinction:
- MapSelection(selected=...) - For tracking user selection state (input_map → server)
- Map().with_active(...) - For programmatic highlighting based on computed logic
"""

from shiny import App, render, ui

from shinymap import Map, MapSelection, input_map, output_map, render_map, scale_sequential

from shared import DEMO_GEOMETRY, TOOLTIPS


# Example 1: MapSelection - User selection tracking
_ui_user_selection = ui.card(
    ui.card_header("MapSelection: User Selection Tracking"),
    ui.p(
        "MapSelection tracks which regions the user selected via input_map. "
        "The 'selected' parameter reflects the current selection state."
    ),
    ui.layout_columns(
        input_map("user_selected", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="multiple"),
        output_map("user_selection_display", DEMO_GEOMETRY, tooltips=TOOLTIPS),
    ),
    ui.output_text_verbatim("user_selection_text"),
)


def _server_user_selection(input, output, session):
    
    @render_map
    def user_selection_display():
        # MapSelection automatically highlights the selected regions
        # The 'selected' parameter comes from user interaction
        selected = input.user_selected()
        return (
            MapSelection(selected=selected)
            .with_fill_color("#e2e8f0")  # Base color
            .with_fill_color_selected("#3b82f6")  # Selected regions get blue
        )

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
        input_map("region_counts", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="count", value={}),
        output_map("programmatic_display", DEMO_GEOMETRY, tooltips=TOOLTIPS),
    ),
    ui.output_text_verbatim("programmatic_text"),
)


def _server_programmatic(input, output, session):
    @render_map
    def programmatic_display():
        counts = input.region_counts() or {}

        # Compute which regions to highlight (count >= 3)
        high_value_regions = set(rid for rid, count in counts.items() if count >= 3)

        # Use Map to programmatically highlight by varying stroke width
        # This is NOT tracking user selection - it's highlighting based on logic
        fills = scale_sequential(counts, list(DEMO_GEOMETRY.regions.keys()), max_count=10)

        # Create stroke width dict: thicker for high-value regions
        stroke_widths = {rid: 4.0 if rid in high_value_regions else 1.0
                        for rid in DEMO_GEOMETRY.regions.keys()}

        return (
            Map()
            .with_fill_color(fills)
            .with_counts(counts)
            .with_stroke_width(stroke_widths)  # Programmatic: highlight with thicker borders
        )

    @render.text
    def programmatic_text():
        counts = input.region_counts() or {}
        high_value = [rid for rid, count in counts.items() if count >= 3]
        if high_value:
            return f"Regions with count ≥ 3 (highlighted): {', '.join(high_value)}"
        return "No regions have count ≥ 3 yet"


# Example 3: Combined - User selection + Programmatic highlighting
_ui_combined = ui.card(
    ui.card_header("Combined: User Selection + Computed Highlighting"),
    ui.p(
        "MapSelection for user selection, but we compute additional highlighting "
        "for regions that are 'neighbors' of selected regions (simulated)."
    ),
    ui.layout_columns(
        input_map("combined_selected", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="single"),
        output_map("combined_display", DEMO_GEOMETRY, tooltips=TOOLTIPS),
    ),
    ui.output_text_verbatim("combined_text"),
)


# Simulated neighbor relationships
NEIGHBORS = {
    "circle": ["square", "triangle"],
    "square": ["circle", "pentagon"],
    "triangle": ["circle", "hexagon"],
    "pentagon": ["square", "hexagon"],
    "hexagon": ["triangle", "pentagon"],
}


def _server_combined(input, output, session):
    @render_map
    def combined_display():
        selected = input.combined_selected()

        # Compute neighbors of selected region
        neighbors = NEIGHBORS.get(selected, []) if selected else []

        # Use MapSelection for the user's selected region
        # But we can still use with_active() to highlight neighbors
        return (
            MapSelection(selected=selected)
            .with_fill_color("#e2e8f0")  # Base
            .with_fill_color_selected("#3b82f6")  # User's selection is blue
            # Note: with_active() would override the selected highlighting
            # So for this use case, we'd use with_fill_color() with a dict instead:
            .with_fill_color({rid: "#93c5fd" for rid in neighbors})  # Neighbors light blue
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

- **`MapSelection(selected=...)`**: Use when you want to **track and visualize user selection**
  from an input_map. The `selected` parameter reflects what the user chose.

- **Programmatic highlighting**: Use computed styling (e.g., `with_fill_color()`, `with_stroke_width()`)
  to **highlight regions based on logic** (thresholds, relationships, algorithms, etc.) that is NOT
  directly tied to user selection from an input.

**When to use each:**
- User clicks → tracking their selection? → `MapSelection(selected=input.my_map())`
- Computing which regions to highlight based on data/logic? → Use conditional styling with dicts
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
