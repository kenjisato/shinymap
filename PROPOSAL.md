# shinymap: Visual Input Components for Interactive Applications

## 1. Project Goals

**Core Mission**: Provide visual, shape-based alternatives to standard HTML form inputs and statistical visualizations for interactive applications across React, R Shiny, and Python Shiny.

### Input Components: Visual Alternatives to Form Controls

shinymap transforms familiar input interaction patterns into visual, spatial interfaces:

- `input_map(mode="single")` → Visual radio buttons (select one region)
- `input_map(mode="multiple")` → Visual checkboxes (select multiple regions)
- `input_map(mode="count")` → Visual counter/range input (click to increment with smooth color feedback)

### Output Components: Simplified Statistical Visualization

Beyond interactive inputs, shinymap's `output_map` provides a declarative API for common statistical visualizations:

```python
# Traditional approach: complex plotting library setup
import plotly.express as px
fig = px.choropleth(df, locations="region", color="value", ...)

# shinymap approach: declarative, focused API
Map(GEOMETRY).with_fill_color(scale_sequential(counts, region_ids))
```

The output component offers:
- **Simplified API** for common patterns (choropleth maps, categorical coloring, diverging scales)
- **Geometry agnostic** design (works with any SVG paths, not just geographic maps)
- **Built-in color utilities** (`scale_sequential`, `scale_diverging`, `scale_qualitative`)
- **Consistent styling** between input and output maps for cohesive UIs

This dual focus—interactive inputs AND simplified outputs—makes shinymap valuable even for non-interactive visualizations.

### Multi-Platform Architecture

shinymap is designed as a layered, multi-platform system:

**Current Development** (Core Library):
- **React component library** (`packages/shinymap/js/`) - Foundation for all platforms
- **Python Shiny adapter** (`packages/shinymap/python/`) - Bindings for Shiny for Python
- **R Shiny adapter** (planned) - Bindings for R Shiny users

**Future Extension** (Geographic Toolkit):
- **Core shinymap** provides geometry-agnostic interaction and visualization
- **shinymap-geo** extension will add:
  - Geographic data loading (GeoJSON, TopoJSON, shapefiles)
  - Coordinate projection support
  - Integration with R's `sf` package and Python's `geopandas`
  - Pre-packaged geographic datasets (countries, US states, etc.)

This architecture ensures:
1. **React library maintenance** is central to the project (all platforms depend on it)
2. **R Shiny support** is a first-class goal (many users love R Shiny!)
3. **Core vs. geo separation** keeps the base library lightweight and flexible

### Key Design Principles

1. **Input-First Philosophy**: The `input_map` component treats regions as interactive controls first, visualizations second. Users interact with shapes like clicking radio buttons or checkboxes.

2. **Geometry Agnostic**: Works with any SVG path geometry—geographic maps, abstract shapes, diagrams, floor plans, anatomical illustrations, or custom visualizations.

3. **Unified Count Model**: All interaction modes use a single internal representation (`{region_id: count}`), enabling smooth transitions between interaction patterns and consistent color mapping.

4. **Smooth Visual Feedback**: Every interaction produces a visible change. Color interpolation ensures gradual intensity changes, not discrete jumps.

5. **Declarative API**: Fluent methods (`with_fill_color()`, `with_stroke_width()`, `with_counts()`) and built-in color utilities make common patterns simple and readable.

### Non-Goals

- **Not a full GIS toolkit**: Advanced geospatial analysis, projections, and coordinate transformations belong in the **shinymap-geo** extension (future work), not the core library.

- **Not a general plotting library**: For publication-quality static visualizations with full customization, use specialized libraries (ggplot2, matplotlib, plotly). shinymap focuses on interactive patterns and common statistical visualizations.

- **Not region-data preprocessing**: shinymap expects geometry data (SVG paths) to be provided. Shapefile parsing, simplification, and format conversion belong in **shinymap-geo** or external tools.

- **Not a general-purpose UI framework**: shinymap provides map/shape-based inputs and outputs, not buttons, dropdowns, or other standard UI elements.

## 2. Prior Art

