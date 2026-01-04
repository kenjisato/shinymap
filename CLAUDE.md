# Guide for AI Assistants

This document provides context for AI assistants (like Claude) working on the shinymap project.

## Project Overview

**shinymap** provides **visual alternatives to standard HTML form inputs** using SVG regions:
- `input_map(mode="single")` → Visual radio buttons (select one region)
- `input_map(mode="multiple")` → Visual checkboxes (select multiple regions)
- `input_map(mode=Count())` → Visual counter (click to increment with visual feedback)
- `input_map(mode=Cycle(n))` → Visual state cycling (n discrete states)

Additionally, `output_map` provides simplified statistical visualizations (choropleths, categorical coloring) with a declarative API.

**Not just maps**: Works with any SVG paths - geographic maps, diagrams, floor plans, anatomical illustrations, etc.

## Architecture

**Multi-platform design**:
- **React core** (`packages/shinymap/js`): TypeScript/React components (InputMap/OutputMap)
- **Python Shiny** (`packages/shinymap/python`): Shiny for Python bindings + prebuilt assets
- **R Shiny** (`packages/shinymap/r`): Planned, will mirror Python API

**Core vs. Geo separation**:
- **Core library** (current): Geometry-agnostic components, lightweight demo geometry
- **shinymap-geo** (future): GeoJSON/TopoJSON loading, projections, `sf`/`geopandas` integration, pre-packaged geographic datasets

## Key Design Principles

1. **Input-first philosophy**: These are form controls, not just visualizations. Return simple values (`str`, `list`, `dict`), not shapes/GeoJSON.

2. **Unified value model**: Internally uses `{region_id: int}` representation. Python API transforms this to ergonomic types:
   - `mode="single"` or `Single()` → `str | None`
   - `mode="multiple"` or `Multiple()` → `list[str]`
   - `Count()` or `Cycle(n)` → `dict[str, int]`
   - `Display()` for output_map → values index into aesthetics; optionally clickable with `clickable=True`

3. **Geometry-agnostic**: Same API works for any SVG paths, not geography-specific.

4. **Pre-1.0.0**: Breaking changes are acceptable while optimizing for clarity and performance. Don't add backward-compatibility shims yet.

5. **Avoid over-engineering**: Only make changes directly requested or clearly necessary. Keep solutions simple and focused.

6. **Late serialization**: Keep data as typed Python objects as long as possible. Serialization to dict/JSON should only happen at the JavaScript boundary (when sending data to the frontend). This separation keeps business logic testable and maintains type safety throughout the Python layer. See [design/aes-resolution.md](design/aes-resolution.md) for the aesthetic resolution architecture.

## Development Environment

- **Python**: Minimum 3.12, use `uv` for dependency management, `hatch` for builds
- **JavaScript/TypeScript**: React components in `packages/shinymap/js`
- **License**: MIT (keep all dependencies MIT-compatible)

## Development Commands (Mandatory)

**ALWAYS use the Makefile** for build operations. NEVER manually run npm/tsc/esbuild commands.

| Command | Purpose |
|---------|---------|
| `make install` | Install all dependencies (npm + uv sync) |
| `make build` | Full build: TypeScript → bundle → Python assets |
| `make test` | Run Python tests |
| `make lint` | Run TypeScript linter |
| `make format` | Format TypeScript code |

**Python commands** (always prefix with `uv run`):

| Command | Purpose |
|---------|---------|
| `uv run pytest packages/shinymap/python/tests -v` | Run Python tests |
| `uv run ruff check packages/shinymap/python` | Lint Python code |
| `uv run ruff format packages/shinymap/python` | Format Python code |
| `uv run mypy packages/shinymap/python/src` | Type check Python |

**Prohibitions**:
- NEVER run `pip install` - use `uv sync` or `uv add <package>`
- NEVER run `npm install` manually - use `make install`
- NEVER run `tsc` or `esbuild` directly - use `make build`

## Git Workflow

We use a **Main-Only Strategy**:

