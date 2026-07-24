# Tasks: Fix Python CI (mypy + format) on dev

All errors verified on dev @ 6c03e8c (2026-07-20). Total: 36 mypy errors in
2 files + 3 unformatted files.

## Phase 1: mypy fixes

- [X] T001 Fix 35 errors in `packages/shinymap/python/src/shinymap/kit/_caption.py`
  - **Error group A (34 errors at line 105)**: `text_attrs` is inferred as
    `dict[str, str]` and spread into `svg.Text(**text_attrs)`, whose
    parameters are narrowly typed (Literals, Length, etc.).
    Fix: annotate the dict where it is created (around line 58):
    ```python
    from typing import Any
    ...
    text_attrs: dict[str, Any] = {
        "text_anchor": "middle",
        ...
    }
    ```
    This is honest typing: `describe(**kwargs: Any)` forwards arbitrary
    user-provided Text attributes.
  - **Error group B (1 error at line 109)**: `labels` is declared
    `dict[str, list[Text]]` but `Regions.__init__` expects
    `dict[str, list[str | Element]]` (invariance). Fix: change the
    annotation (around line 55):
    ```python
    from ..svg import Element  # Element = Circle | Rect | Path | Polygon | Ellipse | Line | Text  (svg/_elements.py:244)
    ...
    labels: dict[str, list[str | Element]] = {}
    ```
    `Element` is already exported from `shinymap.svg` (`svg/__init__.py:24`).

- [X] T002 Fix 1 error in `packages/shinymap/python/src/shinymap/kit/sketch/_tab_relabel.py:540`
  - `group_aes` (defined around line 514) mixes `aes.ByState(...)` and
    `aes.Shape(...)` values, so it is inferred `dict[str, object]`;
    `aes.ByGroup(**group_aes)` expects values of type
    `ByState[Any] | BaseAesthetic | MissingType | None`.
    Fix: annotate explicitly:
    ```python
    group_aes: dict[str, aes.ByState | aes.Shape] = {
        "__all": aes.ByState(...),
        ...
    }
    ```
    If mypy needs the type parameter, use `aes.ByState[Any]`.

## Phase 2: formatting

- [X] T003 Run `make format-python`. Expected to reformat exactly:
  - `packages/shinymap/python/src/shinymap/kit/sketch/app.py`
  - `packages/shinymap/python/src/shinymap/kit/sketch/_tab_original.py`
  - `packages/shinymap/python/src/shinymap/kit/sketch/_tab_relabel.py`

  Note: the unmerged branch `task/phase6-treat-as-line` also reformatted
  these files. After this fix merges, that branch must rebase onto dev
  (see specs/001-kit-module/tasks.md).

## Phase 3: verify

- [X] T004 Run full gates and confirm acceptance criteria in spec.md:
  ```bash
  make lint-python      # ruff check + mypy, 0 errors
  uv run ruff format --check packages/shinymap/python
  make test             # expect 353 passed, 2 skipped, 1 xfailed
  ```
- [ ] T005 Ask user for review, then commit and open PR to `dev`
  (title: `fix: resolve mypy and formatting errors in kit module`)
