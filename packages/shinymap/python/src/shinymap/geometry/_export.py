"""Export geometry to SVG format (preserves original aesthetics).

This module provides functionality to export shinymap geometry back to SVG files,
preserving original aesthetics (fill, stroke, etc.) from the source SVG.

Key use cases:
1. SVG round-tripping: Convert SVG → Geometry → SVG
2. Export modified geometry after relabeling/merging operations
3. Save geometry with annotations added by converter app
"""

from __future__ import annotations

from pathlib import Path as PathType
from typing import TYPE_CHECKING

import svg

from shinymap.types import MISSING, MissingType

if TYPE_CHECKING:
    from ._geometry import Outline

# Type alias for backward compatibility in type hints
Geometry = "Outline"


def export_svg(
    geometry: Outline,
    output_path: str | PathType,
    viewbox: str | MissingType = MISSING,
    width: int | str | MissingType = MISSING,
    height: int | str | MissingType = MISSING,
    include_ids: bool = True,
) -> None:
    """Export shinymap geometry to SVG file.

    This function preserves original SVG aesthetics (fill, stroke, etc.)
    from the geometry. Useful for round-tripping geometry or exporting
    modified geometry after relabeling/merging operations.

    Args:
        geometry: Geometry object to export
        output_path: Path to write SVG file
        viewbox: ViewBox string (default: use geometry.viewbox() method)
        width: SVG width attribute (default: extract from viewBox)
        height: SVG height attribute (default: extract from viewBox)
        include_ids: Add id attributes to elements (default: True)

    Example:
        >>> from shinymap.geometry import Geometry, export_svg
        >>> geom = Geometry.from_svg("input.svg")
        >>>
        >>> # Basic export preserving original aesthetics
        >>> export_svg(geom, "output.svg")
        >>>
        >>> # Export with custom viewBox
        >>> export_svg(geom, "custom.svg", viewbox="0 0 1000 1000")
        >>>
        >>> # Export without id attributes
        >>> export_svg(geom, "no_ids.svg", include_ids=False)

    Note:
        Exported SVG preserves aesthetic attributes (fill, stroke, etc.)
        from the original geometry. These aesthetics are NOT used by shinymap
        for interactive rendering - they're preserved for SVG export only.
    """
    # Determine viewBox string
    viewbox_str: str
    if viewbox is MISSING:
        # Try to use viewBox string from metadata first (preserves original format)
        if "viewBox" in geometry.metadata:
            viewbox_str = geometry.metadata["viewBox"]
        else:
            # Calculate from geometry bounds
            vb_tuple = geometry.viewbox()
            viewbox_str = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"
    else:
        viewbox_str = viewbox  # type: ignore[assignment]

    # Determine width/height from viewBox if not specified
    width_attr: int | str | None = None
    height_attr: int | str | None = None

    if width is not MISSING:
        width_attr = width  # type: ignore[assignment]

    if height is not MISSING:
        height_attr = height  # type: ignore[assignment]

    # If width/height still not set, extract from viewBox
    if width_attr is None:
        parts = viewbox_str.split()
        if len(parts) == 4:
            width_attr = parts[2]  # third value is width

    if height_attr is None:
        parts = viewbox_str.split()
        if len(parts) == 4:
            height_attr = parts[3]  # fourth value is height

    # Create SVG elements list
    svg_elements: list[svg.Element] = []

    for region_id, region_elements in geometry.regions.items():
        for elem in region_elements:
            # Add id attribute if requested
            if include_ids:
                # Clone element with id attribute
                # svg.py elements are dataclasses, so we can use replace
                import dataclasses

                elem_with_id = dataclasses.replace(elem, id=region_id)  # type: ignore[type-var]
                svg_elements.append(elem_with_id)  # type: ignore[arg-type]
            else:
                svg_elements.append(elem)  # type: ignore[arg-type]

    # Create SVG root
    root = svg.SVG(
        width=width_attr,  # type: ignore[arg-type]
        height=height_attr,  # type: ignore[arg-type]
        viewBox=viewbox_str,  # type: ignore[arg-type]
        elements=svg_elements,
    )

    # Write to file
    output_path = PathType(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        # svg.py's SVG.__str__() renders the complete SVG document
        f.write(str(root))


__all__ = ["export_svg"]
