# Plan: shinymap.kit — Phase 7 (Review App)

Technical plan for the remaining work. As-built architecture of Phases 1–6
is documented in [dev/design/kit-module.md](../../dev/design/kit-module.md) (archive);
this plan reflects the code as it exists on `dev` + `task/phase6-treat-as-line`.

## As-Built Module Layout (Phases 1–6)

```
packages/shinymap/python/src/shinymap/kit/
├── __init__.py          # Exports: apply_mapping, describe, glaze, generate_code
├── _caption.py          # describe(), glaze()
├── _code_gen.py         # apply_mapping(), generate_code()
├── caption/__main__.py  # CLI: python -m shinymap.kit.caption
└── sketch/
    ├── __main__.py      # CLI (argparse: -f/--file, -H/--host, -p/--port, -b)
    ├── app.py           # App assembly + Globals (reactive state holder)
    ├── _tab_original.py # Original outline view (layer color-coding pattern)
    ├── _tab_relabel.py  # Relabel/merge/layer/lines UI
    ├── _tab_infer.py    # Code generation from original file
    └── _tab_finish.py   # Final JSON preview/export
```

Note: the old design doc's `kit/_app_review.py` naming is superseded —
follow the sketch convention: app code lives in `kit/review/app.py`.

## New Files (Phase 7)

```
packages/shinymap/python/src/shinymap/kit/review/
├── __init__.py          # empty or app re-export
├── __main__.py          # CLI, mirror sketch/__main__.py argparse options
└── app.py               # UI + server (single file; split only if >~500 lines)
packages/shinymap/python/tests/test_review_app.py
```

## Key APIs to Use (verified locations)

| Need | API | Where |
|------|-----|-------|
| Layer membership | `Outline.layers_dict()` → keys overlay/underlay/annotation/hidden | outline/_outline.py:494 |
| Layer queries | `overlay_ids()` :411, `underlay_ids()` :431, `hidden_ids()` :451 | outline/_outline.py |
| Element types | `Outline.region_types()` → region_id → "shape"/"line"/"text" | outline/_outline.py:725 |
| Bounds | `elem.bounds()` per element; combine like kit/_caption.py:78-95 | svg/_elements.py |
| Aesthetic resolution | `Wash(...).build(outline, value=...)` → `StillLife(builder)` | _stilllife.py:55 |
| Resolved aes lookup | `StillLife.aes(region)`, `StillLife.aes_table(region_ids)` | _stilllife.py |
| Static SVG export | `StillLife.to_svg(output=None) -> str` (renders underlay→base→overlay→selection→hover) | _stilllife.py:301 |
| Map rendering | `output_map()` + `@render_map` + `Map(outline, aes=aes.ByGroup(...))` | shinymap._ui |
| Region click | `input_map(id, outline, mode="single", ...)` for the inspect view | shinymap._ui |

## Design Decisions

1. **Separate app, not a sketch tab** (per design doc decision) — review is
   read-only; separation prevents accidental edits and keeps sketch focused.
2. **Layer color scheme**: reuse the sketch palette from
   `kit/sketch/_tab_original.py:67-118`:
   main=blue (#bfdbfe/#1e40af), overlay=orange (#fed7aa/#ea580c),
   underlay=yellow (#fef08a/#ca8a04), hidden=gray dashed (#e5e7eb/#6b7280),
   annotation=green (#bbf7d0/#16a34a). Extract into a module-level constant
   in `kit/review/app.py` (do NOT refactor sketch to share it — minimal diffs;
   note the duplication in tasks.md Parking Lot).
3. **Layer visualization technique**: build a temporary outline for display
   with `update_metadata({"groups": {...by layer...}, "hidden": []})` so
   hidden regions become visible (same trick as `_tab_relabel.py:502-511`),
   then style with `aes.ByGroup`.
4. **Inspect interaction**: `input_map(mode="single")` — a single selected
   region drives a details panel (`@render.text`/`@render.ui`).
5. **Aesthetics panel**: a default sample `Wash` with visible base/select
   states; the currently inspected region is passed as
   `value={region_id: 1}` to preview select aesthetics. Show
   `StillLife.aes_table()` output as a table for all regions.
6. **Read-only guarantee**: the app holds the loaded `Outline` in a
   reactive value and never writes files except the SVG download
   (tempfile + `render.download`, same pattern as sketch `_tab_finish.py`).

## Data Flow

```
CLI -f FILE or ui.input_file
  → load (reuse loading approach from kit/sketch/app.py; accepts .svg/.json)
  → reactive outline
      ├─ Tab "Layers":  display outline w/ layer groups → output_map/render_map
      ├─ Tab "Inspect": input_map(mode="single") → details panel
      │                   (region_types, layers_dict, bounds, groups)
      ├─ Tab "Aesthetics": Wash + StillLife → aes_table + preview map
      └─ Download: StillLife.to_svg() → render.download
```

## Test Strategy

- Unit: pure helpers (layer→groups mapping, bounds formatting) in
  `test_review_app.py`
- Import smoke test: app module imports cleanly (pattern:
  `tests/test_examples.py`)
- Existing StillLife tests already cover to_svg(); do not duplicate
- Integration (Playwright) tests: optional, only if trivial with existing
  fixtures in `tests/test_integration.py`

## Risks

- `update_metadata` merge semantics for clearing layers: follow the exact
  pattern in `_tab_relabel.py` (set explicit empty lists) — do not guess.
- `Wash`/`StillLife` construction requires `WashResult.build()` output;
  check `_stilllife.py` docstring example before wiring.
