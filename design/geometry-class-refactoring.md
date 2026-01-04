# Geometry Class Refactoring

**Status**: IMPLEMENTED (v0.2.0)

> **Note**: This document is kept for historical reference. The Outline class,
> Map() function, and OOP geometry API are implemented.
>
> **API Changes since v0.2.0**:
> - Class renamed from `Geometry` to `Outline`
> - `active_ids` parameter removed; selection derived from `value > 0`
> - `geometry` parameter renamed to `outline` (Python) / `regions` (TypeScript)
> - See [static-map-and-aes-dump.md](static-map-and-aes-dump.md) for migration details

## Problem Statement

Current geometry handling has issues:

1. **Repetitive dict extraction**: Code repeatedly extracts regions, viewBox, overlays from dicts
2. **Inconsistent viewBox types**: String format makes zoom/pan manipulation difficult
3. **Mixed formats**: Intermediate (list-based) vs final (string-based) paths cause confusion
4. **No type safety**: Plain dicts provide no validation

## Solution: Commit to OOP-First Design

### Design Philosophy

**Make OOP the only user-facing interface**:

```python
# Clean, simple, ONLY way
geo = Geometry.from_dict(data)
Map(geo)
input_map("id", geo, mode="multiple")
output_map("id", geo)

# With zoom override
Map(geo, view_box=(10, 10, 80, 80))
```

**No dict-based alternatives** for user-facing functions. `MapBuilder` remains internal for fluent API.

### Architecture

```
User-facing (OOP only):
  Map(geometry: Geometry) -> MapBuilder
  input_map(id, geometry: Geometry) -> Tag
  output_map(id, geometry: Geometry | None = None) -> Tag

Internal (fluent API):
  MapBuilder (renamed fields: regions, view_box tuple, overlay_regions)
    .with_fills()
    .with_counts()
    etc.
```

## Python API Design

### 1. `Geometry` Class (Already Implemented ✅)

```python
@dataclass
class Geometry:
    """Canonical geometry representation.

    Attributes:
        regions: All regions INCLUDING overlay regions
        metadata: Dict with viewBox, overlays, source, license, etc.
    """
    regions: dict[str, list[str]]
    metadata: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Geometry": ...

    def viewbox(self, padding: float = 0.02) -> tuple[float, float, float, float]: ...

    def overlays(self) -> list[str]:
        return self.metadata.get("overlays", [])
```

### 2. `MapBuilder` - Internal Fluent API

```python
class MapBuilder:
    """Internal builder for map payloads.

    Users create this via Map() function, not directly.

    Example:
        Map(geo).with_fills(colors).with_counts(counts)
    """

    def __init__(
        self,
        *,
        regions: GeometryMap,
        view_box: tuple[float, float, float, float],
        overlay_regions: GeometryMap | None = None,
        overlay_aesthetic: Mapping[str, Any] | None = None,
        tooltips: TooltipMap = None,
    ):
        """Internal constructor - use Map() instead.

        Args:
            regions: Dict of main regions {regionId: [path1, ...]}
            view_box: ViewBox as tuple (x, y, width, height)
            overlay_regions: Optional overlay dict
            overlay_aesthetic: Optional overlay styling
            tooltips: Optional tooltips
        """
        self._regions = regions
        self._view_box = view_box  # Always tuple
        self._overlay_regions = overlay_regions
        self._overlay_aesthetic = overlay_aesthetic or {}
        self._tooltips = tooltips

        # Fluent API fields
        self._fill_color: str | Mapping[str, str] | None = None
        self._stroke_width: float | Mapping[str, float] | None = None
        self._stroke_color: str | Mapping[str, str] | None = None
        self._fill_opacity: float | Mapping[str, float] | None = None
        self._counts: CountMap = None
        self._active_ids: Selection = None
        self._default_aesthetic: Mapping[str, Any] | None = None

    def with_tooltips(self, tooltips: TooltipMap) -> "MapBuilder":
        """Set region tooltips."""
        self._tooltips = tooltips
        return self

    def with_fills(self, fill_color: str | Mapping[str, str]) -> "MapBuilder":
        """Set fill colors."""
        # Update to use self._regions instead of self._geometry
        if fill_color is None:
            return self

        # Normalize to dict (only if regions is available)
        if self._regions is not None:
            normalized = _normalize_fills(fill_color, self._regions)
        else:
            normalized = fill_color if isinstance(fill_color, dict) else None

        # Merge with existing
        if self._fill_color is None:
            self._fill_color = normalized if normalized else fill_color
        else:
            if self._regions is not None:
                existing_normalized = _normalize_fills(self._fill_color, self._regions)
                if existing_normalized and normalized:
                    self._fill_color = {**existing_normalized, **normalized}
                elif normalized:
                    self._fill_color = normalized
            else:
                self._fill_color = fill_color

        return self

    def with_counts(self, counts: CountMap) -> "MapBuilder":
        """Set count badges."""
        self._counts = counts
        return self

    def with_active(self, active_ids: Selection) -> "MapBuilder":
        """Set active region IDs."""
        self._active_ids = active_ids
        return self

    # ... other with_* methods (with_stroke_width, with_stroke_color, etc.)

    def build(self) -> MapPayload:
        """Build MapPayload - converts tuple viewBox to string for React."""
        # Convert tuple viewBox to string for serialization
        view_box_str = f"{self._view_box[0]} {self._view_box[1]} {self._view_box[2]} {self._view_box[3]}"

        return MapPayload(
            geometry=self._regions,  # Payload uses "geometry" key
            tooltips=self._tooltips,
            fill_color=self._fill_color,
            fill_opacity=self._fill_opacity,
            stroke_color=self._stroke_color,
            stroke_width=self._stroke_width,
            counts=self._counts,
            active_ids=self._active_ids,
            view_box=view_box_str,  # String for React (temporary)
            default_aesthetic=self._default_aesthetic,
            overlay_geometry=self._overlay_regions,  # Payload uses "overlay_geometry" key
            overlay_aesthetic=self._overlay_aesthetic,
        )

    def as_json(self) -> Mapping[str, Any]:
        """Convert to JSON dict."""
        return self.build().as_json()
```

