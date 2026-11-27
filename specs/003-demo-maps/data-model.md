# Data model: demo outline metadata

Each demo file is ordinary outline JSON (as written by `Outline.to_json()`): region ID → path, plus `_metadata`. The keys below are added to `_metadata`; existing keys (`viewBox`, layers) keep their meaning.

| Key | Type | Content |
|---|---|---|
| `names` | `{lang: {region_id: str}}` | `"en"` for every map; `"ja"` also for `japan` |
| `source` | `str` | e.g. `"Natural Earth 1:110m Admin 0 – Countries, v5.1.1"` |
| `source_url` | `str` | download URL |
| `license` | `str` | `"Public domain"` |
| `id_scheme` | `str` | `"ISO 3166-1 alpha-3 (see NOTICE for exceptions)"`, `"USPS"`, `"JIS X 0401"` |
| `generated_by` | `str` | script path and mapshaper version |

`japan` and `us_states` also contain one non-region element `_inset_frames` (rectangles around relocated areas), listed in `_metadata["overlay"]`; it has no name and is excluded from the region counts below.

Validation (in the build script and tests):

- region count: world = number of features in the filtered source (176 at 5.1.1), `us_states` = 51, `japan` = 47
- IDs unique and non-empty; every ID has an `"en"` name (and `"ja"` for `japan`)
- `japan` IDs are exactly `"01"`…`"47"`; `us_states` IDs are 2 uppercase letters; `world` IDs are 3 uppercase letters

`NOTICE.md` next to the files repeats source, version, license and the world-map code exceptions for people reading the package.
