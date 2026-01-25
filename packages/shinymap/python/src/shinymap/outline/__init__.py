"""Outline utilities for working with SVG paths.

This subpackage provides the Outline class for working with SVG outlines:

## Loading Outlines

```python
from shinymap import Outline

# From SVG file
outline = Outline.from_svg("map.svg")

# From JSON file
outline = Outline.from_json("map.json")

# From dict
outline = Outline.from_dict({"region_01": ["M 10 10 L 40 10 Z"]})
```

## Transformations (Fluent API)

```python
outline = (
    Outline.from_svg("map.svg")
    .relabel({"tokyo": "path_1", "hokkaido": ["path_2", "path_3"]})
    .move_layer("overlay", "_border")
    .update_metadata({"source": "Custom SVG"})
)
outline.to_json("map.json")
```

## One-shot Conversion

For scripted conversions, use `shinymap.kit.convert`:

```python
from shinymap.kit import convert

convert(
    "map.svg",
    "map.json",
    relabel={"tokyo": "path_1"},
    overlay_ids=["_border"],
)
```

## Interactive Conversion

For interactive SVG relabeling and layer assignment:

```bash
uv run python -m shinymap.kit.sketch
```
"""

from __future__ import annotations

from ._core import Outline
from ._export import export_svg
from ._regions import Regions
from ._repr_config import ReprConfig, get_repr_config, set_repr_options

__all__ = [
    "Outline",
    "Regions",
    "export_svg",
    "ReprConfig",
    "get_repr_config",
    "set_repr_options",
]

# EOL stubs for moved functions
_MOVED_TO_KIT = {
    "convert": "shinymap.kit.convert",
    "from_svg": "Outline.from_svg",
    "from_json": "Outline.from_json",
    "infer_relabel": "shinymap.kit (or use sketch app)",
}


# End-of-Life stubs for moved SVG element classes
_MOVED_TO_SVG = {
    "Circle",
    "Rect",
    "Path",
    "Polygon",
    "Ellipse",
    "Line",
    "Text",
    "Element",
    "ELEMENT_TYPE_MAP",
}


def __getattr__(name: str):
    if name in _MOVED_TO_KIT:
        replacement = _MOVED_TO_KIT[name]
        raise ImportError(
            f"'{name}' has been removed from shinymap.outline. Use {replacement} instead."
        )
    if name in _MOVED_TO_SVG:
        raise ImportError(
            f"'{name}' has moved to shinymap.svg. "
            f"Please update your import:\n"
            f"  from shinymap.svg import {name}"
        )
    raise AttributeError(f"module 'shinymap.outline' has no attribute '{name}'")
