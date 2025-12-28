# Mode Classes and Indexed Aesthetic Design

**Created**: 2025-12-26
**Status**: Draft proposal

## Problem Statement

### Current Issues

1. **JavaScript-driven count styling**: Count-based colors are computed in JS, hard to customize from Python
2. **Z-index conflict**: Base layer renders count colors, but selection overlay paints `aesSelect` on top
3. **Dual aesthetic sources**: Users must ensure `aesBase` matches count palette[0] for consistent appearance
4. **Limited count/cycle customization**: No Python API to define palettes or opacity ramps

### What Works Well

The simple string modes work great for the majority of use cases:

```python
input_map("id", geometry, mode="single")
input_map("id", geometry, mode="multiple")
```

These should remain the primary API - minimal and clean.

## Proposed Solution

### Shiny-Aligned Naming

Following Shiny's input naming conventions for familiar API. Since `input_map` displays all options visually (like radio buttons/checkboxes), not hidden in a dropdown:

| Shiny UI | shinymap | Selection behavior |
|----------|----------|-------------------|
| `input_radio_buttons` | `input_radio_buttons` | Single selection → `str \| None` |
| `input_checkbox_group` | `input_checkbox_group` | Multiple selection → `list[str]` |

These are **sugar functions** (aliases) for `input_map(mode=...)`:

```python
from shinymap import input_radio_buttons, input_checkbox_group

# Single selection (visual radio buttons)
input_radio_buttons("region", geometry)
# Equivalent to: input_map("region", geometry, mode="single")

# Multiple selection (visual checkbox group)
input_checkbox_group("regions", geometry)
# Equivalent to: input_map("regions", geometry, mode="multiple")
```

**Note**: Count/Cycle modes have no Shiny equivalent, so they remain as `input_map(mode=...)`.

### Two-Tier API

**Tier 1: Simple API (permanent, primary)**

```python
# Sugar functions (recommended for common cases)
input_radio_buttons("id", geometry)    # single selection
input_checkbox_group("id", geometry)   # multiple selection

# Or explicit mode parameter
input_map("id", geometry, mode="single")
input_map("id", geometry, mode="multiple")
```

**Tier 2: Mode classes (advanced, for power users)**

```python
from shinymap import input_map, aes
from shinymap.mode import Single, Multiple, Cycle, Count

# Multiple with selection limit
input_map(
    "regions",
    geometry,
    mode=Multiple(max_selection=3),
)

# Cycle mode with custom palette
input_map(
    "survey",
    geometry,
    mode=Cycle(
        n=4,
        aes=aes.Indexed(
            fill_color=["#e2e8f0", "#ef4444", "#eab308", "#22c55e"],
        ),
    ),
)

# Count mode with opacity gradient
input_map(
    "clicks",
    geometry,
    mode=Count(
        aes=aes.Indexed(
            fill_color="#f97316",
            fill_opacity=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        ),
    ),
)
```

### Mode Classes (Advanced API)

```python
from dataclasses import dataclass

@dataclass
class Single:
    """Single selection mode with customization options.

    Args:
        selected: Initially selected region ID.
        allow_deselect: If True, clicking selected region deselects it.
        aes: Two-state aesthetic [unselected, selected].
    """
    selected: str | None = None
    allow_deselect: bool = True
    aes: aes.Indexed | None = None

@dataclass
class Multiple:
    """Multiple selection mode with customization options.

    Args:
        selected: Initially selected region IDs.
        max_selection: Maximum selections allowed.
        aes: Two-state aesthetic [unselected, selected].
    """
    selected: list[str] | None = None
    max_selection: int | None = None
    aes: aes.Indexed | None = None

@dataclass
class Cycle:
    """Cycle mode - finite state cycling (e.g., traffic light survey).

    Args:
        n: Number of states (e.g., 4 for gray→red→yellow→green→gray).
        values: Initial state per region {id: state_index}.
        aes: Indexed aesthetic - can be aes.Indexed (global) or aes.ByGroup
             wrapping aes.Indexed for per-group palettes.
    """
    n: int
    values: dict[str, int] | None = None
    aes: aes.Indexed | aes.ByGroup | None = None

@dataclass
class Count:
    """Count mode - unbounded counting.

    Args:
        values: Initial counts per region {id: count}.
        max_count: Optional cap for aesthetic scaling (clamping).
        aes: Indexed aesthetic - can be aes.Indexed (global) or aes.ByGroup
             wrapping aes.Indexed for per-group palettes.
    """
    values: dict[str, int] | None = None
    max_count: int | None = None
    aes: aes.Indexed | aes.ByGroup | None = None
```

### aes.Indexed

