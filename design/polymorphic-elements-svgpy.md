# Polymorphic Elements Refactor Using svg.py

**Status**: PARTIALLY IMPLEMENTED (v0.2.0)
**Created**: 2025-12-20

> **Note**: Phase 1-2 (Python backend) are complete. Phase 3-4 (TypeScript
> frontend, export_svg) are pending. Currently, JavaScript receives simplified
> path strings via `load_geometry()` as a temporary measure.

**Objective**: Support all SVG element types (circle, rect, polygon, ellipse, line, **text**) in shinymap by leveraging svg.py as a dependency and extending it with mixins for shinymap-specific functionality.

## Background

Current limitation: `geometry.from_svg()` only extracts `<path>` elements, silently ignoring circles, rectangles, text, and other shapes exported by tools like PowerPoint and Illustrator. This violates the "geometry-agnostic" goal.

**User requirement**: "Our primary goal is to make a geometry-agnostic map library."

**Key user need**: Text element support enables **SVG-to-SVG conversion** for annotation layers showing region IDs, making the converter app easier to use.

## Decision: Use svg.py as Foundation

Rather than reimplementing SVG element classes, we will:
1. Add **svg.py** (MIT license, 100% type-safe) as a dependency
2. Extend svg.py element classes with **mixins** for shinymap-specific functionality
3. Keep shinymap focused on interactive mapping, not SVG primitives

### svg.py Architecture (analyzed)

**Element hierarchy**:
```python
@dataclass
class Element:
    """Base class for all SVG elements"""
    element_name: ClassVar[str]
    elements: list[Element] | None = None
    text: str | None = None
    id: str | None = None
    # ... core attributes

    def as_dict(self) -> dict[str, str]:
        """Convert to attribute dict (snake_case → kebab-case)"""

    def as_str(self) -> str:
        """Serialize to SVG string"""

    def __str__(self) -> str:
        return self.as_str()

# Shape elements with mixin composition
@dataclass
class Path(Element, _FigureElement):
    element_name = "path"
    d: list[PathData] | None = None  # NOTE: list[PathData], not string!
    transform: list[Transform] | None = None

@dataclass
class Circle(Element, _FigureElement):
    element_name = "circle"
    cx: Length | Number | None = None
    cy: Length | Number | None = None
    r: Length | Number | None = None

@dataclass
class Rect(Element, _FigureElement):
    element_name = "rect"
    x: Length | Number | None = None
    y: Length | Number | None = None
    width: Length | Number | None = None
    height: Length | Number | None = None

@dataclass
class Text(Element, _TextElement):
    element_name = "text"
    x: Length | Number | None = None
    y: Length | Number | None = None
    # text content via Element.text field, not separate attribute
```

**Key features**:
- **Dataclasses**: Type-safe, immutable-friendly
- **Mixin composition**: `_FigureElement`, `GraphicsElementEvents`, `Color`, `Graphics`, `FillStroke`
- **Automatic snake_case → kebab-case conversion**: `stroke_width` → `stroke-width`
- **Serialization**: `__str__()` returns valid SVG markup
- **No bounds calculation**: svg.py focuses on generation, not analysis

## Shinymap Extension Strategy

### What svg.py Provides

✅ Type-safe element classes (Path, Circle, Rect, Polygon, Ellipse, Line, **Text**)
✅ SVG attribute handling (fill, stroke, transform, etc.)
✅ Serialization to SVG strings
✅ Mixin-based composition model

### What shinymap Needs to Add

❌ **Bounds calculation**: `element.bounds() → (min_x, min_y, max_x, max_y)`
❌ **JSON serialization**: `element.to_dict()` for shinymap JSON format
❌ **JSON deserialization**: `Element.from_dict(data)` to reconstruct elements
❌ **Region semantics**: Treating elements as clickable regions, not just graphics

### Key Design Decisions (User Approved)

#### Decision 1: Transforms (Approved: Option A)
**How to handle transformed bounds?**
- **Option A** ✅: Ignore transforms (bounds in local coordinates)
- **Option B**: Apply transforms (requires matrix math, needs svgpathtools as optional dependency)

**Decision**: Start with Option A. Since svgpathtools is already an optional dependency, we can add Option B later if needed.

