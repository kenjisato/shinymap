"""Type-safe aesthetic builders for shinymap.

This module provides dataclass-based builders for SVG aesthetics with IDE autocomplete
support. Each builder type corresponds to a category of SVG elements:

- ShapeAesthetic: For filled shapes (Circle, Rect, Path, Polygon, Ellipse)
- LineAesthetic: For stroke-only elements (Line)
- TextAesthetic: For text elements (fill for color, stroke for outline)

These classes use the MISSING sentinel to distinguish unset parameters from None
(which represents transparent/none in SVG).

Numeric fields (fill_opacity, stroke_width) also accept RelativeExpr for
parent-relative values:

    from shinymap.relative import PARENT

    aes_hover = ShapeAesthetic(stroke_width=PARENT.stroke_width + 2)
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import TYPE_CHECKING, Any, Literal

from ._sentinel import MISSING, MissingType

if TYPE_CHECKING:
    from .relative import RelativeExpr

PathKind = Literal["shape", "line", "text"]


@dataclass
class BaseAesthetic:
    """Base class for all aesthetic types.

    Provides common functionality for converting to dict and partial updates.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API parameters, filtering out MISSING values.

        Returns a dict containing only parameters that were explicitly set.
        None values are preserved (they mean transparent/none in SVG).
        RelativeExpr values are serialized to their JSON representation.

        Example:
            >>> aes = ShapeAesthetic(fill_color="#fff", stroke_color=None)
            >>> aes.to_dict()
            {'fill_color': '#fff', 'stroke_color': None}
        """
        # Import here to avoid circular dependency
        from .relative import RelativeExpr

        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, MissingType):
                continue
            if isinstance(value, RelativeExpr):
                result[f.name] = value.to_json()
            else:
                result[f.name] = value
        return result

    def update(self, **kwargs: Any) -> BaseAesthetic:
        """Return new aesthetic with updated parameters (other params unchanged).

        Uses dataclasses.replace() for immutable update pattern.

        Example:
            >>> shape = ShapeAesthetic(stroke_width=1, fill_color="#fff")
            >>> updated = shape.update(stroke_width=2)
            >>> updated.stroke_width
            2
            >>> updated.fill_color  # Unchanged
            '#fff'
        """
        return replace(self, **kwargs)


@dataclass
class ShapeAesthetic(BaseAesthetic):
    """Aesthetic for shape elements (Circle, Rect, Path, Polygon, Ellipse).

    Supports all aesthetic properties including fill and stroke.

    Args:
        fill_color: Fill color (e.g., "#3b82f6", "none" for transparent)
        fill_opacity: Fill opacity (0.0 to 1.0)
        stroke_color: Stroke color (e.g., "#000")
        stroke_width: Stroke width in viewBox units (default) or screen pixels
        stroke_dasharray: Dash pattern (e.g., "5,5" for dashed, "1,3" for dotted)
        non_scaling_stroke: If True, stroke width is in screen pixels (default: False)

    Example:
        >>> from shinymap import aes
        >>> region_aes = aes.Shape(fill_color="#3b82f6", stroke_width=1)
    """

    fill_color: str | None | MissingType = MISSING
    fill_opacity: float | RelativeExpr | None | MissingType = MISSING
    stroke_color: str | None | MissingType = MISSING
    stroke_width: float | RelativeExpr | None | MissingType = MISSING
    stroke_dasharray: str | None | MissingType = MISSING
    non_scaling_stroke: bool | MissingType = MISSING


@dataclass
class LineAesthetic(BaseAesthetic):
    """Aesthetic for line elements (stroke only, no fill).

    Only supports stroke properties since lines have no fill area.
    When converted to dict, always includes fill_color=None to ensure
    no fill is applied (lines are stroke-only by definition).

    Args:
        stroke_color: Stroke color (e.g., "#ddd")
        stroke_width: Stroke width in viewBox units, or RelativeExpr for parent-relative
        stroke_dasharray: Dash pattern (e.g., "5,5" for dashed)
        non_scaling_stroke: If True, stroke width is in screen pixels (default: False)

    Example:
        >>> from shinymap import aes, linestyle
        >>> grid_aes = aes.Line(stroke_color="#ddd", stroke_dasharray=linestyle.DASHED)
    """

    stroke_color: str | None | MissingType = MISSING
    stroke_width: float | RelativeExpr | None | MissingType = MISSING
    stroke_dasharray: str | None | MissingType = MISSING
    non_scaling_stroke: bool | MissingType = MISSING

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, always including fill_color=None.

        Lines are stroke-only by definition, so fill_color is always None.
        """
        result = super().to_dict()
        # Lines have no fill by definition
        result["fill_color"] = None
        return result


