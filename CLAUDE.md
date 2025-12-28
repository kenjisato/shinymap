# Guide for AI Assistants

This document provides context for AI assistants (like Claude) working on the shinymap project.

## Project Overview

**shinymap** provides **visual alternatives to standard HTML form inputs** using SVG regions:
- `input_map(mode="single")` → Visual radio buttons (select one region)
- `input_map(mode="multiple")` → Visual checkboxes (select multiple regions)
- `input_map(mode="count")` → Visual counter/range input (click to increment with visual feedback)

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

2. **Unified count model**: Internally uses `{region_id: count}` representation. Python API transforms this to ergonomic types:
   - `mode="single"` → `str | None`
   - `mode="multiple"` → `list[str]`
   - `mode="count"` → `dict[str, int]`

3. **Geometry-agnostic**: Same API works for any SVG paths, not geography-specific.

4. **Pre-1.0.0**: Breaking changes are acceptable while optimizing for clarity and performance. Don't add backward-compatibility shims yet.

5. **Avoid over-engineering**: Only make changes directly requested or clearly necessary. Keep solutions simple and focused.

## Development Environment

- **Python**: Minimum 3.12, use `uv` for dependency management, `hatch` for builds
- **JavaScript/TypeScript**: React components in `packages/shinymap/js`
- **License**: MIT (keep all dependencies MIT-compatible)

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

## Performance Philosophy

**Input components**: Already highly efficient. Click interactions update only changed regions via React reconciliation.

**Output components**: Follow standard Shiny patterns - `@render_map` re-executes and sends complete payload, React reconciliation updates DOM. This is a **general Shiny pattern** (like matplotlib regeneration), not a shinymap-specific problem.

**When performance matters** (>500 regions, expensive computations, high interaction frequency):
- Use action buttons, debouncing, caching (standard Shiny patterns)
- Consider `update_map()` for partial updates (see [design/update_map_implementation.md](design/update_map_implementation.md))
- Defer optimizations until real-world use cases demonstrate need

## Common Patterns

### Python Color Scaling

```python
from shinymap import scale_sequential, scale_diverging, scale_qualitative

# Sequential (count data)
fills = scale_sequential(counts, region_ids, palette=SEQUENTIAL_BLUE, max_count=10)

# Diverging (positive/negative)
fills = scale_diverging(values, region_ids, low_color="#ef4444", mid_color="#f3f4f6", high_color="#3b82f6")

# Qualitative (categories)
fills = scale_qualitative(categories, region_ids, palette=QUALITATIVE)
```

### MapBuilder Fluent API

```python
from shinymap import Map, render_map

@render_map
def my_map():
    return (
        Map(geometry, tooltips=tooltips)
        .with_fill_color(fills)
        .with_counts(counts)
        .with_active(active_ids)
    )
```

### Aesthetic Parameters

Configure aesthetics using `aes_*` parameters:

```python
from shinymap import aes

# Input map with custom hover and selection aesthetics
input_map(
    "region",
    geometry,
    aes_hover=aes.Shape(stroke_color="#374151", stroke_width=2),
    aes_select=aes.Shape(fill_color="#fbbf24"),
)

# Using dict syntax (alternative)
input_map(
    "region",
    geometry,
    aes_hover={
        "stroke_color": "#1e40af",
        "stroke_width": 2,
        "fill_color": "#3b82f6",
        "fill_opacity": 0.2
    }
)
```

Note: Aesthetic dicts use snake_case keys in Python (`stroke_color`, `stroke_width`, `fill_color`, `fill_opacity`) which are automatically converted to camelCase for JavaScript.

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

1. Check [SPEC.md](SPEC.md) for current implementation status and philosophy
2. Check [design/](design/) for detailed implementation plans if feature is mentioned in SPEC
3. Check [CONTRIBUTING.md](CONTRIBUTING.md) for practical workflows and command sequences (especially useful for understanding working directories)
4. Check [SHINY-FOR-PYTHON.md](SHINY-FOR-PYTHON.md) for Python-specific patterns and best practices
5. For new features, assess whether detailed design document is needed before implementation
6. Prefer editing existing files over creating new ones
7. Use TodoWrite tool for multi-step tasks to track progress
8. After implementing changes, update relevant documentation (SPEC, PROPOSAL, README as appropriate)

## SVG Rendering and Overlay Architecture

**Challenge**: SVG elements render in DOM order (painter's algorithm), where later elements appear on top. This creates border visibility issues:
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

**Implementation details**:
- InputMap and OutputMap both implement this layered rendering
- Hover state tracked via React `useState` with mouse/focus event handlers
- Python aesthetic dicts (`hover_highlight`, `default_aesthetic`) are recursively converted from snake_case to camelCase
- Overlays render duplicate `<path>` elements with the same geometry but different aesthetics

See [SPEC.md](SPEC.md) for detailed technical documentation.

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
