"""Core Shiny for Python bindings for the shinymap renderer."""

from __future__ import annotations

__version__ = "0.3.0-dev"

from . import aes, color, geometry, linestyle
from ._aesthetics import BaseAesthetic
from ._sentinel import MISSING, MissingType
from ._theme import configure_theme
from ._ui import (
    Map,
    MapBuilder,
    input_checkbox_group,
    input_map,
    input_radio_buttons,
    output_map,
    render_map,
    update_map,
)
from ._wash import WashConfig, WashResult, wash
from .relative import (
    DEFAULT_HOVER_AESTHETIC,
    DEFAULT_LINE_AESTHETIC,
    DEFAULT_SHAPE_AESTHETIC,
    DEFAULT_TEXT_AESTHETIC,
    PARENT,
    AestheticConfig,
    RegionState,
    RelativeExpr,
    preview_region,
    resolve_region,
)

__all__ = [
    "__version__",
    "MISSING",
    "MissingType",
    "Map",
    "MapBuilder",
    "input_map",
    "input_radio_buttons",
    "input_checkbox_group",
    "output_map",
    "render_map",
    "update_map",
    # Theme configuration (deprecated, use wash() instead)
    "configure_theme",
    # Wash factory (watercolor-inspired aesthetic configuration)
    "wash",
    "WashResult",
    "WashConfig",
    # Aesthetic builders (IDE-friendly)
    "aes",  # Module: aes.Shape(), aes.Line(), aes.Text()
    "linestyle",  # Module: linestyle.DASHED, linestyle.DOTTED, etc.
    "BaseAesthetic",  # Base class for type hints in function signatures
    # PARENT proxy and relative expressions
    "PARENT",
    "RelativeExpr",
    # Default aesthetics
    "DEFAULT_SHAPE_AESTHETIC",
    "DEFAULT_LINE_AESTHETIC",
    "DEFAULT_TEXT_AESTHETIC",
    "DEFAULT_HOVER_AESTHETIC",
    # Aesthetic debugging utilities
    "RegionState",
    "AestheticConfig",
    "resolve_region",
    "preview_region",
    # Subpackages
    "color",  # Color palettes and scale functions
    "geometry",  # Geometry creation utilities
]
