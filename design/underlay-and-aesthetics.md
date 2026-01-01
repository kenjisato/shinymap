# Underlay Layer, Non-Scaling Stroke, and Enhanced Aesthetics

**Status**: IMPLEMENTED (v0.2.0)
**Created**: 2025-12-22

> **Note**: This document is kept for historical reference. Underlay layer,
> non-scaling stroke, stroke-dasharray, and aesthetic builders are implemented.

## Table of Contents

1. [Overview](#overview)
2. [Motivation](#motivation)
3. [Current Architecture](#current-architecture)
4. [Design](#design)
5. [Implementation Plan](#implementation-plan)
6. [Testing Strategy](#testing-strategy)
7. [Alternative Approaches](#alternative-approaches)
8. [References](#references)

---

## Overview

This document describes the implementation of three related enhancements to shinymap:

1. **Underlay layer support** - Render annotation layers (grids, backgrounds) below interactive base regions
2. **Non-scaling stroke** - Make stroke-width predictable across different viewBox/viewport sizes using SVG `vector-effect` attribute
3. **Enhanced aesthetics** - Add stroke-dasharray support and type-safe aesthetic builder classes for better developer experience

These features address fundamental usability issues and provide essential tools for creating professional map visualizations.

---

## Motivation

### Problem 1: Missing Underlay Layer and Rigid Aesthetic System

**Current limitation**: Only `overlay_regions` exists, which renders on top of base regions. No way to render grids or reference lines below the base layer.

**Additional issue**: `overlay_aesthetic` parameter (old API) applied the same aesthetic to all overlay regions. This was too rigid because:
- Overlays contain mixed element types (lines, shapes, text) needing different aesthetics
- Different overlay groups (borders vs. labels) need different styling
- Layer membership and aesthetic assignment are conflated

**User pain point**: Geographic maps often need:
- Grid lines below interactive regions (underlay)
- Multiple overlay groups with different aesthetics (borders vs. labels)
- Flexible control over which regions render in which layers

**Use case example**:
```python
# Old approach (too rigid):
output_map(
    geometry=prefectures,
    overlay_regions={"borders": [...], "labels": [...]},
    overlay_aesthetic={"stroke_color": "#000"}  # ← Same for ALL overlays!
)

# New approach (flexible):
output_map(
    geometry=prefectures,
    underlays=["grid"],  # Group names → underlay layer
    overlays=["borders", "labels"],  # Group names → overlay layer
    aes_group={
        "grid": {"stroke_color": "#ddd", "stroke_dasharray": "1,3"},
        "borders": {"stroke_color": "#000", "stroke_width": 2},
        "labels": {"fill_color": "#000"},
    }
)
```

**Why it matters**: Professional cartography requires:
1. Proper layer separation (underlay/base/overlay)
2. Different aesthetics for different groups
3. Separation of concerns (grouping vs. layer assignment vs. styling)

---

### Problem 2: Unpredictable Stroke Width

**Current behavior**: SVG `stroke-width` is specified in viewBox coordinate units, not screen pixels.

**The issue**: Visual stroke width varies based on:
- viewBox dimensions (e.g., `viewBox="0 0 1270 1524"` for Japan map)
- Viewport size (browser window dimensions)
- Aspect ratio differences between viewBox and viewport

**Concrete example**: User sets `stroke_width=3`:
- In viewBox coordinates: 3 units
- On screen: `3 × (viewport_width / viewBox_width)` pixels
- Japan map (1270 wide) in 600px container: `3 × (600/1270) ≈ 1.4px` (too thin!)
- Same map in 1200px container: `3 × (1200/1270) ≈ 2.8px` (closer but still inconsistent)

**User experience**: Trial-and-error to find the right stroke-width value for each map geometry. What works for Japan map fails for US map. Responsive layouts require different values for different screen sizes.

**Solution**: SVG `vector-effect="non-scaling-stroke"` attribute ([MDN docs](https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/vector-effect))
- Production-ready as of 2025 (Chrome issues from 2023 resolved)
- Makes stroke-width always render at specified pixel width
- `stroke_width=3` → 3 screen pixels, regardless of viewBox scaling
- Responsive by default: strokes maintain consistent visual weight

**Why it matters**: Predictable stroke widths are essential for:
- Professional appearance (consistent line weights)
- Accessibility (readable borders for vision-impaired users)
- Responsive design (same visual weight across devices)
- Developer experience (no trial-and-error)

---

### Problem 3: Limited Aesthetic Features

**Current limitations**:
- No `stroke-dasharray` support (can't create dashed/dotted lines)
- All element types (Circle, Line, Text, Path) receive identical aesthetic treatment
- No type-safe builders for IDE autocomplete
- No validation warnings for inappropriate aesthetics (e.g., fill on Line elements)

**Use cases requiring dashed lines**:
- Dashed borders for disputed territories
- Dotted lines for ferry routes or airline paths
- Dash-dot patterns for maritime boundaries
- Interactive line charts (demand/supply curves in economics education)

**Use cases requiring text stroke**:
- Text labels with stroke outlines for low-contrast situations
- White outline on dark backgrounds for legibility
- Interactive text regions (economics education app with clickable labels)

**Developer experience issues**:
- No IDE autocomplete for aesthetic parameters
- Typos in parameter names go undetected until runtime
- Unclear which aesthetics apply to which element types
- Repetitive dictionary construction: `{"stroke_color": "#fff", "stroke_width": 2}`

**Why it matters**: Type-safe builders with IDE support reduce errors, improve discoverability, and make code more maintainable.

---

## Current Architecture

### Rendering Layers (4-Layer Model)

**Current stack (bottom to top)**:
```
Layer 4: Hover overlay (topmost)
         ↑ Duplicate of hovered region with hover aesthetics
         ↑ pointerEvents="none" (non-interactive)

Layer 3: Selection overlay
         ↑ Duplicates of selected regions with selection aesthetics
         ↑ pointerEvents="none" (non-interactive)

Layer 2: Overlay geometry (above base)
         ↑ Annotation paths (dividers, borders, labels)
         ↑ pointerEvents="none" (non-interactive)

Layer 1: Base regions (interactive)
         ↑ All geometry regions with default aesthetics
         ↑ Click handlers attached
         ↑ Hover state tracking
```

**SVG structure**:
```tsx
<svg viewBox={viewBox}>
  {/* Group 1: Base + Overlay (currently inline) */}
  <g>
    {renderBaseRegions()}  {/* Interactive */}
    {renderOverlayRegions()}  {/* Non-interactive, inline */}
  </g>

  {/* Group 2: Selection overlay */}
  <g>{renderSelectedRegions()}</g>

  {/* Group 3: Hover overlay */}
  <g>{renderHoveredRegion()}</g>
</svg>
```

**Issue**: No layer below base regions. Overlay geometry is inline with base (same `<g>` group), not in separate group.

---

### Stroke Width Behavior

**Current implementation flow**:

1. **Python API** (`_ui.py`):
   ```python
   MapBuilder.with_stroke_width(3.0)
   ```
   - Accepts `float` or `dict[str, float]`
   - Passed through MapPayload as `stroke_width: float | dict`
   - `_camel_props()` converts `stroke_width` → `strokeWidth`

2. **JavaScript Reception** (`types.ts`, `OutputMap.tsx`):
   ```typescript
   OutputMapProps.strokeWidth?: number | Record<RegionId, number>
   ```
   - Normalized to per-region dict
   - Resolved into `AestheticStyle`

3. **SVG Rendering** (`renderElement.tsx`):
   ```typescript
   <path strokeWidth={strokeWidth} ... />
   ```
   - Passed directly to SVG element
   - No calculation or scaling applied

**Result**: `strokeWidth` is in viewBox units, visual width varies with viewport size.

---

### Aesthetic System

**States and parameters**:

**Interactive elements** (main geometry):
- `aes_base`: Not selected, not hovered (renamed from `default_aesthetic`)
- `aes_hover`: Hovered state (renamed from `hover_highlight`)
- `aes_select`: Selected state (renamed from `selected_aesthetic`)
- Selected + hovered: Combination (hover renders on top)

**Overlay elements** (non-interactive):
- `aes_group`: Per-group aesthetics (replaces single `overlay_aesthetic`)

**Current parameters** (all aesthetics):
- `fill_color` / `fillColor`
- `fill_opacity` / `fillOpacity`
- `stroke_color` / `strokeColor`
- `stroke_width` / `strokeWidth`

**Missing**: `stroke_dasharray`, element-type validation, type-safe builders

---

## Design

### Architecture: 5-Layer Rendering Model

**Proposed stack (bottom to top)**:
```
Layer 5: Hover overlay (topmost)
         ↑ Duplicate of hovered region

Layer 4: Selection overlay
         ↑ Duplicates of selected regions

Layer 3: Overlay geometry (above base)
         ↑ Annotations (dividers, borders, labels)

Layer 2: Base regions (interactive)
         ↑ Main geometry with click handlers

Layer 1: Underlay geometry (NEW - below base)
         ↑ Background elements (grids, graticules)
         ↑ pointerEvents="none" (non-interactive)
```

**SVG structure**:
```tsx
<svg viewBox={viewBox}>
  {/* Group 1: Underlay (NEW) */}
  <g>
    {renderUnderlayRegions()}  {/* Non-interactive background */}
  </g>

  {/* Group 2: Base regions */}
  <g>
    {renderBaseRegions()}  {/* Interactive */}
  </g>

  {/* Group 3: Overlay regions (NEW - separate group) */}
  <g>
    {renderOverlayRegions()}  {/* Non-interactive annotations */}
  </g>

  {/* Group 4: Selection overlay */}
  <g>{renderSelectedRegions()}</g>

  {/* Group 5: Hover overlay */}
  <g>{renderHoveredRegion()}</g>
</svg>
```

**Benefits**:
- Underlay renders below all other layers
- Base and overlay in separate groups (clean layer separation)
- Symmetric underlay/overlay structure
- No z-index hacks needed (DOM order controls stacking)
- Clean separation of concerns

---

### API Design

#### Group-Based Layer System

**Key concepts**:
1. JSON stores groups (tags) as metadata
2. Python API specifies layer membership and aesthetics separately
3. **Layer membership is exclusive** (region can only be in one layer)
4. **Group aesthetics can overlap** (region can be in multiple aesthetic groups)

**JSON metadata** (geometry file):
```json
{
  "_metadata": {
    "viewBox": "0 0 1270 1524",
    "groups": {
      "grid": ["grid_lat", "grid_lon"],
      "borders": ["prefecture_borders"],
      "labels": ["tokyo_label", "osaka_label"],
      "coastal": ["tokyo", "osaka", "fukuoka"],
      "mountain": ["nagano", "yamanashi"]
    }
  },
  "tokyo": [...],
  "osaka": [...],
  "grid_lat": [...],
  "grid_lon": [...],
  "prefecture_borders": [...],
  "tokyo_label": [...],
  "osaka_label": [...],
  "nagano": [...],
  "yamanashi": [...],
  "fukuoka": [...]
}
```

**Note**: Groups are optional metadata. Each region ID can be used as an implicit singleton group.

---

#### Python API

**`input_map()` signature**:
```python
def input_map(
    id: str,
    geometry: GeometryMap,
    mode: InputMapMode = "single",
    # ... existing parameters ...

    # BREAKING CHANGE: Remove overlay_regions, overlay_aesthetic
    # NEW: Group-based layer specification (EXCLUSIVE)
    underlays: list[str] | None = None,  # Group names → underlay layer (exclusive)
    overlays: list[str] | None = None,  # Group names → overlay layer (exclusive)
    hidden: list[str] | None = None,  # Group names → hide completely (exclusive)

    # NEW: Group aesthetics (NON-EXCLUSIVE, can overlap)
    aes_group: dict[str, dict[str, Any] | BaseAesthetic] | None = None,

    # ... rest
) -> Tag:
```

**Layer assignment rules**:
- **Exclusive**: A region can only be in ONE layer (underlay/base/overlay/hidden)
- If region appears in multiple layer lists, use **priority order**: `hidden > overlays > underlays > base`
- Base layer = all regions not in underlays/overlays/hidden

**Group aesthetic rules**:
- **Non-exclusive**: A region can be in multiple aesthetic groups
- If region is in multiple groups, **merge aesthetics** using MISSING sentinel
- Attributes set to MISSING don't override (other attributes do override)
- Final priority: `region-specific > group aesthetics > default_aesthetic`

**`output_map()` signature**:
```python
def output_map(
    id: str,
    *,
    geometry: GeometryMap | None = None,
    # ... existing parameters ...

    # BREAKING CHANGE: Remove overlay_regions, overlay_aesthetic
    # NEW: Group-based layer specification
    underlays: list[str] | None = None,
    overlays: list[str] | None = None,
    hidden: list[str] | None = None,
    aes_group: dict[str, dict[str, Any] | BaseAesthetic] | None = None,

    # ... rest
) -> Tag:
```

**`MapBuilder` fluent API**:
```python
class MapBuilder:
    def with_layers(
        self,
        underlays: list[str] | None = None,
        overlays: list[str] | None = None,
        hidden: list[str] | None = None,
    ) -> MapBuilder:
        """Specify which groups render in which layers (exclusive)."""
        self._underlays = underlays
        self._overlays = overlays
        self._hidden = hidden
        return self

    def with_group_aesthetics(
        self,
        aes_group: dict[str, dict[str, Any] | BaseAesthetic],
    ) -> MapBuilder:
        """Set aesthetics for groups (non-exclusive, can overlap)."""
        self._aes_group = aes_group
        return self
```

**`MapPayload` dataclass**:
```python
@dataclass
class MapPayload:
    # ... existing fields ...
    # BREAKING CHANGE: Remove overlay_regions, overlay_aesthetic
    underlays: list[str] | None = None
    overlays: list[str] | None = None
    hidden: list[str] | None = None
    aes_group: dict[str, dict[str, Any]] | None = None
```

**Usage example 1: Layer assignment**:
```python
from shinymap import output_map, aes

# Group-based layers with IDE-friendly aesthetic builders
output_map(
    "map",
    geometry=prefectures,
    underlays=["grid"],  # Grid group → underlay layer (EXCLUSIVE)
    overlays=["borders", "labels"],  # Border/label groups → overlay layer (EXCLUSIVE)
    aes_group={
        "grid": aes.Line(stroke_color="#ddd", stroke_width=0.5, stroke_dasharray=aes.line.dashed),
        "borders": aes.Line(stroke_color="#000", stroke_width=2),
        "labels": aes.Text(fill_color="#000"),
    }
)
```

**Usage example 2: Overlapping aesthetic groups**:
```python
from shinymap import output_map, aes

# Regions can be in multiple aesthetic groups (non-exclusive)
output_map(
    "map",
    geometry=prefectures,
    aes_group={
        "coastal": aes.Shape(fill_color="#3b82f6"),  # Tokyo, Osaka, Fukuoka
        "mountain": aes.Shape(fill_color="#10b981"),  # Nagano, Yamanashi
        "highlight": aes.Shape(stroke_color="#000", stroke_width=2),  # Could include Tokyo
    }
)
# If Tokyo is in both "coastal" and "highlight" groups:
# - fill_color from "coastal" (#3b82f6)
# - stroke_color and stroke_width from "highlight"
# - Merged using MISSING sentinel (later group wins for specified params)
```

**Usage example 3: Implicit singleton groups**:
```python
from shinymap import output_map, aes

# Use region IDs directly as implicit groups
output_map(
    "map",
    geometry=geo,
    overlays=["tokyo", "osaka"],  # Region IDs as implicit groups (layer assignment)
    aes_group={
        "tokyo": aes.Shape(fill_color="#ef4444"),
        "osaka": aes.Shape(fill_color="#3b82f6"),
    }
)
```

**Aesthetic merging with MISSING sentinel**:
```python
from shinymap import aes

# Define base aesthetic for coastal regions
coastal_aes = aes.Shape(fill_color="#3b82f6", fill_opacity=0.7)

# Override only stroke for highlighted regions
highlight_aes = aes.Shape(stroke_color="#000", stroke_width=2)
# fill_color and fill_opacity are MISSING, so they won't override coastal_aes

# Result for region in both groups:
# {fill_color: "#3b82f6", fill_opacity: 0.7, stroke_color: "#000", stroke_width: 2}
```

**API Design Benefits**:
- **IDE-friendly**: `aes.` triggers autocomplete showing `Line()`, `Shape()`, `Text()`
- **Consistent prefix**: All aesthetic builders share `aes.` namespace
- **Expressive**: `aes.line.dashed` clearly indicates what the constant represents
- **Clean imports**: `from shinymap import aes`

---

#### TypeScript API

**Type definitions** (`types.ts`):
```typescript
// Geometry metadata with groups
export type GeometryMetadata = {
  viewBox?: string;
  groups?: Record<string, RegionId[]>;  // NEW: group name → region IDs
  // ... existing fields
};

export type InputMapProps = {
  // ... existing props ...

  // BREAKING CHANGE: Remove overlayGeometry, overlayAesthetic
  // NEW: Group-based layer specification
  underlays?: string[];  // Group names for underlay layer
  overlays?: string[];  // Group names for overlay layer
  hidden?: string[];  // Group names to hide
  aesGroup?: Record<string, AestheticStyle>;  // Group name → aesthetic
};

export type OutputMapProps = {
  // ... existing props ...

  // BREAKING CHANGE: Remove overlayGeometry, overlayAesthetic
  // NEW: Group-based layer specification
  underlays?: string[];
  overlays?: string[];
  hidden?: string[];
  aesGroup?: Record<string, AestheticStyle>;
};

export type AestheticStyle = {
  fillColor?: string;
  fillOpacity?: number;
  strokeColor?: string;
  strokeWidth?: number;
  strokeDasharray?: string;  // NEW
  nonScalingStroke?: boolean;  // NEW
};
```

---

### Aesthetic Enhancements

#### 1. stroke-dasharray Support

**Python**: Already handled by `_camel_props()` conversion (snake_case → camelCase)
```python
input_map(
    "map",
    geometry,
    aes_base={"stroke_dasharray": "5,5"}  # Dashed border
)
```

**TypeScript**: Extract and pass to `renderElement()`:
```typescript
const strokeDasharray = aesthetic.strokeDasharray;
renderElement({ strokeDasharray, ... });
```

**SVG**: Pass to element as attribute:
```tsx
<path strokeDasharray={strokeDasharray} ... />
```

**Common patterns**:
- `"5,5"` - Dashed
- `"1,3"` - Dotted
- `"5,5,1,5"` - Dash-dot
- `null` - Solid (default)

---

#### 2. Non-Scaling Stroke

**Implementation**: Add `vectorEffect` attribute to SVG elements

**TypeScript** (`renderElement.tsx`):
```typescript
export function renderElement(props: RenderElementProps) {
  const { nonScalingStroke = true, ... } = props;

  const vectorEffect = nonScalingStroke !== false
    ? "non-scaling-stroke"
    : undefined;

  const commonProps = {
    ...elementProps,
    vectorEffect,  // NEW
    // ... rest
  };

  // Apply to all elements
  return <path {...commonProps} />;
}
```

**Default behavior**: `nonScalingStroke=true` (predictable widths)
**Opt-out**: `nonScalingStroke=false` (viewBox-relative widths)

**Usage**:
```python
# Default: non-scaling stroke
input_map("map", geometry, aes_base={"stroke_width": 3})
# → Always 3px on screen

# Opt-out: scaling stroke
input_map("map", geometry, aes_base={
    "stroke_width": 3,
    "non_scaling_stroke": False
})
# → 3 viewBox units (varies with zoom)
```

---

#### 3. Type-Safe Aesthetic Builders

**Design principles**:
1. **MISSING sentinel**: Distinguish unset from `None` (transparent)
2. **Base class**: Share `to_dict()` and `update()` logic
3. **Direct API acceptance**: Pass instances without `.to_dict()`
4. **Immutable updates**: `.update()` returns new instance

**Implementation** (`_aesthetics.py`):
```python
from dataclasses import dataclass, replace
from typing import Any


# Sentinel for missing/unset values
class _Missing:
    """Sentinel for missing aesthetic values.

    None is a valid aesthetic value (e.g., fill_color=None for transparent).
    MISSING indicates the parameter was not specified.
    """
    def __repr__(self) -> str:
        return "MISSING"

MISSING = _Missing()


@dataclass
class BaseAesthetic:
    """Base class for all aesthetic types."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API parameters, filtering out MISSING values."""
        return {
            k: v for k, v in self.__dict__.items()
            if not isinstance(v, _Missing)
        }

    def update(self, **kwargs: Any) -> "BaseAesthetic":
        """Return new aesthetic with updated parameters.

        Uses dataclasses.replace() for immutable update pattern.

        Example:
            aes = ShapeAesthetic(stroke_width=1, fill_color="#fff")
            aes_updated = aes.update(stroke_width=2)  # fill_color unchanged
        """
        return replace(self, **kwargs)


@dataclass
class ShapeAesthetic(BaseAesthetic):
    """Aesthetic for shape elements (Circle, Rect, Path, Polygon, Ellipse).

    Supports all aesthetic properties.
    """
    fill_color: str | None | _Missing = MISSING
    fill_opacity: float | None | _Missing = MISSING
    stroke_color: str | None | _Missing = MISSING
    stroke_width: float | None | _Missing = MISSING
    stroke_dasharray: str | None | _Missing = MISSING
    non_scaling_stroke: bool | _Missing = MISSING


@dataclass
class LineAesthetic(BaseAesthetic):
    """Aesthetic for line elements.

    Only supports stroke properties (no fill area).
    """
    stroke_color: str | None | _Missing = MISSING
    stroke_width: float | None | _Missing = MISSING
    stroke_dasharray: str | None | _Missing = MISSING
    non_scaling_stroke: bool | _Missing = MISSING


@dataclass
class TextAesthetic(BaseAesthetic):
    """Aesthetic for text elements.

    Supports fill for text color, stroke for outline.
    """
    fill_color: str | None | _Missing = MISSING
    fill_opacity: float | None | _Missing = MISSING
    stroke_color: str | None | _Missing = MISSING  # For outline
    stroke_width: float | None | _Missing = MISSING
    stroke_dasharray: str | None | _Missing = MISSING
    non_scaling_stroke: bool | _Missing = MISSING


# Convenience constants for common dash patterns
SOLID = None
DASHED = "5,5"
DOTTED = "1,3"
DASH_DOT = "5,5,1,5"
```

**Direct API acceptance** (`_ui.py`):
```python
from typing import Any
from ._aesthetics import BaseAesthetic


def _normalize_aesthetic(
    aes: dict[str, Any] | BaseAesthetic | None
) -> dict[str, Any] | None:
    """Convert BaseAesthetic to dict, or pass through dict/None."""
    if aes is None:
        return None
    if isinstance(aes, BaseAesthetic):
        return aes.to_dict()
    return aes


# Update input_map() signature
def input_map(
    id: str,
    geometry: GeometryMap,
    # ...
    aes_base: dict[str, Any] | BaseAesthetic | None = None,
    aes_hover: dict[str, Any] | BaseAesthetic | None = None,
    aes_select: dict[str, Any] | BaseAesthetic | None = None,
    aes_group: dict[str, dict[str, Any] | BaseAesthetic] | None = None,
    # ...
):
    # Normalize before passing to JavaScript
    aes_base = _normalize_aesthetic(aes_base)
    aes_hover = _normalize_aesthetic(aes_hover)
    aes_select = _normalize_aesthetic(aes_select)
    aes_group = _normalize_group_aesthetics(aes_group)
    # ... etc
```

**Usage examples**:
```python
from shinymap import input_map, aes

# Type-safe with IDE autocomplete
input_map(
    "region",
    geometry,
    aes_base=aes.Shape(
        fill_color="#e5e7eb",
        stroke_color="#d1d5db",
        stroke_width=1
    ),  # No .to_dict() needed!
    aes_hover=aes.Shape(
        stroke_color="#374151",
        stroke_width=2,
        stroke_dasharray=aes.line.dashed  # IDE suggests: solid, dashed, dotted, dash_dot
    ),
)

# Partial updates
base_aes = aes.Shape(stroke_width=1, fill_color="#fff")
hover_aes = base_aes.update(stroke_width=2)  # Only changes stroke_width

# MISSING vs None
aes.Shape(fill_color=None).to_dict()
# → {"fill_color": None}  (transparent fill)

from shinymap._aesthetics import MISSING
aes.Shape(fill_color=MISSING).to_dict()
# → {}  (parameter not specified)

aes.Shape().to_dict()
# → {}  (all parameters unset)
```

**Benefits**:
1. **IDE autocomplete**: Only shows valid parameters for each element type
2. **Type safety**: Catches typos at development time (not runtime)
3. **Self-documenting**: Clear which aesthetics apply to which elements
4. **Convenience constants**: Pre-defined dash patterns
5. **Immutable updates**: Functional programming pattern
6. **Distinction**: MISSING vs None for transparent fills

---

## Implementation Plan

See [plan file](/Users/kenjisato/.claude/plans/enchanted-hugging-fox.md) for detailed phase-by-phase checklist.

**Summary**:

1. **Phase 1**: Non-scaling stroke (TypeScript + Python)
2. **Phase 2**: Underlay layer (Python + TypeScript + React)
3. **Phase 3**: stroke-dasharray (TypeScript + Python)
4. **Phase 4**: Aesthetic builders (Python)
5. **Phase 5**: Validation (optional)
6. **Phase 6**: Documentation

**Order rationale**:
- Non-scaling stroke first: Simple, high impact, foundational
- Underlay second: New feature, moderate complexity
- stroke-dasharray third: Simple addition, builds on Phase 1
- Builders fourth: High value, independent of other phases
- Validation fifth: Optional enhancement
- Documentation last: After all implementation complete

---

## Testing Strategy

### Unit Tests (Python)

**Aesthetic builders** (`test_aesthetics.py`):
- `ShapeAesthetic().to_dict()` returns `{}`
- `ShapeAesthetic(fill_color="#fff").to_dict()` returns `{"fill_color": "#fff"}`
- `ShapeAesthetic(fill_color=None).to_dict()` includes `None` (not filtered)
- `ShapeAesthetic(fill_color=MISSING).to_dict()` excludes MISSING (filtered)
- `.update()` method: changes only specified params, original unchanged
- Convenience constants: `DASHED == "5,5"`, etc.

**Validation helpers** (`test_validation.py`):
- `_collect_element_types()` with mixed element types
- Validation warns for Line + fill
- Validation does NOT warn for Text + stroke
- Validation does NOT warn for Shape + any aesthetics

### Integration Tests (Python)

- Full `input_map()` with underlay
- Full `output_map()` with underlay
- Pass `ShapeAesthetic(...)` directly to `input_map()`
- Pass `ShapeAesthetic(...).to_dict()` to `input_map()`
- Validation warnings in real-world usage

### Component Tests (TypeScript)

- `renderElement()` with `vectorEffect` attribute
- `renderElement()` with `strokeDasharray` attribute
- `InputMap` with underlay rendering (below base)
- `OutputMap` with underlay rendering (below base)

### Manual Testing

- Build: `make build` succeeds
- All Python tests pass: `make test`
- Example apps render correctly:
  - Underlay appears below base
  - Non-scaling stroke produces consistent widths
  - Dashed lines render correctly
- IDE autocomplete works for aesthetic builders
- Browser SVG inspection confirms attributes present
- Responsive behavior: stroke widths consistent across viewport sizes

### Visual Testing

- Japan map with `stroke_width=3`:
  - Default: 3px on screen regardless of viewport size
  - `non_scaling_stroke=False`: varies with zoom
- Grid underlay with dashed lines:
  - Renders below prefecture boundaries
  - Non-interactive (clicks pass through)
  - Dashed pattern visible

---

## Alternative Approaches

### Underlay Layer

**Alternative 1: Reuse `overlay_regions` with z-index**
- **Rejected**: SVG doesn't support CSS z-index reliably
- DOM order is the only way to control layer stacking in SVG

**Alternative 2: Support multiple overlay/underlay layers**
```python
underlays=[
    {"geometry": GRID, "aesthetic": GRID_STYLE},
    {"geometry": MARKERS, "aesthetic": MARKER_STYLE},
]
```
- **Deferred**: Single underlay layer is sufficient for MVP
- Can extend to `list[dict]` in future if needed
- Preserves API symmetry with single overlay

**Alternative 3: Combined `annotation_layers` parameter**
```python
annotation_layers=[
    {"geometry": GRID, "aesthetic": GRID_STYLE, "z_order": -1},  # Below
    {"geometry": DIVIDERS, "aesthetic": DIV_STYLE, "z_order": 1},  # Above
]
```
- **Rejected**: Less intuitive than separate underlay/overlay
- z_order abstraction adds complexity
- Symmetric underlay/overlay is more predictable

---

### Non-Scaling Stroke

**Alternative 1: Calculate scaled strokeWidth in JavaScript**
```typescript
const scaledWidth = strokeWidth * (viewportWidth / viewBoxWidth);
```
- **Rejected**: Complex calculation, aspect ratio issues
- Doesn't handle zoom/pan correctly
- `vector-effect` is simpler and browser-native

**Alternative 2: Document that stroke-width is in SVG units**
- **Rejected**: Poor user experience (trial-and-error)
- Responsive design requires different values per viewport
- `vector-effect` makes it predictable out-of-the-box

**Alternative 3: Make `vector-effect` opt-in (default off)**
- **Rejected**: Default behavior should be predictable
- Users expect `stroke_width=3` to mean 3 pixels, not 3 viewBox units
- Opt-in would perpetuate current problem

**Alternative 4: Separate `stroke_width_px` parameter**
```python
default_aesthetic={
    "stroke_width": 3,  # viewBox units
    "stroke_width_px": 3,  # screen pixels
}
```
- **Rejected**: Confusing to have two width parameters
- `non_scaling_stroke` boolean is clearer
- Less API surface area

---

### Aesthetic Builders

**Alternative 1: Use TypedDict instead of dataclasses**
```python
class ShapeAestheticDict(TypedDict, total=False):
    fill_color: str
    stroke_width: float
    # ...

def make_shape_aesthetic(**kwargs) -> ShapeAestheticDict:
    return kwargs
```
- **Rejected**: No IDE autocomplete for dict construction
- No `.update()` method for partial updates
- Dataclasses provide better developer experience

**Alternative 2: Runtime validation only (no type-safe builders)**
```python
def _validate_aesthetic(aes: dict) -> None:
    if "fill_color" in aes and not isinstance(aes["fill_color"], str):
        raise TypeError(...)
```
- **Rejected**: User prefers IDE support over runtime-only validation
- Builders catch errors at development time (before running code)
- Type hints enable static analysis

**Alternative 3: Separate builder functions**
```python
def shape_aesthetic(*, fill_color=None, stroke_width=None, ...) -> dict:
    return {k: v for k, v in locals().items() if v is not None}
```
- **Rejected**: No `.update()` method
- No distinction between MISSING and None
- Dataclasses provide more features (repr, equality, etc.)

**Alternative 4: Use `None` to mean "unset"**
```python
@dataclass
class ShapeAesthetic:
    fill_color: str | None = None

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}
```
- **Rejected**: Can't distinguish unset from transparent
- `fill_color=None` should mean transparent fill, not "don't set fill_color"
- MISSING sentinel is more explicit

---

## References

### External Documentation

- [SVG vector-effect - MDN](https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/vector-effect)
- [Scaling SVGs without scaling strokes (2025)](https://wildfirestudios.ca/blog/scaling-svgs-without-scaling-their-strokes-2025-edition)
- [SVG stroke-dasharray - MDN](https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/stroke-dasharray)
- [Python dataclasses.replace](https://docs.python.org/3/library/dataclasses.html#dataclasses.replace)

### Internal Documentation

- [SPEC.md](../SPEC.md) - Current overlay layer documentation
- [design/update_map_implementation.md](./update_map_implementation.md) - Update pattern reference
- [design/polymorphic-elements-svgpy.md](./polymorphic-elements-svgpy.md) - Element type system

### Browser Support

**vector-effect="non-scaling-stroke"**:
- Chrome: ✅ Supported (2025)
- Firefox: ✅ Supported
- Safari: ✅ Supported
- Edge: ✅ Supported
- IE11: ❌ Not supported (acceptable - IE11 is EOL)

**stroke-dasharray**:
- Universal SVG support (all modern browsers)

---

## Appendix: Usage Examples

### Example 1: Geographic Map with Grid

```python
from shinymap import output_map, aes
from shinymap.geometry import Geometry

# Load main geometry and grid
japan = Geometry.from_json("japan_prefectures.json")
grid = Geometry.from_json("lat_lon_grid.json")

output_map(
    "japan_map",
    geometry=japan.main_regions(),
    tooltips=prefecture_names,
    fills=population_colors,
    underlays=["grid"],
    aes_group={
        "grid": aes.Shape(
            stroke_color="#e0e0e0",
            stroke_width=0.5,
            stroke_dasharray=aes.line.dotted,
            fill_color="none"
        ),
    }
)
```

### Example 2: Interactive Economics Diagram

```python
from shinymap import input_map, aes

# Supply/demand curves as interactive lines
input_map(
    "curves",
    geometry={
        "supply": supply_line,
        "demand": demand_line,
        "supply_label": supply_text,
        "demand_label": demand_text,
    },
    mode="multiple",
    aes_base=aes.Line(
        stroke_width=2,
        non_scaling_stroke=True  # Consistent width across zoom
    ),
    aes_hover=aes.Line(
        stroke_width=3,
        stroke_dasharray=linestyle.DASHED
    ),
    overlays=["supply_label", "demand_label"],
    aes_group={
        "labels": aes.Text(
            fill_color="#000",
            stroke_color="#fff",  # White outline for legibility
            stroke_width=0.5
        ),
    }
)
```

### Example 3: Partial Aesthetic Updates

```python
from shinymap import input_map, aes

# Define base theme
base_theme = aes.Shape(
    fill_color="#e5e7eb",
    stroke_color="#9ca3af",
    stroke_width=1,
    non_scaling_stroke=True
)

# Create variants
hover_theme = base_theme.update(
    stroke_color="#374151",
    stroke_width=2
)

selected_theme = base_theme.update(
    fill_color="#3b82f6",
    fill_opacity=0.5
)

input_map(
    "map",
    geometry,
    aes_base=base_theme,
    aes_hover=hover_theme,
    aes_select=selected_theme,
)
```

---

**End of Design Document**

*This document will be updated as implementation progresses.*
