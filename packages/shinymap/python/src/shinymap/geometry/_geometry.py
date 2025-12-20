"""Geometry class for canonical geometry representation."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._bounds import _normalize_geometry_dict, calculate_viewbox


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
    def from_dict(cls, data: dict[str, Any]) -> Geometry:
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

    @classmethod
    def from_json(cls, json_path: str | Path) -> Geometry:
        """Load geometry from JSON file.

        Args:
            json_path: Path to JSON file in shinymap format

        Returns:
            Geometry object with normalized list-based paths

        Example:
            >>> geo = Geometry.from_json("japan_prefectures.json")
            >>> geo.regions.keys()
            dict_keys(['01', '02', ...])
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {path}")

        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON file: {e}") from e

        return cls.from_dict(data)

    @classmethod
    def from_svg(
        cls,
        svg_path: str | Path,
        extract_viewbox: bool = True,
    ) -> Geometry:
        """Extract geometry from SVG file.

        Extracts path elements from an SVG file and generates auto-IDs for paths
        without IDs (path_1, path_2, etc.). This is the starting point for the
        interactive workflow where you can inspect extracted paths and apply
        transformations.

        Args:
            svg_path: Path to input SVG file
            extract_viewbox: If True, extract viewBox from SVG root element

        Returns:
            Geometry object with extracted paths

        Raises:
            FileNotFoundError: If svg_path does not exist
            ValueError: If SVG parsing fails

        Example:
            >>> # Basic extraction
            >>> geo = Geometry.from_svg("map.svg")
            >>> geo.regions.keys()
            dict_keys(['path_1', 'path_2', 'path_3'])
            >>>
            >>> # With transformations
            >>> geo = Geometry.from_svg("map.svg")
            >>> geo.relabel({"hokkaido": ["path_1", "path_2"]})
            >>> geo.set_overlays(["_border"])
            >>> geo.to_json("output.json")
        """
        svg_path = Path(svg_path)
        if not svg_path.exists():
            raise FileNotFoundError(f"SVG file not found: {svg_path}")

        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse SVG: {e}") from e

        # SVG namespace handling
        ns = {"svg": "http://www.w3.org/2000/svg"}

        # Extract viewBox from root SVG element
        viewbox = None
        if extract_viewbox:
            viewbox = root.get("viewBox")

        # Extract all path elements with d attribute
        # Generate IDs for paths without them
        regions: dict[str, list[str]] = {}
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

            regions[path_id] = [path_d.strip()]

        # Build metadata
        metadata: dict[str, Any] = {}
        if viewbox:
            metadata["viewBox"] = viewbox

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
        return calculate_viewbox(paths, padding=padding, bounds_fn=None)

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
        overlays = self.metadata.get("overlays", [])
        return list(overlays) if isinstance(overlays, list) else []

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

    def relabel(self, mapping: dict[str, str | list[str]]) -> Geometry:
        """Rename or merge regions (returns new Geometry object).

        This method applies relabeling transformations to create a new Geometry
        object with renamed or merged regions. Original object is unchanged.

        Args:
            mapping: Dict mapping new IDs to old ID(s)
                - String value: rename single region (e.g., {"tokyo": "path_5"})
                - List value: merge multiple regions (e.g., {"hokkaido": ["path_1", "path_2"]})

        Returns:
            New Geometry object with relabeled regions

        Raises:
            ValueError: If an old ID in mapping doesn't exist

        Example:
            >>> geo = Geometry.from_dict({
            ...     "path_1": ["M 0 0 L 10 0"],
            ...     "path_2": ["M 20 0 L 30 0"],
            ...     "path_3": ["M 40 0 L 50 0"]
            ... })
            >>> # Rename and merge
            >>> geo2 = geo.relabel({
            ...     "region_a": ["path_1", "path_2"],  # Merge
            ...     "_border": "path_3"                 # Rename
            ... })
            >>> geo2.regions.keys()
            dict_keys(['region_a', '_border'])
        """
        new_regions: dict[str, list[str]] = {}
        relabeled_ids: set[str] = set()

        # Apply relabeling
        for new_id, old_id_or_ids in mapping.items():
            # Normalize to list for uniform processing
            old_ids = [old_id_or_ids] if isinstance(old_id_or_ids, str) else old_id_or_ids

            # Collect all paths (flatten nested lists from multiple regions)
            path_parts = []
            for old_id in old_ids:
                if old_id not in self.regions:
                    raise ValueError(f"Path '{old_id}' not found in geometry")
                # Extend to flatten: self.regions[old_id] is already a list
                path_parts.extend(self.regions[old_id])
                relabeled_ids.add(old_id)

            # Store as list (single region = single-element, merge = multi-element)
            new_regions[new_id] = path_parts

        # Keep regions that weren't relabeled
        for region_id, paths in self.regions.items():
            if region_id not in relabeled_ids:
                new_regions[region_id] = paths

        return Geometry(regions=new_regions, metadata=dict(self.metadata))

    def set_overlays(self, overlay_ids: list[str]) -> Geometry:
        """Set overlay region IDs in metadata (returns new Geometry object).

        Args:
            overlay_ids: List of region IDs to mark as overlays

        Returns:
            New Geometry object with updated overlay metadata

        Example:
            >>> geo = Geometry.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"]
            ... })
            >>> geo2 = geo.set_overlays(["_border"])
            >>> geo2.overlays()
            ['_border']
        """
        new_metadata = dict(self.metadata)
        new_metadata["overlays"] = overlay_ids
        return Geometry(regions=dict(self.regions), metadata=new_metadata)

    def update_metadata(self, metadata: dict[str, Any]) -> Geometry:
        """Update metadata (returns new Geometry object).

        Merges provided metadata with existing metadata. Existing keys are
        overwritten by new values.

        Args:
            metadata: Dict of metadata to merge

        Returns:
            New Geometry object with updated metadata

        Example:
            >>> geo = Geometry.from_dict({"region": ["M 0 0"]})
            >>> geo2 = geo.update_metadata({
            ...     "source": "Wikimedia Commons",
            ...     "license": "CC BY-SA 3.0"
            ... })
            >>> geo2.metadata["source"]
            'Wikimedia Commons'
        """
        new_metadata = {**self.metadata, **metadata}
        return Geometry(regions=dict(self.regions), metadata=new_metadata)

    def to_dict(self) -> dict[str, Any]:
        """Export to dict in shinymap JSON format.

        Returns:
            Dict with _metadata and region paths (list-based format)

        Example:
            >>> geo = Geometry.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_metadata": {"viewBox": "0 0 100 100"}
            ... })
            >>> geo.to_dict()
            {'_metadata': {'viewBox': '0 0 100 100'}, 'region': ['M 0 0']}
        """
        output: dict[str, Any] = {}
        if self.metadata:
            output["_metadata"] = dict(self.metadata)
        output.update(self.regions)
        return output

    def to_json(self, output_path: str | Path) -> None:
        """Write geometry to JSON file.

        Args:
            output_path: Path to write JSON file

        Example:
            >>> geo = Geometry.from_svg("map.svg")
            >>> geo.to_json("output.json")
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
