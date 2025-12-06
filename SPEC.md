# Project Specification

This repository hosts a reusable React map renderer (SVG path based) and language-specific adapters for Shiny (Python now, R later).

## Core Philosophy: Visual Input Components First

shinymap provides **visual alternatives to standard HTML form inputs**:
- `input_map(mode="single")` → Visual radio buttons (select one region)
- `input_map(mode="multiple")` → Visual checkboxes (select multiple regions)
- `input_map(mode="count")` → Visual counter/range input (click to increment with visual feedback)

Additionally, `output_map` provides simplified statistical visualizations (choropleths, categorical coloring) with a declarative API.

## Overarching Goals

- Deliver interactive input/output maps where arbitrary regions (defined by SVG paths) can be clicked, hovered, and styled. Geometry is intentionally generic; no hardwired geography-specific logic lives in the core.
- Publish a Shiny for Python package (`shinymap`) that bundles the frontend so users can `pip install` and go—no knowledge of the React internals required.
- Keep the design generic: any tabular dataset plus a path JSON can drive the map. Richer geography (prefectures, world maps, etc.) lives in separate asset packages or extensions (`shinymap-geo`).
- License everything under MIT and keep dependencies MIT-compatible.
- Preserve a clean separation between map rendering logic and dataset-specific geometry/assets.
- Maintain a **React core library** as the foundation, with parallel bindings for **R Shiny** and **Python Shiny** (not "JavaScript first, then port").

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

**Internal unified count model**:
- Input maps internally use `{region_id: count}` representation with `cycle` (how counts advance) and `maxSelection` (cap on non-zero regions)
- Mode values provide convenient presets: `single` → toggle + maxSelection 1; `multiple` → toggle + unlimited; `count` → increment + unlimited
- This unified internal model enables flexible mode switching and consistent color mapping

**External ergonomic APIs**:
- Python Shiny adapters provide mode-appropriate return types:
  - `input.map_id()` returns `str | None` for single mode
  - `input.map_id()` returns `list[str]` for multiple mode
  - `input.map_id()` returns `dict[str, int]` for count mode
- R Shiny (planned): character scalar/vector for single/multiple, named integer vector for count
- React: JavaScript objects/arrays following standard patterns

**Styling**:
- User-defined via `defaultAesthetic` and `resolveAesthetic` (args include id/mode/isHovered/isSelected/count/base)
- No opinionated hover/selection defaults; `regionProps` can attach extra SVG props/effects
- Output maps mirror the naming: `containerStyle`, `resolveAesthetic`, `regionProps`; minimal defaults (fills/defaultFill + strokeColor/strokeWidth)

### Packages and scope

**Core library** (current development):
- `packages/shinymap/js`: React components (InputMap/OutputMap) using SVG paths; geometry-agnostic
- `packages/shinymap/python`: Shiny for Python bindings; mirrors the JS API and ships prebuilt assets + demo geometry
- `packages/shinymap/r` (planned): Shiny for R bindings following the same philosophy

**Geographic extension** (`shinymap-geo`, future):
- Geographic data loading (GeoJSON, TopoJSON, Shapefiles)
- Coordinate projection support
- Integration with `sf` (R) and `geopandas` (Python)
- Pre-packaged datasets (world countries, US states, Japan prefectures, etc.)
- Geometry simplification and optimization utilities

This separation keeps the core library lightweight while allowing advanced GIS features for users who need them.

## Geometry & Assets
- Maintain a lightweight demo path JSON inside the core package (`shinymap`) and document how to build additional geometry bundles (source attribution, simplification tolerance, regeneration scripts).
- Provide guidance for separate asset packages (npm/PyPI/CRAN) that ship richer geometries (e.g., Japan prefectures, world/regional maps). Keep the core generic.
- Allow consumers to supply alternative geometry/path collections via the API.

## Shiny for Python (`shinymap`)

- Bundle the prebuilt JS/CSS assets plus the tiny demo geometry so `pip install shinymap` is ready to use out of the box.
- Provide helpers (`input_map`, `output_map`, `Map` / `render_map`) that hide the React layer completely.
- Input components surface their state via the declared Shiny input ID with mode-appropriate return types (see External ergonomic APIs above).
- Server helpers should minimize boilerplate while staying explicit and readable.
- Input helpers expose the same internal unified model as the JS component: values are `{id: count}` map internally, but the Python API returns mode-appropriate types (`str | None`, `list[str]`, or `dict[str, int]`).
- Define JSON payload schema for the React output: geometry config, fills, static tooltips, optional active selection, optional colorbar metadata.
- State flow: the input component calls `Shiny.setInputValue(id, value)` for selections. The server sends updated payloads (including the active selection) to the output component. Hover is purely visual.
- Package requirements: MIT license, semver, Python ≥3.12, dependencies (`shiny>=…`). Ship wheel + sdist artifacts for PyPI.

