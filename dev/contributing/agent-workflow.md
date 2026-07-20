# AI Agent Workflow (Spec-Driven)

How to run development sessions with the Spec Kit workflow. Non-negotiables
live in [.specify/memory/constitution.md](../../.specify/memory/constitution.md).

## Artifact Model

```
.specify/
  memory/constitution.md      # Non-negotiable principles (rarely changes)
  templates/                  # spec/plan/tasks templates (Spec Kit managed)
  scripts/                    # Spec Kit helper scripts
specs/
  NNN-<slug>/
    spec.md                   # WHAT/WHY - user stories, acceptance criteria
    plan.md                   # HOW - architecture, files, decisions
    tasks.md                  # Task breakdown + progress (single source of truth)
    research.md, data-model.md, contracts/   # optional supporting docs
```

Artifacts are **permanent**: they merge with the feature via PR. There is no
cleanup step and no separate session-log file. Progress = checkboxes in
tasks.md. Session handoff = "read tasks.md, continue from first unchecked task".

## Phase Flow and Gates

```
/speckit-specify  → spec.md   → [USER APPROVAL]
/speckit-clarify  (optional: resolve ambiguities before planning)
/speckit-plan     → plan.md   → [USER APPROVAL]
/speckit-tasks    → tasks.md
/speckit-analyze  (optional but recommended: run once with a strong model
                   before handing off to implementation sessions)
/speckit-implement → code     → [make gates] → [USER REVIEW before commit]
```

**Do not skip approval gates.** If implementation reveals that spec or plan
is wrong, stop, update the artifact, get approval, then continue.

## Session Types

### Planning session (strong model, e.g. Opus)
1. `git switch -c feature/NNN-<slug> dev`
2. Run specify/clarify/plan/tasks phases with the user
3. Ensure tasks.md is executable by a weaker model: exact file paths,
   function signatures, acceptance criteria, verification commands per task
4. Commit artifacts (with user review) to the feature branch

### Implementation session (Sonnet-class)
1. `git switch feature/NNN-<slug>` and read `specs/NNN-<slug>/tasks.md`
2. Pick the first unchecked task (respect dependency order)
3. `git switch -c task/<TNNN-slug> feature/NNN-<slug>`
4. Implement exactly what the task says; if the task is ambiguous or wrong,
   stop and ask (do not improvise beyond the plan)
5. Run quality gates (constitution: make lint-python / format-python / test)
6. Mark the task `[X]` in tasks.md (same commit as the implementation)
7. Ask user for review, then squash-merge to the feature branch

### Review before PR
Run the `spec-reviewer` subagent on the feature diff
(`git diff dev...feature/NNN-<slug>`) to check spec/plan/constitution
compliance, then create the PR to `dev`.

## Starting a Session Checklist

```markdown
1. git branch --show-current
2. git pull (if shared branch)
3. Find the feature: ls specs/ , read specs/NNN-<slug>/tasks.md
4. Read spec.md / plan.md if unfamiliar with the feature
5. make test to verify starting state
6. Continue from first unchecked task
```

## During a Session

- Mark tasks `[X]` in tasks.md immediately when done - never batch
- One intent per commit; ask user for review before committing
- Checkpoint before diversions: `git commit --allow-empty -m "chore: checkpoint before <reason>"`

## Parallel Tasks

Tasks marked `[P]` in tasks.md touch disjoint files and may run in parallel:
- Sequential execution is the safe default
- For parallel subagents, use isolated worktrees to avoid conflicts
- Tasks touching the same file must always run sequentially

## Diversion Handling

Create a `div/*` branch when you must fix something that "should have been
done first" (public API change, module reorganization, broken CI):

1. Checkpoint current work
2. Note the diversion in the current feature's tasks.md (one line, with date)
3. Branch from the appropriate base (`feature/*` or `dev`) - **never from `task/*`**
4. Complete, merge (PR if dev-level), return and rebase

## Parking Lot

When you discover unrelated issues: don't fix them now. Add to tasks.md:

```markdown
## Parking Lot
- [ ] Bug: <description> (file:line)
```

Address parking lot items as separate tasks or GitHub issues.

## Recovery from Memory Loss

1. `git branch --show-current` + `git log --oneline -5`
2. `ls specs/` - find the active feature (highest NNN with unchecked tasks)
3. Read that feature's tasks.md, then plan.md if needed
4. `make test` to verify state
5. Continue from first unchecked task
