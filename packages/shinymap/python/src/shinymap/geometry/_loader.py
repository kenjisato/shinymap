"""Geometry loading utilities for runtime use in Shiny apps.

This module provides the load_geometry() function for loading shinymap JSON
files at runtime in Shiny applications. It handles:
- Loading and parsing JSON files
- Separating main geometry from overlays
- Computing or extracting viewBox
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._bounds import BoundsCalculator, _normalize_geometry_dict, calculate_viewbox


def load_geometry(
    json_path: Path | str,
    overlay_keys: list[str] | None = None,
    use_metadata_overlays: bool = True,
    viewbox_from_metadata: bool = True,
    viewbox_covers_overlays: bool = True,
    viewbox_padding: float = 0.0,
    bounds_fn: BoundsCalculator | None = None,
) -> tuple[dict[str, str], dict[str, str], str]:
    """Load SVG geometry from shinymap JSON format.

    Expects JSON files with list-based path format:
    {
      "_metadata": {"viewBox": "0 0 100 100"},
      "region_01": ["M 10 10 L 40 10 L 40 40 L 10 40 Z"],
      "hokkaido": ["M 0 0 L 100 0 Z", "M 200 0 L 300 0 Z"]
    }

    Path lists are joined with spaces for rendering: " ".join(path_list)

    Args:
        json_path: Path to JSON file in shinymap geometry format
        overlay_keys: Explicit list of keys to treat as overlays.
                     If None and use_metadata_overlays=True, uses _metadata.overlays
        use_metadata_overlays: If True, read overlay keys from _metadata.overlays
        viewbox_from_metadata: If True, use _metadata.viewBox if present
        viewbox_covers_overlays: If True, computed viewBox includes overlays
        viewbox_padding: Percentage padding for computed viewBox (0.05 = 5%)
        bounds_fn: Optional custom function to calculate path bounds (advanced usage).
                  Takes path_d string, returns (min_x, min_y, max_x, max_y).
                  If None, automatically uses svgpathtools if available, else regex-based.

    Returns:
        Tuple of (geometry, overlay_geometry, viewbox):
            - geometry: Main interactive regions (dict mapping IDs to SVG paths)
            - overlay_geometry: Non-interactive overlays (dict mapping IDs to SVG paths)
            - viewbox: ViewBox string in format "min_x min_y width height"

    Raises:
        FileNotFoundError: If json_path does not exist
        ValueError: If JSON parsing fails

    Note:
        Viewbox calculation automatically uses svgpathtools for accurate curve bounds
        if installed. If curve commands are detected but svgpathtools is not available,
        a warning is issued suggesting installation.

    Example:
        >>> # Load with metadata-specified overlays
        >>> geom, overlays, vb = load_geometry("map.json")

        >>> # Override with explicit overlay keys
        >>> geom, overlays, vb = load_geometry(
        ...     "map.json",
        ...     overlay_keys=["_border", "_grid"],
        ...     viewbox_padding=0.02
        ... )

        >>> # Compute tight viewBox around main geometry only
        >>> geom, overlays, vb = load_geometry(
        ...     "map.json",
        ...     viewbox_from_metadata=False,
        ...     viewbox_covers_overlays=False
        ... )
    """
    json_path = Path(json_path)
    if not json_path.exists():
        msg = f"JSON file not found: {json_path}"
        raise FileNotFoundError(msg)

    try:
        with open(json_path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        msg = f"Failed to parse JSON: {e}"
        raise ValueError(msg) from e

    # Extract metadata
    metadata = data.get("_metadata", {}) if isinstance(data.get("_metadata"), dict) else {}

    # Determine overlay keys
    overlay_key_set: set[str] = set()

    if overlay_keys:
        # Explicit overlay keys provided
        overlay_key_set = set(overlay_keys)
    elif use_metadata_overlays and "overlays" in metadata:
        # Use overlays from metadata
        meta_overlays = metadata["overlays"]
        if isinstance(meta_overlays, list):
            overlay_key_set = set(meta_overlays)

    # Normalize all geometry (both main and overlays) using shared function
    all_geometry = _normalize_geometry_dict(data)

    # Separate geometry and overlays based on overlay_key_set
    geometry: dict[str, str] = {}
    overlay_geometry: dict[str, str] = {}

    for key, path_str in all_geometry.items():
        if key in overlay_key_set:
            overlay_geometry[key] = path_str
        else:
            geometry[key] = path_str

    # Determine viewBox
    viewbox: str

    if viewbox_from_metadata and "viewBox" in metadata:
        # Use viewBox from metadata
        viewbox = metadata["viewBox"]
    else:
        # Compute viewBox
        if viewbox_covers_overlays and overlay_geometry:
            all_paths = {**geometry, **overlay_geometry}
            vb_tuple = calculate_viewbox(all_paths, padding=viewbox_padding, bounds_fn=bounds_fn)
        else:
            vb_tuple = calculate_viewbox(geometry, padding=viewbox_padding, bounds_fn=bounds_fn)

        # Format as viewBox string
        viewbox = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"

    return geometry, overlay_geometry, viewbox
