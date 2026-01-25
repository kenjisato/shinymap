"""Sketch app: Upload Tab."""

from __future__ import annotations

from pathlib import Path

from shiny import reactive, render, ui

from ... import Map, aes
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

        # Clear layer metadata so all regions (including hidden) are visible
        # But use groups to show which layer each region was originally in
        all_ids = set(outline.regions.keys())
        overlay_ids = set(outline.metadata.get("overlay", []))
        underlay_ids = set(outline.metadata.get("underlay", []))
        hidden_ids = set(outline.metadata.get("hidden", []))
        annotation_ids = set(outline.metadata.get("annotation", []))
        main_ids = all_ids - overlay_ids - underlay_ids - hidden_ids - annotation_ids

        # Create groups for styling by original layer
        groups = {}
        if main_ids:
            groups["_main"] = list(main_ids)
        if overlay_ids:
            groups["_overlay"] = list(overlay_ids)
        if underlay_ids:
            groups["_underlay"] = list(underlay_ids)
        if hidden_ids:
            groups["_hidden"] = list(hidden_ids)
        if annotation_ids:
            groups["_annotation"] = list(annotation_ids)

        # Clear layer metadata by setting to empty lists (update_metadata merges,
        # so we can't delete keys - we must override them with empty values)
        # This ensures all regions are rendered as main layer
        display_outline = outline.update_metadata({
            "overlay": [],
            "underlay": [],
            "hidden": [],
            "annotation": [],
            "groups": groups,
        })

        # Style: main=blue, overlay=orange, underlay=yellow, hidden=gray, annotation=green
        group_aes = {
            "_main": aes.Shape(fill_color="#bfdbfe", stroke_color="#1e40af"),  # blue
            "_overlay": aes.Shape(fill_color="#fed7aa", stroke_color="#ea580c"),  # orange
            "_underlay": aes.Shape(fill_color="#fef08a", stroke_color="#ca8a04"),  # yellow
            "_hidden": aes.Shape(
                fill_color="#e5e7eb", stroke_color="#6b7280", stroke_dasharray="4 2"
            ),  # gray dashed
            "_annotation": aes.Shape(fill_color="#bbf7d0", stroke_color="#16a34a"),  # green
        }

        return Map(display_outline, aes=aes.ByGroup(**group_aes))

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

        region_ids = list(outline.regions.keys())
        if not region_ids:
            return "No elements found in file."

        # Get layer assignments
        overlay_ids = set(outline.metadata.get("overlay", []))
        underlay_ids = set(outline.metadata.get("underlay", []))
        hidden_ids = set(outline.metadata.get("hidden", []))
        annotation_ids = set(outline.metadata.get("annotation", []))

        # Get metadata groups
        metadata_groups = outline.metadata.get("groups", {})
        if not isinstance(metadata_groups, dict):
            metadata_groups = {}

        # Build reverse lookup: region_id -> list of group names
        region_to_groups: dict[str, list[str]] = {}
        for group_name, members in metadata_groups.items():
            if isinstance(members, (list, tuple)):
                for rid in members:
                    if rid not in region_to_groups:
                        region_to_groups[rid] = []
                    region_to_groups[rid].append(group_name)

        # Count auto-generated IDs
        auto_generated = sum(1 for pid in region_ids if pid.startswith("path_"))

        msg = f"Found {len(region_ids)} regions"
        if auto_generated > 0:
            msg += f" ({auto_generated} auto-generated IDs)"

        # Show layer summary if any non-main layers exist
        layer_counts = []
        if overlay_ids:
            layer_counts.append(f"▲ {len(overlay_ids)} overlay")
        if underlay_ids:
            layer_counts.append(f"▼ {len(underlay_ids)} underlay")
        if hidden_ids:
            layer_counts.append(f"○ {len(hidden_ids)} hidden")
        if annotation_ids:
            layer_counts.append(f"★ {len(annotation_ids)} annotation")

        if layer_counts:
            msg += f"\nLayers: {', '.join(layer_counts)}"

        # Show groups summary
        if metadata_groups:
            group_info = ", ".join(f"{k}({len(v)})" for k, v in metadata_groups.items())
            msg += f"\nGroups: {group_info}"

        msg += "\n\n"

        # Build region list with layer indicators and group membership
        lines = []
        for pid in region_ids:
            # Layer indicator
            if pid in overlay_ids:
                line = f"▲ {pid}"
            elif pid in underlay_ids:
                line = f"▼ {pid}"
            elif pid in hidden_ids:
                line = f"○ {pid}"
            elif pid in annotation_ids:
                line = f"★ {pid}"
            else:
                line = f"■ {pid}"

            # Add group membership
            if pid in region_to_groups:
                groups_str = ", ".join(region_to_groups[pid])
                line += f"  [{groups_str}]"

            lines.append(line)

        return msg + "\n".join(lines)
