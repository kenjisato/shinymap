"""StillLife next to the live map: the same picture, as a static SVG.

The left card is an ordinary `output_map` + `@render_map`. The right card draws
`StillLife(Map(...), map_id="live")` with `@render.ui`: it follows the output's
outline, wash and aes, so both show the same map. The SVG can be downloaded.

The values are made up for the demo.

Run:
    uv run shiny run packages/shinymap/python/examples/app_stilllife.py
"""

import inspect
from pathlib import Path

from shiny import App, reactive, render, ui

from shinymap import Map, StillLife, Wash, aes
from shinymap.aes.color import scale_continuous
from shinymap.outline import Outline

from japan_prefectures import PREF_NAMES_JA, PREF_NAMES_ROMAJI

OUTLINE = (
    Outline.from_json(Path(__file__).parent / "data" / "japan_prefectures.json")
    .path_as_line("_divider_lines")
    .set_overlays(["_divider_lines"])
)
CODES = list(PREF_NAMES_JA)
TOOLTIPS = {code: f"{PREF_NAMES_JA[code]} ({PREF_NAMES_ROMAJI[code]})" for code in CODES}

# Made-up values: two patterns to switch between, and a few regions without data
DATASETS = {
    "north_south": {code: 100 - 2 * i for i, code in enumerate(CODES)},
    "scattered": {code: (i * 37) % 100 for i, code in enumerate(CODES) if i % 11 != 5},
}

wc = Wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#e2e8f0", stroke_color="#ffffff", stroke_width=1.5),
        hover=aes.Shape(stroke_color="#0f172a", stroke_width=3),
    ),
    line=aes.Line(stroke_color="#64748b", stroke_width=2),
)


app_ui = ui.page_fluid(
    ui.h3("StillLife: the live map as a static SVG"),
    ui.layout_columns(
        ui.input_radio_buttons(
            "dataset",
            "Values (made up)",
            {"north_south": "North → south", "scattered": "Scattered, some missing"},
            inline=True,
        ),
        ui.input_slider("vmax", "vmax", min=50, max=150, value=100, step=10),
        col_widths=(6, 6),
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("@render_map (in the browser)"),
            wc.output_map("live", OUTLINE, tooltips=TOOLTIPS, height="520px"),
        ),
        ui.card(
            ui.card_header(
                "StillLife(Map(...), map_id=\"live\") (static SVG)",
                ui.download_link("download", "Download SVG", class_="float-end"),
            ),
            ui.div(ui.output_ui("still"), style="height: 520px;"),
        ),
        col_widths=(6, 6),
    ),
    ui.output_ui("code"),
)


def server(input, output, session):
    @reactive.calc
    def colors():
        return scale_continuous(DATASETS[input.dataset()], CODES, vmin=0, vmax=input.vmax())

    @wc.render_map
    def live():
        return Map(fill_color=colors())

    @render.ui
    def still():
        pic = StillLife(Map(fill_color=colors()), map_id="live")
        return ui.HTML(pic.to_svg(fit=True))

    @render.download(filename="map.svg")
    def download():
        yield StillLife(Map(fill_color=colors()), map_id="live").to_svg()

    @render.ui
    def code():  # this server function, as it runs
        return ui.pre(inspect.getsource(server))


app = App(app_ui, server)
