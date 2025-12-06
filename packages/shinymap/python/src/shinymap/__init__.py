__version__ = "0.0.1"

"""Core Shiny for Python bindings for the shinymap renderer."""

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
from ._ui import Map, MapBuilder, MapPayload, input_map, output_map, render_map

__all__ = [
    "__version__",
    "Map",
    "MapBuilder",
    "MapPayload",
    "input_map",
    "output_map",
    "render_map",
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
]
