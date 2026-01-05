# Dependency Policy

Guidelines for adding dependencies to shinymap.

## Allowed Licenses

- MIT
- BSD-2-Clause
- BSD-3-Clause
- Apache-2.0

## Licenses to Avoid

- GPL, AGPL (unless explicitly approved by project owner)

## Adding a New Dependency

Before adding any dependency, verify:

1. **Justification**: Why can't stdlib or existing deps solve this?
2. **Size/maintenance**: Is the package actively maintained? How large is it?
3. **License**: Does it use an allowed license?

## Package Managers

| Platform | Manager | Add Command |
|----------|---------|-------------|
| Python | uv | `uv add <package>` |
| JavaScript | npm | Via `make install` |

**Prefer**: `uv sync` over `pip install`
**Prefer**: `make install` over manual `npm install`
