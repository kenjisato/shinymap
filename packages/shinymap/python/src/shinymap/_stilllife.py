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

from .aes._core import BaseAesthetic, ByGroup, ByState, IndexedAesthetic
from .relative import AestheticConfig, RegionState, resolve_region
from .types import MISSING, MissingType

if TYPE_CHECKING:
    from ._map import MapBuilder
    from .outline import Outline
    from .uicore._wash import WashResult


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
        output_id: str | None = None,
        wash: WashResult | None = None,
    ):
        """Create a still life from a map.

        Pass what ``@render_map`` returns, ``Map(...)``, to draw the map as the
        browser shows it, or a builder from ``Wash.build()``.

        Args:
            builder: ``Map(...)``, or a MapBuilder from ``WashResult.build()``.
            value: Override value dict. If None, uses builder's value.
            hovered: Region ID to show as hovered.
            output_id: ID of an ``output_map()``. The picture then uses that
                output's outline, mode, wash and ``aes``, with the map layered over
                them exactly as ``@render_map`` does, so ``Map()`` needs no outline.
            wash: Wash to draw a ``Map(...)`` with, when there is no
                ``output_map()`` to follow. Default: ``shinymap.default_wash``.

        Raises:
            ValueError: If both ``output_id`` and ``wash`` are given, if
                ``output_id`` names no ``output_map()``, if there is no outline,
                or if a ``Wash.build()`` builder is combined with either.

        Examples:
            ```pycon
            >>> from shinymap import Map, Outline, StillLife, output_map
            >>> outline = Outline.from_dict({"a": "M 0 0 L 10 0 L 10 10 Z"})
            >>> pic = StillLife(Map(outline, fill_color={"a": "#ff0000"}))
            >>> pic.aes("a")["fill_color"]
            '#ff0000'
            >>> _ = output_map("result", outline)
            >>> pic = StillLife(Map(fill_color={"a": "#00ff00"}), output_id="result")
            >>> pic.aes("a")["fill_color"]
            '#00ff00'

            ```
        """
        if output_id is not None and wash is not None:
            raise ValueError(
                "Pass either output_id= (follow an output_map()) or wash=, not both: "
                "the output already has its wash."
            )

        if builder._resolved_aes is not None:
            if output_id is not None or wash is not None:
                raise ValueError(
                    "This builder comes from Wash.build() and already has its look; "
                    "pass Map(...) to use output_id= or wash=."
                )
            outline = builder._outline
            resolved_aes = builder._resolved_aes
            mode = getattr(builder, "_mode", None)
        else:
            from .uicore._render_map import _resolve_map_aes

            static: Mapping[str, Any]
            if output_id is not None:
                from shiny.module import resolve_id

                from .uicore._registry import _static_map_params

                key = resolve_id(output_id)
                if key not in _static_map_params:
                    raise ValueError(
                        f"No output_map({output_id!r}) found. Call output_map() first, "
                        "or pass wash= to draw the map on its own."
                    )
                static = _static_map_params[key]
            elif wash is not None:
                static = {"wash_config": wash.config}
            else:
                static = {}

            outline = static.get("outline") or builder._outline
            if outline is None:
                raise ValueError(
                    "StillLife needs an outline: pass it to Map(outline, ...), "
                    "or pass output_id= of an output_map() that has one."
                )
            if builder._layers is not None:
                layers = {k: v for k, v in builder._layers.items() if v is not None}
                outline = outline.merge_layers(layers)
            resolved_aes = _resolve_map_aes(builder._aes, static, outline)
            mode = static.get("mode")

        if outline is None:
            raise ValueError("MapBuilder lacks _outline.")

        self._outline: Outline = outline
        self._resolved_aes: ByGroup = resolved_aes
        self._value: Mapping[str, int] = value if value is not None else (builder._value or {})
        self._hovered: str | None = hovered
        self._mode: Any = mode

    def _region_group(self, region_id: str) -> str | None:
        for group_name, region_ids in self._outline.groups().items():
            if region_id in region_ids:
                return group_name
        return None

    def _uses_indexed(self) -> bool:
        """Whether the mode carries indexed aesthetics (JS then skips selection)."""
        return isinstance(getattr(self._mode, "aes", None), (IndexedAesthetic, ByGroup))

    def _indexed_for(self, region_id: str) -> IndexedAesthetic | None:
        """The indexed aesthetic that applies to a region, as in the JS components.

        ``mode.aes`` is either one ``aes.Indexed`` for every region, or an
        ``aes.ByGroup`` of them keyed by region ID or group name.
        """
        mode_aes = getattr(self._mode, "aes", None)
        if isinstance(mode_aes, IndexedAesthetic):
            return mode_aes
        if isinstance(mode_aes, ByGroup):
            direct = mode_aes.get(region_id, MISSING)
            if isinstance(direct, IndexedAesthetic):
                return direct
            group = self._region_group(region_id)
            if group is not None:
                by_group = mode_aes.get(group, MISSING)
                if isinstance(by_group, IndexedAesthetic):
                    return by_group
        return None

    def _apply_indexed(
        self, aesthetic: BaseAesthetic, indexed: IndexedAesthetic, count: int
    ) -> BaseAesthetic:
        """Override the properties ``indexed`` defines, picked by ``count``.

        Cycle wraps (``count % n``, then modulo the list length); other modes
        clamp to the last entry. This mirrors ``resolveIndexedAesthetic`` in JS.
        """
        import dataclasses

        n = getattr(self._mode, "n", None)
        wrap = isinstance(n, int) and n > 0
        max_count = getattr(self._mode, "max_count", None)
        if isinstance(max_count, int):
            count = min(count, max_count)  # Count(max_count=k)
        index = count % n if isinstance(n, int) and n > 0 else count

        names = {f.name for f in dataclasses.fields(aesthetic)}
        overrides: dict[str, Any] = {}
        for name in (
            "fill_color",
            "fill_opacity",
            "stroke_color",
            "stroke_width",
            "stroke_dasharray",
        ):
            value = getattr(indexed, name)
            if value is None or name not in names:
                continue
            if isinstance(value, list):
                if not value:
                    continue
                value = value[index % len(value)] if wrap else value[min(index, len(value) - 1)]
            overrides[name] = value
        return dataclasses.replace(aesthetic, **overrides)  # type: ignore[type-var]

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

        region_group = self._region_group(region)

        if self._uses_indexed():
            # Indexed modes show state through the base look and draw no select
            # layer, for every region: base -> indexed values (if any) -> hover,
            # as in the JS components
            base_state = RegionState(
                region_id=region, value=0, is_hovered=False, group=region_group
            )
            base: BaseAesthetic = resolve_region(base_state, config)
            indexed = self._indexed_for(region)
            if indexed is not None:
                base = self._apply_indexed(base, indexed, value)
            if not hovered:
                return self._aesthetic_to_dict(base)
            hover_config = AestheticConfig(
                aes_base=base, aes_select=None, aes_hover=config.aes_hover
            )
            hover_state = RegionState(
                region_id=region, value=0, is_hovered=True, group=region_group
            )
            return self._aesthetic_to_dict(resolve_region(hover_state, hover_config))

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

        Renders layers in order: underlay → base → overlay → selection → hover
        → annotation. Regions with an indexed aesthetic show their state in the
        base layer and get no selection copy, as in the JS components.

        Args:
            output: If provided, write SVG to file and return None.
                If None, return SVG as string.

        Returns:
            SVG string if output is None, otherwise None.
        """
        import dataclasses

        import svg

        from .svg import Path as PathElement

        # ViewBox
        vb = self._outline.viewbox()
        viewbox_str = f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}"

        # Layer sets
        overlays = set(self._outline.overlay_ids())
        underlays = set(self._outline.underlay_ids())
        hidden = set(self._outline.hidden_ids())
        annotations = set(self._outline.annotation_ids())

        # Helper to apply aesthetics to element
        def style_element(elem: Any, aes_dict: dict[str, Any]) -> svg.Element:
            if isinstance(elem, str):
                elem = PathElement(d=elem)  # type: ignore[arg-type]
            kwargs: dict[str, Any] = {}

            # Check if element is a Line (no fill support)
            is_line = hasattr(elem, "element_name") and elem.element_name == "line"

            # Map aes keys to SVG attrs (skip fill for lines)
            if not is_line:
                if "fill_color" in aes_dict:
                    kwargs["fill"] = aes_dict["fill_color"]
                if "fill_opacity" in aes_dict:
                    kwargs["fill_opacity"] = aes_dict["fill_opacity"]
            if "stroke_color" in aes_dict:
                kwargs["stroke"] = aes_dict["stroke_color"]
            if "stroke_width" in aes_dict:
                kwargs["stroke_width"] = aes_dict["stroke_width"]
            if "stroke_dasharray" in aes_dict:
                kwargs["stroke_dasharray"] = aes_dict["stroke_dasharray"]

            return dataclasses.replace(elem, **kwargs)  # type: ignore[type-var]

        # Build element list in layer order
        svg_elements: list[svg.Element] = []

        def render(region_id: str, is_hovered: bool = False) -> None:
            aes_dict = self.aes(region_id, is_hovered=is_hovered)
            for elem in self._outline.regions.get(region_id, []):
                svg_elements.append(style_element(elem, aes_dict))  # type: ignore[arg-type]

        # Render layers: underlay → base → overlay → selection → hover
        for region_id in self._outline.regions:
            if region_id in hidden:
                continue
            if region_id in underlays:
                render(region_id)

        for region_id in self._outline.regions:
            if region_id in hidden | underlays | overlays | annotations:
                continue
            render(region_id)

        for region_id in self._outline.regions:
            if region_id in overlays:
                render(region_id)

        # Selection overlay
        for region_id in self._outline.regions:
            if (
                region_id not in hidden | underlays | overlays | annotations
                and self._value.get(region_id, 0) > 0
                and not self._uses_indexed()
            ):
                render(region_id)

        # Hover overlay
        if self._hovered and self._hovered not in hidden:
            render(self._hovered, is_hovered=True)

        # Annotation: always on top, even above hover
        for region_id in self._outline.regions:
            if region_id in annotations and region_id not in hidden:
                render(region_id)

        # Create SVG
        root = svg.SVG(
            width=str(vb[2]),  # type: ignore[arg-type]
            height=str(vb[3]),  # type: ignore[arg-type]
            viewBox=viewbox_str,  # type: ignore[arg-type]
            elements=svg_elements,
        )
        svg_str = str(root)

        if output is not None:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_text(svg_str, encoding="utf-8")
            return None
        return svg_str


__all__ = ["StillLife"]
