from __future__ import annotations

import json
import tempfile
from pathlib import Path

from shiny import App, reactive, render, ui

from ..._ui import Map, input_map, output_map, render_map, update_map
from .._core import Outline, convert, infer_relabel
from ._tool import generate_code, load_file

# Module-level variable for CLI-provided SVG/JSON file
_initial_file: Path | None

## Upload File =====================================================================

panel_upload = ui.nav_panel(
    "Upload",
    ui.h2("Upload File"),
    ui.layout_columns(
        ui.TagList(
            ui.output_ui("upload_file"),
            output_map("output_path_file"),
            ui.output_text("path_file_name"),
            ui.input_text("meta_source", "Source"),
            ui.input_text("meta_license", "License"),
        ),
        ui.TagList(
            ui.help_text("Path IDs"),
            ui.output_text_verbatim("path_list", placeholder=True),
        ),
        col_widths=(4, 8),
    ),
)


def server_file_upload(input, file_name, extracted_data):
    @render_map
    def output_path_file():
        if _initial_file is not None:
            result = convert(_initial_file)
            # Result is the final JSON - create Outline object from it
            geo = Outline.from_dict(result)
            return Map(geo)
        # Return empty map when no file loaded
        empty_geo = Outline.from_dict({"_metadata": {"viewBox": "0 0 100 100"}})
        return Map(empty_geo)

    @render.ui
    def upload_file():
        if _initial_file is None:
            return ui.input_file(
                "path_file",
                "Choose SVG or JSON file",
                accept=[".svg", ".json"],
                multiple=False,
            )

    @reactive.effect
    @reactive.event(input.path_file)
    def parse_uploaded_svg():
        """Parse uploaded SVG or JSON file."""
        file_info = input.path_file()
        if not file_info:
            extracted_data.set(None)
            return

        # Read the uploaded file
        file_path = file_info[0]["datapath"]
        file_name.set(file_info[0]["name"])

        try:
            extracted_data.set(load_file(file_path, file_name()))
        except Exception as e:
            extracted_data.set({"error": str(e)})

    @render.text
    def path_file_name():
        if file_name():
            return f"File: {file_name()}"
        return "No file"


## Relabeling Page =====================================================================

panel_relabeling = ui.nav_panel(
    "Relabeling",
    ui.layout_columns(
        ui.output_ui("map_relabeling"),
        ui.TagList(
            ui.layout_columns(
                ui.layout_columns(
                    ui.TagList(
                        ui.help_text("New ID"),
                        ui.input_text("new_id", ""),
                    ),
                    ui.input_radio_buttons(
                        "target_layer",
                        "Layer",
                        choices=["Interactive", "Overlay"],
                        selected="Interactive",
                        inline=True,
                    ),
                    col_widths=(6, 6),
                ),
                ui.TagList(
                    ui.input_action_button("register_relabel", "Register", class_="btn-primary"),
                    ui.input_action_button("unregister_relabel", "Unregister", class_="btn-danger"),
                ),
                col_widths=(6, 6),
            ),
            ui.help_text("Old ID (selected objects)"),
            ui.output_text_verbatim("selected_original_ids", placeholder=True),
            ui.help_text("Registered objects (pending relabeling)"),
            ui.output_text_verbatim("registered_objects_display", placeholder=True),
        ),
    ),
)


