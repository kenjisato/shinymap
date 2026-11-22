"""Sketch app: Infer tab for generating reproducible Python code."""

from __future__ import annotations

from pathlib import Path

from shiny import reactive, render, ui

from ...outline import Outline

## Inference Page =====================================================================

ui_tab_infer = ui.nav_panel(
    "Generate Code",
    ui.layout_sidebar(
        ui.sidebar(
            ui.p(
                "Upload the original source file to generate code that "
                "reproduces the current transformations."
            ),
            ui.input_file(
                "original_source_file",
                "Original SVG/JSON file",
                accept=[".svg", ".json"],
                multiple=False,
            ),
            ui.hr(),
            ui.input_text("code_input_filename", "Input filename (in code)"),
            ui.input_text("code_output_filename", "Output filename", value="output.json"),
        ),
        ui.TagList(
            ui.output_ui("original_status"),
            ui.help_text("Generated Python Code"),
            ui.output_text_verbatim("inferred_code", placeholder=True),
        ),
    ),
)


def server_tab_infer(input, globals):
    @reactive.calc
    def get_original_outline():
        """Get the original outline - from uploaded file or fallback to loaded file."""
        file_info = input.original_source_file()
        if file_info:
            # User uploaded an original file
            file_path = Path(file_info[0]["datapath"])
            original_name = file_info[0]["name"]
            if file_path.suffix.lower() == ".json":
                outline = Outline.from_json(file_path)
            else:
                outline = Outline.from_svg(file_path, extract_viewbox=True)
            return {"outline": outline, "name": original_name, "uploaded": True}

        # Fallback to the file loaded in Original Outline tab
        if globals.original_outline:
            name = globals.original_file.name if globals.original_file else "original"
            return {"outline": globals.original_outline, "name": name, "uploaded": False}

        return None

    @render.ui
    def original_status():
        """Show status of which original is being used."""
        info = get_original_outline()
        if not info:
            return ui.div(
                ui.p("No original file available. Upload a file above."),
                class_="alert alert-warning",
            )

        if info["uploaded"]:
            return ui.div(
                ui.p(f"Using uploaded original: {info['name']}"),
                class_="alert alert-success",
            )
        else:
            return ui.div(
                ui.p(
                    f"Using loaded file as original: {info['name']}. "
                    "Upload the actual original SVG if this is an intermediate file."
                ),
                class_="alert alert-info",
            )

    @render.text
    def inferred_code():
        """Generate Python code from current state."""
        original_info = get_original_outline()
        current = globals.outline()

        if not original_info or not current:
            return "# Load files first to generate code."

        original = original_info["outline"]

        # Get input filename
        input_filename = input.code_input_filename().strip()
        if not input_filename:
            input_filename = original_info["name"]

        output_filename = input.code_output_filename().strip() or "output.json"

        # Infer relabel mapping by comparing original and current outlines
        relabel = _infer_relabel(original, current)

        # Get layer assignments - only include IDs that are NEW (not already in original)
        original_overlay = set(original.metadata.get("overlay", []))
        original_underlay = set(original.metadata.get("underlay", []))
        original_hidden = set(original.metadata.get("hidden", []))
        original_annotation = set(original.metadata.get("annotation", []))

        current_overlay = globals.overlay_ids() or set()
        current_underlay = globals.underlay_ids() or set()
        current_hidden = globals.hidden_ids() or set()
        current_annotation = globals.annotation_ids() or set()

        # Only emit move_layer for IDs that changed from their original layer
        new_overlay = current_overlay - original_overlay
        new_underlay = current_underlay - original_underlay
        new_hidden = current_hidden - original_hidden
        new_annotation = current_annotation - original_annotation

        overlay_ids = list(new_overlay) if new_overlay else None
        underlay_ids = list(new_underlay) if new_underlay else None
        hidden_ids = list(new_hidden) if new_hidden else None
        annotation_ids = list(new_annotation) if new_annotation else None

        # Get lines_as_path - only include IDs that are NEW
        original_lines = set(original.metadata.get("lines_as_path", []))
        current_lines = globals.lines_as_path_ids() or set()
        new_lines = current_lines - original_lines
        lines_as_path_ids = list(new_lines) if new_lines else None

        # Get metadata groups - only include if different from original
        original_groups = original.metadata.get("groups", {})
        current_groups = dict(globals.metadata_groups()) if globals.metadata_groups() else {}
        metadata_groups = current_groups if current_groups != original_groups else None

        # Get metadata from current outline (excluding internal keys)
        metadata = {}
        internal_keys = {
            "viewBox",
            "overlay",
            "underlay",
            "hidden",
            "annotation",
            "lines_as_path",
            "original_source",
            "groups",
        }
        for key, value in current.metadata.items():
            if not key.startswith("_") and key not in internal_keys:
                metadata[key] = value

        # Determine loader based on file extension
        if input_filename.lower().endswith(".json"):
            loader = "from_json"
        else:
            loader = "from_svg"

        # Generate code
        lines = [
            "# Generated by shinymap sketch app",
            "from shinymap import Outline",
            "",
            f'outline = Outline.{loader}("{input_filename}")',
        ]

        if relabel:
            lines.append("")
            lines.append("# Relabel/merge regions")
            lines.append("outline = outline.relabel({")
            for new_id, old_ids in relabel.items():
                lines.append(f'    "{new_id}": {old_ids!r},')
            lines.append("})")

        if overlay_ids:
            lines.append("")
            lines.append("# Set overlay layer")
            lines.append(f"outline = outline.move_layer('overlay', {overlay_ids!r})")

        if underlay_ids:
            lines.append("")
            lines.append("# Set underlay layer")
            lines.append(f"outline = outline.move_layer('underlay', {underlay_ids!r})")

        if hidden_ids:
            lines.append("")
            lines.append("# Set hidden layer")
            lines.append(f"outline = outline.move_layer('hidden', {hidden_ids!r})")

        if annotation_ids:
            lines.append("")
            lines.append("# Set annotation layer")
            lines.append(f"outline = outline.move_layer('annotation', {annotation_ids!r})")

        if lines_as_path_ids:
            lines.append("")
            lines.append("# Mark regions as lines (stroke-only)")
            lines.append(f"outline = outline.path_as_line(*{lines_as_path_ids!r})")

        if metadata_groups:
            lines.append("")
            lines.append("# Set metadata groups")
            lines.append("outline = outline.update_metadata({")
            lines.append(f'    "groups": {metadata_groups!r},')
            lines.append("})")

        if metadata:
            lines.append("")
            lines.append("# Add metadata")
            lines.append("outline = outline.update_metadata({")
            for key, value in metadata.items():
                lines.append(f'    "{key}": {value!r},')
            lines.append("})")

        lines.append("")
        lines.append("# Save to JSON")
        lines.append(f'outline.to_json("{output_filename}")')

        return "\n".join(lines)


def _infer_relabel(original, current):
    """Infer relabel mapping by comparing original and current outlines.

    Compares elements in regions to detect renames and merges.
    """
    original_keys = set(original.regions.keys())
    current_keys = set(current.regions.keys())

    # Keys that exist in current but not in original (new/renamed)
    new_keys = current_keys - original_keys
    # Keys that exist in original but not in current (removed/merged)
    removed_keys = original_keys - current_keys

    if not new_keys or not removed_keys:
        return None

    inferred_relabel = {}

    for new_key in new_keys:
        current_elements = current.regions.get(new_key, [])
        matched_originals = []

        for orig_key in removed_keys:
            orig_elements = original.regions.get(orig_key, [])
            # Check if original elements are in current region
            for orig_elem in orig_elements:
                if orig_elem in current_elements:
                    matched_originals.append(orig_key)
                    break

        if matched_originals:
            if len(matched_originals) == 1:
                # Single match - rename
                inferred_relabel[new_key] = matched_originals[0]
            else:
                # Multiple matches - merge
                inferred_relabel[new_key] = matched_originals

    return inferred_relabel if inferred_relabel else None
