# Design: Aesthetic Resolution Architecture

**Status**: In Progress
**Created**: 2025-12-30
**Updated**: 2026-01-01

This document describes the aesthetic resolution system in shinymap.

**Related documents:**
- [aes-protocol.md](aes-protocol.md) - Dict serialization protocol (`to_dict()`/`from_dict()`)
- [aes-payload-v03.md](aes-payload-v03.md) - v0.3 payload format for JavaScript
- [restructuring-toward-v0.3.md](restructuring-toward-v0.3.md) - Broader goal of eliminating circular dependencies

## Philosophy

### Late Serialization

Keep data as typed Python objects as long as possible. Serialization to dict/JSON should only happen at the JavaScript boundary (when sending data to the frontend).

**Benefits:**
- Business logic remains testable with type-safe objects
- IDE autocomplete and type checking work throughout Python layer
- Single point of conversion reduces bugs from scattered serialization

### Separation of Resolution and Serialization

Resolution and payload building are two distinct processes:

1. **Resolution**: Takes user aesthetics + wash config → produces fully resolved aesthetics
   - Used by: payload building, `static_map()`, tabular dump
2. **Payload building**: Takes resolved aesthetics → produces JSON for JavaScript
   - Used by: `_input_map()`, `_output_map()`

This separation allows resolution to be reused for non-interactive outputs.

## Two-Dimensional Resolution

Aesthetic resolution happens along two orthogonal dimensions:

### The Resolution Table

```
              base        select      hover
__all         A           B           C        <- global default
__shape       D           E           F        <- shape elements default
__line        G           H           I        <- line elements default
__text        J           K           L        <- text elements default
groupA        M           N           O        <- group-specific
shapeA        P           Q           R        <- region-specific
```

### Dimensions of Inheritance

| Sentinel | Direction | Meaning |
|----------|-----------|---------|
| `aes.copy_group` | ↑ (group) | Copy from parent group (region → group → __type → __all) |
| `aes.copy_parent` | ← (layer) | Copy from previous layer (base → select → hover) |

Additionally, `aes.disabled` is a constant aesthetic with transparent values for making elements invisible.

### aes.copy_group: Group Inheritance (↑)

When a value is `aes.copy_group` (or omitted), walk **up** the group hierarchy:

```
region → group → __type → __all
```

Example:
```
              base        select      hover
__all         ?           ?           W
__shape       ?           X           copy_group  → resolves to W (from __all)
shapeA        Y           copy_group  ?           → select resolves to X (from __shape)
```

- `shapeA.select = aes.copy_group` → inherits from `__shape.select` (X)
- `__shape.hover = aes.copy_group` → inherits from `__all.hover` (W)

### aes.copy_parent: Layer Inheritance (←)

When a value is `aes.copy_parent`, copy from the **previous layer** in the chain:

```
base → select → hover
```

Example:
```
              base        select      hover
shapeA        Y           copy_parent ?        → select same as Y
groupA        Z           W           copy_parent → hover same as W
```

- `shapeA.select = aes.copy_parent` → visually identical to `shapeA.base` (Y), but rendered in selection overlay (higher z-index)
- `groupA.hover = aes.copy_parent` → visually identical to `groupA.select` (W), but rendered in hover overlay

### aes.disabled: Skip Overlay Rendering

`aes.disabled` indicates that a layer should not be rendered at all (no overlay).

This is different from `aes.copy_parent`:

| Sentinel | Visual | Z-index overlay | Opacity stacking |
|----------|--------|-----------------|------------------|
| `aes.copy_parent` | Same as parent layer | **Yes** (rendered in overlay) | Overlay on top of base (less transparent) |
| `aes.disabled` | Same as parent layer | **No** (stays at base z-index) | Base opacity preserved |

Key behavioral differences:
- **Z-index**: With `aes.copy_parent`, selected/hovered regions are rendered in overlay layers, so their borders are fully visible on top of neighbors. With `aes.disabled`, no overlay rendering, so borders may be partially hidden by adjacent regions.
- **Opacity**: When `fill_opacity < 1`, `aes.copy_parent` renders an overlay on top of the base layer, making the region appear more opaque. With `aes.disabled`, no overlay is rendered, so base transparency is preserved.

Example usage:

```python
aes.ByState(
    base=aes.Shape(fill_color="#e5e7eb"),
    select=aes.disabled,  # no selection overlay (stays at base z-index)
    hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
)
```

For hiding regions completely (no rendering at all), use geometry metadata (`layers.hidden`) instead.

### Error Cases

| Case | Behavior |
|------|----------|
| `base = aes.copy_parent` | **Error** - no layer to the left. |
| `base = aes.disabled` | **Error** - base must have concrete values. |
| `__all = aes.copy_group` | **Error** - no group above. Must provide concrete aesthetic. |

### Resolution Order (Python Side)

Python performs the following resolution steps before sending payload to JavaScript:

1. **Group resolution (↑)**: For each MISSING value, walk up the hierarchy
2. **Layer resolution (←)**: For each None value, copy from previous layer