def server_relabeling(input, extracted_data, relabel_rules, registered_ids, overlay_ids):
    @render.ui
    def map_relabeling():
        """Preview the extracted geometry with state-based styling."""
        data = extracted_data()
        if not data or "error" in data:
            return ui.p("Invalid data")

        # Get Outline object from loaded data
        geo = data.get("geometry")
        if not geo:
            return ui.p("Invalid data")

        if not geo.regions:
            return ui.p("Invalid data")

        # Get current R (registered) state
        current_registered = registered_ids()

        # Build fill_color map based on R state
        # Registered -> white-ish (done), Not registered -> gray-ish (needs attention)
        fill_colors = {}
        for region_id in geo.regions.keys():
            is_registered = region_id in current_registered
            if is_registered:
                fill_colors[region_id] = "#f8fafc"  # slate-50 (white-ish, registered)
            else:
                fill_colors[region_id] = "#cbd5e1"  # slate-300 (gray-ish, not registered)

        return input_map(
            "relabeling",
            geo,
            mode="multiple",
            fill_color=fill_colors,
            default_aesthetic={"stroke_color": "#64748b", "stroke_width": 1},
            selected_aesthetic={"stroke_color": "#11203b", "stroke_width": 5},
            hover_highlight={
                "fill_color": "#fef08a",
                "fill_opacity": 0.6,
                "stroke_width": 0,
            },
        )

    @render.text
    def selected_original_ids():
        return "\n".join(input.relabeling())

    @render.text
    def registered_objects_display():
        """Display registered objects with their new IDs."""
        current_rules = relabel_rules()

        if not current_rules:
            return "No objects registered for relabeling."

        lines = []
        # Format: {"new_id": ["old_id1", "old_id2"]}
        for new_id, old_ids in sorted(current_rules.items()):
            old_ids_str = ", ".join(sorted(old_ids))
            lines.append(f"{new_id} ← [{old_ids_str}]")

        return "\n".join(lines)

    @reactive.effect
    @reactive.event(input.register_relabel)
    def handle_register():
        """Handle 1/0 -> 0/1 transition: Register selected objects and clear selection."""
        new_id = input.new_id().strip()
        if not new_id:
            return

        # Get current selection from input map
        current_selected = set(input.relabeling())
        if not current_selected:
            return

        # Update relabel_rules with format: {"new_id": ["old_id1", "old_id2"]}
        current_rules = dict(relabel_rules())
        current_overlay = overlay_ids()

        # First, remove selected IDs from any existing mappings (allow re-registration)
        # Also track which old new_ids need to be removed from overlay_ids
        old_new_ids_to_remove = set()
        for existing_new_id, old_ids in list(current_rules.items()):
            # Remove selected IDs from this mapping
            remaining = [oid for oid in old_ids if oid not in current_selected]
            if remaining:
                current_rules[existing_new_id] = remaining
            else:
                # Remove the mapping entirely if no old IDs remain
                del current_rules[existing_new_id]
                # Track this new_id for removal from overlay_ids
                old_new_ids_to_remove.add(existing_new_id)

        # Now add selected IDs to the new_id mapping
        if new_id in current_rules:
            # Append to existing list (avoid duplicates, though shouldn't be any after removal)
            existing = set(current_rules[new_id])
            current_rules[new_id] = list(existing | current_selected)
        else:
            # Create new list for this new_id
            current_rules[new_id] = list(current_selected)

        relabel_rules.set(current_rules)

        # Update overlay_ids based on target layer
        # Remove old new_ids that no longer have any regions mapped to them
        current_overlay = current_overlay - old_new_ids_to_remove

        # Add or remove new_id from overlay based on target layer
        if input.target_layer() == "Overlay":
            current_overlay = current_overlay | {new_id}
        else:
            # If switching to Interactive, remove from overlay
            current_overlay = current_overlay - {new_id}

        overlay_ids.set(current_overlay)

        # Move from S to R: add to registered
        current_registered = registered_ids()
        registered_ids.set(current_registered | current_selected)

        # Clear selection in the map
        update_map("relabeling", value={})

        # Clear the new_id input for next entry
        ui.update_text("new_id", value="")

    @reactive.effect
    @reactive.event(input.unregister_relabel)
    def handle_unregister():
        """Handle 1/1 -> 0/0 transition: Unregister selected objects and clear selection."""
        # Get current selection from input map
        current_selected = set(input.relabeling())
        current_registered = registered_ids()

        # Only unregister objects that are both selected AND registered (1/1 state)
        to_unregister = current_selected & current_registered

        if not to_unregister:
            return

        # Remove from relabel_rules (format: {"new_id": ["old_id1", "old_id2"]})
        current_rules = dict(relabel_rules())
        current_overlay = overlay_ids()
        updated_rules = {}
        removed_new_ids = set()

        for new_id, old_ids in current_rules.items():
            # Remove unregistered IDs from the list
            remaining = [oid for oid in old_ids if oid not in to_unregister]
            # Only keep the entry if there are still IDs mapped to this new_id
            if remaining:
                updated_rules[new_id] = remaining
            else:
                # Track new_ids that were completely removed
                removed_new_ids.add(new_id)

        relabel_rules.set(updated_rules)

        # Remove from R
        registered_ids.set(current_registered - to_unregister)

        # Remove any overlay IDs that no longer have regions mapped to them
        overlay_ids.set(current_overlay - removed_new_ids)

        # Clear selection in the map
        update_map("relabeling", value={})


