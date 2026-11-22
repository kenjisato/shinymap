"""Utility functions for shinymap.

This module provides helper functions for creating aesthetic values,
particularly for use with aes.Indexed in Count/Cycle modes.
"""

from __future__ import annotations

from ._linspace import linspace
from ._svg import path_bb, strip_unit

__all__ = ["linspace", "path_bb", "strip_unit"]
