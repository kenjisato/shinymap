"""Type definitions for shinymap.

This module exports types for use in type hints and isinstance checks.

Usage:
    from shinymap.types import MISSING, MissingType, BaseAesthetic, MapBuilder
"""

from __future__ import annotations

from typing import TYPE_CHECKING


class MissingType:
    """Sentinel type for missing optional parameters.

    This is better than using None because None might be a valid value.
    MissingType is falsy, allowing for concise `value or default` patterns.

    Example:
        >>> from shinymap.types import MISSING
        >>> def foo(x: int | MissingType = MISSING):
        ...     x = x or 42  # Use default if x is MISSING
        ...     print(f"x = {x}")
        >>> foo()
        x = 42
        >>> foo(10)
        x = 10
        >>> foo(None)  # None is a valid value, different from missing
        x = None
    """

    def __repr__(self) -> str:
        return "shinymap.types.MISSING"

    def __bool__(self) -> bool:
        """Make MISSING falsy for use in `value or default` patterns."""
        return False


# Singleton sentinel value for missing parameters
MISSING = MissingType()


def __getattr__(name: str):
    """Lazy import for types that have circular dependencies."""
    if name == "BaseAesthetic":
        from .aes._core import BaseAesthetic

        return BaseAesthetic
    if name == "MapBuilder":
        from ._map import MapBuilder

        return MapBuilder
    if name == "WashConfig":
        from ._wash import WashConfig

        return WashConfig
    if name == "WashResult":
        from ._wash import WashResult

        return WashResult
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


if TYPE_CHECKING:
    from ._map import MapBuilder
    from ._wash import WashConfig, WashResult
    from .aes._core import BaseAesthetic

__all__ = [
    "BaseAesthetic",
    "MapBuilder",
    "MISSING",
    "MissingType",
    "WashConfig",
    "WashResult",
]
