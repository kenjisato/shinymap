"""SVG conversion utilities for transforming SVG files to shinymap JSON format.

This module provides functions for converting SVG files to shinymap JSON format:
- from_svg(): Extract paths from SVG with auto-generated IDs
- from_json(): Apply transformations to extracted JSON
- convert(): One-shot conversion combining both steps
- infer_relabel(): Infer relabel mapping by comparing files
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._outline import Outline


def from_svg(
    svg_path: Path | str,
    output_path: Path | str | None = None,
    extract_viewbox: bool = True,
) -> dict[str, Any]:
    """Extract extracted JSON from SVG file (Step 1 of interactive workflow).

    This function extracts path elements from an SVG file and generates auto-IDs
    for paths without IDs. The result is "extracted JSON" (before relabeling) that
    can be further transformed using from_json().

    For one-shot conversion with all transformations, use convert() instead.
    For OOP API, use Outline.from_svg() instead.

    Args:
        svg_path: Path to input SVG file
        output_path: Optional path to write JSON output (if None, returns dict only)
        extract_viewbox: If True, extract viewBox from SVG root element

    Returns:
        Dict in extracted JSON format with auto-generated IDs

    Raises:
        FileNotFoundError: If svg_path does not exist
        ValueError: If SVG parsing fails

    Example:
        >>> # Interactive workflow: Step 1 - Extract
        >>> extracted = from_svg("map.svg", "map_extracted.json")
        >>> # Inspect extracted JSON, identify paths to group/rename
        >>> # Step 2 - Apply transformations
        >>> final = from_json(
        ...     extracted,
        ...     relabel={"region_01": "path_1", "hokkaido": ["path_2", "path_3"]}
        ... )

        >>> # Or: one-shot conversion
        >>> final = convert(
        ...     "map.svg",
        ...     "map.json",
        ...     relabel={"region_01": "path_1"}
        ... )
    """
    # Use Outline class method internally
    geo = Outline.from_svg(svg_path, extract_viewbox=extract_viewbox)

    # Write to file if output_path provided
    if output_path:
        geo.to_json(output_path)

    return geo.to_dict()


def from_json(
    extracted_json: dict[str, Any] | Path | str,
    output_path: Path | str | None = None,
    relabel: dict[str, str | list[str]] | None = None,
    overlay_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Transform extracted JSON to final JSON (Step 2 of interactive workflow).

    This function takes "extracted" JSON (raw SVG paths with auto-generated IDs)
    and applies relabeling (renaming/grouping) and metadata updates to produce final JSON.

    For OOP API, use Outline.from_dict() or Outline.from_json_file() with method chaining instead.

    Args:
        extracted_json: Input JSON dict (or path to JSON file) with path data
        output_path: Optional path to write JSON output (if None, returns dict only)
        relabel: Optional dict to rename or merge paths. Maps new ID to old ID(s).
                 - String value: rename single path (e.g., {"okinawa": "path_3"})
                 - List value: merge multiple paths (e.g., {"hokkaido": ["path_1", "path_2"]})
        overlay_ids: List of path IDs to mark as overlays in metadata
        metadata: Additional metadata to merge with existing _metadata field

    Returns:
        Transformed JSON dict in shinymap format

    Raises:
        FileNotFoundError: If extracted_json is a path and file doesn't exist
        ValueError: If JSON parsing fails or relabeled paths not found

    Example:
        >>> # Interactive workflow
        >>> # Step 1: Extract
        >>> extracted = from_svg("map.svg")
        >>>
        >>> # Inspect extracted, plan transformations
        >>> print(list(extracted.keys()))
        ['_metadata', 'path_1', 'path_2', 'path_3']
        >>>
        >>> # Step 2: Apply transformations
        >>> final = from_json(
        ...     extracted,
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
        >>> final["_border"]  # Renamed from path_3
        >>> final["_metadata"]["overlays"]
        ['_border']
    """
    # Load from file or dict
    if isinstance(extracted_json, (Path, str)):
        geo = Outline.from_json(extracted_json)
    else:
        geo = Outline.from_dict(extracted_json)

    # Apply transformations using Outline methods
    if relabel:
        geo = geo.relabel(relabel)
    if overlay_ids:
        geo = geo.set_overlays(overlay_ids)
    if metadata:
        geo = geo.update_metadata(metadata)

    # Write to file if output_path provided
    if output_path:
        geo.to_json(output_path)

    return geo.to_dict()


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
    file_path = Path(input_path).expanduser()

    intermediate: dict[str, Any] | Path
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
    initial_path = Path(initial_file).expanduser()
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

    # Helper to convert element to hashable representation
    def to_hashable(elem):
        """Convert element (string or dict) to hashable form."""
        if isinstance(elem, str):
            return elem
        elif isinstance(elem, dict):
            # Convert dict to sorted tuple of items for hashing
            return tuple(sorted(elem.items()))
        else:
            return str(elem)

    # Build reverse mapping: tuple(path_list) -> intermediate_id
    # Use hashable representation for v1.x element dicts
    intermediate_data_to_id: dict[tuple, str] = {
        tuple(to_hashable(elem) for elem in path_list): iid
        for iid, path_list in intermediate_paths.items()
    }

    relabel: dict[str, str | list[str]] = {}

    for final_id, final_path_list in final_paths.items():
        final_tuple = tuple(to_hashable(elem) for elem in final_path_list)

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
            for elem in final_path_list:
                # Find intermediate ID with this exact element as single-element list
                elem_hashable = to_hashable(elem)
                found = False
                for iid, ipath_list in intermediate_paths.items():
                    if len(ipath_list) == 1 and to_hashable(ipath_list[0]) == elem_hashable:
                        matched_ids.append(iid)
                        found = True
                        break
                if not found:
                    # Element doesn't match any intermediate - might be manually edited
                    matched_ids = []
                    break

            if matched_ids and len(matched_ids) > 1:
                # Merge detected
                relabel[final_id] = matched_ids
            # else: couldn't infer transformation (skip)

    return relabel if relabel else None
