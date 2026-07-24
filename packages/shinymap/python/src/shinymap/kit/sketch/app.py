"""Sketch app for interactive SVG relabeling and layer assignment."""

from __future__ import annotations

from pathlib import Path

from shiny import App, reactive, ui

from ...outline import Outline
from ._tab_finish import server_tab_finish, ui_tab_finish
from ._tab_infer import server_tab_infer, ui_tab_infer

# Implementation
from ._tab_original import server_tab_original, ui_tab_original
from ._tab_relabel import server_relabeling, ui_tab_relabeling

# Module-level variable for CLI-provided SVG/JSON file
_initial_file: Path | None = None


# Global variables used throughout the app
class Globals:
    """
    Globals
    =======

    Singleton variable `globals = Globals()` contains (reactive) values that
    are passed around and used throughout the subservers. It has the following
    entries:

    # Reactive Values

    outline: Outline
        Current outline being edited.

    relabel_rules: dict
        Dictionary of ID mapping, "new" from "old"
        Format: {"new_id": ["old_id1", "old_id2"]}

    registered_ids: set[str]
        OLD IDs marked for relabeling. (R flag)

    overlay_ids: set[str]
        OLD IDs assigned to overlay layer.

    underlay_ids: set[str]
        OLD IDs assigned to underlay layer.

    hidden_ids: set[str]
        OLD IDs assigned to hidden layer.

    annotation_ids: set[str]
        OLD IDs assigned to annotation layer.

    metadata_groups: dict[str, list[str]]
        Metadata groups for styling. Format: {"group_name": ["region_id1", "region_id2"]}

    # Static Values

    original_file: Path | None
        Path to the original file (set via property).

    original_outline: Outline | None
        Unmodified original outline.

    initial_file: Path | None
        CLI provided file.

    message: dict
        Error/status messages.
    """

    def __init__(self):
        # Reactive values
        self.relabel_rules = reactive.value({})
        self.registered_ids = reactive.value(set())
        self.outline = reactive.value()

        # Layer assignments (track OLD IDs)
        self.overlay_ids = reactive.value(set())
        self.underlay_ids = reactive.value(set())
        self.hidden_ids = reactive.value(set())
        self.annotation_ids = reactive.value(set())

        # Metadata groups for styling
        self.metadata_groups = reactive.value({})

        self.conversion_params = reactive.value()

        # Static values
        self.__original_file = None
        self.original_outline = None
        self.initial_file: Path | None = None
        self.message = {}

    @property
    def original_file(self):
        return self.__original_file

    @original_file.setter
    def original_file(self, path: Path | str | None):
        # Updating original_file invokes update of the following objects:
        #   - original_outline
        #   - outline (for edits)
        #   - layer assignments (overlay_ids, underlay_ids, hidden_ids, annotation_ids)

        if path:
            path = Path(path)
            if path.suffix.lower() == ".json":
                outline = Outline.from_json(path)
            else:
                outline = Outline.from_svg(path, extract_viewbox=True)
                outline.metadata["original_source"] = path.name

            # Store original outline (with layer metadata intact for display)
            self.original_outline = outline

            # Extract layer assignments from metadata and populate globals
            # Then clear them from working outline so all regions are interactive
            self.overlay_ids.set(set(outline.metadata.get("overlay", [])))
            self.underlay_ids.set(set(outline.metadata.get("underlay", [])))
            self.hidden_ids.set(set(outline.metadata.get("hidden", [])))
            self.annotation_ids.set(set(outline.metadata.get("annotation", [])))

            # Extract metadata groups (for styling)
            original_groups = outline.metadata.get("groups", {})
            if isinstance(original_groups, dict):
                # Convert lists to ensure consistency
                self.metadata_groups.set(
                    {k: list(v) for k, v in original_groups.items() if isinstance(v, (list, tuple))}
                )
            else:
                self.metadata_groups.set({})

            # Create working outline with layer metadata cleared
            # (update_metadata merges, so set to empty lists to override)
            working_outline = outline.update_metadata(
                {
                    "overlay": [],
                    "underlay": [],
                    "hidden": [],
                    "annotation": [],
                }
            )

            self.outline.set(working_outline)

        else:
            # Empty outline
            outline = Outline.from_dict({"_metadata": {"viewBox": "0 0 100 100"}})
            self.original_outline = outline
            self.outline.set(outline)

        self.__original_file = path


## UI =========================================================================
app_ui = ui.page_fillable(
    ui.h1("SVG to shinymap JSON Converter"),
    ui.p(
        "Upload an SVG file, configure the conversion, and download both the JSON output "
        "and the Python code to regenerate it."
    ),
    ui.navset_tab(
        ui_tab_original,
        ui_tab_relabeling,
        ui_tab_finish,
        ui_tab_infer,
    ),
    title="SVG to shinymap JSON Converter",
)


## Server =====================================================================
def server(input, output, session):
    globals = Globals()
    globals.original_file = _initial_file
    globals.initial_file = _initial_file

    server_tab_original(input, globals)
    server_relabeling(input, globals)
    server_tab_finish(input, globals)
    server_tab_infer(input, globals)


def app_run(initial_file: Path | None = None, **kwargs):
    """Run the sketch app.

    Args:
        initial_file: Optional path to SVG/JSON file to pre-load
        **kwargs: Additional arguments passed to App.run()
    """
    global _initial_file
    _initial_file = initial_file

    app = App(app_ui, server)
    return app.run(**kwargs)
