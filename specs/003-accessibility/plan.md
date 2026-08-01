# Plan: Keyboard Navigation and ARIA Support

**Status**: Approved (user, 2026-07-20)
**Spec**: [spec.md](spec.md) (approved 2026-07-20)

> **UX tunability (user request)**: keyboard behavior and focus visuals are
> expected to be adjusted after hands-on use. Therefore key bindings and the
> default focus aesthetic MUST live in one shared constants module
> (`js/src/a11y.ts`, D3/D5) so they can be changed in one place. D1
> (selection does not follow focus) and the D5 ring style are explicitly
> revisitable decisions — do not scatter assumptions about them across
> components.

All file/line references verified on `dev` @ 6c03e8c.

## Current State (verified)

| Fact | Location |
|------|----------|
| Root SVG has `role="img"` only, no tabIndex | InputMap.tsx:225-229, OutputMap.tsx:186-191 |
| Regions get onClick / onMouseEnter/Leave / onFocus/Blur; **focus reuses hover state** | InputMap.tsx:334-338 (onFocus/Blur → hover at 336-337), OutputMap.tsx:317-318 |
| No tabIndex/role/aria on paths; no onKeyDown anywhere | renderElement.tsx:87-102 (commonProps) |
| Hover state: `useState<RegionId \| null>` | InputMap.tsx:110 |
| Click logic: `handleClick()` updates `counts: Record<RegionId, number>` | InputMap.tsx:142-168 |
| Mode: `modeConfig.type` ("single"/"multiple"/"count"/"cycle"/"display") | InputMap.tsx:91, types.ts:143, 274-280 |
| Layer order: base → selection → hover → annotation, overlays `pointer-events: none` | InputMap.tsx:416-501 |
| Tooltip = SVG `<title>` per element | renderElement.tsx:106 |
| Existing a11y test asserts `role="img"` only | tests/test_integration.py:144-149 |

## Design Decisions

### D1. Selection does NOT follow focus (deviation from strict APG radio pattern)
Arrow keys move focus only; Enter/Space selects. WAI-APG recommends
selection-follows-focus for radio groups but explicitly allows decoupling
when selection triggers expensive side effects — every selection here is a
server round-trip in Shiny. Document in SPEC.md.

### D2. Roving tabindex, state in React
- New state: `focusedRegion: RegionId | null` (separate from `hovered`) and
  `tabTarget: RegionId` (the region with `tabIndex=0`; all others `-1`).
- Initial `tabTarget`: first selected region if any (radio convention),
  else first interactive region in DOM order.
- Arrow/Home/End updates `tabTarget` and calls `.focus()` on the target DOM
  node via a ref map: `useRef<Map<RegionId, SVGElement>>` populated by a
  ref callback passed through renderElement.
- Interactive region order = the array already used to render the base
  layer group (excludes overlay/underlay/hidden/annotation by construction).

### D3. Keyboard handler
One shared `handleKeyDown(id, event)` attached to each region:
- ArrowRight/Down → next; ArrowLeft/Up → previous (wrap); Home/End → first/last
  — all with `event.preventDefault()` (avoid page scroll)
- Enter/Space → `event.preventDefault()`; call existing `handleClick(id)`
  (single code path, satisfies spec R1)
- `+`/`=` and `-` in count/cycle mode → increment / decrement:
  - count: `max(0, count - 1)` for decrement; increment mirrors click
  - cycle: `(count ± 1 + n) % n`
  - implemented as a new `adjustCount(id, delta)` beside handleClick,
    firing the same onChange
- Other keys: ignore (do not preventDefault)

### D4. ARIA attributes
- Root `<svg>`: for InputMap — `role="radiogroup"` (single) or
  `role="group"` (others); accessible name resolved by T001 — see finding
  below.

