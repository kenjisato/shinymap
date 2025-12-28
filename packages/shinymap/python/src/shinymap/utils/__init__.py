"""Utility functions for shinymap.

This module provides helper functions for creating aesthetic values,
particularly for use with aes.Indexed in Count/Cycle modes.
"""

from __future__ import annotations

__all__ = ["linspace"]


def linspace(start: float, stop: float, num: int = 5) -> list[float]:
    """Generate evenly spaced values between start and stop (inclusive).

    Similar to numpy.linspace, but returns a plain Python list.
    Useful for creating opacity gradients, stroke width progressions,
    or any numeric aesthetic property that varies by state/count.

    Args:
        start: Starting value (included in output).
        stop: Ending value (included in output).
        num: Number of values to generate (default: 5). Must be >= 1.

    Returns:
        List of evenly spaced float values.

    Raises:
        ValueError: If num < 1.

    Example:
        >>> from shinymap.utils import linspace
        >>> from shinymap import aes
        >>>
        >>> # Opacity gradient from transparent to opaque
        >>> linspace(0.0, 1.0, num=6)
        [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        >>>
        >>> # Stroke width progression
        >>> linspace(0.5, 3.0, num=6)
        [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        >>>
        >>> # Use with aes.Indexed for count mode
        >>> aes.Indexed(
        ...     fill_color="#f97316",
        ...     fill_opacity=linspace(0.0, 1.0, num=6),
        ... )
    """
    if num < 1:
        raise ValueError("num must be at least 1")

    if num == 1:
        return [start]

    step = (stop - start) / (num - 1)
    return [start + i * step for i in range(num)]
