# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Planned as 0.4.0: the breaking changes below follow from fixes, not redesigns.

### Breaking changes

- **Plural layer keys raise `ValueError`** (`overlays`, `underlays`, `annotations`) in an
  outline's `_metadata`, `Outline.merge_layers()` and `Map(layers=)`; the message names
  the singular key. In 0.3.0 they were silently ignored, which turned overlay regions
  into clickable main regions (#52).
- `Map().with_value()` validates its values like `Map(value=)` and `input_map(value=)`:
  floats, strings and negative values raise (#58).
- `import shinymap.geometry` raises the migration `ImportError` on import, not only on
  attribute access (#58).

### Added

- `aes.color.scale_continuous(values, region_ids, vmin=..., vmax=...)` colors data
  values such as populations or ratios: it takes floats, clamps to `vmin`/`vmax`, and
  gives regions without a value a neutral gray. `scale_sequential` stays the scale for
  counts (#63).
- `Map(fill_color={region_id: color})` and `MapBuilder.with_fill_color()` color regions
  by value, e.g. with a color scale's output, layered over `aes=` (#64).
- `shinymap.default_wash`: the library's default look as a `Wash`; `input_map`,
  `output_map` and `render_map` are its methods (#62).
- `Wash.build(..., mode=...)` and `StillLife` render indexed aesthetics (`Cycle` / `Count` /
  `Display` with `aes.Indexed`, also per group via `aes.ByGroup`) the same way the
  browser does: Cycle wraps, other modes clamp to the last entry, and indexed modes draw
  no selection layer (#50).
- `StillLife.to_svg()` draws the annotation layer on top of hover (#50).
- Documentation: Modes, Aesthetics and Layers pages; the figures on the site are drawn
  by shinymap when the site is built (#47, #48).

### Changed

- The JavaScript bundle is React's production build, minified: `shinymap.global.js`
  goes from 1.17 MB to 211 KB (#59).

### Fixed

- `Single(allow_deselect=False)` is honoured: clicking the selected region keeps it
  selected (#27, #61).
- `Count(max_count=...)` caps the indexed aesthetic, in the browser and in `StillLife`;
  before, it had no effect (#53).
- The selection and hover overlays use each region's own `select` / `hover` looks, and a
  region's `hover=None` turns its hover off; before, they used the `__all` looks (#57).
- `output_map(..., mode=Display(clickable=True))` without an outline keeps its mode and
  click input when `@render_map` supplies the outline (#56).
- Values accept numpy integers and bools (converted to `int`), so values built from a
  pandas DataFrame work (#58).
- A click on an `input_map()` right after the page loads is no longer reset to the
  initial value by the bridge's retry that waits for Shiny (#51).
- `StillLife.to_svg()` no longer draws annotation regions in the base layer, and draws
  selection copies only for base-layer regions (#50).
- The sdist no longer includes `examples/data/scripts/README.md` (#58).

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
- **`Map(active=...)` removed**: selection is derived from `value > 0`. On the builder,
  `with_active()` is removed and `with_geometry_metadata()` is now `with_outline_metadata()`.
- `input_radio_buttons()` and `input_checkbox_group()` also take `outline` (was `geometry`).
- **Top-level API reorganized**:
  - `wash()` is now the class `Wash`; `configure_theme()` is removed (use `Wash`).
  - `shinymap.color` and `shinymap.linestyle` moved to `shinymap.aes.color` and
    `shinymap.aes.line`.
  - `MapBuilder`, `MISSING`, `BaseAesthetic`, `WashConfig` and `WashResult` are no longer
    exported from `shinymap`; import them from `shinymap.types`.
  - The `DEFAULT_*_AESTHETIC` constants are removed; defaults come from `Wash`.
- **SVG conversion moved**: `shinymap.geometry.convert` and the converter app are now in
  `shinymap.kit` (`kit.convert`, `python -m shinymap.kit.sketch`); `from_svg` / `from_json`
  are `Outline.from_svg()` / `Outline.from_json()`.
- `Map(aes=...)` no longer accepts a raw dict; pass `aes` objects.
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
  - `Count(max_count=10, aes=aes.Indexed(fill_color=[...]))` for count visualization
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

