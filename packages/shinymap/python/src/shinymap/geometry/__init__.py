"""End-of-life stub: shinymap.geometry has been renamed to shinymap.outline.

This module exists only to provide a helpful error message for users
who have not yet migrated their imports. Importing it in any form raises.
"""

raise ImportError(
    "'shinymap.geometry' has been renamed to 'shinymap.outline' in shinymap 0.3.0.\n"
    "Please update your imports, e.g.:\n"
    "  from shinymap.outline import Outline   # was: Geometry\n"
    "  from shinymap import outline"
)
