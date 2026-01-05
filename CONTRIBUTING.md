# Contributing to shinymap

Thank you for your interest in contributing to shinymap!

## Quick Start

```bash
# Clone and setup
git clone https://github.com/kenjisato/shinymap.git
cd shinymap
make install

# Build and test
make build
make test
```

## Repository Structure

```
shinymap/
├── packages/shinymap/js/       # React/TypeScript components
├── packages/shinymap/python/   # Python Shiny adapter + bundled JS
├── design/                     # Implementation plans
└── contributing/               # Detailed guides (see below)
```

## Detailed Guides

| Guide | Purpose |
|-------|---------|
| [contributing/build.md](contributing/build.md) | Build commands, quality gates, working directories |
| [contributing/git-strategy.md](contributing/git-strategy.md) | Branching, releases, hotfixes |
| [contributing/agent-workflow.md](contributing/agent-workflow.md) | Context management, checkpoints (for AI assistants) |
| [contributing/api-cookbook.md](contributing/api-cookbook.md) | Code patterns and examples |

## Essential Commands

```bash
# Build
make build          # Full build (TypeScript + Python bundle)
make test           # Run Python tests

# Code quality
make lint           # Lint TypeScript
make format         # Format TypeScript
make lint-python    # Lint Python
make format-python  # Format Python
make check-python   # Full Python check (lint + format + mypy)
```

## Pull Request Process

1. Create a feature branch from `dev`
2. Make changes and run quality checks
3. Create PR to `dev` (not `main`)
4. After review, merge to `dev`

See [contributing/git-strategy.md](contributing/git-strategy.md) for full details.

## Code of Conduct

Be respectful and constructive. We aim for an inclusive community.

---

**For AI assistants**: See [AGENTS.md](AGENTS.md) for essential guidance.
