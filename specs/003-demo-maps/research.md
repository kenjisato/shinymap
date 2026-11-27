# Research: 003-demo-maps

A spike (2026-11-27) ran the full recipe with mapshaper 0.8.13 and Natural Earth 5.1.1, loaded each SVG with `Outline.from_svg()`, and rendered the results. Everything below marked "verified" was run; the rest is reasoning.

## Recipe works with today's `from_svg()` (verified)

mapshaper's SVG is a root `<svg viewBox="0 0 800 H">`, one `<g id="<layer>">` without styles or transforms, and one `<path id=… d=…>` per feature (multi-part features, i.e. islands, stay one path). `from_svg()` reads the viewBox, skips the `<g>`, and uses each `id`. No auto-generated IDs.

`-clean` after `-simplify` is required: without it, the extent keeps islands that simplification removed, leaving empty areas.

## Source: Natural Earth 5.1.1 (public domain)

- Decision: Natural Earth for all three maps, from `https://naciscdn.org/naturalearth/{110m,50m,10m}/cultural/<name>.zip`.
- Rationale: public domain, no credit required, no 測量法 question (unlike N03, see #76).
- Alternatives: N03 for Japan (blocked on GSI confirmation), US Census cartographic boundaries (public domain, but a second pipeline for one map).

## World countries

- Decision: 1:110m `admin_0_countries`, Antarctica filtered out, `-simplify 30% keep-shapes -clean`, Robinson centred on 11°E (`+proj=robin +lon_0=11`), ID from `ADM0_A3`, then rename `SAH→ESH`, `PSX→PSE`, `SDS→SSD` to match ISO 3166-1; `KOS→XKX` (the widely used user-assigned code). Northern Cyprus (`CYN`) and Somaliland (`SOL`) have no ISO code; keep Natural Earth's codes and say so in `NOTICE.md` and the docs. Verified: 176 regions, 47 KB SVG.
- Rationale: `ISO_A3` is `-99` for France and Norway; `ISO_A3_EH` still `-99` for three features, which would collide. `ADM0_A3` is unique. Centring on 11°E puts the seam in the Bering Strait so Russia and Fiji are not split (verified by rendering).
- Trade-off: 110m lacks small countries (Singapore, Bahrain, Malta, Andorra, Monaco, Liechtenstein, Maldives, Mauritius, Barbados, Cape Verde, Comoros, Hong Kong). 50m includes them but is 130–234 KB. Decision: 110m; the docs say small countries are missing. A demo map does not need them.

## US states

- Decision: 1:50m `admin_1_states_provinces_lakes`, filter `adm0_a3=="USA"`, save subset first, then `-simplify 20% keep-shapes -proj albersusa`, ID from `postal`. Verified: 51 regions, USPS codes, 30 KB SVG.
- Rationale: `-proj albersusa` moves Alaska and Hawaii into insets (FR-004). The `_lakes` variant keeps Michigan and others off the Great Lakes. Filtering before simplifying avoids "unprojectable vertices" warnings.

## Japan prefectures

- Decision: 1:10m `admin_1_states_provinces`, filter `adm0_a3=="JPN"`, `code = iso_3166_2.slice(3)` ("01"–"47"), keep `name` and `name_ja`; `-clip bbox=122,24,146,46` (drops Ogasawara/Minamitorishima, which otherwise stretch the frame), `-simplify 20% keep-shapes -clean`, `+proj=tmerc +lon_0=137`, Okinawa moved with `-affine where='code=="47"'` into the Sea of Japan. Verified: 47 regions, 33 KB SVG; render looks recognisable.
- Rationale: `postal` is empty for four prefectures; `iso_3166_2` is complete. `name_ja` is present for all 47.

## Inset frames (decided 2026-11-27 with the maintainer)

- Decision: frame every relocated area with a rectangle computed from its bounding box in the final SVG (plus padding), as one overlay region `_inset_frames` per map. The build script fails if a frame overlaps another region's bounding box.
- Rationale: frames are the customary sign that an area was moved; without them Okinawa reads as lying in the Sea of Japan. Computing them from the output keeps them correct when simplification or shift values change, and works for `albersusa`, whose shifts are internal to mapshaper. They are drawn lines, not geographic logic, so they fit amended constitution II. The current Japan map already carries a divider line as an overlay.
- Alternatives: diagonal or L-shaped separators (need per-map placement rules, harder to automate); hand-placed coordinates (go stale).

## Tool: mapshaper (MPL-2.0)

- Decision: maintainer script calls `npx --yes mapshaper@0.8.13`; users are pointed to the browser version (mapshaper.org).
- Rationale: one tool does filter, simplify, project, clip and SVG export with an ID field. Node is already needed for the JS build. Pinning the version through npx avoids adding it to a package manifest.
- Alternatives: geopandas + shapely (large Python dev deps, no SVG export), QGIS (GUI, not scriptable for contributors).
- Licence: MPL-2.0 is fine for a tool that is run, not distributed.

## `from_svg()` gaps (from reading the code)

- Duplicate `id`s: the later element silently replaces the earlier. Decision: raise `ValueError` naming the ID (in scope per FR-007; it bites recipe users with a bad ID field).
- `transform` attributes are ignored and `data-*` attributes dropped. mapshaper writes neither by default; names come from the build script, not the SVG. No change.

## Names

- Decision: the build script reads names from the GeoJSON step (`name`, `name_ja`) and writes them into outline metadata ([data-model.md](data-model.md)); `from_svg()` stays unchanged.
- Alternative: mapshaper `svg-data=` + teaching `from_svg()` to read `data-*`. Rejected: more surface for one internal use.
