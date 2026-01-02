"""Wash factory for creating configured map functions with custom default aesthetics.

Wash() is like preparing a watercolor canvas - it sets the foundational
layer that all maps in your app will build upon.
"""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from ..aes._core import (
    BaseAesthetic,
    ByGroup,
    ByState,
    LineAesthetic,
    PathAesthetic,
    ShapeAesthetic,
    TextAesthetic,
)
from ..mode import Display, ModeType, OutputModeType
from ..types import MISSING, MissingType

if TYPE_CHECKING:
    from htmltools import TagList

    from ..geometry import Outline

# Type alias for Wash() aesthetic parameters
# Accepts ByState, single aesthetic, dict shorthand, None, or MISSING
WashAestheticParam = ByState | BaseAesthetic | dict[str, Any] | None | MissingType

# Type alias for input_map/output_map aes parameter
# Accepts ByGroup for group-wise configuration, or simpler forms
AesParam = ByGroup | ByState | BaseAesthetic | None | MissingType


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
    """Configuration created by Wash() for use by map functions.

    Stores normalized ByState for each element type.
    """

    shape: ByState[ShapeAesthetic] | None | MissingType
    line: ByState[LineAesthetic] | None | MissingType
    text: ByState[TextAesthetic] | None | MissingType

    def get_by_state_for_kind(self, kind: str) -> ByState:
        """Get the ByState for a given element kind, with library defaults.

        Returns a complete ByState with base/select/hover filled from:
        1. This wash config's settings for the element kind
        2. Library defaults where wash config is MISSING

        Args:
            kind: Element kind ("shape", "line", or "text")

        Returns:
            Complete ByState with all layers filled
        """
        from ..aes import _defaults as aes_defaults

        # Get wash config for this kind
        if kind == "line":
            wash_state = self.line
            lib_base = aes_defaults.line
        elif kind == "text":
            wash_state = self.text
            lib_base = aes_defaults.text
        else:  # "shape" or default
            wash_state = self.shape
            lib_base = aes_defaults.shape

        # Build complete ByState with defaults
        if isinstance(wash_state, ByState):
            base = wash_state.base if isinstance(wash_state.base, BaseAesthetic) else lib_base
            select = wash_state.select if isinstance(wash_state.select, BaseAesthetic) else None
            # hover: use wash if set, else library default
            if isinstance(wash_state.hover, BaseAesthetic):
                hover = wash_state.hover
            elif wash_state.hover is None:
                hover = None  # Explicit disable
            else:
                hover = aes_defaults.hover
        else:
            base = lib_base
            select = None
            hover = aes_defaults.hover

        return ByState(base=base, select=select, hover=hover)

    def get_base_for_kind(self, kind: str) -> BaseAesthetic | None:
        """Get the base aesthetic for a given element kind.

        Args:
            kind: Element kind ("shape", "line", or "text")

        Returns:
            The base aesthetic if available, None otherwise
        """
        by_state = self.get_by_state_for_kind(kind)
        if isinstance(by_state.base, BaseAesthetic):
            return by_state.base
        return None

    def apply(
        self,
        aes: ByGroup | ByState | BaseAesthetic | None | MissingType,
        geometry: Outline,
    ) -> ByGroup:
        """Apply user aesthetic on top of this wash config's defaults.

        Resolves MISSING (group inheritance) and fills in wash defaults.
        RelativeExpr values are NOT resolved - they are preserved for JavaScript
        runtime resolution.

        Args:
            aes: User's aesthetic (ByGroup, ByState, BaseAesthetic, None, or MISSING)
            geometry: Outline object with regions and metadata

        Returns:
            Fully resolved ByGroup with all entries having complete ByState values.
            RelativeExpr values are preserved (not resolved).

        Example:
            >>> from shinymap import Wash, aes, PARENT
            >>> wc = Wash(shape=aes.ByState(
            ...     base=aes.Shape(fill_color="#e5e7eb", stroke_width=1.0),
            ...     hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
            ... ))
            >>> resolved = wc.config.apply(aes.Shape(fill_color="#3b82f6"), geometry)
            >>> resolved["__all"].base.fill_color
            '#3b82f6'
            >>> resolved["__all"].base.stroke_width  # inherited from wash
            1.0
            >>> # hover.stroke_width is still RelativeExpr (not resolved)
        """
        # Get region types and groups from geometry
        region_types = geometry.region_types()
        geo_groups = geometry.groups()

        def resolve_path_kind(aesthetic: BaseAesthetic) -> BaseAesthetic:
            """Resolve PathAesthetic.kind against wash config defaults."""
            if isinstance(aesthetic, PathAesthetic) and not isinstance(aesthetic.kind, MissingType):
                parent = self.get_base_for_kind(aesthetic.kind)
                if parent is not None:
                    return aesthetic.resolve(parent)
            return aesthetic

        def resolve_by_state(
            user_by_state: ByState | BaseAesthetic | None | MissingType,
            element_type: str,
        ) -> ByState:
            """Resolve a user ByState against wash defaults for element type.

            MISSING values inherit from wash. RelativeExpr is NOT resolved.
            """
            wash_by_state = self.get_by_state_for_kind(element_type)
            resolved_base = wash_by_state.base
            resolved_select = wash_by_state.select
            resolved_hover = wash_by_state.hover

            if isinstance(user_by_state, ByState):
                # Apply user base
                if isinstance(user_by_state.base, BaseAesthetic):
                    user_base = resolve_path_kind(user_by_state.base)
                    resolved_base = user_base.resolve(resolved_base)  # type: ignore[assignment]

                # Apply user select
                if not isinstance(user_by_state.select, MissingType):
                    if user_by_state.select is None:
                        resolved_select = None
                    elif isinstance(user_by_state.select, BaseAesthetic):
                        user_select = resolve_path_kind(user_by_state.select)
                        parent = resolved_select if resolved_select else resolved_base
                        resolved_select = user_select.resolve(parent)  # type: ignore[assignment]

                # Apply user hover
                if not isinstance(user_by_state.hover, MissingType):
                    if user_by_state.hover is None:
                        resolved_hover = None
                    elif isinstance(user_by_state.hover, BaseAesthetic):
                        user_hover = resolve_path_kind(user_by_state.hover)
                        parent = resolved_hover if resolved_hover else resolved_base
                        resolved_hover = user_hover.resolve(parent)  # type: ignore[assignment]

            elif isinstance(user_by_state, BaseAesthetic):
                # Single aesthetic applies as base only
                user_base = resolve_path_kind(user_by_state)
                resolved_base = user_base.resolve(resolved_base)  # type: ignore[assignment]

            # NOTE: We do NOT resolve RelativeExpr here - that's done by JavaScript

            return ByState(
                base=resolved_base,
                select=resolved_select,
                hover=resolved_hover,
            )

        # Normalize user aes to ByGroup
        user_by_group: ByGroup
        if isinstance(aes, ByGroup):
            user_by_group = aes
        elif isinstance(aes, (ByState, BaseAesthetic)):
            user_by_group = ByGroup(__all=aes)
        else:
            user_by_group = ByGroup()

        # Build result ByGroup
        result_entries: dict[str, ByState | BaseAesthetic | None | MissingType] = {}

        # 1. Always add __all (from wash defaults + user __all if present)
        user_all = user_by_group.get("__all", MISSING)
        result_entries["__all"] = resolve_by_state(user_all, "shape")

        # 2. Add type defaults if user provided them
        for type_key in ["__shape", "__line", "__text"]:
            user_type = user_by_group.get(type_key, MISSING)
            if not isinstance(user_type, MissingType):
                elem_type = type_key[2:]  # Remove "__" prefix
                result_entries[type_key] = resolve_by_state(user_type, elem_type)

        # 3. Add group entries
        for group_name in geo_groups:
            user_group = user_by_group.get(group_name, MISSING)
            if not isinstance(user_group, MissingType):
                # Groups default to shape type
                result_entries[group_name] = resolve_by_state(user_group, "shape")

        # 4. Add individual region entries
        for region_id in geometry.regions:
            user_region = user_by_group.get(region_id, MISSING)
            if not isinstance(user_region, MissingType):
                elem_type = region_types.get(region_id, "shape")
                result_entries[region_id] = resolve_by_state(user_region, elem_type)

        return ByGroup(**result_entries)


