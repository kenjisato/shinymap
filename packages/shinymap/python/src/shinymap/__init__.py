"""Core Shiny for Python bindings for the shinymap renderer."""

from __future__ import annotations

__version__ = "0.0.1"

from ._colors import (
    NEUTRALS,
    QUALITATIVE,
    SEQUENTIAL_BLUE,
    SEQUENTIAL_GREEN,
    SEQUENTIAL_ORANGE,
    lerp_hex,
    scale_diverging,
    scale_qualitative,
    scale_sequential,
)
from . import geometry
from ._ui import (
    Map,
    MapBuilder,
    MapCount,
    MapCountBuilder,
    MapPayload,
    MapSelection,
    MapSelectionBuilder,
    input_map,
    output_map,
    render_map,
    update_map,
)

__all__ = [
    "__version__",
    "Map",
    "MapBuilder",
    "MapSelection",
    "MapSelectionBuilder",
    "MapCount",
    "MapCountBuilder",
    "MapPayload",
    "input_map",
    "output_map",
    "render_map",
    "update_map",
    # Color utilities
    "NEUTRALS",
    "QUALITATIVE",
    "SEQUENTIAL_BLUE",
    "SEQUENTIAL_GREEN",
    "SEQUENTIAL_ORANGE",
    "lerp_hex",
    "scale_sequential",
    "scale_diverging",
    "scale_qualitative",
    # Geometry subpackage
    "geometry",
]
