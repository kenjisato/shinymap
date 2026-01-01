"""Core UI module for shinymap.

This module provides the core UI functions without pre-initialized defaults.
Use the `ui` module for the public API with sensible defaults.

Exports:
    Wash: Factory for creating configured map functions with custom aesthetics
    WashResult: Object returned by Wash() with input_map, output_map, render_map methods
    WashConfig: Configuration dataclass used by WashResult
    update_map: Function to update map components without full re-render
"""

from ._update_map import update_map
from ._wash import Wash, WashConfig, WashResult

__all__ = [
    "Wash",
    "WashResult",
    "WashConfig",
    "update_map",
]