class WashResult:
    """Functions configured by Wash().

    Provides configured versions of input_map, output_map, and render_map
    that use the Wash's default aesthetics.
    """

    def __init__(self, config: WashConfig) -> None:
        self.config = config

    def input_map(
        self,
        id: str,
        geometry: Outline,
        mode: Literal["single", "multiple"] | ModeType,
        *,
        tooltips: dict[str, str] | None = None,
        aes: AesParam = MISSING,
        value: dict[str, int] | None = None,
        view_box: tuple[float, float, float, float] | None = None,
        layers: dict[str, list[str]] | None = None,
        raw: bool = False,
        width: str | None = "100%",
        height: str | None = "320px",
        class_: str | None = None,
        style: MutableMapping[str, str] | None = None,
    ) -> TagList:
        """Create interactive map with Wash aesthetics applied.

        Args:
            id: Input ID for Shiny
            geometry: Outline object
            mode: Interaction mode ("single", "multiple", or Mode class instance)
            tooltips: Region tooltips as {region_id: tooltip_text}
            aes: Aesthetic overrides (ByGroup, ByState, or BaseAesthetic).
                Merged with Wash defaults.
            value: Initial selection state
            view_box: Override viewBox tuple
            layers: Layer configuration {underlays: [...], overlays: [...], hidden: [...]}
            raw: If True, return raw dict[str, int] value instead of transformed
                types (str for single, list for multiple). Useful when you need
                consistent dict format regardless of mode.
            width: Container width (CSS)
            height: Container height (CSS)
            class_: Additional CSS classes
            style: Additional inline styles

        Returns:
            TagList with the map component
        """
        from ._input_map import _input_map

        # Resolve aes against wash config
        resolved_aes = self.config.apply(aes, geometry)

        return _input_map(
            id,
            geometry,
            mode,
            resolved_aes,
            tooltips,
            value,
            view_box,
            layers,
            raw,
            width,
            height,
            class_,
            style,
        )

    def output_map(
        self,
        id: str,
        geometry: Outline | None = None,
        *,
        mode: Display = Display(),
        aes: AesParam = MISSING,
        tooltips: dict[str, str] | None = None,
        view_box: tuple[float, float, float, float] | None = None,
        layers: dict[str, list[str]] | None = None,
        width: str | None = "100%",
        height: str | None = "320px",
        class_: str | None = None,
        style: MutableMapping[str, str] | None = None,
    ) -> TagList:
        """UI placeholder for a @render_map output with Wash aesthetics.

        Args:
            id: Output ID (must match @render_map function name)
            geometry: Outline object
            mode: Display mode with optional indexed aesthetics.
                  Use Display(aes=aes.Indexed(...)) to prepopulate the
                  value-to-color mapping in the UI declaration.
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

        Example:
            >>> from shinymap import output_map, aes
            >>> from shinymap.mode import Display
            >>>
            >>> # Prepopulate color scale in UI declaration
            >>> output_map(
            ...     "status_map",
            ...     geometry,
            ...     mode=Display(aes=aes.Indexed(
            ...         fill_color=["#f3f4f6", "#22c55e", "#f59e0b", "#ef4444"]
            ...     ))
            ... )
        """
        from ._output_map import _output_map

        # Resolve aes against wash config (geometry required for resolution)
        if geometry is not None:
            resolved_aes = self.config.apply(aes, geometry)
        else:
            # No geometry - create empty ByGroup (will be populated later)
            resolved_aes = ByGroup()

        return _output_map(
            id,
            geometry,
            mode,
            resolved_aes,
            tooltips,
            view_box,
            layers,
            width,
            height,
            class_,
            style,
        )

    def render_map(self, fn: Callable | None = None) -> Callable:
        """Shiny render decorator with Wash aesthetics.

        Works exactly like the base render_map decorator.
        Wash aesthetics are applied via output_map().
        """
        from ._render_map import _render_map

        return _render_map(fn)  # type: ignore[no-any-return]


