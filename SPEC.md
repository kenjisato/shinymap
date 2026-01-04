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

**Mode Classes** (v0.2.0+):
Mode configuration uses class instances instead of string literals for better customization:

```python
from shinymap import input_map, output_map
from shinymap.mode import Single, Multiple, Cycle, Count, Display

# Basic modes (equivalent to mode="single" / mode="multiple")
input_map("id", outline, mode=Single())
input_map("id", outline, mode=Multiple())

# Cycle mode: finite state cycling (0 → 1 → 2 → 3 → 0)
input_map("id", outline, mode=Cycle(n=4))

# Count mode: unbounded or capped counting
input_map("id", outline, mode=Count())          # Unbounded
input_map("id", outline, mode=Count(max=10))    # Capped at 10

# Display mode for output_map: hover-only, values index into aesthetics
output_map("id", outline, mode=Display(aes=aes.Indexed(
    fill_color=["#gray", "#green", "#yellow", "#red"]
)))

# Display mode with click events
output_map("id", outline, mode=Display(clickable=True, input_id="clicked"))

# With initial values
input_map("id", outline, mode=Single(selected="region_a"))
input_map("id", outline, mode=Multiple(selected=["a", "b"]))
input_map("id", outline, mode=Count(values={"a": 3, "b": 5}))

# With indexed aesthetics for visual feedback
from shinymap import aes
CYCLE_COLORS = ["#e2e8f0", "#fecaca", "#fef08a", "#bbf7d0"]
input_map("id", outline, mode=Cycle(n=4, aes=aes.Indexed(fill_color=CYCLE_COLORS)))
```

**Styling** (v0.2.0 - Hierarchical Aesthetic System):

The aesthetic system uses a hierarchical structure with state-based and group-based configuration:

```python
from shinymap import aes

# State-based aesthetics (base, hover, select states)
style = aes.ByState(
    base=aes.Shape(fill_color="#e2e8f0", stroke_color="#94a3b8"),
    hover=aes.Shape(stroke_color="#1e40af", stroke_width=2),
    select=aes.Shape(fill_color="#3b82f6", stroke_color="#1e40af"),
)

# Group-based aesthetics (different regions get different styles)
style = aes.ByGroup(
    __all=aes.Shape(fill_color="#e2e8f0"),  # Default for all regions
    tokyo=aes.Shape(fill_color="#fecaca"),   # Override for specific region
    _dividers=aes.Line(stroke_color="#666"),  # Line regions
)

# Indexed aesthetics for count/cycle modes
style = aes.Indexed(
    fill_color=["#e2e8f0", "#bfdbfe", "#60a5fa", "#2563eb"],  # Array indexed by count
)
```

**Type-safe aesthetic builders**:
- `aes.Shape()`: For filled regions (fill_color, fill_opacity, stroke_color, stroke_width, stroke_dasharray)
- `aes.Line()`: For stroke-only regions (stroke_color, stroke_width, stroke_dasharray)
- `aes.Text()`: For text elements (fill_color, font_size, font_family)
- `aes.ByState()`: Combines base/hover/select states
- `aes.ByGroup()`: Per-region or per-group overrides
- `aes.Indexed()`: Array-indexed aesthetics for count/cycle modes
- `linestyle.SOLID`, `linestyle.DASHED`, `linestyle.DOTTED`, `linestyle.DASH_DOT`: Line style constants

**Hover implementation**:
- Hover aesthetics defined in `aes.ByState(hover=...)` or via `aes_hover` parameter
- Rendered as separate overlay layer on top of all regions (solves SVG z-index border visibility)
- `pointer-events: none` ensures clicks pass through to base regions
- Snake_case keys in Python automatically converted to camelCase for React

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

**JSON Format** (v0.x and v1.x):

Shinymap supports two JSON formats:

**v0.x format** (backward compatible): String-based paths
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

**v1.x format** (polymorphic elements): Element objects with type information
```json
{
  "_metadata": {
    "viewBox": "0 0 100 100"
  },
  "circle_region": [{"type": "circle", "cx": 50, "cy": 50, "r": 30}],
  "rect_region": [{"type": "rect", "x": 10, "y": 10, "width": 30, "height": 20}],
  "path_region": [{"type": "path", "d": "M 0 0 L 100 100"}],
  "text_label": [{"type": "text", "x": 50, "y": 50, "text": "Label"}]
}
```

