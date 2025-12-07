from shiny import App, ui

from shinymap import QUALITATIVE, Map, input_map, output_map, render_map, scale_qualitative

DEMO_GEOMETRY = {
    "circle": "M25,50 A20,20 0 1 1 24.999,50 Z",
    "square": "M10 10 H40 V40 H10 Z",
    "triangle": "M75 70 L90 40 L60 40 Z",
}

TOOLTIPS = {"circle": "Circle", "square": "Square", "triangle": "Triangle"}
SHAPE_COLORS = {"circle": QUALITATIVE[0], "square": QUALITATIVE[1], "triangle": QUALITATIVE[2]}



## Basic Example --------

ui_basic = ui.page_fillable(
    ui.card(
        ui.card_header("Single Select"),
        ui.layout_columns(
            input_map(
                "region",
                DEMO_GEOMETRY,
                tooltips=TOOLTIPS,
                mode="single",
                value={},
                hover_highlight={"stroke_width": 1},
            ),
            output_map("single_select_output")
        ),
    )
)


def server_basic(input):

    def selected_ids(counts: dict[str, int] | None) -> list[str]:
        """Return IDs of regions with count > 0."""
        return [id for id, count in (counts or {}).items() if count > 0]


    def fills_for_summary(counts: dict[str, int] | None) -> dict[str, str]:
        """Active regions get their assigned color; inactive regions are neutral gray."""
        counts = counts or {}
        return scale_qualitative(
            categories={rid: rid if counts.get(rid, 0) > 0 else None for rid in DEMO_GEOMETRY},
            region_ids=list(DEMO_GEOMETRY.keys()),
            palette=[SHAPE_COLORS[rid] for rid in DEMO_GEOMETRY],
        )

    @render_map
    def single_select_output():
        selected = input.region()
        counts = {selected: 1} if selected else {}
        return (
            Map(DEMO_GEOMETRY, tooltips=TOOLTIPS)
            .with_fills(fills_for_summary(counts))
            .with_counts(counts)
            .with_active(selected_ids(counts))
            .with_stroke_width(1.5)
        )



## Put them together

app_ui = ui.page_navbar(
    ui.nav_panel("Basic Examples", ui_basic),
    title="ShinyMap"
)

def server(input, output, session):

    server_basic(input)


app = App(app_ui, server)
