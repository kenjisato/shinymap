"""Mixins to extend svg.py elements with shinymap-specific functionality.

This module provides mixins that add bounds calculation and JSON serialization
to svg.py element classes. These mixins are designed to be used with multiple
inheritance alongside svg.py's element classes.

Key design decisions:
1. Bounds calculation ignores transforms (returns local coordinate bounds)
2. PathData objects are kept in svg.py's native format internally
3. Text bounds are approximate (position only, no font metrics)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass
class BoundsMixin:
    """Adds bounds() method to SVG elements.

    This mixin provides bounding box calculation for all supported SVG element types.
    Bounds are calculated in the element's local coordinate system (transforms are ignored).

    For accurate curve bounds in Path elements, install svgpathtools as an optional dependency.
    Without it, curve bounds are approximated using coordinate endpoints only.
    """

    def bounds(self) -> tuple[float, float, float, float]:
        """Calculate element bounding box in local coordinates.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y)

        Note:
            Does NOT apply transforms. Returns bounds in element's local coordinate system.

        Raises:
            NotImplementedError: If bounds calculation is not implemented for element type
        """
        # Import here to avoid circular dependency and runtime overhead
        import svg

        # Dispatch based on element type
        if isinstance(self, svg.Circle):
            return self._bounds_circle()
        elif isinstance(self, svg.Rect):
            return self._bounds_rect()
        elif isinstance(self, svg.Path):
            return self._bounds_path()
        elif isinstance(self, svg.Polygon):
            return self._bounds_polygon()
        elif isinstance(self, svg.Ellipse):
            return self._bounds_ellipse()
        elif isinstance(self, svg.Line):
            return self._bounds_line()
        elif isinstance(self, svg.Text):
            return self._bounds_text()
        else:
            raise NotImplementedError(
                f"Bounds calculation not implemented for {type(self).__name__}"
            )

    def _bounds_circle(self) -> tuple[float, float, float, float]:
        """Calculate bounds for circle element."""
        cx = float(self.cx or 0)  # type: ignore
        cy = float(self.cy or 0)  # type: ignore
        r = float(self.r or 0)  # type: ignore
        return (cx - r, cy - r, cx + r, cy + r)

    def _bounds_rect(self) -> tuple[float, float, float, float]:
        """Calculate bounds for rect element."""
        x = float(self.x or 0)  # type: ignore
        y = float(self.y or 0)  # type: ignore
        w = float(self.width or 0)  # type: ignore
        h = float(self.height or 0)  # type: ignore
        return (x, y, x + w, y + h)

    def _bounds_path(self) -> tuple[float, float, float, float]:
        """Calculate bounds for path element.

        Uses path_bb from utils for compatibility.
        Converts svg.py's PathData objects to string first.
        """
        from ..utils import path_bb

        if self.d is None:  # type: ignore
            return (0.0, 0.0, 0.0, 0.0)

        # Convert PathData list to string
        # svg.py's PathData objects have __str__ method that returns valid SVG path syntax
        if isinstance(self.d, str):  # type: ignore
            # Already a string (backward compatibility)
            path_str = self.d  # type: ignore
        else:
            # List of PathData objects
            path_str = " ".join(str(cmd) for cmd in self.d)  # type: ignore

        return path_bb(path_str)

    def _bounds_polygon(self) -> tuple[float, float, float, float]:
        """Calculate bounds for polygon element."""
        if not self.points:  # type: ignore
            return (0.0, 0.0, 0.0, 0.0)

        points = self.points  # type: ignore

        # svg.py stores points as list[Number]
        if len(points) < 2:
            return (0.0, 0.0, 0.0, 0.0)

        x_coords = [float(points[i]) for i in range(0, len(points), 2)]
        y_coords = [float(points[i]) for i in range(1, len(points), 2)]

        if not x_coords or not y_coords:
            return (0.0, 0.0, 0.0, 0.0)

        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def _bounds_ellipse(self) -> tuple[float, float, float, float]:
        """Calculate bounds for ellipse element."""
        cx = float(self.cx or 0)  # type: ignore
        cy = float(self.cy or 0)  # type: ignore
        rx = float(self.rx or 0)  # type: ignore
        ry = float(self.ry or 0)  # type: ignore
        return (cx - rx, cy - ry, cx + rx, cy + ry)

    def _bounds_line(self) -> tuple[float, float, float, float]:
        """Calculate bounds for line element."""
        x1 = float(self.x1 or 0)  # type: ignore
        y1 = float(self.y1 or 0)  # type: ignore
        x2 = float(self.x2 or 0)  # type: ignore
        y2 = float(self.y2 or 0)  # type: ignore

        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)

        return (min_x, min_y, max_x, max_y)

    def _bounds_text(self) -> tuple[float, float, float, float]:
        """Calculate approximate bounds for text element.

        Note:
            True text bounds require font metrics (font family, size, weight, glyph shapes).
            This returns a minimal box at the text anchor position. For accurate bounds,
            a proper text layout engine is needed.

            This is sufficient for most use cases since text elements in shinymap are
            typically used for annotation layers, not interactive regions.

        Returns:
            Minimal bounding box at text position (x, y, x+1, y+1)
        """
        x = float(self.x or 0)  # type: ignore
        y = float(self.y or 0)  # type: ignore

        # Return minimal box (text position with tiny extent)
        # Real text rendering would compute actual glyph bounds from font metrics
        return (x, y, x + 1, y + 1)


@dataclass
class JSONSerializableMixin:
    """Adds to_dict/from_dict for shinymap JSON format.

    Important: JSON format preserves SVG aesthetics (fill, stroke, etc.) but these
    are NOT used by shinymap for rendering. Interactive aesthetics are controlled
    via Python API parameters (default_aesthetic, selection_aesthetic, etc.).

    Preserved aesthetics serve two purposes:
    1. SVG export: When converting back to SVG, original styles are maintained
    2. Reference: Users can inspect original design, but shinymap ignores during render
    """

    def attrs(self):
        """Iterate over non-None attributes excluding internal fields.

        Yields tuples of (key, value) for attributes that should be serialized.
        Filters out None values and internal fields (elements, element_name).

        Yields:
            Tuple of (attribute_name, attribute_value)

        Example:
            >>> circle = Circle(cx=100, cy=100, r=50, fill="#ff0000")
            >>> for key, val in circle.attrs():
            ...     print(f"{key}={val}")
            cx=100
            cy=100
            r=50
            fill=#ff0000
        """
        for key, val in vars(self).items():
            if val is None or key in ("elements", "element_name"):
                continue
            yield key, val

    def to_dict(self) -> dict[str, Any]:
        """Convert element to dict for JSON serialization.

        Returns dict in format:
            {
                "type": "circle",
                "cx": 100,
                "cy": 100,
                "r": 50,
                "fill": "#ff0000",  # Preserved but not used by shinymap
                "stroke": "#000000",
                ...
            }

        Note:
            Aesthetic attributes (fill, stroke, font_size, etc.) are preserved
            from the original SVG but are NOT used by shinymap for rendering.
            Use Python API to control interactive appearance.

        Returns:
            Dict suitable for JSON serialization
        """
        result = {"type": self.element_name}  # type: ignore

        # Serialize all non-None attributes
        for key, val in self.attrs():
            # Handle special cases for complex types
            if key == "d" and hasattr(val, "__iter__") and not isinstance(val, str):
                # PathData list → string
                result["d"] = " ".join(str(cmd) for cmd in val)
            elif key == "text" and val is not None:
                # Text content
                result["text"] = str(val)
            elif key == "points" and hasattr(val, "__iter__"):
                # Points list → space-separated string
                result["points"] = " ".join(str(p) for p in val)
            elif key == "class_":
                # class_ → class (remove trailing underscore)
                if isinstance(val, list):
                    result["class"] = " ".join(val)
                else:
                    result["class"] = str(val)
            elif key.endswith("_") and not key.startswith("_"):
                # Remove trailing underscore (Python reserved word workaround)
                clean_key = key.rstrip("_")
                result[clean_key] = val
            else:
                # Standard attribute
                result[key] = val

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Any:
        """Reconstruct element from dict.

        Args:
            data: Dict with "type" key and element attributes

        Returns:
            Appropriate element instance (Circle, Rect, Path, etc.)

        Raises:
            ValueError: If type is missing or unknown
        """
        elem_type = data.get("type")
        if not elem_type:
            raise ValueError("Missing 'type' field in element dict")

        # Import here to avoid circular dependency
        from ._elements import ELEMENT_TYPE_MAP

        element_cls = ELEMENT_TYPE_MAP.get(elem_type)
        if not element_cls:
            raise ValueError(f"Unknown element type: {elem_type}")

        # Create a copy to avoid mutating input
        attrs = dict(data)
        attrs.pop("type")  # Remove type field

        # Handle special conversions
        if "class" in attrs:
            # class → class_ (Python reserved word)
            attrs["class_"] = attrs.pop("class").split()

        # For path elements, svg.py can accept string for d parameter
        # It will be handled by svg.py's constructor

        # Create instance with attributes
        return element_cls(**attrs)


@dataclass
class ShinymapElementMixin(BoundsMixin, JSONSerializableMixin):
    """Combined mixin adding bounds() and JSON serialization to svg.py elements.

    This mixin is designed to be used with multiple inheritance:

        @dataclass
        class Circle(svg.Circle, ShinymapElementMixin):
            pass

    The element will then have:
    - All svg.py Circle functionality (constructor, rendering, etc.)
    - bounds() method for bounding box calculation
    - to_dict() for JSON serialization
    - from_dict() class method for deserialization
    - Clean __repr__() showing only non-None attributes
    - SVG markup via str() (from svg.py's __str__)

    Note on str() vs repr():
    - repr(element) → Clean Python representation: Circle(cx=100, cy=100, r=50)
    - str(element) → SVG markup: <circle cx="100" cy="100" r="50"/>
    """

    def __repr__(self) -> str:
        """Return clean Python repr showing only non-None attributes.

        Uses reprlib for concise output similar to to_dict() format.
        Only shows attributes with non-None values.

        Example:
            >>> circle = Circle(cx=100, cy=100, r=50, fill="#ff0000")
            >>> repr(circle)
            "Circle(cx=100, cy=100, r=50, fill='#ff0000')"
            >>> str(circle)  # SVG markup from svg.py
            '<circle cx="100" cy="100" r="50" fill="#ff0000"/>'
        """
        import reprlib

        class_name = self.__class__.__name__
        attrs = []

        for key, val in self.attrs():
            # Use reprlib for string truncation
            val_repr = reprlib.repr(val)
            attrs.append(f"{key}={val_repr}")

        if attrs:
            return f"{class_name}({', '.join(attrs)})"
        else:
            return f"{class_name}()"


__all__ = ["BoundsMixin", "JSONSerializableMixin", "ShinymapElementMixin"]
