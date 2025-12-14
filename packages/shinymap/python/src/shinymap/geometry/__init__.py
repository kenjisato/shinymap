"""Geometry utilities for working with SVG paths.

This subpackage provides tools for:
- Converting SVG files to shinymap JSON format (convert, from_svg, from_json)
- Loading geometry from JSON files (load_geometry)
- Computing viewBox from geometry dicts (compute_viewbox_from_dict)
- Inferring conversion code from original source (infer_relabel)

## JSON Format

Shinymap geometry JSON files use a **list-based path format**:

```json
{
  "_metadata": {
    "viewBox": "0 0 100 100",
    "source": "Custom SVG",
    "license": "MIT"
  },
  "region_01": ["M 10 10 L 40 10 L 40 40 L 10 40 Z"],
  "hokkaido": [
    "M 0 0 L 100 0 L 100 100 Z",
    "M 200 0 L 300 0 L 300 100 Z"
  ]
}
```

**Key points:**
- Each region maps to a **list of SVG path strings**
- Single-element list: single path (e.g., `"region_01": ["M 10 10..."]`)
- Multi-element list: merged paths (e.g., `"hokkaido": ["M 0 0...", "M 200 0..."]`)
- Paths are joined with spaces when rendered: `" ".join(path_list)`

## Conversion Workflows

**Interactive workflow** (two-step for manual inspection):
```python
from shinymap.geometry import from_svg, from_json

# Step 1: Extract intermediate JSON with auto-generated IDs
intermediate = from_svg("map.svg", "intermediate.json")
# Result: {"_metadata": {...}, "path_1": ["M..."], "path_2": ["M..."], ...}

# Inspect intermediate JSON, plan transformations
print(list(intermediate.keys()))  # ['_metadata', 'path_1', 'path_2', ...]

# Step 2: Apply transformations
final = from_json(
    intermediate,
    "final.json",
    relabel={
        "region_01": "path_1",              # Rename: path_1 → region_01
        "hokkaido": ["path_2", "path_3"],   # Merge: combine into hokkaido
    },
    overlay_ids=["_border"],
    metadata={"source": "Custom", "license": "MIT"}
)
# Result: {"region_01": ["M..."], "hokkaido": ["M...", "M..."], ...}
```

**One-shot conversion** (scripting/reproducibility):
```python
from shinymap.geometry import convert

# From SVG file
result = convert(
    "map.svg",
    "map.json",
    relabel={
        "region_01": "path_1",              # Rename single path
        "hokkaido": ["path_2", "path_3"],   # Merge multiple paths
    },
    overlay_ids=["_border"],
    metadata={"source": "Custom", "license": "MIT"}
)

# From intermediate JSON file
result = convert(
    "intermediate.json",
    "final.json",
    relabel={"region_01": "path_1"},
)
```

**Infer conversion code** (reproducibility from manual work):
```python
from shinymap.geometry import infer_relabel, convert

# After manually creating final.json, infer the transformations
relabel = infer_relabel("original.svg", "final.json")
# Returns: {"region_01": "path_1", "hokkaido": ["path_2", "path_3"]}

# Generate reproducible code
code = f'''
convert(
    "original.svg",
    "final.json",
    relabel={relabel},
)
'''
```
"""

from __future__ import annotations

from ._core import (
    compute_viewbox_from_dict,
    convert,
    from_json,
    from_svg,
    infer_relabel,
    load_geometry,
)

__all__ = [
    "compute_viewbox_from_dict",
    "convert",
    "from_svg",
    "from_json",
    "infer_relabel",
    "load_geometry",
]
