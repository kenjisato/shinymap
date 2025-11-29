# shinymap Monorepo

This repository now hosts a multi-package workspace:

- `packages/shinymap/` – core map renderer and language bindings with lightweight demo geometry.
- `packages/shinymapjp/` – Japan-prefecture geometry assets (JS + Python façades).
- `archive/legacy/` – the previous implementation preserved for reference while the new modular design is built out.

See `SPEC.md` for the current roadmap and design goals.

> The repository is pre-1.0.0. Breaking changes are expected while we focus on clarity and performance.

## Development Notes

- Python packages use [Hatch](https://hatch.pypa.io/) for builds. When working locally, we recommend managing environments and dependencies with [uv](https://docs.astral.sh/uv/).
- Minimum supported Python version is 3.12.