### Clickable SVG Regions: Not New in Web Development

The core technical pattern—clickable SVG regions with state management—is **well-established in the React/web ecosystem**:

- **`react-svg-map`**: SVG-based maps with clickable regions and selection state
- **`react-simple-maps`**: Geographic visualizations with interaction support
- **Generic pattern**: Many web apps implement custom clickable diagrams (seat selectors, floor plans, etc.)

**What's not new**: The React implementation of clickable SVG regions and state handling.

**What shinymap contributes**: Integration of this pattern into the Shiny ecosystem (R and Python) with a **systematic design as input components** rather than ad-hoc interactive maps.

### R Shiny Extensions: Rich Ecosystem, But Gaps Remain

**Map-oriented packages**:
- **`leaflet` + `leaflet.extras` + `mapedit`**: Interactive maps with drawing/editing, returning shapes/GeoJSON. Powerful for GIS workflows but framed as "map editing/exploration", not as general **form input** components analogous to radio buttons or checkboxes.

**Visual input packages**:
- **`shinyWidgets`**: Rich input controls (button-like radios, fancy pickers) with no spatial/geometric layout support.
- **`vfinputs`** (Visual Filter Inputs): Visual filter specification, mostly chart/slider interfaces, not arbitrary SVG regions.
- **`clickableImageMap`**: Makes tableGrob cells clickable (image map pattern), scoped to tables rather than arbitrary SVG or maps.

**Gap identified**: R Shiny has advanced interactive maps and many custom inputs, but **no package systematically treats arbitrary SVG regions as first-class input controls** with radio/checkbox/counter semantics.

### Shiny for Python: Younger Ecosystem

- **Interactive mapping**: `ipyleaflet`, `pydeck` can be used as outputs, but no well-established **visual input component** package.
- **Other Python frameworks** (Dash, Bokeh): Have clickable choropleths/maps, but not framed as a **unified family of input widgets**.

**Opportunity**: Shiny for Python has a smaller ecosystem than R Shiny. A visual input/choropleth package that works across both platforms from day one fills a real gap for Python users.

### Statistical Visualization Libraries

**ggplot2 (R)**: `geom_map()`, `geom_sf()` for static choropleth maps. Excellent for publication graphics, not designed for interactive input.

**plotly/Dash (Python/R)**: Rich interactive visualizations with choropleth support. Optimized for exploration/dashboards, but heavyweight for simple input controls. Interaction is secondary to visualization.

**Leaflet/Folium**: Geographic-first with GIS features (projections, layers, markers). Assumes geographic data and returns shapes/GeoJSON.

**Observable Plot (JavaScript)**: Declarative visualization with elegant API. JavaScript-only, no Shiny integration.

### Realistic Differentiation for shinymap

Given the above landscape, shinymap's **honest differentiation points** are:

1. **Input-first design philosophy**: Start from HTML input semantics (single-choice, multiple-choice, counters) and treat SVG/geometry as the visualization layer. Return simple values (string, list, dict), not shapes/GeoJSON.

2. **Geometry-agnostic approach**: Same API for geographic maps, abstract diagrams, floor plans, anatomical illustrations—anything representable as SVG paths.

3. **Unified count model**: All modes use `{region_id: count}` internally, feeding both input state and color scaling. Switching modes or between input/output is conceptually simple.

4. **Cross-ecosystem design from day one**: React core with parallel bindings for R Shiny and Python Shiny. Not "JavaScript first, then port" or "R first, then Python binding"—but first-class, consistent design across platforms.

5. **Filling gaps in both Shiny ecosystems**: R Shiny lacks geometry-agnostic visual inputs; Python Shiny lacks mature visual input packages entirely.

## 3. User Story

### Story 1: Quiz Application - Color Wheel Learning Tool

**Context**: An art teacher creates an interactive quiz where students identify color relationships by clicking on a color wheel divided into regions.

**Without shinymap**:
```python
# Limited to standard radio buttons with text labels
ui.input_radio_buttons("color_answer", "Select the complementary color:",
                       choices=["Red", "Orange", "Yellow", "Green", "Blue", "Purple"])
```

