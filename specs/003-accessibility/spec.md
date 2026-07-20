# Spec: Keyboard Navigation and ARIA Support

**Status**: Approved (user, 2026-07-20)
**Branch**: `feature/003-accessibility`
**Origin**: dev/SPEC.md §Accessibility ("input components, not just pictures —
proper accessibility would be a genuine differentiator")

## Why

shinymap positions its components as **form controls** (visual radio buttons,
checkboxes, counters). Standard HTML form controls are keyboard-operable and
expose name/role/value to assistive technology; shinymap currently does
neither (root SVG has `role="img"` only; regions have no `tabIndex`, no
`role`, no `aria-*`, no `onKeyDown`). This gap:

- contradicts the input-first philosophy (a control you cannot reach by
  keyboard is not a control),
- fails WCAG 2.1 Level A (2.1.1 Keyboard, 4.1.2 Name/Role/Value) for any
  app that uses shinymap as its only input for a question,
- weakens the JOSS/academic positioning where accessibility is a
  differentiator vs. existing clickable-SVG libraries.

## User Stories

1. **Keyboard user**: I Tab to the map (one tab stop), move between regions
   with arrow keys, and select with Enter/Space — producing exactly the same
   input value as a mouse click.
2. **Screen reader user**: When I focus a region I hear its name and state
   ("Tokyo, radio button, selected" / "Osaka, checkbox, not checked" /
   "Kyoto, 3 of 5"), and the group announces its label.
3. **Low-vision user**: I can always see which region has keyboard focus,
   distinctly from mouse hover and from selection.
4. **App author**: I get all of this by default from `input_map()` without
   new required parameters; region names come from the `tooltips` I already
   provide (falling back to region IDs).

## Requirements

### R1. Keyboard interaction model (all input modes + Display(clickable))

- The map is **one tab stop** (roving tabindex among regions). Tab/Shift+Tab
  enter and leave the component; they do not walk through regions.
- Arrow keys move focus between regions in DOM order (Left/Up = previous,
  Right/Down = next, wrapping). `Home`/`End` jump to first/last region.
- `Enter` or `Space` activates the focused region — identical semantics to
  click for the current mode (toggle / select / increment / cycle).
- Count mode additionally supports `+` (increment, same as Enter/Space)
  and `-` (decrement) keys; cycle mode: `+`/`-` cycle forward/backward.
- Keyboard activation triggers the same `onChange` → Shiny input update
  path as click (no separate code path).

### R2. Roles and states per mode

| Mode | Container role | Region role | Region state |
|------|----------------|-------------|--------------|
| single | `radiogroup` | `radio` | `aria-checked` |
| multiple | `group` | `checkbox` | `aria-checked` |
| count / cycle | `group` | `button` | value in accessible name, e.g. "Tokyo, 3" (exact pattern in plan) |
| Display(clickable=True) | `group` | `button` | — |
| Display (non-clickable) | `img` (unchanged) | none | — |

- Every interactive region has an accessible name: `tooltips[region_id]`
  if provided, else the region ID.
- The container's accessible name comes from the existing Shiny input label
  (or an explicit parameter if none exists — plan decides).

### R3. Visible focus indicator

- A focused region shows a visible indicator **by default** (no user
  configuration required), visually distinct from hover and selection.
- Rendered via the existing overlay architecture (a focus overlay above
  hover, `pointer-events: none`), so it is never hidden by neighboring
  regions' fills.
- Mouse hover must no longer be conflated with keyboard focus (today
  `onFocus`/`onBlur` reuse the hover state — InputMap.tsx:336-337).

### R4. No regressions

- Mouse behavior, payload format, and the Python API remain unchanged;
  existing apps get accessibility without code changes.
- Overlay/annotation layers keep `pointer-events: none` and are excluded
  from the focus order (as are `hidden`/`underlay` regions).

## Acceptance Criteria

Verified via Playwright integration tests (packages/shinymap/python/tests/)
plus JS unit/snapshot tests:

- [ ] AC1: Tab focuses the map as a single tab stop; Shift+Tab leaves it;
  regions never appear as extra document tab stops
- [ ] AC2: Arrow keys / Home / End move focus among interactive regions
  only (overlay/underlay/hidden/annotation excluded), with wrap-around
- [ ] AC3: Enter/Space on a focused region updates the Shiny input value
  identically to clicking that region, in all four input modes
- [ ] AC4: Count mode can increment and decrement via keyboard
- [ ] AC5: Roles/aria-checked/accessible names match the R2 table
  (asserted via DOM attributes for each mode)
- [ ] AC6: Focused region shows the default focus indicator; hovering a
  different region shows hover styling simultaneously (states independent)
- [ ] AC7: Non-clickable OutputMap keeps `role="img"` and gains no tab stops
- [ ] AC8: Existing mouse interaction tests still pass unchanged
- [ ] AC9: Quality gates pass (constitution: make lint/format/build for TS,
  lint-python/format-python, test)

## Out of Scope (documented limitations)

- **Spatial arrow navigation** (moving focus geographically up/down/left/
  right) — v1 uses DOM order; spatial order is a possible future enhancement
- **aria-live announcements** beyond state attributes (e.g. selection-count
  summaries)
- **Focus virtualization** for very large maps; guidance stays "keyboard
  navigation is designed for maps up to a few hundred regions" (SPEC.md)
- **User-configurable focus aesthetics** (`aes` focus state) — default
  indicator only in v1; extending `aes.ByState` is a separate feature
- R Shiny bindings (will inherit the React behavior when built)

## Resolved Questions (user decisions, 2026-07-20)

1. Count decrement key: **`+` / `-` keys** (see R1).
2. Container accessible name: **deferred** — plan includes an investigation
   task on the existing `input_map` label wiring; a new `aria_label`
   parameter is out of scope for v1 unless the investigation shows the
   label wiring is insufficient.
3. `Single(allow_deselect=True)` with nothing selected: **approved** —
   `aria-checked="false"` on all radios (valid ARIA).
