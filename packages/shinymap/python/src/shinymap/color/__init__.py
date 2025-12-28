"""Color palettes and scale utilities for shinymap.

This subpackage provides:
- Pre-defined color palettes for different use cases
- Color scale functions for mapping data to colors

Palette Categories:
    - neutral: Default/fallback colors
    - qualitative: Distinct colors for categorical data
    - sequential: Ordered palettes for count/continuous data
    - binary: Two-state palettes for Single/Multiple modes
    - cycle: Multi-state palettes for Cycle mode

Scale Functions:
    - scale_sequential: Map counts to sequential colors
    - scale_diverging: Map values to diverging colors (red-white-blue)
    - scale_qualitative: Map categories to distinct colors
    - lerp_hex: Interpolate between two hex colors

Usage:
    >>> from shinymap.color import SEQUENTIAL_BLUE, scale_sequential
    >>> from shinymap.color import HUE_CYCLE_4, BINARY_TOGGLE
"""

from __future__ import annotations

# Neutral colors
from .neutral import NEUTRALS

# Qualitative palette
from .qualitative import QUALITATIVE

# Sequential palettes
from .sequential import SEQUENTIAL_BLUE, SEQUENTIAL_GREEN, SEQUENTIAL_ORANGE

# Binary (two-state) palettes
from .binary import BINARY_GREEN, BINARY_RED, BINARY_TOGGLE

# Cycle mode palettes
from .cycle import HUE_CYCLE_4, LIKERT_5, PRIORITY_5, SENTIMENT_3

# Scale functions
from .scale import lerp_hex, scale_diverging, scale_qualitative, scale_sequential

__all__ = [
    # Neutral
    "NEUTRALS",
    # Qualitative
    "QUALITATIVE",
    # Sequential
    "SEQUENTIAL_BLUE",
    "SEQUENTIAL_GREEN",
    "SEQUENTIAL_ORANGE",
    # Binary
    "BINARY_TOGGLE",
    "BINARY_GREEN",
    "BINARY_RED",
    # Cycle
    "HUE_CYCLE_4",
    "SENTIMENT_3",
    "PRIORITY_5",
    "LIKERT_5",
    # Scale functions
    "lerp_hex",
    "scale_sequential",
    "scale_diverging",
    "scale_qualitative",
]
