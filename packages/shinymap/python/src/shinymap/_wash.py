"""Wash factory for creating configured map functions with custom default aesthetics.

The wash() function is like preparing a watercolor canvas - it sets the foundational
layer that all maps in your app will build upon.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from ._aesthetics import (
    BaseAesthetic,
    ByGroup,
    ByState,
    LineAesthetic,
    PathAesthetic,
    ShapeAesthetic,
    TextAesthetic,
)
from ._sentinel import MISSING, MissingType
from .mode import ModeType

if TYPE_CHECKING:
    from htmltools import TagList

    from .geometry import Geometry

# Type alias for wash() aesthetic parameters
# Accepts ByState, single aesthetic, dict shorthand, None, or MISSING
WashAestheticParam = ByState | BaseAesthetic | dict[str, Any] | None | MissingType

# Type alias for input_map/output_map aes parameter
# Accepts ByGroup for group-wise configuration, or simpler forms
AesParam = ByGroup | ByState | BaseAesthetic | None | MissingType

# Valid keys for each aesthetic type
_SHAPE_KEYS = {
    "fill_color",
    "fill_opacity",
    "stroke_color",
    "stroke_width",
    "stroke_dasharray",
    "non_scaling_stroke",
}
_LINE_KEYS = {"stroke_color", "stroke_width", "stroke_dasharray", "non_scaling_stroke"}
_TEXT_KEYS = {
    "fill_color",
    "fill_opacity",
    "stroke_color",
    "stroke_width",
    "stroke_dasharray",
    "non_scaling_stroke",
}


def _warn_unknown_keys(d: dict[str, Any], valid_keys: set[str], aesthetic_type: str) -> None:
    """Warn if dict contains keys not recognized by the aesthetic type."""
    unknown = set(d.keys()) - valid_keys
    if unknown:
        warnings.warn(
            f"Unknown keys for {aesthetic_type}: {unknown}. Valid keys are: {sorted(valid_keys)}",
            UserWarning,
            stacklevel=4,  # Caller -> _normalize_to_by_state -> _dict_to_* -> here
        )


def _dict_to_shape(d: dict[str, Any]) -> ShapeAesthetic:
    """Convert a dict to ShapeAesthetic."""
    _warn_unknown_keys(d, _SHAPE_KEYS, "Shape")
    return ShapeAesthetic(
        fill_color=d.get("fill_color", MISSING),
        fill_opacity=d.get("fill_opacity", MISSING),
        stroke_color=d.get("stroke_color", MISSING),
        stroke_width=d.get("stroke_width", MISSING),
        stroke_dasharray=d.get("stroke_dasharray", MISSING),
        non_scaling_stroke=d.get("non_scaling_stroke", MISSING),
    )


def _dict_to_line(d: dict[str, Any]) -> LineAesthetic:
    """Convert a dict to LineAesthetic."""
    _warn_unknown_keys(d, _LINE_KEYS, "Line")
    return LineAesthetic(
        stroke_color=d.get("stroke_color", MISSING),
        stroke_width=d.get("stroke_width", MISSING),
        stroke_dasharray=d.get("stroke_dasharray", MISSING),
        non_scaling_stroke=d.get("non_scaling_stroke", MISSING),
    )


def _dict_to_text(d: dict[str, Any]) -> TextAesthetic:
    """Convert a dict to TextAesthetic."""
    _warn_unknown_keys(d, _TEXT_KEYS, "Text")
    return TextAesthetic(
        fill_color=d.get("fill_color", MISSING),
        fill_opacity=d.get("fill_opacity", MISSING),
        stroke_color=d.get("stroke_color", MISSING),
        stroke_width=d.get("stroke_width", MISSING),
        stroke_dasharray=d.get("stroke_dasharray", MISSING),
        non_scaling_stroke=d.get("non_scaling_stroke", MISSING),
    )


def _normalize_to_by_state[T: BaseAesthetic](
    value: ByState[T] | T | dict[str, Any] | None | MissingType,
    dict_converter: Callable[[dict[str, Any]], T],
) -> ByState[T] | None | MissingType:
    """Normalize a wash aesthetic parameter to ByState.

    - MISSING -> MISSING (inherit library defaults)
    - None -> None (invisible/disabled)
    - dict -> ByState(base=dict_converter(dict))
    - BaseAesthetic -> ByState(base=aesthetic)
    - ByState -> pass through
    """
    if isinstance(value, MissingType):
        return MISSING
    if value is None:
        return None
    if isinstance(value, ByState):
        return value
    if isinstance(value, dict):
        return ByState(base=dict_converter(value))
    # Single aesthetic -> wrap as base only
    return ByState(base=value)


@dataclass
class WashConfig:
    """Configuration created by wash() for use by map functions.

    Stores normalized ByState for each element type.
    """

    shape: ByState[ShapeAesthetic] | None | MissingType
    line: ByState[LineAesthetic] | None | MissingType
    text: ByState[TextAesthetic] | None | MissingType


class WashResult:
    """Functions configured by wash().

    Provides configured versions of input_map, output_map, and render_map
    that use the wash's default aesthetics.
    """

    def __init__(self, config: WashConfig) -> None:
        self.config = config

    def input_map(
        self,
        id: str,
        geometry: Geometry,
        mode: Literal["single", "multiple"] | ModeType,
        *,
        tooltips: dict[str, str] | None = None,
        aes: AesParam = MISSING,
        value: dict[str, int] | None = None,
        view_box: tuple[float, float, float, float] | None = None,
        layers: dict[str, list[str]] | None = None,
        width: str | None = "100%",
        height: str | None = "320px",
        class_: str | None = None,
        style: MutableMapping[str, str] | None = None,
    ) -> TagList:
        """Create interactive map with wash aesthetics applied.

        Args:
            id: Input ID for Shiny
            geometry: Geometry object
            mode: Interaction mode ("single", "multiple", or Mode class instance)
            tooltips: Region tooltips as {region_id: tooltip_text}
            aes: Aesthetic overrides (ByGroup, ByState, or BaseAesthetic).
                Merged with wash defaults.
            value: Initial selection state
            view_box: Override viewBox tuple
            layers: Layer configuration {underlays: [...], overlays: [...], hidden: [...]}
            width: Container width (CSS)
            height: Container height (CSS)
            class_: Additional CSS classes
            style: Additional inline styles

        Returns:
            TagList with the map component
        """
        from ._base import base_input_map

        return base_input_map(
            id,
            geometry,
            mode,
            tooltips=tooltips,
            value=value,
            view_box=view_box,
            aes=aes,
            wash_config=self.config,
            layers=layers,
            width=width,
            height=height,
            class_=class_,
            style=style,
        )

    def output_map(
        self,
        id: str,
        geometry: Geometry | None = None,
        *,
        aes: AesParam = MISSING,
        tooltips: dict[str, str] | None = None,
        view_box: tuple[float, float, float, float] | None = None,
        layers: dict[str, list[str]] | None = None,
        width: str | None = "100%",
        height: str | None = "320px",
        class_: str | None = None,
        style: MutableMapping[str, str] | None = None,
    ) -> TagList:
        """UI placeholder for a @render_map output with wash aesthetics.

        Args:
            id: Output ID (must match @render_map function name)
            geometry: Geometry object
            aes: Group-wise aesthetic overrides
            tooltips: Optional static tooltips
            view_box: Optional viewBox tuple
            layers: Layer configuration {underlays: [...], overlays: [...], hidden: [...]}
            width: Container width (CSS)
            height: Container height (CSS)
            class_: Additional CSS classes
            style: Additional inline styles

        Returns:
            TagList with the output container
        """
        from ._base import base_output_map

        return base_output_map(
            id,
            geometry,
            tooltips=tooltips,
            view_box=view_box,
            aes=aes,
            wash_config=self.config,
            layers=layers,
            width=width,
            height=height,
            class_=class_,
            style=style,
        )

    def render_map(self, fn: Callable | None = None) -> Callable:
        """Shiny render decorator with wash aesthetics.

        Works exactly like the base render_map decorator.
        Wash aesthetics are applied via output_map().
        """
        from ._base import base_render_map

        return base_render_map(fn)  # type: ignore[no-any-return]


def _get_wash_defaults_for_kind(config: WashConfig, kind: str) -> dict[str, Any]:
    """Get wash defaults based on kind (shape, line, text).

    Returns a dict of default aesthetic values from the wash config
    for the specified element kind.
    """
    defaults: dict[str, Any] = {}

    if kind == "line":
        if not isinstance(config.line, MissingType) and config.line is not None:
            if not isinstance(config.line.base, MissingType) and config.line.base is not None:
                defaults = config.line.base.to_dict()
    elif kind == "text":
        if not isinstance(config.text, MissingType) and config.text is not None:
            if not isinstance(config.text.base, MissingType) and config.text.base is not None:
                defaults = config.text.base.to_dict()
    else:  # "shape" or default
        if not isinstance(config.shape, MissingType) and config.shape is not None:
            if not isinstance(config.shape.base, MissingType) and config.shape.base is not None:
                defaults = config.shape.base.to_dict()

    return defaults


def _apply_path_kind_defaults(aesthetic: BaseAesthetic, config: WashConfig) -> dict[str, Any]:
    """Apply wash defaults based on PathAesthetic.kind, then merge with explicit values.

    For PathAesthetic with kind="line", starts with line defaults from wash config,
    then overrides with any explicitly set values from the aesthetic.
    """
    if isinstance(aesthetic, PathAesthetic) and not isinstance(aesthetic.kind, MissingType):
        # Get defaults for the specified kind
        defaults = _get_wash_defaults_for_kind(config, aesthetic.kind)
        # Get explicit values from the PathAesthetic (excludes MISSING values)
        explicit = aesthetic.to_dict()
        # Remove 'kind' from explicit - it's metadata, not an SVG property
        explicit.pop("kind", None)
        # Merge: defaults first, then explicit overrides
        return {**defaults, **explicit}
    else:
        # Not a PathAesthetic with kind, or kind is MISSING - use as-is
        return aesthetic.to_dict()


def _convert_to_legacy_format(
    config: WashConfig, aes: AesParam
) -> tuple[
    dict[str, Any] | None,  # aes_base
    dict[str, Any] | None | MissingType,  # aes_hover
    dict[str, Any] | None,  # aes_select
    dict[str, dict[str, Any]] | None,  # aes_group
]:
    """Convert wash config and aes parameter to legacy format.

    This is a temporary bridge until TypeScript supports the new ByGroup/ByState format.
    """
    aes_base: dict[str, Any] | None = None
    aes_hover: dict[str, Any] | None | MissingType = MISSING
    aes_select: dict[str, Any] | None = None
    aes_group: dict[str, dict[str, Any]] | None = None

    # Extract from wash config (shape element type for now)
    if not isinstance(config.shape, MissingType) and config.shape is not None:
        shape_states = config.shape
        if not isinstance(shape_states.base, MissingType) and shape_states.base is not None:
            aes_base = shape_states.base.to_dict()
        if not isinstance(shape_states.hover, MissingType):
            if shape_states.hover is None:
                aes_hover = None
            else:
                aes_hover = shape_states.hover.to_dict()
        if not isinstance(shape_states.select, MissingType) and shape_states.select is not None:
            aes_select = shape_states.select.to_dict()

    # Apply call-site overrides
    if isinstance(aes, ByGroup):
        aes_group = {}
        for group_name in aes.keys():
            group_value = aes[group_name]
            if isinstance(group_value, ByState):
                # Extract base aesthetic for the group
                if not isinstance(group_value.base, MissingType) and group_value.base is not None:
                    aes_group[group_name] = _apply_path_kind_defaults(group_value.base, config)
            elif isinstance(group_value, BaseAesthetic):
                aes_group[group_name] = _apply_path_kind_defaults(group_value, config)
            elif group_value is None:
                aes_group[group_name] = {}  # Empty dict to mark as overridden
    elif isinstance(aes, ByState):
        # Single ByState applies to all (treat as __all)
        if not isinstance(aes.base, MissingType) and aes.base is not None:
            aes_base = _apply_path_kind_defaults(aes.base, config)
        if not isinstance(aes.hover, MissingType):
            if aes.hover is None:
                aes_hover = None
            else:
                aes_hover = _apply_path_kind_defaults(aes.hover, config)
        if not isinstance(aes.select, MissingType) and aes.select is not None:
            aes_select = _apply_path_kind_defaults(aes.select, config)
    elif isinstance(aes, BaseAesthetic):
        # Single aesthetic applies as base
        aes_base = _apply_path_kind_defaults(aes, config)
    elif aes is None:
        # Explicit None disables aesthetics
        aes_base = {}

    return aes_base, aes_hover, aes_select, aes_group


def _convert_to_aes_dict(config: WashConfig, aes: AesParam) -> dict[str, Any] | None:
    """Convert wash config and aes parameter to new nested aes dict format.

    Returns a dict with keys: base, hover, select, group
    Each value is a dict of aesthetic properties ready for JavaScript (snake_case keys).
    The _camel_props function in _base.py will convert to camelCase when serializing.
    """
    result: dict[str, Any] = {}

    # Step 1: Extract from wash config (shape element type for now)
    if not isinstance(config.shape, MissingType) and config.shape is not None:
        shape_states = config.shape
        if not isinstance(shape_states.base, MissingType) and shape_states.base is not None:
            result["base"] = shape_states.base.to_dict()
        if not isinstance(shape_states.hover, MissingType):
            if shape_states.hover is None:
                result["hover"] = None
            else:
                result["hover"] = shape_states.hover.to_dict()
        if not isinstance(shape_states.select, MissingType) and shape_states.select is not None:
            result["select"] = shape_states.select.to_dict()

    # Step 2: Apply call-site overrides
    if isinstance(aes, ByGroup):
        aes_group: dict[str, Any] = {}
        for group_name in aes.keys():
            group_value = aes[group_name]
            if isinstance(group_value, ByState):
                # Extract base aesthetic for the group
                if not isinstance(group_value.base, MissingType) and group_value.base is not None:
                    aes_group[group_name] = _apply_path_kind_defaults(group_value.base, config)
            elif isinstance(group_value, BaseAesthetic):
                aes_group[group_name] = _apply_path_kind_defaults(group_value, config)
            elif group_value is None:
                aes_group[group_name] = {}
        if aes_group:
            result["group"] = aes_group
    elif isinstance(aes, ByState):
        # Single ByState overrides wash defaults
        if not isinstance(aes.base, MissingType) and aes.base is not None:
            result["base"] = _apply_path_kind_defaults(aes.base, config)
        if not isinstance(aes.hover, MissingType):
            if aes.hover is None:
                result["hover"] = None
            else:
                result["hover"] = _apply_path_kind_defaults(aes.hover, config)
        if not isinstance(aes.select, MissingType) and aes.select is not None:
            result["select"] = _apply_path_kind_defaults(aes.select, config)
    elif isinstance(aes, BaseAesthetic):
        # Single aesthetic applies as base
        result["base"] = _apply_path_kind_defaults(aes, config)
    elif aes is None:
        # Explicit None disables aesthetics
        result["base"] = {}

    return result if result else None


def wash(
    *,
    shape: ByState[ShapeAesthetic] | ShapeAesthetic | dict[str, Any] | None | MissingType = MISSING,
    line: ByState[LineAesthetic] | LineAesthetic | dict[str, Any] | None | MissingType = MISSING,
    text: ByState[TextAesthetic] | TextAesthetic | dict[str, Any] | None | MissingType = MISSING,
) -> WashResult:
    """Create configured map functions with custom default aesthetics.

    The wash() function is like preparing a watercolor canvas - it sets
    the foundational layer that all maps in your app will build upon.

    Parameters
    ----------
    shape
        Aesthetics for shape elements (Circle, Rect, Path, Polygon, Ellipse).
        Can be:
        - ByState: Full state configuration (base, select, hover)
        - ShapeAesthetic: Base state only (via aes.Shape())
        - dict: Shorthand for base state (e.g., {"fill_color": "#f0f9ff"})
        - None: Shapes invisible/disabled
        - MISSING: Inherit library defaults
    line
        Aesthetics for line elements. Same value types as shape.
    text
        Aesthetics for text elements. Same value types as shape.

    Returns
    -------
    WashResult
        An object with configured input_map, output_map, and render_map
        methods that use the wash's default aesthetics.

    Notes
    -----
    wash() only understands element types (shape, line, text). Group-specific
    aesthetics (like "coastal", "mountain") should be specified in input_map/output_map
    using the aes parameter with ByGroup.

    Examples
    --------
    >>> from shinymap import wash, aes, PARENT
    >>>
    >>> # Full form with ByState for each element type
    >>> wc = wash(
    ...     shape=aes.ByState(
    ...         base=aes.Shape(fill_color="#f0f9ff", stroke_color="#0369a1"),
    ...         select=aes.Shape(fill_color="#7dd3fc"),
    ...         hover=aes.Shape(stroke_width=PARENT.stroke_width + 2),
    ...     ),
    ...     line=aes.ByState(
    ...         base=aes.Line(stroke_color="#0369a1"),
    ...         hover=aes.Line(stroke_width=PARENT.stroke_width + 1),
    ...     ),
    ...     text=aes.Text(fill_color="#0c4a6e"),  # base only shorthand
    ... )
    >>>
    >>> # Dict shorthand for simple base-only configuration
    >>> wc = wash(
    ...     shape={"fill_color": "#f0f9ff", "stroke_color": "#0369a1"},
    ...     line={"stroke_color": "#0369a1"},
    ... )
    >>>
    >>> # Use the configured functions
    >>> wc.input_map("region", geometry)
    >>>
    >>> @wc.render_map
    ... def my_map():
    ...     return Map(geometry)
    """
    config = WashConfig(
        shape=_normalize_to_by_state(shape, _dict_to_shape),
        line=_normalize_to_by_state(line, _dict_to_line),
        text=_normalize_to_by_state(text, _dict_to_text),
    )

    return WashResult(config)


__all__ = ["wash", "WashResult", "WashConfig"]
