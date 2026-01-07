## Diversion: input-map-module-ns

### Issue
GitHub Issue #8: input_map doesn't support Shiny module namespacing

### Problem
When `input_map` is used inside a Shiny module (`@module.ui`), the ID is not namespaced:
- HTML element gets `id="selector"`
- Shiny expects `id="module_id-selector"`
- Result: `input.selector()` returns None

### Root Cause
In `_input_map.py`, the ID is used directly without resolving through Shiny's namespace:
```python
container = div(
    id=id,  # Should be resolve_id(id)
    ...
    data_shinymap_input_id=id,  # Should also be resolve_id(id)
)
```

### Fix
Use `shiny._namespaces.resolve_id(id)` to properly namespace the ID.

### Files to Modify
- `packages/shinymap/python/src/shinymap/uicore/_input_map.py`
- Possibly `_update_map.py` as well (uses similar pattern)

### Return To
After merging this diversion to dev:
1. `git switch feature/kit-module && git rebase dev`
2. `git switch task/kit-module-phase2 && git rebase feature/kit-module`
3. See COMMUNICATION.task.kit-module-phase2.md for next steps
