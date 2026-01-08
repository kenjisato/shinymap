"""Kit module for preparing SVG files for use with shinymap.

This module provides tools for:
- Interactive relabeling and layer assignment (sketch app)
- Generating reference SVGs with ID labels (caption tool)
- One-shot conversion from mapping dicts (apply_mapping)
- Code generation for reproducible conversions

Command-line usage:
    # Generate reference SVG with ID labels
    uv run python -m shinymap.kit.caption input.svg -o labeled.svg

    # Interactive sketch app
    uv run python -m shinymap.kit.sketch [-f FILE]

    # Interactive review app
    uv run python -m shinymap.kit.review [-f FILE]

Programmatic usage:
    >>> from shinymap import Outline
    >>> from shinymap.kit import describe, glaze, apply_mapping
    >>>
    >>> # Generate labels at region centers
    >>> outline = Outline.from_svg("map.svg")
    >>> labels = describe(outline)
    >>> labeled = glaze(outline, labels)
    >>>
    >>> # One-shot conversion from mapping
    >>> mapping = {
    ...     "groups": {"tokyo": "path_1", "osaka": ["path_2", "path_3"]},
    ...     "layers": {"overlay": ["_border"]},
    ... }
    >>> converted = apply_mapping(outline, mapping)
"""

from shinymap.kit._caption import describe, glaze
from shinymap.kit._code_gen import apply_mapping, convert, generate_code

__all__ = [
    # Conversion
    "convert",
    "apply_mapping",
    "generate_code",
    # Composable utilities
    "describe",
    "glaze",
]
