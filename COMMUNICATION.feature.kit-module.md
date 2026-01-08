## Feature: kit-module

### Design Document
design/kit-module.md

### Progress

Following the Migration Plan in design/kit-module.md:

| Phase | Description | Status | Commit |
|-------|-------------|--------|--------|
| 1 | Add new Outline methods | done | e8adbed |
| 2 | Create kit module structure | done | 4d6ed2b9910e9ed0d927414667f7db5003f22788 |
| 3 | Clean up old locations | pending | — |
| 4 | Create caption tool | pending | — |
| 5 | Enhance sketch app | pending | — |
| 6 | Create review app | pending | — |

### Next: Phase 3 - Clean up old locations

1. Remove `from_svg`, `from_json`, `convert`, `infer_relabel` from `outline/__init__.py` exports
2. Deprecate `outline/_conversion.py` (keep `infer_relabel()` if still useful for code generation)
3. Add EOL stub for `outline/converter/` - DONE in Phase 2

### Issues Filed
- #10: output_map click input_id module namespacing bug
- #11: Feature request for ungroup() method
