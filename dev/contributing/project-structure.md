# Project Structure

Repository layout for shinymap.

## Directory Map

```
shinymap/
├── packages/shinymap/js/src/          # React/TypeScript source
│   └── components/                    # InputMap, OutputMap
├── packages/shinymap/python/
│   ├── src/shinymap/                  # Python package source
│   │   └── www/                       # Built JS assets (generated)
│   ├── tests/                         # Python tests
│   └── examples/                      # Example Shiny apps
├── docs/                              # User-facing documentation site (Quarto)
├── specs/                             # Feature specs + task progress (Spec Kit)
├── dev/                               # Internal docs
│   ├── SPEC.md                        # Technical specification
│   ├── PROPOSAL.md                    # Project proposal (JOSS)
│   ├── design/                        # Legacy design documents (archive)
│   └── contributing/                  # Development guides
├── .specify/                          # Spec Kit templates, scripts, constitution
├── .claude/                           # Claude Code skills and subagents
├── AGENTS.md                          # AI agent instructions
└── CONTRIBUTING.md                    # Getting started
```

## Key Locations

| What | Where |
|------|-------|
| React components | `packages/shinymap/js/src/components/` |
| Python source | `packages/shinymap/python/src/shinymap/` |
| Tests | `packages/shinymap/python/tests/` |
| Example apps | `packages/shinymap/python/examples/` |
| Feature specs (active) | `specs/` |
| Design documents (archive) | `dev/design/` |
| Built JS assets | `packages/shinymap/python/src/shinymap/www/` |

## Working Directories

| Task | Run From |
|------|----------|
| All make commands | Repository root |
| Running example apps | `packages/shinymap/python/` |
| Manual npm commands | `packages/shinymap/js/` (prefer make) |
