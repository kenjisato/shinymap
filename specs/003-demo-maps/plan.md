# Implementation Plan: Bundled demo maps and a GeoJSON-to-outline recipe

**Branch**: `feature/003-demo-maps` | **Date**: 2026-11-27 | **Spec**: [spec.md](spec.md)

## Summary

Ship three demo outlines (world, US states, Japan prefectures) inside the `shinymap` Python package, loaded with one function. Build them from Natural Earth with a maintainer script that runs mapshaper and `Outline.from_svg()`, the same recipe a new docs page teaches for one's own GeoJSON. Remove the CC BY-SA Japan map, make `from_svg()` refuse duplicate IDs, and update the constitution, PROPOSAL and SPEC to drop `shinymap-geo`.

A spike ran the whole recipe for all three maps (see [research.md](research.md)); `from_svg()` loads mapshaper's SVG unchanged.

## Technical Context

**Language/Version**: Python ≥ 3.12 (package); Node.js (already used for the JS build) for the maintainer script only
**Primary Dependencies**: none new at runtime. Maintainer script: mapshaper 0.8.13 (MPL-2.0), run with `npx --yes mapshaper@0.8.13`, not added to any package manifest — **needs maintainer approval**
**Storage**: three JSON outline files inside the package (`importlib.resources`)
**Testing**: pytest (unit + doctest), existing `make` gates
**Target Platform**: wherever shinymap installs
**Project Type**: library
**Constraints**: demo data ≤ 1 MB total (spike: ~120 KB for all three); no share-alike data
**Scale/Scope**: 176 countries, 51 US regions, 47 prefectures

## Constitution Check

| Principle | Status |
|---|---|
| I Input-first | Unchanged; demo maps are outlines like any other |
| II Geometry-agnostic | **Violated by bundled map data as currently worded** → amended in its own PR (T001) before data lands. Code stays free of geographic logic: no projection, no GeoJSON reading |
| III Value model | Unchanged |
| IV No shims | The CC BY-SA map and its example helpers are removed, not kept alongside |
| V Minimal diffs | One loader function; the `from_svg()` change is limited to the duplicate-ID gap the spike found |
| VI MIT-compatible deps | No runtime dependency. mapshaper (MPL-2.0) is a maintainer-only tool, run via npx, not distributed |
| VII Docs grow with code | New vignette + quartodoc entry for the loader |

Post-design re-check: same as above; no new violations.

## Design decisions

Details and alternatives in [research.md](research.md).

- **Loader**: `shinymap.outline.load_demo(name)` with names `"world"`, `"us_states"`, `"japan"` → `Outline`. Contract: [contracts/load_demo.md](contracts/load_demo.md).
- **Data files**: `packages/shinymap/python/src/shinymap/outline/demo/{world,us_states,japan}.json` (outline JSON as written by `Outline.to_json()`), plus `NOTICE.md` there with source, version and license.
- **Names and provenance** live in each outline's metadata: [data-model.md](data-model.md).
- **Maintainer script**: `packages/shinymap/python/scripts/demo_maps/` — a shell script with the mapshaper commands and a small Python step (load SVG with `from_svg()`, check region count and ID uniqueness, add names/metadata, write JSON). `make demo-maps` runs it. Natural Earth zips are downloaded to a git-ignored cache, pinned to version 5.1.1.
- **Inset frames**: every relocated area (Okinawa in `japan`; Alaska and Hawaii in `us_states`) gets a rectangular frame, built by the script from the area's bounding box in the final SVG coordinates plus padding. All frames of a map form one non-interactive region `_inset_frames` in the overlay layer. The script fails if a frame's box overlaps another region's box. No hand-tuned frame coordinates. Users who do not want frames remove the one region (docs show how).
- **`from_svg()`**: raise `ValueError` naming the ID when two elements share an `id`. Today the later one silently replaces the earlier one, which would lose regions for anyone following the recipe with a bad ID field.
- **Japan example migration**: `examples/app_japan.py`, `examples/app_stilllife.py` and their tests use `load_demo("japan")`; `examples/japan_prefectures.py` and `examples/data/` (the CC BY-SA JSON, its `LICENSE.txt`, `scripts/transform_japan.py`) are deleted.
- **Docs**: new `docs/vignettes/maps.qmd` (demo maps; making your own with mapshaper's browser version; the duplicate-ID error and how to fix it in mapshaper).
- **Plan documents**: constitution II amended (v1.2.0, MINOR); `dev/PROPOSAL.md` and `dev/SPEC.md` drop `shinymap-geo` and state GIS features as a non-goal; SPEC "Geometry & Assets" rewritten to the recipe.

## Project Structure

```text
specs/003-demo-maps/          spec, plan, research, data-model, contracts/, quickstart, tasks
.specify/memory/constitution.md        II amended (own PR)
dev/PROPOSAL.md, dev/SPEC.md           shinymap-geo removed
packages/shinymap/python/
├── src/shinymap/outline/
│   ├── _demo.py                       load_demo()
│   ├── _outline.py                    from_svg(): duplicate-ID error
│   └── demo/{world,us_states,japan}.json, NOTICE.md
├── scripts/demo_maps/                 build.sh + finish.py (maintainer only)
├── examples/                          Japan examples migrated; data/ removed
└── tests/                             test_demo_maps.py, from_svg duplicate test, examples tests
docs/vignettes/maps.qmd, docs/_quarto.yml
Makefile                               demo-maps target
```

## PR sequence (one PR per task into `feature/003-demo-maps`)

1. Constitution II amendment (maintainer approval).
2. `from_svg()` duplicate-ID error + test.
3. Maintainer script + generated demo data + `NOTICE.md` + `make demo-maps`.
4. `load_demo()` + tests + docstring examples.
5. Migrate Japan examples; delete CC BY-SA data.
6. Docs vignette + quartodoc.
7. PROPOSAL/SPEC update.

No JS changes, so the generated-bundle conflicts do not apply.

## Complexity Tracking

None beyond the constitution amendment, which the spec requires (FR-011).
