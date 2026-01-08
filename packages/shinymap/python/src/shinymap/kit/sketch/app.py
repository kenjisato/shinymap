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
    are passed around and used thoughout the subservers. It has the following
    entries:

    # Reactive Values

    file_name: str
        File name of the source image/file.

    extracted_data: Outline
        Intermediate representation of the map.

    relabel_rules: dict
        Dictionary of ID mapping, "new" from "old"
        Format: {"new_id": ["old_id1", "old_id2"]}

    registered_ids: list[str]
        Objects marked for relabeling. (R flag)

    overlay_ids: list[str]
        List of overlay ids ? (Really need this? )

    # Static Values

    initial_file: Path | None
        CLI provided file


    """

    def __init__(self):
        # Reactive values
        self.relabel_rules = reactive.value({})
        self.registered_ids = reactive.value(set())
        self.outline = reactive.value()

        self.overlay_ids = reactive.value(set())
        self.underlay_ids = reactive.value(set())
        self.hidden_ids = reactive.value(set())

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

        if path:
            path = Path(path)
            if path.suffix.lower() == ".json":
                outline = Outline.from_json(path)
            else:
                outline = Outline.from_svg(path, extract_viewbox=True)
                outline.metadata["original_source"] = path.name

            self.outline.set(outline)

        else:
            # Empty outline
            outline = Outline.from_dict({"_metadata": {"viewBox": "0 0 100 100"}})

        self.__original_file = path
        self.original_outline = outline


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