**With shinymap**:
```python
# Visual, intuitive selection on an actual color wheel
input_map("color_answer", COLOR_WHEEL_GEOMETRY, mode="single", cycle=4)
```

Students click directly on the color wheel's regions. The `cycle=4` parameter creates a red→yellow→green→gray cycling pattern, perfect for quiz feedback without separate answer-checking logic.

### Story 2: Election Results Dashboard - Statistical Output

**Context**: A data journalist creates an election results dashboard showing vote margins by county.

**Traditional approach**:
```python
import plotly.express as px
# Requires data wrangling, GeoJSON loading, complex configuration
fig = px.choropleth(df, geojson=counties_geojson, locations="fips",
                   color="margin", color_continuous_scale="RdBu", ...)
```

**With shinymap**:
```python
# Declarative, focused API
@render_map
def election_map():
    return (
        Map(COUNTIES_GEOMETRY)
        .with_fill_color(scale_diverging(vote_margins, county_ids,
                                         low_color="#ef4444", high_color="#3b82f6"))
        .with_tooltips(county_names)
    )
```

The simplified API makes common patterns (diverging color scales, tooltips) straightforward without sacrificing flexibility.

### Story 3: Political Preference Survey - Multiple Region Selection

**Context**: A political scientist surveys constituents about which congressional districts they're familiar with.

**Without shinymap**:
```python
# Long list of checkbox labels
ui.input_checkbox_group("districts", "Select all districts you're familiar with:",
                        choices=[f"District {i}" for i in range(1, 54)])
```

**With shinymap**:
```python
# Visual map with clickable regions
input_map("districts", STATE_DISTRICTS_GEOMETRY, mode="multiple", max_selection=10)
```

Users click directly on the map regions they recognize. The `max_selection=10` parameter limits selections, and the visual interface makes spatial patterns immediately obvious.

### Story 4: Event Registration - Seat Selection with Visual Feedback

**Context**: A theater website lets users select seats, showing real-time availability as seats are clicked.

**Without shinymap**:
```python
# Complex grid of buttons with manual state management
# (requires custom JavaScript for visual feedback)
```

**With shinymap**:
```python
# Interactive seat map with automatic visual feedback
input_map("seats", THEATER_SEATING_GEOMETRY, mode="count", value={})

@render_map
def seat_availability():
    selections = input.seats() or {}
    # Color intensity shows selection frequency
    return Map(THEATER_SEATING_GEOMETRY).with_fill_color(
        scale_sequential(selections, list(THEATER_SEATING_GEOMETRY.keys()))
    )
```

Each click increments a counter, with color intensity showing how often each seat has been selected (useful for admin dashboards showing popular vs. unpopular seats).

### Story 5: Medical Education - Anatomy Labeling Practice

**Context**: A medical student practices identifying anatomical structures by clicking on diagram regions.

**Without shinymap**:
```python
# Separate image and checkbox list, hard to connect visually
```

**With shinymap**:
```python
# Direct interaction with anatomical diagram
input_map("identified_structures", HEART_ANATOMY_GEOMETRY, mode="multiple")

@render_map
def anatomy_feedback():
    identified = input.identified_structures() or []
    correct = ["aorta", "left_ventricle", "right_atrium"]
    colors = {
        region: "#22c55e" if region in correct else "#ef4444"
        for region in identified
    }
    return Map(HEART_ANATOMY_GEOMETRY).with_fill_color(colors)
```

Students click directly on the diagram, with immediate color-coded feedback on correctness.

## 4. First Sketch

### Platform Architecture

```
┌─────────────────────────────────────────────┐
│  React Component Library (Core)             │
│  packages/shinymap/js/                      │
│  - InputMap, OutputMap components           │
│  - Interaction logic, visual feedback       │
│  - Geometry-agnostic SVG rendering          │
└─────────────────┬───────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
┌─────▼─────────┐   ┌─────────▼──────┐
│ Python Shiny  │   │   R Shiny      │
│ Adapter       │   │   Adapter      │
│ (Current)     │   │   (Planned)    │
└───────────────┘   └────────────────┘

Future Extension:
┌─────────────────────────────────────────────┐
│  shinymap-geo                               │
│  - GeoJSON/TopoJSON loading                 │
│  - Coordinate projections                   │
│  - Pre-packaged geographic datasets         │
│  - Integration with sf/geopandas            │
└─────────────────────────────────────────────┘
```

