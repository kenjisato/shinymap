"""Utilities for loading and converting SVG geometry.

This module provides tools for working with SVG geometry in shinymap:

1. **SVG to JSON converter**: Extract path data from SVG files into shinymap JSON format
2. **JSON loader**: Load geometry from JSON with automatic viewBox calculation

## Shinymap JSON Geometry Format

The shinymap geometry format is designed for simplicity and transparency:

**Structure:**
```json
{
    "_metadata": {
        "source": "Wikimedia Commons - File:Japan_template_large.svg",
        "license": "CC BY-SA 3.0",
        "viewBox": "0 0 1500 1500",
        "overlays": ["_divider_lines", "_border"]
    },
    "region1": "M 0 0 L 100 0 L 100 100 Z",
    "region2": "M 100 0 L 200 0 L 200 100 Z",
    "_divider_lines": "M 100 0 L 100 100",
    "_border": "M 0 0 L 200 0 L 200 200 L 0 200 Z"
}
```

**Rules:**
1. **String values** = SVG path data (geometry)
2. **Dict/list values** = metadata (ignored by loader)
3. **Keys starting with underscore** = typically overlays or metadata
4. **_metadata.viewBox** (optional) = preferred viewBox string
5. **_metadata.overlays** (optional) = list of overlay keys

**Why this format?**
- **Flat and transparent**: Easy to inspect, edit, version control
- **SVG-native**: Path strings are valid SVG without transformation
- **Extensible**: Metadata coexists with geometry without conflicts
- **Geometry-agnostic**: Works for maps, diagrams, floor plans, etc.

**Comparison to GeoJSON/TopoJSON:**
- GeoJSON/TopoJSON are standards for *geographic* data with projections
- shinymap format is geometry-agnostic (works for any SVG paths)
- Simpler when you already have SVG paths from design tools
- For geographic workflows, use shinymap-geo (future extension)
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# Type alias for bounds calculator functions
BoundsCalculator = Callable[[str], tuple[float, float, float, float]]


@dataclass
class Geometry:
    """Canonical geometry representation (list-based, lossless).

    This class encapsulates SVG path geometry with metadata. It uses list-based
    paths as the canonical format to preserve multi-path regions without loss.

    Attributes:
        regions: Dictionary mapping region IDs to lists of SVG path strings
        metadata: Optional metadata dict (viewBox, overlays, source, license, etc.)

    Example:
        >>> # Load from dict
        >>> data = {"region1": ["M 0 0 L 10 0"], "_metadata": {"viewBox": "0 0 100 100"}}
        >>> geo = Geometry.from_dict(data)
        >>>
        >>> # Access properties
        >>> geo.regions
        {'region1': ['M 0 0 L 10 0']}
        >>> geo.viewbox()
        (0.0, 0.0, 100.0, 100.0)
    """
    regions: dict[str, list[str]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Geometry":
        """Load geometry from dict (accepts both list and string path formats).

        Args:
            data: Dictionary with regions and optional _metadata key

        Returns:
            Geometry object with normalized list-based paths

        Raises:
            ValueError: If _metadata exists but is not a dict

        Example:
            >>> # String format (gets normalized to list)
            >>> Geometry.from_dict({"a": "M 0 0 L 10 0"})
            Geometry(regions={'a': ['M 0 0 L 10 0']}, metadata={})

            >>> # List format (already canonical)
            >>> Geometry.from_dict({"a": ["M 0 0", "L 10 0"]})
            Geometry(regions={'a': ['M 0 0', 'L 10 0']}, metadata={})
        """
        regions = {}
        metadata = {}

        for key, value in data.items():
            if key == "_metadata":
                if not isinstance(value, dict):
                    raise ValueError(f"_metadata must be a dict, got {type(value).__name__}")
                metadata = value
            elif isinstance(value, list):
                regions[key] = value  # Already list format
            elif isinstance(value, str):
                regions[key] = [value]  # Normalize string to single-element list

        return cls(regions=regions, metadata=metadata)

    def viewbox(self, padding: float = 0.02) -> tuple[float, float, float, float]:
        """Get viewBox from metadata, or compute from geometry coordinates.

        Args:
            padding: Padding fraction for computed viewBox (default 2%)

        Returns:
            ViewBox tuple in format (x, y, width, height)

        Example:
            >>> geo = Geometry.from_dict({"a": ["M 0 0 L 100 100"]})
            >>> geo.viewbox()
            (-2.0, -2.0, 104.0, 104.0)  # With 2% padding
        """
        if "viewBox" in self.metadata:
            # Parse viewBox string to tuple
            vb_str = self.metadata["viewBox"]
            parts = vb_str.split()
            if len(parts) != 4:
                raise ValueError(f"Invalid viewBox format: {vb_str}")
            return (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
        # Compute from geometry - normalize to string format first
        paths = _normalize_geometry_dict(self.regions)
        return _calculate_viewbox(paths, padding=padding, bounds_fn=None)

    def overlays(self) -> list[str]:
        """Get overlay region IDs from metadata.

        Returns:
            List of region IDs marked as overlays

        Example:
            >>> geo = Geometry.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"],
            ...     "_metadata": {"overlays": ["_border"]}
            ... })
            >>> geo.overlays()
            ['_border']
        """
        return self.metadata.get("overlays", [])

    def main_regions(self) -> dict[str, list[str]]:
        """Get main regions (excluding overlays).

        Returns:
            Dict of main regions {regionId: [path1, ...]}

        Example:
            >>> geo = Geometry.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"],
            ...     "_metadata": {"overlays": ["_border"]}
            ... })
            >>> geo.main_regions()
            {'region': ['M 0 0']}
        """
        overlay_ids = set(self.overlays())
        return {k: v for k, v in self.regions.items() if k not in overlay_ids}

    def overlay_regions(self) -> dict[str, list[str]]:
        """Get overlay regions only.

        Returns:
            Dict of overlay regions {regionId: [path1, ...]}

        Example:
            >>> geo = Geometry.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"],
            ...     "_metadata": {"overlays": ["_border"]}
            ... })
            >>> geo.overlay_regions()
            {'_border': ['M 0 0 L 100 0']}
        """
        overlay_ids = set(self.overlays())
        return {k: v for k, v in self.regions.items() if k in overlay_ids}


def _parse_svg_path_bounds(path_d: str) -> tuple[float, float, float, float]:
    """Extract bounding box from SVG path data (simple regex-based implementation).

    Args:
        path_d: SVG path data string (e.g., "M 10 20 L 30 40 Z")

    Returns:
        Tuple of (min_x, min_y, max_x, max_y)

    Note:
        This is a simplified parser for polygon paths (M, L commands).
        Does not handle curves (C, Q, A) accurately - uses only coordinate endpoints.
        Sufficient for simplified map geometries.

        For accurate curve handling, provide a custom bounds_fn using a library
        like svgpathtools.

    Example:
        >>> _parse_svg_path_bounds("M 0 0 L 100 0 L 100 100 Z")
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


