"""UI utility functions for shinymap components."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any

from htmltools import HTMLDependency

from .. import __version__
from ..types import OutlineMap


def _dependency() -> HTMLDependency:
    """Get the shinymap HTML dependency (JS bundle)."""
    return HTMLDependency(
        name="shinymap",
        version=__version__,
        source={"package": "shinymap", "subdir": "www"},
        script=[{"src": "shinymap.global.js"}, {"src": "shinymap-shiny.js"}],
    )


def _merge_styles(
    width: str | None, height: str | None, style: MutableMapping[str, str] | None
) -> MutableMapping[str, str]:
    """Merge width/height with style dict."""
    merged: MutableMapping[str, str] = {} if style is None else dict(style)
    if width is not None:
        merged.setdefault("width", width)
    if height is not None:
        merged.setdefault("height", height)
    return merged


def _class_names(base: str, extra: str | None) -> str:
    """Combine CSS class names."""
    return f"{base} {extra}" if extra else base


def _normalize_outline(outline: OutlineMap) -> Mapping[str, list[dict[str, Any]]]:
    """Normalize outline to Element list format for JavaScript.

    Converts outline regions to a consistent list-of-dicts format.
    JavaScript (shinymap-shiny.js) handles snake_case to camelCase conversion.
    """
    result: dict[str, list[dict[str, Any]]] = {}
    for region_id, value in outline.items():
        if isinstance(value, str):
            result[region_id] = [{"type": "path", "d": value}]
        elif isinstance(value, list):
            elements: list[dict[str, Any]] = []
            for item in value:
                if isinstance(item, str):
                    elements.append({"type": "path", "d": item})
                elif hasattr(item, "to_dict"):
                    elements.append(item.to_dict())
                elif isinstance(item, dict):
                    elements.append(item)
            result[region_id] = elements
        elif hasattr(value, "to_dict"):
            result[region_id] = [value.to_dict()]
        elif isinstance(value, dict):
            result[region_id] = [value]
    return result


def _strip_none(data: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from dict."""
    return {k: v for k, v in data.items() if v is not None}


def _validate_value(
    value: Mapping[str, int] | None,
    param_name: str = "value",
) -> None:
    """Validate that a value map contains only non-negative integers.

    Args:
        value: The value map to validate (or None)
        param_name: Name of the parameter for error messages

    Raises:
        ValueError: If any value is negative or not an integer
    """
    if value is None:
        return

    for region_id, count in value.items():
        if not isinstance(count, int):
            raise ValueError(
                f"{param_name}[{region_id!r}] must be an integer, "
                f"got {type(count).__name__}: {count!r}"
            )
        if count < 0:
            raise ValueError(
                f"{param_name}[{region_id!r}] must be non-negative, got {count}"
            )
