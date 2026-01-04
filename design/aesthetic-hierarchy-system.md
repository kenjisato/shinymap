# Aesthetic Hierarchy System: The Watercolor Model

**Status**: IMPLEMENTED (v0.2.0)
**Created**: 2025-12-25

> **Note**: This document is kept for historical reference. The wash() factory,
> ByState/ByType/ByGroup containers, and PARENT proxy are all implemented.
> For current architecture, see [aes-resolution.md](aes-resolution.md).
>
> **Update (v0.3.0)**: The `static_map` function mentioned in this document was
> implemented differently as the `StillLife` class. See [static-map-and-aes-dump.md](static-map-and-aes-dump.md)
> for the actual implementation which provides `StillLife.aes()` for aesthetic inspection
> and `StillLife.to_svg()` for static SVG export.

## Table of Contents

1. [Overview](#overview)
2. [The Configuration Matrix](#the-configuration-matrix)
3. [Container Classes](#container-classes)
4. [The Watercolor Metaphor](#the-watercolor-metaphor)
5. [Resolution Hierarchy](#resolution-hierarchy)
6. [API Design](#api-design)
7. [Implementation Plan](#implementation-plan)
8. [Migration Guide](#migration-guide)
9. [Alternative Approaches](#alternative-approaches)
10. [Future: Extending the Watercolor Metaphor](#future-extending-the-watercolor-metaphor)

---

## Overview

This document proposes a unified aesthetic hierarchy system for shinymap, inspired by watercolor painting techniques. The system introduces:

1. **`wash()` factory function** - Creates configured versions of `input_map`, `output_map`, `static_map`, and `render_map`
2. **Three container classes** - `aes.ByState`, `aes.ByType`, `aes.ByGroup` for composable configuration
3. **Unified `aes` parameter** - Single parameter for all aesthetic configuration
4. **Special group names** - `__all`, `__shape`, `__line`, `__text` for element-type-based styling
5. **`PARENT` proxy** - Relative value expressions like `PARENT.stroke_width + 1`

---

## The Configuration Matrix

The aesthetic system can be visualized as a matrix where rows are targets (groups/regions) and columns are interaction states:

```
              base        select      hover
__all         ?           ?           ?        <- global default
__shape       ?           ?           ?        <- shape elements default
__line        ?           ?           ?        <- line elements default
__text        ?           ?           ?        <- text elements default
groupA        ?           ?           ?        <- group-specific
groupB        ?           ?           ?
shapeA        ?           ?           ?        <- region-specific (shape)
lineA         ?           ?           ?        <- region-specific (line)
textA         ?           ?           ?        <- region-specific (text)
```

Each cell `?` can hold a `BaseAesthetic` (Shape, Line, or Text).

The three container classes provide different ways to fill this matrix:

| Container | Fills | Description |
|-----------|-------|-------------|
| `aes.ByState(base=, select=, hover=)` | One row (all columns for a single target) | "For this target, define its states" |
| `aes.ByGroup(__all=, groupA=, ...)` | One column across rows (one state for multiple targets) | "For this state, define which targets it affects" |
| `aes.ByType(shape=, line=, text=)` | The `__shape`, `__line`, `__text` rows | Used by `wash()` which doesn't know about groups |

---

## Container Classes

### `aes.ByState` - Row-wise Configuration

Groups aesthetics by interaction state for a single target:

```python
aes.ByState(
    base=aes.Shape(fill_color="#f0f9ff"),      # Default state
    select=aes.Shape(fill_color="#7dd3fc"),    # When selected
    hover=aes.Shape(stroke_width=PARENT.stroke_width + 2),  # When hovered
)
```

The first positional argument is `base`. If only `base` is needed, shorthand is allowed:
```python
aes.Shape(fill_color="#f0f9ff")  # Equivalent to ByState(base=aes.Shape(...))
```

### `aes.ByType` - Element Type Configuration

Groups aesthetics by element type (shape, line, text). Used by `wash()`:

```python
aes.ByType(
    shape=aes.ByState(base=..., hover=...),  # For shape elements
    line=aes.ByState(base=..., hover=...),   # For line elements
    text=aes.ByState(base=...),              # For text elements
)

# Shorthand when only base state is needed:
aes.ByType(
    shape=aes.Shape(fill_color="#e0f2fe"),
    line=aes.Line(stroke_color="#0369a1"),
    text=aes.Text(fill_color="#0c4a6e"),
)
```

### `aes.ByGroup` - Group-wise Configuration

Groups aesthetics by group/region name. Used by `input_map()` and `output_map()`:

```python
aes.ByGroup(
    __all=aes.ByState(base=..., hover=...),    # Default for all
    coastal=aes.Shape(fill_color="#bae6fd"),   # Override for coastal (base only)
    mountain=aes.ByState(                       # Full state config for mountain
        base=aes.Shape(fill_color="#d1fae5"),
        select=aes.Shape(fill_color="#6ee7b7"),
    ),
)
```

### Composition: ByGroup wraps ByState (Option A)

The design follows **"row-first"** composition: ByGroup wraps ByState.

```python
# Correct: ByGroup wraps ByState
aes=aes.ByGroup(
    __all=aes.ByState(base=aes.Shape(...), hover=aes.Shape(...)),
    groupA=aes.ByState(base=aes.Shape(...), select=aes.Shape(...)),
)
```

**Rationale:**
1. **Mental model**: Users think "I have group A, what should it look like?" not "I'm configuring hover, which groups need it?"
2. **Sparse matrix**: Most groups only override base, not all states. This is more compact.
3. **Partial overrides**: When groupA only needs a base color change, pass `Shape(...)` without wrapping in `ByState`.
4. **CSS consistency**: CSS groups properties by selector (element), not by property type.

---

## The Watercolor Metaphor

Traditional cartography used watercolor washes to paint maps. This technique provides a natural mental model for our aesthetic hierarchy:

| Watercolor Concept | Shinymap Concept | Description |
|-------------------|------------------|-------------|
| **Gesso** (white primer) | Library defaults | Minimal black/white defaults that underlie everything |
| **Wash** (base layer) | Factory defaults | Transparent layer that sets the overall tone |
| **Glaze** (transparent overlay) | Per-region/group aesthetics | Layers that add depth and color |
| **Lifting** (removing paint) | Selection state | Revealing different color when selected |
| **Wet edge** (active area) | Hover state | The region currently being interacted with |

Like watercolor, each layer is transparent and builds upon the previous one. The final appearance is the cumulative effect of all layers.

**Why "wash"?**
- A **wash** is the foundational layer in watercolor that establishes the painting's overall character
- It evokes "washing the canvas" - resetting to a clean, consistent base
- Maps have historically been painted with watercolor washes
- Short, memorable, and works as both noun ("the wash") and verb ("wash the canvas")

---

## Resolution Hierarchy

### Layer Stack (Bottom to Top)

```
LIBRARY_DEFAULT    ← Minimal black/white (like gesso primer)
      ↓ merge
WASH_DEFAULT       ← Factory-configured defaults (like base wash)
      ↓ merge
aes                ← Per-region/group aesthetics (like glazes)
      ↓ merge
aes_select         ← Selected state aesthetics
      ↓ merge
aes_hover          ← Hover state aesthetics (topmost layer)
```

Each layer **merges** with the previous one. Only explicitly set properties override; `MISSING` properties are inherited from below.

### Library Defaults (Gesso)

Minimal, black-and-white defaults that serve as the foundation:

```python
# In shinymap/relative.py (already implemented)
DEFAULT_SHAPE_AESTHETIC = ShapeAesthetic(
    fill_color="#e5e7eb",      # Gray-200
    fill_opacity=1.0,
    stroke_color="#000000",
    stroke_width=1.0,
)

DEFAULT_LINE_AESTHETIC = LineAesthetic(
    stroke_color="#000000",
    stroke_width=1.0,
)

DEFAULT_TEXT_AESTHETIC = TextAesthetic(
    fill_color="#000000",
    fill_opacity=1.0,
)

DEFAULT_HOVER_AESTHETIC = ShapeAesthetic(
    stroke_width=PARENT.stroke_width + 1,
)
```

### Wash Defaults (Factory Configuration)

The `wash()` factory allows apps to establish their own default palette:

```python
from shinymap import wash, aes

# Create configured map functions
wc = wash(
    shape_aes=aes.Shape(fill_color="#f0f9ff", stroke_color="#0369a1"),
    line_aes=aes.Line(stroke_color="#0369a1"),
    text_aes=aes.Text(fill_color="#0c4a6e"),
    hover_aes=aes.Shape(stroke_width=PARENT.stroke_width + 2),
    select_aes=aes.Shape(fill_color="#7dd3fc"),
)

# Use the configured functions
wc.input_map("region", geometry)

@wc.render_map
def my_map():
    return Map(geometry)
```

---

## API Design

### The `wash()` Factory

`wash()` configures element-type defaults using `aes.ByType`. It doesn't know about groups.

```python
def wash(
    *,
    # Element-type aesthetics (ByType wraps ByState)
    shape: ByState[ShapeAesthetic] | ShapeAesthetic | None | MissingType = MISSING,
    line: ByState[LineAesthetic] | LineAesthetic | None | MissingType = MISSING,
    text: ByState[TextAesthetic] | TextAesthetic | None | MissingType = MISSING,
) -> WashResult:
    """Create configured map functions with custom default aesthetics.

    The wash() function is like preparing a watercolor canvas - it sets
    the foundational layer that all maps in your app will build upon.

    Parameters accept:
    - MISSING: Inherit library defaults
    - None: Element type is invisible/disabled
    - Single aesthetic: Base state only (shorthand)
    - ByState: Full state configuration (base, select, hover)

    Returns an object with configured:
    - input_map
    - output_map
    - static_map
    - render_map
    """
    ...
```

**Usage:**

```python
from shinymap import wash, aes, PARENT

# Full form with ByState for each element type
wc = wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#f0f9ff", stroke_color="#0369a1"),
        select=aes.Shape(fill_color="#7dd3fc"),
        hover=aes.Shape(stroke_width=PARENT.stroke_width + 2),
    ),
    line=aes.ByState(
        base=aes.Line(stroke_color="#0369a1"),
        hover=aes.Line(stroke_width=PARENT.stroke_width + 1),
    ),
    text=aes.Text(fill_color="#0c4a6e"),  # base only shorthand
)

# Shorthand: just base aesthetics
wc = wash(
    shape=aes.Shape(fill_color="#f0f9ff"),
    line=aes.Line(stroke_color="#0369a1"),
)
```

### Return Type

```python
@dataclass
class WashResult:
    """Functions configured by wash()."""

    config: WashConfig

    input_map: Callable[..., Tag]
    output_map: Callable[..., Tag]
    static_map: Callable[..., Tag]
    render_map: Callable[..., Callable]
```

### Unified `aes` Parameter in `input_map()` / `output_map()`

The `aes` parameter accepts `aes.ByGroup` for group-wise configuration:

```python
# Type definition
AesSpec = ByGroup | ByState | BaseAesthetic | None | MissingType
```

**Usage patterns:**

```python
# Pattern 1: Single aesthetic for all regions (base only)
input_map("region", geometry, aes=aes.Shape(fill_color="#e5e7eb"))

# Pattern 2: Full state configuration for all regions
input_map("region", geometry, aes=aes.ByState(
    base=aes.Shape(fill_color="#e5e7eb"),
    select=aes.Shape(fill_color="#3b82f6"),
    hover=aes.Shape(stroke_width=PARENT.stroke_width + 2),
))

# Pattern 3: Per-group configuration with ByGroup
input_map("region", geometry, aes=aes.ByGroup(
    __all=aes.ByState(
        base=aes.Shape(fill_color="#e5e7eb"),
        hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
    ),
    coastal=aes.Shape(fill_color="#3b82f6"),  # base only shorthand
    mountain=aes.ByState(
        base=aes.Shape(fill_color="#10b981"),
        select=aes.Shape(fill_color="#6ee7b7"),
    ),
))
```

### Special Group Names in ByGroup

| Group Name | Applies To | Priority |
|------------|-----------|----------|
| `__all` | All regions regardless of type | Lowest |
| `__shape` | Shape elements (Circle, Rect, Path, Polygon, Ellipse) | Medium |
| `__line` | Line elements | Medium |
| `__text` | Text elements | Medium |
| `"group_name"` | Named groups from geometry metadata | High |
| `"region_id"` | Individual region IDs | Highest |

**Resolution order** (for regions in multiple groups):

```
__all → __shape/__line/__text → explicit groups (insertion order) → region_id
```

### Complete Example

```python
from shinymap import wash, aes, PARENT, Map, render_map

# Prepare the canvas with app-wide defaults (element-type configuration)
wc = wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#f8fafc", stroke_color="#94a3b8", stroke_width=1),
        select=aes.Shape(fill_color="#bfdbfe", stroke_color="#2563eb"),
        hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
    ),
    line=aes.ByState(
        base=aes.Line(stroke_color="#475569", stroke_width=1.5),
        hover=aes.Line(stroke_width=PARENT.stroke_width + 0.5),
    ),
    text=aes.Text(fill_color="#1e293b"),
)

# Use configured functions with group-specific overrides
app_ui = ui.page_fluid(
    wc.input_map("region", geometry, aes=aes.ByGroup(
        highlighted=aes.Shape(fill_color="#fef3c7"),  # Override for highlighted group
    )),
    wc.output_map("result"),
)

def server(input, output, session):
    @wc.render_map
    def result():
        return (
            Map(geometry)
            .with_aes(aes.ByGroup(
                selected=aes.Shape(fill_color="#10b981"),
            ))
        )
```

---

## Implementation Plan

### Phase 1: Container Classes

- [x] Create `StateAesthetics[T]` (renamed to `ByState`) in `_aesthetics.py`
- [ ] Create `ByType` container class
- [ ] Create `ByGroup` container class
- [ ] Export all containers from `aes.py` module
- [ ] Add `AesSpec` type alias

### Phase 2: wash() Factory

- [x] Create `WashResult` dataclass
- [x] Implement basic `wash()` factory function
- [ ] Update `wash()` to use new parameter names (`shape`, `line`, `text`)
- [ ] Implement wash-aware wrapper functions that merge config with call-site args

### Phase 3: Parameter Unification

- [ ] Add unified `aes` parameter to `input_map()`
- [ ] Add unified `aes` parameter to `output_map()`
- [ ] Update `MapBuilder.with_aes()` to accept `AesSpec`
- [ ] Update `MapPayload` dataclass
- [ ] Implement special group resolution (`__all`, `__shape`, `__line`, `__text`)

### Phase 4: TypeScript Updates

- [ ] Update `AestheticSpec` type in `types.ts`
- [ ] Add `ByState`, `ByType`, `ByGroup` type definitions
- [ ] Add special group resolution to `resolveAesthetic()`
- [ ] Update `InputMap` and `OutputMap` components

### Phase 5: Breaking Change Cleanup

- [ ] Remove `configure_theme()` function
- [ ] Remove deprecated parameter names (`aes_base`, `aes_group`)
- [ ] Rename `StateAesthetics` to `ByState` (or keep both as aliases)
- [ ] Update all examples
- [ ] Update documentation

### Phase 6: Testing

- [ ] Unit tests for `ByState`, `ByType`, `ByGroup`
- [ ] Unit tests for `wash()` factory
- [ ] Unit tests for group resolution order
- [ ] Integration tests with special groups
- [ ] Visual regression tests

---

## Migration Guide

### From Current API

```python
# Before (0.1.x)
from shinymap import input_map, configure_theme

configure_theme(default_aesthetic={"fill_color": "#f0f9ff"})

input_map("region", geometry,
    aes_base={"stroke_color": "#000"},
    aes_group={"coastal": {"fill_color": "#3b82f6"}},
    aes_hover={"stroke_width": 2},
)
```

```python
# After (0.2.x)
from shinymap import wash, aes, PARENT

# App-wide defaults via wash()
wc = wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#f0f9ff"),
        hover=aes.Shape(stroke_width=PARENT.stroke_width + 1),
    ),
)

# Per-map configuration via aes parameter
wc.input_map("region", geometry,
    aes=aes.ByGroup(
        __all=aes.Shape(stroke_color="#000"),
        coastal=aes.Shape(fill_color="#3b82f6"),
    ),
)
```

### Key Changes

| 0.1.x | 0.2.x |
|-------|-------|
| `configure_theme()` | `wash()` factory |
| `aes_base` + `aes_group` | Unified `aes` with `aes.ByGroup()` |
| Dict literals `{"fill_color": ...}` | `aes.Shape()`, `aes.Line()`, `aes.Text()` |
| Separate `aes_hover`, `aes_select` | Bundled in `aes.ByState(base=, select=, hover=)` |
| `shape_aes`, `line_aes`, `text_aes` | `shape`, `line`, `text` |

### Container Class Summary

| Container | Purpose | Used By |
|-----------|---------|---------|
| `aes.ByState(base=, select=, hover=)` | Bundle aesthetics for all interaction states | Everywhere |
| `aes.ByType(shape=, line=, text=)` | Bundle aesthetics for all element types | `wash()` |
| `aes.ByGroup(__all=, groupA=, ...)` | Bundle aesthetics for all groups/regions | `input_map()`, `output_map()` |

---

## Alternative Approaches

### Factory Naming

**Considered alternatives:**

| Name | Pros | Cons |
|------|------|------|
| `factory()` | Descriptive | Industrial, cold |
| `theme()` | Familiar (CSS) | Overloaded term |
| `base()` | Simple | Too generic |
| `canvas()` | Artistic | Conflicts with HTML `<canvas>` |
| `palette()` | Artistic | Should be reserved for colors |
| `atelier()` | Artistic, French | Obscure |
| `underpainting()` | Accurate | Too long |

**Decision**: `wash()` balances brevity, expressiveness, and thematic consistency.

### Container Composition Order

**Option A: ByGroup wraps ByState (row-first)** ✓ SELECTED
```python
aes=aes.ByGroup(
    __all=aes.ByState(base=..., hover=...),
    groupA=aes.ByState(base=..., select=...),
)
```
→ "For each group, define its states"

**Option B: ByState wraps ByGroup (column-first)**
```python
aes=aes.ByState(
    base=aes.ByGroup(__all=..., groupA=...),
    hover=aes.ByGroup(__all=...),
)
```
→ "For each state, define which groups it affects"

**Decision**: Option A selected because:
1. **Mental model**: Users think "I have group A, what should it look like?" not "I'm configuring hover, which groups need it?"
2. **Sparse matrix**: Most groups only override base, not all states. Option A is more compact.
3. **Partial overrides**: When groupA only needs a base color change, pass `Shape(...)` without wrapping.
4. **CSS consistency**: CSS groups properties by selector (element), not by property type.

### Parameter Structure

**Alternative 1: Separate parameters preserved**
```python
wash(
    aes_base={...},
    aes_group={...},  # Separate
)
```
- **Rejected**: Adds complexity, users must learn when to use which

**Alternative 2: Nested structure**
```python
wash(
    aes={
        "base": {...},
        "groups": {...},
    }
)
```
- **Rejected**: Extra nesting, harder to type

**Decision**: Container classes (`ByState`, `ByType`, `ByGroup`) with special group names (`__all`, `__shape`, etc.)

### State Aesthetic Structure

**Alternative: Keep states simple**
```python
# Only single aesthetic allowed
aes_hover=aes.Shape(...)
```
- **Rejected**: Can't have different hover for lines vs shapes

**Decision**: States bundled in `ByState` container for consistency and composability.

---

## Future: Extending the Watercolor Metaphor

The watercolor metaphor could be extended throughout the library for naming consistency. This section captures ideas for future refactoring (not part of v0.2.x scope).

### Potential Renamings

| Current Name | Watercolor Alternative | Rationale |
|--------------|------------------------|-----------|
| `aes` module | `pigment` | The coloring material |
| `aes.Shape()` | `pigment.Shape()` | Consistent with metaphor |
| `geometry` | `outline`, `sketch`, `linework` | The drawn outlines of shapes (not mathematical "geometry" or earth-related "geo") |
| `overlays` | `details` or `drybrush` | Fine details added on top |
| `underlays` | `underwash` | Layer beneath the main wash |
| `fill_color` | `tint` | Diluted color application |
| `stroke_color` | `ink` | Edge definition |
| `PARENT` | `BENEATH` or `UNDER` | What's underneath this layer |

**Note on `geometry`**: The current name is somewhat misleading - "geo" means earth and "geometry" sounds mathematical. Since we're really describing the **outlines/shapes** that define regions, alternatives like `outline`, `sketch`, or `linework` better capture the concept (and fit the watercolor metaphor where you first sketch the outline before applying washes).

### Watercolor Technique Vocabulary

For reference, watercolor techniques that might inspire future naming:

- **Wet-on-wet**: Applying paint to wet paper (blending, soft edges)
- **Wet-on-dry**: Applying paint to dry paper (crisp edges)
- **Glazing**: Transparent layers over dried paint
- **Lifting**: Removing paint to reveal lighter areas
- **Blooming**: Paint spreading into wet areas
- **Granulation**: Texture from pigment settling
- **Salt technique**: Texture effects
- **Masking**: Preserving white areas (like `hidden` regions?)

### Decision Criteria

Before adopting more watercolor terms, consider:

1. **Discoverability**: Will users find `pigment.Shape()` or expect `aes.Shape()`?
2. **Consistency**: If we use `wash()`, does `aes` feel out of place?
3. **Documentation burden**: More metaphor = more explaining
4. **IDE experience**: Short, common words autocomplete better

### Recommendation

Start with `wash()` as the single watercolor-inspired name. Observe how users respond. If the metaphor resonates, consider extending it in a future major version (v1.0 or beyond). The current `aes` module is well-established in data visualization (ggplot2, plotnine) and may be worth preserving for familiarity.

---

## References

- [PARENT proxy implementation](../packages/shinymap/python/src/shinymap/relative.py)
- [Current aesthetic system](./underlay-and-aesthetics.md)
- [Polymorphic elements design](./polymorphic-elements-svgpy.md)

---

**End of Design Document**

*This document describes the target API for version 0.2.x.*