**Polymorphic Element Types** (v0.2.0):
- `Circle`: cx, cy, r
- `Rect`: x, y, width, height, rx, ry
- `Ellipse`: cx, cy, rx, ry
- `Path`: d (path data)
- `Polygon`: points
- `Line`: x1, y1, x2, y2
- `Text`: x, y, text, font_size, font_family, text_anchor, dominant_baseline

All element types support optional aesthetic attributes (fill, stroke, stroke_width) which are preserved for SVG export but NOT used by shinymap for interactive rendering.

**Key points**:
- v0.x format: Each region ID maps to **either a string or a list of strings**
- v1.x format: Each region ID maps to **a list of element objects**
- Both formats are automatically detected and supported throughout the stack
- The `Geometry` class converts between formats seamlessly
- `Geometry.from_svg()` returns v1.x format with polymorphic elements

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
geo = geo.path_as_line("_dividers", "_grid")         # Mark regions as lines (v0.2.0)

# Method chaining
final = (
    Geometry.from_svg("map.svg")
    .relabel({"hokkaido": ["path_1", "path_2"]})
    .set_overlays(["_border"])
    .path_as_line("_divider_lines")                  # Auto-apply stroke-only rendering
    .update_metadata({"source": "Custom", "license": "MIT"})
)

# Export to JSON
final.to_json("output.json")
final_dict = final.to_dict()

# Export to SVG (round-trip, preserves original aesthetics)
from shinymap.outline import export_svg
export_svg(final, "output.svg")

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

The `Outline` class is the recommended way to pass geometry to UI functions:

```python
from shinymap import Map, input_map, output_map
from shinymap.outline import Outline

outline = Outline.from_json("map.json")

# Input maps
input_map("my_input", outline, mode="multiple")

# Output maps with static outline
output_map("my_output", outline, tooltips=tooltips)

# Output maps with dynamic rendering
@render_map
def my_output():
    return Map(outline).with_value(counts)
```

## Shiny for Python (`shinymap`)

- Bundle the prebuilt JS/CSS assets plus the tiny demo geometry so `pip install shinymap` is ready to use out of the box.
- Provide helpers (`input_map`, `output_map`, `Map` / `render_map`) that hide the React layer completely.
- Input components surface their state via the declared Shiny input ID with mode-appropriate return types (see External ergonomic APIs above).
- Server helpers should minimize boilerplate while staying explicit and readable.
- Input helpers expose the same internal unified model as the JS component: values are `{id: count}` map internally, but the Python API returns mode-appropriate types (`str | None`, `list[str]`, or `dict[str, int]`).
- Define JSON payload schema for the React output: regions config, fills, static tooltips, value dict, optional colorbar metadata.
- State flow: the input component calls `Shiny.setInputValue(id, value)` for selections. The server sends updated payloads (including the value dict for selection state) to the output component. Hover is purely visual. Selection is derived from `value > 0`.
- Package requirements: MIT license, semver, Python ≥3.12, dependencies (`shiny>=…`). Ship wheel + sdist artifacts for PyPI.

### Color Scaling Utilities

Provide built-in color scaling functions for common statistical visualization patterns:

- **`scale_sequential(counts, region_ids, palette=SEQUENTIAL_BLUE, max_count=None)`**: Maps count data to sequential color scales (light to dark). Uses continuous color interpolation for smooth visual feedback. The `max_count` parameter allows fixed scaling for interactive visualizations.

- **`scale_diverging(values, region_ids, low_color, mid_color, high_color, midpoint=0.0)`**: Maps numeric values to diverging color scales (red-gray-blue style) for positive/negative data.

- **`scale_qualitative(categories, region_ids, palette=QUALITATIVE)`**: Maps categorical data to distinct colors, cycling through the palette if needed.

All utilities use the internal `lerp_hex()` helper for color interpolation. Pre-defined palettes (SEQUENTIAL_BLUE, SEQUENTIAL_GREEN, SEQUENTIAL_ORANGE, QUALITATIVE) are provided but customizable.

### Wash API (v0.2.0)

The `wash()` function provides a factory pattern for creating themed map components with consistent aesthetics:

```python
from shinymap import wash, aes

# Create themed map factory
w = wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#e2e8f0", stroke_color="#94a3b8"),
        hover=aes.Shape(stroke_color="#1e40af", stroke_width=2),
        select=aes.Shape(fill_color="#3b82f6"),
    ),
    line=aes.Line(stroke_color="#666", stroke_width=1),
)

# Use themed factory to create maps
w.input_map("region", outline, mode="single")
w.output_map("display", outline)

# Access resolved aesthetics
result = w.result  # WashResult with shape, line, text aesthetics
```

