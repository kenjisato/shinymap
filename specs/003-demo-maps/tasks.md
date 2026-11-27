# Tasks: Bundled demo maps and a GeoJSON-to-outline recipe

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/load_demo.md](contracts/load_demo.md), [quickstart.md](quickstart.md)

**Branching**: each task is one branch `task/T0NN-<slug>` from `feature/003-demo-maps` and one PR back into it (squash). Mark `[X]` when its PR merges. Before every PR: `make check-python` and `make test` pass (no JS is touched).

**Tests**: each task ships its own tests (project quality gates), listed in the task.

## Phase 1: Foundational (blocks the data)

- [ ] T001 Amend constitution II in `.specify/memory/constitution.md` (spec FR-011): keep "the API is geometry-agnostic; the core's code has no geographic logic (no projections, no GeoJSON reading, nothing in the API assumes places)"; allow the core to ship demo maps as shape data; delete the sentence sending geographic features to `shinymap-geo`. Bump **Version** to 1.2.0 (MINOR, principle change) and **Last Amended** to the merge date. Constitution-only PR; the maintainer approves it explicitly.
- [ ] T002 Make `Outline.from_svg()` raise `ValueError` naming the duplicated `id` and the file when two elements share an `id` (today `regions[elem_id] = [...]` in `packages/shinymap/python/src/shinymap/outline/_outline.py` silently overwrites; contract in [contracts/load_demo.md](contracts/load_demo.md)). Auto-generated IDs are unaffected. Add tests in `packages/shinymap/python/tests/` for: duplicate explicit ids → error; unique ids → unchanged. Note the change under "Unreleased" in `CHANGELOG.md`.

## Phase 2: User Story 1 — Try shinymap on a familiar map (P1) 🎯 MVP

**Goal**: three demo outlines in the installed package, loaded in one line.
**Independent test**: in a fresh env, `load_demo(name)` for each name renders in `input_map`/`output_map`; counts and IDs per data-model.md.

- [ ] T003 [US1] Maintainer build for the demo data (depends on T001, T002):
  - `packages/shinymap/python/scripts/demo_maps/build.sh`: download Natural Earth 5.1.1 zips into a git-ignored cache (`packages/shinymap/python/scripts/demo_maps/.cache/`, add to `.gitignore`), run `npx --yes mapshaper@0.8.13` with the per-map commands in [research.md](research.md) (World, US states, Japan sections, including `-clean`, the `+lon_0=11` Robinson, `albersusa`, the Japan clip and Okinawa `-affine`), producing one SVG per map plus a GeoJSON/CSV of names.
  - `packages/shinymap/python/scripts/demo_maps/finish.py`: load each SVG with `Outline.from_svg()`; apply the world ID renames (`SAH→ESH`, `PSX→PSE`, `SDS→SSD`, `KOS→XKX`); add metadata keys per data-model.md (`DemoMap.names`, `DemoMap.source`, `DemoMap.source_url`, `DemoMap.license`, `DemoMap.id_scheme`, `DemoMap.generated_by`); add the inset frames per [research.md](research.md) "Inset frames" (rectangles from the relocated areas' bounding boxes plus padding → one `_inset_frames` path region listed in `_metadata["overlay"]` and marked stroke-only with `path_as_line`; fail if a frame box overlaps another region's box); run the data-model.md validation (counts, ID shapes, names) and fail loudly; write `packages/shinymap/python/src/shinymap/outline/demo/{world,us_states,japan}.json` with `Outline.to_json()`.
  - `packages/shinymap/python/src/shinymap/outline/demo/NOTICE.md`: source, version, URLs, public-domain statement, the world code exceptions (`CYN`, `SOL`, `XKX`) and the missing small countries.
  - `Makefile`: `demo-maps` target running the script; add it to `make help`.
  - Commit the generated JSON. Record total size in the PR description (must be ≤ 1 MB, SC-003). Check that the wheel includes the JSON (`uv build` in `packages/shinymap/python`, list the wheel).
  - Test: a test that runs `finish.py`'s validation function on the committed JSON (no network).
