# Aesthetic Payload Format v0.3

**Status**: Proposed
**Created**: 2025-12-30
**Supersedes**: Parts of [props-structure.md](props-structure.md), [aesthetic-hierarchy-system.md](aesthetic-hierarchy-system.md)

This document describes the new aesthetic payload format for v0.3, designed to simplify JavaScript code by moving all resolution logic to Python.

## Design Goals

1. **Minimal JS logic**: JS does lookup + RelativeExpr resolution only
2. **Compact payload**: Group regions with identical styling to reduce payload size
3. **Complete entries**: Each entry contains full `{base, select, hover}` - MISSING and None resolved, but RelativeExpr preserved
4. **Clear contract**: Simple matching algorithm on JS side, RelativeExpr resolution at render time

## Payload Format

```json
{
  "region1": {"base": {...}, "select": {...}, "hover": {...}},
  "group1": {"base": {...}, "select": {...}, "hover": {...}},
  "__shape": {"base": {...}, "select": {...}, "hover": {...}},
  "__all": {"base": {...}, "select": {...}, "hover": {...}},
  "_metadata": {
    "group1": ["region3", "region4"],
    "__shape": ["region1", "region2", "region3", "region4", "region5"],
    "__line": ["line1", "line2"],
    "__text": ["label1"]
  }
}
```

### Entry Types

| Key | Description |
|-----|-------------|
| `region_id` | Explicit styling for individual region (highest priority) |
| `group_name` | Shared styling for named group |
| `__shape` | Default for all shape elements |
| `__line` | Default for all line elements |
| `__text` | Default for all text elements |
| `__all` | Global default (lowest priority) |
| `_metadata` | Maps group/type names to member region IDs |

### Entry Structure

Every entry (except `_metadata`) is a complete ByState:

```json
{
  "base": {
    "fill_color": "#e5e7eb",
    "fill_opacity": 1.0,
    "stroke_color": "#94a3b8",
    "stroke_width": 1.0,
    "stroke_dasharray": null,
    "non_scaling_stroke": false
  },
  "select": {
    "fill_color": "#3b82f6",
    "stroke_width": {"__relative__": true, "field": "stroke_width", "offset": 0.5},
    ...
  },
  "hover": {
    "stroke_width": {"__relative__": true, "field": "stroke_width", "offset": 1},
    ...
  }
}
```

**Key points**:
- No `MISSING` - all group inheritance resolved in Python
- No `None` layer copying - resolved in Python
- **RelativeExpr preserved** - serialized as `{"__relative__": true, "field": "...", "offset": N}` for JS runtime resolution

## Three-Phase Architecture

### Phase 1: Resolution (Python)

Python resolves aesthetics along two dimensions (see [aes-resolution.md](aes-resolution.md) for details):

- **Group dimension (↑)**: `MISSING` inherits from parent group
- **Layer dimension (←)**: `None` copies from previous layer (base → select → hover)
- **RelativeExpr**: **NOT resolved** - preserved for JavaScript

**Result**: ByGroup where MISSING and None are resolved, but RelativeExpr remains.

### Phase 2: Payload Building (Python)

Serialization of resolved ByGroup to JSON:

- Convert each ByState to `{base, select, hover}` dict
- Serialize RelativeExpr as `{"__relative__": true, "field": "...", "offset": N}`
- Add `_metadata` for group membership lookup

**Result**: Each entry is complete (no MISSING/None), but may contain RelativeExpr.

### Phase 3: JavaScript (Lookup + RelativeExpr Resolution)

JS performs:

1. **Lookup** in reverse priority order:
   ```
   region_id → group_name → __shape/__line/__text → __all
   ```
   First match wins - return immediately. **No merging.**

2. **RelativeExpr resolution** at render time:
   - For each property with `{"__relative__": true, ...}`, compute against actual parent
   - `select` properties: parent is `base`
   - `hover` properties: parent is `select` if selected, else `base`

This split ensures JavaScript knows the actual parent based on current interaction state.

### JS Lookup Algorithm

```typescript
function getAesForRegion(
  regionId: string,
  elementType: 'shape' | 'line' | 'text',
  aes: AesPayload
): ByStateAes {
  // 1. Check explicit region entry
  if (aes[regionId]) return aes[regionId];

  // 2. Check named groups (from _metadata)
  const metadata = aes._metadata || {};
  for (const [groupName, members] of Object.entries(metadata)) {
    if (groupName.startsWith('__')) continue; // Skip type defaults
    if (members.includes(regionId) && aes[groupName]) {
      return aes[groupName];
    }
  }

  // 3. Check element type default
  const typeKey = `__${elementType}` as const;
  if (aes[typeKey]) return aes[typeKey];

  // 4. Check global default
  if (aes.__all) return aes.__all;

  // 5. Use library defaults
  return DEFAULT_BYSTATE;
}
```

### JS RelativeExpr Resolution

