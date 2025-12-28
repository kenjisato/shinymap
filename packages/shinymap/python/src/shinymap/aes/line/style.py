"""Line style constants for stroke-dasharray patterns.

This module provides pre-defined constants for common stroke-dasharray patterns.
Use these with the aesthetic builders for consistent, readable code.

Usage:
    >>> from shinymap.aes import line
    >>>
    >>> # Dashed line
    >>> grid_aes = aes.Line(stroke_color="#ddd", stroke_dasharray=line.dashed)
    >>>
    >>> # Dotted line
    >>> dotted_aes = aes.Line(stroke_dasharray=line.dotted)
    >>>
    >>> # Custom pattern (just use a string directly)
    >>> custom_aes = aes.Line(stroke_dasharray="10,5,2,5")
"""

from __future__ import annotations

__all__ = ["solid", "dashed", "dotted", "dash_dot"]

# Solid line (no dashing) - represented as None
solid: None = None
"""Solid line (no dashing). This is the default."""

# Common dash patterns
dashed: str = "5,5"
"""Dashed line pattern (5px dash, 5px gap)."""

dotted: str = "1,3"
"""Dotted line pattern (1px dot, 3px gap)."""

dash_dot: str = "5,3,1,3"
"""Dash-dot line pattern (5px dash, 3px gap, 1px dot, 3px gap)."""
