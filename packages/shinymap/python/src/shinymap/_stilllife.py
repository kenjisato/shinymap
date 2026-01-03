"""StillLife class for static map analysis and export.

Like a still life painting, this class captures a map's state at a
specific moment for aesthetic inspection and static SVG export.

The painting metaphor:
- Wash: Prepare the canvas with default colors (like a watercolor wash)
- Map/MapBuilder: Work in progress, dynamic and changing
- StillLife: Static captured scene, ready for analysis and display
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .aes._core import BaseAesthetic, ByGroup, ByState
from .relative import AestheticConfig, RegionState, resolve_region
from .types import MISSING, MissingType

if TYPE_CHECKING:
    from ._map import MapBuilder
    from .outline import Outline


class StillLife:
    """Static snapshot of a map for aesthetic analysis and SVG export.

    Like a still life painting, this class captures a map's state at a
    specific moment, allowing you to:

    - Inspect resolved aesthetics for any region
    - Export a static SVG with specific hover/selection states

    StillLife requires a `MapBuilder` created via `WashResult.build()`, which
    populates the private `_outline` and `_resolved_aes` fields.

    Examples:
        >>> from shinymap import Wash, StillLife, aes, Outline
        >>> wc = Wash(shape=aes.ByState(
        ...     base=aes.Shape(fill_color="#e2e8f0"),
        ...     select=aes.Shape(fill_color="#3b82f6"),
        ... ))
        >>> outline = Outline.from_dict({"a": "M 0 0 L 10 10", "b": "M 20 0 L 30 10"})
        >>> builder = wc.build(outline, value={"a": 1, "b": 0})
        >>> pic = StillLife(builder)
        >>> pic.aes("a")["fill_color"]  # Selected (value=1)
        '#3b82f6'
        >>> pic.aes("b")["fill_color"]  # Not selected (value=0)
        '#e2e8f0'
    """

    def __init__(
        self,
        builder: MapBuilder,
        *,
        value: dict[str, int] | None = None,
        hovered: str | None = None,
    ):
        """Create a still life from a MapBuilder.

        Args:
            builder: MapBuilder created via WashResult.build().
                Must have _outline and _resolved_aes populated.
            value: Override value dict. If None, uses builder's value.
            hovered: Region ID to show as hovered.

        Raises:
            ValueError: If builder lacks required _outline or _resolved_aes.

        Examples:
            >>> from shinymap import Wash, StillLife, aes, Outline
            >>> wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))
            >>> outline = Outline.from_dict({"a": "M 0 0 L 10 10"})
            >>> builder = wc.build(outline, value={"a": 1})
            >>> pic = StillLife(builder)
            >>> pic = StillLife(builder, value={"a": 0})  # Override value
            >>> pic = StillLife(builder, hovered="a")  # With hover state
        """
        # Validate builder has required fields
        if builder._outline is None:
            raise ValueError(
                "MapBuilder lacks _outline. "
                "Use WashResult.build() to create a MapBuilder for StillLife."
            )
        if builder._resolved_aes is None:
            raise ValueError(
                "MapBuilder lacks _resolved_aes. "
                "Use WashResult.build() to create a MapBuilder for StillLife."
            )

        self._outline: Outline = builder._outline
        self._resolved_aes: ByGroup = builder._resolved_aes
        self._value: Mapping[str, int] = value if value is not None else (builder._value or {})
        self._hovered: str | None = hovered

    def _lookup_by_state(self, region_id: str) -> ByState:
        """Look up the ByState for a region following the resolution hierarchy.

        Resolution order:
        1. Exact region_id match
        2. Group match (if region belongs to a group)
        3. Element type match (__shape, __line, __text)
        4. Global fallback (__all)

        Args:
            region_id: The region ID to look up

        Returns:
            ByState for the region (may be from higher level in hierarchy)
        """
        # 1. Check for exact region match
        region_entry = self._resolved_aes.get(region_id, MISSING)
        if isinstance(region_entry, ByState):
            return region_entry

        # 2. Check for group match
        groups = self._outline.groups()
        region_group = None
        for group_name, region_ids in groups.items():
            if region_id in region_ids:
                region_group = group_name
                break

        if region_group:
            group_entry = self._resolved_aes.get(region_group, MISSING)
            if isinstance(group_entry, ByState):
                return group_entry

        # 3. Check for element type match
        region_types = self._outline.region_types()
        elem_type = region_types.get(region_id, "shape")
        type_key = f"__{elem_type}"
        type_entry = self._resolved_aes.get(type_key, MISSING)
        if isinstance(type_entry, ByState):
            return type_entry

        # 4. Fall back to __all
        all_entry = self._resolved_aes.get("__all", MISSING)
        if isinstance(all_entry, ByState):
            return all_entry

        # Should not happen if WashResult.build() was used correctly
        from .aes import _defaults as aes_defaults

        return ByState(base=aes_defaults.shape)

    def _build_aesthetic_config(self, by_state: ByState) -> AestheticConfig:
        """Build AestheticConfig from ByState for resolve_region().

        Args:
            by_state: ByState with base, select, hover aesthetics

        Returns:
            AestheticConfig ready for resolve_region()
        """
        # Extract base, select, hover from ByState
        aes_base = by_state.base if isinstance(by_state.base, BaseAesthetic) else None
        aes_select = by_state.select if isinstance(by_state.select, BaseAesthetic) else None

        # Handle hover: MISSING means use default, None means disabled
        aes_hover: BaseAesthetic | None | MissingType
        if isinstance(by_state.hover, BaseAesthetic):
            aes_hover = by_state.hover
        elif by_state.hover is None:
            aes_hover = None
        else:
            aes_hover = MISSING

        return AestheticConfig(
            aes_base=aes_base,
            aes_select=aes_select,
            aes_hover=aes_hover,
        )

    def aes(
        self,
        region: str,
        *,
        is_hovered: bool | None = None,
    ) -> dict[str, Any]:
        """Get resolved aesthetic for a region.

        Args:
            region: Region ID to get aesthetic for
            is_hovered: Override hover state. If None, uses the hovered
                region set in StillLife constructor.

        Returns:
            Dict of resolved aesthetic properties (fill_color, stroke_width, etc.)

        Examples:
            >>> from shinymap import Wash, StillLife, aes, Outline
            >>> wc = Wash(shape=aes.ByState(
            ...     base=aes.Shape(fill_color="#e2e8f0", stroke_width=1.0),
            ...     select=aes.Shape(fill_color="#3b82f6"),
            ... ))
            >>> outline = Outline.from_dict({"a": "M 0 0 L 10 10"})
            >>> builder = wc.build(outline, value={"a": 1})
            >>> pic = StillLife(builder)
            >>> resolved = pic.aes("a")
            >>> resolved["fill_color"]
            '#3b82f6'
            >>> resolved["stroke_width"]
            1.0
        """
        # Look up ByState for region
        by_state = self._lookup_by_state(region)

        # Build config
        config = self._build_aesthetic_config(by_state)

        # Get value and determine hover state
        value = self._value.get(region, 0)

        # Determine hover state
        if is_hovered is not None:
            hovered = is_hovered
        else:
            hovered = self._hovered == region

        # Get group for region
        groups = self._outline.groups()
        region_group = None
        for group_name, region_ids in groups.items():
            if region in region_ids:
                region_group = group_name
                break

        # Build state
        state = RegionState(
            region_id=region,
            value=value,
            is_hovered=hovered,
            group=region_group,
        )

        # TODO: resolve_region() always returns ShapeAesthetic regardless of element type.
        #       This means Line/Text elements get fill_color/fill_opacity which don't apply.
        #       Consider adding element type awareness to return LineAesthetic/TextAesthetic.
        #       See: https://github.com/kenjisato/shinymap/issues/3
        resolved = resolve_region(state, config)
        return self._aesthetic_to_dict(resolved)

    def _aesthetic_to_dict(self, aes: BaseAesthetic) -> dict[str, Any]:
        """Convert a resolved aesthetic to a dict.

        Args:
            aes: Resolved BaseAesthetic (ShapeAesthetic, LineAesthetic, etc.)

        Returns:
            Dict with all aesthetic properties
        """
        result: dict[str, Any] = {}
        for f in fields(aes):
            value = getattr(aes, f.name)
            if not isinstance(value, MissingType):
                result[f.name] = value
        return result

    def aes_table(
        self,
        *,
        region_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get resolved aesthetics for multiple regions.

        Args:
            region_ids: Specific region IDs to include. If None, includes
                all regions in the outline.

        Returns:
            List of dicts, each containing region_id and resolved aesthetics.

        Examples:
            >>> from shinymap import Wash, StillLife, aes, Outline
            >>> wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))
            >>> outline = Outline.from_dict({"a": "M 0 0", "b": "M 10 0"})
            >>> builder = wc.build(outline, value={"a": 1, "b": 0})
            >>> pic = StillLife(builder)
            >>> table = pic.aes_table()
            >>> len(table)
            2
            >>> table[0]["region_id"] in ["a", "b"]
            True
        """
        # Determine which regions to include
        if region_ids is None:
            region_ids = list(self._outline.regions.keys())

        result: list[dict[str, Any]] = []
        for region_id in region_ids:
            aes_dict = self.aes(region_id)
            aes_dict["region_id"] = region_id
            result.append(aes_dict)

        return result

    def to_svg(
        self,
        output: str | Path | None = None,
    ) -> str | None:
        """Generate static SVG with resolved aesthetics.

        Note: This method will be implemented in Phase 2.

        Args:
            output: If provided, write SVG to file and return None.
                If None, return SVG as string.

        Returns:
            SVG string if output is None, otherwise None.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError(
            "StillLife.to_svg() will be implemented in Phase 2. "
            "See design/static-map-and-aes-dump.md for details."
        )


__all__ = ["StillLife"]