def _normalize_geometry_dict(geometry: dict[str, Any]) -> dict[str, str]:
    """Normalize geometry dict to string-valued format.

    Accepts both string-valued dicts (shinymap format) and list-valued dicts
    (intermediate JSON format). Automatically skips non-string/non-list values
    like _metadata.

    Args:
        geometry: Dict with string or list[str] values representing SVG paths

    Returns:
        Dict with string-valued paths only (lists joined with space)

    Example:
        >>> # String format (already normalized)
        >>> _normalize_geometry_dict({"a": "M 0 0 L 10 10"})
        {'a': 'M 0 0 L 10 10'}

        >>> # List format (intermediate JSON)
        >>> _normalize_geometry_dict({"a": ["M 0 0", "L 10 10"]})
        {'a': 'M 0 0 L 10 10'}

        >>> # Mixed with metadata (skipped)
        >>> _normalize_geometry_dict({
        ...     "_metadata": {"viewBox": "0 0 100 100"},
        ...     "region": "M 0 0 L 100 0"
        ... })
        {'region': 'M 0 0 L 100 0'}
    """
    paths: dict[str, str] = {}

    for key, value in geometry.items():
        if isinstance(value, str):
            # Already string format (shinymap format)
            paths[key] = value
        elif isinstance(value, list):
            # List format (intermediate JSON) - join with space
            paths[key] = " ".join(value)
        # Skip non-string/non-list values (like _metadata dict)

    return paths


