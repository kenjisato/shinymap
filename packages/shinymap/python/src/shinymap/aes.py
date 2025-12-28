"""Aesthetic builder factory functions for IDE-friendly API.

This module provides factory functions that create aesthetic instances with
IDE autocomplete support. Use these instead of directly instantiating the
aesthetic classes.

Usage:
    >>> from shinymap import aes, linestyle
    >>>
    >>> # Create shape aesthetic (for filled regions)
    >>> region_aes = aes.Shape(fill_color="#3b82f6", stroke_width=1)
    >>>
    >>> # Create line aesthetic (stroke only, no fill)
    >>> grid_aes = aes.Line(stroke_color="#ddd", stroke_dasharray=linestyle.DASHED)
    >>>
    >>> # Create path aesthetic (for paths used as lines or with explicit control)
    >>> divider_aes = aes.Path(kind="line", stroke_color="#000")  # applies line defaults
    >>>
    >>> # Create text aesthetic with outline
    >>> label_aes = aes.Text(fill_color="#000", stroke_color="#fff", stroke_width=0.5)
    >>>
    >>> # Partial updates (returns new instance)
    >>> hover_aes = region_aes.update(stroke_width=2)
    >>>
    >>> # Explicit None means "none/transparent" in SVG
    >>> transparent = aes.Shape(fill_color=None)  # fill_color: None in to_dict()
    >>>
    >>> # MISSING (default) means "not specified"
    >>> minimal = aes.Shape(stroke_width=1)  # only stroke_width in to_dict()
    >>>
    >>> # Relative values using PARENT proxy
    >>> from shinymap import PARENT
    >>> hover_aes = aes.Shape(stroke_width=PARENT.stroke_width + 2)
"""

from __future__ import annotations

from typing import Literal

from ._aesthetics import (
    ByGroup,
    ByState,
    ByType,
    IndexedAesthetic,
    LineAesthetic,
    PathAesthetic,
    ShapeAesthetic,
    TextAesthetic,
)
from ._sentinel import MISSING, MissingType
from .relative import RelativeExpr

PathKind = Literal["shape", "line", "text"]

__all__ = ["Line", "Shape", "Text", "Path", "Indexed", "ByState", "ByType", "ByGroup"]


def Line(
    stroke_color: str | None | MissingType = MISSING,
    stroke_width: float | RelativeExpr | None | MissingType = MISSING,
    stroke_dasharray: str | None | MissingType = MISSING,
    non_scaling_stroke: bool | MissingType = MISSING,
) -> LineAesthetic:
    """Create line aesthetic (stroke only, no fill).

    Use for line elements where only stroke properties are relevant.

    Args:
        stroke_color: Stroke color (e.g., "#ddd"). None means "none" in SVG.
        stroke_width: Stroke width in viewBox units, or RelativeExpr for parent-relative values
        stroke_dasharray: Dash pattern (e.g., "5,5" for dashed). Use linestyle constants.
        non_scaling_stroke: If True, stroke width is in screen pixels (default: False)

    Returns:
        LineAesthetic instance

    Example:
        >>> from shinymap import aes, linestyle
        >>> grid_aes = aes.Line(stroke_color="#ddd", stroke_dasharray=linestyle.DASHED)
    """
    return LineAesthetic(
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray,
        non_scaling_stroke=non_scaling_stroke,
    )


def Shape(
    fill_color: str | None | MissingType = MISSING,
    fill_opacity: float | RelativeExpr | None | MissingType = MISSING,
    stroke_color: str | None | MissingType = MISSING,
    stroke_width: float | RelativeExpr | None | MissingType = MISSING,
    stroke_dasharray: str | None | MissingType = MISSING,
    non_scaling_stroke: bool | MissingType = MISSING,
) -> ShapeAesthetic:
    """Create shape aesthetic (fill and stroke).

    Use for filled shapes like circles, rectangles, paths, polygons.

    Args:
        fill_color: Fill color (e.g., "#3b82f6"). None means "none" (transparent).
        fill_opacity: Fill opacity (0.0 to 1.0), or RelativeExpr for parent-relative
        stroke_color: Stroke color (e.g., "#000"). None means "none".
        stroke_width: Stroke width in viewBox units, or RelativeExpr for parent-relative values
        stroke_dasharray: Dash pattern (e.g., "5,5"). Use linestyle constants.
        non_scaling_stroke: If True, stroke width is in screen pixels (default: False)

    Returns:
        ShapeAesthetic instance

    Example:
        >>> from shinymap import aes
        >>> region_aes = aes.Shape(fill_color="#3b82f6", stroke_color="#000", stroke_width=1)
    """
    return ShapeAesthetic(
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray,
        non_scaling_stroke=non_scaling_stroke,
    )


