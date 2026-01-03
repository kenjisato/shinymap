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

from ..types import MISSING, MissingType
from ..utils._dict import _warn_invalid_keys

if TYPE_CHECKING:
    from ..relative import RelativeExpr

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

        Examples:
            ```pycon
            >>> aes = ShapeAesthetic(fill_color="#fff", stroke_color=None)
            >>> aes.to_dict()
            {'fill_color': '#fff', 'stroke_color': None, 'type': 'shape'}
            ```
        """
        # Import here to avoid circular dependency
        from ..relative import RelativeExpr

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

        Examples:
            ```pycon
            >>> shape = ShapeAesthetic(stroke_width=1, fill_color="#fff")
            >>> updated = shape.update(stroke_width=2)
            >>> updated.stroke_width
            2
            >>> updated.fill_color  # Unchanged
            '#fff'
            ```
        """
        return replace(self, **kwargs)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BaseAesthetic:
        """Convert a dict to Aesthetic. Subclasses must override."""
        raise NotImplementedError("Subclasses must implement from_dict()")

    def resolve(self, parent: BaseAesthetic) -> BaseAesthetic:
        """Resolve this aesthetic against a parent.

        MISSING values inherit from parent.
        RelativeExpr values compute relative to parent.
        Explicit values (including None) override parent.

        Args:
            parent: The resolved parent aesthetic to inherit from

        Returns:
            A new aesthetic with all values resolved

        Examples:
            ```pycon
            >>> from shinymap import aes, PARENT
            >>> parent = aes.Shape(fill_color="#fff", stroke_width=1.0)
            >>> child = aes.Shape(stroke_width=PARENT.stroke_width + 1)
            >>> resolved = child.resolve(parent)
            >>> resolved.fill_color  # inherited from parent
            '#fff'
            >>> resolved.stroke_width  # resolved: 1.0 + 1 = 2.0
            2.0
            ```
        """
        # Import here to avoid circular dependency
        from ..relative import RelativeExpr

        resolved_values: dict[str, Any] = {}

        for f in fields(self):
            key = f.name
            child_value = getattr(self, key)
            parent_value = getattr(parent, key, MISSING)

            if isinstance(child_value, MissingType):
                # Not specified in child, inherit from parent
                resolved_values[key] = parent_value
            elif isinstance(child_value, RelativeExpr):
                # Resolve against parent
                if isinstance(parent_value, (int, float)):
                    resolved_values[key] = child_value.resolve(parent_value)
                else:
                    # Parent value not numeric, keep the expression (edge case)
                    resolved_values[key] = child_value
            else:
                # Explicit value (including None) overrides parent
                resolved_values[key] = child_value

        return self.__class__(**resolved_values)


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

    Examples:
        ```pycon
        >>> from shinymap import aes
        >>> region_aes = aes.Shape(fill_color="#3b82f6", stroke_width=1)
        ```
    """

    fill_color: str | None | MissingType = MISSING
    fill_opacity: float | RelativeExpr | None | MissingType = MISSING
    stroke_color: str | None | MissingType = MISSING
    stroke_width: float | RelativeExpr | None | MissingType = MISSING
    stroke_dasharray: str | None | MissingType = MISSING
    non_scaling_stroke: bool | MissingType = MISSING

    _valid_keys = {
        "type",
        "fill_color",
        "fill_opacity",
        "stroke_color",
        "stroke_width",
        "stroke_dasharray",
        "non_scaling_stroke",
    }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with type key."""
        result = super().to_dict()
        result["type"] = "shape"
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ShapeAesthetic:
        """Convert a dict to ShapeAesthetic."""
        _warn_invalid_keys(d, cls._valid_keys, "Shape")
        return ShapeAesthetic(
            fill_color=d.get("fill_color", MISSING),
            fill_opacity=d.get("fill_opacity", MISSING),
            stroke_color=d.get("stroke_color", MISSING),
            stroke_width=d.get("stroke_width", MISSING),
            stroke_dasharray=d.get("stroke_dasharray", MISSING),
            non_scaling_stroke=d.get("non_scaling_stroke", MISSING),
        )


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

    Examples:
        ```pycon
        >>> from shinymap import aes
        >>> grid_aes = aes.Line(stroke_color="#ddd", stroke_dasharray=aes.line.dashed)
        ```
    """

    stroke_color: str | None | MissingType = MISSING
    stroke_width: float | RelativeExpr | None | MissingType = MISSING
    stroke_dasharray: str | None | MissingType = MISSING
    non_scaling_stroke: bool | MissingType = MISSING

    _valid_keys = {"type", "stroke_color", "stroke_width", "stroke_dasharray", "non_scaling_stroke"}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with type key and fill_color=None.

        Lines are stroke-only by definition, so fill_color is always None.
        """
        result = super().to_dict()
        result["type"] = "line"
        # Lines have no fill by definition
        result["fill_color"] = None
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LineAesthetic:
        """Convert a dict to LineAesthetic."""
        _warn_invalid_keys(d, cls._valid_keys, "Line")
        return LineAesthetic(
            stroke_color=d.get("stroke_color", MISSING),
            stroke_width=d.get("stroke_width", MISSING),
            stroke_dasharray=d.get("stroke_dasharray", MISSING),
            non_scaling_stroke=d.get("non_scaling_stroke", MISSING),
        )


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

    Examples:
        ```pycon
        >>> from shinymap import aes
        >>> label_aes = aes.Text(fill_color="#000", stroke_color="#fff", stroke_width=0.5)
        ```
    """

    fill_color: str | None | MissingType = MISSING
    fill_opacity: float | RelativeExpr | None | MissingType = MISSING
    stroke_color: str | None | MissingType = MISSING
    stroke_width: float | RelativeExpr | None | MissingType = MISSING
    stroke_dasharray: str | None | MissingType = MISSING
    non_scaling_stroke: bool | MissingType = MISSING

    _valid_keys = {
        "type",
        "fill_color",
        "fill_opacity",
        "stroke_color",
        "stroke_width",
        "stroke_dasharray",
        "non_scaling_stroke",
    }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with type key."""
        result = super().to_dict()
        result["type"] = "text"
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TextAesthetic:
        """Convert a dict to TextAesthetic."""
        _warn_invalid_keys(d, cls._valid_keys, "Text")
        return TextAesthetic(
            fill_color=d.get("fill_color", MISSING),
            fill_opacity=d.get("fill_opacity", MISSING),
            stroke_color=d.get("stroke_color", MISSING),
            stroke_width=d.get("stroke_width", MISSING),
            stroke_dasharray=d.get("stroke_dasharray", MISSING),
            non_scaling_stroke=d.get("non_scaling_stroke", MISSING),
        )


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
              When set, Wash() applies the corresponding type's defaults.
              Default is MISSING (no type hint, treated as shape).
        fill_color: Fill color. None means "none" (no fill, stroke-only).
        fill_opacity: Fill opacity (0.0 to 1.0), or RelativeExpr for parent-relative
        stroke_color: Stroke color (e.g., "#000"). None means "none" (no stroke).
        stroke_width: Stroke width in viewBox units, or RelativeExpr for parent-relative
        stroke_dasharray: Dash pattern (e.g., "5,5" for dashed)
        non_scaling_stroke: If True, stroke width is in screen pixels (default: False)

    Examples:
        ```pycon
        >>> from shinymap import aes
        >>> # Path used as a line (apply line defaults from wash)
        >>> divider_aes = aes.Path(kind="line", stroke_color="#000")
        >>> # Path with explicit no-fill (stroke only)
        >>> border_aes = aes.Path(fill_color=None, stroke_color="#000")
        >>> # Path used as a shape (filled)
        >>> region_aes = aes.Path(fill_color="#3b82f6", stroke_color="#fff")
        ```
    """

    kind: PathKind | MissingType = MISSING
    fill_color: str | None | MissingType = MISSING
    fill_opacity: float | RelativeExpr | None | MissingType = MISSING
    stroke_color: str | None | MissingType = MISSING
    stroke_width: float | RelativeExpr | None | MissingType = MISSING
    stroke_dasharray: str | None | MissingType = MISSING
    non_scaling_stroke: bool | MissingType = MISSING

    _valid_keys = {
        "type",
        "kind",
        "fill_color",
        "fill_opacity",
        "stroke_color",
        "stroke_width",
        "stroke_dasharray",
        "non_scaling_stroke",
    }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with type key."""
        result = super().to_dict()
        result["type"] = "path"
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PathAesthetic:
        """Convert a dict to PathAesthetic."""
        _warn_invalid_keys(d, cls._valid_keys, "Path")
        return PathAesthetic(
            kind=d.get("kind", MISSING),
            fill_color=d.get("fill_color", MISSING),
            fill_opacity=d.get("fill_opacity", MISSING),
            stroke_color=d.get("stroke_color", MISSING),
            stroke_width=d.get("stroke_width", MISSING),
            stroke_dasharray=d.get("stroke_dasharray", MISSING),
            non_scaling_stroke=d.get("non_scaling_stroke", MISSING),
        )