**T001 finding (2026-08-01, verified on `dev` @ 7e72938)**: there is no
label wiring to reference. `input_map()` has no `label` parameter at any
layer (`ui/_ui.py` → `Wash.input_map()` at `uicore/_wash.py:369` →
`_input_map()` at `uicore/_input_map.py:28`), and `_input_map` emits only
`div#<resolved_id>.shinymap-input[data-shinymap-props]` — no `<label>`,
heading, or sibling text node. The JS payload carries `regions`,
`tooltips`, `view_box`, `outline_metadata`, `value`, `mode`, `aes`,
`layers`, `raw` — no name field. The container div also has no `**kwargs`
passthrough, so app authors cannot supply `aria-label` themselves today.
**Decision**: root svg gets `role` but **no accessible name in v1**;
regions carry names via `aria-label` (spec R2). Adding an `aria_label`
parameter (or generic attribute passthrough) requires a spec amendment —
recorded in the Parking Lot, user gate.
- Per region (via new optional fields in renderElement commonProps):
  - `role`: "radio" / "checkbox" / "button" per spec R2 table
  - `aria-checked`: single/multiple only, from `counts[id] > 0`
  - `aria-label`: `tooltips[id] ?? id`; count/cycle append `, ${count}`
  - `tabIndex`: roving (D2)
  - `focusable="false"` is NOT needed once tabIndex is explicit
- OutputMap: non-clickable → unchanged (`role="img"`, no tabIndex);
  clickable → `role="group"` root, `role="button"` regions, same roving
  tabindex + Enter/Space → onRegionClick.

### D5. Focus indicator via a new overlay layer
- New layer rendered **above hover** (final order: base → selection →
  hover → focus → annotation), `pointer-events: none`, duplicating the
  focused region's geometry.
- Default focus aesthetic: single high-contrast ring
  (`stroke: #1d4ed8, strokeWidth: 3, fill: none`), defined as
  `DEFAULT_FOCUS_AESTHETIC` in `js/src/a11y.ts` next to `KEY_BINDINGS`
  (one tuning point — see UX tunability note). Suppress native UA outline
  with `outline: none` on paths (we provide our own indicator).
- `onFocus`/`onBlur` now drive `focusedRegion` (fixing the hover
  conflation); hover remains mouse-only.

### D6. No Python API changes
Tooltips and mode already flow to JS. Python work is limited to
integration tests + docs. (If T-inv concludes a container label is
needed, that becomes a follow-up spec amendment — user gate.)

## Files Touched

| File | Change |
|------|--------|
| js/src/components/InputMap.tsx | focusedRegion/tabTarget state, ref map, handleKeyDown, adjustCount, ARIA props, focus overlay, root role |
| js/src/components/OutputMap.tsx | same, gated on `mode.clickable` |
| js/src/utils/renderElement.tsx | pass through tabIndex/role/aria-checked/aria-label/onKeyDown/ref |
| js/src/a11y.ts (new) | KEY_BINDINGS + DEFAULT_FOCUS_AESTHETIC constants (single tuning point) |
| js/src/types.ts | only if prop types need extension (no ModeConfig change) |
| python tests/test_integration.py | new TestKeyboard* classes (Playwright `page.keyboard`) covering AC1-AC7 |
| dev/SPEC.md | rewrite §Accessibility (730-747) to implemented status + D1 rationale + documented limitations |

## Test Strategy

- **No JS unit tests in v1**: the JS package has no test runner
  (packages/shinymap/js/package.json has no `test` script). Adding Vitest
  is a new dev dependency → requires separate user approval (parking lot).
  TS correctness is covered by `make build` (tsc) + eslint.
- **Playwright (Python integration)** carries behavior verification —
  Tab entry, arrow movement (assert document.activeElement id), Enter/Space
  value updates (assert via Shiny output like existing click tests),
  focus indicator presence (focus overlay path exists), role/aria DOM
  assertions per mode (AC1-AC7).
- **Regression**: existing mouse tests untouched and passing (AC8).

## Risks

- **SVG element focusability across browsers**: `tabIndex` on SVG shapes is
  supported in modern evergreen browsers; CI covers chromium only — accept,
  note Firefox/Safari as manual checks in tasks.
- **`+` key layout variance**: on many layouts `+` is Shift+`=`; match both
  `event.key === "+"` and `"="`.
