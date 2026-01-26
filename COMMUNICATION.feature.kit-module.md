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
| 5 | Layer Enhancement | done | (pending PR) |
| 6 | Treat as Line | pending | — |
| 7 | Create review app | pending | — |

### Completed: Phase 5 - Layer Enhancement

All items complete per design/kit-module.md checklist:
- [x] Add layer navigation to sketch UI (pills for hidden/underlay/main/overlay/annotation)
- [x] Track layer assignments via globals (overlay_ids, underlay_ids, hidden_ids, annotation_ids)
- [x] Add visual layer indicators in region list (symbols shown in registered objects display)
- [x] Implement layer assignment UI (layer-specific views with selection)
- [x] Apply layer assignments in final JSON export
- [x] Preserve and display original file's layer metadata and groups
- [x] Update code generation to include all layer types

Additional improvements:
- Simplified rename workflow: renames apply immediately, sidebar shows `new_id <- original_id`
- Fixed metadata groups to respect ID renaming
- Fixed layer assignments to update when regions are renamed
- Fixed code generation to only emit `move_layer` for changed IDs (not already in original)

### Next: Phase 6 - Treat as Line

Per design/kit-module.md checklist:
- [ ] Add `is_stroke_only_candidate()` detection
- [ ] Add "Treat as Line" indicator in sketch UI
- [ ] Add toggle to add/remove from `lines_as_path`
- [ ] Update code generation to include `path_as_line()` calls

### Issues Filed
- #10: output_map click input_id module namespacing bug
- #11: Feature request for ungroup() method
