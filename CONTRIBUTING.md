Here’s a ready-to-commit `CONTRIBUTING.md` tailored for GenAI-assisted projects — designed to keep AI-generated code **consistent, minimal, and maintainable** as your team (and the model) scale up:

---

# Contributing Guide

Welcome! This project uses **Generative AI to assist with development**, but all contributions are expected to follow a consistent human-reviewed workflow.

The goal: **concise, idiomatic, and maintainable code**.
GenAI is allowed to *write*, never to *design*.

---

## 1. Repository Constitution

All contributions—human or AI—must comply with the following principles:

### Style & Formatting

* Use **consistent naming**: lowercase_with_underscores for functions, UpperCamelCase for classes.
* Run the formatter and linter before committing:

  * **Python**: `ruff check --fix && ruff format`
  * **JS/TS**: `eslint --fix && prettier --write`
  * **Rust**: `cargo fmt && cargo clippy -D warnings`
* Avoid auto-generated docstrings and redundant comments. Explain *why*, not *what*.

### Architecture

* Keep the **public API minimal**. Avoid unnecessary abstractions.
* No factories, builders, or managers unless absolutely required.
* Favor **pure functions** and small modules over class hierarchies.
* Separate **I/O** (side effects) from **logic** (computation).

### Testing

* Every contribution must include tests.
* Follow the **arrange–act–assert** pattern.
* Minimum coverage: 80%.
* Do not mock for the sake of mocking—mock only external boundaries.

### Error Handling

* Use explicit exception types or error enums.
* Log only contextual information—never secrets or raw payloads.
* Fail fast and clearly: prefer explicit errors over silent fallbacks.

### Dependencies

* Prefer standard libraries or existing dependencies.
* Adding a new dependency requires justification in the PR description.
* Always pin versions in `pyproject.toml`, `package.json`, or `Cargo.toml`.

---

## 2. Using GenAI Productively

### General Rules

* Prompt for **small, focused slices** (≤ 200 LOC, including tests).
* Always include the **Constitution summary** (above) in prompts.
* Never ask the AI to “design the architecture” — that’s human work.
* Prefer:

  > “Implement this function using my repo’s error-handling and style rules.”

### Prompt Template

```
Generate only the code and tests for the single slice below.
Constraints: minimal, idiomatic, no patterns unless essential.
Follow our Constitution. Output only code and tests—no explanations.
```

### Review After Generation

1. Run all linters and formatters.
2. Check for:

   * Redundant abstraction layers.
   * Over-commented or verbose code.
   * Hidden dependencies.
3. Simplify before committing.

---

## 3. Pull Request Requirements

Each PR must:

* Reference an issue or task.
* Include **what**, **why**, and **how tested**.
* Contain ≤ 200 LOC (excluding docs/tests) unless justified.
* Pass all CI checks (lint, format, type-check, test, license).
* Use the PR template provided in `.github/PULL_REQUEST_TEMPLATE.md`.

Example PR summary:

```
Implements token parsing (issue #42)
- Adds parse_auth_header(header: str) -> Token|None
- No new dependencies
- Unit tests for 3 edge cases
```

---

## 4. CI Requirements

The CI pipeline enforces:

* Style: format + lint
* Static analysis: mypy, eslint, clippy
* Tests: ≥ 80% coverage
* Security: dependency audit (pip-audit / npm audit / cargo audit)
* Licensing: `reuse lint`

Any failure blocks merging.

---

## 5. Code “Gardening” Sessions

Every 1–2 weeks:

* Deduplicate utilities.
* Collapse over-abstracted layers.
* Remove dead code.
* Update the Constitution if new conventions emerge.

---

## 6. Philosophy

> “AI can generate code, but humans maintain it.”

We value **clarity over cleverness**, **simplicity over generality**, and **consistency over freedom**.
If in doubt: write less, test more, and review as if you’ll maintain this in a year.

---

Would you like me to tailor this version for a specific language stack (e.g., Python-only, or multi-language repo with Python + TypeScript + Rust)? I can generate the matching `.github/workflows/ci.yml` at the same time.
