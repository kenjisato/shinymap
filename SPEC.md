# Project Specification

This repository hosts a reusable React map renderer and language-specific adapters for Shiny (Python now, R later). The overarching goals:

- Deliver interactive input/output maps where prefectures/regions can be clicked, hovered, and colored.
- Publish a Shiny for Python package (`shinymapjp`) that bundles the frontend so users can `pip install` and go—no knowledge of the React internals required.
- Keep the design generic: any tabular dataset plus a path JSON can drive the map, not just the built-in Japan geometry.
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

## Geometry & Assets
- Maintain a lightweight demo path JSON inside the core package (`shinymap`) and document how to build additional geometry bundles (source attribution, simplification tolerance, regeneration scripts).
- Provide guidance for separate asset packages (npm/PyPI/CRAN) such as `shinymapjp` that ship richer geometries (e.g., Japan prefectures).
- Allow consumers to supply alternative geometry/path collections via the API.

## Shiny for Python (`shinymapjp`)

- Bundle the prebuilt JS/CSS assets plus the tiny demo geometry so `pip install shinymapjp` is ready to use out of the box.
- Provide helpers (`input_map`, `output_map`, `map` / `render_map`) that hide the React layer completely.
- Input components surface their state via the declared Shiny input ID (e.g., `input['pref_in']`). Outputs should react to the same state; avoid emitting auxiliary IDs such as `{output_id}__selection`.
- Server helpers should minimize boilerplate while staying explicit and readable.
- Input API modes:
  - **Single selection:** `input['pref_in']` returns a single region ID (string) and the selected region is highlighted.
  - **Multiple selection:** `input['pref_in']` returns an array of region IDs or a `{id: boolean}` map; highlighted regions reflect the active set.
  - **Click counter:** `input['pref_in']` returns a `{id: number}` map or array of counts; the map uses alpha/annotation to visualize click frequencies.
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
  - Python quickstart with full code sample.
  - Schema for geometry/paths and how to regenerate them.
  - Versioning policy and changelog location.
  - Future R package expectations.
- Keep prose concise and human-friendly; highlight default behaviors (e.g., tooltips static, hover visual-only).

## Open / Deferred Items

- Hover events remain visual only; revisit if live hover data is ever required.
- Keyboard navigation, ARIA labeling, and broader accessibility to be tackled in the next major update.
- Optional decorator APIs and additional syntactic sugar are undecided; revisit once core UX is validated.
