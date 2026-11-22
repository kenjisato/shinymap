---
name: shiny-for-python
description: Best practices for writing or reviewing Shiny for Python code. Use whenever creating or modifying Shiny apps (packages/shinymap/python/examples/, shinymap kit apps such as sketch/review, or any app.py using `from shiny import`), and when reviewing Shiny code for deprecated patterns.
---

# Shiny for Python Best Practices

Read [references/shiny-for-python.md](references/shiny-for-python.md) for the
full guide before writing or reviewing Shiny for Python code.

Quick checklist (details and correct/wrong examples in the reference):

- No `@output` decorator — use `@render.xxx` directly
- No `ui.panel_sidebar()` / `ui.panel_main()` — use `ui.page_sidebar(ui.sidebar(...), ...)`
- Lowercase reactives: `reactive.value` / `reactive.calc` / `reactive.effect`
- Never mix Shiny Core and Express syntax in one app (this repo uses **Core**)
- Follow the reference's import patterns and app structure sections
- For React/JS custom components, see the reference's "How to Develop React
  Integration" section

shinymap-specific: kit apps (`kit/sketch/`, `kit/review/`) follow the module
conventions in `dev/contributing/api-cookbook.md` and the tab-module pattern
of `kit/sketch/app.py`.
