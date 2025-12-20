"""Utilities for loading and converting SVG geometry.

This module provides tools for working with SVG geometry in shinymap:

1. **SVG to JSON converter**: Extract path data from SVG files into shinymap JSON format
2. **JSON loader**: Load geometry from JSON with automatic viewBox calculation

## Shinymap JSON Geometry Format

The shinymap geometry format is designed for simplicity and transparency:

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
1. **String values** = SVG path data (geometry)
2. **Dict/list values** = metadata (ignored by loader)
3. **Keys starting with underscore** = typically overlays or metadata
4. **_metadata.viewBox** (optional) = preferred viewBox string
5. **_metadata.overlays** (optional) = list of overlay keys

**Why this format?**
- **Flat and transparent**: Easy to inspect, edit, version control
- **SVG-native**: Path strings are valid SVG without transformation
- **Extensible**: Metadata coexists with geometry without conflicts
- **Geometry-agnostic**: Works for maps, diagrams, floor plans, etc.

**Comparison to GeoJSON/TopoJSON:**
- GeoJSON/TopoJSON are standards for *geographic* data with projections
- shinymap format is geometry-agnostic (works for any SVG paths)
- Simpler when you already have SVG paths from design tools
- For geographic workflows, use shinymap-geo (future extension)
"""

from __future__ import annotations

# Re-export BoundsCalculator type alias
# Re-export viewbox calculation utilities (public API)
from ._bounds import (
    BoundsCalculator,
    calculate_viewbox,
    compute_viewbox_from_dict,
)

# Re-export conversion functions
from ._conversion import (
    convert,
    from_json,
    from_svg,
    infer_relabel,
)

# Re-export Geometry class
from ._geometry import Geometry

# Re-export loader function
from ._loader import load_geometry

# Note: Internal helper functions from _bounds are not re-exported:
# - _parse_svg_dimension
# - _has_complex_commands
# - _find_complex_commands
# - _compute_bounds_accurate
# - _parse_svg_path_bounds
# - _normalize_geometry_dict
# These remain private to the geometry package.

__all__ = [
    # Type alias
    "BoundsCalculator",
    # Main class
    "Geometry",
    # Conversion functions
    "from_svg",
    "from_json",
    "convert",
    "infer_relabel",
    # Loader function
    "load_geometry",
    # ViewBox utilities
    "calculate_viewbox",
    "compute_viewbox_from_dict",
]
