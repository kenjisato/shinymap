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
- Checkpoint before any diversion
- One intent per commit
- Tasks squash to single commit

See [contributing/git-strategy.md](contributing/git-strategy.md) for details.

## Definition of Done

A task is NOT complete until these pass (run before any commit):

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

## Build Commands

**ALWAYS use Makefile** from repository root. NEVER run npm/tsc/esbuild directly.

```bash
make install       # Install dependencies
make build         # Full build (TypeScript → bundle → Python assets)
make test          # Run Python tests
make lint          # Lint TypeScript
make format        # Format TypeScript
make lint-python   # Lint Python
make format-python # Format Python
```

**Prohibitions**:
- NEVER run `pip install` - use `uv sync` or `uv add`
- NEVER run `npm install` manually - use `make install`

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

## Repo Map

```
shinymap/
├── packages/shinymap/js/src/          # React/TypeScript source
│   └── components/                    # InputMap, OutputMap
├── packages/shinymap/python/
│   ├── src/shinymap/                  # Python package source
│   │   └── www/                       # Built JS assets land here
│   ├── tests/                         # Python tests
│   └── examples/                      # Example apps
├── design/                            # Implementation plans
├── contributing/                      # Detailed workflows
└── SPEC.md                            # Technical specification
```

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

See [contributing/git-strategy.md](contributing/git-strategy.md) for templates.

## What to Read

| Document | Purpose |
|----------|---------|
| [SPEC.md](SPEC.md) | Technical specification, API philosophy, architecture |
| [design/](design/) | Detailed implementation plans |
| [contributing/](contributing/) | Build commands, git strategy, workflows |
| [contributing/api-cookbook.md](contributing/api-cookbook.md) | Code patterns and examples |

## Project Philosophy

- **Pre-1.0.0**: Breaking changes acceptable; no backward-compatibility shims
- **Input-first design**: These are form controls returning simple values (`str`, `list`, `dict`)
- **Geometry-agnostic**: Works with any SVG paths, not geography-specific
- **Unified value model**: `{region_id: int}` internally; `value > 0` means selected

## Communication Style

- Concise and direct
- Technical accuracy over validation
- No time estimates - provide concrete steps

## Dependency Policy

**Allowed licenses**: MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0
**Avoid**: GPL, AGPL (unless explicitly approved)

New dependency requires:
1. Justification (why stdlib or existing deps won't work)
2. Size/maintenance check
3. License verification