### Input Component Analogy

```
Standard HTML                shinymap Equivalent                Use Case
─────────────────           ──────────────────────             ─────────────────
<input type="radio">    →   input_map(mode="single")           Select one region
                            - Click to select                   (quiz answers,
                            - Click again to deselect           preference choices)
                            - Visual highlight for selection

<input type="checkbox"> →   input_map(mode="multiple")         Select many regions
                            - Click to toggle selection         (familiar areas,
                            - max_selection parameter           multi-choice quiz)
                            - Visual highlight for each

<input type="range">    →   input_map(mode="count")            Incremental counter
                            - Click to increment count          (ratings, frequency,
                            - Smooth color intensity feedback   seat popularity)
                            - cycle parameter for wrapping
```

### Basic API Structure

**Input Component** (form control analog):
```python
from shinymap import input_map

# Radio button analog: select one US state
input_map("selected_state", US_STATES_GEOMETRY, mode="single")

# Checkbox analog: select multiple prefectures
input_map("familiar_prefectures", JAPAN_PREFS_GEOMETRY, mode="multiple")

# Counter/range analog: click to increment with visual feedback
input_map("region_ratings", REGIONS_GEOMETRY, mode="count")
```

**Output Component** (simplified statistical visualization):
```python
from shinymap import output_map, render_map, Map
from shinymap import scale_sequential, scale_diverging, scale_qualitative

@render_map
def results_map():
    counts = input.region_ratings() or {}
    return (
        Map(REGIONS_GEOMETRY)
        .with_fill_color(scale_sequential(counts, list(REGIONS_GEOMETRY.keys())))
        .with_counts(counts)  # Show numeric labels
        .with_tooltips(region_names)
    )
```

**Color Scaling Utilities**:
```python
# Sequential: light to dark based on count
fills = scale_sequential(counts, region_ids, palette=SEQUENTIAL_BLUE)

# Diverging: red-gray-blue for positive/negative values
fills = scale_diverging(values, region_ids, midpoint=0.0)

# Qualitative: categorical colors
fills = scale_qualitative(categories, region_ids, palette=QUALITATIVE)
```

### Visual Feedback Example

For count mode, every click produces a visible color change through continuous interpolation:

```
Click sequence on a region:
  No clicks → palette[0] (lightest blue)
  1 click   → blend(palette[0], palette[1], t=0.1)
  2 clicks  → blend(palette[0], palette[1], t=0.2)
  ...
  5 clicks  → blend(palette[2], palette[3], t=0.5)
  ...
  10 clicks → palette[-1] (darkest blue)
```

This ensures smooth, intuitive visual feedback analogous to a range slider's thumb position.

### Geometry Flexibility

```python
# Geographic map (classic use case)
input_map("country", WORLD_COUNTRIES, mode="single")

# Abstract shapes (quiz, color wheel)
input_map("shape_answer", {"circle": "M...", "square": "M...", "triangle": "M..."},
          mode="single")

# Floor plan (room selection)
input_map("rooms", BUILDING_FLOOR_PLAN, mode="multiple")

# Anatomical diagram (medical education)
input_map("organs", HEART_ANATOMY, mode="multiple")
```

The power of shinymap is that the same interaction patterns (single select, multiple select, count/increment) and visualization APIs work across any visual domain—not just maps.

## 5. Technical Considerations and Future Work

### Data Model and API Boundaries

**Region identifiers**:
- All region IDs will be **strings** for JSON stability across R, Python, and JavaScript.
- This avoids subtle differences between languages (e.g., numeric vs. string keys in dictionaries/objects).

**Geometry representation**:
- JSON format: `{ region_id: path_string | path_array, "_metadata": {...} }`
- Paths can be single strings or arrays of strings for multi-part regions
- This serves as the target format for:
  - `shinymap-geo` conversions from `sf` (R) / `geopandas` (Python)
  - Manual SVG integration via the `Geometry` class
  - Pre-packaged datasets