### 3. `Map()` - User-Facing OOP Function

```python
def Map(
    geometry: Geometry,
    *,
    view_box: tuple[float, float, float, float] | None = None,
    tooltips: dict[str, str] | None = None,
    fill_color: dict[str, str] | str | None = None,
    counts: dict[str, int] | None = None,
    active: list[str] | None = None,
) -> MapBuilder:
    """Create map from Geometry object.

    Args:
        geometry: Geometry object with regions, viewBox, metadata
        view_box: Override viewBox tuple (for zoom/pan). If None, uses geometry.viewbox()
        tooltips: Region tooltips
        fill_color: Fill colors (string for all, dict for per-region)
        counts: Count badges per region
        active: Active region IDs

    Example:
        # Simple usage
        geo = Geometry.from_dict(data)
        Map(geo)

        # With zoom override
        Map(geo, view_box=(10, 10, 80, 80))

        # With inline styling
        Map(geo, fill_color=colors, counts=counts)

        # With fluent styling
        Map(geo).with_fills(colors).with_counts(counts)

    Returns:
        MapBuilder instance for method chaining
    """
    # Extract overlays from metadata
    overlay_ids = geometry.overlays()
    overlay_regions = {k: v for k, v in geometry.regions.items() if k in overlay_ids}
    main_regions = {k: v for k, v in geometry.regions.items() if k not in overlay_ids}

    # Create MapBuilder with extracted data
    builder = MapBuilder(
        regions=main_regions,
        view_box=view_box or geometry.viewbox(),
        overlay_regions=overlay_regions if overlay_regions else None,
        tooltips=tooltips,
    )

    # Apply optional styling
    if fill_color is not None:
        builder = builder.with_fills(fill_color)
    if counts is not None:
        builder = builder.with_counts(counts)
    if active is not None:
        builder = builder.with_active(active)

    return builder
```

### 4. `input_map()` - User-Facing OOP Function