def Text(
    fill_color: str | None | MissingType = MISSING,
    fill_opacity: float | RelativeExpr | None | MissingType = MISSING,
    stroke_color: str | None | MissingType = MISSING,
    stroke_width: float | RelativeExpr | None | MissingType = MISSING,
    stroke_dasharray: str | None | MissingType = MISSING,
    non_scaling_stroke: bool | MissingType = MISSING,
) -> TextAesthetic:
    """Create text aesthetic (fill for color, stroke for outline).

    Use for text labels where fill controls text color and stroke adds outline.

    Args:
        fill_color: Text color (e.g., "#000"). None means "none" (transparent).
        fill_opacity: Text opacity (0.0 to 1.0), or RelativeExpr for parent-relative
        stroke_color: Outline color (e.g., "#fff" for white outline). None means "none".
        stroke_width: Outline width in viewBox units, or RelativeExpr for parent-relative values
        stroke_dasharray: Outline dash pattern (rarely used for text)
        non_scaling_stroke: If True, stroke width is in screen pixels (default: False)

    Returns:
        TextAesthetic instance

    Example:
        >>> from shinymap import aes
        >>> label_aes = aes.Text(fill_color="#000", stroke_color="#fff", stroke_width=0.5)
    """
    return TextAesthetic(
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray,
        non_scaling_stroke=non_scaling_stroke,
    )


def Path(
    kind: PathKind | MissingType = MISSING,
    fill_color: str | None | MissingType = MISSING,
    fill_opacity: float | RelativeExpr | None | MissingType = MISSING,
    stroke_color: str | None | MissingType = MISSING,
    stroke_width: float | RelativeExpr | None | MissingType = MISSING,
    stroke_dasharray: str | None | MissingType = MISSING,
    non_scaling_stroke: bool | MissingType = MISSING,
) -> PathAesthetic:
    """Create path aesthetic (flexible: can be filled or stroke-only).

    Use for <path> elements that may represent either shapes (filled) or lines
    (stroke-only). Unlike Shape or Line, Path provides full control over all
    properties without implying how the element should be rendered.

    This is particularly useful for:
    - Path elements imported from SVG with fill="none" (semantically lines)
    - Grid lines or dividers drawn with path notation
    - Elements where you want explicit control over both fill and stroke

    Args:
        kind: Semantic type for default aesthetic resolution ("shape", "line", "text").
              When set, wash() applies the corresponding type's defaults.
              Use "line" for paths that are semantically lines (grid, dividers).
        fill_color: Fill color. None means "none" (stroke-only, no fill).
        fill_opacity: Fill opacity (0.0 to 1.0), or RelativeExpr for parent-relative
        stroke_color: Stroke color (e.g., "#000"). None means "none" (no stroke).
        stroke_width: Stroke width in viewBox units, or RelativeExpr for parent-relative
        stroke_dasharray: Dash pattern (e.g., "5,5" for dashed). Use linestyle constants.
        non_scaling_stroke: If True, stroke width is in screen pixels (default: False)

    Returns:
        PathAesthetic instance

    Example:
        >>> from shinymap import aes
        >>> # Path used as a line (apply line defaults from wash)
        >>> divider_aes = aes.Path(kind="line", stroke_color="#000")
        >>> # Path with explicit no-fill (stroke only)
        >>> border_aes = aes.Path(fill_color=None, stroke_color="#000", stroke_width=1)
        >>> # Path used as a shape (filled)
        >>> region_aes = aes.Path(fill_color="#3b82f6", stroke_color="#fff")
    """
    return PathAesthetic(
        kind=kind,
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray,
        non_scaling_stroke=non_scaling_stroke,
    )


def Indexed(
    fill_color: str | list[str] | None = None,
    fill_opacity: float | list[float] | None = None,
    stroke_color: str | list[str] | None = None,
    stroke_width: float | list[float] | None = None,
    stroke_dasharray: str | list[str] | None = None,
) -> IndexedAesthetic:
    """Create indexed aesthetic for multi-state modes (Cycle, Count).

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

    Returns:
        IndexedAesthetic instance

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
    return IndexedAesthetic(
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray,
    )
