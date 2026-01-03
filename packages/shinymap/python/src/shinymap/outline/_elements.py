"""Shinymap SVG element classes (extends svg.py with bounds/JSON support).

This module provides shinymap-enhanced versions of svg.py element classes.
Each class inherits from both svg.py's element class and ShinymapElementMixin,
providing:

1. All svg.py functionality (construction, rendering, attributes)
2. bounds() method for bounding box calculation
3. to_dict()/from_dict() for JSON serialization

Important note on aesthetics:
    These classes preserve SVG aesthetic attributes (fill, stroke, font_size, etc.)
    from the original SVG, but shinymap does NOT use these for rendering.
    Interactive aesthetics are controlled via Python API (default_aesthetic,
    with_fill_color(), etc.). Preserved values are for SVG export and reference only.

Example:
    >>> from shinymap.outline import Circle
    >>> circle = Circle(cx=100, cy=100, r=50, fill="#ff0000")
    >>> circle.bounds()
    (50.0, 50.0, 150.0, 150.0)
    >>> circle.to_dict()
    {'type': 'circle', 'cx': 100, 'cy': 100, 'r': 50, 'fill': '#ff0000'}
    >>> str(circle)  # SVG rendering from svg.py
    '<circle cx="100" cy="100" r="50" fill="#ff0000"/>'
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import svg

from ._element_mixins import ShinymapElementMixin

if TYPE_CHECKING:
    pass


@dataclass
class Circle(svg.Circle, ShinymapElementMixin):
    """Circle element with bounds calculation and JSON serialization.

    Inherits all attributes from svg.Circle:
        cx: Center x coordinate
        cy: Center y coordinate
        r: Radius
        fill: Fill color (preserved but not used by shinymap)
        stroke: Stroke color (preserved but not used by shinymap)
        stroke_width: Stroke width (preserved but not used by shinymap)
        ... and all other svg.Circle attributes

    Note:
        Aesthetic attributes (fill, stroke, etc.) are preserved from SVG
        but NOT used by shinymap for rendering. Use Python API parameters
        (default_aesthetic, with_fill_color(), etc.) to control appearance.

    Examples:
        ```pycon
        >>> circle = Circle(cx=100, cy=100, r=50)
        >>> circle.bounds()
        (50.0, 50.0, 150.0, 150.0)
        ```
    """

    def __repr__(self) -> str:
        """Return clean repr showing only non-None attributes."""
        return ShinymapElementMixin.__repr__(self)


@dataclass
class Rect(svg.Rect, ShinymapElementMixin):
    """Rectangle element with bounds calculation and JSON serialization.

    Inherits all attributes from svg.Rect:
        x: Top-left x coordinate
        y: Top-left y coordinate
        width: Rectangle width
        height: Rectangle height
        rx: Horizontal corner radius (optional)
        ry: Vertical corner radius (optional)
        fill: Fill color (preserved but not used by shinymap)
        stroke: Stroke color (preserved but not used by shinymap)
        ... and all other svg.Rect attributes

    Examples:
        ```pycon
        >>> rect = Rect(x=10, y=20, width=100, height=80)
        >>> rect.bounds()
        (10.0, 20.0, 110.0, 100.0)
        ```
    """

    def __repr__(self) -> str:
        """Return clean repr showing only non-None attributes."""
        return ShinymapElementMixin.__repr__(self)


@dataclass
class Path(svg.Path, ShinymapElementMixin):
    """Path element with bounds calculation and JSON serialization.

    Inherits all attributes from svg.Path:
        d: Path data (accepts string or list[PathData])
        fill: Fill color (preserved but not used by shinymap)
        stroke: Stroke color (preserved but not used by shinymap)
        ... and all other svg.Path attributes

    Note:
        Path data can be specified as either:
        1. String: "M 0 0 L 100 0 L 100 100 Z"
        2. List of PathData objects: [M(0, 0), L(100, 0), L(100, 100), Z()]

        Internally, svg.py uses PathData objects. When serializing to JSON,
        these are converted to strings.

    Examples:
        ```pycon
        >>> path = Path(d="M 0 0 L 100 0 L 100 100 Z")
        >>> path.bounds()
        (0.0, 0.0, 100.0, 100.0)
        
        >>> from svg._path import M, L, Z
        >>> path = Path(d=[M(0, 0), L(100, 0), L(100, 100), Z()])
        >>> path.bounds()
        (0.0, 0.0, 100.0, 100.0)
        ```
    """

    def __repr__(self) -> str:
        """Return clean repr showing only non-None attributes."""
        return ShinymapElementMixin.__repr__(self)


@dataclass
class Polygon(svg.Polygon, ShinymapElementMixin):
    """Polygon element with bounds calculation and JSON serialization.

    Inherits all attributes from svg.Polygon:
        points: List of coordinates [x1, y1, x2, y2, ...]
        fill: Fill color (preserved but not used by shinymap)
        stroke: Stroke color (preserved but not used by shinymap)
        ... and all other svg.Polygon attributes

    Examples:
        ```pycon
        >>> polygon = Polygon(points=[0, 0, 100, 0, 100, 100, 0, 100])
        >>> polygon.bounds()
        (0.0, 0.0, 100.0, 100.0)
        ```
    """

    def __repr__(self) -> str:
        """Return clean repr showing only non-None attributes."""
        return ShinymapElementMixin.__repr__(self)


@dataclass
class Ellipse(svg.Ellipse, ShinymapElementMixin):
    """Ellipse element with bounds calculation and JSON serialization.

    Inherits all attributes from svg.Ellipse:
        cx: Center x coordinate
        cy: Center y coordinate
        rx: Horizontal radius
        ry: Vertical radius
        fill: Fill color (preserved but not used by shinymap)
        stroke: Stroke color (preserved but not used by shinymap)
        ... and all other svg.Ellipse attributes

    Examples:
        ```pycon
        >>> ellipse = Ellipse(cx=100, cy=100, rx=50, ry=30)
        >>> ellipse.bounds()
        (50.0, 70.0, 150.0, 130.0)
        ```
    """

    def __repr__(self) -> str:
        """Return clean repr showing only non-None attributes."""
        return ShinymapElementMixin.__repr__(self)


@dataclass
class Line(svg.Line, ShinymapElementMixin):
    """Line element with bounds calculation and JSON serialization.

    Inherits all attributes from svg.Line:
        x1: Start x coordinate
        y1: Start y coordinate
        x2: End x coordinate
        y2: End y coordinate
        stroke: Stroke color (preserved but not used by shinymap)
        stroke_width: Stroke width (preserved but not used by shinymap)
        ... and all other svg.Line attributes

    Examples:
        ```pycon
        >>> line = Line(x1=0, y1=0, x2=100, y2=100)
        >>> line.bounds()
        (0.0, 0.0, 100.0, 100.0)
        ```
    """

    def __repr__(self) -> str:
        """Return clean repr showing only non-None attributes."""
        return ShinymapElementMixin.__repr__(self)


@dataclass
class Text(svg.Text, ShinymapElementMixin):
    """Text element with bounds calculation and JSON serialization.

    Inherits all attributes from svg.Text:
        x: Text anchor x coordinate
        y: Text anchor y coordinate
        text: Text content (via Element.text field)
        font_size: Font size (preserved but not used by shinymap)
        font_family: Font family (preserved but not used by shinymap)
        fill: Text color (preserved but not used by shinymap)
        ... and all other svg.Text attributes

    Note:
        Bounds calculation for text is approximate (position only).
        True text bounds require font metrics which are not available
        without a text layout engine. This is sufficient for annotation
        layers but not for precise interactive text regions.

    Examples:
        ```pycon
        >>> text = Text(x=100, y=100, text="Hello")
        >>> text.bounds()  # Approximate bounds
        (100.0, 100.0, 101.0, 101.0)
        ```
    """

    def __repr__(self) -> str:
        """Return clean repr showing only non-None attributes."""
        return ShinymapElementMixin.__repr__(self)


# Type union for all supported elements
Element = Circle | Rect | Path | Polygon | Ellipse | Line | Text

# Map type string to class (for from_dict deserialization)
ELEMENT_TYPE_MAP: dict[str, type[Circle | Rect | Path | Polygon | Ellipse | Line | Text]] = {
    "circle": Circle,
    "rect": Rect,
    "path": Path,
    "polygon": Polygon,
    "ellipse": Ellipse,
    "line": Line,
    "text": Text,
}

__all__ = [
    "Circle",
    "Rect",
    "Path",
    "Polygon",
    "Ellipse",
    "Line",
    "Text",
    "Element",
    "ELEMENT_TYPE_MAP",
]