def _calculate_viewbox(
    paths: dict[str, str],
    padding: float = 0.0,
    bounds_fn: BoundsCalculator | None = None,
) -> tuple[float, float, float, float]:
    """Calculate viewBox that covers all paths with optional padding.

    Args:
        paths: Dict mapping region IDs to SVG path data strings
        padding: Percentage of dimensions to add as padding (0.05 = 5%)
        bounds_fn: Optional custom function to calculate path bounds.
                  Takes path_d string, returns (min_x, min_y, max_x, max_y).
                  If None, uses default _parse_svg_path_bounds (regex-based).

    Returns:
        Tuple of (min_x, min_y, width, height) for SVG viewBox

    Example:
        >>> # Default bounds calculator
        >>> paths = {"a": "M 0 0 L 100 0 L 100 100 Z"}
        >>> _calculate_viewbox(paths, padding=0.1)
        (-5.0, -5.0, 110.0, 110.0)

        >>> # Format as viewBox string
        >>> vb = _calculate_viewbox(paths)
        >>> viewbox_str = f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}"
        >>> viewbox_str
        '0.0 0.0 100.0 100.0'

        >>> # Custom bounds calculator using svgpathtools
        >>> from svgpathtools import parse_path
        >>> def accurate_bounds(path_d: str) -> tuple[float, float, float, float]:
        ...     path = parse_path(path_d)
        ...     xmin, xmax, ymin, ymax = path.bbox()
        ...     return (xmin, ymin, xmax, ymax)
        >>> _calculate_viewbox(paths, bounds_fn=accurate_bounds)
        (0.0, 0.0, 100.0, 100.0)
    """
    if not paths:
        return (0.0, 0.0, 100.0, 100.0)

    # Use default bounds calculator if none provided
    if bounds_fn is None:
        bounds_fn = _parse_svg_path_bounds

    # Calculate bounds for all paths
    all_bounds = [bounds_fn(path_d) for path_d in paths.values()]

    min_x = min(b[0] for b in all_bounds)
    min_y = min(b[1] for b in all_bounds)
    max_x = max(b[2] for b in all_bounds)
    max_y = max(b[3] for b in all_bounds)

    width = max_x - min_x
    height = max_y - min_y

    # Apply padding
    if padding > 0:
        pad_x = width * padding
        pad_y = height * padding
        min_x -= pad_x
        min_y -= pad_y
        width += 2 * pad_x
        height += 2 * pad_y

    return (min_x, min_y, width, height)


