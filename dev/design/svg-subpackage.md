# Design: Move SVG Elements to `shinymap.svg` Subpackage

**Status**: Implemented
**Created**: 2026-01-04

## Problem

Currently, SVG element classes (Circle, Path, Line, etc.) are exported from `shinymap.outline`:

```python
from shinymap.outline import Circle, Path, Line, Outline
```

This mixing feels awkward because:
1. `Outline` is a shinymap-specific container class
2. `Circle`, `Path`, etc. are extensions of the `svg` library's element classes
3. The relationship to `svg` library is hidden

## Proposed Solution

Create a dedicated `shinymap.svg` subpackage that makes the extension relationship explicit:

```python
from shinymap import svg

circle = svg.Circle(cx=10, cy=10, r=20)
```

Or with direct imports:
```python
from shinymap.svg import Circle, Path, Line
```

This design:
- Conveys that `shinymap.svg` extends the `svg` library
- Separates concerns: `outline` for Outline, `svg` for elements
- Matches user mental model: "I'm working with SVG elements"

## File Structure

### Current
```
shinymap/
├── outline/
│   ├── __init__.py          # Exports Outline + Circle, Path, etc.
│   ├── _elements.py          # Element class definitions
│   ├── _element_mixins.py    # BoundsMixin, JSONSerializableMixin
│   └── ...
```

### Proposed
```
shinymap/
├── svg/
│   ├── __init__.py          # Exports Circle, Path, Line, etc.
│   ├── _elements.py          # Element class definitions (moved)
│   └── _mixins.py            # Mixin classes (moved)
├── outline/
│   ├── __init__.py          # Exports Outline only (+ End-of-Life stubs)
│   └── ...
```

## API Changes

### New API (primary)
```python
from shinymap import svg
from shinymap.svg import Circle, Path, Line, Rect, Polygon, Ellipse, Text

# Usage
circle = svg.Circle(cx=50, cy=50, r=30)
```

### Old API (breaks with helpful error)
```python
from shinymap.outline import Circle  # ImportError with migration instructions
```

## Migration Strategy

Follow the library's **End-of-Life ImportError pattern** (see CLAUDE.md):

```python
# Old import raises helpful ImportError
from shinymap.outline import Circle
# -> ImportError: 'Circle' has moved to shinymap.svg.
#    Please update your import:
#      from shinymap.svg import Circle
```

Add `__getattr__` to `outline/__init__.py` with moved names:

```python
_MOVED_TO_SVG = {"Circle", "Rect", "Path", "Polygon", "Ellipse", "Line", "Text", "Element", "ELEMENT_TYPE_MAP"}
```

## Files Requiring Updates

### Move files
- `outline/_elements.py` → `svg/_elements.py`
- `outline/_element_mixins.py` → `svg/_mixins.py`

### Update imports
- `outline/__init__.py` - Add End-of-Life `__getattr__` for moved names
- `outline/_outline.py` - Internal imports
- `outline/_regions.py` - Internal imports
- `outline/_export.py` - Internal imports
- `outline/_conversion.py` - Internal imports
- `_stilllife.py` - Uses `Path as PathElement`
- Tests: `test_stilllife.py`, `test_element_*.py`, `test_export_svg.py`

### Update docstrings/examples
- All docstrings referencing `from shinymap.outline import Circle`
- CLAUDE.md examples
- Example scripts

## Implementation Plan

### Phase 1: Create svg subpackage
1. Create `shinymap/svg/__init__.py`
2. Move `_element_mixins.py` → `svg/_mixins.py`
3. Move `_elements.py` → `svg/_elements.py`
4. Update internal imports in moved files

### Phase 2: Update outline package
1. Update `outline/__init__.py` with End-of-Life `__getattr__` for moved names
2. Update internal imports in outline modules

### Phase 3: Update consumers
1. Update `_stilllife.py` imports
2. Update test files
3. Update docstrings and examples

### Phase 4: Documentation
1. Update CLAUDE.md with new import style
2. Update any other docs

## Questions to Resolve

1. **Top-level re-export?** Should `shinymap/__init__.py` export `svg`?
   - `from shinymap import svg` ← requires explicit re-export
   - Recommendation: Yes, for ergonomic access

2. **Element type alias?** Keep `Element = Circle | Path | ...` union type?
   - Recommendation: Yes, useful for type hints

3. **ELEMENT_TYPE_MAP location?** Keep in `svg/_elements.py`?
   - Recommendation: Yes, it's used for JSON deserialization

## Risks

- **Import cycles**: Need to verify no circular dependencies
- **Missed updates**: May miss some internal imports; tests should catch this

## Success Criteria

1. All tests pass
2. `from shinymap import svg; svg.Circle(...)` works
3. `from shinymap.svg import Circle` works
4. `from shinymap.outline import Circle` raises helpful `ImportError`
5. All internal code updated to use new paths