@dataclass
class TextAesthetic(BaseAesthetic):
    """Aesthetic for text elements.

    Supports fill for text color and stroke for outline effects.

    Args:
        fill_color: Text color (e.g., "#000")
        fill_opacity: Text opacity (0.0 to 1.0), or RelativeExpr for parent-relative
        stroke_color: Outline color (e.g., "#fff" for white outline)
        stroke_width: Outline width in viewBox units, or RelativeExpr for parent-relative
        stroke_dasharray: Outline dash pattern (rarely used for text)
        non_scaling_stroke: If True, stroke width is in screen pixels (default: False)

    Example:
        >>> from shinymap import aes
        >>> label_aes = aes.Text(fill_color="#000", stroke_color="#fff", stroke_width=0.5)
    """

    fill_color: str | None | MissingType = MISSING
    fill_opacity: float | RelativeExpr | None | MissingType = MISSING
    stroke_color: str | None | MissingType = MISSING
    stroke_width: float | RelativeExpr | None | MissingType = MISSING
    stroke_dasharray: str | None | MissingType = MISSING
    non_scaling_stroke: bool | MissingType = MISSING


@dataclass
class PathAesthetic(BaseAesthetic):
    """Aesthetic for path elements (flexible: can be filled or stroke-only).

    Use for <path> elements that may be used as either shapes (filled) or lines
    (stroke-only). Unlike Shape or Line, Path allows full control without
    implying how the element should be rendered.

    This is useful for path elements imported from SVG that have fill="none"
    (semantically lines drawn with path notation) or when you want explicit
    control over all properties.

    Args:
        kind: Semantic type for default aesthetic resolution ("shape", "line", "text").
              When set, wash() applies the corresponding type's defaults.
              Default is MISSING (no type hint, treated as shape).
        fill_color: Fill color. None means "none" (no fill, stroke-only).
        fill_opacity: Fill opacity (0.0 to 1.0), or RelativeExpr for parent-relative
        stroke_color: Stroke color (e.g., "#000"). None means "none" (no stroke).
        stroke_width: Stroke width in viewBox units, or RelativeExpr for parent-relative
        stroke_dasharray: Dash pattern (e.g., "5,5" for dashed)
        non_scaling_stroke: If True, stroke width is in screen pixels (default: False)

    Example:
        >>> from shinymap import aes
        >>> # Path used as a line (apply line defaults from wash)
        >>> divider_aes = aes.Path(kind="line", stroke_color="#000")
        >>> # Path with explicit no-fill (stroke only)
        >>> border_aes = aes.Path(fill_color=None, stroke_color="#000")
        >>> # Path used as a shape (filled)
        >>> region_aes = aes.Path(fill_color="#3b82f6", stroke_color="#fff")
    """

    kind: PathKind | MissingType = MISSING
    fill_color: str | None | MissingType = MISSING
    fill_opacity: float | RelativeExpr | None | MissingType = MISSING
    stroke_color: str | None | MissingType = MISSING
    stroke_width: float | RelativeExpr | None | MissingType = MISSING
    stroke_dasharray: str | None | MissingType = MISSING
    non_scaling_stroke: bool | MissingType = MISSING