**RelativeExpr is NOT resolved in Python** - it is serialized and sent to JavaScript for runtime resolution.

### RelativeExpr: JavaScript Runtime Resolution

`RelativeExpr` values (e.g., `PARENT.stroke_width + 1`) are serialized to JSON and sent to JavaScript:

```python
# Python (user code)
hover = aes.Shape(stroke_width=PARENT.stroke_width + 1)

# Serialized in payload
{"stroke_width": {"__relative__": true, "field": "stroke_width", "offset": 1}}
```

JavaScript resolves RelativeExpr at render time because only JS knows the actual parent:
- **hover when not selected**: parent is `base`
- **hover when selected**: parent is `select`
- **select with RelativeExpr**: parent is `base`

This is why RelativeExpr resolution must happen on the client side - the parent depends on the current interaction state which only JavaScript knows.

## Aesthetic Hierarchy (Legacy View)

> **Note**: This section describes the layer hierarchy. For the complete picture,
> see "Two-Dimensional Resolution" above which covers both group and layer dimensions.

The aesthetic system uses a layered hierarchy where each layer can override or modify properties from the layer below:

```
Layer 0: LIBRARY DEFAULT   (aes._defaults.shape/line/text)
Layer 1: WASH CONFIG       (wash(shape=..., line=..., text=...))
Layer 2: BASE              (aes.ByState(base=...))
Layer 3: SELECT            (aes.ByState(select=...)) - if selected
Layer 4: HOVER             (aes.ByState(hover=...)) - if hovered
```

### Resolution Chain

Layers resolve sequentially, each against the result of the previous:

```
wash_default → base.resolve(wash_default) → resolved_base
                                         → select.resolve(resolved_base) → resolved_select
                                         → hover.resolve(resolved_select if selected else resolved_base)
```

Key insight: `select` resolves against `resolved_base`, and `hover` resolves against the current state (either `resolved_select` or `resolved_base` depending on selection).

### ByGroup: Orthogonal to Layers

`ByGroup` is a **container** that maps region/group names to aesthetic configurations. It represents the **group dimension** (↑), while layers represent the **layer dimension** (←).

```python
aes.ByGroup(
    __all=aes.ByState(
        base=aes.Shape(fill_color="#e5e7eb"),
        hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
    ),
    coastal=aes.Shape(fill_color="#3b82f6"),  # base only (shorthand)
    mountain=aes.ByState(
        base=aes.Shape(fill_color="#10b981"),
        select=aes.Shape(fill_color="#6ee7b7"),
    ),
)
```

Each entry in `ByGroup` can be:
- A `ByState` with full `base/select/hover` configuration
- A single leaf aesthetic (shorthand for `ByState(base=...)`)
- `MISSING` (inherit from parent group)

Resolution priority within `ByGroup` (bottom to top):
1. `region_id` (highest) - individual region override
2. `<group_name>` - named group from geometry metadata
3. `__shape`, `__line`, `__text` - element type defaults
4. `__all` - global default (lowest)

### Existing Infrastructure

`relative.py` already provides resolution functions:
- `_merge_aesthetic(child, parent)` - Merges child onto resolved parent
- `resolve_region(state, config)` - Resolves full chain for a region
- `preview_region(state, config)` - Debugging tool showing layer-by-layer resolution

## Leaf Aesthetic Types

Four leaf aesthetic types exist:
- **ShapeAesthetic**: Filled regions (fill + stroke)
- **LineAesthetic**: Stroke-only elements (grid lines, dividers)
- **TextAesthetic**: Text elements (fill for text color, stroke for outline)
- **PathAesthetic**: Flexible type with `kind` hint for rendering

### Embed/Resolve/Project Pattern

```
LeafAesthetic --(embed)--> BaseAesthetic --(resolve)--> BaseAesthetic --(project)--> LeafAesthetic
```

1. **Embed**: Leaf type is "promoted" to BaseAesthetic for chain resolution
2. **Resolve**: Chain walks through layers, resolving MISSING and RelativeExpr
3. **Project**: Final resolved BaseAesthetic is "projected" back to leaf type

This allows interactive effects (hover, select) to work on any leaf type, not just shapes.

## IndexedAesthetic: Special Case

`IndexedAesthetic` is used with `Count()` and `Cycle()` modes to provide state-based visual feedback. It does NOT fit cleanly into the resolution chain described above.

### How IndexedAesthetic Works

IndexedAesthetic provides a list of aesthetic values indexed by count/state:

```python
aes.Indexed(
    fill_color=["#e2e8f0", "#fbbf24", "#f97316", "#ef4444"],  # 4 states
    fill_opacity=[0.3, 0.5, 0.7, 1.0],
)
```

### Rendering Behavior (JavaScript Side)

Based on `InputMap.tsx`, IndexedAesthetic has special rendering rules:

