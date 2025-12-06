"""Demo showcasing all input modes for shinymap."""

from shiny import App, render, ui

from shinymap import Map, input_map, output_map, render_map, scale_sequential

DEMO_GEOMETRY = {
    "circle": "M25,50 A20,20 0 1 1 24.999,50 Z",
    "square": "M10 10 H40 V40 H10 Z",
    "triangle": "M75 70 L90 40 L60 40 Z",
}

TOOLTIPS = {"circle": "Circle", "square": "Square", "triangle": "Triangle"}


app_ui = ui.page_fluid(
    ui.h2("shinymap Input Modes Demo"),
    ui.p("This demo showcases all the input modes available in shinymap."),
    # Single selection mode
    ui.h3("1. Single Selection (mode='single')"),
    ui.p("Click shapes to select one at a time. Clicking again deselects."),
    ui.layout_columns(
        input_map("single", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="single", value={}),
        ui.div(
            ui.h4("Selected Region:"),
            ui.output_text_verbatim("single_output"),
        ),
    ),
    ui.hr(),
    # Multiple selection mode
    ui.h3("2. Multiple Selection (mode='multiple')"),
    ui.p("Click shapes to select multiple. Click again to deselect."),
    ui.layout_columns(
        input_map("multiple", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="multiple", value={}),
        ui.div(
            ui.h4("Selected Regions:"),
            ui.output_text_verbatim("multiple_output"),
        ),
    ),
    ui.hr(),
    # Count mode (unlimited)
    ui.h3("3. Count Mode - Unlimited (mode='count')"),
    ui.p("Click shapes to increment counters. Keeps counting up indefinitely."),
    ui.layout_columns(
        input_map("count_unlimited", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="count", value={}),
        ui.div(
            ui.h4("Click Counts:"),
            ui.output_text_verbatim("count_unlimited_output"),
        ),
    ),
    ui.hr(),
    # Count mode with cycle - HUE CYCLING
    ui.h3("4. Count Mode - Hue Cycling (mode='count', cycle=4)"),
    ui.p("Click shapes to cycle through colors: gray→red→yellow→green→gray. Perfect for color wheel quizzes!"),
    ui.layout_columns(
        input_map("count_cycle", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="count", cycle=4, value={}),
        ui.div(
            ui.h4("Current Colors (0-3):"),
            ui.output_text_verbatim("count_cycle_output"),
        ),
    ),
    ui.hr(),
    # Multiple selection with max_selection
    ui.h3("5. Multiple Selection with Limit (mode='multiple', max_selection=2)"),
    ui.p("Select up to 2 shapes. Further clicks are ignored."),
    ui.layout_columns(
        input_map("limited", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="multiple", max_selection=2, value={}),
        ui.div(
            ui.h4("Selected (max 2):"),
            ui.output_text_verbatim("limited_output"),
        ),
    ),
    ui.hr(),
    # Visual feedback with output map
    ui.h3("6. Visual Feedback with Output Map"),
    ui.p("Click to count, see the visual feedback with color intensity. Uses fixed ceiling (max=10) for consistent scaling."),
    ui.layout_columns(
        input_map("visual_input", DEMO_GEOMETRY, tooltips=TOOLTIPS, mode="count", value={}),
        output_map("visual_output"),
    ),
)


def server(input, output, session):
    @render.text
    def single_output():
        selected = input.single()  # Returns string or None
        if selected:
            return f"Selected: {selected}"
        return "None selected"

    @render.text
    def multiple_output():
        selected = input.multiple()  # Returns list of strings
        if selected:
            return f"Selected: {', '.join(selected)}"
        return "None selected"

    @render.text
    def count_unlimited_output():
        value = input.count_unlimited() or {}
        counts_str = ", ".join([f"{id}: {count}" for id, count in value.items() if count > 0])
        return counts_str if counts_str else "No clicks yet"

    @render.text
    def count_cycle_output():
        value = input.count_cycle() or {}
        color_names = ["gray", "red", "yellow", "green"]
        counts_str = ", ".join(
            [f"{id}: {color_names[count % 4]}" for id, count in value.items() if count > 0]
        )
        return counts_str if counts_str else "No clicks yet"

    @render.text
    def limited_output():
        selected = input.limited()  # Returns list of strings
        if selected:
            return f"Selected: {', '.join(selected)} ({len(selected)}/2)"
        return "None selected (0/2)"

    @render_map
    def visual_output():
        counts = input.visual_input() or {}
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_fills(scale_sequential(counts, list(DEMO_GEOMETRY.keys()), max_count=10))
            .with_counts(counts)
        )


app = App(app_ui, server)
