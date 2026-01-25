## Feature: kit-module

### Design Document
design/kit-module.md

### Progress

Following the Migration Plan in design/kit-module.md:

| Phase | Description | Status | Commit |
|-------|-------------|--------|--------|
| 1 | Add new Outline methods | done | e8adbed |
| 2 | Create kit module structure | done | 6b141c0 |
| 3 | Clean up old locations | done | 3e57957 |
| 4 | Create caption tool | done | a4a8f62 |
| 5 | Layer Enhancement | pending | — |
| 6 | Treat as Line | pending | — |
| 7 | Create review app | pending | — |

### Next: Phase 5 - Layer Enhancement

Per design/kit-module.md checklist:
- [x] Add layer dropdown to sketch UI (hidden/underlay/main/overlay) — implemented as visual button panel in `_layer_chooser.py`
- [ ] Update `relabel_rules` to track layer per region
- [x] Add visual layer indicators in region list — symbols shown in registered objects display
- [ ] Implement bulk layer assignment for selections — currently requires re-registration
- [ ] Update code generation to include all layer types

### Issues Filed
- #10: output_map click input_id module namespacing bug
- #11: Feature request for ungroup() method
