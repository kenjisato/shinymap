# Build Commands and Quality Gates

## Prerequisites

- **Python**: 3.12 or higher
- **Node.js**: 18 or higher
- **uv**: Python dependency management ([install guide](https://docs.astral.sh/uv/))

## Makefile Commands

All commands run from repository root.

### Build Commands

```bash
make install       # Install all dependencies (npm + uv sync)
make build         # Full build (TypeScript ’ bundle ’ Python assets)
make build-js      # TypeScript compilation only
make build-bundle  # Bundle React components for Python package
make build-shiny   # Build Shiny bridge
make clean         # Remove build artifacts
```

### Test Commands

```bash
make test          # Run Python tests
```

### Code Quality Commands

```bash
# TypeScript
make lint          # Lint TypeScript (ESLint)
make format        # Format TypeScript (Prettier)

# Python
make lint-python   # Lint Python (ruff check)
make format-python # Format Python (ruff format)
make check-python  # Full check (lint + format check + mypy)
```

### Documentation Commands

```bash
make docs          # Build full documentation site
make docs-python   # Generate Python API docs (quartodoc)
make docs-typescript # Generate TypeScript API docs (typedoc)
make docs-preview  # Preview documentation locally
```

## Quality Gates

A task is NOT complete until these pass:

### If TypeScript touched:
```bash
make lint && make format
make build  # CRITICAL: bundles JS into Python package
```

### If Python touched:
```bash
make lint-python
make format-python
# Or all at once:
make check-python
```

### Always:
```bash
make test  # Must pass
```

## Working Directories

| Task | Working Directory |
|------|-------------------|
| All make commands | Repository root |
| Running example apps | `packages/shinymap/python/` |
| Manual npm commands | `packages/shinymap/js/` (avoid - use make) |

## Build Sequence

When React code changes:

1. TypeScript compilation (`make build-js`)
2. Bundle for Python (`make build-bundle`)
3. Build Shiny bridge (`make build-shiny`)
4. Run Python tests (`make test`)

`make build` runs steps 1-3 automatically.

## Common Issues

### "Module not found" after React changes
Rebuild the bundle: `make build`

### Python imports not resolving
Run: `make install`

### Linting errors on commit
Run: `make format` (TypeScript) or `make format-python` (Python)

### Tests failing after TypeScript changes
Always run `make build` before `make test`