class ByState[T: BaseAesthetic]:
    """Container for element aesthetics across interaction states.

    Groups base, select, and hover aesthetics for a single element type.
    The type parameter T is constrained to BaseAesthetic subclasses
    (ShapeAesthetic, LineAesthetic, TextAesthetic).

    Args:
        base: Aesthetic for the default/base state (positional).
              MISSING = inherit from library default, None = invisible.
        select: Aesthetic override when region is selected.
                MISSING = inherit from base, None = no selection effect.
        hover: Aesthetic override when region is hovered.
               MISSING = inherit library default hover, None = no hover effect.

    Example:
        >>> from shinymap import aes, PARENT
        >>>
        >>> # Full form with all states
        >>> shape_states = aes.ByState(
        ...     aes.Shape(fill_color="#f0f9ff"),
        ...     select=aes.Shape(fill_color="#7dd3fc"),
        ...     hover=aes.Shape(stroke_width=PARENT.stroke_width + 2),
        ... )
        >>>
        >>> # Base only (select/hover inherit defaults)
        >>> line_states = aes.ByState(aes.Line(stroke_color="#0369a1"))
    """

    __slots__ = ("base", "select", "hover")

    def __init__(
        self,
        base: T | None | MissingType = MISSING,
        *,
        select: T | None | MissingType = MISSING,
        hover: T | None | MissingType = MISSING,
    ) -> None:
        self.base = base
        self.select = select
        self.hover = hover

    def __repr__(self) -> str:
        parts = []
        if not isinstance(self.base, MissingType):
            parts.append(f"base={self.base!r}")
        if not isinstance(self.select, MissingType):
            parts.append(f"select={self.select!r}")
        if not isinstance(self.hover, MissingType):
            parts.append(f"hover={self.hover!r}")
        if not parts:
            return "ByState()"
        return f"ByState({', '.join(parts)})"


class ByType:
    """Container for aesthetics by element type (shape, line, text).

    Used by wash() to configure element-type defaults. Does not know about groups.

    Args:
        shape: Aesthetics for shape elements (Circle, Rect, Path, Polygon, Ellipse).
               Can be ByState for full state config, or single aesthetic for base only.
        line: Aesthetics for line elements.
        text: Aesthetics for text elements.

    Example:
        >>> from shinymap import aes, PARENT
        >>>
        >>> # Full form with ByState for each element type
        >>> aes.ByType(
        ...     shape=aes.ByState(
        ...         base=aes.Shape(fill_color="#f0f9ff"),
        ...         hover=aes.Shape(stroke_width=PARENT.stroke_width + 2),
        ...     ),
        ...     line=aes.Line(stroke_color="#0369a1"),  # base only shorthand
        ...     text=aes.Text(fill_color="#0c4a6e"),
        ... )
    """

    __slots__ = ("shape", "line", "text")

    def __init__(
        self,
        *,
        shape: ByState[ShapeAesthetic] | ShapeAesthetic | None | MissingType = MISSING,
        line: ByState[LineAesthetic] | LineAesthetic | None | MissingType = MISSING,
        text: ByState[TextAesthetic] | TextAesthetic | None | MissingType = MISSING,
    ) -> None:
        self.shape = shape
        self.line = line
        self.text = text

    def __repr__(self) -> str:
        parts = []
        if not isinstance(self.shape, MissingType):
            parts.append(f"shape={self.shape!r}")
        if not isinstance(self.line, MissingType):
            parts.append(f"line={self.line!r}")
        if not isinstance(self.text, MissingType):
            parts.append(f"text={self.text!r}")
        if not parts:
            return "ByType()"
        return f"ByType({', '.join(parts)})"


