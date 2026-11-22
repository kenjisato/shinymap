"""Aesthetic module for shinymap.

This module provides:
- Factory functions for creating aesthetics: Shape(), Line(), Text(), Path(), Indexed()
- Grouping classes: ByState, ByGroup, ByType
- Submodules: color, line, default

Usage:
    from shinymap import aes

    # Create aesthetics
    shape_aes = aes.Shape(fill_color="#3b82f6")
    line_aes = aes.Line(stroke_dasharray=aes.line.dashed)

    # Use defaults
    base_shape = aes.default.shape

    # Use color scales
    fills = aes.color.scale_sequential(counts, region_ids)
"""

from __future__ import annotations

from . import _defaults as default

# Submodules
from . import color, line

# Factory functions
from ._factory import (
    ByGroup,
    ByState,
    ByType,
    Indexed,
    Line,
    Path,
    Shape,
    Text,
)

__all__ = [
    # Factory functions
    "Line",
    "Shape",
    "Text",
    "Path",
    "Indexed",
    # Grouping classes
    "ByState",
    "ByType",
    "ByGroup",
    # Submodules
    "color",
    "line",
    "default",
]