```python
@dataclass
class Indexed:
    """Index-based aesthetic for multi-state modes.

    Values are indexed by count/state:
    - For Single/Multiple: index 0 = off, index 1 = on
    - For Cycle mode: index = count % n (wrapping)
    - For Count mode: index = min(count, len(list) - 1) (clamping)

    IMPORTANT: aes.Indexed[0] is used as the base aesthetic for ALL regions.
    This ensures never-touched regions and count=0 regions look the same.

    Args:
        fill_color: Single color or list of colors indexed by state.
        fill_opacity: Single value or list of opacities (0.0-1.0).
        stroke_color: Optional stroke color(s).
        stroke_width: Optional stroke width(s).
        stroke_dasharray: Optional dash pattern(s) for line styling.
    """
    fill_color: str | list[str] | None = None
    fill_opacity: float | list[float] | None = None
    stroke_color: str | list[str] | None = None
    stroke_width: float | list[float] | None = None
    stroke_dasharray: str | list[str] | None = None
```

### Per-Group Indexed Aesthetics

For per-group palettes (e.g., color coordination quiz), wrap `aes.Indexed` in `aes.ByGroup`:

```python
# Each group gets a different indexed palette
aes.ByGroup(
    question_1=aes.Indexed(fill_color=["#bfdbfe", "#2563eb"]),  # blue
    question_2=aes.Indexed(fill_color=["#bbf7d0", "#16a34a"]),  # green
    question_3=aes.Indexed(fill_color=["#fecaca", "#dc2626"]),  # red
)
```

Resolution priority (highest to lowest):
1. Region ID match in ByGroup → use that group's Indexed palette
2. Group name match in ByGroup → use that group's Indexed palette
3. `__all` key in ByGroup → use as fallback Indexed palette
4. Mode class's default Indexed → use if aes.ByGroup not provided

### Examples

```python
from shinymap import input_map, aes
from shinymap.mode import Single, Multiple, Cycle, Count
from shinymap.palettes import HUE_CYCLE_4

# Multiple with selection limit
input_map(
    "regions",
    geometry,
    mode=Multiple(max_selection=3),
)

# Traffic light survey (4 states)
input_map(
    "rating",
    geometry,
    mode=Cycle(
        n=4,
        aes=aes.Indexed(fill_color=HUE_CYCLE_4),
    ),
)

# Heat map with opacity gradient (using linspace)
from shinymap.utils import linspace

input_map(
    "clicks",
    geometry,
    mode=Count(
        aes=aes.Indexed(
            fill_color="#f97316",
            fill_opacity=linspace(0.0, 1.0, num=6),
        ),
    ),
)

# Line toggle (solid/dashed)
input_map(
    "routes",
    geometry,
    mode=Cycle(
        n=2,
        aes=aes.Indexed(
            stroke_color=["#94a3b8", "#3b82f6"],
            stroke_width=[0.5, 2],
            stroke_dasharray=["4 2", ""],  # dashed → solid
        ),
    ),
)

# Per-group palettes (e.g., color coordination quiz)
# Each group has different hue: unselected=light, selected=saturated
input_map(
    "quiz",
    geometry,
    mode=Cycle(
        n=2,
        aes=aes.ByGroup(
            question_1=aes.Indexed(fill_color=["#bfdbfe", "#2563eb"]),  # blue
            question_2=aes.Indexed(fill_color=["#bbf7d0", "#16a34a"]),  # green
            question_3=aes.Indexed(fill_color=["#fecaca", "#dc2626"]),  # red
        ),
    ),
)
```

### Utility Functions

Utilities live in `shinymap.utils` subpackage (not the root namespace):

```python
from shinymap.utils import linspace

# Generate evenly spaced values (like numpy.linspace)
linspace(start=0.2, stop=1.0, num=5)
# => [0.2, 0.4, 0.6, 0.8, 1.0]

# Works for any numeric aesthetic property
linspace(start=0.5, stop=3.0, num=6)  # stroke widths
# => [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
```

### Pre-defined Palettes

```python
from shinymap.palettes import (
    HUE_CYCLE_4,        # gray, red, yellow, green
    SEQUENTIAL_ORANGE,  # light to dark orange
    SEQUENTIAL_BLUE,    # light to dark blue
)
```

## Rendering Architecture

### Key Insight: aes.Indexed[0] as Base

For Mode classes with `aes.Indexed`, `aes.Indexed[0]` is used for the **base layer**:

| State | Aesthetic Used |
|-------|----------------|
| Never touched | `aes.Indexed[0]` |
| count = 0 | `aes.Indexed[0]` |
| count > 0 | `aes.Indexed[count]` (on state layer) |

