"""Module-level registries for shinymap UI components.

This module holds shared state that needs to be accessed by multiple
UI components without causing circular imports.
"""

from collections.abc import Mapping, MutableMapping
from typing import Any

# Module-level registry for static parameters from output_map()
# Used by _output_map to store static params, and by _render_map to retrieve them
_static_map_params: MutableMapping[str, Mapping[str, Any]] = {}