# Type alias for leaf aesthetic types only
LeafAesthetic = ShapeAesthetic | LineAesthetic | TextAesthetic | PathAesthetic


def _leaf_from_dict(d: dict[str, Any]) -> LeafAesthetic:
    """Deserialize dict to leaf aesthetic type only.

    Used by container types (ByState, ByType) that expect leaf aesthetics.
    Raises ValueError if type is a container type.
    """
    leaf_types: dict[str, type[LeafAesthetic]] = {
        "shape": ShapeAesthetic,
        "line": LineAesthetic,
        "text": TextAesthetic,
        "path": PathAesthetic,
    }

    aes_type = d.get("type")
    if aes_type is None:
        raise ValueError("Dict must have 'type' key for deserialization")
    if aes_type not in leaf_types:
        raise ValueError(
            f"Expected leaf aesthetic type (shape, line, text, path), got: {aes_type!r}"
        )

    return leaf_types[aes_type].from_dict(d)


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

    Examples:
        ```pycon
        >>> from shinymap import aes, PARENT

        >>> # Full form with all states
        >>> shape_states = aes.ByState(
        ...     aes.Shape(fill_color="#f0f9ff"),
        ...     select=aes.Shape(fill_color="#7dd3fc"),
        ...     hover=aes.Shape(stroke_width=PARENT.stroke_width + 2),
        ... )

        >>> # Base only (select/hover inherit defaults)
        >>> line_states = aes.ByState(aes.Line(stroke_color="#0369a1"))
        ```
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with type key, recursively converting nested aesthetics."""
        result: dict[str, Any] = {"type": "bystate"}
        if not isinstance(self.base, MissingType):
            if self.base is None:
                result["base"] = None
            else:
                result["base"] = self.base.to_dict()
        if not isinstance(self.select, MissingType):
            if self.select is None:
                result["select"] = None
            else:
                result["select"] = self.select.to_dict()
        if not isinstance(self.hover, MissingType):
            if self.hover is None:
                result["hover"] = None
            else:
                result["hover"] = self.hover.to_dict()
        return result

    def to_js_dict(self) -> dict[str, Any]:
        """Convert to dict format for JavaScript consumption.

        Unlike to_dict(), this produces a simplified format without type
        discriminators, suitable for direct use by React components.

        Returns:
            Dict with keys: base, select, hover
            Each value is a dict of aesthetic properties (snake_case keys).
        """

        def _leaf_to_js(aes: BaseAesthetic) -> dict[str, Any]:
            """Convert leaf aesthetic to JS dict, stripping metadata."""
            d = aes.to_dict()
            d.pop("type", None)  # Remove type discriminator
            d.pop("kind", None)  # Remove PathAesthetic.kind
            return d

        result: dict[str, Any] = {}
        if not isinstance(self.base, MissingType) and self.base is not None:
            result["base"] = _leaf_to_js(self.base)
        if not isinstance(self.select, MissingType):
            if self.select is None:
                result["select"] = None
            else:
                result["select"] = _leaf_to_js(self.select)
        if not isinstance(self.hover, MissingType):
            if self.hover is None:
                result["hover"] = None
            else:
                result["hover"] = _leaf_to_js(self.hover)
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ByState:
        """Convert dict with base/select/hover keys to ByState.

        Recursively deserializes nested aesthetic dicts using _leaf_from_dict().
        """
        base: BaseAesthetic | None | MissingType = MISSING
        select: BaseAesthetic | None | MissingType = MISSING
        hover: BaseAesthetic | None | MissingType = MISSING

        if "base" in d:
            if d["base"] is None:
                base = None
            else:
                base = _leaf_from_dict(d["base"])
        if "select" in d:
            if d["select"] is None:
                select = None
            else:
                select = _leaf_from_dict(d["select"])
        if "hover" in d:
            if d["hover"] is None:
                hover = None
            else:
                hover = _leaf_from_dict(d["hover"])

        return ByState(base=base, select=select, hover=hover)

    def resolve_for_region(
        self,
        wash_default: BaseAesthetic,
        is_selected: bool = False,
        is_hovered: bool = False,
    ) -> BaseAesthetic:
        """Resolve the final aesthetic for a region given its state.

        Chain: wash_default → base → select (if selected) → hover (if hovered)

        Args:
            wash_default: The wash config default aesthetic for this element type
            is_selected: Whether the region is currently selected
            is_hovered: Whether the region is currently hovered

        Returns:
            A fully resolved aesthetic

        Examples:
            ```pycon
            >>> from shinymap import aes, PARENT
            >>> default = aes.Shape(fill_color="#e5e7eb", stroke_width=1.0)
            >>> states = aes.ByState(
            ...     base=aes.Shape(fill_color="#3b82f6"),
            ...     select=aes.Shape(fill_color="#1e40af"),
            ...     hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
            ... )
            >>> # Not selected, not hovered
            >>> resolved = states.resolve_for_region(default)
            >>> resolved.fill_color
            '#3b82f6'
            >>> resolved.stroke_width  # inherited from default
            1.0
            >>> # Selected and hovered
            >>> resolved = states.resolve_for_region(default, is_selected=True, is_hovered=True)
            >>> resolved.fill_color  # from select
            '#1e40af'
            >>> resolved.stroke_width  # 1.0 + 1 from hover
            2.0
            ```
        """
        # Layer 1: base resolves against wash default
        if isinstance(self.base, MissingType) or self.base is None:
            current = wash_default
        else:
            current = self.base.resolve(wash_default)

        # Layer 2: select resolves against base (if selected)
        if is_selected and not isinstance(self.select, MissingType):
            if self.select is not None:
                current = self.select.resolve(current)

        # Layer 3: hover resolves against current (if hovered)
        if is_hovered and not isinstance(self.hover, MissingType):
            if self.hover is not None:
                current = self.hover.resolve(current)

        return current


class ByType:
    """Container for aesthetics by element type (shape, line, text).

    Used by Wash() to configure element-type defaults. Does not know about groups.

    Args:
        shape: Aesthetics for shape elements (Circle, Rect, Path, Polygon, Ellipse).
               Can be ByState for full state config, or single aesthetic for base only.
        line: Aesthetics for line elements.
        text: Aesthetics for text elements.

    Examples:
        ```pycon
        >>> from shinymap import aes, PARENT

        >>> # Full form with ByState for each element type
        >>> _ = aes.ByType(
        ...     shape=aes.ByState(
        ...         base=aes.Shape(fill_color="#f0f9ff"),
        ...         hover=aes.Shape(stroke_width=PARENT.stroke_width + 2),
        ...     ),
        ...     line=aes.Line(stroke_color="#0369a1"),  # base only shorthand
        ...     text=aes.Text(fill_color="#0c4a6e"),
        ... )
        ```
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with type key, recursively converting nested aesthetics."""
        result: dict[str, Any] = {"type": "bytype"}

        def _convert_value(v: ByState | BaseAesthetic | None) -> dict[str, Any] | None:
            if v is None:
                return None
            return v.to_dict()

        if not isinstance(self.shape, MissingType):
            result["shape"] = _convert_value(self.shape)
        if not isinstance(self.line, MissingType):
            result["line"] = _convert_value(self.line)
        if not isinstance(self.text, MissingType):
            result["text"] = _convert_value(self.text)
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ByType:
        """Convert dict with shape/line/text keys to ByType.

        Values can be ByState dicts or leaf aesthetic dicts.
        """

        def _parse_value(
            v: dict[str, Any] | None, expected_leaf: type[LeafAesthetic]
        ) -> ByState | LeafAesthetic | None | MissingType:
            if v is None:
                return None
            aes_type = v.get("type")
            if aes_type == "bystate":
                return ByState.from_dict(v)
            # Leaf aesthetic - use expected type
            return expected_leaf.from_dict(v)

        shape: ByState[ShapeAesthetic] | ShapeAesthetic | None | MissingType = MISSING
        line: ByState[LineAesthetic] | LineAesthetic | None | MissingType = MISSING
        text: ByState[TextAesthetic] | TextAesthetic | None | MissingType = MISSING

        if "shape" in d:
            shape = _parse_value(d["shape"], ShapeAesthetic)  # type: ignore[assignment]
        if "line" in d:
            line = _parse_value(d["line"], LineAesthetic)  # type: ignore[assignment]
        if "text" in d:
            text = _parse_value(d["text"], TextAesthetic)  # type: ignore[assignment]

        return ByType(shape=shape, line=line, text=text)


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

    Examples:
        ```pycon
        >>> from shinymap import aes, PARENT

        >>> _ = aes.ByGroup(
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
        ```
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with type key, recursively converting nested aesthetics."""
        result: dict[str, Any] = {"type": "bygroup"}
        for key, value in self._groups.items():
            if isinstance(value, MissingType):
                continue
            if value is None:
                result[key] = None
            else:
                result[key] = value.to_dict()
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ByGroup:
        """Convert dict to ByGroup.

        Values can be ByState dicts or leaf aesthetic dicts.
        """
        groups: dict[str, ByState | BaseAesthetic | None | MissingType] = {}

        for key, value in d.items():
            if key == "type":
                continue  # Skip the type key
            if value is None:
                groups[key] = None
            elif isinstance(value, dict):
                aes_type = value.get("type")
                if aes_type == "bystate":
                    groups[key] = ByState.from_dict(value)
                else:
                    # Leaf aesthetic
                    groups[key] = _leaf_from_dict(value)

        return ByGroup(**groups)


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

    Examples:
        ```pycon
        >>> from shinymap import aes

        >>> # Two-state (off/on) with different colors
        >>> _ = aes.Indexed(fill_color=["#e5e7eb", "#3b82f6"])

        >>> # Heat map with opacity gradient
        >>> from shinymap.utils import linspace
        >>> _ = aes.Indexed(fill_color="#f97316", fill_opacity=linspace(0.0, 1.0, num=6))

        >>> # Traffic light (4 states)
        >>> _ = aes.Indexed(fill_color=["#e2e8f0", "#ef4444", "#eab308", "#22c55e"])
        ```
    """

    fill_color: str | list[str] | None = None
    fill_opacity: float | list[float] | None = None
    stroke_color: str | list[str] | None = None
    stroke_width: float | list[float] | None = None
    stroke_dasharray: str | list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with type key (snake_case)."""
        result: dict[str, Any] = {"type": "indexed"}
        if self.fill_color is not None:
            result["fill_color"] = self.fill_color
        if self.fill_opacity is not None:
            result["fill_opacity"] = self.fill_opacity
        if self.stroke_color is not None:
            result["stroke_color"] = self.stroke_color
        if self.stroke_width is not None:
            result["stroke_width"] = self.stroke_width
        if self.stroke_dasharray is not None:
            result["stroke_dasharray"] = self.stroke_dasharray
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> IndexedAesthetic:
        """Convert a dict to IndexedAesthetic."""
        return IndexedAesthetic(
            fill_color=d.get("fill_color"),
            fill_opacity=d.get("fill_opacity"),
            stroke_color=d.get("stroke_color"),
            stroke_width=d.get("stroke_width"),
            stroke_dasharray=d.get("stroke_dasharray"),
        )

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


