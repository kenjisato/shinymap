"""Line style constants for stroke-dasharray patterns.

Usage:
    from shinymap.aes import line

    grid_aes = aes.Line(stroke_dasharray=line.dashed)
"""

from __future__ import annotations

from .style import dash_dot, dashed, dotted, solid

__all__ = ["solid", "dashed", "dotted", "dash_dot"]
