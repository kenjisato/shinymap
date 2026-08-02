# Tasks: Keyboard Navigation and ARIA Support

**Branching**: `feature/003-accessibility` (this branch) ← `task/T00X-*`
branches, squash-merged. Rebase this feature branch onto `dev` after PR #19
merges. All design decisions in [plan.md](plan.md); requirements in
[spec.md](spec.md). Implementation sessions: Sonnet-class per AGENTS.md
model routing.

## Phase 0: Investigation

- [X] T001 Investigate container accessible-name wiring (plan D4 / spec Q2)
  - **Result**: no label wiring exists. Root svg gets `role` but no
    accessible name in v1; `aria_label` parameter deferred to a spec
    amendment (Parking Lot). Full finding recorded in plan.md D4.
  - Read `packages/shinymap/python/src/shinymap/_ui.py` `input_map()`:
    does it render a Shiny label element with an id near the map container?
  - If yes: plan to reference it via `aria-labelledby` on the root svg
    (id must be passed in the JS payload — check what props reach InputMap).
  - If no label wiring exists: root svg gets no accessible name in v1;
    record that a future `aria_label` parameter needs a spec amendment
    (user gate). Do NOT add Python parameters in this feature.
  - Deliverable: amend plan.md D4 with findings (2-5 lines), no code.

## Phase 1: Foundation

- [X] T002 renderElement passthrough
  (`packages/shinymap/js/src/utils/renderElement.tsx`)
  - Extend the props consumed at renderElement.tsx:39-40 and commonProps
    (87-102) with optional: `tabIndex`, `role`, `ariaChecked`
    (→ `aria-checked`), `ariaLabel` (→ `aria-label`), `onKeyDown`,
    `elementRef` (ref callback attached to the rendered SVG element)
  - All optional; rendered output unchanged when unset
  - Verify: `make build && make lint`

- [X] T003 Create `packages/shinymap/js/src/a11y.ts` [P with T002]
  - `KEY_BINDINGS`: maps `event.key` values → actions
    (next: ArrowRight/ArrowDown; prev: ArrowLeft/ArrowUp; first: Home;
    last: End; activate: Enter/" "; increment: "+"/"="; decrement: "-")
  - `DEFAULT_FOCUS_AESTHETIC = { strokeColor: "#1d4ed8", strokeWidth: 3,
    fillColor: "none" }` (align field names with existing aesthetic types
    in types.ts)
  - Single tuning point per plan's UX-tunability note; short doc comment
    saying these are intended to be adjusted after UX feedback

## Phase 2: InputMap (`packages/shinymap/js/src/components/InputMap.tsx`)

- [X] T004 Separate focus from hover + focus overlay (depends: T002, T003)
  - New `focusedRegion` state; change onFocus/onBlur (currently
    InputMap.tsx:336-337 reusing hover) to set `focusedRegion`; hover
    becomes mouse-only
  - New focus overlay layer above hover (order: base → selection → hover →
    focus → annotation), duplicating the focused region with
    DEFAULT_FOCUS_AESTHETIC, `pointer-events: none` (mirror hover overlay
    structure at InputMap.tsx:416-501)
  - `outline: none` style on region elements
  - Verify: `make build && make lint`; manual: focus via JS console shows ring

- [X] T005 Roving tabindex + navigation keys (depends: T004)
  - `tabTarget` state per plan D2 (initial: first selected region for
    single mode, else first interactive region); regions get
    `tabIndex={id === tabTarget ? 0 : -1}`
  - Ref map `useRef<Map<RegionId, Element>>` via T002 `elementRef`
  - `handleKeyDown(id, e)`: next/prev (wrap), Home/End per KEY_BINDINGS,
    `e.preventDefault()`, update tabTarget + call `.focus()`
  - Navigation order = base-layer region array (already excludes
    overlay/underlay/hidden/annotation)