**Benefits**:
- Consistent styling across multiple map components
- Separates aesthetic configuration from map creation
- IDE autocomplete for aesthetic properties
- Type-safe aesthetic composition

### Static Analysis with StillLife (v0.3.0)

The `StillLife` class provides static aesthetic analysis and SVG export, enabling:
- Inspection of resolved aesthetics for any region
- Static SVG export with specific selection/hover states (for thumbnails, documentation, print)

```python
from shinymap import Wash, StillLife, aes, Outline

# Create builder via wash
wc = Wash(shape=aes.ByState(
    base=aes.Shape(fill_color="#e2e8f0"),
    select=aes.Shape(fill_color="#3b82f6"),
))
outline = Outline.from_json("map.json")
builder = wc.build(outline, value={"region_a": 1, "region_b": 0})

# Create snapshot for analysis
pic = StillLife(builder)
pic.aes("region_a")["fill_color"]  # '#3b82f6' (selected)
pic.aes("region_b")["fill_color"]  # '#e2e8f0' (not selected)
pic.aes_table()                     # All regions' aesthetics

# Export static SVG
pic.to_svg()                        # Returns SVG string
pic.to_svg(output="map.svg")        # Writes to file

# With hover state
pic_hovered = StillLife(builder, hovered="region_a")
pic_hovered.to_svg(output="map_hover.svg")
```

**Note**: `StillLife.to_svg()` applies shinymap's resolved aesthetics (selection, hover states). For SVG round-tripping that preserves original aesthetics, use `export_svg()` from `shinymap.outline` instead.

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

**Example with hover highlighting** (v0.2.0 syntax):

```python
from shinymap import input_map, aes

# Input map with custom aesthetics
input_map(
    "prefecture_selector",
    GEOMETRY,
    tooltips=TOOLTIPS,
    mode="single",
    aes=aes.ByState(
        base=aes.Shape(fill_color="#e5e7eb", stroke_color="#d1d5db", stroke_width=1),
        hover=aes.Shape(stroke_color="#374151", stroke_width=2),
        select=aes.Shape(fill_color="#3b82f6"),
    ),
)
```

The hover overlay is automatically rendered on top of everything, ensuring the darker, thicker border is always fully visible even when adjacent regions would normally hide parts of it.

**Non-Interactive Annotation Layers**

**Purpose**: Display static annotation layers that render above base regions but below selection/hover highlights.

**Use cases**:
- Dividing lines (e.g., separating repositioned insets from mainland)
- Administrative boundaries that aren't clickable regions
- Grid lines or reference markers

**Current implementation** (v0.2.0 - layers parameter):

```python
from shinymap import input_map, aes
from shinymap.outline import Outline

# Option 1: Use path_as_line() for line regions
outline = Outline.from_json("map.json").path_as_line("_dividers")
input_map("map_id", outline, mode="single")

# Option 2: Use aes.ByGroup for per-region styling
input_map(
    "map_id",
    outline,
    mode="single",
    aes=aes.ByGroup(
        __all=aes.Shape(fill_color="#e2e8f0"),
        _dividers=aes.Line(stroke_color="#999", stroke_width=2),
    ),
)
```

**Implementation details**:
- Overlay layer rendered AFTER interactive regions, BEFORE selection/hover
- `pointerEvents="none"` prevents click interference

**Layer System** (v0.2.0):

Regions can be assigned to non-interactive layers via Outline methods or the `layers` parameter:

```python
from shinymap import input_map, aes
from shinymap.outline import Outline

# Method 1: Use set_overlays() on Outline (currently implemented)
outline = Outline.from_json("map.json").set_overlays(["_border", "_dividers"])

# Method 2: Use merge_layers() for multiple layer types (currently implemented)
outline = outline.merge_layers({
    "underlays": ["_grid"],
    "overlays": ["_border"],
})

# Method 3: Planned - move_layer() for fluent API (not yet implemented)
outline = (
    Outline.from_json("map.json")
    .move_layer("underlay", "_grid", "_background")
    .move_layer("overlay", "_border", "_dividers")
    .move_layer("hidden", "_construction_guides")
)

# Method 4: Specify layers explicitly via input_map/output_map parameter
input_map(
    "map_id",
    outline,
    layers={
        "underlays": ["grid_lines"],
        "overlays": ["border_lines"],
        "hidden": ["construction_guides"],
    },
)
```

**Line regions** (v0.2.0):

