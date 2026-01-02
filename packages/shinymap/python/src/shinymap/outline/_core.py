"""Utilities for loading and converting SVG outlines.

This module provides tools for working with SVG outlines in shinymap:

1. **SVG to JSON converter**: Extract path data from SVG files into shinymap JSON format
2. **JSON loader**: Load outline from JSON with automatic viewBox calculation

## Shinymap JSON Outline Format

The shinymap outline format is designed for simplicity and transparency:

**Structure:**
```json
{
    "_metadata": {
        "source": "Wikimedia Commons - File:Japan_template_large.svg",
        "license": "CC BY-SA 3.0",
        "viewBox": "0 0 1500 1500",
        "overlays": ["_divider_lines", "_border"]
    },
    "region1": "M 0 0 L 100 0 L 100 100 Z",
    "region2": "M 100 0 L 200 0 L 200 100 Z",
    "_divider_lines": "M 100 0 L 100 100",
    "_border": "M 0 0 L 200 0 L 200 200 L 0 200 Z"
}
```

**Rules:**
1. **String values** = SVG path data (outline)
2. **Dict/list values** = metadata (ignored by loader)
3. **Keys starting with underscore** = typically overlays or metadata
4. **_metadata.viewBox** (optional) = preferred viewBox string
5. **_metadata.overlays** (optional) = list of overlay keys

**Why this format?**
- **Flat and transparent**: Easy to inspect, edit, version control
- **SVG-native**: Path strings are valid SVG without transformation
- **Extensible**: Metadata coexists with outline without conflicts
- **Geometry-agnostic**: Works for maps, diagrams, floor plans, etc.

**Comparison to GeoJSON/TopoJSON:**
- GeoJSON/TopoJSON are standards for *geographic* data with projections
- shinymap format is geometry-agnostic (works for any SVG paths)
- Simpler when you already have SVG paths from design tools
- For geographic workflows, use shinymap-geo (future extension)
"""

from __future__ import annotations

# Re-export conversion functions
from ._conversion import (
    convert,
    from_json,
    from_svg,
    infer_relabel,
)

# Re-export Outline class
from ._outline import Outline

__all__ = [
    # Main class
    "Outline",
    # Conversion functions
    "from_svg",
    "from_json",
    "convert",
    "infer_relabel",
]