- [X] T006 Activation keys (depends: T005)
  - Enter/Space → `e.preventDefault()` + existing `handleClick(id)`
    (InputMap.tsx:142-168) — no separate state path
  - count mode: "+"/"=" increment (same as click), "-" decrement
    `max(0, count-1)`; cycle mode: "+"/"-" → `(count ± 1 + n) % n`
    via new `adjustCount(id, delta)` firing the same onChange
  - Keys other than KEY_BINDINGS: no preventDefault

- [X] T007 ARIA attributes (depends: T005; can develop with T006 in parallel
  only if working in the same branch — otherwise sequential, same file)
  - Root svg (InputMap.tsx:225-229): `role="radiogroup"` (single) /
    `role="group"` (multiple/count/cycle); **no `aria-label` on the root**
    per T001 finding (plan.md D4)
  - Regions: `role` + `aria-checked` per spec R2 table;
    `aria-label = tooltips[id] ?? id`, count/cycle append `, ${count}`
  - **Also update the test fixtures**: `tests/conftest.py` waits on
    `svg[role='img']` in all three fixtures, and
    `test_integration.py::test_svg_has_accessibility_role` asserts
    `role="img"`. Changing the InputMap root role breaks both. OutputMap
    keeps `role="img"` (spec AC7), so split the assertion by component.
  - Verify: `make build && make lint`; DOM inspection in demo app

## Phase 3: OutputMap (`packages/shinymap/js/src/components/OutputMap.tsx`)

- [ ] T008 Clickable Display mode a11y (depends: T007 — reuse patterns)
  - Gate everything on `mode.clickable` (OutputMap.tsx:77): roving
    tabindex, handleKeyDown (navigation + Enter/Space → onRegionClick),
    `role="group"` root / `role="button"` regions, focus overlay
  - Fix onFocus/onBlur hover conflation (OutputMap.tsx:317-318) same as T004
  - Non-clickable: verify zero change (`role="img"`, no tabIndex) — spec AC7

## Phase 4: Tests

- [ ] T009 Playwright integration tests (depends: T008)
  - **First** run `make build` and commit the regenerated bundles
    (`js/dist/`, `python/src/shinymap/www/`) as one `chore:` commit —
    T002-T008 deliberately keep generated artifacts out of task commits so
    each source diff stays reviewable; the Playwright tests load the
    Python package's bundle and need it current
  - New file `packages/shinymap/python/tests/test_a11y.py` following
    `test_integration.py` fixtures/conventions (markers: integration)
  - Cover AC1-AC7 from spec.md; map each test name to its AC in a comment
  - Keyboard via `page.keyboard.press(...)`; focus assertions via
    `page.evaluate("document.activeElement...")`; value assertions via
    rendered Shiny output (same technique as existing click tests)

- [ ] T010 Gates + regression (depends: T009)
  - `make lint && make format && make build` (TS)
  - `make lint-python && make format-python`
  - `make test` — all existing tests pass unchanged (AC8), new tests green
  - Check spec.md AC checkboxes that are now verified

## Phase 5: Docs and wrap-up

- [ ] T011 Documentation (depends: T010) [P with T012]
  - Rewrite dev/SPEC.md §Accessibility (lines ~730-747): implemented
    behavior, D1 rationale (selection does not follow focus), documented
    limitations (DOM-order navigation, few-hundred-regions guidance)
  - CHANGELOG.md entry under Unreleased/0.3.0
- [ ] T012 Manual cross-browser check (depends: T010) [P with T011]
  - Firefox + Safari: Tab reaches map, ring visible, arrows/Enter work
    (CI is chromium-only); record results here
- [ ] T013 Review + PR (depends: T011, T012)
  - Run spec-reviewer subagent on `git diff dev...feature/003-accessibility`
  - User review → PR to dev referencing specs/003-accessibility/

## Parking Lot

- [ ] Container accessible name (`aria_label` parameter or generic attribute
  passthrough on `input_map()`) — needs a spec amendment, user gate (T001)
- [ ] JS unit test runner (Vitest) — new dev dependency, needs user approval
- [ ] `aes` focus state (user-configurable focus aesthetics) — separate spec
- [ ] Spatial (geometric) arrow navigation — future enhancement
- [ ] aria-live selection summaries for screen readers
