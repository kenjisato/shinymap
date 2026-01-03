# Design: Unified MapBuilder for Static Analysis and Export

**Status**: Phase 1 Complete (see Amendment below)
**Created**: 2026-01-01
**Updated**: 2026-01-02

> **Note**: The original design proposed adding static analysis methods to MapBuilder.
> This was revised to use a separate `StillLife` class. See the [Amendment](#amendment-stilllife-class-for-static-analysis-2026-01-02) at the end of this document.

## Overview

This document describes a unified approach to static analysis and SVG export through a single `MapBuilder` class, avoiding separate APIs for `dump_aes` and `static_map`.

## Motivation

Currently:
- `output_map()` uses `MapBuilder` (intermediate object returned by `Map()`)
- `input_map()` builds payload directly (no intermediate)
- Aesthetic resolution happens on JavaScript side for interactive maps
- No Python-side tools to inspect what aesthetics will be applied

**Goals**:
1. Unified builder pattern for both input and output maps
2. Static analysis methods (`dump_aes()`) on the builder
3. Static SVG export (`to_svg()`) on the builder
4. Consistent API for interactive and static use cases
5. `Display()` as a first-class Mode type like `Count()` and `Cycle()`

## Key Insight: Unified Mode System

All map types use a Mode object that defines behavior and can carry indexed aesthetics:

```python
# input_map modes
input_map("id", geometry, mode="single")
input_map("id", geometry, mode="multiple")
input_map("id", geometry, mode=Count(aes=aes.Indexed(fill_color=[...])))
input_map("id", geometry, mode=Cycle(n=4, aes=aes.Indexed(fill_color=[...])))

# output_map mode - Display() as first-class Mode!
output_map("id", geometry, mode=Display(aes=aes.Indexed(fill_color=["red", "yellow", "green"])))
```

This allows prepopulating the value-to-color mapping directly in the output_map declaration.

### Mode Types

| Mode | Click Behavior | Value Semantics |
|------|---------------|-----------------|
| `Single()` | Select one | 0 = not selected, 1 = selected |
| `Multiple()` | Toggle selection | 0 = not selected, 1 = selected |
| `Count()` | Increment | min(value, len-1) → aesthetic index |
| `Cycle(n)` | Cycle through n states | value % n → aesthetic index |
| `Display()` | Hover only (no click) | value → aesthetic index (user-provided) |

All modes share the same `value: dict[str, int]` model.

## Display() Mode Design

```python
@dataclass
class Display(Mode):
    """Display-only mode for output_map.

    Regions respond to hover but not click. Value determines
    which indexed aesthetic to use.
    """
    aes: IndexedAesthetic | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"type": "display"}
        if self.aes is not None:
            result["aes_indexed"] = self.aes.to_dict()
        return result
```

### Usage Examples

```python
from shinymap import output_map, aes
from shinymap.mode import Display

# Traffic light colors for status values
output_map(
    "status_map",
    geometry,
    mode=Display(aes=aes.Indexed(
        fill_color=["#gray", "#green", "#yellow", "#red"]
    ))
)

@render_map
def status_map():
    # value 0=unknown, 1=good, 2=warning, 3=error
    return Map(geometry, value=status_values)
```

## Common Data Structures

Both `input_map` and `output_map` share:
- `outline: Outline` - geometry
- `resolved_aes: ByGroup` - pre-resolved aesthetics
- `value: dict[str, int]` - region values (unified model)
- `mode: ModeType` - mode configuration (including `Display()`)
- `tooltips: dict[str, str]` - region tooltips
- `view_box: tuple` - SVG viewBox
- `layers: dict` - layer configuration

A single `MapBuilder` can handle all mode types.

## Proposed Architecture

### Unified MapBuilder

```python
class MapBuilder:
    """Builder for map payloads supporting both interactive and static output."""

    def __init__(
        self,
        outline: Outline,
        *,
        resolved_aes: ByGroup,
        value: dict[str, int] | None = None,
        mode: ModeType | None = None,
        tooltips: dict[str, str] | None = None,
        view_box: tuple[float, float, float, float] | None = None,
        layers: dict[str, list[str]] | None = None,
    ):
        ...

    # Fluent setters
    def with_value(self, value: dict[str, int]) -> MapBuilder: ...
    def with_aes(self, aes: AesType) -> MapBuilder: ...
    def with_tooltips(self, tooltips: dict[str, str]) -> MapBuilder: ...
    def with_view_box(self, view_box: tuple) -> MapBuilder: ...
    def with_layers(self, layers: dict) -> MapBuilder: ...

    # Payload generation (for Shiny)
    def as_json(self) -> dict: ...

    # Static analysis
    def dump_aes(
        self,
        region_id: str,
        *,
        is_hovered: bool = False,
    ) -> dict[str, Any]:
        """Get resolved aesthetic for a region.

        Uses value dict to determine selected state:
        - value > 0: is_selected = True
        - value = 0 or missing: is_selected = False
        """
        ...

    def dump_aes_table(
        self,
        *,
        region_ids: list[str] | None = None,  # None = all regions
        include_hover: bool = False,
    ) -> list[dict[str, Any]]:
        """Get resolved aesthetics for multiple regions."""
        ...

    # Static SVG export
    def to_svg(
        self,
        *,
        hovered_id: str | None = None,
        output: str | Path | None = None,
    ) -> str | None:
        """Generate static SVG with resolved aesthetics.

        Uses value dict to determine which regions are selected.

        Args:
            hovered_id: Optional region to show as hovered
            output: If provided, write to file and return None

        Returns:
            SVG string (if output is None)
        """
        ...
```

### WashResult.build() Entry Point

```python
class WashResult:
    def build(
        self,
        geometry: Outline,
        *,
        aes: AesParam = MISSING,
        value: dict[str, int] | None = None,
        mode: ModeType | None = None,
        tooltips: dict[str, str] | None = None,
        view_box: tuple | None = None,
        layers: dict | None = None,
    ) -> MapBuilder:
        """Create a MapBuilder with wash aesthetics applied.

        This is the unified entry point for:
        - Interactive maps (input_map, output_map)
        - Static analysis (dump_aes)
        - Static export (to_svg)
        """
        resolved_aes = self.config.apply(aes, geometry)
        return MapBuilder(
            geometry,
            resolved_aes=resolved_aes,
            value=value,
            mode=mode,
            tooltips=tooltips,
            view_box=view_box,
            layers=layers,
        )

    def input_map(self, id: str, geometry: Outline, mode: ModeType, ...) -> TagList:
        """Create interactive input map (convenience wrapper)."""
        builder = self.build(geometry, mode=mode, aes=aes, ...)
        return _render_input_map(id, builder, ...)

    def output_map(
        self,
        id: str,
        geometry: Outline | None = None,
        *,
        mode: Display | None = None,  # Accept Display() mode
        ...
    ) -> TagList:
        """UI placeholder for @render_map output.

        Args:
            mode: Display mode with optional indexed aesthetics.
                  If None, uses Display() with default aesthetics.
        """
        effective_mode = mode if mode is not None else Display()
        ...
```

## Usage Examples

### Interactive Maps (unchanged API)

```python
wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))

# input_map - unchanged
wc.input_map("region", geometry, mode="single")

# output_map with Display() mode
wc.output_map("my_map", geometry, mode=Display(
    aes=aes.Indexed(fill_color=["#gray", "#blue", "#green"])
))

@wc.render_map
def my_map():
    return Map(geometry, value=counts)
```

### Static Analysis

```python
wc = Wash(shape=aes.ByState(
    base=aes.Shape(fill_color="#e2e8f0"),
    select=aes.Shape(fill_color="#3b82f6"),
))

# Create builder - same value model as interactive maps
builder = wc.build(geometry, value={"region1": 1, "region2": 0, "region3": 2})

# Inspect aesthetic for a region
aes_dict = builder.dump_aes("region1")  # region1 has value=1
print(aes_dict)
# {"fill_color": "#3b82f6", ...}

# Table for all regions
table = builder.dump_aes_table()
for row in table:
    print(f"{row['region_id']}: {row['fill_color']}")
```

### Static SVG Export

```python
builder = wc.build(geometry, value={"region1": 1, "region2": 1, "region3": 0})

# Get SVG string
svg_str = builder.to_svg()

# With hover state
svg_str = builder.to_svg(hovered_id="region3")

# Save to file
builder.to_svg(output="map.svg")
```

### Chained Usage

```python
# Fluent API
(wc.build(geometry)
   .with_value({"region1": 1, "region2": 1})
   .to_svg(output="selection.svg"))
```

### Value-State Mapping with Display() Mode

```python
# Prepopulate color scale in output_map declaration
wc.output_map(
    "status",
    geometry,
    mode=Display(aes=aes.Indexed(
        fill_color=["#f3f4f6", "#22c55e", "#f59e0b", "#ef4444"]
    ))
)

@wc.render_map
def status():
    # Just provide values - colors are already configured
    return Map(geometry, value=status_values)
```

## Implementation Plan

### Phase 0: Add Display() Mode ✅ COMPLETE

1. [x] Add `Display` class to `shinymap/mode.py`
2. [x] Update mode normalization to handle Display
3. [x] Update output_map to accept mode parameter (`mode: Display = Display()`)
4. [x] Update JS to handle "display" mode type

**Additional features implemented:**
- [x] `Display(clickable=True)` - enables click events on output maps
- [x] `Display(input_id="custom")` - custom input ID for click events
- [x] `raw=True` on `input_map` - returns raw dict instead of transformed types
- [x] Fixed mode.py to use snake_case keys (JS handles camelCase conversion)

### Phase 1: Extend MapBuilder

1. [ ] Add `outline` and `resolved_aes` storage to MapBuilder
2. [ ] Add `mode` parameter support
3. [ ] Implement `dump_aes()` method using value-based selection
4. [ ] Implement `dump_aes_table()` method
5. [ ] Add unit tests for analysis methods

### Phase 2: Add SVG Export

1. [ ] Implement `to_svg()` method
2. [ ] Handle layer rendering order (underlay → base → overlay → selection → hover)
3. [ ] Apply resolved aesthetics to SVG elements
4. [ ] Add unit tests for SVG export

### Phase 3: Add WashResult.build()

1. [ ] Add `build()` method to WashResult
2. [ ] Refactor `input_map()` to use build() internally (optional)
3. [ ] Update documentation and examples

### Phase 4: Cleanup

1. [ ] Update design documents
2. [ ] Add integration tests
3. [ ] Update CLAUDE.md with new API

## Resolution Logic

### dump_aes() Implementation

```python
def dump_aes(
    self,
    region_id: str,
    *,
    is_hovered: bool = False,
) -> dict[str, Any]:
    """Get resolved aesthetic for a region."""
    from ..relative import RegionState, AestheticConfig, resolve_region

    # 1. Look up ByState for region (region_id → group → __type → __all)
    by_state = self._lookup_by_state(region_id)

    # 2. Get value and determine is_selected
    value = self._value.get(region_id, 0) if self._value else 0
    is_selected = value > 0

    # 3. Build config
    config = AestheticConfig(
        aes_base=by_state.base,
        aes_select=by_state.select,
        aes_hover=by_state.hover,
        count=value,  # for IndexedAesthetic
    )

    # 4. Build state
    state = RegionState(
        region_id=region_id,
        is_selected=is_selected,
        is_hovered=is_hovered,
        group=self._outline.group_for(region_id),
    )

    # 5. Resolve and return as dict
    resolved = resolve_region(state, config)
    return resolved.to_dict()
```

### to_svg() Implementation

Uses the same resolution logic as `dump_aes()` but applies to all regions:

1. For each region, resolve aesthetic based on value (value > 0 → selected)
2. Render layers in order: underlay → base → overlay → selection → hover
3. Build SVG using `svg` library

## Differences from export_svg()

| Aspect | `export_svg()` | `MapBuilder.to_svg()` |
|--------|---------------|----------------------|
| Aesthetics | Original SVG attributes | Resolved shinymap aesthetics |
| State support | No | Yes (selected via value, hovered) |
| Layers | No | Yes (underlay/overlay) |
| Value-based colors | No | Yes (IndexedAesthetic) |
| Use case | Round-trip SVG | Static visualization |

## Design Decisions

1. **Keep both `Map()` and `build()`**
   - `Map()` is already public API for output_map usage
   - `wc.build()` returns MapBuilder with wash aesthetics pre-applied
   - Both serve different purposes and can coexist

2. **MapBuilder stores `outline` reference**
   - Current design: stores extracted `_regions` dict only
   - New design: also store `Outline` reference for group lookups, element types
   - Needed for `dump_aes()` to look up groups and `to_svg()` to access path data
   - Slight memory overhead is acceptable

3. **Value-to-selection mapping**
   - When `aes.Indexed` is NOT provided:
     - `value = 0` → base aesthetic (not selected)
     - `value > 0` → select aesthetic (selected)
   - When `aes.Indexed` IS provided:
     - `value` → index into indexed aesthetic array
   - This keeps the default simple while allowing complex cases via IndexedAesthetic

## Breaking Change: Upgrade RegionState to Use Value

### Rationale

Currently `RegionState` has:
```python
@dataclass
class RegionState:
    region_id: str
    is_selected: bool = False  # Too limited!
    is_hovered: bool = False
    group: str | None = None
```

The boolean `is_selected` doesn't support:
- `Count()` mode: needs actual count for `IndexedAesthetic` lookup
- `Cycle(n)` mode: needs value to compute `value % n`
- `Display()` mode: needs value for indexed color mapping

### New Design

```python
@dataclass
class RegionState:
    region_id: str
    value: int = 0  # The actual value (count, cycle state, etc.)
    is_hovered: bool = False
    group: str | None = None

    @property
    def is_selected(self) -> bool:
        """Derived from value for backwards compatibility."""
        return self.value > 0
```

### Impact on resolve_region()

The `resolve_region()` function needs to:
1. Use `state.value` for `IndexedAesthetic` resolution
2. Use `state.is_selected` (derived property) for select layer logic

```python
def resolve_region(state: RegionState, config: AestheticConfig) -> ShapeAesthetic:
    # ... existing layers ...

    # Layer 3: SELECT (if selected)
    if state.is_selected:  # Now a property: value > 0
        current = _merge_aesthetic(config.aes_select, current)

    # IndexedAesthetic resolution uses state.value
    # (implementation depends on how IndexedAesthetic is stored in config)
```

### Files to Modify

- `packages/shinymap/python/src/shinymap/relative.py` - Update `RegionState`
- Tests that create `RegionState` with `is_selected=True` → `value=1`

### Commit Strategy

This change should be done **together with** the `active_ids` removal since both are part of the unified value model.

## Breaking Change: Deprecate `active_ids`

### Rationale

Currently `output_map` uses `active_ids` to specify highlighted regions separately from `value`. This creates redundancy:

```python
# Current API (redundant)
Map(geometry, value=counts, active=["region1", "region2"])
```

With the unified value model, `active_ids` is unnecessary:
- `value > 0` already means "selected/active"
- `IndexedAesthetic` handles complex value-to-color mappings

```python
# New API (unified)
Map(geometry, value={"region1": 1, "region2": 1, "region3": 0})
```

### Migration Path

1. **Python changes**:
   - Remove `active` parameter from `Map()` function
   - Remove `with_active()` method from `MapBuilder`
   - Remove `_active_ids` field from `MapBuilder`
   - Update `as_json()` to not emit `active_ids`

2. **TypeScript changes**:
   - Remove `activeIds` from props interface
   - Update `InputMap.tsx` and `OutputMap.tsx` to derive selection from `value`
   - Selection logic: `isSelected = (value[regionId] ?? 0) > 0`

3. **JavaScript payload changes**:
   - Remove `active_ids` from payload structure
   - Update `shinymap-shiny.js` if needed

### Files to Modify

**Python**:
- `packages/shinymap/python/src/shinymap/_map.py` - Remove `active` param and `with_active()`
- `packages/shinymap/python/src/shinymap/uicore/_render_map.py` - Update if uses active_ids

**TypeScript**:
- `packages/shinymap/js/src/types.ts` - Remove `activeIds` from interfaces
- `packages/shinymap/js/src/components/InputMap.tsx` - Derive selection from value
- `packages/shinymap/js/src/components/OutputMap.tsx` - Derive selection from value

### Commit Strategy

The `RegionState` upgrade and `active_ids` removal should be a **single commit** before implementing the MapBuilder extensions:

```
Unify selection model: value replaces is_selected and active_ids

BREAKING CHANGE:
- RegionState.is_selected replaced with RegionState.value (int)
- is_selected is now a derived property (value > 0)
- Map() active parameter removed, use value dict instead
- MapBuilder.with_active() removed

Migration:
  # Python - Map()
  # Before
  Map(geometry, value=counts, active=["a", "b"])

  # After
  Map(geometry, value={"a": 1, "b": 1, "c": 0})

  # Python - RegionState
  # Before
  RegionState("region1", is_selected=True)

  # After
  RegionState("region1", value=1)
```

## Related Documents

- [props-structure.md](props-structure.md) - Mode types and value semantics
- [aes-protocol.md](aes-protocol.md) - References `dump_table()` in checklist
- [aes-resolution.md](aes-resolution.md) - Resolution logic
- [aes-payload-v03.md](aes-payload-v03.md) - Payload format

---

# Amendment: StillLife Class for Static Analysis (2026-01-02)

## Design Revision

After implementing the prerequisite changes (Phase 0.5), we reconsidered the original approach of adding `dump_aes()` and `to_svg()` methods directly to MapBuilder.

### Concerns with Original Approach

1. **Lazy imports inside methods**: The `dump_aes()` method would require importing from `relative.py` inside the method body to avoid circular dependencies. This is a code smell.

2. **Mixed responsibilities**: MapBuilder would become responsible for two distinct concerns:
   - Building payloads for Shiny (existing)
   - Static analysis and export (new)

3. **Optional workflow penalty**: Most users won't need static analysis, but MapBuilder would carry the extra complexity.

### New Approach: Separate StillLife Class

Instead of extending MapBuilder, we introduce a dedicated `StillLife` class that captures a map's state for static analysis and export.

The name follows the painting metaphor established by `Wash()` (watercolor wash):
- **Wash**: Prepare the canvas with default colors (like a watercolor wash)
- **StillLife**: Capture the final scene for analysis and display

## StillLife Class Design

```python
from shinymap import Wash, StillLife

wc = Wash(shape=aes.Shape(fill_color="#e2e8f0"))
builder = wc.build(geometry, value={"region1": 1, "region2": 0})

# StillLife captures the scene for analysis/export
pic = StillLife(builder, hovered="region2")

pic.aes("region1")           # Resolved aesthetic for region1
pic.aes_table()              # All regions' aesthetics
pic.to_svg("map.svg")        # Export static SVG
```

### Naming: The Painting Metaphor

| Class | Painting Metaphor | Role |
|-------|-------------------|------|
| `Wash` | Watercolor wash layer | Set default colors/aesthetics |
| `Map` / `MapBuilder` | Work in progress | Dynamic, changing state |
| `StillLife` | Still life painting | Static captured scene |

Alternative names considered:
- **Snapshot** - Familiar to developers (database snapshots)
- **Print** - Final output for reproduction
- **Proof** - Test print for inspection
- **Frame** - Ready for display

**StillLife** was chosen because it evokes a classic painting genre and suggests both analysis ("studying a still life") and export ("displaying a still life").

## StillLife API

```python
class StillLife:
    """Static snapshot of a map for aesthetic analysis and SVG export.

    Like a still life painting, this class captures a map's state at a
    specific moment, allowing you to:
    - Inspect resolved aesthetics for any region
    - Export a static SVG with specific hover/selection states
    """

    def __init__(
        self,
        builder: MapBuilder,
        *,
        value: dict[str, int] | None = None,  # Override builder's value
        hovered: str | None = None,
    ):
        """Create a still life from a MapBuilder.

        Args:
            builder: MapBuilder created via WashResult.build()
            value: Override value dict (if None, uses builder's value)
            hovered: Region ID to show as hovered
        """
        ...

    def aes(
        self,
        region: str,
        *,
        is_hovered: bool | None = None
    ) -> dict[str, Any]:
        """Get resolved aesthetic for a region."""
        ...

    def aes_table(
        self,
        *,
        region_ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get resolved aesthetics for multiple regions."""
        ...

    def to_svg(
        self,
        output: str | Path | None = None
    ) -> str | None:
        """Generate static SVG with resolved aesthetics."""
        ...
```

## Revised Implementation Plan

### Phase 0.5: Prerequisite Changes ✅ COMPLETE

1. [x] Upgrade `RegionState` to use `value: int` with `is_selected` as derived property
2. [x] Remove `active_ids` from Python and TypeScript
3. [x] TypeScript components derive selection from `value > 0`

### Phase 1: StillLife Class (REVISED) ✅ COMPLETE

1. [x] Create `shinymap/_stilllife.py` module
2. [x] Implement `StillLife.__init__()` - validates builder, stores state
3. [x] Implement `StillLife.aes()` - resolve aesthetic for single region
4. [x] Implement `StillLife.aes_table()` - resolve for all regions
5. [x] Add `WashResult.build()` method
6. [x] Extend `MapBuilder.__init__` to accept `_outline` and `_resolved_aes` (private)
7. [x] Export `StillLife` from `shinymap/__init__.py`
8. [x] Add unit tests

### Phase 2: SVG Export

1. [ ] Implement `StillLife.to_svg()` method
2. [ ] Handle layer rendering order
3. [ ] Apply resolved aesthetics to SVG elements
4. [ ] Add unit tests

### Phase 3: Documentation

1. [ ] Update design documents
2. [ ] Add examples
3. [ ] Update CLAUDE.md with new API

## Module Structure

```
shinymap/
├── __init__.py          # Export StillLife
├── _map.py              # MapBuilder (unchanged public API)
├── _stilllife.py        # NEW: StillLife class
├── uicore/
│   └── _wash.py         # Add build() method to WashResult
└── ...
```

## Benefits of StillLife Approach

1. **Clean separation**: MapBuilder stays focused on Shiny payloads
2. **No lazy imports in MapBuilder**: Heavy imports only in `_stilllife.py`
3. **Explicit opt-in**: Users who need static analysis import `StillLife`
4. **Testable**: `StillLife` can be tested independently
5. **Future-proof**: Can add PDF export, animations without touching MapBuilder
6. **Clear mental model**: Interactive (MapBuilder) vs Static (StillLife)
7. **Consistent metaphor**: Wash → StillLife follows painting theme

## Comparison: Original vs Revised

| Aspect | Original (MapBuilder) | Revised (StillLife) |
|--------|----------------------|---------------------|
| Static methods on | MapBuilder | StillLife |
| Lazy imports | Yes (in methods) | No (in module) |
| Separation of concerns | Mixed | Clean |
| User workflow | `builder.dump_aes()` | `StillLife(builder).aes()` |
| Module dependencies | MapBuilder imports relative | StillLife imports all |
| Breaking changes | Extends MapBuilder | Additive only |

---

# Prerequisite: Eliminate "geometry" Naming Confusion (2026-01-02)

## Problem

Three related terms are used inconsistently, causing confusion when reading code:

| Term | Current Usage | Problem |
|------|---------------|---------|
| `geometry` | JS prop, Python param, payload key | Overloaded, vague |
| `outline` | Python `Outline` class | Clear but underused |
| `regions` | Python `Regions` class | Sometimes called `geometry` |

**Confusing code examples:**
```python
# Param says "geometry" but receives Outline
Map(geometry=outline_obj)

# Internal var is "_regions" but emitted as "geometry"
data["geometry"] = _normalize_outline(self._regions)

# JS receives "geometry" which is actually regions
<InputMap geometry={...} />
```

## Solution: Eliminate "geometry" Entirely

**Goal**: Zero occurrences of "geo" in the codebase (except maybe legacy comments).

### New Naming Convention

| Concept | Class/Type | Variable/Param | Payload Key |
|---------|------------|----------------|-------------|
| Full container | `Outline` | `outline` | n/a |
| Region dict | `Regions` | `regions` | `regions` |

### Python Changes

**API (breaking):**
```python
# Before
Map(geometry=outline)
input_map("id", geometry, mode="single")
output_map("id", geometry)

# After
Map(outline=outline)
# OR for convenience:
Map(outline)  # positional

input_map("id", outline, mode="single")
output_map("id", outline)
```

**Internal:**
- `MapBuilder._regions` → keep (it's accurate)
- `_normalize_outline()` → `_normalize_regions()` (it normalizes regions, not outline)
- All `geometry` variables → `outline` or `regions`

**Payload:**
```python
# Before
data["geometry"] = ...

# After
data["regions"] = ...
```

### TypeScript Changes

**Props (breaking for React users):**
```typescript
// Before
<InputMap geometry={...} />
<OutputMap geometry={...} />

// After
<InputMap regions={...} />
<OutputMap regions={...} />
```

**Types:**
```typescript
// Before
type GeometryMap = Record<RegionId, Element[]>;

// After
type RegionsMap = Record<RegionId, Element[]>;
// Keep GeometryMap as alias for backwards compat? Or remove entirely?
```

**Payload handling:**
```typescript
// Before
props.geometry

// After
props.regions
```

### Files to Modify

**Python:**
- `_map.py`: `Map(geometry=)` → `Map(outline=)`
- `_map.py`: `MapBuilder.__init__(regions=)` - keep
- `_map.py`: `as_json()` emit `regions` instead of `geometry`
- `uicore/_input_map.py`: param `outline` (already correct?)
- `uicore/_output_map.py`: param `outline` (already correct?)
- `uicore/_wash.py`: check param names
- `uicore/_util.py`: `_normalize_outline()` → `_normalize_regions()`
- All examples in `examples/`
- Tests

**TypeScript:**
- `types.ts`: `GeometryMap` → `RegionsMap`, update prop interfaces
- `components/InputMap.tsx`: `geometry` prop → `regions`
- `components/OutputMap.tsx`: `geometry` prop → `regions`
- `utils/geometry.ts`: function names if any use "geometry"
- `shinyBridge.ts`: payload key handling
- `demo/`: update all demos

### Migration Guide

```python
# Python migration
# Before (v0.2.x)
from shinymap import Map, input_map, output_map

Map(geometry=outline)
input_map("id", geometry, mode="single")

# After (v0.3.0)
Map(outline=outline)
# or positional:
Map(outline)

input_map("id", outline, mode="single")
```

```typescript
// TypeScript migration
// Before
<InputMap geometry={regions} />

// After
<InputMap regions={regions} />
```

### Implementation Order

1. **Phase 0.6**: Rename in Python
   - Update `_map.py`, `_util.py`, UI functions
   - Update payload key to `regions`
   - Update all Python examples and tests

2. **Phase 0.7**: Rename in TypeScript
   - Update types and interfaces
   - Update components
   - Update demos
   - Rebuild dist/

3. **Phase 0.8**: Documentation
   - Update CLAUDE.md, SPEC.md, README.md
   - Migration notes in CHANGELOG

This should be done **before** Phase 1 (StillLife) to avoid propagating confusion.