```typescript
interface RelativeExpr {
  __relative__: true;
  field: string;
  offset: number;
}

function isRelativeExpr(value: unknown): value is RelativeExpr {
  return typeof value === 'object' && value !== null && '__relative__' in value;
}

function resolveRelativeValue(expr: RelativeExpr, parent: LeafAesthetic): number {
  const parentValue = parent[expr.field as keyof LeafAesthetic];
  if (typeof parentValue !== 'number') {
    throw new Error(`Cannot resolve relative expr: ${expr.field} is not a number`);
  }
  return parentValue + expr.offset;
}

// At render time, for each region:
function resolveAesForState(
  byState: ByStateAes,
  isSelected: boolean,
  isHovered: boolean
): LeafAesthetic {
  const base = byState.base;

  // Resolve select layer against base
  const select = isSelected && byState.select
    ? resolveLayer(byState.select, base)
    : null;

  // Resolve hover layer against current state (select if selected, else base)
  const parent = select ?? base;
  const hover = isHovered && byState.hover
    ? resolveLayer(byState.hover, parent)
    : null;

  // Return appropriate aesthetic based on state
  return hover ?? select ?? base;
}

function resolveLayer(layer: LeafAesthetic, parent: LeafAesthetic): LeafAesthetic {
  const resolved: LeafAesthetic = { ...layer };
  for (const [key, value] of Object.entries(layer)) {
    if (isRelativeExpr(value)) {
      resolved[key] = resolveRelativeValue(value, parent);
    }
  }
  return resolved;
}
```

## Example

### User Input (Python)

```python
wc = Wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#e5e7eb", stroke_width=1.0),
        hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
    )
)

wc.input_map("map", geometry, aes=aes.ByGroup(
    coastal=aes.Shape(fill_color="#3b82f6"),
    region4=aes.Shape(fill_color="#ff0000"),
))
```

### Generated Payload

```json
{
  "region4": {
    "base": {"fill_color": "#ff0000", "stroke_width": 1.0, ...},
    "select": null,
    "hover": {"stroke_width": {"__relative__": true, "field": "stroke_width", "offset": 1}, ...}
  },
  "coastal": {
    "base": {"fill_color": "#3b82f6", "stroke_width": 1.0, ...},
    "select": null,
    "hover": {"stroke_width": {"__relative__": true, "field": "stroke_width", "offset": 1}, ...}
  },
  "__shape": {
    "base": {"fill_color": "#e5e7eb", "stroke_width": 1.0, ...},
    "select": null,
    "hover": {"stroke_width": {"__relative__": true, "field": "stroke_width", "offset": 1}, ...}
  },
  "_metadata": {
    "coastal": ["region1", "region2", "region3"],
    "__shape": ["region1", "region2", "region3", "region4", "region5"]
  }
}
```

Note: `hover.stroke_width` is a RelativeExpr, not a resolved value. JavaScript resolves it at render time against the current state's parent (base or select).

### JS Lookups

- `region4` → finds `"region4"` entry → returns red fill
- `region1` → no entry → checks groups → `coastal` matches → returns blue fill
- `region5` → no entry → no group match → `__shape` matches → returns gray fill

## Comparison with v0.2

### v0.2 (Current)

```json
{
  "base": {...},
  "select": {...},
  "hover": {...},
  "group": {
    "coastal": {...},
    "region4": {...}
  }
}
```

- JS must merge `group` entries with `base`
- JS must resolve `RelativeExpr` in hover
- Group entries are partial (only override properties)

### v0.3 (Proposed)

```json
{
  "region4": {"base": ..., "select": ..., "hover": ...},
  "coastal": {"base": ..., "select": ..., "hover": ...},
  "__shape": {"base": ..., "select": ..., "hover": ...},
  "_metadata": {...}
}
```

- JS does lookup + RelativeExpr resolution only
- MISSING and None pre-resolved in Python
- RelativeExpr preserved in payload for JS runtime resolution
- Each entry is complete (no partial overrides)

## Benefits

1. **Simpler JS**: Lookup + RelativeExpr only, no MISSING/None resolution
2. **Correct hover behavior**: JS resolves RelativeExpr against actual parent (base or select)
3. **Testable**: MISSING/None resolution in Python, easy to unit test
4. **Debuggable**: Can dump resolved payload to see exactly what JS receives
5. **Compact**: Groups share entries (not repeated per-region)
6. **Extensible**: Easy to add new group types

## Migration

### Breaking Changes

- `aes` payload structure changes completely
- JS components must be updated to use new lookup logic
- RelativeExpr format unchanged but now used in complete entries (not partial overrides)

### Compatibility

- Python API (`ByGroup`, `ByState`, etc.) unchanged
- User code doesn't need changes
- Only internal serialization changes
- RelativeExpr continues to work (JS already has resolution logic)

## Implementation Plan

1. [ ] Create `shinymap/payload/` module with `_build_aes_payload()` function
2. [ ] Add JS `getAesForRegion()` lookup function to `types.ts`
3. [ ] Keep `RelativeExpr` handling in JS (for runtime resolution)
4. [ ] Add `resolveAesForState()` to resolve RelativeExpr at render time
5. [ ] Update `InputMap.tsx` to use new lookup + resolution
6. [ ] Update `OutputMap.tsx` to use new lookup + resolution
7. [ ] Remove old `_convert_aes_to_dict()` from Python
8. [ ] Add tests for payload generation
9. [ ] Add tests for JS lookup and RelativeExpr resolution

## Related Documents

- [aes-resolution.md](aes-resolution.md) - Python resolution logic
- [aes-protocol.md](aes-protocol.md) - Dict serialization protocol
- [restructuring-toward-v0.3.md](restructuring-toward-v0.3.md) - Module layering goals
