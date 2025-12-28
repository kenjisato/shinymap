# Design Documents

This directory contains detailed implementation plans, technical decisions, and design explorations for shinymap features.

## Purpose

Design documents serve as:
- **Implementation references**: Detailed code proposals with examples and rationale
- **Decision records**: Why certain approaches were chosen over alternatives
- **Future roadmap**: Ideas and features not yet implemented but worth preserving
- **Knowledge transfer**: Context for contributors and future maintainers

## Document Types

### Implementation Plans
Detailed technical proposals for features mentioned in [SPEC.md](../SPEC.md) but not yet implemented. These include:
- API design with code examples
- Implementation complexity assessment
- Use cases and benefits
- Testing checklists

Example: [update_map_implementation.md](update_map_implementation.md)

### Technical Decisions
Records of significant architectural choices, including:
- Problem statement
- Alternatives considered
- Decision made and rationale
- Consequences and trade-offs

### Performance Investigations
Analysis of performance characteristics:
- Profiling results
- Optimization strategies
- Benchmarks and comparisons

### UI/UX Explorations
Design explorations for user-facing features:
- API ergonomics discussions
- Naming conventions
- Default behaviors

## Contributing

When adding a new design document:

1. **Use descriptive filenames**: `feature_name_implementation.md`, `decision_unified_count_model.md`
2. **Include context**: Why this document exists and what problem it addresses
3. **Show examples**: Code samples are more valuable than abstract descriptions
4. **Assess complexity**: Implementation effort vs. benefit analysis
5. **Link to SPEC**: Reference the relevant section in [SPEC.md](../SPEC.md)
6. **Date decisions**: Include when major decisions were made (helps understand evolution)

## Index

### Implementation Plans
- [update_map_implementation.md](update_map_implementation.md) - Partial update API following Shiny's `update_*()` pattern

### Future Topics
These topics are mentioned in SPEC.md but don't yet have detailed design documents:

- **Hover events**: Whether/how to emit hover data to the server
- **Keyboard navigation**: Tab order, focus management, Enter/Space selection for accessibility
- **ARIA roles**: Mapping spatial layouts to traditional form control semantics
- **Delta-based updates**: Sending only changed regions for large maps (performance optimization)
- **Canvas fallback**: Alternative rendering for very large maps (1000+ regions)
- **Geographic extension** (`shinymap-geo`): GeoJSON/TopoJSON loading, coordinate projections, `sf`/`geopandas` integration

### Near-term TODOs (from v0.2.0 development)

- **Converter app**: The SVG-to-Geometry converter app needs functionality to be useful. Currently a placeholder.
- **`static_map()` function**: Python-only function to render a map as a static SVG string (no JavaScript/React). Useful for:
  - Conversion workflow: preview geometry before saving
  - Export: generate SVG files for documents/presentations
  - Testing: visual regression tests without browser
