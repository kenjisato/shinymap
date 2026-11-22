"""Default aesthetic values for shinymap.

These defaults match the JavaScript DEFAULT_AESTHETIC_VALUES and provide
sensible starting points for map styling.
"""

from __future__ import annotations

from ..relative import RelativeExpr
from ._core import LineAesthetic, ShapeAesthetic, TextAesthetic

# Default aesthetic values by type (matches JavaScript DEFAULT_AESTHETIC_VALUES)
shape = ShapeAesthetic(
    fill_color="#e2e8f0",
    fill_opacity=1.0,
    stroke_color="#334155",
    stroke_width=1.0,
    stroke_dasharray="",
    non_scaling_stroke=True,
)

line = LineAesthetic(
    stroke_color="#334155",
    stroke_width=1.0,
    stroke_dasharray="",
    non_scaling_stroke=True,
)

text = TextAesthetic(
    fill_color="#334155",
    fill_opacity=1.0,
    stroke_color=None,
    stroke_width=None,
    stroke_dasharray=None,
    non_scaling_stroke=True,
)

# Default hover aesthetic (PARENT.stroke_width + 1)
hover = ShapeAesthetic(
    stroke_width=RelativeExpr("stroke_width", "+", 1.0),
)

__all__ = ["shape", "line", "text", "hover"]
