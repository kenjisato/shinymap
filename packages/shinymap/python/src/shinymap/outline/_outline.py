"""Outline class for canonical outline representation."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path as PathType
from typing import TYPE_CHECKING, Any

from ._regions import Regions

if TYPE_CHECKING:
    from ..svg import Element


@dataclass
class Outline:
    """Canonical outline representation with polymorphic elements.

    This class encapsulates SVG outline with metadata. It supports both:
    - v0.x format: String-based paths (for backward compatibility)
    - v1.x format: Polymorphic element objects (Circle, Rect, Path, etc.)

    The class automatically converts between formats for seamless migration.

    Attributes:
        regions: Regions object (dict subclass) mapping region IDs to lists of elements
                 (str for v0.x compatibility, Element objects for v1.x)
        metadata: Optional metadata dict (viewBox, overlays, source, license, etc.)

    Note on aesthetics:
        SVG elements preserve aesthetic attributes (fill, stroke, etc.) but these
        are NOT used by shinymap for rendering. Interactive appearance is controlled
        via Python API. Preserved values are for SVG export and reference only.

    Examples:
        ```pycon
        >>> # v0.x format (backward compatible)
        >>> data = {"region1": ["M 0 0 L 10 0"], "_metadata": {"viewBox": "0 0 100 100"}}
        >>> geo = Outline.from_dict(data)

        >>> # v1.x format (polymorphic elements)
        >>> from shinymap.svg import Circle
        >>> geo = Outline(regions={"r1": [Circle(cx=100, cy=100, r=50)]}, metadata={})
        ```
    """

    regions: Regions
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Convert regions to Regions object if needed."""
        if not isinstance(self.regions, Regions):
            self.regions = Regions(self.regions)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Outline:
        """Load outline from dict (supports v0.x strings and v1.x element dicts).

        Automatically detects format and converts:
        - v0.x: String paths → kept as strings (backward compatible)
        - v1.x: Element dicts → deserialized to Element objects

        Args:
            data: Dictionary with regions and optional _metadata key

        Returns:
            Outline object with normalized list-based regions

        Raises:
            ValueError: If _metadata exists but is not a dict

        Examples:
            ```pycon
            >>> # v0.x string format (backward compatible)
            >>> outline = Outline.from_dict({"a": "M 0 0 L 10 0"})
            >>> list(outline.regions.keys())
            ['a']

            >>> # v0.x list format
            >>> outline = Outline.from_dict({"a": ["M 0 0", "L 10 0"]})
            >>> outline.regions["a"]
            ['M 0 0', 'L 10 0']

            >>> # v1.x element format
            >>> data = {"a": [{"type": "circle", "cx": 100, "cy": 100, "r": 50}]}
            >>> outline = Outline.from_dict(data)
            >>> outline.regions["a"]
            [Circle(cx=100, cy=100, r=50)]
            ```
        """
        from ..svg._mixins import JSONSerializableMixin

        regions_dict: dict[str, list[str | Element]] = {}
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
                    regions_dict[key] = elements
                else:
                    # v0.x format: list of strings
                    regions_dict[key] = value
            elif isinstance(value, str):
                # v0.x format: single string path
                regions_dict[key] = [value]

        return cls(regions=Regions(regions_dict), metadata=metadata)

    @classmethod
    def from_json(cls, json_path: str | PathType) -> Outline:
        """Load outline from JSON file.

        Args:
            json_path: Path to JSON file in shinymap format

        Returns:
            Outline object with normalized list-based paths

        Examples:
            ```pycon
            >>> geo = Outline.from_json("japan_prefectures.json")  # doctest: +SKIP
            >>> geo.regions.keys()  # doctest: +SKIP
            dict_keys(['01', '02', ...])
            ```
        """
        path = PathType(json_path).expanduser()
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
    ) -> Outline:
        """Extract outline from SVG file (all element types).

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
            Outline object with extracted elements (v1.x format)

        Raises:
            FileNotFoundError: If svg_path does not exist
            ValueError: If SVG parsing fails

        Examples:
            ```pycon
            >>> # Basic extraction (all element types)
            >>> geo = Outline.from_svg("design.svg")  # doctest: +SKIP
            >>> geo.regions.keys()  # doctest: +SKIP
            dict_keys(['circle_1', 'rect_1', 'path_1', 'text_1'])

            >>> # With transformations
            >>> geo = Outline.from_svg("map.svg")  # doctest: +SKIP
            >>> geo.relabel({"hokkaido": ["circle_1", "circle_2"]})  # doctest: +SKIP
            >>> geo.set_overlays(["_border"])  # doctest: +SKIP
            >>> geo.to_json("output.json")  # doctest: +SKIP
            ```
        """
        from ..svg import Circle, Ellipse, Line, Path, Polygon, Rect, Text

        svg_path = PathType(svg_path).expanduser()
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
                cx=circle_elem.get("cx"),  # type: ignore[arg-type]
                cy=circle_elem.get("cy"),  # type: ignore[arg-type]
                r=circle_elem.get("r"),  # type: ignore[arg-type]
                fill=circle_elem.get("fill"),
                stroke=circle_elem.get("stroke"),
                stroke_width=circle_elem.get("stroke-width"),  # type: ignore[arg-type]
            )
            regions[elem_id] = [circle]

        # Extract rectangles
        for rect_elem in root.findall(".//svg:rect", ns):
            elem_id = get_element_id(rect_elem, "rect")
            # NOTE: svg.py accepts string attributes at runtime but type annotations expect numbers
            # This is a known limitation of svg.py's type annotations
            rect = Rect(
                x=rect_elem.get("x"),  # type: ignore[arg-type]
                y=rect_elem.get("y"),  # type: ignore[arg-type]
                width=rect_elem.get("width"),  # type: ignore[arg-type]
                height=rect_elem.get("height"),  # type: ignore[arg-type]
                rx=rect_elem.get("rx"),  # type: ignore[arg-type]
                ry=rect_elem.get("ry"),  # type: ignore[arg-type]
                fill=rect_elem.get("fill"),
                stroke=rect_elem.get("stroke"),
                stroke_width=rect_elem.get("stroke-width"),  # type: ignore[arg-type]
            )
            regions[elem_id] = [rect]

        # Extract paths
        # TODO: Detect paths that are semantically lines, not filled shapes.
        # Detection heuristics:
        # 1. fill="none" indicates stroke-only rendering
        # 2. Path 'd' attribute not ending with 'Z' (close path) indicates open path
        # Open paths without fill are typically lines (grid lines, dividers, borders).
        # Consider converting such paths to Line elements or marking them for
        # automatic stroke-only aesthetic handling.
        for path_elem in root.findall(".//svg:path[@d]", ns):
            path_d = path_elem.get("d")
            if not path_d:
                continue
            elem_id = get_element_id(path_elem, "path")
            path = Path(
                d=path_d.strip(),  # type: ignore[arg-type]
                fill=path_elem.get("fill"),
                stroke=path_elem.get("stroke"),
                stroke_width=path_elem.get("stroke-width"),  # type: ignore[arg-type]
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
                points=points,  # type: ignore[arg-type]
                fill=polygon_elem.get("fill"),
                stroke=polygon_elem.get("stroke"),
                stroke_width=polygon_elem.get("stroke-width"),  # type: ignore[arg-type]
            )
            regions[elem_id] = [polygon]

        # Extract ellipses
        for ellipse_elem in root.findall(".//svg:ellipse", ns):
            elem_id = get_element_id(ellipse_elem, "ellipse")
            ellipse = Ellipse(
                cx=ellipse_elem.get("cx"),  # type: ignore[arg-type]
                cy=ellipse_elem.get("cy"),  # type: ignore[arg-type]
                rx=ellipse_elem.get("rx"),  # type: ignore[arg-type]
                ry=ellipse_elem.get("ry"),  # type: ignore[arg-type]
                fill=ellipse_elem.get("fill"),
                stroke=ellipse_elem.get("stroke"),
                stroke_width=ellipse_elem.get("stroke-width"),  # type: ignore[arg-type]
            )
            regions[elem_id] = [ellipse]

        # Extract lines
        for line_elem in root.findall(".//svg:line", ns):
            elem_id = get_element_id(line_elem, "line")
            line = Line(
                x1=line_elem.get("x1"),  # type: ignore[arg-type]
                y1=line_elem.get("y1"),  # type: ignore[arg-type]
                x2=line_elem.get("x2"),  # type: ignore[arg-type]
                y2=line_elem.get("y2"),  # type: ignore[arg-type]
                stroke=line_elem.get("stroke"),
                stroke_width=line_elem.get("stroke-width"),  # type: ignore[arg-type]
            )
            regions[elem_id] = [line]

        # Extract text elements
        for text_elem in root.findall(".//svg:text", ns):
            elem_id = get_element_id(text_elem, "text")
            # Get text content (may be in text attribute or as element text)
            text_content = text_elem.text or ""
            text = Text(
                x=text_elem.get("x"),  # type: ignore[arg-type]
                y=text_elem.get("y"),  # type: ignore[arg-type]
                text=text_content.strip() if text_content else None,
                font_size=text_elem.get("font-size"),  # type: ignore[arg-type]
                font_family=text_elem.get("font-family"),
                font_weight=text_elem.get("font-weight"),  # type: ignore[arg-type]
                font_style=text_elem.get("font-style"),  # type: ignore[arg-type]
                text_anchor=text_elem.get("text-anchor"),  # type: ignore[arg-type]
                dominant_baseline=text_elem.get("dominant-baseline"),  # type: ignore[arg-type]
                fill=text_elem.get("fill"),
                transform=text_elem.get("transform"),  # type: ignore[arg-type]
            )
            regions[elem_id] = [text]

        # Build metadata
        metadata: dict[str, Any] = {}
        if viewbox:
            metadata["viewBox"] = viewbox

        return cls(regions=Regions(regions), metadata=metadata)  # type: ignore[arg-type]

    def viewbox(self, padding: float = 0.02) -> tuple[float, float, float, float]:
        """Get viewBox from metadata, or compute from outline coordinates.

        Works with both v0.x (string paths) and v1.x (Element objects).

        Args:
            padding: Padding fraction for computed viewBox (default 2%)

        Returns:
            ViewBox tuple in format (x, y, width, height)

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({"a": ["M 0 0 L 100 100"]})
            >>> geo.viewbox()  # Returns with 2% padding
            (-2.0, -2.0, 104.0, 104.0)
            ```
        """
        if "viewBox" in self.metadata:
            # Parse viewBox string to tuple
            vb_str = self.metadata["viewBox"]
            parts = vb_str.split()
            if len(parts) != 4:
                raise ValueError(f"Invalid viewBox format: {vb_str}")
            return (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))

        # Compute from outline
        # Collect all bounds from all elements
        all_bounds: list[tuple[float, float, float, float]] = []

        for elements in self.regions.values():
            for elem in elements:
                if isinstance(elem, str):
                    # v0.x format: parse path string
                    from ..utils import path_bb

                    bounds = path_bb(elem)
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

    def overlay_ids(self) -> list[str]:
        """Get region IDs in the overlay layer.

        Returns:
            List of region IDs in the overlay layer

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"],
            ...     "_metadata": {"overlay": ["_border"]}
            ... })
            >>> geo.overlay_ids()
            ['_border']
            ```
        """
        overlay = self.metadata.get("overlay", [])
        return list(overlay) if isinstance(overlay, list) else []

    def underlay_ids(self) -> list[str]:
        """Get region IDs in the underlay layer.

        Returns:
            List of region IDs in the underlay layer

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_bg": ["M 0 0 L 100 0 L 100 100 L 0 100 Z"],
            ...     "_metadata": {"underlay": ["_bg"]}
            ... })
            >>> geo.underlay_ids()
            ['_bg']
            ```
        """
        underlay = self.metadata.get("underlay", [])
        return list(underlay) if isinstance(underlay, list) else []

    def hidden_ids(self) -> list[str]:
        """Get region IDs in the hidden layer.

        Returns:
            List of region IDs in the hidden layer

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_temp": ["M 0 0 L 100 0"],
            ...     "_metadata": {"hidden": ["_temp"]}
            ... })
            >>> geo.hidden_ids()
            ['_temp']
            ```
        """
        hidden = self.metadata.get("hidden", [])
        return list(hidden) if isinstance(hidden, list) else []

    def layers_dict(self) -> dict[str, list[str]] | None:
        """Get layers configuration dict for JavaScript props.

        Returns a dict with overlay, underlay, and hidden keys if any
        layer configuration is present in metadata. Returns None if no
        layer configuration exists.

        Returns:
            Dict with layer configuration or None

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"],
            ...     "_metadata": {"overlay": ["_border"], "underlay": ["_bg"]}
            ... })
            >>> geo.layers_dict()
            {'overlay': ['_border'], 'underlay': ['_bg']}
            ```
        """
        overlay = self.overlay_ids()
        underlay = self.underlay_ids()
        hidden = self.hidden_ids()

        if not overlay and not underlay and not hidden:
            return None

        result: dict[str, list[str]] = {}
        if overlay:
            result["overlay"] = overlay
        if underlay:
            result["underlay"] = underlay
        if hidden:
            result["hidden"] = hidden

        return result

    def main_regions(self) -> Regions:
        """Get main regions (excluding overlay layer).

        Returns:
            Regions object with main regions {regionId: [element1, ...]}
            (elements can be strings for v0.x or Element objects for v1.x)

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"],
            ...     "_metadata": {"overlay": ["_border"]}
            ... })
            >>> geo.main_regions()
            Regions({
              'region': ['M 0 0'],
            })
            ```
        """
        overlay = set(self.overlay_ids())
        return Regions({k: v for k, v in self.regions.items() if k not in overlay})

    def overlay_regions(self) -> Regions:
        """Get overlay regions only.

        Returns:
            Regions object with overlay regions {regionId: [element1, ...]}
            (elements can be strings for v0.x or Element objects for v1.x)

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"],
            ...     "_metadata": {"overlay": ["_border"]}
            ... })
            >>> geo.overlay_regions()
            Regions({
              '_border': ['M 0 0 L 100 0'],
            })
            ```
        """
        overlay = set(self.overlay_ids())
        return Regions({k: v for k, v in self.regions.items() if k in overlay})

    def relabel(self, mapping: dict[str, str | list[str]]) -> Outline:
        """Rename or merge regions (returns new Outline object).

        This method applies relabeling transformations to create a new Outline
        object with renamed or merged regions. Original object is unchanged.

        Args:
            mapping: Dict mapping new IDs to old ID(s)
                - String value: rename single region (e.g., {"tokyo": "path_5"})
                - List value: merge multiple regions (e.g., {"hokkaido": ["path_1", "path_2"]})

        Returns:
            New Outline object with relabeled regions

        Raises:
            ValueError: If an old ID in mapping doesn't exist

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
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
            ```
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
                    raise ValueError(f"Path '{old_id}' not found in outline")
                # Extend to flatten: self.regions[old_id] is already a list
                path_parts.extend(self.regions[old_id])
                relabeled_ids.add(old_id)

            # Store as list (single region = single-element, merge = multi-element)
            new_regions[new_id] = path_parts  # type: ignore[assignment]

        # Keep regions that weren't relabeled
        for region_id, paths in self.regions.items():
            if region_id not in relabeled_ids:
                new_regions[region_id] = paths  # type: ignore[assignment]

        return Outline(regions=Regions(new_regions), metadata=dict(self.metadata))  # type: ignore[arg-type]

    def set_overlays(self, overlay_ids: list[str]) -> Outline:
        """Set overlay region IDs in metadata (returns new Outline object).

        Args:
            overlay_ids: List of region IDs to mark as overlays

        Returns:
            New Outline object with updated overlay metadata

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"]
            ... })
            >>> geo2 = geo.set_overlays(["_border"])
            >>> geo2.overlay_ids()
            ['_border']
            ```
        """
        new_metadata = dict(self.metadata)
        new_metadata["overlay"] = overlay_ids
        return Outline(regions=Regions(dict(self.regions)), metadata=new_metadata)

    def update_metadata(self, metadata: dict[str, Any]) -> Outline:
        """Update metadata (returns new Outline object).

        Merges provided metadata with existing metadata. Existing keys are
        overwritten by new values.

        Args:
            metadata: Dict of metadata to merge

        Returns:
            New Outline object with updated metadata

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({"region": ["M 0 0"]})
            >>> geo2 = geo.update_metadata({
            ...     "source": "Wikimedia Commons",
            ...     "license": "CC BY-SA 3.0"
            ... })
            >>> geo2.metadata["source"]
            'Wikimedia Commons'
            ```
        """
        new_metadata = {**self.metadata, **metadata}
        return Outline(regions=Regions(dict(self.regions)), metadata=new_metadata)

    def path_as_line(self, *region_ids: str) -> Outline:
        """Mark regions as lines described in path notation.

        Some SVG paths represent lines (dividers, borders, grids) rather than
        filled shapes. This method stores the region IDs so that stroke-only
        aesthetics are automatically applied.

        Args:
            *region_ids: Region IDs containing line elements in path notation

        Returns:
            New Outline object with line regions recorded in metadata

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
            ...     "region": ["M 0 0 L 100 100"],
            ...     "_divider": ["M 50 0 L 50 100"]
            ... })
            >>> geo2 = geo.path_as_line("_divider")
            >>> # Now _divider will use stroke-only rendering
            ```
        """
        # Get existing list or create new one
        existing = list(self.metadata.get("lines_as_path", []))

        # Add new region IDs (avoid duplicates)
        for region_id in region_ids:
            if region_id not in existing:
                existing.append(region_id)

        new_metadata = {**self.metadata, "lines_as_path": existing}
        return Outline(regions=Regions(dict(self.regions)), metadata=new_metadata)

    def region_types(self) -> dict[str, str]:
        """Get aesthetic element type for each region.

        Returns a mapping of region_id -> element_type where element_type is
        one of "shape", "line", or "text" for aesthetic resolution purposes.

        Priority:
        1. metadata["lines_as_path"] - explicit line override for path elements
        2. Element's element_name:
           - "line" → "line"
           - "text" → "text"
           - All others → "shape"

        Returns:
            Dict mapping region IDs to their aesthetic element types

        Examples:
            ```pycon
            >>> # v1.x format with mixed elements
            >>> from shinymap.svg import Circle, Line, Text, Path
            >>> outline = Outline(regions={
            ...     "region": [Circle(cx=50, cy=50, r=30)],
            ...     "_divider": [Line(x1=0, y1=50, x2=100, y2=50)],
            ...     "label": [Text(x=50, y=50, text="A")],
            ... }, metadata={})
            >>> outline.region_types()
            {'region': 'shape', '_divider': 'line', 'label': 'text'}

            >>> # Path marked as line via path_as_line()
            >>> outline = Outline(regions={
            ...     "_border": [Path(d="M 0 0 L 100 0")],
            ... }, metadata={}).path_as_line("_border")
            >>> outline.region_types()
            {'_border': 'line'}
            ```
        """
        lines_as_path = set(self.metadata.get("lines_as_path", []))
        result: dict[str, str] = {}

        for region_id, elements in self.regions.items():
            # Check explicit line override first
            if region_id in lines_as_path:
                result[region_id] = "line"
                continue

            if not elements:
                result[region_id] = "shape"
                continue

            first_elem = elements[0]
            if isinstance(first_elem, str):
                # v0.x format: string path → shape (unless in lines_as_path, checked above)
                result[region_id] = "shape"
            else:
                # v1.x format: check element_name
                elem_name = getattr(first_elem, "element_name", "path")
                if elem_name == "line":
                    result[region_id] = "line"
                elif elem_name == "text":
                    result[region_id] = "text"
                else:
                    result[region_id] = "shape"

        return result

    def groups(self) -> dict[str, list[str]]:
        """Get group membership from metadata.

        Returns:
            Dict mapping group names to lists of region IDs

        Examples:
            ```pycon
            >>> geo = Outline.from_dict({
            ...     "region1": ["M 0 0"],
            ...     "region2": ["M 10 0"],
            ...     "_metadata": {"groups": {"coastal": ["region1", "region2"]}}
            ... })
            >>> geo.groups()
            {'coastal': ['region1', 'region2']}
            ```
        """
        return dict(self.metadata.get("groups", {}))

    def metadata_dict(
        self, view_box: tuple[float, float, float, float] | None = None
    ) -> dict[str, Any] | None:
        """Build outline metadata dict for JavaScript props.

        Creates the outlineMetadata object sent to React components,
        containing viewBox and groups information.

        Args:
            view_box: Optional override viewBox tuple. If None, uses self.viewbox()

        Returns:
            Dict with viewBox and groups, or None if no metadata

        Examples:
            ```pycon
            >>> outline = Outline.from_dict({
            ...     "region1": ["M 0 0 L 100 100"],
            ...     "_metadata": {"groups": {"coastal": ["region1"]}}
            ... })
            >>> outline.metadata_dict()
            {'viewBox': '-2.0 -2.0 104.0 104.0', 'groups': {'coastal': ['region1']}}
            ```
        """
        if not self.metadata:
            return None

        vb_tuple = view_box if view_box else self.viewbox()
        vb_str = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"

        result: dict[str, Any] = {"viewBox": vb_str}

        groups = self.metadata.get("groups")
        if groups:
            result["groups"] = groups

        return result if result else None

    def merge_layers(self, layers: dict[str, list[str]] | None) -> Outline:
        """Merge provided layers with outline's metadata.

        Returns a new Outline with updated metadata containing the merged
        layers configuration. Explicit layers take priority over existing metadata.

        This method follows the immutable pattern - the original Outline is
        unchanged and a new Outline is returned.

        Args:
            layers: Optional explicit layer configuration with keys:
                    underlay, overlay, hidden

        Returns:
            New Outline with merged layers in metadata

        Examples:
            ```pycon
            >>> outline = Outline.from_dict({
            ...     "region": ["M 0 0"],
            ...     "_border": ["M 0 0 L 100 0"],
            ...     "_metadata": {"overlay": ["_border"]}
            ... })
            >>> merged = outline.merge_layers({"underlay": ["_bg"]})
            >>> merged.metadata
            {'overlay': ['_border'], 'underlay': ['_bg']}
            >>> merged = outline.merge_layers({"overlay": ["_custom"]})
            >>> merged.metadata
            {'overlay': ['_custom']}
            ```
        """
        if layers is None:
            return self

        new_metadata = dict(self.metadata)

        # Merge layers: explicit layers override metadata
        if layers.get("underlay"):
            new_metadata["underlay"] = layers["underlay"]
        if layers.get("overlay"):
            new_metadata["overlay"] = layers["overlay"]
        if layers.get("hidden"):
            new_metadata["hidden"] = layers["hidden"]

        return Outline(regions=Regions(dict(self.regions)), metadata=new_metadata)

    def to_dict(self) -> dict[str, Any]:
        """Export to dict in shinymap JSON format.

        Automatically serializes elements:
        - v0.x format: Strings are kept as-is
        - v1.x format: Element objects are serialized to dicts via to_dict()

        Returns:
            Dict with _metadata and region data (v0.x strings or v1.x element dicts)

        Examples:
            ```pycon
            >>> # v0.x format (strings) - empty metadata is omitted
            >>> outline = Outline.from_dict({"region": ["M 0 0"]})
            >>> outline.to_dict()
            {'region': ['M 0 0']}

            >>> # v1.x format (elements)
            >>> from shinymap.svg import Circle
            >>> outline = Outline(regions={"r1": [Circle(cx=100, cy=100, r=50)]}, metadata={})
            >>> outline.to_dict()
            {'r1': [{'type': 'circle', 'cx': 100, 'cy': 100, 'r': 50}]}
            ```
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
                    serialized_elements.append(elem.to_dict())  # type: ignore[arg-type]
            output[region_id] = serialized_elements

        return output

    def to_json(self, output_path: str | PathType) -> None:
        """Write outline to JSON file.

        Args:
            output_path: Path to write JSON file

        Examples:
            ```pycon
            >>> geo = Outline.from_svg("map.svg")  # doctest: +SKIP
            >>> geo.to_json("output.json")  # doctest: +SKIP
            ```
        """
        output_path = PathType(output_path).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def __repr__(self) -> str:
        """Return clean repr showing regions summary and metadata.

        Uses reprlib for concise output suitable for interactive use.
        Shows region count instead of full region data.
        Uses global repr configuration from get_repr_config().

        Examples:
            ```pycon
            >>> geo = Outline.from_svg("map.svg")  # doctest: +SKIP
            >>> geo  # doctest: +SKIP
            Outline(regions={47 regions}, metadata={'viewBox': '0 0 1000 1000'})
            ```
        """
        import reprlib

        from ._repr_config import get_repr_config

        config = get_repr_config()

        r = reprlib.Repr()
        r.maxdict = config.max_metadata_items

        # Create summary for regions (show count + preview of keys)
        region_count = len(self.regions)
        show_threshold = max(3, config.max_regions // 2)
        if region_count <= show_threshold:
            region_keys = list(self.regions.keys())
            regions_repr = f"{{{', '.join(repr(k) for k in region_keys)}}}"
        else:
            preview_count = max(2, show_threshold // 2)
            region_keys = list(self.regions.keys())[:preview_count]
            regions_repr = (
                f"{{{', '.join(repr(k) for k in region_keys)}, ... ({region_count} regions)}}"
            )

        # Use reprlib for metadata
        metadata_repr = r.repr(self.metadata)

        return f"Outline(regions={regions_repr}, metadata={metadata_repr})"