Mark path regions that represent lines (not filled shapes) for automatic stroke-only rendering:

```python
# Mark regions containing lines described in path notation
outline = outline.path_as_line("_divider_lines", "_grid")

# These regions automatically get stroke-only aesthetics
# (fill="none", stroke applied from default line aesthetic)
```

**Render order** (5 layers, bottom to top):
1. **Underlay** - Background elements (grids, reference lines)
2. **Base regions** - Interactive regions with click/hover handling
3. **Overlay** - Non-interactive annotations (borders, labels)
4. **Selection overlay** - Selected regions (border visibility)
5. **Hover overlay** - Hovered region (always on top)

**Type-safe Aesthetic Builders**:

```python
from shinymap import aes

# IDE autocomplete for all aesthetic properties
grid_style = aes.Line(
    stroke_color="#ddd",
    stroke_width=1,
    stroke_dasharray=aes.line.dashed,  # Predefined: solid, dashed, dotted, dash_dot
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

# Static layer configuration in output_map (v0.2.0)
output_map(
    "prefecture_map",
    GEOMETRY,
    layers={"underlays": ["grid"], "overlays": ["dividers"]},
    aes=aes.ByGroup(
        grid=aes.Line(stroke_color="#eee", stroke_dasharray="5,5"),
        dividers=aes.Line(stroke_color="#999", stroke_width=2),
    ),
)
```

### Static vs Dynamic Parameters

Separate structural configuration (static) from reactive data (dynamic) to keep server code clean and focused.

**Current API** (v0.2.0+):

```python
from shinymap import output_map, render_map, Map, aes

# UI layer - define static structure once
app_ui = ui.page_fluid(
    output_map(
        "my_map",
        OUTLINE,                     # Static - defined once
        tooltips=TOOLTIPS,           # Static - defined once
        aes=aes.ByState(...),        # Static - defined once
        layers={"overlays": [...]},  # Static - defined once
    ),
)

# Server layer - focus only on reactive data transformations
@render_map
def my_map():
    # Just provide dynamic value - static config already in output_map()
    return Map().with_value(counts)
```

**Benefits**:
1. **Cleaner server code**: No repeated outline/tooltips/viewBox in every render function
2. **Better separation of concerns**: UI layer = structure, server layer = data transformations
3. **Easier maintenance**: Static configuration in one place, visible in UI definition
4. **Consistent with Shiny patterns**: Similar to how `output_plot(width=, height=)` defines figure size in UI, not in render function

Static parameters defined in `output_map()` are merged with dynamic parameters from `Map()` builders.

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

## Interactive Output Maps

Output maps can optionally respond to click events using `Display(clickable=True)` mode:

```python
from shinymap import output_map, render_map, Map
from shinymap.mode import Display

# UI - output map with click events enabled
output_map(
    "my_map",
    OUTLINE,
    mode=Display(clickable=True, input_id="clicked_region"),
)

@render_map
def my_map():
    return Map().with_value(status_values)

# Server - handle click events
@reactive.effect
@reactive.event(input.clicked_region)
def handle_click():
    region_id = input.clicked_region()
    # Handle the click (e.g., show details, copy to clipboard)
```

**Display mode options**:
- `Display()`: Hover only, no click (default)
- `Display(clickable=True)`: Emit click events to default input ID (output ID + "_click")
- `Display(clickable=True, input_id="custom")`: Emit click events to custom input ID
- `Display(aes=aes.Indexed(...))`: Value-indexed aesthetics for choropleth-style visualizations

### Alternative: `@render.ui` with `input_map`

For cases requiring fully dynamic UI (e.g., changing geometry, tooltips, or mode based on reactive inputs), the idiomatic Shiny pattern is `@render.ui`:

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
        PCCS_OUTLINE,
        tooltips=tooltips,
        mode="single",
    )
```

**When to use each approach**:

| Approach | Use When |
|----------|----------|
| `Display(clickable=True)` | Static structure, dynamic values; click events needed |
| `@render.ui` + `input_map` | Dynamic structure (geometry, tooltips, mode change reactively) |

**Performance comparison**: Future work. Both approaches use React reconciliation at the component level; benchmarking is needed to quantify differences for typical use cases.

## Open / Deferred Items

- Hover events remain visual only; revisit if live hover data is ever required.
- Optional decorator APIs and additional syntactic sugar are undecided; revisit once core UX is validated.
- Python adapter: add static per-region aesthetic overrides (per-id fills/props) to mirror React flexibility.