### Color Scaling Utilities

Provide built-in color scaling functions for common statistical visualization patterns:

- **`scale_sequential(counts, region_ids, palette=SEQUENTIAL_BLUE, max_count=None)`**: Maps count data to sequential color scales (light to dark). Uses continuous color interpolation for smooth visual feedback. The `max_count` parameter allows fixed scaling for interactive visualizations.

- **`scale_diverging(values, region_ids, low_color, mid_color, high_color, midpoint=0.0)`**: Maps numeric values to diverging color scales (red-gray-blue style) for positive/negative data.

- **`scale_qualitative(categories, region_ids, palette=QUALITATIVE)`**: Maps categorical data to distinct colors, cycling through the palette if needed.

All utilities use the internal `lerp_hex()` helper for color interpolation. Pre-defined palettes (SEQUENTIAL_BLUE, SEQUENTIAL_GREEN, SEQUENTIAL_ORANGE, QUALITATIVE) are provided but customizable.

### Partial Update API

**`update_map(id, tooltips=, fills=, counts=, active_ids=, session=)`** provides selective property updates following Shiny's `update_*()` pattern (like `ui.update_slider`, `ui.update_select`).

**Use cases**:
- Highlighting active regions without re-executing expensive `@render_map` computations
- Updating tooltips dynamically (if hover events are added later)
- Changing fills based on fast computations while deferring full map re-render

**Example**:
```python
@reactive.effect
@reactive.event(input.selected)
def _():
    ui.update_map("my_map", active_ids=input.selected())
```

This complements rather than replaces `@render_map` for performance-critical scenarios. Tooltip updates are very cheap (lightweight SVG `<title>` elements); React reconciliation handles DOM updates efficiently.

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

## Performance Considerations

**Input components**: Highly efficient. Click interactions update only the specific regions that changed via React's reconciliation. No performance concerns for typical use cases (dozens to hundreds of regions).

**Output components**: Follow standard Shiny patterns. When input data changes, `@render_map` re-executes, serializes complete map state to JSON, and sends to client. React reconciliation then updates only changed DOM elements.

**Known limitation**: Output maps don't leverage Shiny's fine-grained reactivity at the region level. All regions are treated as a single reactive dependency. This is a **general Shiny pattern** (similar to matplotlib plot regeneration) rather than shinymap-specific.

**When this matters**:
- Maps with >500 regions
- Computationally expensive color scaling
- High interaction frequency

**Mitigation strategies**:
- React handles DOM reconciliation efficiently; typical maps (<100 regions) update smoothly
- JSON payloads are small (<50KB for typical geographic maps)
- For expensive computations: use standard Shiny patterns (action buttons, debouncing, caching)
- Example: Defer rendering until user clicks "Update Map" button

**Future optimization**: Implement delta-based updates to send only changed regions. This requires custom Shiny bindings and increases implementation complexity. Defer until real-world use cases demonstrate need.

## Accessibility

**Goal**: These are input components, not just pictures. Proper accessibility would be a genuine differentiator.

**Current status**: Basic mouse interaction implemented (hover, click).

**Planned features** (with limitations):
- **Keyboard navigation**: Tab/Shift+Tab to move between regions, Enter/Space to select/toggle. Feasible for small to medium maps (<100 regions).
- **ARIA labels**: `aria-label` for each region, basic screen reader support. Straightforward to implement.
- **ARIA roles**: Explore appropriate roles for radio/checkbox group semantics. May be challenging to map visual spatial layouts to traditional form control roles.
- **Focus indicators**: Visual feedback for keyboard focus distinct from mouse hover. Straightforward.

**Challenges**:
- Complex ARIA role semantics for non-standard spatial layouts
- Focus management with hundreds/thousands of regions
- Screen reader verbosity with many regions

Accessibility is planned with specific limitations acknowledged. Not all features from standard form controls will translate cleanly to spatial visual interfaces.

## Open / Deferred Items

- Hover events remain visual only; revisit if live hover data is ever required.
- Optional decorator APIs and additional syntactic sugar are undecided; revisit once core UX is validated.
- Python adapter: add static per-region aesthetic overrides (per-id fills/props) to mirror React flexibility.
