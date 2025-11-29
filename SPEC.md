# Project Specification

This repository hosts a reusable React map renderer (SVG path based) and language-specific adapters for Shiny (Python now, R later). The overarching goals:

- Deliver interactive input/output maps where arbitrary regions (defined by SVG paths) can be clicked, hovered, and styled. Geometry is intentionally generic; no hardwired Japan-specific logic lives in the core.
- Publish a Shiny for Python package (`shinymapjp` naming is legacy) that bundles the frontend so users can `pip install` and go—no knowledge of the React internals required.
- Keep the design generic: any tabular dataset plus a path JSON can drive the map. Richer geography (prefectures, world maps, etc.) lives in separate asset packages or extensions.
- License everything under MIT and keep dependencies MIT-compatible.
- Preserve a clean separation between map rendering logic and dataset-specific geometry/assets.

## React Map Package

**Audience:** plain TypeScript/JavaScript apps and the Shiny adapters.

- Provide input and output map primitives capable of: click selection, hover highlighting, configurable fills (highlight/choropleth), and tooltip display.
- Tooltips are static by default. They may be replaced by a new payload from the server, but there is no hover event emission.
- Ship as an npm package with ESM build + type declarations. Follow standard semver versioning.
- Expose a clear public API; do not rely on internal directory structure (e.g., `srcts` is an implementation detail).
- Keep code idiomatic, concise, and readable—prioritize clarity over cleverness and document non-obvious logic.
- The project is pre-1.0.0; breaking changes are acceptable while optimizing for clarity and performance. Do not add backward-compatibility shims yet.
- Geometry assets should be swappable: component APIs accept arbitrary path dictionaries keyed by region IDs. The core bundle (`shinymap`) ships only with lightweight demo shapes (e.g., circles/rectangles) so no large geography is embedded by default; richer datasets live in separate asset packages.
- Accessibility: hover-only feedback is acceptable for the initial release. Keyboard navigation to be addressed in the next iteration.

### Current Input/Output API philosophy
- Input maps use a unified count model with `cycle` (how counts advance) and `maxSelection` (cap on non-zero regions). Mode values are conveniences: single → toggle + maxSelection 1; multiple → toggle + unlimited; count → increment + unlimited. Caps block new activations; single replaces the active region when clicked elsewhere.
- Styling is user-defined via `defaultAesthetic` and `resolveAesthetic` (args include id/mode/isHovered/isSelected/count/base). No opinionated hover/selection defaults; `regionProps` can attach extra SVG props/effects.
- Output maps mirror the naming: `containerStyle`, `resolveAesthetic`, `regionProps`; minimal defaults (fills/defaultFill + strokeColor/strokeWidth), optional per-region overrides.

### Packages and scope
- `packages/shinymap/js`: React components (InputMap/OutputMap) using SVG paths; geometry-agnostic.
- `packages/shinymap/python`: Shiny for Python bindings; mirrors the JS API and ships prebuilt assets + demo geometry.
- `packages/shinymapjp`: originally intended for Japan prefectures; broader general-geomap support is preferred (ship geometry as separate assets, keep core generic).

## Geometry & Assets
- Maintain a lightweight demo path JSON inside the core package (`shinymap`) and document how to build additional geometry bundles (source attribution, simplification tolerance, regeneration scripts).
- Provide guidance for separate asset packages (npm/PyPI/CRAN) that ship richer geometries (e.g., Japan prefectures, world/regional maps). Keep the core generic.
- Allow consumers to supply alternative geometry/path collections via the API.

## Shiny for Python (`shinymapjp`)

- Bundle the prebuilt JS/CSS assets plus the tiny demo geometry so `pip install shinymapjp` is ready to use out of the box.
- Provide helpers (`input_map`, `output_map`, `map` / `render_map`) that hide the React layer completely.
- Input components surface their state via the declared Shiny input ID (e.g., `input['pref_in']`). Outputs should react to the same state; avoid emitting auxiliary IDs such as `{output_id}__selection`.
- Server helpers should minimize boilerplate while staying explicit and readable.
- Input helpers should expose the same unified model as the JS component: values are a `{id: count}` map plus convenience presets (single/multiple/count) that set `cycle`/`maxSelection` defaults. Consider offering helper functions to emit legacy shapes (string/array) if needed, but the underlying payload is count-based.
- Define JSON payload schema for the React output: geometry config, fills, static tooltips, optional active selection, optional colorbar metadata.
- State flow: the input component calls `Shiny.setInputValue(id, value)` for selections. The server sends updated payloads (including the active selection) to the output component. Hover is purely visual.
- Package requirements: MIT license, semver, Python ≥3.12, dependencies (`shiny>=…`, optional `cairosvg`). Ship wheel + sdist artifacts for PyPI.

## Shiny for R (Future Work)

- Mirror the Python API and packaging approach (bundle assets in `inst/www`, provide `input_map`, `output_map`, etc.).
- Align documentation, naming, and behavior so users can switch between Python and R with minimal friction.

## Testing & CI

- Frontend: unit/snapshot tests for map rendering and interaction logic.
- Python: integration tests ensuring the adapters produce correct payloads and hide frontend concerns.
- Plan future R tests once the adapter exists.
- Enforce lint/format (TypeScript + ESLint, Python linting) via CI (e.g., GitHub Actions).

## Documentation

- README / docs should cover:
  - React usage (import map primitives, pass geometry + fill data).
  - Python quickstart with full code sample (showing cycle/maxSelection + resolveAesthetic usage).
  - Schema for geometry/paths and how to regenerate them.
  - Versioning policy and changelog location.
  - Future R package expectations.
- Keep prose concise and human-friendly; highlight default behaviors (e.g., tooltips static, hover visual-only).

## Open / Deferred Items

- Hover events remain visual only; revisit if live hover data is ever required.
- Keyboard navigation, ARIA labeling, and broader accessibility to be tackled in the next major update.
- Optional decorator APIs and additional syntactic sugar are undecided; revisit once core UX is validated.