def from_svg(
    svg_path: Path | str,
    output_path: Path | str | None = None,
    extract_viewbox: bool = True,
) -> dict[str, Any]:
    """Extract intermediate JSON from SVG file (Step 1 of interactive workflow).

    This function extracts path elements from an SVG file and generates auto-IDs
    for paths without IDs. The result is "intermediate JSON" that can be further
    transformed using from_json().

    For one-shot conversion with all transformations, use convert() instead.

    Args:
        svg_path: Path to input SVG file
        output_path: Optional path to write JSON output (if None, returns dict only)
        extract_viewbox: If True, extract viewBox from SVG root element

    Returns:
        Dict in intermediate JSON format with auto-generated IDs

    Raises:
        FileNotFoundError: If svg_path does not exist
        ValueError: If SVG parsing fails

    Example:
        >>> # Interactive workflow: Step 1 - Extract intermediate JSON
        >>> intermediate = from_svg("map.svg", "map_intermediate.json")
        >>> # Inspect intermediate JSON, identify paths to group/rename
        >>> # Step 2 - Apply transformations
        >>> final = from_json(
        ...     intermediate,
        ...     id_mapping={"path_1": "region_01"},
        ...     grouping={"hokkaido": ["path_2", "path_3"]}
        ... )

        >>> # Or: one-shot conversion
        >>> final = convert(
        ...     "map.svg",
        ...     "map.json",
        ...     id_mapping={"path_1": "region_01"},
        ...     grouping={"hokkaido": ["path_2", "path_3"]}
        ... )
    """
    svg_path = Path(svg_path)
    if not svg_path.exists():
        msg = f"SVG file not found: {svg_path}"
        raise FileNotFoundError(msg)

    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as e:
        msg = f"Failed to parse SVG: {e}"
        raise ValueError(msg) from e

    # SVG namespace handling
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Extract viewBox from root SVG element
    viewbox = None
    if extract_viewbox:
        viewbox = root.get("viewBox")

    # Extract all path elements with d attribute
    # Generate IDs for paths without them
    output_paths: dict[str, list[str]] = {}
    auto_id_counter = 1

    for path_elem in root.findall(".//svg:path[@d]", ns):
        path_d = path_elem.get("d")
        if not path_d:
            continue

        # Get existing ID or generate one
        path_id = path_elem.get("id")
        if not path_id:
            path_id = f"path_{auto_id_counter}"
            auto_id_counter += 1

        output_paths[path_id] = [path_d.strip()]

    # Build metadata
    meta: dict[str, Any] = {}
    if viewbox:
        meta["viewBox"] = viewbox

    # Construct output
    output: dict[str, Any] = {}
    if meta:
        output["_metadata"] = meta

    output.update(output_paths)

    # Write to file if output_path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    return output


