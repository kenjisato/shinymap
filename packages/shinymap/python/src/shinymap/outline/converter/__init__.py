"""This module has moved to shinymap.kit.sketch.

Run with: uv run python -m shinymap.kit.sketch
"""


def __getattr__(name: str):
    raise ImportError(
        "'shinymap.outline.converter' has moved to 'shinymap.kit.sketch'. "
        "Run with: uv run python -m shinymap.kit.sketch"
    )
