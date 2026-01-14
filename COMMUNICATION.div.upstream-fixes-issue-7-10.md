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

### Issue #7 - READY FOR REVIEW
**Feature**: Add 'annotation' layer that renders above hover/selection layers

**Problem**: Overlay regions (including those added via `glaze()`) render below selection/hover layers. Text labels get covered when regions are selected or hovered.

**Changes**:
- `layers.ts`: Added `annotation` to `LayerAssignment` type and `assignLayers()` function
- `types.ts`: Added `annotation` to `LayersConfig` type
- `InputMap.tsx`: Added Layer 6 annotation rendering after hover layer
- `OutputMap.tsx`: Added Layer 6 annotation rendering after hover layer
- `_outline.py`: Added `annotation_ids()`, updated `layers_dict()`, `merge_layers()`, and `move_layer()`
- `app_annotation.py`: Demo app comparing annotation vs overlay layer behavior

**Demo app**: `packages/shinymap/python/examples/app_annotation.py`
```bash
cd packages/shinymap/python/examples && uv run shiny run app_annotation.py
```

**Rendering order** (SVG stacking - later = on top):
1. Underlay
2. Base (interactive)
3. Overlay
4. Selection layer
5. Hover layer
6. **Annotation layer** (new - always on top)

## Implementation Plan

### TypeScript Changes (4 files)

1. **`packages/shinymap/js/src/utils/layers.ts`**
   - Add `annotation: Set<RegionId>` to `LayerAssignment` type (line 45-50)
   - Update `assignLayers()` to accept `annotation` parameter
   - Add annotation to the if-else assignment chain (after hidden, before overlay)

2. **`packages/shinymap/js/src/types.ts`**
   - Add `annotation?: string[]` to `LayersConfig` type (lines 680-688)

3. **`packages/shinymap/js/src/components/InputMap.tsx`**
   - Extract `annotation` from layers config
   - Pass `annotation` to `assignLayers()` call
   - Add Layer 6 rendering after hover layer

4. **`packages/shinymap/js/src/components/OutputMap.tsx`**
   - Extract `annotation` from layers config
   - Pass `annotation` to `assignLayers()` call
   - Add Layer 6 rendering after hover layer

### Python Changes (1 file)

5. **`packages/shinymap/python/src/shinymap/outline/_outline.py`**
   - Add `annotation_ids()` method (similar to `overlay_ids()`)
   - Update `layers_dict()` to include "annotation" key
   - Update `move_layer()` to accept "annotation" as valid layer

### Key Details

**Assignment logic in assignLayers()** - each region goes to exactly one layer:
```typescript
if (hiddenRegions.has(id)) {
  result.hidden.add(id);        // hidden wins (don't render)
} else if (annotationRegions.has(id)) {
  result.annotation.add(id);    // NEW: annotation next
} else if (overlayRegions.has(id)) {
  result.overlay.add(id);
} else if (underlayRegions.has(id)) {
  result.underlay.add(id);
} else {
  result.base.add(id);          // default
}
```

**Layer 6 rendering:**
```tsx
{/* Layer 6: Annotation - always on top, even above hover */}
<g>{renderNonInteractiveLayer(layerAssignment.annotation, "annotation")}</g>
```

### Notes
- `glaze()` already implemented in task branch (commit fbced42)
- This diversion adds the annotation layer infrastructure
- Task branch will rebase onto dev after this diversion merges

## Completed Steps

1. [x] Update `LayerAssignment` type and `assignLayers()` in layers.ts
2. [x] Add `annotation` to `LayersConfig` in types.ts
3. [x] Add Layer 6 annotation rendering to InputMap.tsx
4. [x] Add Layer 6 annotation rendering to OutputMap.tsx
5. [x] Update Python Outline class (annotation_ids, layers_dict, move_layer)
6. [x] Run linting, formatting, and tests
7. [x] Create demo app (app_annotation.py)

## Commands

```bash
# Resume work
git checkout div/upstream-fixes-issue-7-10

# Run tests
make lint && make test
```
