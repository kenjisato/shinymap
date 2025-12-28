"""Line style constants for stroke-dasharray patterns.

This module provides pre-defined constants for common stroke-dasharray patterns.
Use these with the aesthetic builders for consistent, readable code.

Usage:
    >>> from shinymap import aes, linestyle
    >>>
    >>> # Dashed line
    >>> grid_aes = aes.Line(stroke_color="#ddd", stroke_dasharray=linestyle.DASHED)
    >>>
    >>> # Dotted line
    >>> dotted_aes = aes.Line(stroke_dasharray=linestyle.DOTTED)
    >>>
    >>> # Custom pattern (just use a string directly)
    >>> custom_aes = aes.Line(stroke_dasharray="10,5,2,5")
"""

from __future__ import annotations

__all__ = ["SOLID", "DASHED", "DOTTED", "DASH_DOT"]

# Solid line (no dashing) - represented as None
SOLID: None = None
"""Solid line (no dashing). This is the default."""

# Common dash patterns
DASHED: str = "5,5"
"""Dashed line pattern (5px dash, 5px gap)."""

DOTTED: str = "1,3"
"""Dotted line pattern (1px dot, 3px gap)."""

DASH_DOT: str = "5,3,1,3"
"""Dash-dot line pattern (5px dash, 3px gap, 1px dot, 3px gap)."""
