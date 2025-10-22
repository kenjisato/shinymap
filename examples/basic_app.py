from __future__ import annotations

import pandas as pd
from shiny import App, Inputs, Outputs, Session, render, ui

import pandas as pd, shinyjpmap as jp

df = pd.DataFrame({
    "pref_code": [1, 13, 27, 47],
    "value": [0.1, 0.3, 0.6, 0.9],
    "tip": ["Hokkaido", "Tokyo", "Osaka", "Okinawa"],
})
svg = jp.map(df, color="value", tooltip="tip", palette="viridis").data


app_ui = ui.page_fluid(
    jp.input_map(
        "pref_in",
        #regions=["Tohoku"],
        okinawa="bottomright",
        map_width="360px",
        map_height="360px",
    ),
    jp.output_map("pref_out"),
    ui.output_text("clicked"),
)


def server(input: Inputs, output: Outputs, session: Session):
    @output
    @render.ui
    def pref_out():
        map_img = jp.map(
            df,
            color="value",
            tooltip="tip",
            okinawa="bottomright",
            map_width="360px",
            map_height="360px",
            palette="viridis",
        )
        return map_img.as_ui()

    @output
    @render.text
    def clicked():
        value = input.pref_in()
        return f"clicked: {value}" if value else "clicked: (none)"


app = App(app_ui, server=server)
