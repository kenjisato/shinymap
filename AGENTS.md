# AI Agent Instructions

Essential guidance for AI assistants working on shinymap.

This project uses **Spec-Driven Development** with [GitHub Spec Kit](https://github.com/github/spec-kit).
Non-negotiable principles live in the [constitution](.specify/memory/constitution.md) — read it first.

## Operating Rules (Priority Order)

**When instructions conflict**: constitution > Makefile > this guide > CONTRIBUTING > SPEC/design

**Hard constraints** (details in the constitution):
- Don't claim tests passed unless you actually ran them
- No secrets, no external network calls beyond authorized APIs
- No deleting git history, no force-pushing
- Minimal diffs - no drive-by refactors, no improvements beyond what's requested
- Late serialization is architecture, not preference - keep typed Python objects; serialize only at JS boundary
- New dependencies require explicit user approval

## Spec-Driven Workflow

Every feature produces permanent artifacts in `specs/NNN-<slug>/`:

| Artifact | Contents | Created by | Gate |
|----------|----------|------------|------|
| `spec.md` | WHAT/WHY: user stories, acceptance criteria | `/speckit-specify` | **User approval** |
| `plan.md` | HOW: architecture, file structure, tech decisions | `/speckit-plan` | **User approval** |
| `tasks.md` | Task breakdown (T001…), dependencies, `[P]` parallel markers, progress checkboxes | `/speckit-tasks` | — |
| implementation | Code, per task | `/speckit-implement` or manual | `make` gates + **user review before commit** |

Optional: `/speckit-clarify` (before plan), `/speckit-analyze` (after tasks, before implement).

**Session handoff**: `tasks.md` is the single source of truth for progress.
There are no COMMUNICATION files. To resume work: read `specs/NNN-<slug>/tasks.md`,
continue from the first unchecked task. Mark tasks `[X]` immediately when done.

## Model Routing (Orchestration)

Phases have different capability requirements. Follow this routing:

| Phase | Model / Agent | Notes |
|-------|---------------|-------|
| specify / plan / tasks / analyze | Strong model (Opus-class), main session | Design judgment; task granularity determines implementer success |
| implement (per task) | Sonnet-class, main session or `implementer` subagent | tasks.md must be detailed enough to execute without re-investigation |
| verify (lint/format/test) | Mechanical (`make` targets) | No model judgment needed |
| pre-PR review | `spec-reviewer` subagent (Opus-class) | Compares diff against spec.md/plan.md |

Custom subagents are defined in `.claude/agents/`:
- `implementer` — executes one task from tasks.md, runs quality gates
- `spec-reviewer` — reviews a diff for spec/plan/constitution compliance

Tasks marked `[P]` touch disjoint files and may run in parallel
(use isolated worktrees when running parallel subagents).

## Git Workflow

**Branch hierarchy**: `dev` ← `feature/NNN-<slug>` ← `task/<TNNN-slug>`

- `dev`: Integration line (protected, PR only)
- `feature/NNN-<slug>`: 1:1 with `specs/NNN-<slug>/`
- `task/<TNNN-slug>`: 1:1 with a task ID in tasks.md (squashed on merge)
- `div/*`: Diversions for "should-have-been-done-before" fixes (never branch from `task/*`)

**Rules**:
- **Never edit `dev` branch directly** - always use a branch and PR
- One intent per commit
- Tasks squash to single commit
- **Ask user for manual review before committing**

See [dev/contributing/git-strategy.md](dev/contributing/git-strategy.md) for details.

## Definition of Ready-for-Review

A task is NOT ready for review until these pass:

```bash
# If TypeScript touched:
make lint && make format
make build

# If Python touched (lint-python runs ruff AND mypy, matching CI):
make lint-python
make format-python

# Always:
make test
```

If gates fail, fix them before moving on.

**Important**: Agents never declare "task is complete". Always declare
**"ready for review"** and let the user make the final determination.

See [dev/contributing/build.md](dev/contributing/build.md) for all commands.

## Ask Before Proceeding

**Stop and ask** when:
- Changing public API behavior
- Introducing new dependency
- Altering the unified value model or serialization boundary
- Adding/renaming user-facing modes
- Performance work not explicitly requested
- Deviating from an approved spec.md or plan.md (update the artifact first)

**Proceed with stated assumptions** for:
- Refactors strictly local to requested files
- Test fixes consistent with spec
- Doc updates to reflect actual behavior

**Parking lot**: Record unrelated issues you discover in the feature's
tasks.md under a "Parking Lot" section (or file a GitHub issue), rather
than fixing them now.

## What to Read

| Document | Purpose |
|----------|---------|
| [.specify/memory/constitution.md](.specify/memory/constitution.md) | Non-negotiable principles and quality gates |
| [specs/](specs/) | Feature specs, plans, and task progress (start here to resume work) |
| [dev/SPEC.md](dev/SPEC.md) | Product-level technical specification, API philosophy |
| [dev/design/](dev/design/) | Legacy design documents (archive; new features use specs/) |
| [dev/contributing/](dev/contributing/) | Build commands, git strategy, workflows |
| [dev/contributing/api-cookbook.md](dev/contributing/api-cookbook.md) | Code patterns and examples |
| [dev/contributing/project-structure.md](dev/contributing/project-structure.md) | Repository layout |
| [dev/contributing/dependencies.md](dev/contributing/dependencies.md) | Dependency policy |

## Context Efficiency (Sub-Agents)

Sub-agents run in separate context windows. Only their final result returns
to the main conversation. Use them to preserve context for actual
implementation work.

| Agent | Use For |
|-------|---------|
| `Explore` | Multi-file searches, codebase questions, understanding unfamiliar code |
| `Plan` | Design strategy before implementing features touching 3+ files |
| `implementer` | One tasks.md task (Sonnet; keeps main context clean) |
| `spec-reviewer` | Pre-PR diff review against spec/plan/constitution |
| `general-purpose` | Complex multi-step research |

**Guidelines**:
- Prefer `Explore` agent over direct file reads when exploring unfamiliar areas
- Run long commands (full test suite, builds) in background when possible
- Keep main context for coding - delegate research to sub-agents

## Communication Style

- Concise and direct
- Technical accuracy over validation
- No time estimates - provide concrete steps
