"""Sentinel value for missing optional parameters.

This module provides a sentinel value MISSING that can be used throughout the library
to indicate missing optional parameters, avoiding ambiguity with None which might be
a valid value.
"""

from __future__ import annotations


class MissingType:
    """Sentinel type for missing optional parameters.

    This is better than using None because None might be a valid value.
    MissingType is falsy, allowing for concise `value or default` patterns.

    Example:
        >>> from shinymap import MISSING
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
        return "shinymap.MISSING"

    def __bool__(self) -> bool:
        """Make MISSING falsy for use in `value or default` patterns."""
        return False


# Singleton sentinel value for missing parameters
MISSING = MissingType()


__all__ = ["MissingType", "MISSING"]
