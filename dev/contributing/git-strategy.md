# Git Strategy for AI-Assisted Development

## Branch Hierarchy

```
dev (protected)              # Integration line, PR only
├── feature/NNN-<slug>       # 1:1 with specs/NNN-<slug>/ (one spec)
│   ├── task/<TNNN-slug>     # 1:1 with a task ID in tasks.md (squashed)
│   └── div/<topic>          # Feature-level diversion
└── task/<item>              # Small standalone changes (direct PR to dev)

div/*                        # Dev-level diversions (cross-feature fixes)
```

## Branch Scope and Merge Style

| Branch | Based on | Merges to | How |
|--------|----------|-----------|-----|
| `task/*` (standalone) | `dev` | `dev` | PR (squash) |
| `task/*` (in feature) | `feature/*` | `feature/*` | Squash merge |
| `feature/NNN-<slug>` | `dev` | `dev` | PR (1-several commits) |
| `div/*` (feature-level) | `feature/*` | `feature/*` | Squash merge |
| `div/*` (dev-level) | `dev` | `dev` | PR (squash) |

**`dev` is protected**: Always use PR to merge.

## Mapping to Spec Artifacts

`specs/NNN-<slug>/tasks.md` contains the task breakdown:

```markdown
## Phase 1: Setup
- [ ] T001 Create module skeleton in packages/.../kit/review/
- [ ] T002 [P] Add CLI entry in kit/review/__main__.py
```

**Workflow**:
1. `feature/NNN-<slug>` branch for the spec (spec.md, plan.md, tasks.md
   committed here first)
2. `task/<TNNN-slug>` branch for each task (e.g. `task/T001-module-skeleton`)
3. Complete task → mark `[X]` in tasks.md → squash-merge to `feature/*`
4. All tasks done → spec-reviewer check → PR `feature/*` to `dev`

Spec artifacts are permanent and merge with the feature. **Do not delete
them before PR** (this replaces the old COMMUNICATION.*.md convention,
which required deletion).

## Diversion Protocol

Diversions can be feature-level or dev-level. **Never branch div/* from task/***.

If you need a diversion while working on a task, checkpoint the task first,
then create the diversion from the appropriate base (feature/* or dev).

**Feature-level** (affects only this feature):
```bash
git switch -c div/<topic>-YYYYMMDD-HHMM feature/<name>
# ... fix ...
git switch feature/<name>
git merge --squash div/<topic>-...
git commit -m "refactor: <topic>"
git switch task/<item>
git rebase feature/<name>
```

**Dev-level** (affects multiple features, needs PR to dev):
```bash
git switch -c div/<topic>-YYYYMMDD-HHMM dev
# ... fix ...
# Create PR to dev, merge
git switch feature/<name>
git rebase dev
git switch task/<item>
git rebase feature/<name>
```

**Before any diversion**: checkpoint commit on current branch, and note the
diversion in the feature's tasks.md.

## Non-Negotiable Rules

1. **Never edit `dev` directly** - always use a branch and PR
2. **Spec artifacts before implementation** - no feature branch without
   specs/NNN-<slug>/ (spec.md approved by user)
3. **Ask user for review before committing**
4. **Checkpoint before diversion**
5. **One intent per commit**
6. **Tasks squash to single commit**
7. **Mark tasks `[X]` in tasks.md in the same commit as the implementation**
8. **PR to merge into `dev`**

## Command Reference

```bash
# Start feature (planning session)
git switch -c feature/NNN-<slug> dev
# ... create specs/NNN-<slug>/{spec,plan,tasks}.md via /speckit-* ...

# Start task (implementation session)
git switch -c task/<TNNN-slug> feature/NNN-<slug>

# Complete task (in feature)
git switch feature/NNN-<slug>
git merge --squash task/<TNNN-slug>
git commit -m "feat: <task summary> (TNNN)"

# Complete feature (PR)
# Push feature/NNN-<slug>, create PR to dev

# Start standalone task
git switch -c task/<item> dev
```

## Rule of Thumb

- **feature/NNN-slug = one spec directory**
- **task/* = one tasks.md item, squashed**
- **Checkpoint before leaving any branch**
- **PR to merge into dev**
