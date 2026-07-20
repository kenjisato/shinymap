# shinymap Constitution

Non-negotiable principles for shinymap development. All specs, plans, tasks,
and implementations MUST comply. When any other document conflicts with this
constitution, the constitution wins (except the Makefile, which is the
authoritative source for command sequences).

## Core Principles

### I. Input-First Philosophy
shinymap components are form controls, not visualizations. Inputs return
simple values (`str | None`, `list[str]`, `dict[str, int]`), never shapes or
GeoJSON. New features must preserve this contract.

### II. Geometry-Agnostic Design
The same API works for any SVG paths: geographic maps, diagrams, floor plans,
anatomical illustrations. Nothing in the core library may assume geographic
semantics (projections, coordinates, place names). Geographic features belong
to the future `shinymap-geo` extension.

### III. Unified Value Model with Late Serialization (NON-NEGOTIABLE)
Internally, selection state is a `{region_id: count}` mapping; mode classes
(Single/Multiple/Cycle/Count) transform it to ergonomic Python types. Keep
typed Python objects throughout the Python layer; serialize (snake_case →
camelCase, dict conversion) only at the JS boundary. This is architecture,
not preference.

### IV. Pre-1.0 Breaking Changes, No Compatibility Shims
Breaking changes are acceptable while optimizing for clarity. Do not add
backward-compatibility shims, renamed re-exports, or deprecation layers.
For removed/renamed public API, use the End-of-Life ImportError pattern
(raise ImportError with migration instructions).

### V. Simplicity and Minimal Diffs
Only make changes directly requested or clearly necessary for the current
task. No drive-by refactors, no speculative abstractions, no performance
work unless requested. Defer optimizations until real-world use demonstrates
need.

### VI. MIT-Compatible Dependencies Only
The project is MIT licensed. Every dependency (Python and JS) must be
MIT-compatible. Introducing any new dependency requires explicit user
approval before implementation.

## Platform Constraints

- Python: minimum 3.12; `uv` for dependency management, `hatch` for builds.
- Workspace setup: `uv sync --all-packages --all-extras` at repo root, then
  `uv run playwright install chromium` (required for integration tests).
- Multi-platform architecture: React core (`packages/shinymap/js`),
  Python Shiny bindings (`packages/shinymap/python`), R Shiny planned.
  TypeScript components and Python adapters must stay in sync.

## Development Workflow

### Spec-Driven Development
Every feature follows: `spec.md` (WHAT/WHY, user approval required) →
`plan.md` (HOW, user approval required) → `tasks.md` (task breakdown) →
implementation. Artifacts live in `specs/NNN-<slug>/` and are permanent:
they merge with the feature and serve as session handoff. Session recovery =
read `specs/NNN-<slug>/tasks.md` and continue from the first unchecked task.

### Branching (maps Spec Kit features onto the repo git strategy)
- `dev` is protected: merge only via PR.
- Feature branch `feature/NNN-<slug>` corresponds 1:1 to `specs/NNN-<slug>/`.
- Task branch `task/<TNNN-slug>` corresponds 1:1 to a task ID in `tasks.md`;
  squash-merged into its feature branch.
- `div/*` diversions for should-have-been-done-first fixes; never branch
  `div/*` from `task/*`.

### Quality Gates (Definition of Ready-for-Review)
All of the following MUST pass before a task is declared ready for review:

```bash
# If TypeScript touched:
make lint && make format && make build

# If Python touched (lint-python includes ruff AND mypy):
make lint-python && make format-python

# Always:
make test
```

- Never claim tests passed without actually running them.
- Agents never declare "complete"; they declare **"ready for review"** and
  the user makes the final determination.
- **User review is required before every commit.**

## Governance

- This constitution supersedes AGENTS.md, CONTRIBUTING.md, and design
  documents when they conflict.
- Amendments require a PR approved by the maintainer and a version bump
  below (semver: principle changes = MAJOR/MINOR, wording = PATCH).
- `specs/` checklists and PR reviews must verify compliance with Core
  Principles I–VI.

**Version**: 1.0.0 | **Ratified**: 2026-07-20 | **Last Amended**: 2026-07-20