def Wash(
    *,
    shape: ByState[ShapeAesthetic] | ShapeAesthetic | dict[str, Any] | None | MissingType = MISSING,
    line: ByState[LineAesthetic] | LineAesthetic | dict[str, Any] | None | MissingType = MISSING,
    text: ByState[TextAesthetic] | TextAesthetic | dict[str, Any] | None | MissingType = MISSING,
) -> WashResult:
    """Create configured map functions with custom default aesthetics.

    Wash() is like preparing a watercolor canvas - it sets the foundational
    layer that all maps in your app will build upon.

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
    Wash() only understands element types (shape, line, text). Group-specific
    aesthetics (like "coastal", "mountain") should be specified in input_map/output_map
    using the aes parameter with ByGroup.

    Examples
    --------
    >>> from shinymap import Wash, aes
    >>> from shinymap.relative import PARENT
    >>>
    >>> # Full form with ByState for each element type
    >>> wc = Wash(
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
    >>> wc = Wash(
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
        shape=_normalize_to_by_state(shape, ShapeAesthetic.from_dict),
        line=_normalize_to_by_state(line, LineAesthetic.from_dict),
        text=_normalize_to_by_state(text, TextAesthetic.from_dict),
    )

    return WashResult(config)


__all__ = ["Wash", "WashResult", "WashConfig"]