- **`dev` branch**: Default development branch. All work happens here.
- **`main` branch**: Release branch. Only updated via PRs from `dev`.
- **Auto-tagging**: When PR merges to `main`, version tag is auto-created (skips `-dev` versions).
- **Auto-publish**: Tag push triggers PyPI publish.

**Key points for AI assistants**:
- Always work on `dev` branch (check with `git branch`)
- Never push directly to `main`
- Version in `pyproject.toml` should be `X.Y.Z-dev` during development
- See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed release process

## Quality Gates (Before Declaring Complete)

A task is NOT complete until these checks pass. Run them before any commit.

**For TypeScript changes**:
```bash
make lint && make format
make build  # CRITICAL: bundles JS into Python package
```

**For Python changes**:
```bash
uv run ruff check packages/shinymap/python
uv run ruff format packages/shinymap/python
uv run mypy packages/shinymap/python/src
```

**For any code changes**:
```bash
make test  # Must pass
```

**Rules**:
- If tests fail, fix them before moving on
- If lint fails, fix before committing
- If React code changed, `make build` is mandatory before testing Python

## Key Documents

Read these for detailed context:

- **[SPEC.md](SPEC.md)**: Technical specification, API philosophy, implementation details
- **[PROPOSAL.md](PROPOSAL.md)**: Project proposal for academic journals (e.g., JOSS), user stories, honest prior art assessment
- **[README.md](README.md)**: High-level repository overview
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Practical development workflows, command sequences, working directory guidance (for human contributors)
- **[SHINY-FOR-PYTHON.md](SHINY-FOR-PYTHON.md)**: Best practices for Shiny for Python development
- **[design/](design/)**: Detailed implementation plans for features mentioned in SPEC but not yet implemented

## Document Maintenance

**Keep documents synchronized when making changes**:

- **Design decisions change** → Update [SPEC.md](SPEC.md) and [PROPOSAL.md](PROPOSAL.md)
- **New user-facing API stabilizes** → Update [README.md](README.md) with examples
- **Implementation details needed** → Create detailed design document in [design/](design/)

Check these documents before making significant changes to ensure alignment with project philosophy.

## Snapshot and Context Discipline

### Before Experimental Changes

Create a checkpoint before risky or exploratory changes:
```bash
git add -A && git commit -m "WIP: checkpoint before <experiment>"
```

If the experiment fails, rollback is easy: `git reset --hard HEAD~1`

### Multi-Step Tasks

For complex tasks with multiple steps:
1. Make a checkpoint commit after each significant milestone
2. Use clear commit messages: "WIP: completed step N of task X"
3. This allows partial rollback if later steps fail

### Commit Granularity

**Target: One commit per checklist item.** This provides:
- Safe rollback points at each step
- Clear progress visibility
- Mental peace for both user and AI

This won't always be possible (e.g., atomic changes spanning multiple files), but it's the target granularity.

### Context Management (CRITICAL)

**Two types of documentation**:
- **`design/`** - Long-term design goals and architectural decisions (create before large features)
- **`COMMUNICATION.md`** - Short-term session logging for progress tracking and resumption

When context is getting full or before switching tasks, write to `COMMUNICATION.md`:

1. **Write actionable resumption notes**:
   ```markdown
   ## Session Checkpoint - [Date/Time or Task Name]

   ### Current Task
   [Exact user request that started this work]

   ### Completed
   - [Specific file]: [What was changed and why]
   - [Specific file]: [What was changed and why]

   ### In Progress
   - [File being edited]: [Current state, what's done, what remains]

   ### Next Steps (in order)
   1. [Exact action with file paths]
   2. [Exact action with file paths]
   3. [Exact action with file paths]

   ### Context a Fresh Session Needs
   - [Key decision made and why]
   - [Gotcha or trap to avoid]
   - [Reference: see design/foo.md for details]
   ```

2. **Commit the checkpoint**:
   ```bash
   git add -A && git commit -m "WIP: checkpoint - see COMMUNICATION.md for resumption"
   ```

3. **What NOT to do**:
   - ❌ Vague messages: "WIP: working on feature X"
   - ❌ Trusting memory: "I'll remember what I was doing"
   - ❌ Commit message only: Too short for complex task state

