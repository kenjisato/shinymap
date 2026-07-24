# Spec: Fix Python CI (mypy + format) on dev

**Type**: dev-level diversion (standalone task, PR to `dev`)
**Branch**: `task/002-ci-mypy-fix` from `dev`

## Why

Python CI on `dev` has been red since PR #17/#18 (kit sketch Phase 5,
2026-01-26). Root cause: `make lint-python` did not run mypy at the time
(fixed in the spec-driven-migration diversion; it now matches CI), so the
Phase 5 work passed local gates but fails the CI type-check and format-check
steps.

## Acceptance Criteria

- [ ] AC1: `uv run mypy packages/shinymap/python/src/shinymap` reports 0 errors
- [ ] AC2: `uv run ruff format --check packages/shinymap/python` passes
- [ ] AC3: `uv run ruff check packages/shinymap/python` passes
- [ ] AC4: `make test` passes (353 passed, 2 skipped, 1 xfailed as of writing)
- [ ] AC5: No behavior changes — type annotations and formatting only
- [ ] AC6: Python CI workflow green on the PR

## Out of Scope

- Refactoring `kit/_caption.py` or the sketch app beyond what typing requires
- The 10 integration tests require Playwright chromium
  (`uv run playwright install chromium`); environment setup is not part of
  this fix
