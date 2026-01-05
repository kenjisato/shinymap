# Git Strategy for AI-Assisted Development

## Branch Hierarchy

```
dev (protected)              # Integration line, PR only
├── feature/<name>           # Large changes (one design document)
│   ├── task/<checkbox>      # One checkbox = one task (squashed)
│   └── div/<topic>          # Feature-level diversion
└── task/<item>              # Small standalone changes (direct PR to dev)

div/*                        # Dev-level diversions (cross-feature fixes)
```

## Branch Scope and Merge Style

| Branch | Based on | Merges to | How |
|--------|----------|-----------|-----|
| `task/*` (standalone) | `dev` | `dev` | PR (squash) |
| `task/*` (in feature) | `feature/*` | `feature/*` | Squash merge |
| `feature/*` | `dev` | `dev` | PR (1-several commits) |
| `div/*` (feature-level) | `feature/*` | `feature/*` | Squash merge |
| `div/*` (dev-level) | `dev` | `dev` | PR (squash) |

**`dev` is protected**: Always use PR to merge.

## Mapping to Design Documents

`design/<feature>.md` contains implementation checklist:

```markdown
## Implementation Checklist

### Phase 1
- [ ] Add move_layer() method
- [ ] Add move_group() method

### Phase 2
- [ ] Create kit/ directory
```

**Workflow**:
1. `feature/<name>` branch for the design document
2. `task/<item>` branch for each checkbox
3. Complete task → squash-merge to `feature/*`
4. All tasks done → PR `feature/*` to `dev`

## COMMUNICATION Files

```
COMMUNICATION.feature.<name>.md
COMMUNICATION.task.<item>.md          # If task spans sessions
COMMUNICATION.div.<topic>-YYYYMMDD-HHMM.md
```

### Feature-Level Template

```markdown
## Feature: <name>

### Design Document
design/<feature>.md

### Progress
| Checkbox | Task Branch | Status | Commit |
|----------|-------------|--------|--------|
| Add move_layer() | task/move-layer | done | abc123 |
| Add move_group() | task/move-group | current | — |

### Current Task
Branch: task/<item>

### Recovery
1. git switch feature/<name>
2. Read design/<feature>.md
3. Check progress table
4. Continue current task
```

### Task-Level Template

```markdown
## Task: <item>

### Checkbox
"<exact text from design doc>"

### Progress
- [time] Started
- [time] Checkpoint before diversion

### Current State
Files: [list]
Tests: pass/fail

### Next Steps
1. [action]
```

## Diversion Protocol

Diversions can be feature-level or dev-level. **Never branch div/* from task/***.

If you need a diversion while working on a task, checkpoint the task first, then create the diversion from the appropriate base (feature/* or dev).

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

**Before any diversion**: checkpoint commit on current branch.

## Non-Negotiable Rules

1. **Checkpoint before diversion**
2. **One intent per commit**
3. **Tasks squash to single commit**
4. **Update COMMUNICATION at session boundaries**
5. **PR to merge into `dev`**

## Command Reference

```bash
# Start feature
git switch -c feature/<name> dev

# Start task (in feature)
git switch -c task/<item> feature/<name>

# Start standalone task
git switch -c task/<item> dev

# Complete task (in feature)
git switch feature/<name>
git merge --squash task/<item>
git commit -m "feat: <item>"

# Complete feature (PR)
# Push feature/<name>, create PR to dev

# Complete standalone task (PR)
# Push task/<item>, create PR to dev
```

## Rule of Thumb

- **feature/* = design document scope**
- **task/* = single checkbox, squashed**
- **Checkpoint before leaving any branch**
- **PR to merge into dev**