## Code Generation Page =====================================================================

panel_gen_code = ui.nav_panel(
    "Generated Code",
    ui.layout_columns(
        ui.TagList(
            ui.h2("JSON"),
            ui.output_text_verbatim("json_preview", placeholder=True),
            ui.input_text("output_filename", "Output JSON filename", value="output.json"),
            ui.download_button("download_json", "Download JSON"),
        ),
        ui.TagList(
            ui.h2("Conversion Code"),
            ui.output_text_verbatim("code_preview"),
            ui.download_button("download_code", "Download Python Code"),
        ),
    ),
)

## Inference Page =====================================================================

panel_infer = ui.nav_panel(
    "Infer from Original",
    ui.p(
        "Upload the original source file (SVG or intermediate JSON) "
        "to generate code that reproduces the current final JSON."
    ),
    ui.p("If no file is uploaded, will use the currently loaded file as the original."),
    ui.input_file(
        "original_file",
        "Choose original SVG or JSON file (optional)",
        accept=[".svg", ".json"],
        multiple=False,
    ),
    ui.output_text_verbatim("inferred_code"),
)


app_ui = ui.page_fillable(
    ui.h1("SVG to shinymap JSON Converter"),
    ui.p(
        "Upload an SVG file, configure the conversion, and download both the JSON output "
        "and the Python code to regenerate it."
    ),
    ui.navset_tab(
        panel_upload,
        panel_relabeling,
        panel_gen_code,
        panel_infer,
    ),
    title="SVG to shinymap JSON Converter",
)


## Server =====================================================================


