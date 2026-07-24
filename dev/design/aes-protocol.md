# Aesthetic (aes) Protocol

**Status**: IMPLEMENTED (core protocol complete; dump_table implemented as `StillLife.aes_table()`)
**Created**: 2025-12-30

This document defines the canonical representation and conversion protocols for aesthetic configuration in shinymap.

See also [aes-resolution.md](aes-resolution.md) for the runtime resolution architecture.

## Overview

Aesthetics control the visual appearance of SVG elements (fill, stroke, opacity, etc.) across different interaction states (base, select, hover) and element types (shape, line, text).

### Design Goals

1. **Type safety**: Internal representation uses typed dataclass objects
2. **User convenience**: API accepts both typed objects and dict shorthand
3. **Self-describing**: Dict representation includes type information for deserialization
4. **Round-trip safe**: `obj.to_dict()` → `from_dict(d)` preserves data
5. **Nested handling**: `from_dict()` recursively deserializes nested structures

## Type Hierarchy

```
Aesthetic (abstract)
├── Leaf Aesthetics (single element styling)
│   ├── ShapeAesthetic    (type: "shape")
│   ├── LineAesthetic     (type: "line")
│   ├── TextAesthetic     (type: "text")
│   ├── PathAesthetic     (type: "path")
│   └── IndexedAesthetic  (type: "indexed")
└── Container Types (grouping/composition)
    ├── ByState           (type: "bystate")
    ├── ByGroup           (type: "bygroup")
    └── ByType            (type: "bytype")
```

## Dict Protocol

**Every dict representation MUST include a `type` key** to enable self-describing deserialization.

The `type` key is preserved when sending to JavaScript (may be used for future type safety).

### Leaf Aesthetics

Leaf aesthetics define styling for a single element. They do not contain nested aesthetic objects.

#### ShapeAesthetic

For filled elements (rect, circle, polygon, path):

```python
{
    "type": "shape",
    "fill_color": "#3b82f6",
    "fill_opacity": 0.8,
    "stroke_color": "#1e40af",
    "stroke_width": 1.0,
    "stroke_dasharray": None,  # or "5,5" for dashed
    "non_scaling_stroke": False,
}
```

#### LineAesthetic

For stroke-only elements:

```python
{
    "type": "line",
    "stroke_color": "#94a3b8",
    "stroke_width": 0.5,
    "stroke_dasharray": "5,5",
    "non_scaling_stroke": False,
}
```

#### TextAesthetic

For text elements:

```python
{
    "type": "text",
    "fill_color": "#0f172a",
    "fill_opacity": 1.0,
    "stroke_color": "#ffffff",
    "stroke_width": 0.5,
}
```

#### PathAesthetic

For flexible path elements (can be filled or stroke-only):

```python
{
    "type": "path",
    "kind": "line",  # "shape" | "line" | "text" - for Wash default resolution
    "fill_color": None,
    "stroke_color": "#000000",
    "stroke_width": 1.0,
}
```

#### IndexedAesthetic

For index-based styling in Count/Cycle modes:

```python
{
    "type": "indexed",
    "fill_color": ["#e2e8f0", "#fbbf24", "#f97316", "#ef4444"],
    "fill_opacity": [0.3, 0.5, 0.7, 1.0],
    "stroke_color": "#000000",  # Single value applies to all indices
    "stroke_width": [0.5, 1.0, 1.5, 2.0],
}
```

### Container Types

Container types group aesthetics. They contain nested aesthetic objects that are recursively deserialized.

#### ByState

Groups aesthetics by interaction state:

```python
{
    "type": "bystate",
    "base": {"type": "shape", "fill_color": "#e2e8f0", ...},
    "select": {"type": "shape", "fill_color": "#3b82f6", ...},
    "hover": {"type": "shape", "stroke_width": 2.0, ...},
}
```

- `base`, `select`, `hover` are optional; missing keys mean MISSING (inherit defaults)
- `None` value means explicitly disabled (invisible/no effect)
- Values are leaf aesthetic dicts (recursively deserialized)

#### ByGroup

Groups aesthetics by region/group name:

