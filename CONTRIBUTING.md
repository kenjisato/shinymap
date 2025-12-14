# Contributing to shinymap

Thank you for your interest in contributing to shinymap! This guide provides practical workflows for contributing to this monorepo.

## Repository Structure

```
shinymap/
├── packages/
│   ├── shinymap/js/          # React/TypeScript core components
│   └── shinymap/python/      # Python Shiny adapter + bundled JS assets
├── CLAUDE.md                  # AI assistant guide (design philosophy, project context)
├── CONTRIBUTING.md            # This file (practical development workflows)
└── .github/workflows/         # CI workflows
```

## Prerequisites

- **Python**: 3.12 or higher
- **Node.js**: 18 or higher
- **uv**: Recommended for Python dependency management ([install guide](https://docs.astral.sh/uv/))
- **npm**: Comes with Node.js

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/shinymap.git
   cd shinymap
   ```

2. **Set up Python development:**
   ```bash
   cd packages/shinymap/python
   uv sync --dev
   cd ../../..  # Return to repo root
   ```

3. **Set up JavaScript development:**
   ```bash
   cd packages/shinymap/js
   npm install
   cd ../../..  # Return to repo root
   ```

---

## Development Workflows

### Working with React/TypeScript Code

**Working directory:** `packages/shinymap/js/`

#### After modifying React components:

```bash
cd packages/shinymap/js

# 1. Format and lint
npm run format
npm run lint

# 2. Build TypeScript
npm run build

# 3. Run standalone React demo (optional - for quick testing)
npm run serve
# Opens demo at http://localhost:4173

# 4. Build bundled JS for Python package
node build-global.js

# 5. Test with Python Shiny demo
cd ../python
uv run shiny run examples/demo_app.py
# Opens at http://localhost:8000

# Return to root when done
cd ../../..
```

**Key points:**
- Always rebuild the global bundle (`node build-global.js`) before testing Python integration
- The bundled JS is copied to `packages/shinymap/python/src/shinymap/www/shinymap-shiny.js`
- Lint/format before committing: `npm run lint && npm run format:check`
- **Build sequence matters**: `npm run build` (TypeScript compilation) must complete before `node build-global.js` (bundling)

---

### Working with Python Code

**Working directory:** `packages/shinymap/python/`

#### After modifying Python source:

```bash
cd packages/shinymap/python

# 1. Run linter and formatter
uv run ruff check --fix .
uv run ruff format .

# 2. Type check
uv run mypy src/shinymap

# 3. Run tests
uv run pytest

# 4. Test with example apps
uv run shiny run examples/demo_app.py
# Opens at http://localhost:8000

# Return to root when done
cd ../../..
```

**Running specific tests:**
```bash
cd packages/shinymap/python
uv run pytest tests/test_builder.py -v
uv run pytest --cov=shinymap  # With coverage
```

---

### Cross-Package Workflows

#### When React changes affect Python package:

```bash
# 1. Build and bundle React code
cd packages/shinymap/js
npm run build
node build-global.js

# 2. Test Python integration
cd ../python
uv run pytest  # Run all tests
uv run shiny run examples/demo_app.py  # Manual testing

# Return to root
cd ../../..
```

#### Full pre-commit checklist:

```bash
# JavaScript checks (from packages/shinymap/js/)
cd packages/shinymap/js
npm run lint
npm run format:check
npm run build
cd ../../..

# Python checks (from packages/shinymap/python/)
cd packages/shinymap/python
uv run ruff check .
uv run ruff format --check .
uv run mypy src/shinymap
uv run pytest
cd ../../..
```

---

## Code Quality Standards

### Python

- **Style**: PEP 8 (enforced by ruff)
- **Type hints**: Required for all function signatures
- **Formatting**: `ruff format` (line length: 100)
- **Linting**: `ruff check` (configured in `pyproject.toml`)
- **Testing**: pytest with minimum 80% coverage

### JavaScript/TypeScript

- **Style**: Prettier (100 char line width, 2-space indent)
- **Linting**: ESLint with TypeScript plugin
- **Type checking**: TypeScript strict mode
- **Formatting**: `npm run format`

### General Principles

- **Minimal API surface**: Avoid unnecessary abstractions
- **Simple over clever**: Prefer clear, straightforward code
- **Test new functionality**: Include tests with new features
- **No over-engineering**: Don't add features beyond what's requested
- **Document public APIs**: Include docstrings with examples for user-facing functions

---

## Testing Guidelines

### Python Tests

```python
import pytest
from shinymap import Map

@pytest.mark.unit
def test_map_builder_basic():
    """Test basic Map builder functionality."""
    geometry = {"a": "M0 0 L10 0 L10 10 L0 10 Z"}
    map_obj = Map(geometry)
    payload = map_obj.build()
    assert payload.geometry == geometry
```

**Test markers:**
- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (may require Shiny runtime)

### JavaScript Tests

(Coming soon - test framework to be added)

---

## Pull Request Process

### Before creating a PR:

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the workflows above

3. **Run all checks:**
   ```bash
   # JavaScript (from packages/shinymap/js/)
   npm run lint && npm run format:check && npm run build

   # Python (from packages/shinymap/python/)
   uv run ruff check . && uv run mypy src/shinymap && uv run pytest
   ```

4. **Commit with clear messages:**
   ```bash
   git add .
   git commit -m "Add hover_highlight parameter to input_map

   - Adds stroke_width, fill_opacity options for hover state
   - Updates README with examples
   - Adds tests for hover customization"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

### PR Requirements

- **Reference related issues**: "Fixes #42" or "Relates to #42"
- **Clear description**: What, why, and how you tested
- **Pass CI checks**: All automated checks must pass
- **Keep focused**: One feature/fix per PR
- **Update docs**: Include documentation changes for user-facing features

---

## Release Process

(For maintainers)

### Python Package

```bash
cd packages/shinymap/python

# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Build and publish
rm -rf dist/
uv build
uv publish

cd ../../..
```

### JavaScript Package

```bash
cd packages/shinymap/js

# 1. Update version in package.json
# 2. Rebuild bundle
node build-global.js

# 3. Publish to npm (if applicable)
npm publish

cd ../../..
```

---

## Common Issues

### "Module not found" after React changes
- **Solution**: Rebuild the bundle with `node build-global.js`

### Python imports not resolving
- **Solution**: Run `uv sync --dev` from `packages/shinymap/python/`

### Linting errors on commit
- **Solution**: Run `npm run format` (JS) or `uv run ruff format .` (Python)

### Tests failing after changes
- **Solution**: Check if you need to rebuild the JS bundle for Python tests

---

## Getting Help

- **Issues**: Open an issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check [CLAUDE.md](CLAUDE.md) for project philosophy and design decisions
- **Examples**: See `packages/shinymap/python/examples/` for usage patterns

---

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to foster an inclusive and welcoming community.

---

**Thank you for contributing to shinymap!**

For AI assistants: See [CLAUDE.md](CLAUDE.md) for project context, design philosophy, and architectural decisions.
