"""Type definitions for shinymap.

This module exports types for use in type hints and isinstance checks.

Usage:
    from shinymap.types import MISSING, MissingType, BaseAesthetic, MapBuilder
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any


class MissingType:
    """Sentinel type for missing optional parameters.

    This is better than using None because None might be a valid value.
    MissingType is falsy, allowing for concise `value or default` patterns.

    Example:
        >>> from shinymap.types import MISSING
        >>> # MISSING is falsy, enabling `x or default` pattern
        >>> bool(MISSING)
        False
        >>> # When None is NOT a valid value, use `or`:
        >>> def greet(name=MISSING):
        ...     name = name or "World"
        ...     print(f"Hello, {name}!")
        >>> greet()
        Hello, World!
        >>> greet("Alice")
        Hello, Alice!
        >>>
        >>> # When None IS a valid value, use `is MISSING`:
        >>> def set_color(color=MISSING):
        ...     if color is MISSING:
        ...         color = "#000"  # default black
        ...     print(f"color = {color}")
        >>> set_color()
        color = #000
        >>> set_color("#fff")
        color = #fff
        >>> set_color(None)  # None means "transparent"
        color = None
    """

    def __repr__(self) -> str:
        return "shinymap.types.MISSING"

    def __bool__(self) -> bool:
        """Make MISSING falsy for use in `value or default` patterns."""
        return False


# Singleton sentinel value for missing parameters
MISSING = MissingType()


# Type Aliases
# OutlineMap accepts various region representations:
# - str: single path string
# - list[str]: multiple path strings
# - list[Any]: list containing str, dict, or objects with to_dict() (e.g., Element)
# - dict: single element dict
OutlineMap = Mapping[str, str | list[Any] | dict[str, Any]]

TooltipMap = Mapping[str, str] | None

FillMap = str | Mapping[str, str] | None

CountMap = Mapping[str, int] | None


def __getattr__(name: str):
    """Lazy import for types that have circular dependencies."""
    if name == "BaseAesthetic":
        from .aes._core import BaseAesthetic

        return BaseAesthetic
    if name == "MapBuilder":
        from ._map import MapBuilder

        return MapBuilder
    if name == "WashConfig":
        from .uicore._wash import WashConfig

        return WashConfig
    if name == "WashResult":
        from .uicore._wash import WashResult

        return WashResult
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


if TYPE_CHECKING:
    from ._map import MapBuilder
    from .aes._core import BaseAesthetic
    from .uicore._wash import WashConfig, WashResult

__all__ = [
    "BaseAesthetic",
    "MapBuilder",
    "MISSING",
    "MissingType",
    "WashConfig",
    "WashResult",
    "OutlineMap",
    "TooltipMap",
    "FillMap",
    "CountMap",
]