1. **Base Layer**: IndexedAesthetic is applied to compute base aesthetics based on current count:
   ```javascript
   const indexedAes = resolveIndexedAesthetic(indexedData, count, cycle);
   baseAes = { ...baseAes, ...indexedAes };
   ```

2. **Selection Layer**: **SKIPPED** when using IndexedAesthetic
   ```javascript
   {!aesIndexed && /* selection layer rendering */ }
   ```
   This is intentional: IndexedAesthetic already shows state visually through indexed properties.

3. **Hover Layer**: **WORKS NORMALLY** on top of indexed aesthetics
   - For hovered regions, the indexed aesthetic is applied first
   - Then hover aesthetic is layered on top
   - If region is selected AND hovered but using IndexedAesthetic, selection layer is still skipped

### IndexedAesthetic Chain Summary

| Mode | Base | Select | Hover |
|------|------|--------|-------|
| Normal (Single/Multiple) | ✓ | ✓ (if selected) | ✓ (if hovered) |
| Indexed (Count/Cycle) | ✓ + Indexed[count] | **SKIPPED** | ✓ (if hovered) |

### Why This Design?

IndexedAesthetic semantically replaces the select layer:
- In Count mode, the "selection" is represented by the count value (0, 1, 2, ...)
- In Cycle mode, the "selection" cycles through n states
- Visual feedback comes from indexed properties, not a binary selected/not-selected aesthetic

The hover layer is preserved because hover is an ephemeral interaction state independent of the count/cycle value.

### Index 0 Behavior

**Important**: Index 0 is used as the base aesthetic for never-touched regions and count=0 regions. This ensures visual consistency:

```python
# Index 0 = "off" state, Index 1+ = various "on" states
aes.Indexed(fill_color=["#e5e7eb", "#3b82f6"])  # gray when 0, blue when 1
```

### Future Work: IndexedAesthetic Issues

The following issues need investigation in future iterations:

1. **RelativeExpr in hover aesthetic**: What happens when hover aesthetic uses `PARENT.stroke_width + 1`? The parent is the indexed base, which may have different stroke_width at different counts. Need to verify resolution is correct.

2. **Z-index for count=0 vs count>0**: Since IndexedAesthetic uses only the base layer, regions with count=0 and count>0 are rendered at the same z-index. This may cause partially hidden strokes (the standard SVG painter's algorithm issue). The selection/hover overlay layers exist partly to solve this problem for normal modes.

   Potential solutions:
   - Add a "selected" overlay for count>0 regions in indexed mode
   - Use different rendering approach for indexed regions
   - Accept the limitation and document it

## Implementation Status

### Completed (Python)

1. **`BaseAesthetic.resolve(parent)`** in `aes/_core.py`
   - Resolves MISSING values (inherit from parent)
   - Resolves RelativeExpr values (compute against parent)
   - Returns same type as self

2. **`ByState.resolve_for_region(wash_default, is_selected, is_hovered)`** in `aes/_core.py`
   - Full layer chain: wash_default → base → select → hover

3. **`WashConfig.apply(aes)`** in `wash/_core.py`
   - Applies user aesthetic on top of wash defaults
   - Returns fully resolved `ByState` with all MISSING and RelativeExpr values resolved

4. **Tests** - 47 tests in `test_aes_protocol.py`
   - `TestResolve` - 5 tests for `BaseAesthetic.resolve()`
   - `TestWashConfigApply` - 5 tests for `WashConfig.apply()`
   - `TestByStateResolveForRegion` - 6 tests for layer chain resolution

### Remaining Work

1. ~~**Create `shinymap/payload/` module** for payload building~~ ✅ DONE
   - `_build_aes_payload()` function created in `payload/_aes.py`
   - Serializes to v0.3 payload format
   - RelativeExpr serialized as `{"__relative__": true, "field": "...", "offset": N}`

2. ~~**Update `_input_map.py` and `_output_map.py`**~~ ✅ DONE
   - Uses new payload builder from `shinymap.payload`
   - Old conversion code removed

3. ~~**Move camelCase conversion to JavaScript**~~ ✅ DONE
   - `shinyBridge.ts` (TypeScript) with `snakeToCamelDeep()`
   - Python sends snake_case keys
   - JavaScript converts to camelCase on receive
   - Preserves underscore-prefixed keys (`__all`, `_metadata`, etc.)
   - Built with esbuild, minified to ~6KB

4. ~~**Update JavaScript components**~~ ✅ DONE
   - `getAesForRegion()` lookup function added to `types.ts`
   - `isAesPayload()` type guard for v0.3 format detection
   - `isRelativeExpr()` preserved for runtime resolution
   - `InputMap.tsx` and `OutputMap.tsx` updated to handle v0.3 format
   - Select highlight working correctly

5. ~~**Integration testing**~~ ✅ DONE
   - Playwright set up for browser integration tests
   - 9 integration tests for input_map behavior

### Compatibility

IndexedAesthetic does not participate in the resolution chain:
- Passed through to JavaScript unchanged
- JavaScript handles indexed rendering logic
