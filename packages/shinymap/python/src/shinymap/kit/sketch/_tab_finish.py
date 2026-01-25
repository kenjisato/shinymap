"""Sketch app for interactive SVG relabeling and layer assignment."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from shiny import reactive, render, ui

if TYPE_CHECKING:
    pass

# Module-level variable for CLI-provided SVG/JSON file
_initial_file: Path | None = None


## Code Generation Page =====================================================================

ui_tab_finish = ui.nav_panel(
    "Finishing",
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_text("meta_source", "Source"),
            ui.input_text("meta_license", "License"),
            ui.input_action_button("apply_metadata", "Apply Metadata", class_="btn-success"),
            ui.hr(),
            ui.input_text("output_filename", "Output JSON filename", value="output.json"),
            ui.download_button("download_json", "Download JSON"),
        ),
        ui.TagList(
            ui.output_ui("pending_changes_warning"),
            ui.help_text("JSON"),
            ui.div(
                ui.output_text_verbatim("json_preview", placeholder=True),
                style="height: 400px; overflow: scroll;",
            ),
        ),
    ),
)


def server_tab_finish(input, globals):
    @render.ui
    def pending_changes_warning():
        """Show warning if there are registered but unapplied changes."""
        registered = globals.registered_ids()
        if registered:
            count = len(registered)
            return ui.div(
                ui.p(
                    f"⚠️ {count} region(s) registered but not applied. "
                    "Go to Relabeling tab and click Apply to include them in the output.",
                    style="margin: 0;",
                ),
                class_="alert alert-warning",
            )
        return None

    @reactive.calc
    def final_outline():
        """Get the final outline with all transformations applied.

        This applies layer assignments (overlay, underlay, hidden, annotation)
        and metadata groups that are tracked separately from globals.outline()
        to keep regions interactive in the Relabeling tab.
        """
        outline = globals.outline()
        if not outline:
            return None

        # Apply layer assignments
        overlay_ids = globals.overlay_ids()
        if overlay_ids:
            outline = outline.move_layer("overlay", list(overlay_ids))

        underlay_ids = globals.underlay_ids()
        if underlay_ids:
            outline = outline.move_layer("underlay", list(underlay_ids))

        hidden_ids = globals.hidden_ids()
        if hidden_ids:
            outline = outline.move_layer("hidden", list(hidden_ids))

        annotation_ids = globals.annotation_ids()
        if annotation_ids:
            outline = outline.move_layer("annotation", list(annotation_ids))

        # Apply metadata groups
        metadata_groups = globals.metadata_groups()
        if metadata_groups:
            outline = outline.update_metadata({"groups": dict(metadata_groups)})

        return outline

    @reactive.effect
    @reactive.event(input.apply_metadata)
    def handle_apply_metadata():
        """Apply metadata fields to globals.outline()."""
        outline = globals.outline()
        if not outline:
            return

        # Build metadata dict from inputs
        metadata = {}
        source = input.meta_source().strip()
        license_ = input.meta_license().strip()

        if source:
            metadata["source"] = source
        if license_:
            metadata["license"] = license_

        # Apply metadata if any
        if metadata:
            globals.outline.set(outline.update_metadata(metadata))

    @render.text
    def json_preview():
        """Preview the final JSON with layer assignments applied."""
        outline = final_outline()
        if not outline:
            return "Upload SVG to preview JSON output."

        result = outline.to_dict()
        if "error" in result:
            return f"Error: {result['error']}"

        return json.dumps(result, indent=2, ensure_ascii=False)

    @render.download(filename=lambda: input.output_filename())
    def download_json():
        """Download the final JSON file with layer assignments applied."""
        outline = final_outline()
        if not outline:
            return ""

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            outline.to_json(f.name)
            return f.name
