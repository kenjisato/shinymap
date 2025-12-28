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
- Base aesthetics via `defaultAesthetic` (fillColor, strokeColor, strokeWidth, fillOpacity, strokeDasharray, nonScalingStroke)
- Dynamic styling via `resolveAesthetic` callback (args: id/mode/isHovered/isSelected/count/baseAesthetic)
- Hover highlighting via `hoverHighlight` prop (renders as top-layer overlay for full border visibility)
- Selection highlighting for input maps via `resolveAesthetic` (isSelected=true)
- Selection highlighting for output maps via `fillColorSelected`/`fillColorNotSelected` props
- Per-group aesthetics via `aesGroup` (group name → aesthetic style)
- Extra SVG props via `regionProps` callback
- Output maps support the same aesthetic system with `resolveAesthetic` and `regionProps`
- Type-safe aesthetic builders: `aes.Shape()`, `aes.Line()`, `aes.Text()` with IDE autocomplete
- Line style constants: `linestyle.SOLID`, `linestyle.DASHED`, `linestyle.DOTTED`, `linestyle.DASH_DOT`
- Non-scaling stroke enabled by default (stroke widths are in screen pixels, not viewBox units)

**Hover implementation**:
- `aesHover` prop defines hover aesthetic (default: darker stroke, width 2)
- Rendered as separate overlay layer on top of all regions (solves SVG z-index border visibility)
- `pointer-events: none` ensures clicks pass through to base regions
- When `aesHover` is provided, `resolveAesthetic` receives `isHovered: false` (hover handled by overlay)
- Snake_case keys in Python (`aes_hover={"stroke_color": "...", "stroke_width": ...}`) automatically converted to camelCase for React

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

### Geometry Utilities (`shinymap.geometry`)

The `shinymap.geometry` subpackage provides tools for converting SVG files to shinymap's JSON format and loading geometry for use in applications.

**JSON Format**:
Shinymap uses a **flexible path format** where each region can map to either a single string or a list of strings:

```json
{
  "_metadata": {
    "viewBox": "0 0 100 100",
    "source": "Custom SVG",
    "license": "MIT"
  },
  "region_01": ["M 10 10 L 40 10 L 40 40 L 10 40 Z"],
  "region_02": "M 50 10 L 80 10 L 80 40 L 50 40 Z",
  "hokkaido": [
    "M 0 0 L 100 0 L 100 100 Z",
    "M 200 0 L 300 0 L 300 100 Z"
  ]
}
```

**Key points**:
- Each region ID maps to **either a string or a list of strings**
- String format: `"region_02": "M 50 10..."` (single path as string)
- List format: `"region_01": ["M 10 10..."]` (single path as list)
- Multi-element list: `"hokkaido": ["M 0 0...", "M 200 0..."]` (merged paths)
- Both formats are supported throughout the stack (Python backend, React frontend)
- List arrays are joined with spaces when rendering: `" ".join(path_list)`
- The `Geometry` class prefers the list format for consistency, but UI functions accept both

**Core Functions**:

- **`load_geometry(json_path, overlay_keys=None)`**: Load geometry from shinymap JSON files. Returns `(geometry, overlay_geometry, viewbox)` tuple. Automatically handles path joining, overlay separation, and viewBox computation.

- **`from_svg(svg_path, output_path=None)`**: Extract intermediate JSON from SVG file (Step 1 of interactive workflow). Auto-generates IDs for paths without them.

- **`from_json(intermediate_json, output_path=None, relabel=None, overlay_ids=None, metadata=None)`**: Transform intermediate JSON to final JSON (Step 2 of interactive workflow). Supports renaming and merging paths via `relabel` parameter.

- **`convert(input_path, output_path=None, relabel=None, overlay_ids=None, metadata=None)`**: One-shot conversion from SVG or intermediate JSON to final JSON. Combines `from_svg()` and `from_json()` for scripting and reproducibility.

