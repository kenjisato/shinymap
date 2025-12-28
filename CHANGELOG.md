# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-12-28

### Fixed

- Fix ruff linting errors (import sorting, unused imports, line length)
- Add missing `warnings` import in `geometry/_loader.py`
- Fix mypy type errors with proper annotations and `# type: ignore` comments
- Format Python files with ruff format
- Format JS files with Prettier

## [0.2.0] - 2025-12-28

### Added

- **Aesthetic system**: New `aes` module with `ByState`, `ByGroup`, and `Indexed` classes for declarative styling
  - `aes.ByState()`: Define aesthetics for different interaction states (base, hover, select, active)
  - `aes.ByGroup()`: Apply different aesthetics to different region groups
  - `aes.Indexed()`: Multi-state aesthetics for Cycle/Count modes with indexed arrays
- **Mode classes**: `Single`, `Multiple`, `Cycle`, `Count` classes replace string-based mode configuration
  - Each mode class accepts an optional `aes` parameter for customization
  - `Cycle(n=4, aes=aes.Indexed(fill_color=[...]))` for visual state cycling
  - `Count(max=10, aes=aes.Indexed(fill_color=[...]))` for count visualization
- **Layer system**: Support for underlays, overlays, and hidden layers in geometry
  - Automatic detection of layer types from region ID prefixes (`_underlay_`, `_overlay_`, `_hidden_`)
  - `path_as_line()` method to mark regions containing line paths for stroke-only rendering
- **`wash()` utility**: Transform raw aesthetic dicts into properly structured `aes.ByState` objects
- **Polymorphic elements**: `Element.from_dict()` for flexible element creation from dictionaries

### Changed

- **Refactored UI functions**: `base_input_map()` and `base_output_map()` now accept `aes` as proper objects
- **Nested props structure**: TypeScript types updated to match Python's hierarchical aesthetic model
- **Layered rendering in React**: InputMap and OutputMap now render underlays, base regions, overlays, selections, and hover in correct order

### Fixed

- Cycle mode now properly cycles through indexed colors
- Count mode properly clamps/wraps to indexed aesthetic arrays
- Selection layer correctly skipped when `aesIndexed` is present (avoids double-rendering)

## [0.1.0] - Initial Development

- Basic InputMap and OutputMap components
- Single/Multiple selection modes
- Hover highlighting
- Python Shiny bindings

