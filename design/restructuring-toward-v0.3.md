# Module Restructuring Toward v0.3

**Status**: In Progress
**Created**: 2025-12-30

This document tracks the long-term goal of cleaning up the module structure to eliminate circular dependencies and establish clear separation of responsibilities.

## Problem Statement

The codebase has accumulated circular dependencies that require workarounds:

1. **`TYPE_CHECKING` guards**: 14 files use `if TYPE_CHECKING:` to defer imports
2. **Late imports inside functions**: e.g., `from ..ui._ui import _static_map_params` inside `_output_map()`
3. **Tightly coupled modules**: `wash`, `aes`, `ui`, `geometry`, `relative` all depend on each other

These workarounds:
- Obscure the true dependency graph
- Make the code harder to reason about
- Create subtle bugs when import order matters
- Complicate testing and mocking

### Current Workaround Locations

Files using `TYPE_CHECKING` guards:
- `aes/_core.py`
- `types.py`
- `_validation.py`
- `mode.py`
- `_map.py`
- `geometry/_geometry.py`
- `wash/_core.py`
- `wash/_util.py`
- `wash/__init__.py`
- `geometry/_export.py`
- `geometry/_regions.py`
- `geometry/_element_mixins.py`
- `geometry/_elements.py`
- `ui/_ui.py`

Late imports inside functions:
- `wash/_output_map.py`: imports `_static_map_params` from `ui/_ui.py`
- `wash/_render_map.py`: imports `MapBuilder` and `_apply_static_params`
- `geometry/_geometry.py`: imports `path_bb` from `utils`

## Root Cause

Responsibilities are mixed across modules:
- Resolution logic (business logic) is mixed with serialization (boundary concern)
- Data structures and algorithms are in the same modules
- No clear layering discipline

## Target Architecture

Clear layering with unidirectional dependencies:

```
┌─────────────────────────────────────────────────────┐
│                    ui/ (boundary)                    │
│  input_map, output_map, update_map, render_map      │
│  Serialization to JS happens HERE ONLY              │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                  wash/ (configuration)               │
│  wash() factory, WashConfig, resolution algorithms   │
│  Returns typed Python objects, NOT dicts            │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                   aes/ (data types)                  │
│  BaseAesthetic, ByState, ByGroup, IndexedAesthetic  │
│  Pure data + to_dict()/from_dict() serialization    │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                  types/ (foundation)                 │
│  MISSING, MissingType, type aliases                 │
│  No dependencies on other shinymap modules          │
└─────────────────────────────────────────────────────┘
```

**Key principles:**
- Lower layers NEVER import from higher layers
- Serialization happens only at the UI boundary
- Each layer can be tested in isolation

## Success Criteria

1. **No `TYPE_CHECKING` guards needed** for internal imports
2. **No late imports inside functions** to break cycles
3. **Clear import direction**: lower layers never import from higher layers
4. **Testable in isolation**: each layer can be tested without mocking imports

## Incremental Steps

### Completed

1. ✅ Add `to_dict()`/`from_dict()` to aes classes
2. ✅ Document late serialization philosophy in CLAUDE.md

### In Progress

3. ⬜ Separate resolution from serialization (see [aes-resolution.md](aes-resolution.md))
   - Add `resolve()` method to BaseAesthetic
   - Refactor `_convert_to_aes_dict()` in `wash/_core.py`

### Future

4. ⬜ Move resolution algorithms from `relative.py` to appropriate layer
5. ⬜ Eliminate late imports in `wash/_output_map.py` and `wash/_render_map.py`
6. ⬜ Review and fix `geometry/` module dependencies
7. ⬜ Remove `TYPE_CHECKING` guards one by one
8. ⬜ Final cleanup and verification

## Tracking Progress

When removing a workaround, update this document:
- Remove the file from the "Current Workaround Locations" list
- Add a note about what was done

## Related Documents

- [aes-resolution.md](aes-resolution.md) - Current refactoring focus
- [aes-protocol.md](aes-protocol.md) - Serialization protocol