# Type alias for any aesthetic type
AnyAesthetic = (
    ShapeAesthetic
    | LineAesthetic
    | TextAesthetic
    | PathAesthetic
    | IndexedAesthetic
    | ByState
    | ByType
    | ByGroup
)


def from_dict(d: dict[str, Any]) -> AnyAesthetic:
    """Deserialize dict to appropriate aesthetic type based on 'type' key.

    This is the top-level dispatcher for aesthetic deserialization.
    Container types (ByState, ByGroup, ByType) call this recursively
    to deserialize nested aesthetics.

    Args:
        d: Dict with 'type' key indicating the aesthetic type

    Returns:
        Appropriate aesthetic object

    Raises:
        ValueError: If 'type' key is missing or unknown

    Examples:
        ```pycon
        >>> from_dict({"type": "shape", "fill_color": "#fff"})  # doctest: +ELLIPSIS
        ShapeAesthetic(fill_color='#fff', ...)
        
        >>> from_dict({
        ...     "type": "bystate",
        ...     "base": {"type": "shape", "fill_color": "#fff"},
        ... })  # doctest: +ELLIPSIS
        ByState(base=ShapeAesthetic(fill_color='#fff', ...))
        ```
    """
    aes_type = d.get("type")
    if aes_type is None:
        raise ValueError("Dict must have 'type' key for deserialization")

    # Dispatch based on type
    if aes_type == "shape":
        return ShapeAesthetic.from_dict(d)
    elif aes_type == "line":
        return LineAesthetic.from_dict(d)
    elif aes_type == "text":
        return TextAesthetic.from_dict(d)
    elif aes_type == "path":
        return PathAesthetic.from_dict(d)
    elif aes_type == "indexed":
        return IndexedAesthetic.from_dict(d)
    elif aes_type == "bystate":
        return ByState.from_dict(d)
    elif aes_type == "bygroup":
        return ByGroup.from_dict(d)
    elif aes_type == "bytype":
        return ByType.from_dict(d)
    else:
        raise ValueError(f"Unknown aesthetic type: {aes_type!r}")


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
    "from_dict",
]
