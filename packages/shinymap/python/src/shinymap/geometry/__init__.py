"""End-of-life stub: shinymap.geometry has been renamed to shinymap.outline.

This module exists only to provide a helpful error message for users
who have not yet migrated their imports.
"""

from __future__ import annotations


def __getattr__(name: str):
    """Raise ImportError with migration instructions for any attribute access."""
    raise ImportError(
        f"'shinymap.geometry' has been renamed to 'shinymap.outline'. "
        f"Please update your import:\n"
        f"  from shinymap.outline import {name}\n"
        f"Or:\n"
        f"  from shinymap import outline"
    )