### Side Questions and Diversions

When user asks a question unrelated to the current task:
1. Assess: Is this a quick question (< 2 min) or a major diversion?
2. If quick: Answer briefly, return to task
3. If major diversion:
   - Write current state to `COMMUNICATION.md`
   - Make checkpoint commit
   - Then switch to the new task
4. Consider asking: "Should I complete the current task first?"

### Using GitHub Issues

**When to create an issue**:
- Bug discovered while working on something else (don't fix it now, track it)
- Feature idea mentioned by user worth tracking for later
- Task too large to complete in current session and needs to be parked
- Design question that needs user input before implementation

**When NOT to use issues**:
- Mid-task checkpoints (use `COMMUNICATION.md`)
- Implementation details already decided (use `design/`)
- Quick fixes that will be done this session

**Workflow**:
- If you discover an unrelated bug → `gh issue create`, continue current task
- If user mentions a feature idea → ask "Should I create an issue for this?"
- If task must be parked → create issue with context, reference in `COMMUNICATION.md`

## Performance Philosophy

**Input components**: Already highly efficient. Click interactions update only changed regions via React reconciliation.

**Output components**: Follow standard Shiny patterns - `@render_map` re-executes and sends complete payload, React reconciliation updates DOM. This is a **general Shiny pattern** (like matplotlib regeneration), not a shinymap-specific problem.

**When performance matters** (>500 regions, expensive computations, high interaction frequency):
- Use action buttons, debouncing, caching (standard Shiny patterns)
- Consider `update_map()` for partial updates (see [design/update_map_implementation.md](design/update_map_implementation.md))
- Defer optimizations until real-world use cases demonstrate need

## Common Patterns

### Input Map with wash()

The `wash()` function creates configured map functions with custom default aesthetics:

```python
from shinymap import wash, aes, PARENT

# Create wash with custom theme
wc = wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#e2e8f0", stroke_color="#94a3b8", stroke_width=0.5),
        select=aes.Shape(fill_color="#bfdbfe", stroke_color="#1e40af"),
        hover=aes.Shape(stroke_width=PARENT.stroke_width + 0.5),
    ),
    line=aes.Line(stroke_color="#94a3b8", stroke_width=0.5),
)

# Use washed functions
wc.input_map("region", outline, mode="single")
wc.output_map("my_map", outline)

@wc.render_map
def my_map():
    return Map().with_value(counts)
```

### Output Map with Per-Region Colors

Use `aes.ByGroup` to set per-region aesthetics:

```python
from shinymap import Map, aes

@wc.render_map
def categorical_map():
    # Create per-region aesthetics
    region_aes = {
        region: aes.Shape(fill_color=COLORS[category])
        for region, category in categories.items()
    }
    return Map(aes=aes.ByGroup(**region_aes))
```

### Count Mode with Indexed Aesthetics

```python
from shinymap import aes
from shinymap.mode import Count
from shinymap.aes.color import SEQUENTIAL_ORANGE

wc.input_map(
    "counts",
    outline,
    mode=Count(aes=aes.Indexed(fill_color=["lightgray", *SEQUENTIAL_ORANGE])),
)
```

### Color Scale Functions

```python
from shinymap.aes.color import scale_sequential, scale_diverging, scale_qualitative
from shinymap.aes.color import SEQUENTIAL_BLUE, QUALITATIVE

# Sequential (count data)
fills = scale_sequential(counts, region_ids, palette=SEQUENTIAL_BLUE, max_count=10)

# Diverging (positive/negative)
fills = scale_diverging(values, region_ids, low_color="#ef4444", mid_color="#f3f4f6", high_color="#3b82f6")

# Qualitative (categories)
fills = scale_qualitative(categories, region_ids, palette=QUALITATIVE)
```

### MapBuilder Methods

Available `MapBuilder` methods (via `Map()` or method chaining):

```python
Map(outline, tooltips=tooltips, value=value, aes=aes_config)
# Or fluent API:
Map(outline).with_value(value).with_aes(aes_config)
```

- `.with_value(dict)` - Set region values. Values also determine selection: value > 0 means selected
- `.with_aes(ByGroup|ByState|Shape)` - Set aesthetic configuration
- `.with_tooltips(dict)` - Set region tooltips
- `.with_view_box(tuple)` - Set SVG viewBox
- `.with_layers(dict)` - Set layer configuration

Note: There is NO `.with_fill_color()` method. Use `.with_aes(aes.ByGroup(...))` for per-region colors.

### Value-Based Selection Model

Selection state is derived from `value`:
- `value = 0` or missing: region is not selected (base aesthetic applied)
- `value > 0`: region is selected (select aesthetic applied)

This is the unified model. Encode selection state directly in the value dict:

```python
Map(outline, value={"a": 1, "b": 1, "c": 0})  # a, b are selected; c is not
```

### Display Mode for Output Maps

`Display()` mode enables value-indexed aesthetics on output maps. By default, regions respond to hover but not click. Set `clickable=True` to emit click events.

```python
from shinymap import output_map
from shinymap.mode import Display

# Basic display mode: hover only, value indexes into colors
output_map(
    "status_map",
    outline,
    mode=Display(aes=aes.Indexed(
        fill_color=["#gray", "#green", "#yellow", "#red"]
    ))
)

# Clickable display mode: emits click events
output_map(
    "clickable_map",
    outline,
    mode=Display(clickable=True, input_id="clicked_region")
)

# In server:
@reactive.effect
@reactive.event(input.clicked_region)
def handle_click():
    region_id = input.clicked_region()
    # Handle the click...
```

## Honest Positioning

**What's NOT new**: Clickable SVG regions are well-established in React ecosystem (`react-svg-map`, `react-simple-maps`).

**What shinymap contributes**:
1. Integration into Shiny ecosystems (R/Python) with input-first design
2. Geometry-agnostic approach (not geography-specific)
3. Unified count model enabling consistent behavior across modes
4. Cross-platform design from day one (React, R Shiny, Python Shiny)
5. Filling gaps: R Shiny lacks geometry-agnostic visual inputs; Python Shiny lacks mature visual input packages

## Communication Style

- **Concise and direct**: Avoid superlatives, excessive praise, unnecessary validation
- **Technical accuracy over agreement**: Apply rigorous standards, disagree when necessary
- **Investigate uncertainty**: Find truth first rather than confirming user beliefs
- **No timelines**: Provide concrete implementation steps, not time estimates

## When Starting New Tasks

1. Verify you're on `dev` branch: `git branch`
2. Pull latest: `git pull`
3. Run `make install` if dependencies might have changed
4. Check `COMMUNICATION.md` for any in-progress work from previous sessions
5. For complex tasks, consider a checkpoint commit before starting
6. Check [SPEC.md](SPEC.md) for current implementation status and philosophy
7. Check [design/](design/) for detailed implementation plans if feature is mentioned in SPEC
8. Check [CONTRIBUTING.md](CONTRIBUTING.md) for practical workflows and command sequences (especially useful for understanding working directories)
9. Check [SHINY-FOR-PYTHON.md](SHINY-FOR-PYTHON.md) for Python-specific patterns and best practices
10. For new features, assess whether detailed design document is needed before implementation
11. Prefer editing existing files over creating new ones
12. Use TodoWrite tool for multi-step tasks to track progress
13. After implementing changes, update relevant documentation (SPEC, PROPOSAL, README as appropriate)

## SVG Rendering and Overlay Architecture

**Challenge**: SVG elements render in DOM order (painter's algorithm), where later elements appear on top. This creates border visibility issues:
- SVG strokes are centered on paths (50% inside, 50% outside)
- Adjacent regions' fills can hide neighboring regions' strokes
- Transparent strokes are invisible (adjacent fills show through)
- Selected/hovered regions' borders get partially hidden by non-selected neighbors

**Solution**: Layered overlay rendering ensures important elements (selected, hovered) are always visible.

**Rendering order** (5 layers, bottom to top):
1. **Underlay regions**: Background elements (grids, reference lines) with `pointer-events: none`
2. **Base regions**: Interactive regions with normal aesthetics and click handlers
3. **Overlay regions**: Non-interactive annotations (dividers, borders) with `pointer-events: none`
4. **Selection overlay**: Duplicates of selected/active regions with selection aesthetics and `pointer-events: none`
5. **Hover overlay**: Duplicate of hovered region with hover aesthetics and `pointer-events: none`

**Hidden regions**: Regions in the `hidden` layer are not rendered at all.

This multi-layer approach guarantees:
- Selected regions' borders are fully visible on top of non-selected regions
- Hovered regions' borders are fully visible on top of everything
- All overlays use `pointer-events: none` so clicks pass through to base regions
- No z-index conflicts or CSS hacks needed

### Configuring Layers

**Currently implemented methods**:

```python
from shinymap.outline import Outline

# set_overlays() - mark regions as overlay (implemented)
outline = Outline.from_json("map.json").set_overlays(["_border", "_dividers"])

# merge_layers() - set multiple layer types at once (implemented)
outline = outline.merge_layers({
    "underlays": ["_grid"],
    "overlays": ["_border"],
})

# Via layers parameter on input_map/output_map (implemented)
input_map("id", outline, layers={
    "underlays": ["_grid"],
    "overlays": ["_border"],
    "hidden": ["_guides"],
})
```

**TODO**: Implement `move_layer()` for a more fluent API:

```python
# Planned API (not yet implemented)
outline = (
    Outline.from_json("map.json")
    .move_layer("underlay", "_grid", "_background")
    .move_layer("overlay", "_border", "_dividers")
    .move_layer("hidden", "_construction_guides")
)
```

**Implementation details**:
- Layer assignment logic in [layers.ts](packages/shinymap/js/src/utils/layers.ts)
- `assignLayers()` assigns each region to exactly one layer (priority: hidden > overlay > underlay > base)
- InputMap and OutputMap both implement this layered rendering
- Hover state tracked via React `useState` with mouse/focus event handlers
- Python aesthetic dicts are recursively converted from snake_case to camelCase
- Overlays render duplicate `<path>` elements with the same geometry but different aesthetics

See [SPEC.md](SPEC.md) for detailed technical documentation.

## Static Analysis with StillLife

The `StillLife` class provides static analysis of resolved aesthetics. Create a builder via `WashResult.build()`, then inspect with StillLife:

```python
from shinymap import Wash, StillLife, aes, Outline

wc = Wash(shape=aes.ByState(
    base=aes.Shape(fill_color="#e2e8f0"),
    select=aes.Shape(fill_color="#3b82f6"),
))

outline = Outline.from_dict({"a": "M 0 0 L 10 0 L 10 10 L 0 10 Z", "b": "M 20 0 L 30 0 L 30 10 L 20 10 Z"})
builder = wc.build(outline, value={"a": 1, "b": 0})

pic = StillLife(builder)
pic.aes("a")["fill_color"]  # '#3b82f6' (selected)
pic.aes("b")["fill_color"]  # '#e2e8f0' (not selected)
pic.aes_table()  # Get all regions' aesthetics

# Static SVG export
pic.to_svg()                    # Returns SVG string
pic.to_svg(output="map.svg")    # Writes to file

# With hover state
pic_hovered = StillLife(builder, hovered="a")
pic_hovered.to_svg()            # Includes hover aesthetics
```

Layer rendering order: underlay → base → overlay → selection → hover.

## Deferred/Future Items

These are mentioned in SPEC but not yet implemented:

- Hover event emission to server (currently hover is purely visual)
- Keyboard navigation and full ARIA support for accessibility
- Delta-based updates for large maps (send only changed regions)
- Canvas fallback for very large maps (1000+ regions)
- Geographic extension (`shinymap-geo`) with GeoJSON/TopoJSON support

See [design/README.md](design/README.md) for topics needing detailed design documents.

## Testing Philosophy

- Frontend: unit/snapshot tests for React components
- Python: integration tests ensuring adapters produce correct payloads
- R: (planned) similar integration tests
- Enforce lint/format via CI (TypeScript + ESLint, Python linting)

## Quick Reference Links

- Python examples: [`packages/shinymap/python/examples/`](packages/shinymap/python/examples/)
- React components: [`packages/shinymap/js/src/components/`](packages/shinymap/js/src/components/)
- Python source: [`packages/shinymap/python/src/shinymap/`](packages/shinymap/python/src/shinymap/)
- Design documents: [`design/`](design/)
- Contributing guidelines: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Python Shiny practices: [`SHINY-FOR-PYTHON.md`](SHINY-FOR-PYTHON.md)

## Pre-1.0.0 Breaking Changes: End-of-Life ImportError Pattern

When renaming or moving public modules in pre-1.0.0, use helpful ImportError messages instead of silent breakage. This provides clear migration guidance when users try to import from obsolete locations.

### Implementation Pattern

Create a stub module at the old location that raises `ImportError` with migration instructions:

```python
# shinymap/old_module/__init__.py (stub for moved module)
"""This module has moved. See error message for migration instructions."""

def __getattr__(name: str):
    raise ImportError(
        f"'shinymap.old_module' has been renamed to 'shinymap.new_module'. "
        f"Please update your import:\n"
        f"  from shinymap.new_module import {name}"
    )
```

For modules where specific names moved to a different location:

```python
# In __init__.py of module that lost exports
_MOVED_NAMES = {"OldClass", "old_function"}

def __getattr__(name: str):
    if name in _MOVED_NAMES:
        raise ImportError(
            f"'{name}' has moved to shinymap.new_location. "
            f"Please update your import:\n"
            f"  from shinymap.new_location import {name}"
        )
    raise AttributeError(f"module 'shinymap.xxx' has no attribute '{name}'")
```

### Active End-of-Life Stubs

| Old Import | New Import | Status |
|------------|------------|--------|
| `shinymap.geometry` | `shinymap.outline` | Active (raises ImportError) |

## Obsolete Patterns (Migration Guide)

This section helps identify and update deprecated code patterns. If you encounter these patterns in the codebase, they should be updated to the current API.

### Removed: `geometry` Parameter (Now `outline`)

**Obsolete pattern** (if you see this, update it):
```python
# Python
Map(geometry=outline)
input_map("id", geometry, mode="single")

# TypeScript
<InputMap geometry={regions} />
```

**Current API**:
```python
# Python - first positional arg is `outline`
Map(outline)
input_map("id", outline, mode="single")

# TypeScript - prop is `regions` (the data structure, not Outline object)
<InputMap regions={regions} />
```

The Python `Outline` class wraps the regions dict and provides metadata. TypeScript receives the raw `regions` dict in the payload.

### Removed: `active_ids` and `.with_active()`

**Obsolete pattern** (if you see this, update it):
```python
Map(outline, value=counts, active=["a", "b"])
Map(outline).with_active(["a", "b"])
```

**Current API**:
```python
# Selection is now derived from value > 0
Map(outline, value={"a": 1, "b": 1, "c": 0})  # a, b selected; c not selected
```

The unified value model means:
- `value = 0` or missing → not selected
- `value > 0` → selected

There is no separate `active_ids` parameter or `.with_active()` method.

### Removed: `RegionState(is_selected=True)`

**Obsolete pattern** (if you see this, update it):
```python
state = RegionState("region_1", is_selected=True)
```

**Current API**:
```python
state = RegionState("region_1", value=1)  # value > 0 means selected
state.is_selected  # Property derived from value > 0
```

### Removed: `activeIds` in TypeScript

**Obsolete pattern** (if you see this, update it):
```typescript
<OutputMap activeIds={["a", "b"]} />
```

**Current API**:
```typescript
<OutputMap value={{ a: 1, b: 1, c: 0 }} />
// Selection derived: deriveActiveFromValue(value) → Set of IDs where value > 0
```

### Payload Key Changes

| Old Key | New Key | Notes |
|---------|---------|-------|
| `geometry` | `regions` | In JSON payload sent to JS |
| `active_ids` | (removed) | Selection derived from `value` |