- **`infer_relabel(initial_file, final_json)`**: Infer relabel mapping by comparing initial file (SVG or JSON) with final JSON. Automatically detects renames and merges for reproducibility.

**Workflows**:

*Interactive workflow* (two-step for manual inspection):
```python
from shinymap.geometry import from_svg, from_json

# Step 1: Extract intermediate JSON with auto-generated IDs
intermediate = from_svg("map.svg", "intermediate.json")

# Step 2: Apply transformations
final = from_json(
    intermediate,
    "final.json",
    relabel={
        "region_01": "path_1",              # Rename: path_1 → region_01
        "hokkaido": ["path_2", "path_3"],   # Merge: combine into hokkaido
    },
    overlay_ids=["_border"],
    metadata={"source": "Custom", "license": "MIT"}
)
```

*One-shot conversion* (scripting/reproducibility):
```python
from shinymap.geometry import convert

result = convert(
    "map.svg",
    "map.json",
    relabel={
        "region_01": "path_1",
        "hokkaido": ["path_2", "path_3"],
    },
    overlay_ids=["_border"],
    metadata={"source": "Custom", "license": "MIT"}
)
```

*Infer conversion code* (reproducibility from manual work):
```python
from shinymap.geometry import infer_relabel

# After manually creating final.json, infer the transformations
relabel = infer_relabel("original.svg", "final.json")
# Returns: {"region_01": "path_1", "hokkaido": ["path_2", "path_3"]}
```

**Interactive Converter App**:

An interactive Shiny app for SVG conversion is available:

```bash
# Run converter with browser
uv run python -m shinymap.geometry.converter -b

# Pre-load a file
uv run python -m shinymap.geometry.converter -f map.svg -b
```

The app provides:
- Visual preview of paths found in SVG
- Interactive relabel/merge configuration
- Overlay ID specification
- Metadata editing
- Download both JSON output and reproducible Python code
- "Infer from Original" tab to generate code from existing transformations

**Geometry OOP API**:

The `Geometry` class provides an object-oriented interface for geometry manipulation with immutable transformations:

```python
from shinymap.geometry import Geometry

# Load from various sources
geo = Geometry.from_svg("map.svg", extract_viewbox=True)
geo = Geometry.from_json("map.json")
geo = Geometry.from_dict(data)

# Immutable transformations (returns new Geometry instance)
geo = geo.relabel({"new_id": "old_id"})              # Rename single region
geo = geo.relabel({"merged": ["id1", "id2"]})        # Merge multiple regions
geo = geo.set_overlays(["_border", "_divider"])      # Mark overlay regions
geo = geo.update_metadata({"source": "Custom"})      # Add/update metadata

# Method chaining
final = (
    Geometry.from_svg("map.svg")
    .relabel({"hokkaido": ["path_1", "path_2"]})
    .set_overlays(["_border"])
    .update_metadata({"source": "Custom", "license": "MIT"})
)

# Export
final.to_json("output.json")
final_dict = final.to_dict()

# Access geometry data
regions = geo.regions           # Dict[str, List[str]]
metadata = geo.metadata         # Dict[str, Any]
viewbox = geo.viewbox()         # Tuple[float, float, float, float]
overlays = geo.overlays()       # List[str]
```

**Key features**:
- Immutable: All transformations return new instances
- Flexible path format: Regions map to `List[str]` (single or multiple paths)
- Method chaining: Fluent API for complex workflows
- Type safe: Validates structure at load time

**Integration with UI functions**:

The `Geometry` class is the recommended way to pass geometry to UI functions:

```python
from shinymap import Map, input_map, output_map
from shinymap.geometry import Geometry

geo = Geometry.from_json("map.json")

# Input maps
input_map("my_input", geo, mode="multiple")

# Output maps with static geometry
output_map("my_output", geo, tooltips=tooltips)

# Output maps with dynamic rendering
@render_map
def my_output():
    return Map(geo).with_fill_color(colors).with_counts(counts)
```

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

