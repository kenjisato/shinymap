# AI Agent Instructions

Essential guidance for AI assistants working on shinymap.

## Operating Rules (Priority Order)

**When instructions conflict**: Makefile > this guide > CONTRIBUTING > SPEC/design

**Hard constraints**:
- Don't claim tests passed unless you actually ran them
- No secrets, no external network calls beyond authorized APIs
- No deleting git history, no force-pushing
- Minimal diffs - no drive-by refactors, no improvements beyond what's requested
- Late serialization is architecture, not preference - keep typed Python objects; serialize only at JS boundary

**Default behavior**: small PRs, edit existing files over creating new ones

## Git Workflow

**Branch hierarchy**: `dev` ← `feature/*` ← `task/*`

- `dev`: Integration line (protected, PR only)
- `feature/*`: Large changes (one design document)
- `task/*`: Small changes (one checkbox item, squashed on merge)
- `div/*`: Diversions for "should-have-been-done-before" fixes

**Merge to dev via PR** from `feature/*` (large) or `task/*` (small).

**Rules**:
- **Never edit `dev` branch directly** - always use a branch and PR
- Checkpoint before any diversion
- One intent per commit
- Tasks squash to single commit
- **Ask user for manual review before committing**

See [contributing/git-strategy.md](contributing/git-strategy.md) for details.

## Definition of Done

A task is NOT ready for review until these pass:

```bash
# If TypeScript touched:
make lint && make format
make build

# If Python touched:
make lint-python
make format-python

# Always:
make test
```

If tests fail, fix them before moving on.

**Important**: Agents never declare "task is complete". Always declare **"ready for review"** and let the user make the final determination.

See [contributing/build.md](contributing/build.md) for all commands.

## Ask Before Proceeding

**Stop and ask** when:
- Changing public API behavior
- Introducing new dependency
- Altering the unified value model or serialization boundary
- Adding/renaming user-facing modes
- Performance work not explicitly requested

**Proceed with stated assumptions** for:
- Refactors strictly local to requested files
- Test fixes consistent with spec
- Doc updates to reflect actual behavior

## Context Management

COMMUNICATION files are per-branch:
- `COMMUNICATION.feature.<name>.md` - Feature progress
- `COMMUNICATION.task.<item>.md` - Task details (if multi-session)
- `COMMUNICATION.div.<topic>-YYYYMMDD-HHMM.md` - Diversion context

**At session end**, update with:
- Current branch and commit
- Progress log
- Next steps
- Recovery instructions

**Checkpoint commit**: `git commit --allow-empty -m "chore: checkpoint"`

**Parking lot**: Record unrelated issues in COMMUNICATION rather than fixing now.

See [contributing/agent-workflow.md](contributing/agent-workflow.md) for templates.

## What to Read

| Document | Purpose |
|----------|---------|
| [SPEC.md](SPEC.md) | Technical specification, API philosophy, architecture |
| [design/](design/) | Detailed implementation plans |
| [contributing/](contributing/) | Build commands, git strategy, workflows |
| [contributing/api-cookbook.md](contributing/api-cookbook.md) | Code patterns and examples |
| [contributing/project-structure.md](contributing/project-structure.md) | Repository layout |
| [contributing/dependencies.md](contributing/dependencies.md) | Dependency policy |

## Communication Style

- Concise and direct
- Technical accuracy over validation
- No time estimates - provide concrete steps
