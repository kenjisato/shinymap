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
| 4 | Create caption tool | ready for review | task/caption-cli |
| 5 | Enhance sketch app | pending | — |
| 6 | Create review app | pending | — |

### Current: Phase 4 - Caption tool (ready for review)

**Files created:**
- `kit/caption/__init__.py`
- `kit/caption/__main__.py`

**Test added:**
- `test_import_caption_module` in test_kit.py

**Usage:**
```bash
uv run python -m shinymap.kit.caption map.svg -o labeled.svg -s 5 -c red
```

### Next: Phase 5 - Layer Enhancement

### Issues Filed
- #10: output_map click input_id module namespacing bug
- #11: Feature request for ungroup() method