```python
def input_map(
    id: str,
    geometry: Geometry,
    *,
    mode: Literal["single", "multiple", "count"] = "single",
    view_box: tuple[float, float, float, float] | None = None,
    fill_color: dict[str, str] | str | None = None,
    selected_aesthetic: Mapping[str, Any] | None = None,
    hover_highlight: Mapping[str, Any] | None = None,
    # ... other params
) -> Tag:
    """Create interactive map from Geometry object.

    Args:
        id: Input ID for Shiny
        geometry: Geometry object
        mode: Interaction mode ("single", "multiple", "count")
        view_box: Override viewBox tuple. If None, uses geometry.viewbox()
        fill_color: Fill colors
        selected_aesthetic: Styling for selected regions
        hover_highlight: Styling for hover state

    Example:
        geo = Geometry.from_dict(data)
        input_map("my_map", geo, mode="multiple")
        input_map("my_map", geo, view_box=(10, 10, 80, 80))  # Zoom

    Returns:
        Shiny Tag for rendering
    """
    # Extract viewBox
    vb_tuple = view_box if view_box else geometry.viewbox()

    # Extract main regions (exclude overlays for input maps)
    overlay_ids = set(geometry.overlays())
    main_regions = {k: v for k, v in geometry.regions.items() if k not in overlay_ids}

    # Convert tuple viewBox to string for React (temporary)
    vb_str = f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"

    # Build and serialize payload
    props = {
        "id": id,
        "geometry": main_regions,
        "viewBox": vb_str,
        "mode": mode,
        "fillColor": fill_color,
        "selectedAesthetic": selected_aesthetic,
        "hoverHighlight": hover_highlight,
        # ... other params
    }

    # Apply theme config, camelCase, drop Nones, etc.
    props = _apply_theme_config(props)
    props = _camel_props(_drop_nones(props))

    # Create Shiny Tag
    return Tag(...)
```

### 5. `output_map()` - User-Facing OOP Function

```python
def output_map(
    id: str,
    geometry: Geometry | None = None,  # Positional argument
    *,
    view_box: tuple[float, float, float, float] | None = None,
    tooltips: dict[str, str] | None = None,
    # ... other static params
) -> Tag:
    """Create output map with optional static parameters.

    Args:
        id: Output ID for Shiny
        geometry: Optional Geometry object (can be provided in @render_map instead)
        view_box: Optional viewBox tuple override
        tooltips: Optional static tooltips

    Example:
        # Geometry in output_map (positional argument)
        output_map("my_map", geo, tooltips=tooltips)

        # Geometry in @render_map
        output_map("my_map")

        @render_map
        def my_map():
            return Map(geo).with_fills(...)

    Returns:
        Shiny Tag for rendering
    """
    # Extract data from Geometry if provided
    static_regions = None
    static_view_box = view_box
    static_overlay_regions = None

    if geometry is not None:
        overlay_ids = geometry.overlays()
        static_overlay_regions = {k: v for k, v in geometry.regions.items() if k in overlay_ids}
        static_regions = {k: v for k, v in geometry.regions.items() if k not in overlay_ids}
        if static_view_box is None:
            static_view_box = geometry.viewbox()

    # Convert tuple viewBox to string
    vb_str = None
    if static_view_box:
        vb_str = f"{static_view_box[0]} {static_view_box[1]} {static_view_box[2]} {static_view_box[3]}"

    # Create Tag with static params
    return Tag(...)
```

## Implementation Changes

### Renamed Fields in `MapBuilder`

| Old Field | New Field |
|-----------|-----------|
| `self._geometry` | `self._regions` |
| `self._overlay_geometry` | `self._overlay_regions` |

### Changes to Existing Code

1. **Remove `Map = MapBuilder` alias** (line 451 in `_ui.py`)
2. **Rename `MapBuilder.__init__()` parameter**: `geometry` → `regions`
3. **Update all `MapBuilder` methods** to use `self._regions` instead of `self._geometry`
4. **Add `Map()` function** (new)
5. **Update `input_map()` signature** to accept `Geometry`
6. **Update `output_map()` signature** to accept `Geometry` as positional arg

## React/TypeScript Changes

### Type Definitions

```typescript
// packages/shinymap/js/src/types.ts
export type GeometryMap = Record<RegionId, string | string[]>;
export type ViewBox = [number, number, number, number] | string;
```

### Normalization Helpers

```typescript
// packages/shinymap/js/src/utils/geometry.ts (NEW FILE)
export function normalizePath(path: string | string[]): string {
  return Array.isArray(path) ? path.join(" ") : path;
}

export function normalizeGeometry(geometry: GeometryMap): Record<string, string> {
  const result: Record<string, string> = {};
  for (const [regionId, path] of Object.entries(geometry)) {
    result[regionId] = normalizePath(path);
  }
  return result;
}

export function normalizeViewBox(viewBox: ViewBox): string {
  return Array.isArray(viewBox)
    ? `${viewBox[0]} ${viewBox[1]} ${viewBox[2]} ${viewBox[3]}`
    : viewBox;
}
```