```python
{
    "type": "bygroup",
    "__all": {  # Global default (lowest priority)
        "type": "bystate",
        "base": {"type": "shape", ...},
        "select": {...},
        "hover": {...},
    },
    "__shape": {...},  # Shape elements default
    "__line": {...},   # Line elements default
    "__text": {...},   # Text elements default
    "coastal": {       # Named group
        "type": "bystate",
        "base": {"type": "shape", "fill_color": "#0ea5e9"},
    },
    "region_a": {      # Individual region (can be leaf or ByState)
        "type": "shape",
        "fill_color": "#22c55e",
    },
}
```

Priority (highest to lowest):
1. Individual region ID
2. Named group from geometry metadata
3. Element type default (`__shape`, `__line`, `__text`)
4. Global default (`__all`)

Values can be:
- Leaf aesthetic dict (shorthand for base-only)
- ByState dict (full state configuration)
- `None` (explicitly disabled)

#### ByType

Groups aesthetics by element type (used by Wash):

```python
{
    "type": "bytype",
    "shape": {
        "type": "bystate",
        "base": {"type": "shape", ...},
        "select": {...},
        "hover": {...},
    },
    "line": {
        "type": "bystate",
        "base": {"type": "line", ...},
        ...
    },
    "text": {
        "type": "bystate",
        "base": {"type": "text", ...},
        ...
    },
}
```

## Conversion Methods

### to_dict() → dict

Converts object to dict representation:
- Returns snake_case keys (Python convention)
- **Always includes `type` key**
- Omits MISSING values (not set)
- Preserves None values (explicitly transparent/disabled)
- Container types recursively convert nested objects

```python
aes.Shape(fill_color="#fff").to_dict()
# → {"type": "shape", "fill_color": "#fff"}

aes.ByState(
    base=aes.Shape(fill_color="#fff"),
    hover=aes.Shape(stroke_width=2),
).to_dict()
# → {
#     "type": "bystate",
#     "base": {"type": "shape", "fill_color": "#fff"},
#     "hover": {"type": "shape", "stroke_width": 2},
# }
```

### from_dict(d) → object

Converts dict to typed object:
- Dispatches based on `type` key
- Container types recursively deserialize nested dicts
- Leaf types do not recurse (no nested aesthetics)
- Missing keys become MISSING
- Validates keys and warns on unknown

```python
from_dict({"type": "shape", "fill_color": "#fff"})
# → ShapeAesthetic(fill_color="#fff")

from_dict({
    "type": "bystate",
    "base": {"type": "shape", "fill_color": "#fff"},
    "hover": {"type": "shape", "stroke_width": 2},
})
# → ByState(
#     base=ShapeAesthetic(fill_color="#fff"),
#     hover=ShapeAesthetic(stroke_width=2),
# )

from_dict({
    "type": "bygroup",
    "__all": {"type": "shape", "fill_color": "#e2e8f0"},
    "coastal": {
        "type": "bystate",
        "base": {"type": "shape", "fill_color": "#0ea5e9"},
    },
})
# → ByGroup(
#     __all=ShapeAesthetic(fill_color="#e2e8f0"),
#     coastal=ByState(base=ShapeAesthetic(fill_color="#0ea5e9")),
# )
```

### Type Dispatch

A single `from_dict()` function handles all types:

```python
def from_dict(d: dict[str, Any]) -> Aesthetic:
    """Deserialize dict to appropriate aesthetic type."""
    type_map = {
        # Leaf types
        "shape": ShapeAesthetic.from_dict,
        "line": LineAesthetic.from_dict,
        "text": TextAesthetic.from_dict,
        "path": PathAesthetic.from_dict,
        "indexed": IndexedAesthetic.from_dict,
        # Container types
        "bystate": ByState.from_dict,
        "bygroup": ByGroup.from_dict,
        "bytype": ByType.from_dict,
    }
    aes_type = d.get("type")
    if aes_type is None:
        raise ValueError("Dict must have 'type' key")
    if aes_type not in type_map:
        raise ValueError(f"Unknown aesthetic type: {aes_type}")
    return type_map[aes_type](d)
```

## JavaScript Serialization

When sending to JavaScript, convert snake_case to camelCase:

