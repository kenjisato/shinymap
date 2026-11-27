# Feature Specification: Bundled demo maps and a GeoJSON-to-outline recipe

**Feature Branch**: `feature/003-demo-maps`

**Created**: 2026-11-27

**Status**: Draft

**Input**: GitHub issue #75. Bundle small demo outlines (world countries, US states, Japan prefectures) from public-domain or CC BY sources, replacing the CC BY-SA Japan map; show how to turn one's own GeoJSON into an outline; drop `shinymap-geo` from the plan and state GIS features as a non-goal.

## Clarifications

### Session 2026-11-27

- Q: Constitution II and SPEC keep real maps and geographic features out of the core. How to resolve the conflict? → A: Amend constitution II narrowly. The core's code stays free of geographic logic; the core may ship demo maps as shape data. The reference to `shinymap-geo` is removed.
- Q: Should shinymap read GeoJSON directly? → A: No. GeoJSON is geographic data; shinymap needs simplified shapes with one ID per region, where regions are easy to tell apart. Producing those (projecting, simplifying, picking the ID field) is a drawing step outside shinymap, done with mapshaper. Its SVG output is read by the existing `Outline.from_svg()`. The demo maps are made by the same recipe.

## Context

shinymap's position: clickable shapes as Shiny inputs, not a map library. Mapping libraries (Leaflet, plotly, pydeck) already cover GIS work, so shinymap will not build `shinymap-geo`. Maps stay useful as one kind of shape, and new users expect one to try, so the core ships a few small demo maps and the docs show how to make one's own.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Try shinymap on a familiar map with no data hunting (Priority: P1)

A first-time user installs shinymap and builds an input or output map of world countries, US states, or Japan prefectures without downloading or converting anything.

