# `update_map()` Implementation Reference

This document contains detailed implementation guidance for the `update_map()` function following Shiny's `update_*()` pattern.

## Cost Assessment

**Updating tooltips is NOT expensive**:
- SVG `<title>` elements are lightweight text nodes
- React's reconciliation updates only changed elements
- No layout recalculation or reflow triggered (unlike geometry changes)
- Typical payload size for tooltip-only update: ~1-5KB for 50 regions

**What IS expensive**:
- Recomputing fills with complex color scaling on every hover
- Re-executing expensive server-side computations in `@render_map`
- JSON serialization/deserialization overhead (though minimal for small updates)

## Current Implementation

Tooltips are currently implemented as simple SVG `<title>` elements in [OutputMap.tsx:88](../packages/shinymap/js/src/components/OutputMap.tsx#L88):

```tsx
{tooltip ? <title>{tooltip}</title> : null}
```

When the map payload changes, React's reconciliation efficiently updates only the changed `<title>` elements.

## Proposed Python API

Add to `packages/shinymap/python/src/shinymap/_ui.py`:

```python
def update_map(
    id: str,
    *,
    tooltips: TooltipMap = None,
    fills: FillMap = None,
    counts: CountMap = None,
    active_ids: Selection = None,
    session=None,
):
    """Update specific properties of an output map without full re-render.

    Follows Shiny's update_*() pattern (like ui.update_slider, ui.update_select).
    Sends targeted messages to JavaScript bindings that update specific properties
    without re-rendering the entire component.

    Args:
        id: The output map ID to update
        tooltips: New tooltip mapping (updates only specified regions)
        fills: New fill color mapping
        counts: New count badge mapping
        active_ids: New active/highlighted regions
        session: Shiny session (auto-detected if None)

    Example:
        # Update only active highlighting without re-computing expensive fills
        @reactive.effect
        @reactive.event(input.selected)
        def _():
            ui.update_map("my_map", active_ids=input.selected())

        # Update tooltips on hover (if hover events added later)
        @reactive.effect
        @reactive.event(input.hovered_region)
        def _():
            region = input.hovered_region()
            if region:
                detailed_info = fetch_details(region)
                ui.update_map("my_map", tooltips={region: detailed_info})

    Notes:
        - This complements rather than replaces @render_map
        - Tooltip updates are very cheap (lightweight SVG <title> elements)
        - React reconciliation handles DOM updates efficiently
        - Use for performance-critical scenarios where full re-render is expensive
    """
    from shiny import session as shiny_session
    if session is None:
        session = shiny_session.get_current_session()

    update_payload = _camel_props(_drop_nones({
        "tooltips": tooltips,
        "fills": fills,
        "counts": counts,
        "active_ids": active_ids,
    }))

    session.send_custom_message(
        "shinymap-update",
        {"id": id, "updates": update_payload}
    )
```

## JavaScript Message Handler

Add to `packages/shinymap/python/src/shinymap/www/shinymap-shiny.js` (after bootstrap function):

```javascript
// Register custom message handler for update_map()
if (window.Shiny) {
  Shiny.addCustomMessageHandler("shinymap-update", function(message) {
    const { id, updates } = message;

    // Find the output container
    const container = document.getElementById(id);
    if (!container) {
      console.warn("[shinymap] update_map: container not found for id:", id);
      return;
    }

    // Find the map element within the container
    const mapElement = container.querySelector("[data-shinymap-output]");
    if (!mapElement) {
      console.warn("[shinymap] update_map: map element not found in container:", id);
      return;
    }

    // Parse current payload
    const currentPayload = parseJson(mapElement, "shinymapPayload");
    if (!currentPayload) {
      console.warn("[shinymap] update_map: no existing payload for id:", id);
      return;
    }

    // Merge updates with existing payload
    const mergedPayload = { ...currentPayload, ...updates };

    // Update data attribute with merged payload
    mapElement.dataset.shinymapPayload = JSON.stringify(mergedPayload);

    // Trigger re-render with updated payload
    renderOutputMap(mapElement);

    log("[shinymap] update_map: updated", id, "with", updates);
  });
}
```

## Implementation Complexity vs. Benefit

**Complexity**: Low-Medium
- ~50 lines Python helper function (including docstring)
- ~30 lines JavaScript message handler
- Follows established Shiny patterns (similar to `ui.update_slider`)
- No changes to React components needed (they already handle prop updates efficiently)
- Standard Shiny custom message mechanism

**Benefits**: High
1. **Standard Shiny patterns**: Familiar API for Shiny developers
2. **Efficiency**: Avoid re-executing expensive `@render_map` computations
3. **Responsive interactions**: Update tooltips/highlights without server computation delays
4. **Selective updates**: Change fills/tooltips/counts independently
5. **Composability**: Combine with `@render_map` for complex scenarios

## Use Cases

### Scenario 1: Highlighting active region without re-computing expensive fills

**Without `update_map`** (full re-render):
```python
@render_map
def my_map():
    # Expensive computation runs every time selection changes
    fills = expensive_color_computation(data)
    return Map(geometry).with_fills(fills).with_active(input.selected())
```

**With `update_map`** (cheap highlight change):
```python
@render_map
def my_map():
    # Expensive computation runs only when data changes
    fills = expensive_color_computation(data)
    return Map(geometry).with_fills(fills)

@reactive.effect
@reactive.event(input.selected)
def _():
    # Cheap update: only changes active highlighting
    ui.update_map("my_map", active_ids=input.selected())
```

### Scenario 2: Dynamic tooltips on hover (future feature)

**Requires hover event emission** (not yet implemented):
```python
@render_map
def my_map():
    # Basic tooltips for all regions
    tooltips = {r: get_basic_info(r) for r in regions}
    return Map(geometry, tooltips=tooltips, fills=fills)

@reactive.effect
@reactive.event(input.hovered_region)
def _():
    # Update only the hovered region's tooltip with detailed info
    region = input.hovered_region()
    if region:
        ui.update_map("my_map", tooltips={region: get_detailed_info(region)})
```

### Scenario 3: Incremental fill updates

```python
@render_map
def my_map():
    # Initial render with base fills
    return Map(geometry).with_fills(base_fills)

@reactive.effect
@reactive.event(input.filter_category)
def _():
    # Fast category-based fill update without full re-render
    category = input.filter_category()
    filtered_fills = {r: get_category_color(r, category) for r in regions}
    ui.update_map("my_map", fills=filtered_fills)
```

## Testing Checklist

When implementing `update_map()`:

- [ ] Verify Python function signature matches Shiny conventions
- [ ] Test session auto-detection (None parameter)
- [ ] Test custom message serialization (`_camel_props` conversion)
- [ ] Test JavaScript message handler registration
- [ ] Test payload merging (partial updates don't lose other properties)
- [ ] Test React reconciliation (only changed regions update)
- [ ] Test with missing/invalid IDs (error handling)
- [ ] Test combinations of update parameters (tooltips + fills, etc.)
- [ ] Test interaction with `@render_map` (updates don't conflict)
- [ ] Document in Python docstrings and user guide

## Performance Notes

**When to use `update_map()`**:
- Active region highlighting (selection changes frequently)
- Tooltip updates (if hover events added later)
- Filter-based fill changes (fast computation)
- Any scenario where `@render_map` re-execution is expensive

**When to use `@render_map`**:
- Initial map setup
- Complete data changes
- Complex coordinated updates (geometry + fills + tooltips)
- When computation is already fast (<100ms)

**Best practice**: Start with `@render_map` (simpler). Add `update_map()` only when profiling reveals performance bottlenecks.

## References

- [ui.update_slider – Shiny for Python](https://shiny.posit.co/py/api/core/ui.update_slider.html)
- [ui.update_select – Shiny for Python](https://shiny.posit.co/py/api/core/ui.update_select.html)
- Shiny custom messages: `session.send_custom_message()` and `Shiny.addCustomMessageHandler()`