- [ ] T004 [US1] `load_demo(name)` in `packages/shinymap/python/src/shinymap/outline/_demo.py`, exported from `packages/shinymap/python/src/shinymap/outline/__init__.py`, per [contracts/load_demo.md](contracts/load_demo.md): `Literal["world", "us_states", "japan"]`, reads with `importlib.resources`, returns a new `Outline` per call, unknown name → `ValueError` listing valid names. Docstring with a runnable doctest (region count for `japan` is 47). Tests in `packages/shinymap/python/tests/test_demo_maps.py`: counts and ID shapes per data-model.md, `names["en"]` complete (and `names["ja"]` for `japan`), `_inset_frames` present in `japan` and `us_states` overlays, each map renders through `input_map` without error, unknown name error. Add `outline.load_demo` to the "Outline Utilities" section of `docs/_quarto.yml`.

## Phase 3: User Story 3 — Clear licensing and scope (P3)

**Independent test**: `git grep -il "BY-SA" -- packages/` is empty; examples run on the bundled map.

- [ ] T005 [US3] Migrate the Japan examples to `load_demo("japan")` (depends on T004):
  - `packages/shinymap/python/examples/app_japan.py` and `app_stilllife.py`: replace `Outline.from_json(... "japan_prefectures.json")` and the `_divider_lines` setup with `load_demo("japan")`; take Japanese and English names from `outline.metadata["names"]` instead of `japan_prefectures.PREF_NAMES_JA` / `PREF_NAMES_ROMAJI` (English names replace romaji in tooltips).
  - Delete `packages/shinymap/python/examples/japan_prefectures.py` and the whole `packages/shinymap/python/examples/data/` directory (CC BY-SA JSON, `LICENSE.txt`, `scripts/`).
  - `packages/shinymap/python/tests/test_examples.py`: drop `test_import_japan_prefectures`; keep `test_import_app_japan` passing; adjust any other test that loaded the removed files.
  - Check `git grep -n "japan_prefectures\|examples/data"` outside `specs/`, `CHANGELOG.md` and `dev/design/` (historical) returns nothing.

## Phase 4: User Story 2 — Make my own region map (P2)

**Independent test**: quickstart.md step 7, following only the new page.

- [ ] T006 [US2] Docs page `docs/vignettes/maps.qmd` (constitution VII, spec FR-008), linked from `docs/vignettes/index.qmd`:
  - Demo maps: 5-line `input_map` example with `load_demo("us_states")` (SC-001); a world choropleth with `Map(...).with_fill_color(...)` joined by ISO code; how to read names from `outline.metadata["names"]`; how to remove `_inset_frames`; sources and licence, the world code exceptions and missing small countries.
  - Your own map: GeoJSON → mapshaper.org (browser, no install): import, project, simplify (`keep shapes`), `clean`, choose the ID field, export SVG with that field as id → `Outline.from_svg()` → `input_map`. Include the equivalent mapshaper command line. Explain the duplicate-id error from T002 and how to fix it in mapshaper (dissolve by the ID field). Say plainly that shinymap does not read GeoJSON or project.
  - Render the docs locally the way CI does and confirm the page and the `load_demo` reference build.

## Phase 5: Polish

- [ ] T007 Update plan documents (spec FR-010): in `dev/PROPOSAL.md` remove the `shinymap-geo` sections and mentions, and add to Non-Goals: GIS features (projection, geopandas/sf integration, tiles, simplification, reading GeoJSON) because mapping libraries cover them and shinymap's value is shapes as inputs; in `dev/SPEC.md` rewrite "Packages and scope" (no geographic extension) and "Geometry & Assets" (demo maps in core via `load_demo`; own maps via the mapshaper recipe; `shinymapjp` for Japan variants). Add a CHANGELOG "Unreleased" entry for the demo maps and the removed example data. Delete `specs/003-demo-maps/spike/` (spike renders) in this PR.

## Dependencies

T001 → T003; T002 → T003 → T004 → T005; T004 → T006; T007 any time after T001 (last PR before the feature PR to `dev`). T006 and T005 can run in parallel after T004 (different files).

## Implementation strategy

MVP = T001–T004 (demo maps usable). T005 removes the share-alike data; T006 makes the feature visible to users; T007 aligns the plan documents. After T007: `spec-reviewer` on `dev...feature/003-demo-maps`, then one PR to `dev`.
