"""Theme configuration for app-level aesthetic customization."""

from __future__ import annotations

from collections.abc import Mapping
from contextvars import ContextVar
from typing import Any

# Thread-safe context variable for app-level theme configuration
_theme_config: ContextVar[Mapping[str, Any] | None] = ContextVar("shinymap_theme", default=None)


def configure_theme(**kwargs: Any) -> None:
    """Configure aesthetic defaults for all maps in this app/session.

    This function sets app-level aesthetic defaults that apply to all input_map()
    and output_map() calls within the current session. It uses context variables
    to ensure thread-safety across multiple Shiny sessions.

    Call this function BEFORE defining your UI components. The configuration
    applies to the current session only and does not affect other sessions.

    Args:
        **kwargs: Aesthetic parameters to use as defaults.
                 Common parameters:
                 - default_aesthetic: Base styling dict
                 - selected_aesthetic: Selected region styling dict
                 - hover_highlight: Hover overlay styling dict
                 - fill_color: Fill color(s)
                 - Any other parameter accepted by input_map() or output_map()

    Examples:
        Basic usage:
        >>> from shinymap import configure_theme, input_map
        >>>
        >>> configure_theme(
        ...     selected_aesthetic={"fill_color": "#ffffcc"},
        ...     hover_highlight={"stroke_width": 8}
        ... )
        >>>
        >>> # All maps in this session use the configured defaults
        >>> app_ui = ui.page_sidebar(
        ...     ui.sidebar(
        ...         input_map("map1", geo1),  # Uses configured theme
        ...         input_map("map2", geo2),  # Uses configured theme
        ...     )
        ... )

        Override for specific map:
        >>> configure_theme(hover_highlight={"stroke_width": 4})
        >>> input_map("map1", geo)  # Uses stroke_width: 4
        >>> input_map("map2", geo, hover_highlight={"stroke_width": 8})  # Override

    Note:
        - This configuration is session-scoped (thread-safe for Shiny apps)
        - Explicit parameters to input_map()/output_map() override configured theme
        - System defaults are used for any parameters not configured or specified
    """
    _theme_config.set(dict(kwargs))


def get_theme_config() -> Mapping[str, Any]:
    """Get current theme configuration (internal use only)."""
    return _theme_config.get() or {}