This eliminates the "dual aesthetic" problem.

### Layer Rendering by Mode

| Mode | Base Layer | State/Selection Layer |
|------|------------|----------------------|
| `"single"` | `aesBase` | `aesSelect` |
| `"multiple"` | `aesBase` | `aesSelect` |
| `Single()` | `aes.Indexed[0]` | `aes.Indexed[1]` |
| `Multiple()` | `aes.Indexed[0]` | `aes.Indexed[1]` |
| `Cycle(n)` | `aes.Indexed[0]` | `aes.Indexed[count % n]` |
| `Count()` | `aes.Indexed[0]` | `aes.Indexed[min(count, len-1)]` |

**Note**: String modes use `aesBase`/`aesSelect` from wash. Mode classes use `aes.Indexed`.

## Implementation Checklist

### Python Side

- [ ] Add `input_radio_buttons()` sugar function (alias for `input_map(mode="single")`)
- [ ] Add `input_checkbox_group()` sugar function (alias for `input_map(mode="multiple")`)
- [ ] Create `shinymap/mode.py` with Mode classes (`Single`, `Multiple`, `Cycle`, `Count`)
- [ ] Add `IndexedAesthetic` dataclass in `_aesthetics.py` (internal implementation)
- [ ] Add `aes.Indexed()` factory function in `aes.py` (public API)
- [ ] Create `shinymap/utils/__init__.py` with `linspace()` function
- [ ] Add pre-defined palettes in `palettes.py`
- [ ] Update `base_input_map()` to accept Mode classes alongside strings
- [ ] Serialize `aesIndexed` prop to JavaScript

**File structure note**: Following existing patterns:
- `_aesthetics.py` contains dataclass definitions (internal)
- `aes.py` contains factory functions with IDE-friendly signatures (public API)

### TypeScript Side

- [ ] Add `IndexedAesthetic` type in `types.ts`
- [ ] Add `aesIndexed` prop to `InputMapProps`
- [ ] Implement `resolveIndexedAesthetic()` function
- [ ] Update base layer: use `aesIndexed[0]` when Mode class is used
- [ ] Update state layer: use `aesIndexed[state]` for state > 0
- [ ] Remove hardcoded count styling from `shinymap-shiny.js`

### Testing

- [ ] Unit tests for Mode class serialization
- [ ] Unit tests for `aes.Indexed` serialization
- [ ] Unit tests for `linspace()`
- [ ] Integration test: Cycle mode with custom palette
- [ ] Integration test: Count mode with opacity ramp
- [ ] Visual test: verify base layer uses `aesIndexed[0]`

### Documentation

- [ ] Update SPEC.md with Mode classes API
- [ ] Update SPEC.md with `aes.Indexed` API
- [ ] Add examples for each Mode class
- [ ] Document palettes

## Resolved Questions

### Q1: Never-touched vs count=0 distinction?

**Decision**: No distinction. Both show `aes.Indexed[0]`.

### Q2: Should string modes be deprecated?

**Decision**: No! String modes (`"single"`, `"multiple"`) are permanent and primary. They cover the majority of use cases. Mode classes are for advanced customization.

### Q3: Where does max_selection go?

**Decision**: In `Multiple()` class, not in simple API. Simple API is truly minimal.

### Q4: Why separate `_aesthetics.py` and `aes.py`?

**Decision**: Following existing codebase pattern:
- `_aesthetics.py`: Internal module with dataclass definitions (`ShapeAesthetic`, `LineAesthetic`, etc.)
- `aes.py`: Public API with factory functions (`aes.Shape()`, `aes.Line()`) that provide better IDE autocomplete

This separation allows:
1. Clean public API with function signatures tailored for discoverability
2. Internal implementation details hidden in underscore-prefixed modules
3. Factory functions can add validation or defaults without polluting dataclass definitions

### Q5: Why `linspace` instead of `opacity_ramp`?

**Decision**: `linspace` (from numpy convention) is more generic:
- Works for any numeric property (opacity, stroke_width, etc.)
- Familiar to users with numpy/scipy background
- Name clearly describes what it does: "linear spacing"

The old name `opacity_ramp` was misleading because:
- "ramp" suggests slope/gradient, not discrete values
- Implied it only worked for opacity

## Future Work

### Group Mode

Checkbox group behavior where selecting one region auto-deselects others in the same group.

```python
# Future API concept
input_map(
    "preference",
    geometry,
    mode=Group(
        groups={
            "color": ["red", "green", "blue"],
            "size": ["small", "medium", "large"],
        },
        selected={"color": "red", "size": "medium"},
    ),
)
```
