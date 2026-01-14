# Diversion: Upstream Fixes (Issues #7 and #10)

**Branch**: `div/upstream-fixes-issue-7-10`
**Last commit**: `b1c1595` - fix: add resolve_id() for Shiny module namespacing in output_map (#10)

## Progress

### Issue #10 - COMPLETED
**Bug**: `output_map` doesn't resolve `click_input_id` for Shiny module namespacing

**Fix**:
- `_output_map.py`: Added `resolve_id()` for click_input_id and registry key
- `_render_map.py`: Added `resolve_id()` for registry lookup
- Added `app_module.py` example to test module namespacing

### Issue #7 - NOT STARTED
**Feature**: Add 'annotation' layer that renders above hover/selection layers

**Problem**: Overlay regions (including those added via `glaze()`) render below selection/hover layers. Text labels get covered when regions are selected or hovered.

**Current layer order**:
1. Underlay
2. Base (interactive)
3. Overlay
4. Selection layer
5. Hover layer

**Desired layer order**:
1. Underlay
2. Base (interactive)
3. Overlay
4. Selection layer
5. Hover layer
6. **Annotation layer** (new - always on top)

**Files to modify**:
- `packages/shinymap/js/src/utils/layers.ts` - Add annotation to LayerAssignment
- `packages/shinymap/js/src/components/InputMap.tsx` - Add Layer 6 rendering
- `packages/shinymap/js/src/components/OutputMap.tsx` - Add Layer 6 rendering
- `packages/shinymap/python/src/shinymap/kit/_caption.py` - Add `as_annotation` param to `glaze()`
- `packages/shinymap/python/src/shinymap/outline/_core.py` - Support annotation in metadata

## Next Steps

1. Add "annotation" to `LayerAssignment` type in `layers.ts`
2. Update `assignLayers()` to handle annotation layer
3. Add Layer 6 rendering in both React components
4. Update Python `glaze()` to support `as_annotation=True`
5. Update `Outline.merge_layers()` to handle annotation layer
6. Add tests

## Commands

```bash
# Resume work
git checkout div/upstream-fixes-issue-7-10

# Run tests
make lint && make test
```
