## Feature: kit-module

### Design Document
design/kit-module.md

### Progress

Following the Migration Plan in design/kit-module.md:

| Phase | Description | Status | Commit |
|-------|-------------|--------|--------|
| 1 | Add new Outline methods | done | e8adbed |
| 2 | Create kit module structure | done | fbced42 |
| 3 | Clean up old locations | done | f664b82a834e42815724ae76dcc162ae3fcfe110 |
| 4 | Create caption tool | pending | — |
| 5 | Enhance sketch app | pending | — |
| 6 | Create review app | pending | — |

### Next: Phase 4 - Create caption tool

1. Create `kit/caption/__main__.py` CLI
2. Add font-size and color CLI options
3. Add tests for describe() and glaze()

### Issues Filed
- #10: output_map click input_id module namespacing bug
- #11: Feature request for ungroup() method