**Return types across platforms**:
- **Python**: `dict[str, int]` for count mode, `list[str]` for multiple mode, `str | None` for single mode
- **R**: Named integer vector for count mode, character vector for multiple mode, single string or NULL for single mode
- **React**: JavaScript objects/arrays following standard patterns

### Performance and Rendering Optimization

**Challenge**: SVG rendering can be slow with large maps (hundreds or thousands of regions).

**Current approach**:
- React components separate **static** (path geometry) and **dynamic** (fill colors, stroke styles) aspects
- Color changes update attributes on existing DOM elements rather than re-rendering entire SVG

**Future optimizations** (when performance becomes critical):
1. **Memoization**: Use `React.memo()` and `useMemo()` to prevent unnecessary re-renders
2. **Selective updates**: Only update regions whose state has changed
3. **Simplification utilities**: Provide tools to reduce SVG path complexity for large geographic datasets
4. **Canvas fallback**: For very large maps (1000+ regions), consider Canvas-based rendering with SVG overlay for interactivity
5. **Virtual rendering**: For maps with many off-screen regions, consider viewport-based rendering

**Note**: We will address rendering performance as real-world usage reveals bottlenecks. Premature optimization is avoided in favor of clean, maintainable code.

### Accessibility and Keyboard Support

**Goal**: These are input components, not just pictures. Proper accessibility is a genuine differentiator.

**Planned features**:
- **Keyboard navigation**: Tab/Shift+Tab to move between regions
- **Keyboard selection**: Enter/Space to toggle selection or increment count
- **ARIA roles**: Appropriate roles for radio groups (`role="radiogroup"`), checkbox groups (`role="group"`), etc.
- **ARIA attributes**: `aria-selected`, `aria-checked`, `aria-label` for each region
- **Focus indicators**: Visual feedback for keyboard focus distinct from mouse hover

**Status**: Basic mouse interaction implemented. Keyboard support and ARIA attributes are high-priority future work.

### Mode Semantics and Future Extensions

**Current modes**:
- `mode="single"`: Radio button analog (count ∈ {0,1}, sum ≤ 1)
- `mode="multiple"`: Checkbox analog (count ∈ {0,1}, no constraint)
- `mode="count"`: Counter/range analog (count ∈ {0,1,...,K})

**Open design questions**:
- **Count limits**: How to specify max count, step size, reset behavior?
- **Color mapping**: Linear vs. categorical scales for different count ranges?
- **Future modes**: "rating" (star-based), "ordered categories" (low/medium/high)?

All modes fit the unified `{region_id: count}` model, ensuring consistency.

### Scope of Core vs. Geo Extension

**Core library** (`shinymap`):
- Geometry-agnostic input/output components
- Unified count model and mode semantics
- Color scaling utilities for sequential, diverging, qualitative data
- React components and Shiny (R/Python) adapters

**Geo extension** (`shinymap-geo`, future):
- Geographic data loading (GeoJSON, TopoJSON, Shapefiles)
- Coordinate projection support
- Integration with `sf` (R) and `geopandas` (Python)
- Pre-packaged datasets (world countries, US states, etc.)
- Geometry simplification and optimization utilities

This separation keeps the core library lightweight while allowing advanced GIS features for users who need them.

### Cross-Platform Example

The same conceptual API works across React, Python, and R:

**React**:
```jsx
import { InputMap, OutputMap } from '@shinymap/react';

<InputMap geometry={REGIONS} mode="single" onChange={handleChange} />
```

**Python (Shiny)**:
```python
from shinymap import input_map, render_map, Map

input_map("regions", REGIONS_GEOMETRY, mode="single")

@render_map
def output(): return Map(REGIONS_GEOMETRY).with_fill_color(...)
```

**R (Shiny)** (planned):
```r
library(shinymap)

inputMap("regions", REGIONS_GEOMETRY, mode = "single")

output$map <- renderMap({
  map(REGIONS_GEOMETRY) |> with_fill_color(...)
})
```
