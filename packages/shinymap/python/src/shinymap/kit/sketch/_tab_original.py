"""Sketch app: Upload Tab."""

from __future__ import annotations

from pathlib import Path

from shiny import reactive, render, ui

from ... import Map
from ...ui import output_map, render_map

## Upload File =====================================================================

ui_tab_original = ui.nav_panel(
    "Original Outline",
    ui.layout_columns(
        ui.TagList(
            ui.output_ui("upload_file"),
            ui.output_text("path_file_name"),
            output_map("output_path_file"),
        ),
        ui.div(
            ui.help_text("Path IDs"),
            ui.output_text_verbatim("path_list", placeholder=True),
        ),
        col_widths=(8, 4),
    ),
)


def server_tab_original(input, globals):
    @render.ui
    def upload_file():
        if globals.initial_file is None:
            return ui.input_file(
                "path_file",
                "Choose SVG or JSON file",
                accept=[".svg", ".json"],
                multiple=False,
            )

    # Reactive value to record user operation
    file_upload_status = reactive.value(False)

    @reactive.effect
    @reactive.event(input.path_file)
    def _():
        pass

    @reactive.effect
    @reactive.event(input.path_file)
    def reload_outline():
        """Parse uploaded SVG or JSON file."""
        file_info = input.path_file()
        if not file_info:
            # TODO: check if it's working.
            ui.notification_show("Cancelled.")
            return

        # Read the uploaded file
        file_path = Path(file_info[0]["datapath"])
        globals["oritinal_file"].set(file_path)

        # Record as uploaded
        file_upload_status.set(True)

    @render_map
    def output_path_file():
        # Use original_outline to always show the unchanged original
        outline = globals.original_outline
        if not outline:
            return Map()
        return Map(outline)

    @render.text
    def path_file_name():
        if globals.original_file:
            return f"File: {globals.original_file}"
        return "No file"

    @render.text
    def path_list():
        """Display list of path IDs found/generated in extracted JSON."""
        # Use original_outline to always show the unchanged original
        outline = globals.original_outline
        if not outline:
            return "No file uploaded yet."

        if "error" in globals.message:
            return f"Error parsing SVG: {globals.message['error']}"

        region_ids = outline.regions.keys()
        if not region_ids:
            return "No elements found in file."

        # Count auto-generated IDs
        auto_generated = sum(1 for pid in region_ids if pid.startswith("path_"))

        msg = f"Found {len(region_ids)} regions"
        if auto_generated > 0:
            msg += f" ({auto_generated} auto-generated IDs)"
        msg += ":\n\n"

        return msg + ", ".join(f"{pid}" for pid in region_ids)
