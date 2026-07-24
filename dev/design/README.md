# Design Documents

This directory contains detailed implementation plans, technical decisions, and design explorations for shinymap features.

## Table of Contents

### Current Architecture

Documents describing the current system. **Read these to understand how things work.**

| Document | Description |
|----------|-------------|
| [aes-protocol.md](aes-protocol.md) | Dict serialization protocol (`to_dict()`/`from_dict()`) |
| [aes-resolution.md](aes-resolution.md) | Runtime aesthetic resolution architecture (two-dimensional: group ↑ and layer ←) |
| [aes-payload-v03.md](aes-payload-v03.md) | v0.3 payload format for JavaScript (three-phase: resolution → payload → lookup) |
| [restructuring-toward-v0.3.md](restructuring-toward-v0.3.md) | Long-term goal: eliminate circular dependencies |

### Planned Work

Documents describing future features or improvements. **Read these if you're implementing them.**

| Document | Description |
|----------|-------------|
| [svg-subpackage.md](svg-subpackage.md) | Move SVG elements to `shinymap.svg` subpackage |

### Implemented (Historical Reference)

Documents describing features that have been implemented. **You don't need to read these** unless you want historical context or design rationale.

| Document | Description | Notes |
|----------|-------------|-------|
| [aesthetic-hierarchy-system.md](aesthetic-hierarchy-system.md) | wash(), ByState/ByType/ByGroup | Implemented in v0.2.0 |
| [count-aesthetic-design.md](count-aesthetic-design.md) | Mode classes, aes.Indexed | Implemented in v0.2.0 |
| [underlay-and-aesthetics.md](underlay-and-aesthetics.md) | Underlays, non-scaling stroke | Implemented in v0.2.0 |
| [props-structure.md](props-structure.md) | Nested props (mode, aes, layers) | Implemented in v0.2.0 |
| [geometry-class-refactoring.md](geometry-class-refactoring.md) | Geometry OOP, Map() function | Implemented in v0.2.0 |
| [update_map_implementation.md](update_map_implementation.md) | Partial update API | Implemented in v0.2.0; may need alignment check |
| [static-map-and-aes-dump.md](static-map-and-aes-dump.md) | StillLife class for static analysis and SVG export | Implemented in v0.3.0 |
| [reference-documentation.md](reference-documentation.md) | Documentation site (Quarto, quartodoc, typedoc) | Implemented in v0.3.0 |

### Partially Implemented

| Document | Description | Notes |
|----------|-------------|-------|
| [polymorphic-elements-svgpy.md](polymorphic-elements-svgpy.md) | svg.py integration | Phase 1-2 (Python + export_svg) done; Phase 3-4 (TypeScript frontend) pending |

### Abandoned / Superseded

| Document | Description | Notes |
|----------|-------------|-------|
| (none currently) | | |

## Future Topics

These topics are mentioned in SPEC.md but don't yet have detailed design documents:

- **Hover events**: Whether/how to emit hover data to the server
- **Keyboard navigation**: Tab order, focus management, Enter/Space selection
- **ARIA roles**: Mapping spatial layouts to form control semantics
- **Delta-based updates**: Sending only changed regions for large maps
- **Canvas fallback**: Alternative rendering for 1000+ regions
- **Geographic extension** (`shinymap-geo`): GeoJSON/TopoJSON, projections

## Near-term TODOs

- **Converter app**: Needs functionality improvements
- **TypeScript polymorphic elements**: Phase 3-4 of [polymorphic-elements-svgpy.md](polymorphic-elements-svgpy.md)

## Contributing

When adding a new design document:

1. **Use descriptive filenames**: `feature-name.md`
2. **Include context**: Problem statement and rationale
3. **Show examples**: Code samples over abstract descriptions
4. **Link to SPEC**: Reference relevant [SPEC.md](../SPEC.md) sections
5. **Update this README**: Add to appropriate section with status
