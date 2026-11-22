"""Demo app for annotation layer feature (Issue #7).

The annotation layer renders above hover/selection layers, ensuring
text labels are always visible even when regions are hovered or selected.
"""

from shiny import App, render, ui

from shinymap import Outline, aes, input_map, svg
from shinymap.outline import Regions

# Create an outline with shapes and text labels
OUTLINE_WITH_LABELS = Outline(regions=Regions(
    # Main interactive shapes
    circle=[svg.Circle(cx=25, cy=70, r=20)],
    square=[svg.Path(d="M10 10 H40 V40 H10 Z")],
    triangle=[svg.Path(d="M75 70 L90 40 L60 40 Z")],
    # Text labels (will be placed in annotation layer)
    _label_circle=[
        svg.Text(x=25, y=70, text="C", font_size=10, text_anchor="middle")
    ],
    _label_square=[
        svg.Text(x=25, y=27, text="S", font_size=10, text_anchor="middle")
    ],
    _label_triangle=[
        svg.Text(x=75, y=55, text="T", font_size=10, text_anchor="middle")
    ]
), metadata={"viewBox": "0 0 100 100"})


# Move labels to annotation layer so they render above hover/selection
LABELED_OUTLINE = OUTLINE_WITH_LABELS.move_layer(
    "annotation", "_label_circle", "_label_square", "_label_triangle"
)

# For comparison: labels in overlay layer (will be hidden by hover/selection)
OVERLAY_OUTLINE = OUTLINE_WITH_LABELS.move_layer(
    "overlay", "_label_circle", "_label_square", "_label_triangle"
)

app_ui = ui.page_fixed(
    ui.h2("Annotation Layer Demo"),
    ui.p(
        "The annotation layer renders above hover/selection layers. "
        "Compare the two maps below - hover over the shapes to see the difference."
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Labels in ANNOTATION Layer (Always Visible)"),
            input_map(
                "annotation_map",
                LABELED_OUTLINE,
                mode="multiple",
                aes=aes.ByState(
                    base=aes.Shape(fill_color="#e0f2fe", stroke_color="#0284c7"),
                    select=aes.Shape(fill_color="#7dd3fc", stroke_color="#0369a1"),
                    hover=aes.Shape(fill_opacity=0.8, stroke_width=2),
                ),
            ),
            ui.output_text_verbatim("annotation_selected"),
        ),
        ui.card(
            ui.card_header("Labels in OVERLAY Layer (Hidden by Hover)"),
            input_map(
                "overlay_map",
                OVERLAY_OUTLINE,
                mode="multiple",
                aes=aes.ByState(
                    base=aes.Shape(fill_color="#e0f2fe", stroke_color="#0284c7"),
                    select=aes.Shape(fill_color="#7dd3fc", stroke_color="#0369a1"),
                    hover=aes.Shape(fill_opacity=0.8, stroke_width=2),
                ),
            ),
            ui.output_text_verbatim("overlay_selected"),
        ),
    ),
    ui.h3("How it works"),
    ui.pre(
        ui.code(
            """\
from shinymap import Outline, svg
from shinymap.outline import Regions

# Create outline with text labels
outline = Outline(regions=Regions(
    circle=[svg.Circle(cx=25, cy=70, r=20)],
    _label_circle=[svg.Text(x=25, y=70, text="C", font_size=10, text_anchor="middle")],
    ...
), metadata={"viewBox": "0 0 100 100"})

# Move labels to annotation layer (above hover/selection)
labeled = outline.move_layer("annotation", "_label_circle", ...)
"""
        )
    ),
    title="Annotation Layer Demo",
)


def server(input, output, session):
    @render.text
    def annotation_selected():
        return f"Selected: {input.annotation_map()}"

    @render.text
    def overlay_selected():
        return f"Selected: {input.overlay_map()}"


app = App(app_ui, server)