class ByGroup:
    """Container for aesthetics by group/region name.

    Used by input_map() and output_map() for group-wise configuration.
    ByGroup wraps ByState (row-first composition).

    Special group names:
        __all: Default for all regions regardless of type (lowest priority)
        __shape: Default for shape elements (medium priority)
        __line: Default for line elements (medium priority)
        __text: Default for text elements (medium priority)
        <group_name>: Named groups from geometry metadata (high priority)
        <region_id>: Individual region IDs (highest priority)

    Args:
        **groups: Mapping of group names to aesthetics.
                  Values can be ByState for full state config, or single aesthetic for base only.

    Example:
        >>> from shinymap import aes, PARENT
        >>>
        >>> aes.ByGroup(
        ...     __all=aes.ByState(
        ...         base=aes.Shape(fill_color="#e5e7eb"),
        ...         hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
        ...     ),
        ...     coastal=aes.Shape(fill_color="#3b82f6"),  # base only shorthand
        ...     mountain=aes.ByState(
        ...         base=aes.Shape(fill_color="#10b981"),
        ...         select=aes.Shape(fill_color="#6ee7b7"),
        ...     ),
        ... )
    """

    __slots__ = ("_groups",)

    def __init__(
        self,
        **groups: ByState | BaseAesthetic | None | MissingType,
    ) -> None:
        self._groups: dict[str, ByState | BaseAesthetic | None | MissingType] = groups

    def __getitem__(self, key: str) -> ByState | BaseAesthetic | None | MissingType:
        return self._groups.get(key, MISSING)

    def __contains__(self, key: str) -> bool:
        return key in self._groups

    def __iter__(self):
        return iter(self._groups)

    def keys(self):
        return self._groups.keys()

    def values(self):
        return self._groups.values()

    def items(self):
        return self._groups.items()

    def get(
        self, key: str, default: ByState | BaseAesthetic | None | MissingType = MISSING
    ) -> ByState | BaseAesthetic | None | MissingType:
        return self._groups.get(key, default)

    def __repr__(self) -> str:
        if not self._groups:
            return "ByGroup()"
        parts = [f"{k}={v!r}" for k, v in self._groups.items()]
        return f"ByGroup({', '.join(parts)})"


@dataclass
class IndexedAesthetic:
    """Index-based aesthetic for multi-state modes (Cycle, Count).

    Each property can be a single value (applied to all states) or a list
    of values indexed by state:
    - For Single/Multiple: index 0 = off, index 1 = on
    - For Cycle mode: index = count % n (wrapping)
    - For Count mode: index = min(count, len(list) - 1) (clamping)

    IMPORTANT: Index 0 is used as the base aesthetic for ALL regions.
    This ensures never-touched regions and count=0 regions look the same.

    Args:
        fill_color: Single color or list of colors indexed by state.
        fill_opacity: Single value or list of opacities (0.0-1.0).
        stroke_color: Optional stroke color(s).
        stroke_width: Optional stroke width(s).
        stroke_dasharray: Optional dash pattern(s) for line styling.

    Example:
        >>> from shinymap import aes
        >>>
        >>> # Two-state (off/on) with different colors
        >>> aes.Indexed(fill_color=["#e5e7eb", "#3b82f6"])
        >>>
        >>> # Heat map with opacity gradient
        >>> from shinymap.utils import linspace
        >>> aes.Indexed(fill_color="#f97316", fill_opacity=linspace(0.0, 1.0, num=6))
        >>>
        >>> # Traffic light (4 states)
        >>> aes.Indexed(fill_color=["#e2e8f0", "#ef4444", "#eab308", "#22c55e"])
    """

    fill_color: str | list[str] | None = None
    fill_opacity: float | list[float] | None = None
    stroke_color: str | list[str] | None = None
    stroke_width: float | list[float] | None = None
    stroke_dasharray: str | list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization to JavaScript."""
        result: dict[str, Any] = {}
        if self.fill_color is not None:
            result["fillColor"] = self.fill_color
        if self.fill_opacity is not None:
            result["fillOpacity"] = self.fill_opacity
        if self.stroke_color is not None:
            result["strokeColor"] = self.stroke_color
        if self.stroke_width is not None:
            result["strokeWidth"] = self.stroke_width
        if self.stroke_dasharray is not None:
            result["strokeDasharray"] = self.stroke_dasharray
        return result

    def __repr__(self) -> str:
        parts = []
        if self.fill_color is not None:
            parts.append(f"fill_color={self.fill_color!r}")
        if self.fill_opacity is not None:
            parts.append(f"fill_opacity={self.fill_opacity!r}")
        if self.stroke_color is not None:
            parts.append(f"stroke_color={self.stroke_color!r}")
        if self.stroke_width is not None:
            parts.append(f"stroke_width={self.stroke_width!r}")
        if self.stroke_dasharray is not None:
            parts.append(f"stroke_dasharray={self.stroke_dasharray!r}")
        return f"Indexed({', '.join(parts)})"


__all__ = [
    "BaseAesthetic",
    "ShapeAesthetic",
    "LineAesthetic",
    "TextAesthetic",
    "PathAesthetic",
    "ByState",
    "ByType",
    "ByGroup",
    "IndexedAesthetic",
]
