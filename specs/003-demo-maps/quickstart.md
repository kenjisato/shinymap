# Quickstart validation: 003-demo-maps

Run from the repository root after `uv sync --all-packages --all-extras`.

1. **Gates**: `make check-python` and `make test` pass.
2. **Loader** (SC-001, SC-002): for each name in `world`, `us_states`, `japan`, `load_demo(name)` returns an outline with the region counts in [data-model.md](data-model.md); `tests/test_demo_maps.py` checks counts, ID shapes and names.
3. **In an app**: `uv run shiny run packages/shinymap/python/examples/app_japan.py`; clicking a prefecture shows its `"01"`–`"47"` code. Repeat with a 5-line app using `load_demo("us_states")`.
4. **Size** (SC-003): `du -ch packages/shinymap/python/src/shinymap/outline/demo/*.json` totals ≤ 1 MB.
5. **Licence** (SC-005): `git grep -il "BY-SA" -- packages/` finds nothing.
6. **Regeneration** (FR-006): `make demo-maps` with network access reproduces the three JSON files with no diff.
7. **Recipe** (SC-004): follow `docs/vignettes/maps.qmd` with mapshaper's browser version on a GeoJSON of 47 prefectures; the resulting SVG loads with `Outline.from_svg()` and works in `input_map`.
8. **Duplicate IDs**: an SVG with two `id="A"` paths makes `Outline.from_svg()` raise `ValueError` naming `A`.
9. **Docs**: `make docs` (or the quarto render the CI uses) builds; the API reference lists `load_demo`.