def from_json(
    intermediate_json: dict[str, Any] | Path | str,
    output_path: Path | str | None = None,
    relabel: dict[str, str | list[str]] | None = None,
    overlay_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Transform intermediate JSON to final JSON (Step 2 of interactive workflow).

    This function takes "intermediate" JSON (raw SVG paths with auto-generated IDs)
    and applies relabeling (renaming/grouping) and metadata updates to produce final JSON.

    Args:
        intermediate_json: Input JSON dict (or path to JSON file) with path data
        output_path: Optional path to write JSON output (if None, returns dict only)
        relabel: Optional dict to rename or merge paths. Maps new ID to old ID(s).
                 - String value: rename single path (e.g., {"okinawa": "path_3"})
                 - List value: merge multiple paths (e.g., {"hokkaido": ["path_1", "path_2"]})
        overlay_ids: List of path IDs to mark as overlays in metadata
        metadata: Additional metadata to merge with existing _metadata field

    Returns:
        Transformed JSON dict in shinymap format

    Raises:
        FileNotFoundError: If intermediate_json is a path and file doesn't exist
        ValueError: If JSON parsing fails or relabeled paths not found

    Example:
        >>> # Interactive workflow
        >>> # Step 1: Extract intermediate JSON
        >>> intermediate = from_svg("map.svg")
        >>>
        >>> # Inspect intermediate, plan transformations
        >>> print(list(intermediate.keys()))
        ['_metadata', 'path_1', 'path_2', 'path_3']
        >>>
        >>> # Step 2: Apply transformations
        >>> final = from_json(
        ...     intermediate,
        ...     relabel={
        ...         "region_north": ["path_1", "path_2"],  # Merge multiple
        ...         "_border": "path_3",                    # Rename single
        ...     },
        ...     overlay_ids=["_border"],
        ...     metadata={"source": "Custom SVG", "license": "MIT"}
        ... )
        >>>
        >>> # Result has merged and renamed paths
        >>> final["region_north"]  # Merged path_1 + path_2
        'M 0 0 L 100 0 L 100 100 Z M 200 0 L 300 0 L 300 100 Z'
        >>> final["_border"]  # Renamed from path_3
        'M 0 200 L 100 200 L 100 300 Z'
        >>> final["_metadata"]["overlays"]
        ['_border']
    """
    # Load from file if path provided
    if isinstance(intermediate_json, (Path, str)):
        json_path = Path(intermediate_json)
        if not json_path.exists():
            msg = f"JSON file not found: {json_path}"
            raise FileNotFoundError(msg)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
        except json.JSONDecodeError as e:
            msg = f"Failed to parse JSON: {e}"
            raise ValueError(msg) from e
        intermediate_json = data
    # Extract existing paths (list format only)
    input_paths: dict[str, list[str]] = {}
    for key, value in intermediate_json.items():
        if isinstance(value, list):
            input_paths[key] = value

    # Extract existing metadata
    existing_meta = intermediate_json.get("_metadata", {})
    if not isinstance(existing_meta, dict):
        existing_meta = {}

    # Process relabel mapping
    output_paths: dict[str, list[str]] = {}
    relabeled_ids: set[str] = set()

    if relabel:
        for new_id, old_id_or_ids in relabel.items():
            # Normalize to list for uniform processing
            old_ids = [old_id_or_ids] if isinstance(old_id_or_ids, str) else old_id_or_ids

            # Collect all paths (flatten nested lists from multiple regions)
            path_parts = []
            for old_id in old_ids:
                if old_id not in input_paths:
                    msg = f"Path '{old_id}' (mapped to '{new_id}') not found in intermediate JSON"
                    raise ValueError(msg)
                # Extend to flatten: input_paths[old_id] is already a list
                path_parts.extend(input_paths[old_id])
                relabeled_ids.add(old_id)

            # Store as list (single region = single-element, merge = multi-element)
            output_paths[new_id] = path_parts

    # Process remaining paths (not relabeled) - keep original IDs
    for path_id, path_list in input_paths.items():
        if path_id not in relabeled_ids:
            output_paths[path_id] = path_list

    # Build merged metadata
    merged_meta = {**existing_meta}

    # Merge user-provided metadata
    if metadata:
        merged_meta.update(metadata)

    # Update overlays list
    if overlay_ids:
        merged_meta["overlays"] = overlay_ids

    # Construct output
    output: dict[str, Any] = {}
    if merged_meta:
        output["_metadata"] = merged_meta

    output.update(output_paths)

    # Write to file if output_path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    return output


def convert(
    input_path: Path | str,
    output_path: Path | str | None = None,
    relabel: dict[str, str | list[str]] | None = None,
    overlay_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    extract_viewbox: bool = True,
) -> dict[str, Any]:
    """Convert SVG or intermediate JSON file to final JSON in one step.

    This is a convenience function that combines from_svg() and from_json()
    for scripting and reproducibility. Accepts both SVG files and intermediate
    JSON files. For interactive workflows with intermediate inspection, use
    from_svg() followed by from_json().

    Args:
        input_path: Path to input SVG or intermediate JSON file
        output_path: Optional path to write JSON output (if None, returns dict only)
        relabel: Optional dict to rename or merge paths. Maps new ID to old ID(s).
                 - String value: rename single path (e.g., {"okinawa": "path_3"})
                 - List value: merge multiple paths (e.g., {"hokkaido": ["path_1", "path_2"]})
        overlay_ids: List of path IDs to mark as overlays in metadata
        metadata: Additional metadata to include in _metadata field
        extract_viewbox: If True, extract viewBox from SVG root element (ignored for JSON input)

    Returns:
        Dict in shinymap JSON format

    Raises:
        FileNotFoundError: If input_path does not exist
        ValueError: If SVG/JSON parsing fails or relabeled paths not found

    Example:
        >>> # From SVG file
        >>> result = convert(
        ...     "japan.svg",
        ...     "japan.json",
        ...     relabel={
        ...         "01": ["hokkaido", "northern_territories"],  # Merge multiple
        ...         "_divider": "path_divider",                   # Rename single
        ...     },
        ...     overlay_ids=["_divider"],
        ...     metadata={"source": "Wikimedia Commons", "license": "CC BY-SA 3.0"}
        ... )

        >>> # From intermediate JSON file
        >>> result = convert(
        ...     "intermediate.json",
        ...     "final.json",
        ...     relabel={"region_01": "path_1"},
        ... )

        >>> # For interactive workflow, use two-step process:
        >>> intermediate = from_svg("map.svg")
        >>> # ... inspect intermediate JSON ...
        >>> final = from_json(intermediate, relabel={...})
    """
    # Determine file type by extension
    file_path = Path(input_path)

    if file_path.suffix.lower() == ".json":
        # Input is already intermediate JSON - skip from_svg step
        intermediate = file_path
    else:
        # Input is SVG - extract intermediate JSON
        intermediate = from_svg(input_path, output_path=None, extract_viewbox=extract_viewbox)

    # Apply transformations
    result = from_json(
        intermediate,
        output_path=output_path,
        relabel=relabel,
        overlay_ids=overlay_ids,
        metadata=metadata,
    )

    return result


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
        bounds_fn: Optional custom function to calculate path bounds.
                  Takes path_d string, returns (min_x, min_y, max_x, max_y).
                  If None, uses default parse_svg_path_bounds.

    Returns:
        Tuple of (geometry, overlay_geometry, viewbox):
            - geometry: Main interactive regions (dict mapping IDs to SVG paths)
            - overlay_geometry: Non-interactive overlays (dict mapping IDs to SVG paths)
            - viewbox: ViewBox string in format "min_x min_y width height"

    Raises:
        FileNotFoundError: If json_path does not exist
        ValueError: If JSON parsing fails

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

        >>> # Use custom bounds calculator for accurate curve handling
        >>> from svgpathtools import parse_path
        >>> def accurate_bounds(path_d: str) -> tuple[float, float, float, float]:
        ...     path = parse_path(path_d)
        ...     xmin, xmax, ymin, ymax = path.bbox()
        ...     return (xmin, ymin, xmax, ymax)
        >>> geom, overlays, vb = load_geometry(
        ...     "map.json",
        ...     bounds_fn=accurate_bounds
        ... )
    """
    json_path = Path(json_path)
    if not json_path.exists():
        msg = f"JSON file not found: {json_path}"
        raise FileNotFoundError(msg)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
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
            vb_tuple = _calculate_viewbox(all_paths, padding=viewbox_padding, bounds_fn=bounds_fn)
        else:
            vb_tuple = _calculate_viewbox(geometry, padding=viewbox_padding, bounds_fn=bounds_fn)

        # Format as viewBox string
        viewbox = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"

    return geometry, overlay_geometry, viewbox


def compute_viewbox_from_dict(
    geometry: dict[str, str | list[str]],
    padding: float = 0.0,
    bounds_fn: BoundsCalculator | None = None,
) -> str:
    """Compute viewBox string directly from a geometry dictionary.

    This is a convenience function that computes viewBox from a geometry dict
    without requiring file I/O. Accepts both string-valued dicts (shinymap format)
    and list-valued dicts (intermediate JSON format).

    Args:
        geometry: Dict mapping region IDs to SVG path data (string or list of strings).
                  Non-string/non-list values (like _metadata) are automatically skipped.
        padding: Percentage of dimensions to add as padding (0.05 = 5%)
        bounds_fn: Optional custom function to calculate path bounds.
                  Takes path_d string, returns (min_x, min_y, max_x, max_y).
                  If None, uses default _parse_svg_path_bounds (regex-based).

    Returns:
        ViewBox string in format "min_x min_y width height"

    Example:
        >>> # From shinymap format (string values)
        >>> geometry = {"a": "M 0 0 L 100 0 L 100 100 Z"}
        >>> compute_viewbox_from_dict(geometry)
        '0.0 0.0 100.0 100.0'

        >>> # With padding
        >>> compute_viewbox_from_dict(geometry, padding=0.1)
        '-10.0 -10.0 120.0 120.0'

        >>> # From intermediate JSON format (list values)
        >>> intermediate = {
        ...     "_metadata": {"viewBox": "ignored"},
        ...     "path_1": ["M 10 10 L 40 10 L 40 40 Z"],
        ... }
        >>> compute_viewbox_from_dict(intermediate)
        '10.0 10.0 30.0 30.0'

        >>> # Custom bounds calculator
        >>> from svgpathtools import parse_path
        >>> def accurate_bounds(path_d: str) -> tuple[float, float, float, float]:
        ...     path = parse_path(path_d)
        ...     xmin, xmax, ymin, ymax = path.bbox()
        ...     return (xmin, ymin, xmax, ymax)
        >>> compute_viewbox_from_dict(geometry, bounds_fn=accurate_bounds)
        '0.0 0.0 100.0 100.0'
    """
    # Normalize geometry dict to string format
    paths = _normalize_geometry_dict(geometry)

    # Compute viewBox using existing _calculate_viewbox
    vb_tuple = _calculate_viewbox(paths, padding=padding, bounds_fn=bounds_fn)

    # Format as viewBox string
    return f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"


def infer_relabel(
    initial_file: Path | str,
    final_json: dict[str, Any] | Path | str,
) -> dict[str, str | list[str]] | None:
    """Infer relabel mapping by comparing initial file (SVG or JSON) with final JSON.

    Automatically detects file type and extracts intermediate representation,
    then compares with final JSON to infer transformations.

    Args:
        initial_file: Path to initial SVG or intermediate JSON file
        final_json: Final JSON dict or path after transformations

    Returns:
        Relabel mapping dict, or None if no transformations detected

    Example:
        >>> # From SVG to final JSON
        >>> infer_relabel("map.svg", "final.json")
        {"region_a": "path_1", "hokkaido": ["path_2", "path_3"]}

        >>> # From intermediate JSON to final JSON
        >>> infer_relabel("intermediate.json", "final.json")
        {"region_a": "path_1", "hokkaido": ["path_2", "path_3"]}
    """
    # Load initial file
    initial_path = Path(initial_file)
    if not initial_path.exists():
        msg = f"Initial file not found: {initial_path}"
        raise FileNotFoundError(msg)

    # Determine file type and extract intermediate JSON
    if initial_path.suffix.lower() == ".json":
        # Already intermediate JSON
        with open(initial_path) as f:
            intermediate_data = json.load(f)
    else:
        # Assume SVG - extract intermediate
        intermediate_data = from_svg(initial_path, output_path=None, extract_viewbox=True)

    # Load final JSON
    if isinstance(final_json, (Path, str)):
        with open(final_json) as f:
            final_data = json.load(f)
    else:
        final_data = final_json

    # Extract path data (lists only, skip metadata)
    intermediate_paths = {k: v for k, v in intermediate_data.items() if isinstance(v, list)}
    final_paths = {k: v for k, v in final_data.items() if isinstance(v, list)}

    # Build reverse mapping: tuple(path_list) -> intermediate_id
    intermediate_data_to_id: dict[tuple[str, ...], str] = {
        tuple(path_list): iid for iid, path_list in intermediate_paths.items()
    }

    relabel: dict[str, str | list[str]] = {}

    for final_id, final_path_list in final_paths.items():
        final_tuple = tuple(final_path_list)

        # Check if this exact list matches an intermediate path
        if final_tuple in intermediate_data_to_id:
            intermediate_id = intermediate_data_to_id[final_tuple]
            if intermediate_id != final_id:
                # Rename detected
                relabel[final_id] = intermediate_id
            # else: no change (same ID, same data)
        else:
            # Not an exact match - could be a merge
            # Try to find intermediate paths whose concatenation equals final path
            # Since paths are stored as lists, check if final is concatenation of intermediates

            # Strategy: find intermediate IDs whose paths match elements in final_path_list
            matched_ids = []
            for path_str in final_path_list:
                # Find intermediate ID with this exact path as single element
                found = False
                for iid, ipath_list in intermediate_paths.items():
                    if len(ipath_list) == 1 and ipath_list[0] == path_str:
                        matched_ids.append(iid)
                        found = True
                        break
                if not found:
                    # Path doesn't match any intermediate - might be manually edited
                    matched_ids = []
                    break

            if matched_ids and len(matched_ids) > 1:
                # Merge detected
                relabel[final_id] = matched_ids
            # else: couldn't infer transformation (skip)

    return relabel if relabel else None
