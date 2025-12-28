"""SVG-related utility functions."""

from __future__ import annotations

import re


def path_bb(path_d: str) -> tuple[float, float, float, float]:
    """Extract bounding box from SVG path data.

    Simple regex-based implementation that extracts coordinates from path data.

    Args:
        path_d: SVG path data string (e.g., "M 10 20 L 30 40 Z")

    Returns:
        Tuple of (min_x, min_y, max_x, max_y)

    Note:
        This is a simplified parser for polygon paths (M, L commands).
        Does not handle curves (C, Q, A) accurately - uses only coordinate endpoints.
        Sufficient for simplified map outlines.

    Example:
        >>> path_bb("M 0 0 L 100 0 L 100 100 Z")
        (0.0, 0.0, 100.0, 100.0)
    """
    # Extract all numbers (handles negative, decimals)
    coord_pattern = r"[-]?\d+\.?\d*"
    coords = re.findall(coord_pattern, path_d)

    if len(coords) < 2:
        return (0.0, 0.0, 0.0, 0.0)

    x_coords = [float(coords[i]) for i in range(0, len(coords), 2)]
    y_coords = [float(coords[i]) for i in range(1, len(coords), 2)]

    return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def strip_unit(value: str) -> float | None:
    """Strip SVG unit suffix and parse value as float.

    Args:
        value: SVG dimension string (e.g., "100", "100px", "50pt")

    Returns:
        Parsed float value, or None if parsing fails

    Example:
        >>> strip_unit("100")
        100.0
        >>> strip_unit("100px")
        100.0
        >>> strip_unit("50.5pt")
        50.5
        >>> strip_unit("invalid")
        None
    """
    # Remove common SVG units and try to parse as float
    # Note: This doesn't convert units (e.g., pt to px) - just strips them
    value = value.strip()
    for unit in ["px", "pt", "mm", "cm", "in", "pc", "em", "rem", "%"]:
        if value.endswith(unit):
            value = value[: -len(unit)].strip()
            break

    try:
        return float(value)
    except ValueError:
        return None
