"""Caption utilities for generating labeled SVG references.

This module provides composable functions for adding ID labels to outlines:
- describe(): Generate Text elements with region IDs at each region's center
- glaze(): Add regions as overlay/underlay to an existing outline
"""

from __future__ import annotations

from typing import Any

from ..outline import Outline, Regions
from ..svg import Text


def describe(
    outline: Outline,
    exclude: list[str] | None = None,
    **kwargs: Any,
) -> Regions:
    """Generate Text elements with region IDs at each region's center.

    Creates a Regions dict containing Text elements positioned at the center
    of each region's bounding box. These can be added to the outline using
    glaze() to create a reference SVG with ID labels.

    Args:
        outline: Source outline to generate labels for
        exclude: Region IDs to skip (e.g., overlays, hidden regions)
        **kwargs: Additional attributes passed to Text elements.
            font_size can be absolute (e.g., "5") or percentage of
            smaller viewBox dimension (e.g., "3%"). Default is "3%".
            Other options: fill, text_anchor, etc.

    Returns:
        Regions dict with Text elements keyed as "_label_{region_id}"

    Examples:
        >>> from shinymap import Outline
        >>> from shinymap.kit import describe, glaze
        >>>
        >>> outline = Outline.from_svg("map.svg")
        >>> labels = describe(outline, exclude=outline.overlay_ids())
        >>> labeled = glaze(outline, labels)
        >>>
        >>> # Custom styling with absolute font size
        >>> labels = describe(outline, font_size="5", fill="red")
        >>>
        >>> # Percentage-based font size (2% of smaller viewBox dimension)
        >>> labels = describe(outline, font_size="2%")
    """
    from ..utils import path_bb

    exclude_set = set(exclude) if exclude else set()
    labels: dict[str, list[Text]] = {}

    # Default text attributes
    text_attrs = {
        "text_anchor": "middle",
        "dominant_baseline": "central",
        "font_size": "3%",
        "fill": "#333",
    }
    text_attrs.update(kwargs)

    # Resolve percentage-based font_size
    font_size = text_attrs.get("font_size", "3%")
    if isinstance(font_size, str) and font_size.endswith("%"):
        pct = float(font_size[:-1]) / 100
        vb = outline.viewbox()
        text_attrs["font_size"] = str(round(min(vb[2], vb[3]) * pct, 2))

    for region_id, elements in outline.regions.items():
        if region_id in exclude_set:
            continue

        # Compute bounds for this region's elements
        all_bounds: list[tuple[float, float, float, float]] = []
        for elem in elements:
            if isinstance(elem, str):
                # v0.x format: parse path string
                bounds = path_bb(elem)
                all_bounds.append(bounds)
            else:
                # v1.x format: use element's bounds() method
                all_bounds.append(elem.bounds())

        if not all_bounds:
            continue

        # Combine bounds to get region bounding box
        min_x = min(b[0] for b in all_bounds)
        min_y = min(b[1] for b in all_bounds)
        max_x = max(b[2] for b in all_bounds)
        max_y = max(b[3] for b in all_bounds)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        labels[f"_label_{region_id}"] = [
            Text(
                x=center_x,
                y=center_y,
                text=region_id,
                **text_attrs,
            )
        ]

    return Regions(labels)


def glaze(
    outline: Outline,
    regions: Regions | Outline,
    as_underlay: bool = False,
) -> Outline:
    """Add regions as overlay (default) or underlay to an existing outline.

    Merges additional regions into an outline and assigns them to the
    specified layer. Useful for adding annotations, labels, or other
    decorations to an existing map.

    Args:
        outline: Base outline to add regions to
        regions: Regions to add (Regions dict or Outline object)
        as_underlay: If True, add as underlay; if False (default), add as overlay

    Returns:
        New Outline with regions merged and layer assigned

    Examples:
        >>> from shinymap import Outline, Regions
        >>> from shinymap.svg import Text
        >>> from shinymap.kit import glaze
        >>>
        >>> # Add labels as overlay (default)
        >>> outline = Outline.from_svg("map.svg")
        >>> labels = Regions({"_note": [Text(x=50, y=50, text="Note")]})
        >>> annotated = glaze(outline, labels)
        >>>
        >>> # Add background as underlay
        >>> background = Regions({"_bg": [...]})
        >>> with_bg = glaze(outline, background, as_underlay=True)
    """
    # Get regions to merge
    if isinstance(regions, Outline):
        regions_to_add = dict(regions.regions)
    else:
        regions_to_add = dict(regions)

    # Combine regions from base outline and new regions
    combined_regions = dict(outline.regions)
    combined_regions.update(regions_to_add)

    # Build new metadata with layer assignment
    new_region_ids = list(regions_to_add.keys())
    layer_key = "underlay" if as_underlay else "overlay"

    # Start with existing metadata
    new_metadata = dict(outline.metadata)

    # Get existing layer list and append new IDs
    existing_layer = list(new_metadata.get(layer_key, []))
    for rid in new_region_ids:
        if rid not in existing_layer:
            existing_layer.append(rid)
    new_metadata[layer_key] = existing_layer

    return Outline(regions=Regions(combined_regions), metadata=new_metadata)
