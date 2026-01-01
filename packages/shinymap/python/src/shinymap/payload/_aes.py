"""Build aesthetic payloads for JavaScript consumption.

This module converts resolved ByGroup aesthetics to the v0.3 payload format
for JavaScript. The key design principle is:

- Python (this module) does resolution and serialization
- JavaScript does lookup + RelativeExpr resolution only

The payload format:
{
    "region1": {"base": {...}, "select": {...}, "hover": {...}},
    "group1": {"base": {...}, "select": {...}, "hover": {...}},
    "__shape": {"base": {...}, "select": {...}, "hover": {...}},
    "__all": {"base": {...}, "select": {...}, "hover": {...}},
    "_metadata": {
        "group1": ["region1", "region2"],
        "__shape": ["region1", "region2", "region3"],
        ...
    }
}

JavaScript lookup priority (first match wins):
    region_id → group_name → __shape/__line/__text → __all
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..aes._core import BaseAesthetic, ByGroup, ByState
from ..types import MissingType

if TYPE_CHECKING:
    from ..geometry import Outline


def build_aes_payload(
    resolved: ByGroup,
    geometry: Outline,
) -> dict[str, Any]:
    """Build v0.3 aesthetic payload from resolved ByGroup.

    Takes a resolved ByGroup (from WashConfig.apply()) where MISSING values
    are already resolved, and converts it to the payload format for JavaScript.

    RelativeExpr values are preserved in the payload - JavaScript resolves them
    at render time against the actual parent (base or select depending on state).

    Args:
        resolved: Resolved ByGroup from WashConfig.apply()
        geometry: Outline object with region/group information

    Returns:
        Dict in v0.3 payload format with entries and _metadata

    Example:
        >>> from shinymap import Wash, aes
        >>> from shinymap.payload import build_aes_payload
        >>> wc = Wash(shape=aes.Shape(fill_color="#e5e7eb"))
        >>> resolved = wc.config.apply(aes.ByGroup(coastal=aes.Shape(fill_color="#3b82f6")), geometry)
        >>> payload = build_aes_payload(resolved, geometry)
        >>> payload["coastal"]["base"]["fill_color"]
        '#3b82f6'
    """
    result: dict[str, Any] = {}
    metadata: dict[str, list[str]] = {}

    region_types = geometry.region_types()
    geo_groups = geometry.groups()

    # Convert each entry in resolved ByGroup to payload format
    for key, value in resolved.items():
        if isinstance(value, MissingType):
            continue
        if value is None:
            result[key] = None
            continue

        # Convert ByState or BaseAesthetic to JS dict format
        if isinstance(value, ByState):
            result[key] = value.to_js_dict()
        elif isinstance(value, BaseAesthetic):
            # Wrap as base-only ByState
            result[key] = ByState(base=value).to_js_dict()

    # Build _metadata for JS lookup
    # Groups: map group name to member region IDs
    for group_name, members in geo_groups.items():
        if group_name in resolved:
            metadata[group_name] = list(members)

    # Type defaults: map __shape/__line/__text to region IDs of that type
    shape_regions: list[str] = []
    line_regions: list[str] = []
    text_regions: list[str] = []

    for region_id, elem_type in region_types.items():
        if elem_type == "shape":
            shape_regions.append(region_id)
        elif elem_type == "line":
            line_regions.append(region_id)
        elif elem_type == "text":
            text_regions.append(region_id)

    # Only add type metadata if the resolved ByGroup has that type key
    # or if we have __all (which covers all types)
    if "__shape" in resolved or "__all" in resolved:
        metadata["__shape"] = shape_regions
    if "__line" in resolved or "__all" in resolved:
        metadata["__line"] = line_regions
    if "__text" in resolved or "__all" in resolved:
        metadata["__text"] = text_regions

    if metadata:
        result["_metadata"] = metadata

    return result


__all__ = ["build_aes_payload"]
