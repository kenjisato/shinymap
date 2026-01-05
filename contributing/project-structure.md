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
├── design/                            # Implementation plans
├── contributing/                      # Development guides
├── SPEC.md                            # Technical specification
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
| Design documents | `design/` |
| Built JS assets | `packages/shinymap/python/src/shinymap/www/` |

## Working Directories

| Task | Run From |
|------|----------|
| All make commands | Repository root |
| Running example apps | `packages/shinymap/python/` |
| Manual npm commands | `packages/shinymap/js/` (prefer make) |
