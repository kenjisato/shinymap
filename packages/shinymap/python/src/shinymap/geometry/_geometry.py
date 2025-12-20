"""Geometry class for canonical geometry representation."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path as PathType
from typing import TYPE_CHECKING, Any

from ._bounds import _normalize_geometry_dict, calculate_viewbox

if TYPE_CHECKING:
    from ._elements import Element


@dataclass
class Geometry:
    """Canonical geometry representation with polymorphic elements.

    This class encapsulates SVG geometry with metadata. It supports both:
    - v0.x format: String-based paths (for backward compatibility)
    - v1.x format: Polymorphic element objects (Circle, Rect, Path, etc.)

    The class automatically converts between formats for seamless migration.

    Attributes:
        regions: Dictionary mapping region IDs to lists of elements
                 (str for v0.x compatibility, Element objects for v1.x)
        metadata: Optional metadata dict (viewBox, overlays, source, license, etc.)

    Note on aesthetics:
        SVG elements preserve aesthetic attributes (fill, stroke, etc.) but these
        are NOT used by shinymap for rendering. Interactive appearance is controlled
        via Python API. Preserved values are for SVG export and reference only.

    Example:
        >>> # v0.x format (backward compatible)
        >>> data = {"region1": ["M 0 0 L 10 0"], "_metadata": {"viewBox": "0 0 100 100"}}
        >>> geo = Geometry.from_dict(data)
        >>>
        >>> # v1.x format (polymorphic elements)
        >>> from shinymap.geometry import Circle
        >>> geo = Geometry(regions={"r1": [Circle(cx=100, cy=100, r=50)]}, metadata={})
    """
    regions: dict[str, list[str | Element]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Geometry:
        """Load geometry from dict (supports v0.x strings and v1.x element dicts).

        Automatically detects format and converts:
        - v0.x: String paths → kept as strings (backward compatible)
        - v1.x: Element dicts → deserialized to Element objects

        Args:
            data: Dictionary with regions and optional _metadata key

        Returns:
            Geometry object with normalized list-based regions

        Raises:
            ValueError: If _metadata exists but is not a dict

        Example:
            >>> # v0.x string format (backward compatible)
            >>> Geometry.from_dict({"a": "M 0 0 L 10 0"})
            Geometry(regions={'a': ['M 0 0 L 10 0']}, metadata={})

            >>> # v0.x list format
            >>> Geometry.from_dict({"a": ["M 0 0", "L 10 0"]})
            Geometry(regions={'a': ['M 0 0', 'L 10 0']}, metadata={})

            >>> # v1.x element format
            >>> Geometry.from_dict({"a": [{"type": "circle", "cx": 100, "cy": 100, "r": 50}]})
            Geometry(regions={'a': [Circle(cx=100, cy=100, r=50)]}, metadata={})
        """
        from ._element_mixins import JSONSerializableMixin

        regions: dict[str, list[str | Element]] = {}
        metadata = {}

        for key, value in data.items():
            if key == "_metadata":
                if not isinstance(value, dict):
                    raise ValueError(f"_metadata must be a dict, got {type(value).__name__}")
                metadata = value
            elif isinstance(value, list):
                # List format - check if elements are dicts (v1.x) or strings (v0.x)
                if value and isinstance(value[0], dict):
                    # v1.x format: list of element dicts - use generic from_dict
                    elements = [JSONSerializableMixin.from_dict(elem_dict) for elem_dict in value]
                    regions[key] = elements
                else:
                    # v0.x format: list of strings
                    regions[key] = value
            elif isinstance(value, str):
                # v0.x format: single string path
                regions[key] = [value]

        return cls(regions=regions, metadata=metadata)

    @classmethod
    def from_json(cls, json_path: str | PathType) -> Geometry:
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
        path = PathType(json_path)
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
        svg_path: str | PathType,
        extract_viewbox: bool = True,
    ) -> Geometry:
        """Extract geometry from SVG file (all element types).

        Extracts all supported SVG shape elements (path, circle, rect, polygon,
        ellipse, line, text) and generates auto-IDs for elements without IDs.
        This is v1.0 behavior - returns polymorphic Element objects instead of
        path strings.

        Preserves SVG aesthetics (fill, stroke, etc.) but these are NOT used
        by shinymap for rendering. See class docstring for details.

        Args:
            svg_path: Path to input SVG file
            extract_viewbox: If True, extract viewBox from SVG root element

        Returns:
            Geometry object with extracted elements (v1.x format)

        Raises:
            FileNotFoundError: If svg_path does not exist
            ValueError: If SVG parsing fails

        Example:
            >>> # Basic extraction (all element types)
            >>> geo = Geometry.from_svg("design.svg")
            >>> geo.regions.keys()
            dict_keys(['circle_1', 'rect_1', 'path_1', 'text_1'])
            >>>
            >>> # With transformations
            >>> geo = Geometry.from_svg("map.svg")
            >>> geo.relabel({"hokkaido": ["circle_1", "circle_2"]})
            >>> geo.set_overlays(["_border"])
            >>> geo.to_json("output.json")
        """
        from ._elements import Circle, Ellipse, Line, Path, Polygon, Rect, Text

        svg_path = PathType(svg_path)
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

        # Extract all supported shape elements
        regions: dict[str, list[Element]] = {}
        auto_id_counters: dict[str, int] = {}

        # Helper to get or generate element ID
        def get_element_id(elem: ET.Element, elem_type: str) -> str:
            elem_id = elem.get("id")
            if elem_id:
                return elem_id
            # Generate auto-ID: increment counter then use new value
            counter = auto_id_counters.get(elem_type, 0)
            counter += 1
            auto_id_counters[elem_type] = counter
            return f"{elem_type}_{counter}"

        # Extract circles
        for circle_elem in root.findall(".//svg:circle", ns):
            elem_id = get_element_id(circle_elem, "circle")
            circle = Circle(
                cx=circle_elem.get("cx"),
                cy=circle_elem.get("cy"),
                r=circle_elem.get("r"),
                fill=circle_elem.get("fill"),
                stroke=circle_elem.get("stroke"),
                stroke_width=circle_elem.get("stroke-width"),
            )
            regions[elem_id] = [circle]

        # Extract rectangles
        for rect_elem in root.findall(".//svg:rect", ns):
            elem_id = get_element_id(rect_elem, "rect")
            rect = Rect(
                x=rect_elem.get("x"),
                y=rect_elem.get("y"),
                width=rect_elem.get("width"),
                height=rect_elem.get("height"),
                rx=rect_elem.get("rx"),
                ry=rect_elem.get("ry"),
                fill=rect_elem.get("fill"),
                stroke=rect_elem.get("stroke"),
                stroke_width=rect_elem.get("stroke-width"),
            )
            regions[elem_id] = [rect]

        # Extract paths
        for path_elem in root.findall(".//svg:path[@d]", ns):
            path_d = path_elem.get("d")
            if not path_d:
                continue
            elem_id = get_element_id(path_elem, "path")
            path = Path(
                d=path_d.strip(),
                fill=path_elem.get("fill"),
                stroke=path_elem.get("stroke"),
                stroke_width=path_elem.get("stroke-width"),
            )
            regions[elem_id] = [path]

        # Extract polygons
        for polygon_elem in root.findall(".//svg:polygon", ns):
            points_str = polygon_elem.get("points")
            if not points_str:
                continue
            elem_id = get_element_id(polygon_elem, "polygon")
            # Convert points string to list of numbers
            points = [float(p) for p in points_str.replace(",", " ").split()]
            polygon = Polygon(
                points=points,
                fill=polygon_elem.get("fill"),
                stroke=polygon_elem.get("stroke"),
                stroke_width=polygon_elem.get("stroke-width"),
            )
            regions[elem_id] = [polygon]

        # Extract ellipses
        for ellipse_elem in root.findall(".//svg:ellipse", ns):
            elem_id = get_element_id(ellipse_elem, "ellipse")
            ellipse = Ellipse(
                cx=ellipse_elem.get("cx"),
                cy=ellipse_elem.get("cy"),
                rx=ellipse_elem.get("rx"),
                ry=ellipse_elem.get("ry"),
                fill=ellipse_elem.get("fill"),
                stroke=ellipse_elem.get("stroke"),
                stroke_width=ellipse_elem.get("stroke-width"),
            )
            regions[elem_id] = [ellipse]

        # Extract lines
        for line_elem in root.findall(".//svg:line", ns):
            elem_id = get_element_id(line_elem, "line")
            line = Line(
                x1=line_elem.get("x1"),
                y1=line_elem.get("y1"),
                x2=line_elem.get("x2"),
                y2=line_elem.get("y2"),
                stroke=line_elem.get("stroke"),
                stroke_width=line_elem.get("stroke-width"),
            )
            regions[elem_id] = [line]

        # Extract text elements
        for text_elem in root.findall(".//svg:text", ns):
            elem_id = get_element_id(text_elem, "text")
            # Get text content (may be in text attribute or as element text)
            text_content = text_elem.text or ""
            text = Text(
                x=text_elem.get("x"),
                y=text_elem.get("y"),
                text=text_content.strip() if text_content else None,
                font_size=text_elem.get("font-size"),
                font_family=text_elem.get("font-family"),
                fill=text_elem.get("fill"),
            )
            regions[elem_id] = [text]

        # Build metadata
        metadata: dict[str, Any] = {}
        if viewbox:
            metadata["viewBox"] = viewbox

        return cls(regions=regions, metadata=metadata)

    def viewbox(self, padding: float = 0.02) -> tuple[float, float, float, float]:
        """Get viewBox from metadata, or compute from geometry coordinates.

        Works with both v0.x (string paths) and v1.x (Element objects).

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

        # Compute from geometry
        # Collect all bounds from all elements
        all_bounds: list[tuple[float, float, float, float]] = []

        for elements in self.regions.values():
            for elem in elements:
                if isinstance(elem, str):
                    # v0.x format: parse path string
                    from ._bounds import _parse_svg_path_bounds

                    bounds = _parse_svg_path_bounds(elem)
                    all_bounds.append(bounds)
                else:
                    # v1.x format: use element's bounds() method
                    bounds = elem.bounds()
                    all_bounds.append(bounds)

        if not all_bounds:
            return (0.0, 0.0, 100.0, 100.0)

        # Compute overall bounding box
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

    def main_regions(self) -> dict[str, list[str | Element]]:
        """Get main regions (excluding overlays).

        Returns:
            Dict of main regions {regionId: [element1, ...]}
            (elements can be strings for v0.x or Element objects for v1.x)

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

    def overlay_regions(self) -> dict[str, list[str | Element]]:
        """Get overlay regions only.

        Returns:
            Dict of overlay regions {regionId: [element1, ...]}
            (elements can be strings for v0.x or Element objects for v1.x)

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

        Automatically serializes elements:
        - v0.x format: Strings are kept as-is
        - v1.x format: Element objects are serialized to dicts via to_dict()

        Returns:
            Dict with _metadata and region data (v0.x strings or v1.x element dicts)

        Example:
            >>> # v0.x format (strings)
            >>> geo = Geometry.from_dict({"region": ["M 0 0"]})
            >>> geo.to_dict()
            {'_metadata': {}, 'region': ['M 0 0']}

            >>> # v1.x format (elements)
            >>> from shinymap.geometry import Circle
            >>> geo = Geometry(regions={"r1": [Circle(cx=100, cy=100, r=50)]}, metadata={})
            >>> geo.to_dict()
            {'_metadata': {}, 'r1': [{'type': 'circle', 'cx': 100, 'cy': 100, 'r': 50}]}
        """
        output: dict[str, Any] = {}
        if self.metadata:
            output["_metadata"] = dict(self.metadata)

        # Serialize regions: keep strings as-is, serialize Element objects
        for region_id, elements in self.regions.items():
            serialized_elements = []
            for elem in elements:
                if isinstance(elem, str):
                    # v0.x format: keep string as-is
                    serialized_elements.append(elem)
                else:
                    # v1.x format: serialize Element to dict
                    serialized_elements.append(elem.to_dict())
            output[region_id] = serialized_elements

        return output

    def to_json(self, output_path: str | PathType) -> None:
        """Write geometry to JSON file.

        Args:
            output_path: Path to write JSON file

        Example:
            >>> geo = Geometry.from_svg("map.svg")
            >>> geo.to_json("output.json")
        """
        output_path = PathType(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
