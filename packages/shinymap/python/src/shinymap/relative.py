"""PARENT proxy for relative value expressions.

This module provides a mechanism for expressing aesthetic values relative to
their parent in the hierarchy. Resolution happens automatically when the
library renders the element.

Usage:
    from shinymap import PARENT, aes

    # Relative stroke width (parent + 2)
    aes_hover = aes.Shape(stroke_width=PARENT.stroke_width + 2)

    # Multiple relative values
    aes_select = aes.Shape(
        stroke_width=PARENT.stroke_width * 1.5,
        fill_opacity=PARENT.fill_opacity - 0.2
    )

Supported Operations:
    - Addition: PARENT.property + value
    - Subtraction: PARENT.property - value
    - Multiplication: PARENT.property * value
    - Division: PARENT.property / value

How Resolution Works:

The aesthetic hierarchy is: DEFAULT → BASE → BEAR → SELECT/ACTIVE → HOVER

When rendering, the library:
1. Computes the "parent" aesthetic by merging the chain
2. Detects RelativeExpr values in child aesthetics
3. Resolves them against the computed parent values

This happens automatically in the render layer (JavaScript side for
interactive maps, Python side for export_svg).

Note:
    Arbitrary functions are not supported due to JSON serialization
    requirements. For complex transformations, compute values directly
    in your render function.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Literal


@dataclass(frozen=True)
class RelativeExpr:
    """A deferred expression that references a parent property.

    These expressions capture the intent to compute a value relative to
    a parent property. The library resolves them automatically during
    rendering when the parent context is available.

    Attributes:
        property: The parent property name (e.g., "stroke_width")
        operator: The mathematical operator (+, -, *, /)
        operand: The numeric value to apply with the operator
    """

    property: str
    operator: Literal["+", "-", "*", "/"]
    operand: float

    def resolve(self, parent_value: float) -> float:
        """Resolve this expression given the parent's actual value.

        This method is called by the library's resolution layer.
        You typically don't need to call this directly.

        Args:
            parent_value: The parent's value for this property

        Returns:
            The computed value

        Examples:
            ```pycon
            >>> expr = PARENT.stroke_width + 2
            >>> expr.resolve(1.0)  # 1.0 + 2 = 3.0
            3.0
            ```
        """
        if self.operator == "+":
            return parent_value + self.operand
        elif self.operator == "-":
            return parent_value - self.operand
        elif self.operator == "*":
            return parent_value * self.operand
        elif self.operator == "/":
            if self.operand == 0:
                raise ValueError("Cannot divide by zero")
            return parent_value / self.operand
        raise ValueError(f"Unknown operator: {self.operator}")

    def to_json(self) -> dict[str, Any]:
        """Serialize for sending to JavaScript.

        Returns a dict with a marker that JavaScript can detect
        and resolve at render time.
        """
        return {
            "__relative__": True,
            "property": self.property,
            "operator": self.operator,
            "operand": self.operand,
        }

    def __repr__(self) -> str:
        return f"PARENT.{self.property} {self.operator} {self.operand}"


class ParentProperty:
    """Represents a reference to a specific parent property.

    Created when accessing attributes on the PARENT proxy object.
    Supports arithmetic operations that create RelativeExpr objects.

    Examples:
        ```pycon
        PARENT.stroke_width       # ParentProperty("stroke_width")
        PARENT.stroke_width + 2   # RelativeExpr("stroke_width", "+", 2)
        ```
    """

    __slots__ = ("_name",)

    def __init__(self, name: str):
        self._name = name

    def __add__(self, other: float | int) -> RelativeExpr:
        return RelativeExpr(self._name, "+", float(other))

    def __radd__(self, other: float | int) -> RelativeExpr:
        return RelativeExpr(self._name, "+", float(other))

    def __sub__(self, other: float | int) -> RelativeExpr:
        return RelativeExpr(self._name, "-", float(other))

    def __rsub__(self, other: float | int) -> RelativeExpr:
        raise TypeError(
            "Cannot subtract PARENT.property from a value; use PARENT.property - value instead"
        )

    def __mul__(self, other: float | int) -> RelativeExpr:
        return RelativeExpr(self._name, "*", float(other))

    def __rmul__(self, other: float | int) -> RelativeExpr:
        return RelativeExpr(self._name, "*", float(other))

    def __truediv__(self, other: float | int) -> RelativeExpr:
        return RelativeExpr(self._name, "/", float(other))

    def __repr__(self) -> str:
        return f"PARENT.{self._name}"


class ParentProxy:
    """A proxy object for creating parent property references.

    The singleton PARENT object is an instance of this class.
    Accessing any attribute creates a ParentProperty that can be
    used in arithmetic expressions to create RelativeExpr objects.

    Examples:
        ```pycon
        PARENT.stroke_width       # ParentProperty("stroke_width")
        PARENT.stroke_width + 2   # RelativeExpr("stroke_width", "+", 2)
        2 * PARENT.fill_opacity   # RelativeExpr("fill_opacity", "*", 2)
        ```
    """

    __slots__ = ()

    def __getattr__(self, name: str) -> ParentProperty:
        if name.startswith("_"):
            raise AttributeError(name)
        return ParentProperty(name)

    def __repr__(self) -> str:
        return "PARENT"


# The singleton PARENT object
PARENT = ParentProxy()

# Runtime imports for aesthetic resolution (placed here to avoid circular imports)
from .aes import _defaults as _aes_default  # noqa: E402
from .aes._core import BaseAesthetic, LineAesthetic, ShapeAesthetic, TextAesthetic  # noqa: E402
from .types import MISSING, MissingType  # noqa: E402


@dataclass
class RegionState:
    """Represents the state of a region for aesthetic resolution.

    This class captures the state that affects which aesthetics are applied
    to a region during rendering.

    Attributes:
        region_id: The ID of the region
        value: The region's value (count, cycle state, etc.). Used for:
            - IndexedAesthetic lookup
            - Determining selection state (value > 0 means selected)
        is_hovered: Whether the region is currently hovered
        group: Optional group name for group-based aesthetics
    """

    region_id: str
    value: int = 0
    is_hovered: bool = False
    group: str | None = None

    @property
    def is_selected(self) -> bool:
        """Whether the region is selected (derived from value > 0)."""
        return self.value > 0


@dataclass
class AestheticConfig:
    """Configuration for aesthetic resolution.

    Contains all the aesthetic settings that can be applied to regions.
    This mirrors the props passed to InputMap/OutputMap components.

    Attributes:
        aes_base: Base aesthetic for all regions
        aes_select: Aesthetic override for selected regions
        aes_hover: Aesthetic for hovered regions (None = disabled)
        aes_group: Per-group aesthetic overrides
        fill_color: Per-region or global fill color override
    """

    aes_base: BaseAesthetic | None = None
    aes_select: BaseAesthetic | None = None
    aes_hover: BaseAesthetic | None | MissingType = MISSING
    aes_group: dict[str, BaseAesthetic] | None = None
    fill_color: str | dict[str, str] | None = None


def _get_default_for_type(aes: BaseAesthetic) -> BaseAesthetic:
    """Get the appropriate default aesthetic for a given type."""
    if isinstance(aes, LineAesthetic):
        return _aes_default.line
    if isinstance(aes, TextAesthetic):
        return _aes_default.text
    return _aes_default.shape


def _merge_aesthetic(
    child: BaseAesthetic | None,
    parent_resolved: ShapeAesthetic,
) -> ShapeAesthetic:
    """Merge a child aesthetic onto a resolved parent.

    RelativeExpr values in child are resolved against parent values.
    MISSING values inherit from parent.
    Explicit values (including None) override parent.
    """
    if child is None:
        return parent_resolved

    resolved_values: dict[str, Any] = {}

    for f in fields(ShapeAesthetic):
        key = f.name
        parent_value = getattr(parent_resolved, key)
        child_value = getattr(child, key, MISSING)

        if isinstance(child_value, MissingType):
            # Not specified, inherit from parent
            resolved_values[key] = parent_value
        elif isinstance(child_value, RelativeExpr):
            # Resolve against parent
            if isinstance(parent_value, (int, float)):
                resolved_values[key] = child_value.resolve(parent_value)
            else:
                resolved_values[key] = child_value
        else:
            # Explicit value (including None)
            resolved_values[key] = child_value

    return ShapeAesthetic(**resolved_values)


def resolve_region(
    state: RegionState,
    config: AestheticConfig,
) -> ShapeAesthetic:
    """Resolve the final aesthetic for a region given its state.

    This function walks the aesthetic hierarchy recursively:
        DEFAULT → BASE → GROUP → SELECT (if selected) → HOVER (if hovered)

    Each layer merges onto the previous, with RelativeExpr values
    resolved against the parent layer's values.

    Args:
        state: The region's current state (selected, hovered, group)
        config: The aesthetic configuration (base, select, hover, group aesthetics)

    Returns:
        A fully resolved ShapeAesthetic with all properties set

    Examples:
        ```pycon
        >>> from shinymap import aes, PARENT, resolve_region, RegionState, AestheticConfig
        >>> state = RegionState("region_1", value=1, is_hovered=True)  # value=1 means selected
        >>> config = AestheticConfig(
        ...     aes_base=aes.Shape(stroke_width=2),
        ...     aes_select=aes.Shape(stroke_width=3, fill_color="#fef08a"),
        ...     aes_hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
        ... )
        >>> resolved = resolve_region(state, config)
        >>> resolved.stroke_width  # 3 (from select) + 1 (from hover) = 4
        4.0
        ```
    """
    # Layer 0: DEFAULT
    current = _aes_default.shape

    # Layer 1: BASE
    current = _merge_aesthetic(config.aes_base, current)

    # Layer 1.5: Per-region fill_color override
    if config.fill_color is not None:
        fill: str | None
        if isinstance(config.fill_color, str):
            fill = config.fill_color
        else:
            fill = config.fill_color.get(state.region_id)
        if fill is not None:
            current = ShapeAesthetic(
                fill_color=fill,
                fill_opacity=current.fill_opacity,
                stroke_color=current.stroke_color,
                stroke_width=current.stroke_width,
                stroke_dasharray=current.stroke_dasharray,
                non_scaling_stroke=current.non_scaling_stroke,
            )

    # Layer 2: GROUP (if region belongs to a group)
    if state.group and config.aes_group:
        group_aes = config.aes_group.get(state.group)
        current = _merge_aesthetic(group_aes, current)

    # Layer 3: SELECT (if selected)
    if state.is_selected:
        current = _merge_aesthetic(config.aes_select, current)

    # Layer 4: HOVER (if hovered)
    if state.is_hovered:
        # Determine effective hover aesthetic
        hover_aes: BaseAesthetic | None
        if isinstance(config.aes_hover, MissingType):
            # Not specified: use default hover
            hover_aes = _aes_default.hover
        elif config.aes_hover is None:
            # Explicitly disabled: no hover effect
            hover_aes = None
        else:
            hover_aes = config.aes_hover

        current = _merge_aesthetic(hover_aes, current)

    return current


def preview_region(
    state: RegionState,
    config: AestheticConfig,
) -> str:
    """Preview the aesthetic resolution for a region with verbose output.

    Shows how aesthetics are inherited and resolved at each layer,
    displaying ALL properties at each step.

    Args:
        state: The region's current state
        config: The aesthetic configuration

    Returns:
        A formatted string showing the resolution at each layer

    Examples:
        ```pycon
        >>> from shinymap import aes, PARENT, preview_region, RegionState, AestheticConfig
        >>> state = RegionState("region_1", value=1, is_hovered=True)  # value=1 means selected
        >>> config = AestheticConfig(
        ...     aes_base=aes.Shape(stroke_width=2),
        ...     aes_select=aes.Shape(stroke_width=3),
        ...     aes_hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
        ... )
        >>> print(preview_region(state, config))  # doctest: +SKIP
        ```
    """
    lines: list[str] = []
    lines.append(f"=== Aesthetic Resolution for '{state.region_id}' ===")
    lines.append(
        f"State: value={state.value}, is_selected={state.is_selected}, "
        f"is_hovered={state.is_hovered}, group={state.group}"
    )
    lines.append("")

    def format_aes(aes: ShapeAesthetic, prev: ShapeAesthetic | None = None) -> list[str]:
        """Format aesthetic with change markers."""
        result = []
        for f in fields(ShapeAesthetic):
            key = f.name
            value = getattr(aes, key)
            marker = ""
            if prev is not None:
                prev_value = getattr(prev, key)
                if value != prev_value:
                    marker = " *"
            if value is None:
                result.append(f"    {key + ':':22} None{marker}")
            else:
                result.append(f"    {key + ':':22} {value}{marker}")
        return result

    def format_input(aes: BaseAesthetic | None) -> list[str]:
        """Format input aesthetic (only non-MISSING values)."""
        if aes is None:
            return ["    (none)"]
        result = []
        has_input = False
        for f in fields(aes):
            key = f.name
            value = getattr(aes, key)
            if isinstance(value, MissingType):
                continue
            has_input = True
            if isinstance(value, RelativeExpr):
                result.append(f"    {key + ':':22} {value!r}")
            elif value is None:
                result.append(f"    {key + ':':22} None (transparent)")
            else:
                result.append(f"    {key + ':':22} {value}")
        if not has_input:
            return ["    (all MISSING)"]
        return result

    # Layer 0: DEFAULT
    current = _aes_default.shape
    lines.append("[0] DEFAULT")
    lines.extend(format_aes(current))
    lines.append("")
    prev = current

    # Layer 1: BASE
    lines.append("[1] BASE (aes_base)")
    lines.append("  Input:")
    lines.extend(format_input(config.aes_base))
    current = _merge_aesthetic(config.aes_base, current)
    lines.append("  Resolved:")
    lines.extend(format_aes(current, prev))
    lines.append("")
    prev = current

    # Layer 1.5: fill_color override
    if config.fill_color is not None:
        lines.append("[1.5] fill_color override")
        fill_override: str | None
        if isinstance(config.fill_color, str):
            fill_override = config.fill_color
            lines.append(f"  Input: '{fill_override}' (global)")
        else:
            fill_override = config.fill_color.get(state.region_id)
            lines.append(f"  Input: {config.fill_color}")
            lines.append(f"  For region '{state.region_id}': {fill_override}")
        if fill_override is not None:
            current = ShapeAesthetic(
                fill_color=fill_override,
                fill_opacity=current.fill_opacity,
                stroke_color=current.stroke_color,
                stroke_width=current.stroke_width,
                stroke_dasharray=current.stroke_dasharray,
                non_scaling_stroke=current.non_scaling_stroke,
            )
        lines.append("  Resolved:")
        lines.extend(format_aes(current, prev))
        lines.append("")
        prev = current

    # Layer 2: GROUP
    if state.group:
        lines.append(f"[2] GROUP (group='{state.group}')")
        group_aes = config.aes_group.get(state.group) if config.aes_group else None
        lines.append("  Input:")
        lines.extend(format_input(group_aes))
        current = _merge_aesthetic(group_aes, current)
        lines.append("  Resolved:")
        lines.extend(format_aes(current, prev))
        lines.append("")
        prev = current
    else:
        lines.append("[2] GROUP (skipped - no group)")
        lines.append("")

    # Layer 3: SELECT
    if state.is_selected:
        lines.append("[3] SELECT (is_selected=True)")
        lines.append("  Input:")
        lines.extend(format_input(config.aes_select))
        current = _merge_aesthetic(config.aes_select, current)
        lines.append("  Resolved:")
        lines.extend(format_aes(current, prev))
        lines.append("")
        prev = current
    else:
        lines.append("[3] SELECT (skipped - not selected)")
        lines.append("")

    # Layer 4: HOVER
    if state.is_hovered:
        lines.append("[4] HOVER (is_hovered=True)")
        hover_aes_preview: BaseAesthetic | None
        if isinstance(config.aes_hover, MissingType):
            hover_aes_preview = _aes_default.hover
            lines.append("  Input (using aes.default.hover):")
        elif config.aes_hover is None:
            hover_aes_preview = None
            lines.append("  Input: None (hover disabled)")
        else:
            hover_aes_preview = config.aes_hover
            lines.append("  Input:")
        lines.extend(format_input(hover_aes_preview))
        current = _merge_aesthetic(hover_aes_preview, current)
        lines.append("  Resolved:")
        lines.extend(format_aes(current, prev))
        lines.append("")
    else:
        lines.append("[4] HOVER (skipped - not hovered)")
        lines.append("")

    lines.append("(* = changed from previous layer)")

    return "\n".join(lines)


__all__ = [
    "PARENT",
    "ParentProperty",
    "RelativeExpr",
    "RegionState",
    "AestheticConfig",
    "resolve_region",
    "preview_region",
]