**Why this priority**: The "working app in five minutes" goal (#74) depends on it; today the only real map lives in `examples/data/` and is not part of the installed package.

**Independent Test**: In a fresh environment with only shinymap installed, load each demo map in one line and render it in `input_map` and `output_map`.

**Acceptance Scenarios**:

1. **Given** shinymap is installed, **When** the user loads the world, US, or Japan demo map, **Then** they get an Outline usable directly in `input_map`/`output_map`, with no extra download or package.
2. **Given** a demo map, **When** the user inspects it, **Then** region IDs follow a widely used code scheme and each region has a human-readable name, so the user can join their own data by code.
3. **Given** a demo map, **When** the user looks for its source and license, **Then** both are stated in the package and on the docs page.

---

### User Story 2 - Make my own region map from GeoJSON (Priority: P2)

A user has boundaries as GeoJSON (e.g. from a government portal) and wants a shinymap outline of them: simplified, upright, one region per feature, with IDs from a chosen field.

**Why this priority**: GeoJSON is the format people actually have, and raw GeoJSON is too detailed and unprojected to use as clickable regions. Without a documented recipe, users get stuck or try to load raw data.

**Independent Test**: Following only the docs page, turn a GeoJSON file of polygons into an SVG with mapshaper (browser version, no install) and load it as an Outline whose region IDs are the chosen field.

**Acceptance Scenarios**:

1. **Given** a GeoJSON file of area features, **When** the user follows the docs recipe, **Then** they get an outline with one region per feature, IDs from the chosen field, and a recognisable, simplified shape.
2. **Given** the resulting outline, **When** used in `input_map`, **Then** clicking a region returns the chosen ID.

---

### User Story 3 - Clear licensing and a clear scope (Priority: P3)

Teachers and researchers can use the bundled maps in their own figures without share-alike uncertainty, and contributors can see that GIS features are out of scope.

**Why this priority**: The current Japan map (CC BY-SA 3.0) makes users unsure about their figures; the project plan still promises `shinymap-geo`.

**Independent Test**: No CC BY-SA or other share-alike data remains in the shipped package or examples; PROPOSAL, SPEC and the constitution no longer plan `shinymap-geo` and state GIS features as a non-goal.

**Acceptance Scenarios**:

1. **Given** the repository after this feature, **When** searching examples and package data, **Then** the CC BY-SA Japan map is gone and examples that used it use the bundled Japan demo map.
2. **Given** `dev/PROPOSAL.md`, `dev/SPEC.md` and the constitution, **When** reading them, **Then** none plans `shinymap-geo`, and GIS features (projection, geopandas/sf integration, tiles, simplification, reading GeoJSON) are stated as a non-goal with the reason.

### Edge Cases

- A feature split into several parts (islands): stays one region with that feature's ID.
- Several features sharing one ID value, or features without the ID field: the docs say how this shows up and how to fix it in mapshaper (e.g. dissolve by the field).
- Coordinates spanning the antimeridian (e.g. Russia, Fiji in the world map): the bundled world map must not draw wrap-around artefacts.
- Small territories (islands, enclaves) in demo maps: kept only where they are regions in their own right or needed for recognisable outlines; documented.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The installed shinymap package MUST include three demo maps: world countries, US states (50 + DC), and Japan's 47 prefectures, each loadable in one line as an Outline.
- **FR-002**: Region IDs MUST follow standard codes: ISO 3166-1 alpha-3 for countries, USPS two-letter codes for US states, and JIS X 0401 two-digit codes (`"01"`–`"47"`) for Japanese prefectures (the scheme the current Japan map and the student examples already use). Each region MUST carry an English name; Japanese prefectures MUST also carry the Japanese name.
- **FR-003**: Demo map sources MUST be public domain or CC BY (no share-alike). Source, license, edition/date and any required credit MUST ship with the package and appear on the docs page.
- **FR-004**: US Alaska and Hawaii, and Japan's Okinawa, MUST be placed so the whole map fits a compact frame (insets or repositioning), as is customary for these maps.
- **FR-005**: The total size added by the demo maps MUST be stated in the plan and kept within SC-003.
- **FR-006**: A maintainer MUST be able to regenerate the demo maps from their sources with a script in the repository, using the same GeoJSON → SVG → outline recipe the docs show. The tools it needs MUST NOT become runtime dependencies of shinymap.
- **FR-007**: shinymap MUST NOT gain a GeoJSON reader. Users bring their own regions as SVG with one `id` per region, read by the existing `Outline.from_svg()`. If the recipe reveals a gap in `from_svg()` (e.g. how it treats IDs or multi-part shapes from mapshaper output), fixing that gap is in scope.
- **FR-008**: Per constitution VII, a docs page MUST show the demo maps in use and the recipe GeoJSON → mapshaper (project, simplify, choose the ID field, export SVG) → `Outline.from_svg()`, with copyable examples. New public APIs MUST appear in the API reference.
- **FR-009**: The CC BY-SA Japan map and its license file MUST be removed from the repository; examples and tests that use it MUST use the bundled Japan demo map.
- **FR-010**: `dev/PROPOSAL.md` and `dev/SPEC.md` MUST drop `shinymap-geo` and state GIS features as a non-goal, with the reason (other libraries cover them; shinymap's value is shapes as inputs). The SPEC "Geometry & Assets" section is updated to match.
- **FR-011**: Constitution II MUST be amended in its own PR (maintainer approval, version bump per Governance): the core's code stays free of geographic logic (no projections, no GeoJSON reading, nothing in the API assumes places), and the core may ship demo maps as shape data. The reference to `shinymap-geo` is removed.

### Key Entities

- **Demo map**: a bundled Outline with region IDs, per-region names, a view box, and source/license metadata.
- **Recipe**: the documented steps from a GeoJSON file to an outline; also used by the maintainer script.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user renders any of the three demo maps as an input map with at most 5 lines of code beyond the Shiny app skeleton, with nothing installed but shinymap.
- **SC-002**: Every one of the 3 demo maps has 100% of its expected regions (countries in the source layer, 51 US regions, 47 prefectures) with a code and a name.
- **SC-003**: The three demo maps together add no more than 1 MB to the installed package.
- **SC-004**: Following only the docs page, a user turns a GeoJSON file of 47 prefectures into a working input map on the first try, using the browser version of mapshaper (no install).
- **SC-005**: Zero share-alike-licensed files remain in the shipped package and examples.

## Assumptions

- World map is at a coarse "small-scale" resolution suitable for a page-width figure; small countries may be tiny but still present if the source includes them.
- Projection choices for demo maps (e.g. an equal-area projection for the US, a world projection) are made in the maintainer script; users never choose a projection inside shinymap.
- The bundled Japan map is one general-purpose style. Variants (tile grid, illustrative) and municipalities belong to `shinymapjp` (#76), which may use the same recipe.
- Natural Earth is the expected source for all three maps (public domain). If its Japan prefecture outlines prove too coarse, an N03-derived map is out of scope here until the 測量法 question in #76 is answered.
- The separate student examples repository (`shinymap-examples`) keeps its own map copy; updating it is outside this repository's feature.
- mapshaper (MPL-2.0) is the expected tool for the recipe and the maintainer script: its browser version for users, its command-line version (Node.js, already used to build the JS) for the script. Adding it as a development dependency needs maintainer approval in the plan.
