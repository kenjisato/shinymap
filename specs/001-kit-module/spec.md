# Spec: shinymap.kit — SVG Preparation Toolkit

**Status**: Phases 1–6 implemented (see tasks.md); Phase 7 (review app) remaining
**Origin**: Migrated from dev/design/kit-module.md + COMMUNICATION.feature.kit-module.md (2026-07-20)

## Why

Users receive SVG files from designers, Wikipedia, or drawing tools. These
files have auto-generated element IDs (`path_1`, `circle_2`), no layer
semantics, and no distinction between interactive regions and decorations.
Before such a file can be used with `input_map`/`output_map`, it must be
converted into shinymap's outline JSON with meaningful IDs, merged regions,
layer assignments, and line markings. Doing this by hand is error-prone and
requires knowledge of the JSON format.

## What

`shinymap.kit` provides three tools plus composable functions:

| Tool | Command | Purpose |
|------|---------|---------|
| caption | `python -m shinymap.kit.caption input.svg -o labeled.svg` | Reference SVG with region IDs rendered at region centers |
| sketch | `python -m shinymap.kit.sketch [-f FILE]` | Interactive Shiny app: relabel, merge, assign layers, mark lines, export JSON + reproducible Python code |
| review | `python -m shinymap.kit.review [-f FILE]` | Read-only Shiny app: validate a converted outline before use |

Public API: `apply_mapping()`, `generate_code()`, `describe()`, `glaze()`.

## User Stories

1. **Relabeling**: As a Shiny developer, I load an SVG in sketch, click
   regions, type a meaningful ID, and register the rename — including
   merging multiple paths into one logical region (e.g., an archipelago).
2. **Layers**: I assign regions to `main` / `overlay` / `underlay` /
   `hidden` / `annotation` layers through a layer-navigation UI, and the
   exported JSON reflects the assignments.
3. **Lines**: Stroke-only paths (borders, dividers) are auto-detected and I
   can toggle "Treat as Line" so they render with line aesthetics.
4. **Reproducibility**: I download both the final JSON and a Python script
   that regenerates it from the original SVG (fluent `Outline` method calls).
5. **Review** (Phase 7): I open a converted JSON in the review app to check
   layer assignments (color-coded), inspect any region (ID, element type,
   layer, bounds), preview how aesthetics resolve (StillLife), and export a
   static SVG — without any risk of editing the file.

## Acceptance Criteria — Phase 7 (Review App)

- [ ] AC1: `python -m shinymap.kit.review -f file.json` (or `.svg`) launches
  a Shiny app displaying the outline; without `-f`, an upload control is shown
- [ ] AC2: Map view color-codes regions by layer (main/overlay/underlay/
  hidden/annotation) with a visible legend; hidden regions are rendered
  (dashed/faded) so they can be verified
- [ ] AC3: Clicking a region shows: region ID, element type(s)
  (shape/line/text), layer, bounding box, group membership
- [ ] AC4: An aesthetics panel applies a sample Wash and shows resolved
  aesthetics per region (StillLife); user can toggle a region's selected
  state to preview select aesthetics
- [ ] AC5: A download button exports the current view as static SVG via
  `StillLife.to_svg()`
- [ ] AC6: The app never modifies the loaded file (read-only guarantee)
- [ ] AC7: Quality gates pass (constitution): `make lint-python`,
  `make format-python`, `make test`

## Out of Scope

- Editing features in the review app (use sketch)
- Geographic projections / GeoJSON (future `shinymap-geo`)
- Undo/redo in sketch (deferred from Phase 5)
