"""Core Shiny for Python bindings for the shinymap renderer."""

from __future__ import annotations

__version__ = "0.3.0-dev"

from . import aes, geometry, types, ui, utils
from ._map import Map
from ._wash import Wash
from .geometry import Outline
from .relative import (
    PARENT,
    AestheticConfig,
    RegionState,
    RelativeExpr,
    preview_region,
    resolve_region,
)

# Re-export from ui for convenience
from .ui import (
    input_checkbox_group,
    input_map,
    input_radio_buttons,
    output_map,
    update_map,
)
from .ui._ui import render_map

__all__ = [
    "__version__",
    "Outline",
    "Map",
    "render_map",
    "input_map",
    "input_radio_buttons",
    "input_checkbox_group",
    "output_map",
    "update_map",
    # Wash factory (watercolor-inspired aesthetic configuration)
    "Wash",
    # Aesthetic module (aes.Shape(), aes.Line(), aes.color, aes.line, aes.default)
    "aes",
    # PARENT proxy and relative expressions
    "PARENT",
    "RelativeExpr",
    # Aesthetic debugging utilities
    "RegionState",
    "AestheticConfig",
    "resolve_region",
    "preview_region",
    # Subpackages
    "geometry",  # Outline utilities
    "types",  # Type definitions (MapBuilder, etc.)
    "ui",  # UI components (input_map, output_map, etc.)
    "utils",  # Utility functions (linspace, path_bb, strip_unit)
]
