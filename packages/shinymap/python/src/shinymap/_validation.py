"""Validation helpers for shinymap aesthetics.

This module provides optional validation warnings to help users avoid
applying inappropriate aesthetics to elements (e.g., fill on lines).
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .geometry import Geometry

# Element types that have no fill area
NO_FILL_ELEMENT_TYPES = {"line"}

# Fill-related aesthetic keys
FILL_AESTHETIC_KEYS = {"fill_color", "fill_opacity", "fillColor", "fillOpacity"}


def _collect_element_types(
    geometry: Geometry | Mapping[str, Any],
    region_id: str | None = None,
) -> set[str]:
    """Collect unique element types from geometry.

    Args:
        geometry: Geometry object or dict
        region_id: Optional specific region to check. If None, checks all regions.

    Returns:
        Set of element type strings (e.g., {"path", "line", "circle"})
    """
    element_types: set[str] = set()

    # Handle Geometry object (has .regions attribute that is dict-like)
    if hasattr(geometry, "regions"):
        regions_obj = geometry.regions
        # Regions object is dict-like, iterate over it
        region_ids = [region_id] if region_id else list(regions_obj.keys())
        for rid in region_ids:
            if rid not in regions_obj:
                continue
            elements = regions_obj[rid]
            if isinstance(elements, list):
                for element in elements:
                    # Element dataclass - use class name as element type
                    elem_type = type(element).__name__.lower()
                    element_types.add(elem_type)
    else:
        # Handle raw dict
        regions_dict = {k: v for k, v in geometry.items() if not k.startswith("_")}

        # Filter to specific region if requested
        if region_id is not None:
            if region_id not in regions_dict:
                return element_types
            regions_dict = {region_id: regions_dict[region_id]}

        for elements in regions_dict.values():
            if isinstance(elements, list):
                for element in elements:
                    if isinstance(element, dict) and "type" in element:
                        element_types.add(element["type"].lower())
                    elif hasattr(element, "element_type"):
                        # Element dataclass
                        element_types.add(element.element_type.lower())

    return element_types


def validate_aesthetic_for_elements(
    aesthetic: Mapping[str, Any] | None,
    element_types: set[str],
    context: str = "",
) -> None:
    """Warn if aesthetic contains inappropriate properties for element types.

    Currently warns when fill properties are applied to line-only regions.

    Args:
        aesthetic: Aesthetic dict to validate
        element_types: Set of element types in the region
        context: Optional context string for warning message (e.g., "region 'tokyo'")
    """
    if aesthetic is None:
        return

    # Check if this is a line-only region
    if element_types == {"line"}:
        # Check for fill properties
        fill_keys = FILL_AESTHETIC_KEYS & set(aesthetic.keys())
        if fill_keys:
            # Filter out None values (which mean "transparent", a valid setting)
            non_none_fills = {k for k in fill_keys if aesthetic[k] is not None}
            if non_none_fills:
                context_str = f" for {context}" if context else ""
                warnings.warn(
                    f"Fill aesthetics {non_none_fills} have no effect on Line elements{context_str}. "
                    f"Use aes.Line() for stroke-only aesthetics.",
                    UserWarning,
                    stacklevel=3,
                )


def validate_geometry_aesthetics(
    geometry: Geometry | Mapping[str, Any],
    aes_group: Mapping[str, Mapping[str, Any]] | None = None,
    default_aesthetic: Mapping[str, Any] | None = None,
) -> None:
    """Validate aesthetics against geometry element types.

    Warns if inappropriate aesthetics are detected.

    Args:
        geometry: Geometry object or dict
        aes_group: Optional per-group aesthetics
        default_aesthetic: Optional default aesthetic
    """
    # Collect element types per region
    if hasattr(geometry, "regions"):
        regions_dict = geometry.regions
    else:
        regions_dict = {k: v for k, v in geometry.items() if not k.startswith("_")}

    for region_id in regions_dict:
        element_types = _collect_element_types(geometry, region_id)

        # Check default aesthetic
        if default_aesthetic:
            validate_aesthetic_for_elements(
                default_aesthetic,
                element_types,
                f"region '{region_id}'",
            )

        # Check group aesthetics if this region is in a group
        if aes_group:
            # Check if region is in any aesthetic group
            metadata = getattr(geometry, "metadata", None) or {}
            groups = metadata.get("groups", {})

            for group_name, aesthetic in aes_group.items():
                # Check if region is in this group
                group_members = groups.get(group_name, [])
                if region_id in group_members or group_name == region_id:
                    validate_aesthetic_for_elements(
                        aesthetic,
                        element_types,
                        f"region '{region_id}' (group '{group_name}')",
                    )


__all__ = [
    "validate_aesthetic_for_elements",
    "validate_geometry_aesthetics",
    "_collect_element_types",
]