```python
# Python internal (snake_case)
{"type": "shape", "fill_color": "#fff", "stroke_width": 1}

# JavaScript (camelCase)
{"type": "shape", "fillColor": "#fff", "strokeWidth": 1}
```

The `type` key is preserved in JavaScript output (may be used for future type safety).

Conversion happens at the serialization boundary in `wash/_util.py`:
- `_camel_props()` for top-level keys
- `_convert_aesthetic_dict()` for nested aesthetic dicts

## API Normalization

User-facing APIs accept both dict and object forms:

```python
# These are equivalent:
Wash(shape=aes.Shape(fill_color="#fff"))
Wash(shape={"type": "shape", "fill_color": "#fff"})

# For Wash parameters, type can be inferred from parameter name:
Wash(shape={"fill_color": "#fff"})  # type="shape" inferred

# These are equivalent:
aes.ByGroup(region_a=aes.Shape(fill_color="#fff"))
aes.ByGroup(region_a={"type": "shape", "fill_color": "#fff"})
```

Normalization happens at API boundaries:
- `Wash()` normalizes shape/line/text parameters (can infer type)
- `input_map()`/`output_map()` normalize `aes` parameter
- Internal code works with typed objects only

## RelativeExpr Serialization

`RelativeExpr` values (e.g., `PARENT.stroke_width + 2`) serialize to JSON:

```python
# Object
PARENT.stroke_width + 2

# to_dict() output
{"__relative__": True, "field": "stroke_width", "offset": 2}
```

**Note**: RelativeExpr is preserved in the v0.3 payload format and resolved by JavaScript at render time. This is because the actual parent value depends on the current interaction state (selected/hovered), which only JavaScript knows. See [aes-payload-v03.md](aes-payload-v03.md) for details.

## Sentinel Values

shinymap uses sentinel values in the `aes` namespace to control aesthetic inheritance and rendering behavior.

### Property-Level Sentinels

| Value | Meaning | Dict Representation |
|-------|---------|---------------------|
| `MISSING` | Not set, inherit from parent/default | Key omitted from dict |
| `None` | Explicitly transparent (e.g., no stroke) | `"key": null` |

```python
# MISSING - inherits default
aes.Shape(fill_color="#fff")  # stroke_color is MISSING
# → {"type": "shape", "fill_color": "#fff"}

# None - explicitly no stroke
aes.Shape(fill_color="#fff", stroke_color=None)
# → {"type": "shape", "fill_color": "#fff", "stroke_color": null}
```

### ByState-Level Sentinels

These sentinels control inheritance at the `base`/`select`/`hover` layer level:

| Sentinel | Direction | Meaning |
|----------|-----------|---------|
| `aes.copy_group` | ↑ (group) | Copy from parent group (region → group → __type → __all) |
| `aes.copy_parent` | ← (layer) | Copy from previous layer (base → select → hover) |
| `aes.disabled` | — | Skip overlay rendering (no z-index change) |

```python
aes.ByState(
    base=aes.Shape(fill_color="#e5e7eb"),
    select=aes.copy_group,   # inherit select from parent group
    hover=aes.copy_parent,   # visually same as select, rendered in hover overlay
)

aes.ByState(
    base=aes.Shape(fill_color="#e5e7eb"),
    select=aes.disabled,     # no selection overlay (stays at base z-index)
    hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
)
```

**Behavioral differences between `aes.copy_parent` and `aes.disabled`**:

| Aspect | `aes.copy_parent` | `aes.disabled` |
|--------|-------------------|----------------|
| Z-index | Rendered in overlay (higher) | Stays at base z-index |
| Border visibility | Fully visible on top of neighbors | May be hidden by adjacent regions |
| Opacity stacking | Overlay on top of base (less transparent) | Base opacity preserved |

The opacity stacking matters when `fill_opacity < 1`: with `aes.copy_parent`, the overlay renders on top of the base layer, making the region appear more opaque. With `aes.disabled`, no overlay is rendered, so the base transparency is preserved.

See [aes-resolution.md](aes-resolution.md) for detailed resolution architecture.

## Debugging: Aesthetic Resolution Table

For debugging purposes, aesthetics can be dumped as a flat table showing the resolved values for each (region, state) combination.

