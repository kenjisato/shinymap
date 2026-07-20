# Props Structure Redesign

**Status**: IMPLEMENTED (v0.2.0)
**Created**: 2025-12-27

> **Note**: This document is kept for historical reference. The nested props
> structure (geometry, value, mode, aes, layers) is implemented in
> `wash/_input_map.py` and `wash/_output_map.py`.

## Problem Statement

Current props structure has grown organically and suffers from:
1. Mode-related options scattered at top level (`mode`, `cycle`, `max_selection`, `value`)
2. Aesthetic parameters mixed with geometric params (`aes_base`, `aes_select`, `aes_hover`, `aes_group`)
3. Layer params at different levels (`overlays`, `underlays`, `hidden`, `overlay_geometry`, `overlay_aesthetic`)
4. Legacy params that don't fit new API patterns

## Design Principles

1. **Mode defines behavior, not data** - `value` is top-level because it's data, not configuration
2. **User-owned value-to-index mapping** - library doesn't auto-scale; users compute indices explicitly
3. **Unified model** - input_map and output_map share the same structure

## Proposed Structure

### Python Side (before camelCase conversion)

```python
props = {
    # Core geometry
    "geometry": {"region_id": "path_data", ...},
    "tooltips": {"region_id": "tooltip text", ...},
    "view_box": "0 0 100 100",
    "geometry_metadata": {"viewBox": "...", "groups": {...}},

    # Data (top-level, independent of mode)
    "value": {"region_id": index, ...},  # Index into aesIndexed

    # Mode configuration (defines behavior)
    "mode": {
        "type": "single" | "multiple" | "cycle" | "count" | "display",
        # Type-specific options
        "allow_deselect": True,    # Single only
        "max_selection": 3,        # Multiple only
        "n": 4,                    # Cycle only
        # Indexed aesthetic
        "aes_indexed": {
            "type": "indexed",
            "value": {"fill_color": [...], ...}
        } | {
            "type": "by_group",
            "groups": {"group_name": {"fill_color": [...], ...}, ...}
        },
    },

    # Aesthetic configuration
    "aes": {
        "base": {"fill_color": "#fff", ...},
        "hover": {"stroke_width": 2, ...},
        "select": {"fill_color": "#blue", ...},
        "group": {"group_name": {"fill_color": "#red", ...}, ...},
    },

    # Layer configuration
    "layers": {
        "underlays": ["region_id", ...],
        "overlays": ["region_id", ...],
        "hidden": ["region_id", ...],
    },
}
```

### JavaScript Side (after camelCase conversion)

```typescript
interface MapProps {
  // Core geometry
  geometry: Record<string, string>;
  tooltips?: Record<string, string>;
  viewBox: string;
  geometryMetadata?: GeometryMetadata;

  // Data
  value?: Record<string, number>;  // Index into aesIndexed

  // Mode configuration
  mode: {
    type: "single" | "multiple" | "cycle" | "count" | "display";
    allowDeselect?: boolean;  // Single
    maxSelection?: number;    // Multiple
    n?: number;               // Cycle
    aesIndexed?: IndexedAestheticConfig;
  };

  // Aesthetics
  aes?: {
    base?: Aesthetic;
    hover?: Aesthetic;
    select?: Aesthetic;
    group?: Record<string, Aesthetic>;
  };

  // Layers
  layers?: {
    underlays?: string[];
    overlays?: string[];
    hidden?: string[];
  };
}
```

## Mode Types

| Type | Interactive | Value Semantics |
|------|-------------|-----------------|
| `single` | Click selects one | 0 = not selected, 1 = selected |
| `multiple` | Click toggles | 0 = not selected, 1 = selected |
| `cycle` | Click cycles | value % n → aesthetic index |
| `count` | Click increments | min(value, len-1) → aesthetic index |
| `display` | Hover only | value → aesthetic index (user-provided) |

## Value-to-Index Mapping

User is responsible for computing the index values:

```python
# Sequential scale example
from shinymap.aes.color import scale_sequential

# Option 1: Use helper to compute colors directly
fills = scale_sequential(counts, region_ids)
# Returns: {"region1": "#3b82f6", "region2": "#60a5fa", ...}

# Option 2: Compute indices for aesIndexed
def value_to_index(count: int, max_count: int = 5) -> int:
    return min(count, max_count)

values = {rid: value_to_index(counts.get(rid, 0)) for rid in region_ids}
# Returns: {"region1": 0, "region2": 3, "region3": 5, ...}
```

This gives users full control over the mapping strategy (clamping, wrapping, binning, etc.).

## Benefits

1. **Clear separation**: Data (`value`) vs behavior (`mode`) vs presentation (`aes`)
2. **Predictable**: No hidden auto-scaling or interpolation
3. **Flexible**: Users can implement any mapping strategy
4. **Unified**: Same structure for input and output maps

## Migration Strategy

### Phase 1: Python
- Update `base_input_map()` to emit new nested structure
- Update `base_output_map()` to use `mode.type = "display"`

### Phase 2: TypeScript
- Update `InputMap.tsx` and `OutputMap.tsx` to read from new structure
- Update `shinymap-shiny.js` initialization

### Phase 3: Cleanup
- Remove backward compatibility code
- Update documentation