#### Decision 2: Path Data Format (Approved: Option B)
**svg.py uses `list[PathData]` for path `d` attribute, not strings. How to reconcile?**
- **Option A**: Convert PathData to string in to_dict() for JSON compatibility
- **Option B** ✅: Store as PathData objects internally, serialize when needed

**Decision**: Option B - keep svg.py's native `list[PathData]` representation internally. This gives us merits:
1. Can leverage svg.py's path manipulation tools
2. Type-safe path operations
3. Easier to implement advanced features (path simplification, transformation)
4. Serialize to string only when outputting JSON or rendering

**Implementation**: PathData objects will be converted to/from strings at JSON boundaries.

#### Decision 3: Element Validation (Approved: Option A)
**Should we validate element attributes (e.g., r > 0 for circles)?**
- **Option A** ✅: No validation (trust svg.py's handling)
- **Option B**: Add validation in mixins

**Decision**: Option A initially. Add validation if issues arise in practice.

#### Decision 4: Text Element Support (Approved: v1.0)
**Include text elements in v1.0 or defer to v1.1?**
- **v1.0** ✅: Include text elements

**Rationale**: Text enables **SVG-to-SVG conversion** for annotation layers showing region IDs, making the converter app much more usable. This is a key workflow improvement.

#### Decision 5: Aesthetics Handling (User Concern Addressed)
**Problem**: SVG/svg.py representation includes aesthetic info (fill, stroke_width) that shinymap doesn't use for rendering. Could mislead users.

**Solution**: Be explicit in documentation that shinymap **preserves but does not use** original SVG aesthetics. Aesthetics are controlled via Python API only.

**Purposes of preserved aesthetics**:
1. **SVG export**: When converting geometry to SVG (annotation layers), preserve original styles
2. **Reference**: Inspect original design intent, but shinymap ignores during rendering

**Documentation strategy**:
- Add prominent note in geometry JSON format docs
- Add warning in `from_svg()` docstring
- Consider adding an `export_svg()` method to make this use case explicit

### Mixin Design

We'll create **shinymap-specific mixins** that extend svg.py elements:

```python
from dataclasses import dataclass
from typing import Protocol, Any
import svg

# Protocol for bounds calculation
class HasBounds(Protocol):
    """Elements that can calculate their bounding box."""
    def bounds(self) -> tuple[float, float, float, float]:
        """Return (min_x, min_y, max_x, max_y)."""
        ...

# Mixin for bounds calculation
@dataclass
class BoundsMixin:
    """Adds bounds() method to SVG elements."""

    def bounds(self) -> tuple[float, float, float, float]:
        """Calculate element bounding box in local coordinates.

        Note: Does NOT apply transforms. Returns bounds in element's local coordinate system.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        # Dispatch based on element type
        if isinstance(self, svg.Circle):
            return self._bounds_circle()
        elif isinstance(self, svg.Rect):
            return self._bounds_rect()
        elif isinstance(self, svg.Path):
            return self._bounds_path()
        elif isinstance(self, svg.Polygon):
            return self._bounds_polygon()
        elif isinstance(self, svg.Ellipse):
            return self._bounds_ellipse()
        elif isinstance(self, svg.Line):
            return self._bounds_line()
        elif isinstance(self, svg.Text):
            return self._bounds_text()
        else:
            raise NotImplementedError(f"Bounds not implemented for {type(self)}")

    def _bounds_circle(self) -> tuple[float, float, float, float]:
        cx = float(self.cx or 0)
        cy = float(self.cy or 0)
        r = float(self.r or 0)
        return (cx - r, cy - r, cx + r, cy + r)

    def _bounds_rect(self) -> tuple[float, float, float, float]:
        x = float(self.x or 0)
        y = float(self.y or 0)
        w = float(self.width or 0)
        h = float(self.height or 0)
        return (x, y, x + w, y + h)

    def _bounds_path(self) -> tuple[float, float, float, float]:
        """Calculate path bounds from PathData objects."""
        from shinymap.geometry._bounds import _parse_svg_path_bounds

        # Convert PathData list to string for bounds calculation
        if self.d is None:
            return (0.0, 0.0, 0.0, 0.0)

        # svg.py's PathData objects have __str__ method
        path_str = " ".join(str(cmd) for cmd in self.d)
        return _parse_svg_path_bounds(path_str)

    def _bounds_polygon(self) -> tuple[float, float, float, float]:
        if not self.points:
            return (0.0, 0.0, 0.0, 0.0)

        # svg.py stores points as list[Number]
        points = self.points
        if len(points) < 2:
            return (0.0, 0.0, 0.0, 0.0)

        x_coords = [float(points[i]) for i in range(0, len(points), 2)]
        y_coords = [float(points[i]) for i in range(1, len(points), 2)]

        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def _bounds_ellipse(self) -> tuple[float, float, float, float]:
        cx = float(self.cx or 0)
        cy = float(self.cy or 0)
        rx = float(self.rx or 0)
        ry = float(self.ry or 0)
        return (cx - rx, cy - ry, cx + rx, cy + ry)

    def _bounds_line(self) -> tuple[float, float, float, float]:
        x1 = float(self.x1 or 0)
        y1 = float(self.y1 or 0)
        x2 = float(self.x2 or 0)
        y2 = float(self.y2 or 0)

        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)

        return (min_x, min_y, max_x, max_y)

    def _bounds_text(self) -> tuple[float, float, float, float]:
        """Approximate text bounds using position only.

        Note: True text bounds require font metrics (font family, size, weight).
        This returns a minimal box at the text position. For accurate bounds,
        use a proper text layout engine.
        """
        x = float(self.x or 0)
        y = float(self.y or 0)

        # Return minimal box (text position with small extent)
        # Real text rendering would compute actual glyph bounds
        return (x, y, x + 1, y + 1)

# Mixin for JSON serialization
@dataclass
class JSONSerializableMixin:
    """Adds to_dict/from_dict for shinymap JSON format.

    Note: JSON format preserves SVG aesthetics (fill, stroke, etc.) but these
    are NOT used by shinymap for rendering. Interactive aesthetics are controlled
    via Python API parameters (default_aesthetic, selection_aesthetic, etc.).

    Preserved aesthetics serve two purposes:
    1. SVG export: When converting back to SVG, original styles are maintained
    2. Reference: Users can inspect original design, but shinymap ignores during render
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert element to dict for JSON serialization.

        Returns dict in format:
        {
            "type": "circle",
            "cx": 100,
            "cy": 100,
            "r": 50,
            "fill": "#ff0000",  # Preserved but not used by shinymap
            ...
        }
        """
        result = {"type": self.element_name}

        # Serialize all non-None attributes
        for key, val in vars(self).items():
            if val is None or key in ("elements", "element_name"):
                continue

            # Handle special cases
            if key == "d" and hasattr(val, "__iter__"):
                # PathData list → string
                result["d"] = " ".join(str(cmd) for cmd in val)
            elif key == "text":
                # Text content
                result["text"] = str(val)
            elif key == "points" and hasattr(val, "__iter__"):
                # Points list → string
                result["points"] = " ".join(str(p) for p in val)
            else:
                result[key] = val

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Element":
        """Reconstruct element from dict.

        Args:
            data: Dict with "type" key and element attributes

        Returns:
            Appropriate element instance (Circle, Rect, Path, etc.)
        """
        elem_type = data.pop("type", None)
        if not elem_type:
            raise ValueError("Missing 'type' field in element dict")

        # Import here to avoid circular dependency
        from ._elements import ELEMENT_TYPE_MAP

        element_cls = ELEMENT_TYPE_MAP.get(elem_type)
        if not element_cls:
            raise ValueError(f"Unknown element type: {elem_type}")

        # Special handling for path data
        if elem_type == "path" and "d" in data:
            # Convert string to PathData (if needed)
            # For now, svg.py can accept string for d parameter
            pass

        # Create instance with remaining attributes
        return element_cls(**data)

# Combined mixin for shinymap elements
class ShinymapElementMixin(BoundsMixin, JSONSerializableMixin):
    """Combined mixin adding bounds() and JSON serialization to svg.py elements."""
    pass
```

### Integration Approach: Subclassing with Mixins (Approved)

Create shinymap subclasses that inherit from both svg.py and mixins:

```python
from dataclasses import dataclass
import svg
from shinymap.geometry._element_mixins import ShinymapElementMixin

@dataclass
class Circle(svg.Circle, ShinymapElementMixin):
    """Shinymap circle with bounds calculation and JSON serialization."""
    pass

@dataclass
class Rect(svg.Rect, ShinymapElementMixin):
    """Shinymap rect with bounds calculation."""
    pass

@dataclass
class Path(svg.Path, ShinymapElementMixin):
    """Shinymap path with bounds calculation."""
    pass

@dataclass
class Polygon(svg.Polygon, ShinymapElementMixin):
    """Shinymap polygon with bounds calculation."""
    pass

@dataclass
class Ellipse(svg.Ellipse, ShinymapElementMixin):
    """Shinymap ellipse with bounds calculation."""
    pass

@dataclass
class Line(svg.Line, ShinymapElementMixin):
    """Shinymap line with bounds calculation."""
    pass

@dataclass
class Text(svg.Text, ShinymapElementMixin):
    """Shinymap text with bounds calculation."""
    pass

# Type union for all supported elements
Element = Circle | Rect | Path | Polygon | Ellipse | Line | Text

# Map type string to class (for from_dict deserialization)
ELEMENT_TYPE_MAP = {
    "circle": Circle,
    "rect": Rect,
    "path": Path,
    "polygon": Polygon,
    "ellipse": Ellipse,
    "line": Line,
    "text": Text,
}

# Usage example
circle = Circle(cx=100, cy=100, r=50, fill="#ff0000")
bounds = circle.bounds()  # From BoundsMixin
json_data = circle.to_dict()  # From JSONSerializableMixin
svg_str = str(circle)  # From svg.Circle
```

**Pros**:
- Leverages svg.py's full feature set
- Type-safe (inherits from svg.py dataclasses)
- Mixin composition is explicit
- No duplicate constructors

## Implementation Plan

### Phase 1: Add svg.py Dependency

**File**: `packages/shinymap/python/pyproject.toml`

```toml
dependencies = [
    "shiny>=1.2.0",
    "svg.py>=1.9.0,<2.0.0",  # NEW: SVG element classes
]
```

**Lines**: 1

### Phase 2: Create Element Mixins

**File**: `packages/shinymap/python/src/shinymap/geometry/_element_mixins.py` (new)

Implementation as shown above with:
- `BoundsMixin` with all shape-specific bounds methods
- `JSONSerializableMixin` with to_dict/from_dict
- `ShinymapElementMixin` combining both

**Lines**: ~200

### Phase 3: Create Shinymap Element Classes

**File**: `packages/shinymap/python/src/shinymap/geometry/_elements.py` (new)

```python
"""Shinymap SVG element classes (extends svg.py with bounds/JSON support)."""

from __future__ import annotations

from dataclasses import dataclass
import svg

from ._element_mixins import ShinymapElementMixin

# Shinymap-enhanced elements
@dataclass
class Circle(svg.Circle, ShinymapElementMixin):
    """Circle element with bounds calculation and JSON serialization.

    Note: Aesthetic attributes (fill, stroke, etc.) are preserved from SVG
    but NOT used by shinymap for rendering. Use Python API parameters
    (default_aesthetic, with_fill_color(), etc.) to control appearance.
    """
    pass

@dataclass
class Rect(svg.Rect, ShinymapElementMixin):
    """Rectangle element with bounds and JSON support."""
    pass

@dataclass
class Path(svg.Path, ShinymapElementMixin):
    """Path element with bounds and JSON support."""
    pass

@dataclass
class Polygon(svg.Polygon, ShinymapElementMixin):
    """Polygon element with bounds and JSON support."""
    pass

@dataclass
class Ellipse(svg.Ellipse, ShinymapElementMixin):
    """Ellipse element with bounds and JSON support."""
    pass

@dataclass
class Line(svg.Line, ShinymapElementMixin):
    """Line element with bounds and JSON support."""
    pass

@dataclass
class Text(svg.Text, ShinymapElementMixin):
    """Text element with bounds and JSON support.

    Note: Bounds calculation for text is approximate (position only).
    True bounds require font metrics which are not available without
    a text layout engine.
    """
    pass

# Type union for all supported elements
Element = Circle | Rect | Path | Polygon | Ellipse | Line | Text

# Map type string to class (for from_dict deserialization)
ELEMENT_TYPE_MAP = {
    "circle": Circle,
    "rect": Rect,
    "path": Path,
    "polygon": Polygon,
    "ellipse": Ellipse,
    "line": Line,
    "text": Text,
}

__all__ = [
    "Circle", "Rect", "Path", "Polygon", "Ellipse", "Line", "Text",
    "Element", "ELEMENT_TYPE_MAP"
]
```

**Lines**: ~80

### Phase 4: Update Geometry Class

**File**: `packages/shinymap/python/src/shinymap/geometry/_geometry.py`

Update to use polymorphic elements instead of strings. Key changes:

```python
from ._elements import Circle, Rect, Path, Polygon, Ellipse, Line, Text, Element

@dataclass
class Geometry:
    """Canonical geometry representation using polymorphic elements."""

    regions: dict[str, list[Element]]  # CHANGED: list[str] → list[Element]
    metadata: dict[str, Any]

    @classmethod
    def from_svg(
        cls,
        svg_path: str | PathType,
        extract_viewbox: bool = True,
    ) -> Geometry:
        """Extract geometry from SVG file (all element types).

        Note: Extracts all SVG aesthetics (fill, stroke, etc.) but these
        are NOT used by shinymap for rendering. Use Python API to control
        interactive appearance. Preserved aesthetics enable SVG export.
        """
        # ... extract all element types, not just paths
```

**Lines**: ~400 (modified)

### Phase 5: Update JSON Format

**Shinymap JSON format v1.0** (polymorphic elements):

```json
{
  "_metadata": {
    "source": "PowerPoint export",
    "license": "MIT",
    "viewBox": "0 0 1500 1500"
  },
  "region_01": [
    {
      "type": "circle",
      "cx": 100,
      "cy": 100,
      "r": 50,
      "fill": "#ff0000",
      "stroke": "#000000",
      "stroke_width": 2
    }
  ],
  "region_02": [
    {
      "type": "rect",
      "x": 200,
      "y": 200,
      "width": 100,
      "height": 80,
      "fill": "#00ff00"
    }
  ],
  "region_03": [
    {
      "type": "path",
      "d": "M 0 0 L 100 0 L 100 100 Z",
      "fill": "#0000ff"
    }
  ],
  "label_01": [
    {
      "type": "text",
      "x": 100,
      "y": 100,
      "text": "Region 1",
      "font_size": 14,
      "fill": "#000000"
    }
  ]
}
```

**Important note on aesthetics**: The JSON format preserves SVG aesthetic properties (fill, stroke, stroke_width, font_size, etc.) from the original SVG file, but **shinymap does not use these values for rendering**. Interactive aesthetics are controlled entirely through Python API parameters (`default_aesthetic`, `selection_aesthetic`, `hover_highlight`, `with_fill_color()`, etc.). The preserved aesthetic values serve two purposes:

1. **SVG export**: When converting geometry back to SVG (e.g., for annotation layers via `export_svg()`), the original styles are preserved
2. **Reference**: Users can inspect the original design intent, but shinymap rendering ignores these values

This design keeps geometry and interactive styling separate - geometry defines "what shapes exist" while Python API controls "how shapes look when rendered".

**Backward compatibility** (v0.x string format still works):

```json
{
  "_metadata": {...},
  "region_01": "M 0 0 L 100 0 Z",  // String → treated as path
  "region_02": ["M 0 0 L 100 0 Z", "M 200 0 L 300 0 Z"]  // List of strings → paths
}
```

### Phase 6: Add SVG Export Function

**File**: `packages/shinymap/python/src/shinymap/geometry/_export.py` (new)

```python
"""Export geometry to SVG format (preserves original aesthetics)."""

from __future__ import annotations

from pathlib import Path as PathType
import svg

def export_svg(
    geometry: dict[str, list[Element]],
    output_path: str | PathType,
    viewbox: str | None = None,
    width: int | str | None = None,
    height: int | str | None = None,
    include_ids: bool = True,
    annotation_layer: bool = False,
) -> None:
    """Export shinymap geometry to SVG file.

    This function preserves original SVG aesthetics (fill, stroke, etc.)
    from the geometry. Useful for creating annotation layers or exporting
    converted geometry.

    Args:
        geometry: Dict mapping region IDs to element lists
        output_path: Path to write SVG file
        viewbox: ViewBox string (default: auto-calculate)
        width: SVG width (default: from viewBox)
        height: SVG height (default: from viewBox)
        include_ids: Add id attributes to elements (default: True)
        annotation_layer: Add text labels showing region IDs (default: False)

    Example:
        >>> from shinymap.geometry import Geometry, export_svg
        >>> geom = Geometry.from_svg("input.svg")
        >>> export_svg(geom.regions, "output.svg", annotation_layer=True)
    """
    from ._bounds import calculate_viewbox

    # Calculate viewBox if not provided
    if viewbox is None:
        # Compute from bounds
        all_bounds = [elem.bounds() for elements in geometry.values() for elem in elements]
        # ... compute viewBox

    # Create SVG container
    elements = []

    for region_id, region_elements in geometry.items():
        for elem in region_elements:
            # Clone element with id attribute if requested
            if include_ids:
                elem_copy = dataclasses.replace(elem, id=region_id)
            else:
                elem_copy = elem

            elements.append(elem_copy)

    # Add annotation layer if requested
    if annotation_layer:
        for region_id, region_elements in geometry.items():
            # Compute centroid for label placement
            bounds = [e.bounds() for e in region_elements]
            # ... create Text element at centroid

    # Create SVG root
    root = svg.SVG(
        width=width,
        height=height,
        viewBox=viewbox,
        elements=elements
    )

    # Write to file
    with open(output_path, "w") as f:
        f.write(str(root))
```

**Lines**: ~100

### Phase 7: Update TypeScript Types

**File**: `packages/shinymap/js/src/types.ts`

(Implementation as shown in original plan - TypeScript discriminated unions for all element types)

**Lines**: ~100

### Phase 8: Update React Components

**File**: `packages/shinymap/js/src/components/InputMap.tsx`

(Implementation as shown in original plan - renderElement() helper with switch on element.type)

**Lines**: ~50 changes

## Testing Strategy

### Unit Tests

**Test bounds calculation** (all shapes including text):

```python
def test_text_bounds():
    text = Text(x=100, y=200, text="Hello")
    min_x, min_y, max_x, max_y = text.bounds()
    assert min_x == 100
    assert min_y == 200
    # Approximate bounds (no font metrics)
```

**Test JSON with PathData objects**:

```python
def test_path_with_pathdata():
    """PathData objects should serialize to string in JSON."""
    from svg._path import M, L, Z

    path = Path(d=[M(0, 0), L(100, 0), L(100, 100), Z()])
    data = path.to_dict()

    assert "d" in data
    assert isinstance(data["d"], str)
    assert "M 0 0" in data["d"]
```

**Test SVG export**:

```python
def test_export_svg_preserves_aesthetics():
    """SVG export should preserve original fill/stroke from geometry."""
    geom = {
        "region_01": [Circle(cx=50, cy=50, r=30, fill="#ff0000")]
    }

    export_svg(geom, tmp_path / "test.svg")

    # Read back and verify fill is preserved
    content = (tmp_path / "test.svg").read_text()
    assert 'fill="#ff0000"' in content
```

### Integration Tests

**Test annotation layer generation**:

```python
def test_annotation_layer():
    """export_svg with annotation_layer=True should add text labels."""
    geom = Geometry.from_svg("input.svg")
    export_svg(geom.regions, "annotated.svg", annotation_layer=True)

    content = Path("annotated.svg").read_text()
    # Verify text elements were added for each region
    assert "<text" in content
```

## Migration Guide

(Same as original plan - v0.x files work automatically)

### New Feature: SVG-to-SVG Conversion with Annotations

**Problem**: Converter app is difficult to use because there's no visual way to see region IDs.

**Solution**: Export SVG with annotation layer showing region IDs:

```python
from shinymap.geometry import Geometry, export_svg

# Load original SVG
geom = Geometry.from_svg("powerpoint_export.svg")

# Export with region ID labels
export_svg(
    geom.regions,
    "annotated.svg",
    annotation_layer=True,  # Add text showing region IDs
    include_ids=True,       # Add id attributes to elements
)
```

This creates an annotated SVG you can open in a browser/editor to see which regions have which IDs, making it easy to create the relabel mapping.

## Rollout Plan

### Phase 1: Foundation ✅ COMPLETED

- [x] Add svg.py dependency to pyproject.toml
- [x] Create `_element_mixins.py` with BoundsMixin and JSONSerializableMixin (280 lines)
- [x] Create `_elements.py` with Circle, Rect, Path, Polygon, Ellipse, Line, **Text** (234 lines)
- [x] Write unit tests for bounds() including text (42 tests in test_element_bounds.py, all passing)
- [x] Write unit tests for to_dict()/from_dict() with PathData handling (37 tests in test_element_json.py, all passing)
  - Note: 2 PathData object tests deferred (marked as skipped)

### Phase 2: Python Backend ✅ COMPLETED

- [x] Update Geometry class to use `dict[str, list[Element]]` type signature
- [x] Update `from_svg()` to extract all element types (including text)
- [x] Update `to_json()` to serialize elements (PathData → string) via `element.to_dict()`
- [x] Update `from_dict()` to auto-detect v0.x vs v1.x format and deserialize appropriately
- [x] Update `viewbox()` to handle both string paths and Element objects
- [x] Update `load_geometry()` - marked as TEMPORARY for Phase 3 frontend refactor
- [x] Update `infer_relabel()` to handle Element dicts with hashable tuple comparison
- [x] Update all geometry tests to work with v1.x Element format (153 tests passing)
- [ ] Create `export_svg()` function in `_export.py` - **NOT STARTED**
- [ ] Write integration tests for export_svg - **NOT STARTED**

### Phase 3: TypeScript Frontend ❌ NOT STARTED

- [ ] Update types.ts with Element union types (including TextElement)
- [ ] Create renderElement() helper in InputMap.tsx
- [ ] Update OutputMap.tsx with renderElement()
- [ ] Write React component tests for mixed elements
- [ ] Remove TEMPORARY markers from `_loader.py` after frontend updated

### Phase 4: Documentation & Examples ❌ NOT STARTED

- [ ] Update SPEC.md with polymorphic elements section
- [ ] Add section on aesthetic preservation vs. rendering
- [ ] Create migration guide in design/migration-v0-to-v1.md
- [ ] Add PowerPoint SVG example to examples/
- [ ] Add annotation layer workflow example
- [ ] Update README.md with new capabilities

## Benefits of This Approach

✅ **Leverages existing library**: svg.py is actively maintained, 100% type-safe, MIT-licensed
✅ **Minimal code**: Mixins add ~300 lines vs. ~1500+ for reimplementation
✅ **Type safety**: Inherits svg.py's type-safe dataclasses
✅ **Extensibility**: Easy to add new element types as svg.py adds them
✅ **Standards compliance**: svg.py follows SVG spec exactly
✅ **Backward compatible**: v0.x JSON files work without changes
✅ **Geometry-agnostic**: Supports PowerPoint, Illustrator, Inkscape exports
✅ **SVG export**: Can round-trip geometry back to SVG with preserved aesthetics
✅ **Annotation workflow**: export_svg() with text labels solves converter UX problem
✅ **PathData support**: Keeps svg.py's rich path representation internally

## Risks and Mitigations

**Risk 1**: svg.py API changes break shinymap
**Mitigation**: Pin to minor version (svg.py>=1.9.0,<2.0.0), test upgrades carefully

**Risk 2**: svg.py doesn't support needed SVG features
**Mitigation**: svg.py is comprehensive (based on SVG spec), but can extend with wrappers if needed

**Risk 3**: Performance overhead from mixin dispatch
**Mitigation**: Minimal - bounds() is O(1) for most shapes, only called during viewBox calculation

**Risk 4**: User confusion about why SVG aesthetics aren't used
**Mitigation**: Prominent documentation explaining preservation vs. rendering, clear examples

## Next Steps

1. ✅ **Review approved** by user (completed)
2. **Prototype Phase 1** (mixins + element classes) to validate approach
3. **Run tests** to ensure no regressions with v0.x format
4. **Implement SVG export** with annotation layer
5. **Iterate** based on feedback

---

**Decisions confirmed**:
- ✅ Use svg.py as dependency with subclassing + mixins approach
- ✅ Support text elements in v1.0 for annotation workflow
- ✅ Keep PathData representation internally (Option B)
- ✅ Ignore transforms in bounds calculation initially (Option A)
- ✅ No validation of element attributes initially (Option A)
- ✅ Support width and height on elements (svg.py already has these)
- ✅ Document that aesthetics are preserved but not used for rendering
- ✅ Add export_svg() to enable SVG round-tripping and annotation layers