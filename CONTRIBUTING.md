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
├── docs/                       # User-facing documentation site (Quarto)
├── specs/                      # Feature specs and task progress (Spec Kit)
└── dev/                        # Internal docs: SPEC, PROPOSAL, design/, contributing/
```

## Detailed Guides

| Guide | Purpose |
|-------|---------|
| [dev/contributing/build.md](dev/contributing/build.md) | Build commands, quality gates, working directories |
| [dev/contributing/git-strategy.md](dev/contributing/git-strategy.md) | Branching, releases, hotfixes |
| [dev/contributing/agent-workflow.md](dev/contributing/agent-workflow.md) | Spec-driven workflow (for AI assistants) |
| [dev/contributing/api-cookbook.md](dev/contributing/api-cookbook.md) | Code patterns and examples |

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

See [dev/contributing/git-strategy.md](dev/contributing/git-strategy.md) for full details.

## Code of Conduct

Be respectful and constructive. We aim for an inclusive community.

---

**For AI assistants**: See [AGENTS.md](AGENTS.md) for essential guidance.
