"""Binary (two-state) color palettes for toggle selections.

These palettes define off/on states for Single/Multiple selection modes.
"""

from __future__ import annotations

# Standard binary toggle: light gray → blue
BINARY_TOGGLE = [
    "#e5e7eb",  # gray-200 (off/unselected)
    "#3b82f6",  # blue-500 (on/selected)
]

# Green variant: light gray → green
BINARY_GREEN = [
    "#e5e7eb",  # gray-200 (off)
    "#22c55e",  # green-500 (on)
]

# Red variant: light gray → red
BINARY_RED = [
    "#e5e7eb",  # gray-200 (off)
    "#ef4444",  # red-500 (on)
]

__all__ = ["BINARY_TOGGLE", "BINARY_GREEN", "BINARY_RED"]
