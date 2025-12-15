"""Interactive SVG to shinymap JSON converter.

Usage:
    uv run python -m shinymap.geometry.converter [options]
    python -m shinymap.geometry.converter [options]

Options:
    -H, --host TEXT           Bind socket to this host (default: 127.0.0.1)
    -p, --port INTEGER        Bind socket to this port (default: 8000)
    -b, --launch-browser      Launch browser after starting server
    -f, --file PATH           Path to SVG or JSON file to pre-load

Examples:
    # Run on default host/port
    uv run python -m shinymap.geometry.converter

    # Run on custom port and open browser
    uv run python -m shinymap.geometry.converter -p 9000 -b

    # Pre-load an SVG file
    uv run python -m shinymap.geometry.converter -f path/to/file.svg -b

    # Pre-load intermediate JSON
    uv run python -m shinymap.geometry.converter -f intermediate.json -b

    # Bind to all interfaces
    uv run python -m shinymap.geometry.converter -H 0.0.0.0 -p 8080
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from shiny import App, reactive, render, ui, req

from .._core import compute_viewbox_from_dict, from_json, infer_relabel
from ..._ui import render_map, input_map, update_map
from ..._theme import configure_theme
from ... import Map
from ._tool import generate_code, load_file

# Module-level variable for CLI-provided SVG/JSON file
_cli_file_path: Path | None


configure_theme(
    selected_aesthetic={"fill_color": "#ffffcc"},
    hover_highlight={"stroke_width": 8}
)

## Upload File =====================================================================

panel_upload = ui.nav_panel(
    "Upload",
    ui.h2("Upload File"),

    ui.layout_columns(
        ui.TagList(
            ui.input_file(
                "path_file", 
                "Choose SVG or JSON file", 
                accept=[".svg", ".json"], 
                multiple=False, 
            ),
            ui.output_text("path_file_name"),
            ui.input_text("meta_source", "Source"),
            ui.input_text("meta_license", "License")
        ),
        ui.TagList(
            ui.help_text("Path IDs"),
            ui.output_text_verbatim("path_list", placeholder=True),
        ),
        col_widths=(4, 8),
    )
)

def server_file_upload(input, file_name, intermediate_json):

    @reactive.effect
    @reactive.event(input.path_file)
    def parse_uploaded_svg():
        """Parse uploaded SVG or JSON file."""
        file_info = input.path_file()
        if not file_info:
            intermediate_json.set(None)
            return

        # Read the uploaded file
        file_path = file_info[0]["datapath"]
        file_name.set(file_info[0]["name"])

        try:
            intermediate_json.set(load_file(file_path, file_name()))
        except Exception as e:
            intermediate_json.set({"error": str(e)})

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
                ui.TagList(
                    ui.help_text("New ID"),
                    ui.input_text("new_id", ""),
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
        )
    )
)

def server_relabeling(input, intermediate_json, relabel_rules, registered_ids):
    @render.ui
    def map_relabeling():
        """Preview the intermediate geometry with state-based styling."""
        data = intermediate_json.get()
        if not data or "error" in data:
            return ui.p("Invalid data")

        # Get intermediate JSON (list-based path format)
        intermediate = data.get("intermediate", {})

        # Extract geometry (skip metadata) - keep list format
        geometry = {k: v for k, v in intermediate.items() if isinstance(v, list)}

        if not geometry:
            return ui.p("Invalid data")

        # Compute viewBox directly from intermediate dict
        # First check if metadata contains viewBox
        metadata = intermediate.get("_metadata", {})
        if isinstance(metadata, dict) and "viewBox" in metadata:
            view_box = metadata["viewBox"]
        else:
            # Compute viewBox from geometry with 2% padding
            view_box = compute_viewbox_from_dict(intermediate, padding=0.02)

        # Get current R (registered) state
        current_registered = registered_ids.get()

        # Build fill_color map based on R state
        # Registered -> white-ish (done), Not registered -> gray-ish (needs attention)
        fill_colors = {}
        for region_id in geometry.keys():
            is_registered = region_id in current_registered
            if is_registered:
                fill_colors[region_id] = "#f8fafc"  # slate-50 (white-ish, registered)
            else:
                fill_colors[region_id] = "#cbd5e1"  # slate-300 (gray-ish, not registered)

        return input_map(
            "relabeling",
            geometry,
            mode="multiple",
            view_box=view_box,
            fill_color=fill_colors,
            default_aesthetic={"stroke_color": "#64748b", "stroke_width": 1},  # slate-500
            selected_aesthetic={"stroke_color": "#0f172a", "stroke_width": 3},  # slate-900, thick
            hover_highlight={"fill_color": "#fef08a", "stroke_width": 0}  # yellow-200, no stroke
        )

    @render.text
    def selected_original_ids():
        return "\n".join(input.relabelling())

    @render.text
    def registered_objects_display():
        """Display registered objects with their new IDs."""
        current_rules = relabel_rules.get()

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
        current_rules = dict(relabel_rules.get())

        # Add selected IDs to the list for this new_id
        if new_id in current_rules:
            # Append to existing list (avoid duplicates)
            existing = set(current_rules[new_id])
            current_rules[new_id] = list(existing | current_selected)
        else:
            # Create new list for this new_id
            current_rules[new_id] = list(current_selected)

        relabel_rules.set(current_rules)

        # Move from S to R: add to registered
        current_registered = registered_ids.get()
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
        current_registered = registered_ids.get()

        # Only unregister objects that are both selected AND registered (1/1 state)
        to_unregister = current_selected & current_registered

        if not to_unregister:
            return

        # Remove from relabel_rules (format: {"new_id": ["old_id1", "old_id2"]})
        current_rules = dict(relabel_rules.get())
        updated_rules = {}

        for new_id, old_ids in current_rules.items():
            # Remove unregistered IDs from the list
            remaining = [oid for oid in old_ids if oid not in to_unregister]
            # Only keep the entry if there are still IDs mapped to this new_id
            if remaining:
                updated_rules[new_id] = remaining

        relabel_rules.set(updated_rules)

        # Remove from R
        registered_ids.set(current_registered - to_unregister)

        # Clear selection in the map
        update_map("relabeling", value={})

## Inference Page =====================================================================

panel_infer = ui.nav_panel(
    "Infer from Original",
    ui.p("Upload the original source file (SVG or intermediate JSON) to generate code that reproduces the current final JSON."),
    ui.p("If no file is uploaded, will use the currently loaded file as the original."),
    ui.input_file("original_file", "Choose original SVG or JSON file (optional)", accept=[".svg", ".json"], multiple=False),
    ui.output_text_verbatim("inferred_code"),
)

panel_gen_json = ui.nav_panel(
    "Generated JSON",
    ui.output_text_verbatim("json_"),
    ui.input_text("output_filename", "Output JSON filename", value="output.json"),
    ui.download_button("download_json", "Download JSON"),
)

panel_gen_code = ui.nav_panel(
    "Generated Code",
    ui.output_text_verbatim("code_"),
    ui.download_button("download_code", "Download Python Code"),
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
        panel_gen_json,
        panel_gen_code,
        panel_infer,
    ),
    title="SVG to shinymap JSON Converter",
)

    

## Server =====================================================================

def server(input, output, session):

    intermediate_json = reactive.value()
    file_name = reactive.value()
    relabel_rules = reactive.value({})  # Format: {"new_id": ["old_id1", "old_id2"]}
    registered_ids = reactive.value(set())  # R flag: objects marked for relabeling
    
    if _cli_file_path is not None:
        cli_json = load_file(str(_cli_file_path), _cli_file_path.name)
        intermediate_json.set(cli_json)
        file_name.set(_cli_file_path.name)
    
    server_file_upload(input, file_name, intermediate_json)
    server_relabeling(input, intermediate_json, relabel_rules, registered_ids)

    @render.text
    def path_list():
        """Display list of path IDs found/generated in intermediate JSON."""
        data = intermediate_json.get()
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
        except:
            return default

    @reactive.calc
    def get_conversion_params():
        """Get all conversion parameters."""
        data = intermediate_json.get()
        if not data or "error" in data:
            return None

        metadata = {"source": input.meta_source(), "license": input.meta_license()}
        relabel = relabel_rules()
        overlay_ids = parse_json_input(input.overlay_ids_json(), [])

        # Filter out empty values
        if not metadata or all(v == "" for v in metadata.values()):
            metadata = None
        if not relabel:
            relabel = None
        if not overlay_ids:
            overlay_ids = None

        return {
            "intermediate": data["intermediate"],
            "input_filename": data["filename"],
            "output_filename": input.output_filename(),
            "metadata": metadata,
            "relabel": relabel,
            "overlay_ids": overlay_ids,
        }

    @reactive.calc
    def get_intermediate_json():
        """Get intermediate JSON for preview."""
        data = intermediate_json.get()
        if not data or "error" in data:
            return None
        return data.get("intermediate")

    @reactive.calc
    def get_final_json():
        """Generate the final JSON output by applying transformations."""
        params = get_conversion_params()
        if not params:
            return None

        try:
            # Apply transformations to intermediate JSON
            result = from_json(
                params["intermediate"],
                output_path=None,  # Don't write to file
                relabel=params["relabel"],
                overlay_ids=params["overlay_ids"],
                metadata=params["metadata"],
            )
            return result
        except Exception as e:
            return {"error": str(e)}

    @output
    @render.text
    def json_preview():
        """Preview the final JSON."""
        result = get_final_json()
        if not result:
            return "Upload SVG to preview JSON output."

        if "error" in result:
            return f"Error: {result['error']}"

        return json.dumps(result, indent=2, ensure_ascii=False)

    @output
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
            data = intermediate_json.get()
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


app = App(app_ui, server)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Interactive SVG to shinymap JSON converter",
        prog="python -m shinymap.geometry.converter",
    )
    parser.add_argument(
        "-H",
        "--host",
        default="127.0.0.1",
        help="Bind socket to this host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Bind socket to this port (default: 8000)",
    )
    parser.add_argument(
        "-b",
        "--launch-browser",
        action="store_true",
        help="Launch browser after starting server",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Path to SVG or JSON file to pre-load",
    )

    args = parser.parse_args()

    # Set module-level variable for CLI-provided file
    _cli_file_path = Path(args.file) if args.file else None
    if isinstance(_cli_file_path, Path) and not _cli_file_path.exists():
        raise FileNotFoundError(f"{_cli_file_path}")

    app.run(host=args.host, port=args.port, launch_browser=args.launch_browser)