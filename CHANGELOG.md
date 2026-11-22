# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-11-22

### Breaking changes

- **`geometry` → `outline`**: `Geometry` is now `Outline`, `shinymap.geometry` is now
  `shinymap.outline`, and the `geometry` parameter of `input_map()`, `output_map()` and
  `export_svg()` is now `outline`.
  Importing from `shinymap.geometry` raises an `ImportError` that names the replacement.
- **SVG element classes moved to `shinymap.svg`** (`Circle`, `Path`, `Line`, ...).
  Old import paths raise an `ImportError` with migration instructions.
- **Layer keys are singular**: `overlay`, `underlay`, `hidden` (was `overlays`,
  `underlays`) in metadata and `layers=`. `Outline` accessors are `overlay_ids()`,
  `underlay_ids()` and `hidden_ids()`.
- **`Map(active=...)` removed**: selection is derived from `value > 0`.
- Initial values passed to `Map()` / `input_map()` must be non-negative integers;
  negative or float values now raise.

### Added

- `output_map(mode=Display(...))`: display mode with `clickable=True` to emit clicks
  (optionally to a custom `input_id`) and `aes.Indexed` for value-to-color mapping.
- `input_map(raw=True)` returns the `dict[str, int]` value in every mode.
- Annotation layer, rendered above hover and selection (#7).
- `Outline.move_layer()` and `Outline.move_group()` for assigning layers and merging
  regions fluently.
- `StillLife` for inspecting resolved aesthetics outside a Shiny session, and
  `StillLife.to_svg()` for static SVG export.
- `shinymap.kit`: `python -m shinymap.kit.sketch` converts an SVG into an outline
  (rename, groups, layers, and marking stroke-only paths as lines) and generates the
  Python code to reproduce it; `python -m shinymap.kit.caption` writes a reference SVG
  with region IDs overlaid.

### Fixed

- `input_map()` and `output_map()` work inside Shiny modules (ids are resolved
  through the module namespace) (#8, #10).
- `output_map()` without an `outline` no longer raises `AttributeError`.

## [0.2.2] - 2025-12-28

### Added

- `Map()` and `MapBuilder.with_aes()` now accept `aes.ByGroup`, `aes.ByState`, and `aes.Shape` directly
  - Previously only accepted raw dict format
  - Enables cleaner API: `Map(aes=aes.ByGroup(region1=aes.Shape(fill_color="#fff")))`

### Fixed

- Fix aes merging in `_apply_static_params()` to preserve `lines_as_path` entries from `output_map()`
  - User-provided aes from `Map()` now properly merges with static aes containing `lines_as_path` data
  - Ensures divider lines and other path-as-line regions retain correct aesthetics

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

