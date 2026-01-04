"""SVG element classes extending svg.py with shinymap functionality.

This subpackage provides shinymap-enhanced versions of svg.py element classes
that add:
- bounds() method for bounding box calculation
- to_dict()/from_dict() for JSON serialization

Usage:
    >>> from shinymap import svg
    >>> circle = svg.Circle(cx=100, cy=100, r=50)
    >>> circle.bounds()
    (50.0, 50.0, 150.0, 150.0)

    Or with direct imports:
    >>> from shinymap.svg import Circle, Path, Line
    >>> path = Path(d="M 0 0 L 100 100")
"""

from __future__ import annotations

from ._elements import (
    ELEMENT_TYPE_MAP,
    Circle,
    Element,
    Ellipse,
    Line,
    Path,
    Polygon,
    Rect,
    Text,
)

__all__ = [
    "Circle",
    "Ellipse",
    "Line",
    "Path",
    "Polygon",
    "Rect",
    "Text",
    "Element",
    "ELEMENT_TYPE_MAP",
]