def server(input, output, session):
    extracted_data = reactive.value()
    file_name = reactive.value()
    relabel_rules = reactive.value({})  # Format: {"new_id": ["old_id1", "old_id2"]}
    registered_ids = reactive.value(set())  # R flag: objects marked for relabeling
    overlay_ids = reactive.value(set())

    if _initial_file is not None:
        cli_data = load_file(str(_initial_file), _initial_file.name)
        extracted_data.set(cli_data)
        file_name.set(_initial_file.name)

    server_file_upload(input, file_name, extracted_data)
    server_relabeling(input, extracted_data, relabel_rules, registered_ids, overlay_ids)

    @render.text
    def path_list():
        """Display list of path IDs found/generated in extracted JSON."""
        data = extracted_data()
        if not data:
            return "No SVG file uploaded yet."

        if "error" in data:
            return f"Error parsing SVG: {data['error']}"

        path_ids = data.get("path_ids", [])
        if not path_ids:
            return "No path elements found in SVG."

        # Count auto-generated IDs
        auto_generated = sum(1 for pid in path_ids if pid.startswith("path_"))

        msg = f"Found {len(path_ids)} paths"
        if auto_generated > 0:
            msg += f" ({auto_generated} auto-generated IDs)"
        msg += ":\n\n"

        return msg + "\n".join(f"  • {pid}" for pid in path_ids)

    def parse_json_input(text: str, default):
        """Parse JSON input, return default on error."""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return default

    @reactive.calc
    def get_conversion_params():
        """Get all conversion parameters."""
        data = extracted_data()
        if not data or "error" in data:
            return None

        metadata = {"source": input.meta_source(), "license": input.meta_license()}
        relabel = relabel_rules()
        _overlay_ids = list(overlay_ids())

        # Filter out empty values
        if not metadata or all(v == "" for v in metadata.values()):
            metadata = None
        if not relabel:
            relabel = None
        if not _overlay_ids:
            _overlay_ids = None

        out = {
            "geometry": data["geometry"],
            "input_filename": data["filename"],
            "output_filename": input.output_filename(),
            "metadata": metadata,
            "relabel": relabel,
            "overlay_ids": _overlay_ids,
        }
        return out

    @reactive.calc
    def get_extracted_geo():
        """Get extracted Outline object."""
        data = extracted_data()
        if not data or "error" in data:
            return None
        return data.get("geometry")

    @reactive.calc
    def get_final_json():
        """Generate the final JSON output by applying transformations."""
        params = get_conversion_params()
        if not params:
            return None

        try:
            # Apply transformations using Outline methods
            geo = params["geometry"]

            # Apply relabeling if specified
            if params["relabel"]:
                geo = geo.relabel(params["relabel"])

            # Set overlays if specified
            if params["overlay_ids"]:
                geo = geo.set_overlays(params["overlay_ids"])

            # Update metadata if specified
            if params["metadata"]:
                geo = geo.update_metadata(params["metadata"])

            return geo.to_dict()
        except Exception as e:
            return {"error": str(e)}

    @render.text
    def json_preview():
        """Preview the final JSON."""
        result = get_final_json()
        if not result:
            return "Upload SVG to preview JSON output."

        if "error" in result:
            return f"Error: {result['error']}"

        return json.dumps(result, indent=2, ensure_ascii=False)

    @render.text
    def code_preview():
        """Preview the generated Python code."""
        params = get_conversion_params()
        if not params:
            return "Upload SVG to preview Python code."

        code = generate_code(
            params["input_filename"],
            params["output_filename"],
            params["relabel"],
            params["overlay_ids"],
            params["metadata"],
        )
        return code

    @render.download(filename=lambda: input.output_filename())
    def download_json():
        """Download the final JSON file."""
        result = get_final_json()
        if not result or "error" in result:
            return ""

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            return f.name

    @render.download(filename=lambda: input.output_filename().replace(".json", ".py"))
    def download_code():
        """Download the generated Python code."""
        params = get_conversion_params()
        if not params:
            return ""

        code = generate_code(
            params["input_filename"],
            params["output_filename"],
            params["relabel"],
            params["overlay_ids"],
            params["metadata"],
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            return f.name

    @render.text
    def inferred_code():
        """Infer code from original source file."""
        # Get final JSON
        final = get_final_json()
        if not final or "error" in final:
            return "Generate final JSON first (configure transformations in other tabs)."

        # Get conversion params for metadata and overlay_ids
        params = get_conversion_params()
        if not params:
            return "Upload a file first."

        # Determine original file
        original_file_info = input.original_file()
        if original_file_info:
            # User uploaded original file
            original_path = original_file_info[0]["datapath"]
            original_filename = original_file_info[0]["name"]
        else:
            # Use currently loaded file as original
            data = extracted_data()
            if not data or "error" in data:
                return "No file loaded."
            original_path = data["file_path"]
            original_filename = data["original_source"]

        # Infer relabel mapping
        try:
            inferred_relabel = infer_relabel(original_path, final)
        except Exception as e:
            return f"Error inferring transformations: {e}"

        # Generate code
        code = generate_code(
            original_filename,
            params["output_filename"],
            inferred_relabel,
            params["overlay_ids"],
            params["metadata"],
        )
        return code


def app_run(initial_file, **kwargs):
    global _initial_file
    _initial_file = initial_file

    app = App(app_ui, server)
    return app.run(**kwargs)
