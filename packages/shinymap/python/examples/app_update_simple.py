"""Simple test for update_map() debugging."""

from shiny import App, ui, reactive, render

from shinymap import aes, input_map, update_map

from shared import DEMO_OUTLINE, TOOLTIPS


app_ui = ui.page_fixed(
    ui.h1("Simple Update Test"),
    ui.input_action_button("update_btn", "Click to Update", class_="btn-primary"),
    ui.hr(),
    input_map(
        "test_map",
        DEMO_OUTLINE,
        tooltips=TOOLTIPS,
        mode="multiple",
        aes=aes.ByState(
            base=aes.Shape(
                fill_color="#e2e8f0",
                stroke_width=1,
            )
        ),
    ),
    ui.output_text_verbatim("debug_output"),
    # Enable debug logging in browser console
    ui.tags.script("localStorage.setItem('shinymapDebug', 'true');"),
)


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.update_btn)
    def _():
        print("[DEBUG] Button clicked, calling update_map")
        update_map(
            "test_map",
            fill_color={"circle": "#ef4444", "square": "#3b82f6", "triangle": "#10b981"},
        )
        print("[DEBUG] update_map called")

    @render.text
    def debug_output():
        return f"Button clicks: {input.update_btn()}\nSelected: {input.test_map()}"


app = App(app_ui, server)