### SVG Rendering and Layered Overlays

**Challenge**: SVG elements render in DOM order (painter's algorithm). Later elements appear on top, causing border visibility issues:
- SVG strokes are centered on paths (50% inside, 50% outside)
- Adjacent regions' fills can hide neighboring regions' strokes
- Transparent strokes are invisible (adjacent fills show through)
- Selected/hovered regions' borders get partially hidden by non-selected neighbors

**Solution**: Layered overlay rendering ensures important elements (selected, hovered) are always visible.

**Rendering order** (bottom to top):
1. **Base regions**: All regions with normal aesthetics and click handlers
2. **Overlay geometry**: Non-interactive annotations (dividers, borders, grids) with `pointer-events: none`
3. **Selection overlay**: Duplicates of selected/active regions with selection aesthetics and `pointer-events: none`
4. **Hover overlay**: Duplicate of hovered region with hover aesthetics and `pointer-events: none`

This multi-layer approach guarantees:
- Selected regions' borders are fully visible on top of non-selected regions
- Hovered regions' borders are fully visible on top of everything
- All overlays use `pointer-events: none` so clicks pass through to base regions
- No z-index conflicts or CSS hacks needed

**Example with hover highlighting**:

```python
# Input map with custom hover highlight
input_map(
    "prefecture_selector",
    GEOMETRY,
    tooltips=TOOLTIPS,
    mode="single",
    view_box=VIEWBOX,
    aes_base={
        "fillColor": "#e5e7eb",    # Light gray fill
        "strokeColor": "#d1d5db",  # Light gray border
        "strokeWidth": 1
    },
    aes_hover={
        "stroke_color": "#374151",  # Darker border on hover
        "stroke_width": 2           # Thicker border on hover
    },
    overlay_geometry=DIVIDERS,      # Dividing lines rendered above base regions
    overlay_aesthetic=DIVIDER_STYLE, # but below selection/hover overlays
)
```

The hover overlay is automatically rendered on top of everything, ensuring the darker, thicker border is always fully visible even when adjacent regions would normally hide parts of it.

**Non-Interactive Annotation Layers**

**Purpose**: Display static annotation layers via `overlay_geometry` parameter.

**Use cases**:
- Dividing lines (e.g., separating repositioned insets from mainland)
- Administrative boundaries that aren't clickable regions
- Grid lines or reference markers
- Annotations that should appear above base regions but below selection/hover highlights

**Current implementation** (single overlay layer):

```python
# Single overlay layer (rendered AFTER regions)
input_map(
    "map_id",
    geometry,
    overlay_geometry=DIVIDERS,  # Dict[str, str] of SVG paths
    overlay_aesthetic={         # Styling for overlay
        "fillColor": "none",
        "strokeColor": "#999999",
        "strokeWidth": 2.0,
    },
)

@render_map
def my_map():
    return (
        Map(
            geometry,
            tooltips=tooltips,
            view_box=viewbox,
            overlay_geometry=dividers,
            overlay_aesthetic=divider_style,
        )
        .with_fill_color(fills)
    )
```

**Implementation details** (current):
- Single overlay layer rendered AFTER interactive regions
- `pointerEvents="none"` prevents click interference
- Available in all builders: `Map`, `MapSelection`, `MapCount`
- Serialized in `MapPayload` and passed through to React components

**Group-based Layer System** (implemented):

Regions can be assigned to different layers using group names:

```python
from shinymap import input_map, aes, linestyle

# Geometry with groups defined in metadata
geo = Geometry.from_dict({
    "_metadata": {
        "viewBox": "0 0 100 100",
        "groups": {
            "grid": ["grid_h", "grid_v"],
            "borders": ["divider_1", "divider_2"],
        }
    },
    "grid_h": [...],
    "grid_v": [...],
    "divider_1": [...],
    "divider_2": [...],
    "region_a": [...],
    "region_b": [...],
})

input_map(
    "map_id",
    geo,
    underlays=["grid"],      # Render grid below everything
    overlays=["borders"],    # Render borders above base regions
    hidden=["unused_region"], # Hide completely
    aes_group={              # Per-group aesthetics
        "grid": aes.Line(stroke_color="#ddd", stroke_dasharray=linestyle.DASHED).to_dict(),
        "borders": aes.Line(stroke_color="#999", stroke_width=2).to_dict(),
    },
)
```

**Render order** (5 layers, bottom to top):
1. **Underlay** - Background elements (grids, reference lines)
2. **Base regions** - Interactive regions with click/hover handling
3. **Overlay** - Non-interactive annotations (borders, labels)
4. **Selection overlay** - Selected regions (border visibility)
5. **Hover overlay** - Hovered region (always on top)

**Type-safe Aesthetic Builders**:

```python
from shinymap import aes, linestyle

# IDE autocomplete for all aesthetic properties
grid_style = aes.Line(
    stroke_color="#ddd",
    stroke_width=1,
    stroke_dasharray=linestyle.DASHED,  # Predefined: SOLID, DASHED, DOTTED, DASH_DOT
)

shape_style = aes.Shape(
    fill_color="#3b82f6",
    fill_opacity=0.8,
    stroke_color="#1e40af",
    stroke_width=2,
)

text_style = aes.Text(
    fill_color="#000",
    stroke_color="#fff",  # Outline for readability
    stroke_width=0.5,
)
```

**Example** (Japan prefecture map with grid underlay and dividers overlay):

```python
@render_map
def prefecture_map():
    return (
        MapSelection(
            GEOMETRY,
            selected=input.selected_prefectures(),
            tooltips=TOOLTIPS,
            view_box="0.0 0.0 1270.0 1524.0",
        )
        .with_fill_color("#e5e7eb")
        .with_fill_color_selected("#3b82f6")
    )

# Static layer configuration in output_map
output_map(
    "prefecture_map",
    GEOMETRY,
    underlays=["grid"],
    overlays=["dividers"],
    aes_group={
        "grid": {"stroke_color": "#eee", "stroke_dasharray": "5,5"},
        "dividers": {"stroke_color": "#999", "stroke_width": 2},
    },
)
```

**Legacy API** (deprecated but supported):
- `overlay_geometry` / `overlay_aesthetic` still work for backward compatibility
- New code should use `overlays` + `aes_group` instead

### Static vs Dynamic Parameters (Planned)

**Vision**: Separate structural configuration (static) from reactive data (dynamic) to keep server code clean and focused.

**Current API** (all parameters in builders):

```python
@render_map
def my_map():
    return (
        Map(
            geometry,           # Static - rarely changes
            tooltips=tooltips,  # Static - usually constant
            view_box=viewbox,   # Static - constant for given geometry
            overlay_geometry=dividers,      # Static - constant
            overlay_aesthetic=divider_style, # Static - constant
        )
        .with_fill_color(fills)  # Dynamic - from reactive data
        .with_counts(counts)     # Dynamic - from reactive data
    )
```

**Problem**: Static parameters (geometry, tooltips, viewBox, overlay) are repeated in every `@render_map` function, cluttering server code with structural details that don't change.

**Planned API** (static params in output_map()):

```python
# UI layer - define static structure once
app_ui = ui.page_fluid(
    output_map(
        "my_map",
        geometry=GEOMETRY,           # Static - defined once
        tooltips=TOOLTIPS,           # Static - defined once
        view_box=VIEWBOX,            # Static - defined once
        overlay_geometry=DIVIDERS,   # Static - defined once
        overlay_aesthetic=DIVIDER_STYLE,  # Static - defined once
    ),
)

# Server layer - focus only on reactive data transformations
@render_map
def my_map():
    selected = input.selected_regions()
    fills = scale_qualitative(categories, region_ids)

    # Clean, focused on data only
    return MapSelection(selected=selected).with_fill_color(fills)
```

**Benefits**:
1. **Cleaner server code**: No repeated geometry/tooltips/viewBox in every render function
2. **Better separation of concerns**: UI layer = structure, server layer = data transformations
3. **Easier maintenance**: Static configuration in one place, visible in UI definition
4. **Consistent with Shiny patterns**: Similar to how `output_plot(width=, height=)` defines figure size in UI, not in render function

**Implementation plan**:
- Add optional static parameters to `output_map()` registration
- Merge static params from `output_map()` with dynamic params from `Map*()` builders
- Maintain backward compatibility: if param provided to both, builder value takes precedence
- Static params available to all builders when omitted

**Implementation status**: Not yet implemented. Static parameters currently must be passed to `Map*()` builders.

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

## Interactive Output Maps (Future)

**Vision**: Extend `output_map()` to support optional interactivity while maintaining current simplicity for non-interactive use cases.

**Current workaround**: Users can achieve interactive visualizations using `@render.ui` with `input_map`:

```python
# UI
ui.output_ui("color_ring_ui")

# Server
@render.ui
def color_ring_ui():
    tone = input.tone_selector()
    colors = get_pccs_colors(tone)
    color_data = get_color_conversions(colors)

    # Dynamically recreate input_map with updated tooltips
    tooltips = {color_id: format_color_data(color_data[color_id]) for color_id in colors}

    return input_map(
        "selected_color",
        PCCS_GEOMETRY,
        tooltips=tooltips,
        fills=colors,
        mode="single",
    )
```

**Why this workaround is suboptimal**:

1. **Performance**: Re-rendering entire input component on every reactive change is expensive compared to React reconciliation updating only changed properties
2. **Lost transient state**: Re-creating the component resets hover position and other UI state
3. **Semantic confusion**: Using "input" for pure visualization (when user interaction isn't the primary goal) obscures intent
4. **Pattern inconsistency**: Most Shiny apps use `output_*` for server→client displays; mixing input/output semantics reduces code clarity

**Proposed enhancement**: Add optional parameters to `output_map()` for common interactive patterns:

```python
output_map(
    "my_map",
    geometry=GEOMETRY,
    click_input_id="clicked_region",  # Optional: emit region ID on click
    hover_tooltip=True,               # Optional: show dynamic tooltip data
)

@render_map
def my_map():
    return Map(geometry).with_fill_color(fills).with_tooltip_data(data)
```

**Use case example: PCCS Color Ring Application**

PCCS (Practical Color Coordinate System) is a Japanese color system that groups colors by psychological feelings (vivid, soft, light, etc.).

Application workflow:
1. User selects tone category from input (e.g., "vivid", "soft", "light")
2. Output map displays color ring with actual colors in that tone group
3. Hover over a color shows tooltip with conversions (Munsell, HCL, CMYK, RGB)
4. Click (or double-click) copies color data to clipboard

**Benefits over @render.ui workaround**:
- Better performance: React reconciliation updates only changed tooltips/colors, not entire component
- Preserves UI state: Hover position and focus maintained across updates
- Clearer semantics: `output_map` signals server→client data flow; `input_map` signals user interaction capture
- Maintains library philosophy: Simple, focused, good enough for 80% of interactive visualization needs without D3.js

**Technical notes**:
- Groundwork exists: `_render_map_ui()` already has `click_input_id` parameter
- React components (InputMap/OutputMap) share rendering logic, can share interactivity
- Tooltip data could be passed via `.with_tooltip_data(dict)` method on builders
- Click events follow existing Shiny input pattern: `input.clicked_region()` returns region ID

**Status**: Planned for future. Not yet implemented. Current `@render.ui` + `input_map` workaround is functional but has performance and semantic trade-offs.

## Open / Deferred Items

- Hover events remain visual only; revisit if live hover data is ever required.
- Optional decorator APIs and additional syntactic sugar are undecided; revisit once core UX is validated.
- Python adapter: add static per-region aesthetic overrides (per-id fills/props) to mirror React flexibility.