## Implementation Phases

### Phase 1: Core Infrastructure ✅ COMPLETED
- ✅ `Geometry` class
- ✅ Export from `geometry/__init__.py`

### Phase 2: Python API ✅ COMPLETED
- ✅ Rename `MapBuilder` fields: `_geometry` → `_regions`, `_overlay_geometry` → `_overlay_regions`
- ✅ Update `MapBuilder.__init__()`: rename `geometry` parameter to `regions`
- ✅ Update all `MapBuilder` methods to use new field names (especially `with_fill_color`)
- ✅ No `Map = MapBuilder` alias exists (never created)
- ✅ Create `Map(geometry: Geometry)` function
- ✅ Update `input_map()` to accept `Geometry`
- ✅ Update `output_map()` to accept `Geometry` as optional positional arg
- ✅ Update converter app to use `Map(geo)`
- ✅ `Map` exported in `__all__` in `__init__.py`
- ✅ Add `_viewbox_to_str()` helper function for consistent tuple-to-string conversion
- ✅ Fix type annotations: TYPE_CHECKING import for Geometry, consistent view_box types

### Phase 3: React Updates ✅ COMPLETED
- ✅ Update TypeScript types (`GeometryMap` now accepts `string | string[]`)
- ✅ Create normalization helpers (`normalizeGeometry()`, `normalizePath()`)
- ✅ Update InputMap.tsx to normalize geometry before rendering
- ✅ Update OutputMap.tsx to normalize geometry before rendering
- ✅ TypeScript build passes with no errors

### Phase 4: Documentation ✅ COMPLETED
- ✅ Examples already use Geometry OOP API (no updates needed)
- ✅ Added Geometry OOP API documentation section to SPEC.md
- ✅ Updated SPEC.md geometry format section to document both string and string[] support
- ✅ Updated PROPOSAL.md geometry representation to reflect flexible path format

## User-Facing API (OOP Only)

```python
from shinymap import Map, input_map, output_map
from shinymap.geometry import Geometry

# Load geometry
geo = Geometry.from_dict(data)

# Output maps (for @render_map)
Map(geo)
Map(geo, view_box=(10, 10, 80, 80))  # Zoom
Map(geo, fill_color=colors, counts=counts)  # Inline styling
Map(geo).with_fills(colors).with_counts(counts)  # Fluent styling

# Input maps
input_map("my_map", geo, mode="multiple")
input_map("my_map", geo, view_box=(10, 10, 80, 80))

# Output map in UI (positional geometry arg)
output_map("my_map", geo, tooltips=tooltips)

# Or provide geometry in @render_map
output_map("my_map")

@render_map
def my_map():
    return Map(geo).with_fills(...)
```

## Benefits

1. **Single, clean API**: Only one way to do things - OOP with `Geometry`
2. **Type safety**: `Geometry` validates at load time
3. **Zoom/pan ready**: Tuple viewBox for easy manipulation
4. **Clear naming**: `regions` (dict) vs `geometry` (object) in internal code
5. **No confusion**: No dict-based alternatives to maintain
6. **Concise syntax**: `output_map("id", geo)` with positional arg

## Files to Modify

### Python (Phase 2)
- ✅ `packages/shinymap/python/src/shinymap/geometry/_core.py`
- ✅ `packages/shinymap/python/src/shinymap/geometry/__init__.py`
- ⏳ [packages/shinymap/python/src/shinymap/_ui.py](packages/shinymap/python/src/shinymap/_ui.py)
  - Rename fields throughout `MapBuilder`
  - Remove `Map = MapBuilder` alias
  - Add `Map()` function
  - Update `input_map()` signature
  - Update `output_map()` signature (geometry as positional)
- ⏳ `packages/shinymap/python/src/shinymap/geometry/converter/_app.py`

### React/TypeScript (Phase 3)
- ⬜ `packages/shinymap/js/src/types.ts`
- ⬜ `packages/shinymap/js/src/utils/geometry.ts` (NEW)
- ⬜ `packages/shinymap/js/src/components/InputMap.tsx`
- ⬜ `packages/shinymap/js/src/components/OutputMap.tsx`