### Table Structure

Given geometry with regions and their metadata (group, element type), the table has one row per (region_id, state):

```
id,group,type,state,fill_color,fill_opacity,stroke_color,stroke_width,stroke_dasharray,non_scaling_stroke
shapeA,Group1,shape,base,#e2e8f0,1.0,#94a3b8,0.5,,false
shapeA,Group1,shape,select,#3b82f6,1.0,#1e40af,1.0,,false
shapeA,Group1,shape,hover,#e2e8f0,1.0,#94a3b8,1.5,,false
shapeB,Group1,shape,base,#e2e8f0,1.0,#94a3b8,0.5,,false
shapeB,Group1,shape,select,#3b82f6,1.0,#1e40af,1.0,,false
shapeB,Group1,shape,hover,#e2e8f0,1.0,#94a3b8,1.5,,false
lineA,,line,base,,,,0.5,5,5,false
lineA,,line,select,,,,1.0,,false
lineA,,line,hover,,,,1.5,,false
textA,,text,base,#0f172a,1.0,,,false
textA,,text,select,#1e40af,1.0,,,false
textA,,text,hover,#0f172a,1.0,,,false
```

### Resolution Order

There are two orthogonal dimensions to resolution:

**1. ByGroup Priority** (which aesthetic configuration applies to a region):

Priority (highest to lowest):
1. Individual region ID (`region_a`)
2. Named group from geometry metadata (`Group1`)
3. Element type default (`__shape`, `__line`, `__text`)
4. Global default (`__all`)

This is analogous to SQL WHERE clause specificity:
- `ByGroup(__all=...)` → `WHERE TRUE` (all rows)
- `ByGroup(__shape=...)` → `WHERE type = 'shape'`
- `ByGroup(Group1=...)` → `WHERE group = 'Group1'`
- `ByGroup(shapeA=...)` → `WHERE id = 'shapeA'`

**2. Layer Chain** (how base/select/hover resolve):

Once the applicable ByGroup entry is determined, the layers chain sequentially:
```
wash_default → base.resolve(wash_default) → resolved_base
             → select.resolve(resolved_base) → resolved_select (if selected)
             → hover.resolve(resolved_select or resolved_base) (if hovered)
```

See [aes-resolution.md](aes-resolution.md) for detailed resolution architecture.

### API

```python
from shinymap.aes import dump_table

# Returns CSV string
csv_str = dump_table(geometry, aes=my_aes, wash_config=my_wash)

# Returns pandas DataFrame (if pandas available)
df = dump_table(geometry, aes=my_aes, wash_config=my_wash, as_dataframe=True)

# Filter by criteria
df[df["group"] == "Group1"]  # All regions in Group1
df[df["type"] == "shape"]    # All shape elements
df[df["state"] == "hover"]   # All hover states
```

### Use Cases

1. **Debugging**: "Why is region X not the color I expect?"
2. **Verification**: Ensure all regions have expected styling before deployment
3. **Documentation**: Export styling decisions for design review
4. **Testing**: Assert resolved values in unit tests

## Implementation Checklist

- [x] Add `type` key to all `to_dict()` methods
- [x] Create top-level `from_dict()` function with type dispatch
- [x] Implement `from_dict()` for leaf types (no recursion):
  - [x] `ShapeAesthetic.from_dict()`
  - [x] `LineAesthetic.from_dict()`
  - [x] `TextAesthetic.from_dict()`
  - [x] `PathAesthetic.from_dict()`
  - [x] `IndexedAesthetic.from_dict()`
- [x] Implement recursive `from_dict()` for container types:
  - [x] `ByState.from_dict()` - deserializes base/select/hover
  - [x] `ByGroup.from_dict()` - deserializes group values
  - [x] `ByType.from_dict()` - deserializes shape/line/text
- [x] Update `Wash()` to use `from_dict()` for dict normalization
- [x] Add tests for round-trip conversion
- [x] Add tests for nested deserialization
- [ ] Implement `dump_table()` debugging utility:
  - [ ] CSV string output (no dependencies)
  - [ ] Optional pandas DataFrame output
  - [ ] Aesthetic resolution logic
