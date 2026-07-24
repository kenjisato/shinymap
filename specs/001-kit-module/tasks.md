# Tasks: shinymap.kit

**Branching**: kit-module work merges to `dev` via standalone task branches
(historical convention for this feature; no feature branch). Reference this
spec in PR descriptions.

## Completed (migrated from COMMUNICATION.feature.kit-module.md)

- [X] Phase 1: Outline methods `move_layer()` / `move_group()` (commit e8adbed)
- [X] Phase 2: kit module structure (commit 6b141c0)
- [X] Phase 3: Clean up old locations, EOL stubs (commit 3e57957)
- [X] Phase 4: Caption tool (commit a4a8f62)
- [X] Phase 5: Sketch layer enhancement (PR #17, #18 — merged 2026-01-25)
- [X] Phase 6: Treat as Line — implemented on branch `task/phase6-treat-as-line`
  (commit 93bd0c3), **not yet merged** (see T601)

## Phase 6 Wrap-Up

- [ ] T601 Land `task/phase6-treat-as-line` into dev
  - Prerequisite: specs/002-ci-mypy-fix merged to dev (avoids format conflicts
    in `_tab_relabel.py` / `app.py` / `_tab_original.py`)
  - Steps:
    1. `git switch task/phase6-treat-as-line && git rebase dev`
       (expect conflicts in the 3 reformatted sketch files; resolve keeping
       Phase 6 logic with dev formatting, then run `make format-python`)
    2. Remove committed handoff files (obsolete convention):
       `git rm COMMUNICATION.task.phase6-treat-as-line.md COMMUNICATION.feature.kit-module.md`
    3. Manual UI test: `uv run python -m shinymap.kit.sketch -f <sample.svg>`
       - Lines sub-tab appears; stroke-only paths are pre-flagged
         (`is_stroke_only_candidate`, svg/_elements.py)
       - Mark/unmark toggles update the region list indicator
       - Finish tab JSON contains `lines_as_path`; Infer tab code contains
         `.path_as_line(...)`
       - Renaming a line-marked region preserves the mark
    4. Quality gates: `make lint-python && make format-python && make test`
    5. User review → push → PR to dev

## Phase 7: Review App (see plan.md for all technical decisions)

- [ ] T701 Create `kit/review/` skeleton
  - `kit/review/__init__.py` (empty)
  - `kit/review/__main__.py`: copy argparse structure from
    `kit/sketch/__main__.py` (-f/--file, -H/--host, -p/--port, -b), adjust
    docstring/prog name, call `app_run()` from `kit/review/app.py`
  - `kit/review/app.py`: minimal `app_ui` (page_fillable, title "shinymap
    Outline Review") + `server` + `app_run(initial_file, **kwargs)` following
    `kit/sketch/app.py` conventions (module-level `_initial_file`)
  - Verify: `uv run python -m shinymap.kit.review --help` works

- [ ] T702 File loading + reactive outline (depends: T701)
  - CLI `-f` preload and `ui.input_file` (accept .svg/.json), reusing the
    loading approach in `kit/sketch/app.py`
  - Store `Outline` in `reactive.value`; show file name and region count
  - Invalid file → error message in UI, no traceback

- [ ] T703 Layer visualization tab (depends: T702)
  - Build display outline: groups = one group per layer via `layers_dict()`
    + main = remainder; clear `hidden` so hidden regions render
    (pattern: `kit/sketch/_tab_relabel.py:502-511`)
  - `output_map` + `@render_map` + `Map(display_outline, aes=aes.ByGroup(...))`
    with the palette constant from plan.md §Design Decisions 2
  - Static legend (ui.tags) mapping color → layer name

- [ ] T704 Inspect tab: click-to-inspect (depends: T702) [P with T703]
  - `input_map("inspect", outline, mode="single")` + details panel showing:
    region ID, element type (`region_types()`), layer (from `layers_dict()`,
    default "main"), bounding box (combine `elem.bounds()` like
    `kit/_caption.py:78-95`), group membership, `lines_as_path` flag
  - No region selected → "Click a region to inspect"

- [ ] T705 Aesthetics preview tab with StillLife (depends: T702) [P with T703, T704]
  - Sample `Wash` (base/select states, visible defaults); build via
    `wash.build(outline, value={selected_id: 1})` where selected_id comes
    from a region selector (reuse Inspect selection if simple)
  - Render `StillLife.aes_table()` as a table (`@render.table` or text)
  - Preview map rendered with the same wash

- [ ] T706 Static SVG export (depends: T705)
  - `ui.download_button` + `@render.download` writing
    `StillLife.to_svg()` to a tempfile (pattern:
    `kit/sketch/app.py` download handlers)

- [ ] T707 Tests (depends: T703-T706)
  - `tests/test_review_app.py`: import smoke test (pattern:
    `tests/test_examples.py`), unit tests for layer→groups helper
  - Run full gates: `make lint-python && make format-python && make test`

- [ ] T708 Documentation (depends: T707)
  - dev/design/kit-module.md: mark Phase 7 checklist done, note as-built naming
    (`kit/review/app.py`)
  - README (python package): add `python -m shinymap.kit.review` to tools list
  - Update spec.md acceptance criteria checkboxes after verification

- [ ] T709 Manual test + user review + PR to dev (depends: T708)
  - `uv run python -m shinymap.kit.review -f <converted.json>` — walk through
    AC1–AC6 in spec.md
  - spec-reviewer subagent on `git diff dev...<branch>`
  - User review → PR

## Parking Lot

- [ ] Layer palette duplicated between sketch `_tab_original.py` and review
  app (intentional, minimal diffs) — consider extracting to `kit/_palette.py`
  when touched next
- [ ] Issue #11: `ungroup()` method feature request (open)
- [ ] Integration (Playwright) coverage for kit apps
